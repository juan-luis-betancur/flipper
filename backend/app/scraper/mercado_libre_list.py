"""Listado web Mercado Libre Colombia: extracción de ítems y paginación _Desde_*_NoIndex_True.

Smoke / producción (p. ej. Railway):
- El PoW suele funcionar desde IP residencial; algunas IPs de datacenter reciben 403 o HTML de reto
  sin resolver. Si el pipeline falla en listado, prueba ``ML_COOKIE`` (header ``Cookie`` copiado del
  navegador tras abrir el mismo listado; caduca).
- Ejecutar un smoke manual: ``cd backend && python experiments/ml_list_probe.py --url "<list_url>"``.
"""
from __future__ import annotations

import random
import re
from typing import Any

import httpx  # noqa: F401  # se mantiene por compat de tipos en otros módulos
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

from .mercado_libre_challenge import ML_BROWSER_HEADERS, fetch_html_after_challenge

# Pool de User-Agents de Chrome recientes. Reduce fingerprinting trivial.
_CHROME_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def _pick_user_agent(default_ua: str | None = None) -> str:
    ua = (default_ua or "").strip()
    if ua and "FlipperMVP" not in ua:
        return ua
    return random.choice(_CHROME_UA_POOL)

# Tamaño de página típico en JSON de paginación ML (49 -> 97 = +48).
_ML_PAGE_STEP = 48
_ML_FIRST_OFFSET = 49

_MCO_ITEM_RE = re.compile(
    r"https://[a-z0-9.-]+\.mercadolibre\.com\.co/(?:MCO|MLC)-(\d+)-",
    re.I,
)
_MCO_URL_IN_HTML_RE = re.compile(
    r"https://[a-z0-9.-]+\.mercadolibre\.com\.co/MCO-\d+-[^\s\"'<>]+",
    re.I,
)
_DESDE_SUFFIX_RE = re.compile(r"/_Desde_\d+(?:_NoIndex_True)?/?$", re.I)


def strip_listing_pagination(url: str) -> str:
    u = url.rstrip("/")
    while True:
        nu = _DESDE_SUFFIX_RE.sub("", u)
        if nu == u:
            break
        u = nu
    return u.rstrip("/")


def listing_url_for_page(base_list_url: str, page_index: int) -> str:
    """
    page_index 0 = primera página (URL base sin _Desde_).
    Siguientes: /_Desde_49_NoIndex_True, /_Desde_97_NoIndex_True, ...
    """
    base = strip_listing_pagination(base_list_url)
    if page_index <= 0:
        return base
    offset = _ML_FIRST_OFFSET + (page_index - 1) * _ML_PAGE_STEP
    return f"{base}/_Desde_{offset}_NoIndex_True"


def extract_listing_items(html: str, limit: int | None = None) -> list[dict[str, str]]:
    """id MCO numérico, url canónica de publicación, título si hay en <a>."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    def add_url(href: str, title: str) -> None:
        href = href.strip().split("#")[0]
        m = _MCO_ITEM_RE.match(href)
        if not m:
            return
        item_id = m.group(1)
        if item_id in seen:
            return
        seen.add(item_id)
        t = (title or "").strip().replace("\n", " ")[:200]
        out.append({"id": item_id, "url": href, "title": t or "(sin título)"})

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        add_url(str(a["href"]), (a.get_text() or ""))
        if limit is not None and len(out) >= limit:
            return out

    for href in dict.fromkeys(_MCO_URL_IN_HTML_RE.findall(html)):
        add_url(href, "")
        if limit is not None and len(out) >= limit:
            break

    return out


def gather_listing_item_urls(
    client: Any,
    base_list_url: str,
    max_items: int,
    *,
    max_pages: int = 30,
) -> list[dict[str, str]]:
    """
    Recorre páginas de listado hasta max_items o hasta una página sin ítems nuevos.
    """
    seen: set[str] = set()
    ordered: list[dict[str, str]] = []

    for page in range(max_pages):
        if len(ordered) >= max_items:
            break
        url = listing_url_for_page(base_list_url, page)
        html = fetch_html_after_challenge(client, url)
        if len(html) < 10_000 and "verifyChallenge" in html:
            break
        batch = extract_listing_items(html, limit=None)
        added = False
        for it in batch:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            ordered.append(it)
            added = True
            if len(ordered) >= max_items:
                break
        if not batch or not added:
            break

    return ordered[:max_items]


def ml_client_with_optional_cookie(ml_cookie: str | None) -> Any:
    """Cliente ``curl_cffi`` con TLS fingerprint de Chrome + proxy residencial opcional.

    Akamai Bot Manager (ML) detecta la huella TLS (JA3/JA4) de ``httpx``/``requests``
    como "bot python" aunque el PoW pase. ``curl_cffi`` usa libcurl con BoringSSL e
    ``impersonate="chrome124"``, replicando el handshake real de Chrome. Esto suele
    ser el fix decisivo contra el soft-block que deja páginas sin ítems ``MCO-\\d+-``.

    Si ``ML_PROXY_URL`` está definido en el entorno (formato
    ``http://user:pass@host:port``), se enruta todo el tráfico ML por ese proxy
    residencial (Decodo / IPRoyal / Bright Data).
    """
    from ..config import get_settings

    settings = get_settings()
    headers = dict(ML_BROWSER_HEADERS)
    headers["User-Agent"] = _pick_user_agent(settings.user_agent)

    session_kwargs: dict[str, Any] = {
        "impersonate": "chrome124",
        "timeout": 60.0,
    }
    if settings.ml_proxy_url:
        # curl_cffi acepta `proxies={"http": ..., "https": ...}` o `proxy=<url>`.
        session_kwargs["proxies"] = {
            "http": settings.ml_proxy_url,
            "https": settings.ml_proxy_url,
        }

    session = cffi_requests.Session(**session_kwargs)
    # impersonate ya setea headers base de Chrome; sobreescribimos los nuestros
    # para mantener Accept-Language es-CO y UA rotado.
    session.headers.update(headers)
    if ml_cookie and ml_cookie.strip():
        session.headers["Cookie"] = ml_cookie.strip()
    return session


def fetch_listing_html(client: Any, list_url: str) -> str:
    """Una sola página: PoW o ML_COOKIE ya aplicada en client."""
    return fetch_html_after_challenge(client, list_url)


def scrape_ml_list_urls(list_url: str, max_items: int, ml_cookie: str | None = None) -> list[dict[str, Any]]:
    """
    Devuelve lista de dicts con id, url, title para consumo del scraper de detalle.
    """
    with ml_client_with_optional_cookie(ml_cookie) as client:
        return gather_listing_item_urls(client, list_url, max_items)
