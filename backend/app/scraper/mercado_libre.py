"""Scrape Mercado Libre: listado (PoW + paginación) + detalle por URL."""
from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

from .mercado_libre_challenge import MercadoLibreWall
from .mercado_libre_detail import fetch_detail_row
from .mercado_libre_list import gather_listing_item_urls, ml_client_with_optional_cookie

log = logging.getLogger(__name__)

# Cuántas sesiones nuevas probar antes de rendirse. Cada sesión sale por una IP
# residencial distinta del proxy. La tasa de éxito medida contra ML en agosto de
# 2026 rondó el 3-5% por intento, así que hacen falta bastantes: con 25 intentos
# la probabilidad acumulada queda en ~70%. Ajustable sin desplegar vía
# ML_MAX_SESSION_ATTEMPTS por si ML endurece o afloja.
_MAX_SESSION_ATTEMPTS = int(os.getenv("ML_MAX_SESSION_ATTEMPTS", "25"))

# Espera entre intentos. Corta a propósito: el cuello de botella es encontrar una
# IP limpia, no la paciencia de ML con una IP ya marcada.
_SESSION_RETRY_DELAY = float(os.getenv("ML_SESSION_RETRY_DELAY", "4.0"))


def _listado_con_reintentos(
    list_url: str, max_props: int, ml_cookie: str | None
) -> tuple[Any, list[dict[str, str]]]:
    """Consigue el listado probando sesiones nuevas hasta caer en una IP limpia.

    Devuelve ``(client, items)`` con el cliente que logró pasar, para reutilizar
    sus cookies al pedir los detalles. Lanza ``MercadoLibreWall`` si ninguna
    sesión pasa: nunca devuelve vacío en silencio.
    """
    ultimo_motivo = "sin detalle"

    for intento in range(1, _MAX_SESSION_ATTEMPTS + 1):
        client = ml_client_with_optional_cookie(ml_cookie)
        try:
            items = gather_listing_item_urls(client, list_url, max_props, max_pages=30)
        except MercadoLibreWall as e:
            ultimo_motivo = str(e)
            log.info("ML listado intento %s/%s: muro anti-bot (%s)",
                     intento, _MAX_SESSION_ATTEMPTS, e)
            client.close()
        else:
            if items:
                log.info("ML listado ok en intento %s/%s: %s ítems",
                         intento, _MAX_SESSION_ATTEMPTS, len(items))
                return client, items
            # Sin muro y sin ítems: la página cargó pero venía vacía. Puede ser
            # un listado realmente sin resultados, así que no insistimos.
            log.info("ML listado intento %s: página válida sin ítems", intento)
            return client, []

        if intento < _MAX_SESSION_ATTEMPTS:
            time.sleep(_SESSION_RETRY_DELAY + random.uniform(0, 2.0))

    raise MercadoLibreWall(
        f"Mercado Libre bloqueó las {_MAX_SESSION_ATTEMPTS} sesiones intentadas "
        f"(muro anti-bot en todas). Último motivo: {ultimo_motivo}"
    )


def scrape_mercado_libre(list_url: str, max_props: int, delay: float) -> list[dict[str, Any]]:
    """
    Usa el mismo cliente para listado y detalles (cookies _bmstate/_bmc).
    ML_COOKIE en entorno evita PoW si las cookies siguen válidas.
    ML_PROXY_URL (residencial) se aplica dentro de ml_client_with_optional_cookie.

    ML responde con muro anti-bot a la mayoría de IPs, así que el listado se
    reintenta con sesiones nuevas (cada una sale por otra IP del proxy) hasta
    dar con una que pase.
    """
    if not (list_url or "").strip():
        return []
    ml_cookie = os.environ.get("ML_COOKIE")
    results: list[dict[str, Any]] = []

    client, items = _listado_con_reintentos(list_url.strip(), max_props, ml_cookie)
    try:
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
    finally:
        client.close()

    return results
