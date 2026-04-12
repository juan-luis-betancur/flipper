from __future__ import annotations

from typing import Any, Mapping


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)
        return x if x == x else None  # NaN
    except (TypeError, ValueError):
        return None


def property_matches_alert(prop: Mapping[str, Any], filt: Mapping[str, Any]) -> bool:
    """Apply alert_filters row to a property dict (snake_case DB columns)."""
    price = _num(prop.get("price"))
    m2 = _num(prop.get("precio_por_m2"))
    area = _num(prop.get("area"))
    rooms = prop.get("habitaciones")
    baths = prop.get("banos")
    age = prop.get("antiguedad_max_anos")
    if age is None:
        age = prop.get("antiguedad")

    for lo, hi, val in (
        ("price_min", "price_max", price),
        ("price_m2_min", "price_m2_max", m2),
        ("area_min", "area_max", area),
    ):
        mn = _num(filt.get(lo))
        mx = _num(filt.get(hi))
        if mn is None and mx is None:
            continue
        if val is None:
            return False
        if mn is not None and val < mn:
            return False
        if mx is not None and val > mx:
            return False

    rmin = filt.get("rooms_min")
    if rmin is not None and rooms is not None and int(rooms) < int(rmin):
        return False

    bmin = filt.get("baths_min")
    if bmin is not None and baths is not None and int(baths) < int(bmin):
        return False

    amax = filt.get("max_age_years")
    if amax is not None and age is not None and int(age) > int(amax):
        return False

    nb = filt.get("neighborhoods") or []
    if nb and prop.get("barrio") and prop["barrio"] not in nb:
        return False

    req = filt.get("required_features") or []
    # UI guarda "tiene_porteria" pero el checkbox es «Portería 24h» → columna explícita.
    key_map = {
        "tiene_ascensor": "tiene_ascensor",
        "tiene_porteria": "tiene_porteria_24h",
        "tiene_balcon": "tiene_balcon",
        "tiene_parqueadero": "tiene_parqueadero",
    }
    for feat in req:
        col = key_map.get(str(feat))
        if col and not prop.get(col):
            return False

    return True
