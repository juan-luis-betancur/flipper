"""Reto anti-bot de listado Mercado Libre (_bmstate / PoW / _bmc)."""
from __future__ import annotations

import hashlib
import logging
import re
import time
import urllib.parse
from typing import Any

import httpx  # noqa: F401  # retrocompat: tipos existentes en otros módulos

log = logging.getLogger(__name__)

# URL inequívoca de publicación ML Colombia. Si aparece al menos una vez en el
# HTML, la página trae listados reales (no es soft-block con Andes chrome vacío).
_MCO_ITEM_IN_HTML_RE = re.compile(
    r"https://[a-z0-9.-]+\.mercadolibre\.com\.co/MCO-\d+-", re.I
)

# Muros anti-bot de ML. Vienen con status 200 y ~25-60KB, así que no los delata
# ni el status ni el tamaño: hay que reconocerlos por el bundle de frontend que
# sirven. ``abuse-captcha`` es el CAPTCHA; ``suspicious-traffic`` pide login.
_WALL_MARKERS = ("abuse-captcha", "suspicious-traffic", "verifychallenge")


class MercadoLibreWall(RuntimeError):
    """ML respondió con un muro anti-bot en lugar de la página pedida.

    Es transitorio y depende de la IP: reintentar con una sesión nueva (que el
    proxy residencial resuelve a otra IP) suele pasar en pocos intentos.
    """


def looks_like_wall(html: str) -> bool:
    """True si ML devolvió un muro anti-bot en vez de la página pedida."""
    if not html:
        return True
    low = html.lower()
    return any(m in low for m in _WALL_MARKERS)


# La versión de Chrome debe coincidir con el ``impersonate`` de curl_cffi
# (ver ml_client_with_optional_cookie). Un Chrome real nunca se contradice entre
# huella TLS, User-Agent y Sec-Ch-Ua; esa incoherencia es señal de bot.
CHROME_MAJOR = "124"

ML_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{CHROME_MAJOR}.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": (
        f'"Chromium";v="{CHROME_MAJOR}", "Google Chrome";v="{CHROME_MAJOR}", '
        '"Not-A.Brand";v="99"'
    ),
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}


def get_bmstate_value(client: Any) -> str | None:
    # curl_cffi/requests exponen `client.cookies` como RequestsCookieJar iterable
    # de objetos Cookie con .name/.value/.domain. httpx usa `client.cookies.jar`.
    jar = getattr(client.cookies, "jar", client.cookies)
    for cookie in jar:
        if cookie.name == "_bmstate" and "mercadolibre" in (cookie.domain or ""):
            return cookie.value
    return None


def solve_bmstate_pow(token: str, difficulty_raw: str) -> int:
    """Menor a >= 0 tal que hex(SHA256(token + str(a))) empieza con N ceros (como el JS del sitio)."""
    if str(difficulty_raw).strip() in ("", "0"):
        return 0
    n = int(difficulty_raw)
    prefix = "0" * n
    for a in range(100_000_000):
        digest = hashlib.sha256((token + str(a)).encode()).hexdigest()
        if digest.startswith(prefix):
            return a
    raise RuntimeError("PoW Mercado Libre: no se encontró solución en rango razonable")


def apply_bmc_cookie(client: Any, token: str, a: int) -> None:
    val = urllib.parse.quote(f"{token};{a}")
    client.cookies.set("_bmc", val, domain=".mercadolibre.com.co", path="/")


def fetch_html_after_challenge(
    client: Any,
    url: str,
    *,
    max_attempts: int = 4,
    retry_delay: float = 3.5,
) -> str:
    """GET + PoW + segundo GET. Reintenta el primer GET si ML no setea _bmstate."""
    bm: str | None = None
    last_status: int | None = None
    last_len: int = 0

    is_listing = "/_Desde_" in url or "listado.mercadolibre" in url
    for attempt in range(1, max_attempts + 1):
        r1 = client.get(url)
        last_status = r1.status_code
        body = r1.text
        last_len = len(body)
        # Señales duras de "página real":
        # - Listados: al menos una URL /MCO-\d+- (item real) o "ui-search".
        # - Detalles: "ui-pdp" / "andes-money-amount" o meta product:price.
        if last_len > 50_000:
            has_items = bool(_MCO_ITEM_IN_HTML_RE.search(body))
            if is_listing and (has_items or "ui-search" in body):
                log.info("ML fetch ok url=%s status=%s len=%s items_marker=%s",
                         url, last_status, last_len, has_items)
                return body
            if not is_listing and any(
                m in body for m in ("ui-pdp", "andes-money-amount", 'property="product:price:amount"')
            ):
                return body
        bm = get_bmstate_value(client)
        log.info(
            "ML fetch intermedio url=%s attempt=%s status=%s len=%s bmstate=%s",
            url, attempt, last_status, last_len, bool(bm),
        )
        if bm:
            break
        if attempt < max_attempts:
            time.sleep(retry_delay * attempt)

    if not bm:
        raise MercadoLibreWall(
            f"Mercado Libre: no hay cookie _bmstate tras {max_attempts} intentos "
            f"(último status={last_status}, html_len={last_len})."
        )

    raw = urllib.parse.unquote(bm)
    parts = raw.split(";")
    if len(parts) < 2:
        raise RuntimeError(f"_bmstate inesperado: {raw[:80]}…")
    token, diff = parts[0], parts[1]
    a = solve_bmstate_pow(token, diff)
    apply_bmc_cookie(client, token, a)
    r2 = client.get(url)
    body2 = r2.text
    log.info(
        "ML fetch post-PoW url=%s status=%s len=%s has_mco=%s",
        url, r2.status_code, len(body2),
        bool(_MCO_ITEM_IN_HTML_RE.search(body2)),
    )
    # Resolver el PoW no garantiza pasar: ML puede responder con el muro de
    # CAPTCHA igualmente. Devolverlo como si fuera bueno es lo que hacía que el
    # scraper reportara 0 propiedades en silencio.
    if looks_like_wall(body2):
        raise MercadoLibreWall(
            f"Mercado Libre respondió con muro anti-bot tras resolver el PoW "
            f"(status={r2.status_code}, len={len(body2)})."
        )
    return body2
