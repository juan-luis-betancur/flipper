from __future__ import annotations

import json
import math
import re
import time
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings
from .barrio_llm import enrich_ubicacion_llm_placeholder
from .description_extract import extract_from_description, merge_description_extract
from .finca_raiz_detail import extract_next_data_json, map_property_data_to_row, pick_property_data
from .location_snapshot import patch_ubicacion_from_description_extract, patch_ubicacion_reverse_geocode
from .medellin_neighborhoods import whitelist_barrios

PREFIX = "https://www.fincaraiz.com.co/venta/apartamentos/antioquia"

# Tope de páginas de listado para evitar bucles ante HTML inesperado.
_MAX_LISTING_PAGES = 100

# "Mostrando 1 - 21 de 225 resultados" (números pueden llevar . como miles)
_RESULT_SUMMARY_RE = re.compile(
    r"mostrando\s+(\d[\d.]*)\s*-\s*(\d[\d.]*)\s+de\s+(\d[\d.]*)\s+resultados",
    re.I,
)

_PAGINA_SUFFIX_RE = re.compile(r"/pagina\d+/?$", re.I)

# Última página en enlaces del listado: …/venta/apartamentos/…/pagina42
_PAGINA_IN_LISTING_HREF_RE = re.compile(r"/pagina(\d+)(?:/|$|[?#])", re.I)

PUBLICATION_PATH = {
    "today": "publicado-hoy",
    "yesterday": "publicado-ayer",
    "this_week": "publicado-ultimos-7-dias",
    "last_15_days": "publicado-ultimos-15-dias",
    "last_30_days": "publicado-ultimos-30-dias",
    "last_40_days": "publicado-ultimos-40-dias",
    "none": "",
}


