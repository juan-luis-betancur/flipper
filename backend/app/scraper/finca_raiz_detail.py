"""
Mapeo de pageProps.data (Finca Raíz / Next __NEXT_DATA__) a columnas de properties.
"""

from __future__ import annotations

import re
from typing import Any

from .description_extract import porteria_24h_from_text
from .finca_raiz_age import parse_construction_year_only, parse_fr_antiquity
from .location_snapshot import build_ubicacion_snapshot
from .medellin_neighborhoods import fuzzy_suggest_barrio


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


def _sheet_map(sheet: list[Any] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    if not sheet:
        return out
    for row in sheet:
        if not isinstance(row, dict):
            continue
        k = row.get("field")
        if not k:
            continue
        v = row.get("value")
        if v is None:
            continue
        s = str(v).strip()
        if not s or _is_placeholder(s):
            continue
        out[str(k)] = s
    return out


def _is_placeholder(s: str) -> bool:
    sl = s.lower()
    return "pregúntale" in sl or "preguntale" in sl


def _parse_num(s: str | None) -> float | None:
    if not s:
        return None
    t = re.sub(r"[^\d.,]", "", str(s).replace(".", "").replace(",", "."))
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _parse_int(s: str | float | int | None) -> int | None:
    if s is None:
        return None
    if isinstance(s, (int, float)) and s == s:
        return int(s)
    n = _parse_num(str(s))
    if n is None:
        return None
    return int(round(n))


def _norm_join(names: list[str]) -> str:
    return " ".join(names).lower()


def _facility_booleans(facilities: list[Any] | None) -> dict[str, bool]:
    names: list[str] = []
    if facilities:
        for f in facilities:
            if isinstance(f, dict) and f.get("name"):
                names.append(str(f["name"]))
    j = _norm_join(names)
    p24 = False
    for nm in names:
        if porteria_24h_from_text(nm):
            p24 = True
            break
    if not p24 and j and porteria_24h_from_text(j):
        p24 = True
    return {
        "tiene_ascensor": "ascensor" in j,
        "tiene_porteria": any(
            x in j for x in ("portería", "porteria", "vigilancia", "recepción", "recepcion")
        ),
        "tiene_porteria_24h": p24,
        "tiene_balcon": "balcón" in j or "balcon" in j,
        "tiene_parqueadero": any(
            x in j for x in ("parqueadero", "garaje", "cochera", "estacionamiento")
        ),
        "tiene_gimnasio": "gimnasio" in j,
        "tiene_piscina": "piscina" in j,
        "tiene_cuarto_util": any(
            x in j for x in ("cuarto útil", "cuarto util", "bodega", "depósito", "deposito")
        ),
        "tiene_zona_ropas": any(
            x in j for x in ("zona de ropa", "zona ropa", "lavandería", "lavanderia", "zona de lavandería")
        ),
    }


def _tipo_cocina_from_facilities(facilities: list[Any] | None) -> str | None:
    parts: list[str] = []
    if not facilities:
        return None
    for f in facilities:
        if not isinstance(f, dict):
            continue
        n = str(f.get("name") or "")
        if "cocina" in n.lower():
            parts.append(n)
    if not parts:
        return None
    return ", ".join(parts)[:500]


def pick_property_data(page_props: dict[str, Any]) -> dict[str, Any] | None:
    data = page_props.get("data")
    if isinstance(data, dict) and (data.get("id") is not None or data.get("code")):
        return data
    candidates = _walk(page_props)
    best: dict[str, Any] | None = None
    best_score = -1
    for c in candidates:
        if not isinstance(c, dict):
            continue
        score = len(c)
        if c.get("technicalSheet"):
            score += 80
        if c.get("locations"):
            score += 80
        if c.get("facilities"):
            score += 40
        if c.get("images"):
            score += 20
        if score > best_score:
            best_score = score
            best = c
    return best


def map_property_data_to_row(data: dict[str, Any], url: str, external_id: str) -> dict[str, Any]:
    sheet = _sheet_map(data.get("technicalSheet"))
    facilities = data.get("facilities") if isinstance(data.get("facilities"), list) else []

    title = data.get("title") or data.get("name") or "Sin título"
    desc = str(data.get("description") or "")[:8000] or None

    price_raw = data.get("price")
    price = None
    if isinstance(price_raw, dict):
        price = _first_num(price_raw.get("amount"), price_raw.get("value"))
    else:
        price = _first_num(price_raw, data.get("salePrice"), data.get("operationPrice"))

    area = _first_num(
        data.get("m2"),
        data.get("m2Built"),
        data.get("m2apto"),
        sheet.get("m2Built"),
        sheet.get("m2apto"),
    )
    if area is None:
        area = _parse_num(sheet.get("m2Built") or sheet.get("m2apto") or "")

    area_total = _first_num(data.get("m2Terrain"), data.get("m2Terrace"))
    if area_total is None and sheet.get("m2Terrain"):
        area_total = _parse_num(sheet["m2Terrain"])

    habitaciones = _parse_int(data.get("bedrooms") or data.get("rooms") or sheet.get("bedrooms"))
    banos = _parse_int(data.get("bathrooms") or sheet.get("bathrooms"))
    parqueaderos = _parse_int(data.get("garage") or sheet.get("garage"))

    piso = _parse_int(data.get("floor") or sheet.get("floor"))
    pisos_totales = _parse_int(data.get("floorsCount") or data.get("floorsAmount") or sheet.get("story"))
    if pisos_totales == 0:
        pisos_totales = None

    estrato = _parse_int(data.get("stratum") or sheet.get("stratum"))

    raw_sheet = data.get("technicalSheet") if isinstance(data.get("technicalSheet"), list) else None
    antiguedad_rango, antiguedad_max_anos = parse_fr_antiquity(raw_sheet, sheet, data, desc)

    cy_raw = None
    if raw_sheet:
        for row in raw_sheet:
            if isinstance(row, dict) and str(row.get("field") or "") in (
                "constructionYear",
                "construction_year",
            ):
                v = row.get("value")
                if v is not None and str(v).strip():
                    cy_raw = str(v).strip()
                    break
    if not cy_raw:
        cy_raw = sheet.get("constructionYear") or sheet.get("construction_year")

    ano_construccion = parse_construction_year_only(cy_raw)

    # Compatibilidad con alert_filters.max_age_years (columna legacy `antiguedad`)
    antiguedad = antiguedad_max_anos

    administracion = None
    ce = data.get("commonExpenses")
    if isinstance(ce, dict) and ce.get("amount") is not None:
        administracion = _first_num(ce.get("amount"))
    if administracion is None and sheet.get("commonExpenses"):
        administracion = _parse_num(sheet["commonExpenses"])
    if administracion is not None and administracion == 0:
        administracion = None

    loc = data.get("locations") if isinstance(data.get("locations"), dict) else {}
    neighbourhood_names: list[str] = []
    neigh = loc.get("neighbourhood") or []
    if isinstance(neigh, list):
        for item in neigh:
            if isinstance(item, dict) and item.get("name"):
                neighbourhood_names.append(str(item["name"]).strip())
    barrio = None
    lm = loc.get("location_main")
    if isinstance(lm, dict) and lm.get("name"):
        barrio = str(lm["name"]).strip()
    if not barrio and neighbourhood_names:
        barrio = neighbourhood_names[0]

    zonas: list[str] = []
    for z in loc.get("zone") or []:
        if isinstance(z, dict) and z.get("name"):
            zonas.append(str(z["name"]))
    zona = ", ".join(zonas)[:500] if zonas else None

    ciudad = None
    cities = loc.get("city") or []
    if isinstance(cities, list) and cities:
        c0 = cities[0]
        if isinstance(c0, dict) and c0.get("name"):
            ciudad = str(c0["name"]).strip()

    direccion = (data.get("address") or None) and str(data["address"]).strip() or None

    lat_raw = data.get("latitude")
    lng_raw = data.get("longitude")
    try:
        lat_f = float(lat_raw) if lat_raw is not None else None
        lng_f = float(lng_raw) if lng_raw is not None else None
    except (TypeError, ValueError):
        lat_f = lng_f = None

    fotos: list[str] = []
    for im in data.get("images") or []:
        if isinstance(im, dict) and im.get("image"):
            fotos.append(str(im["image"]))
        if len(fotos) >= 40:
            break

    owner = data.get("owner") if isinstance(data.get("owner"), dict) else {}
    nombre_anunciante = owner.get("name")
    tipo_anunciante = owner.get("type")

    fecha_pub = None
    ca = data.get("created_at") or data.get("updated_at")
    if isinstance(ca, str) and re.match(r"\d{4}-\d{2}-\d{2}", ca):
        fecha_pub = f"{ca}T12:00:00-05:00"

    fb = _facility_booleans(facilities)
    tipo_cocina = _tipo_cocina_from_facilities(facilities)

    desc_l = (desc or "").lower()
    remodel_kw = any(
        k in desc_l
        for k in ("remodelado", "reformado", "renovado", "recién remodelado", "recien remodelado")
    )
    est = (sheet.get("construction_state_name") or "").lower()
    remodel_sheet = "remodel" in est
    es_remodelado = remodel_kw or remodel_sheet

    comodidades = [str(f.get("name")) for f in facilities if isinstance(f, dict) and f.get("name")]

    communes: list[str] = []
    for c in loc.get("commune") or []:
        if isinstance(c, dict) and c.get("name"):
            communes.append(str(c["name"]))

    ubicacion = build_ubicacion_snapshot(
        data=data,
        loc=loc,
        url=url,
        titulo=str(title),
        barrio=barrio,
        zona=zona,
        ciudad=ciudad,
        direccion=direccion,
        latitud=lat_f,
        longitud=lng_f,
        lat_raw=lat_raw,
        lng_raw=lng_raw,
        communes=communes,
        neighbourhood_names=neighbourhood_names,
    )
    ubicacion["schema_version"] = 1
    ubicacion["notas_auditoria"] = (
        "FR `data.locations`: location_main, neighbourhood[], zone[], city[], commune[]. "
        "Coords en `latitude`/`longitude`. Columnas barrio/zona/ciudad = resolución actual MVP."
    )
    if barrio:
        sug = fuzzy_suggest_barrio(barrio)
        if sug and sug != barrio:
            ubicacion["fuzzy_whitelist_sugerencia"] = sug

    row: dict[str, Any] = {
        "external_id": external_id,
        "platform": "finca_raiz",
        "url": url,
        "title": str(title)[:500],
        "price": price,
        "area": area,
        "area_total": area_total,
        "habitaciones": habitaciones,
        "banos": banos,
        "parqueaderos": parqueaderos,
        "piso": piso,
        "pisos_totales": pisos_totales,
        "antiguedad": antiguedad,
        "antiguedad_rango": antiguedad_rango,
        "antiguedad_max_anos": antiguedad_max_anos,
        "estrato": estrato,
        "ano_construccion": ano_construccion,
        "barrio": barrio,
        "zona": zona,
        "ciudad": ciudad,
        "direccion": direccion,
        "latitud": lat_f,
        "longitud": lng_f,
        "administracion": administracion,
        "descripcion": desc,
        "tipo_cocina": tipo_cocina,
        "fotos": fotos or None,
        "nombre_anunciante": nombre_anunciante,
        "tipo_anunciante": tipo_anunciante,
        "fecha_publicacion": fecha_pub,
        "es_remodelado": es_remodelado,
        **fb,
        "datos_crudos": {
            "source": "fincaraiz_next_data",
            "comodidades": comodidades,
            "technical_sheet": sheet,
            "property_type_name": _property_type_label(data, sheet),
            "communes": communes,
            "ubicacion": ubicacion,
        },
    }
    return row


def _property_type_label(data: dict[str, Any], sheet: dict[str, str]) -> str | None:
    pt = data.get("property_type")
    if isinstance(pt, dict) and pt.get("name"):
        return str(pt["name"])
    v = sheet.get("property_type_name")
    return str(v) if v else None


def extract_next_data_json(html: str) -> dict[str, Any] | None:
    """Parse el JSON de script#__NEXT_DATA__ sin depender de BeautifulSoup."""
    import json as _json

    start_tag = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>', html, re.I)
    if not start_tag:
        return None
    start = start_tag.end()
    end = html.lower().find("</script>", start)
    if end < 0:
        return None
    raw = html[start:end].strip()
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        return None
