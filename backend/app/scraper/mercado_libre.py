"""Scrape Mercado Libre: listado (PoW + paginación) + detalle por URL."""
from __future__ import annotations

import logging
import os
import time
from typing import Any

from .mercado_libre_detail import fetch_detail_row
from .mercado_libre_list import gather_listing_item_urls, ml_client_with_optional_cookie

log = logging.getLogger(__name__)


def scrape_mercado_libre(list_url: str, max_props: int, delay: float) -> list[dict[str, Any]]:
    """
    Usa el mismo httpx.Client para listado y detalles (cookies _bmstate/_bmc).
    ML_COOKIE en entorno evita PoW si las cookies siguen válidas.
    """
    if not (list_url or "").strip():
        return []
    ml_cookie = os.environ.get("ML_COOKIE")
    results: list[dict[str, Any]] = []

    with ml_client_with_optional_cookie(ml_cookie) as client:
        items = gather_listing_item_urls(client, list_url.strip(), max_props, max_pages=30)
        for it in items:
            if len(results) >= max_props:
                break
            time.sleep(delay)
            try:
                row = fetch_detail_row(client, it["url"])
                if row:
                    results.append(row)
            except Exception:
                log.debug("ML detalle omitido url=%s", it.get("url"), exc_info=True)
                continue
    return results