def _slug_barrio(name: str) -> str:
    import unicodedata

    s = (
        unicodedata.normalize("NFD", name.strip().lower())
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def _location_segment(neighborhoods: list[str]) -> str:
    slugs = [_slug_barrio(n) for n in neighborhoods if n and n.strip()]
    slugs = [s for s in slugs if s]
    if not slugs:
        return ""
    if len(slugs) == 1:
        return slugs[0]
    return "-y-en-".join(slugs)


def build_list_url(neighborhoods: list[str], publication_filter: str) -> str:
    """Misma lógica que web/src/lib/fincaRaizUrl.ts (path tipo FR real)."""
    loc = _location_segment(neighborhoods)
    pub = PUBLICATION_PATH.get(publication_filter, "")
    if not loc and not pub:
        return PREFIX
    if not loc:
        return f"{PREFIX}/{pub}"
    if not pub:
        return f"{PREFIX}/{loc}"
    return f"{PREFIX}/{loc}/{pub}"


def _external_id_from_url(url: str) -> str | None:
    m = re.search(r"-(\d{4,})\.(?:html?|htm)?(?:$|[?#])", url, re.I)
    if m:
        return m.group(1)
    m = re.search(r"/(\d{5,})(?:[/?#]|$)", url)
    if m:
        return m.group(1)
    return None


def extract_listing_urls(html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"https://www\.fincaraiz\.com\.co[^\"'\s<>]+", html):
        u = m.group(0).split("#")[0].rstrip("\\,.")
        if not re.search(r"\d{4,}", u):
            continue
        if "/apartamento" not in u.lower() and "apartamentos" not in u.lower():
            continue
        if u not in seen:
            seen.add(u)
            found.append(u)
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin("https://www.fincaraiz.com.co", href)
        if "fincaraiz.com.co" not in full:
            continue
        if not re.search(r"\d{4,}", full):
            continue
        if "/apartamento" in full.lower() or "apartamentos" in full.lower():
            full = full.split("#")[0]
            if full not in seen:
                seen.add(full)
                found.append(full)
    return found


def _strip_listing_pagination(url: str) -> str:
    u = url.rstrip("/")
    return _PAGINA_SUFFIX_RE.sub("", u)


def _listing_url_for_page(base: str, page: int) -> str:
    b = base.rstrip("/")
    if page <= 1:
        return b
    return f"{b}/pagina{page}"


def _parse_int_co(s: str) -> int:
    """Enteros como en el sitio (p. ej. miles con punto: 1.225)."""
    return int(re.sub(r"[^\d]", "", s))


def _max_page_from_listing_pagination(html: str) -> int | None:
    """
    Máximo N en hrefs del listado (…/venta/apartamentos/…/paginaN).
    Equivale al último botón numérico antes de «siguiente»; sirve cuando el resumen dice «más de 400».
    """
    soup = BeautifulSoup(html, "html.parser")
    best = 0
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin("https://www.fincaraiz.com.co", href).split("#")[0]
        if "fincaraiz.com.co" not in full.lower():
            continue
        if "/venta/apartamentos" not in full.lower():
            continue
        m = _PAGINA_IN_LISTING_HREF_RE.search(full)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if n > best:
            best = n
    if best < 1:
        return None
    return min(_MAX_LISTING_PAGES, best)


def _pages_from_result_summary(html: str) -> int | None:
    m = _RESULT_SUMMARY_RE.search(html)
    if not m:
        return None
    start = _parse_int_co(m.group(1))
    end = _parse_int_co(m.group(2))
    total = _parse_int_co(m.group(3))
    if end < start or total < 1:
        return None
    per_page = end - start + 1
    if per_page < 1:
        return None
    pages = max(1, math.ceil(total / per_page))
    return min(_MAX_LISTING_PAGES, pages)


def parsed_total_listing_pages(html: str) -> int | None:
    """
    Páginas de listado: primero enlaces /paginaN del listado (robusto con «más de 400»),
    si no hay, resumen «Mostrando … de Z resultados». None si no aplica.
    """
    from_href = _max_page_from_listing_pagination(html)
    if from_href is not None:
        return from_href
    return _pages_from_result_summary(html)


def _gather_listing_urls_across_pages(
    client: httpx.Client,
    base: str,
    max_props: int,
    first_page_html: str,
    known_pages: int | None,
) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def add_from_html(html: str) -> None:
        for u in extract_listing_urls(html):
            if u not in seen:
                seen.add(u)
                ordered.append(u)

    add_from_html(first_page_html)
    if len(ordered) >= max_props:
        return ordered[:max_props]

    if known_pages is not None:
        for p in range(2, known_pages + 1):
            if len(ordered) >= max_props:
                break
            html = fetch_url(client, _listing_url_for_page(base, p))
            add_from_html(html)
        return ordered[:max_props]

    p = 2
    while p <= _MAX_LISTING_PAGES and len(ordered) < max_props:
        html = fetch_url(client, _listing_url_for_page(base, p))
        prev_len = len(ordered)
        add_from_html(html)
        if len(ordered) == prev_len:
            break
        p += 1
    return ordered[:max_props]


def _walk(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        keys = set(obj.keys())
        if ("title" in keys or "name" in keys) and any(
            k in keys for k in ("price", "salePrice", "value", "operationPrice", "m2", "area")
        ):
            out.append(obj)
        for v in obj.values():
            out.extend(_walk(v))
    elif isinstance(obj, list):
        for x in obj:
            out.extend(_walk(x))
    return out


def _first_num(*vals: Any) -> float | None:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).replace(".", "").replace(",", ".")
        s = re.sub(r"[^\d.]", "", s)
        if not s:
            continue
        try:
            return float(s)
        except ValueError:
            continue
    return None


def parse_detail(html: str, url: str) -> dict[str, Any] | None:
    ext = _external_id_from_url(url)
    if not ext:
        return None
    soup = BeautifulSoup(html, "html.parser")

    row: dict[str, Any] | None = None
    nd = extract_next_data_json(html)
    if nd:
        page = (nd.get("props") or {}).get("pageProps") or {}
        data_obj = pick_property_data(page)
        if data_obj:
            row = map_property_data_to_row(data_obj, url, ext)

    if row is None:
        script = soup.find("script", id="__NEXT_DATA__")
        raw: dict[str, Any] | None = None
        if script and script.string:
            try:
                data = json.loads(script.string)
                props = data.get("props") or {}
                page = props.get("pageProps") or {}
                candidates = _walk(page)
                raw = candidates[0] if candidates else page
            except json.JSONDecodeError:
                raw = None
        title = None
        price = None
        area = None
        desc = ""
        if raw:
            title = raw.get("title") or raw.get("name")
            price = _first_num(
                raw.get("price"),
                raw.get("salePrice"),
                raw.get("operationPrice"),
                raw.get("value"),
            )
            if isinstance(raw.get("price"), dict):
                price = _first_num(raw["price"].get("amount"), price)
            area = _first_num(raw.get("area"), raw.get("m2"), raw.get("privateArea"), raw.get("builtArea"))
            desc = str(raw.get("description") or raw.get("descripcion") or "")[:8000]
        if not title:
            og = soup.find("meta", property="og:title")
            if og and og.get("content"):
                title = str(og["content"])
        if price is None:
            t = soup.get_text(" ", strip=True)
            pm = re.search(r"\$\s*([\d.]{6,})", t.replace(".", ""))
            if pm:
                price = _first_num(pm.group(1))
        desc_l = (desc or "").lower()
        remodel = any(
            k in desc_l
            for k in ("remodelado", "reformado", "renovado", "recién remodelado", "recien remodelado")
        )
        row = {
            "external_id": ext,
            "platform": "finca_raiz",
            "url": url,
            "title": (title or "Sin título")[:500],
            "price": price,
            "area": area,
            "descripcion": desc or None,
            "es_remodelado": remodel,
            "datos_crudos": raw or {},
        }

    ex = extract_from_description(row.get("descripcion"))
    merge_description_extract(row, ex, fill_if_missing=True)
    patch_ubicacion_from_description_extract(row)
    patch_ubicacion_reverse_geocode(row, get_settings().user_agent)
    enrich_ubicacion_llm_placeholder(row, whitelist_barrios())

    if not row.get("es_remodelado") and row.get("descripcion"):
        d = str(row["descripcion"]).lower()
        if any(
            k in d
            for k in ("remodelado", "reformado", "renovado", "recién remodelado", "recien remodelado")
        ):
            row["es_remodelado"] = True

    return row


def fetch_url(client: httpx.Client, url: str) -> str:
    s = get_settings()
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            r = client.get(url, timeout=60.0)
            if r.status_code in (429, 403):
                time.sleep(2**attempt * 2)
                continue
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_exc = e
            time.sleep(2**attempt)
    raise last_exc or RuntimeError("fetch failed")


def scrape_source(
    client: httpx.Client,
    list_url: str,
    max_props: int,
    delay: float,
) -> list[dict[str, Any]]:
    base = _strip_listing_pagination(list_url)
    first_html = fetch_url(client, _listing_url_for_page(base, 1))
    known_pages = parsed_total_listing_pages(first_html)
    urls = _gather_listing_urls_across_pages(client, base, max_props, first_html, known_pages)
    results: list[dict[str, Any]] = []
    for u in urls:
        time.sleep(delay)
        try:
            dh = fetch_url(client, u)
            row = parse_detail(dh, u)
            if row:
                results.append(row)
        except Exception:
            continue
        if len(results) >= max_props:
            break
    return results
