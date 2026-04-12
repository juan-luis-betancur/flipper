"""
Snapshot de ubicación en `datos_crudos.ubicacion` para trazabilidad y capas futuras (fuzzy, geocode, LLM).
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

# Claves de `data` (Finca Raíz) relevantes para auditoría de ubicación.
_DATA_LOCATION_TOP_KEYS = frozenset(
    {
        "latitude",
        "longitude",
        "address",
        "locations",
        "showAddress",
        "country_id",
    }
)


def json_safe(value: Any) -> Any:
    """Convierte a tipos serializables en JSON (aprox.)."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(x) for x in value]
    return str(value)[:2000]


def build_ubicacion_snapshot(
    *,
    data: dict[str, Any],
    loc: dict[str, Any],
    url: str,
    titulo: str,
    barrio: str | None,
    zona: str | None,
    ciudad: str | None,
    direccion: str | None,
    latitud: float | None,
    longitud: float | None,
    lat_raw: Any,
    lng_raw: Any,
    communes: list[str],
    neighbourhood_names: list[str],
) -> dict[str, Any]:
    """Arma el dict `ubicacion` persistido en `datos_crudos`."""
    lm = loc.get("location_main")
    location_main_raw = json_safe(lm) if isinstance(lm, dict) else None

    data_loc_audit = {k: json_safe(data.get(k)) for k in sorted(_DATA_LOCATION_TOP_KEYS) if k in data}

    return {
        "platform": "finca_raiz",
        "url": url,
        "titulo": titulo[:500] if titulo else None,
        "direccion_api": direccion,
        "show_address": data.get("showAddress"),
        "country_id": data.get("country_id"),
        "latitud_api_raw": json_safe(lat_raw),
        "longitud_api_raw": json_safe(lng_raw),
        "latitud_resuelta": latitud,
        "longitud_resuelta": longitud,
        "barrio_resuelto": barrio,
        "zona_resuelta": zona,
        "ciudad_resuelta": ciudad,
        "communes": list(communes),
        "fr_neighbourhood_names": list(neighbourhood_names),
        "fr_location_main": location_main_raw,
        "fr_locations": json_safe(loc),
        "fr_locations_keys": sorted(str(k) for k in loc.keys()),
        "data_location_top_level": data_loc_audit,
        "descripcion_extract": {},
    }


def patch_ubicacion_from_description_extract(row: dict[str, Any]) -> None:
    """Copia pistas de `description_extract` al snapshot `ubicacion`."""
    dc = row.get("datos_crudos")
    if not isinstance(dc, dict):
        return
    ub = dc.get("ubicacion")
    if not isinstance(ub, dict):
        return
    ex = dc.get("description_extract")
    if not isinstance(ex, dict):
        return
    keys = (
        "ciudad_desde_descripcion",
        "sector_desde_descripcion",
        "edificio_desde_descripcion",
        "piso_desde_descripcion",
    )
    ub["descripcion_extract"] = {k: ex[k] for k in keys if k in ex}


def patch_ubicacion_reverse_geocode(row: dict[str, Any], user_agent: str) -> None:
    """
    Si REVERSE_GEOCODE_ENABLED=1 y hay coords, llama Nominatim y guarda resultado en ubicacion.
    Uso responsable: User-Agent identificable; respeta política de uso de OSM.
    """
    if os.getenv("REVERSE_GEOCODE_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    dc = row.get("datos_crudos")
    if not isinstance(dc, dict):
        return
    ub = dc.get("ubicacion")
    if not isinstance(ub, dict):
        return
    lat = ub.get("latitud_resuelta")
    lng = ub.get("longitud_resuelta")
    if lat is None or lng is None:
        return
    try:
        la = float(lat)
        lo = float(lng)
    except (TypeError, ValueError):
        return

    try:
        import httpx

        r = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": la, "lon": lo, "format": "json", "accept-language": "es"},
            headers={"User-Agent": user_agent or "FlipperMVP/1.0 (reverse-geocode)"},
            timeout=15.0,
        )
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:  # noqa: BLE001
        ub["reverse_geocode"] = {"error": str(exc)[:500]}
        return

    addr = payload.get("address") if isinstance(payload.get("address"), dict) else {}
    ub["reverse_geocode"] = {
        "display_name": (payload.get("display_name") or "")[:500] if isinstance(payload.get("display_name"), str) else None,
        "address": json_safe(addr),
        "osm_type": payload.get("osm_type"),
        "osm_id": payload.get("osm_id"),
    }
