"""Reto anti-bot de listado Mercado Libre (_bmstate / PoW / _bmc)."""
from __future__ import annotations

import hashlib
import time
import urllib.parse

import httpx

ML_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}


def get_bmstate_value(client: httpx.Client) -> str | None:
    for cookie in client.cookies.jar:
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


def apply_bmc_cookie(client: httpx.Client, token: str, a: int) -> None:
    val = urllib.parse.quote(f"{token};{a}")
    client.cookies.set("_bmc", val, domain=".mercadolibre.com.co", path="/")


def fetch_html_after_challenge(
    client: httpx.Client,
    url: str,
    *,
    max_attempts: int = 4,
    retry_delay: float = 3.5,
) -> str:
    """GET + PoW + segundo GET. Reintenta el primer GET si ML no setea _bmstate."""
    bm: str | None = None
    last_status: int | None = None
    last_len: int = 0

    for attempt in range(1, max_attempts + 1):
        r1 = client.get(url)
        last_status = r1.status_code
        last_len = len(r1.text)
        # Señales de "página real" que ML cambia con frecuencia:
        # - listado: aparece "ui-search" (class legacy) o "andes-pagination" (Andes DS)
        #   o URLs tipo "mercadolibre.com.co/MCO-\d+" (items en el HTML).
        # - detalle: "ui-pdp" (class legacy) o "andes-money-amount" (precio Andes).
        if last_len > 50_000 and any(
            marker in r1.text
            for marker in (
                "ui-search",
                "andes-pagination",
                "ui-pdp",
                "andes-money-amount",
                "mercadolibre.com.co/MCO-",
            )
        ):
            return r1.text
        bm = get_bmstate_value(client)
        if bm:
            break
        if attempt < max_attempts:
            time.sleep(retry_delay * attempt)

    if not bm:
        raise RuntimeError(
            f"Mercado Libre: no hay cookie _bmstate tras {max_attempts} intentos "
            f"(último status={last_status}, html_len={last_len}). "
            "Configura ML_COOKIE (header Cookie del navegador) o reintenta más tarde."
        )

    raw = urllib.parse.unquote(bm)
    parts = raw.split(";")
    if len(parts) < 2:
        raise RuntimeError(f"_bmstate inesperado: {raw[:80]}…")
    token, diff = parts[0], parts[1]
    a = solve_bmstate_pow(token, diff)
    apply_bmc_cookie(client, token, a)
    r2 = client.get(url)
    return r2.text
