"""Reto anti-bot de listado Mercado Libre (_bmstate / PoW / _bmc)."""
from __future__ import annotations

import hashlib
import urllib.parse

import httpx

ML_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9",
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


def fetch_html_after_challenge(client: httpx.Client, url: str) -> str:
    """GET + PoW + segundo GET. Si el HTML ya es listado completo, devuelve al primer intento."""
    r1 = client.get(url)
    if len(r1.text) > 50_000 and "ui-search" in r1.text:
        return r1.text

    bm = get_bmstate_value(client)
    if not bm:
        raise RuntimeError(
            "Mercado Libre: no hay cookie _bmstate. "
            "Configura ML_COOKIE (header Cookie del navegador) o reintenta."
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
