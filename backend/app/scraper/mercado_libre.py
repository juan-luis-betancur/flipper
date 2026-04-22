"""Scrape Mercado Libre: listado (PoW + paginación) + detalle por URL."""
from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

from .mercado_libre_detail import fetch_detail_row
from .mercado_libre_list import gather_listing_item_urls, ml_client_with_optional_cookie

log = logging.getLogger(__name__)

# Señales de bloqueo por IP/Akamai. Si aparecen en las primeras páginas, tiramos un
# error explícito en lugar de devolver 0 propiedades silenciosamente.
_BLOCK_SIGNALS = (
    "Access Denied",
    "Acceso denegado",
    "Bot Manager",
    "Request blocked",
    "unusual traffic",
)


def _looks_blocked(html: str) -> bool:
    if not html:
        return True
    if len(html) < 5000:
        # ML devuelve ~500KB para listados reales; HTML enano = challenge/bloqueo.
        return True
    low = html.lower()
    return any(sig.lower() in low for sig in _BLOCK_SIGNALS)


def scrape_mercado_libre(list_url: str, max_props: int, delay: float) -> list[dict[str, Any]]:
    """
    Usa el mismo httpx.Client para listado y detalles (cookies _bmstate/_bmc).
    ML_COOKIE en entorno evita PoW si las cookies siguen válidas.
    ML_PROXY_URL (residencial) se aplica dentro de ml_client_with_optional_cookie.
    """
    if not (list_url or "").strip():
        return []
    ml_cookie = os.environ.get("ML_COOKIE")
    results: list[dict[str, Any]] = []

    with ml_client_with_optional_cookie(ml_cookie) as client:
        items = gather_listing_item_urls(client, list_url.strip(), max_props, max_pages=30)
        if not items:
            # Probar una vez más el fetch directo para detectar bloqueo claro.
            try:
                probe = client.get(list_url.strip()).text
            except Exception:  # noqa: BLE001
                probe = ""
            if _looks_blocked(probe):
                raise RuntimeError(
                    "Mercado Libre: IP bloqueada o challenge no resuelto "
                    "(HTML vacío/denegado). Configura ML_PROXY_URL con un proxy "
                    "residencial (Decodo/IPRoyal/Bright Data) o ML_COOKIE con la "
                    "cookie del navegador."
                )
            return []

        for it in items:
            if len(results) >= max_props:
                break
            # Jitter: ±50% del delay para romper patrón de timing uniforme.
            sleep_for = max(0.0, delay + random.uniform(-delay * 0.3, delay * 0.5))
            time.sleep(sleep_for)
            try:
                row = fetch_detail_row(client, it["url"])
                if row:
                    results.append(row)
            except Exception:
                log.debug("ML detalle omitido url=%s", it.get("url"), exc_info=True)
                continue
    return results
