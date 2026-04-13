"""Detalle de publicación Mercado Libre (HTML + meta / JSON-LD + bloque ``attributes`` en JSON embebido)."""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any

from bs4 import BeautifulSoup

from .mercado_libre_challenge import fetch_html_after_challenge

log = logging.getLogger(__name__)

_M2_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:m\u00b2|m2|metros?\s*cuadrados?)",
    re.I,
)
_INT_RE = re.compile(r"(\d+)")
_ADMIN_COP_RE = re.compile(r"([\d.]+)\s*(?:COP|cop|\$)")


def _external_id_from_url(url: str) -> str | None:
    m = re.search(r"/(?:MCO|MLC)-(\d+)-", url, re.I)
    return m.group(1) if m else None


def _first_num_from_text(s: str) -> float | None:
    s = re.sub(r"[^\d]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _norm_label(s: str) -> str:
    if not s:
        return ""
    nk = unicodedata.normalize("NFKD", s)
    ascii_s = nk.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", ascii_s).strip()


def _area_m2_from_text(text: str) -> float | None:
    if not text:
        return None
    m = _M2_RE.search(text.replace("m^2", "m2"))
    if m:
        return float(m.group(1).replace(",", "."))
    m2 = _INT_RE.search(text)
    if m2 and "m" in text.lower():
        return float(m2.group(1).replace(",", "."))
    return None


def _int_from_text(text: str) -> int | None:
    if not text:
        return None
    m = _INT_RE.search(text)
    return int(m.group(1)) if m else None


def _administracion_cop(text: str) -> float | None:
    if not text:
        return None
    m = _ADMIN_COP_RE.search(text.replace(" ", ""))
    if not m:
        return _first_num_from_text(text)
    raw = m.group(1).replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_all_ml_attribute_items(html: str) -> list[dict[str, Any]]:
    """
    Une todas las apariciones de ``"attributes":[{ "id": "...", "text": "..." }, ...]``
    (Principales, Comodidades, Ambientes, etc.). Evita duplicados exactos ``(id, text)``.
    """
    needle = '"attributes":['
    decoder = json.JSONDecoder()
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    pos = 0
    while True:
        i = html.find(needle, pos)
        if i == -1:
            break
        start = i + len(needle) - 1
        if start >= len(html) or html[start] != "[":
            start = html.find("[", i, min(i + 40, len(html)))
        if start == -1:
            pos = i + 1
            continue
        try:
            arr, _ = decoder.raw_decode(html, start)
        except json.JSONDecodeError:
            pos = i + 1
            continue
        if not isinstance(arr, list) or not arr:
            pos = i + 1
            continue
        first = arr[0]
        if not isinstance(first, dict) or "id" not in first or "text" not in first:
            pos = i + 1
            continue
        for it in arr:
            if not isinstance(it, dict):
                continue
            rid = str(it.get("id", "")).strip()
            txt = str(it.get("text", "")).strip()
            if not rid:
                continue
            key = (rid, txt)
            if key in seen:
                continue
            seen.add(key)
            out.append({"id": rid, "text": txt})
        pos = i + 1
    return out


def _is_si_value(text: str) -> bool:
    """True solo para respuestas afirmativas explícitas (no números ni ``m``)."""
    n = _norm_label(text)
    if not n:
        return False
    if n in ("si", "yes", "true"):
        return True
    if len(n) == 1 and n == "s":
        return True
    return n.startswith("si ") or n.startswith("s ")


def _technical_sheet_display(items: list[dict[str, Any]]) -> dict[str, str]:
    """Misma idea que FR ``technical_sheet``: etiqueta legible -> valor (último gana si hay colisión)."""
    sheet: dict[str, str] = {}
    for it in items:
        rid = str(it.get("id", "")).strip()
        txt = str(it.get("text", "")).strip()
        if rid:
            sheet[rid] = txt
    return sheet


def _comodidades_si_labels(items: list[dict[str, Any]]) -> list[str]:
    """Lista de nombres de atributo con respuesta afirmativa (como ``comodidades`` en FR)."""
    out: list[str] = []
    seen: set[str] = set()
    for it in items:
        rid = str(it.get("id", "")).strip()
        txt = str(it.get("text", "")).strip()
        if not rid or not _is_si_value(txt):
            continue
        if rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out


def _apply_tiene_flags_from_specs(specs: dict[str, str], partial: dict[str, Any]) -> None:
    """Mapea filas Sí a columnas ``tiene_*`` cuando hay equivalente claro."""
    for key, val in specs.items():
        if not _is_si_value(val):
            continue
        if "balcon" in key or "balcn" in key:
            partial["tiene_balcon"] = True
        if "piscina" in key:
            partial["tiene_piscina"] = True
        if "gimnasio" in key:
            partial["tiene_gimnasio"] = True
        if "ascensor" in key:
            partial["tiene_ascensor"] = True
        if "porter" in key or "vigilancia" in key or "recepcin" in key or "recepcion" in key:
            partial["tiene_porteria"] = True
        if "lavander" in key or "zona de ropa" in key or "ropas" in key:
            partial["tiene_zona_ropas"] = True
        if "parqueadero" in key or "estacionamiento" in key or "garaje" in key:
            partial["tiene_parqueadero"] = True


def _specs_dict_from_attributes(arr: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for it in arr:
        if not isinstance(it, dict):
            continue
        k = _norm_label(str(it.get("id", "")))
        v = str(it.get("text", "")).strip()
        if k:
            out[k] = v
    return out


def _value_for_keys(specs: dict[str, str], *substrings: str) -> str | None:
    for key, val in specs.items():
        for sub in substrings:
            if sub in key:
                return val
    return None


def _merge_specs_into_partial(specs: dict[str, str], partial: dict[str, Any]) -> None:
    """Rellena claves alineadas a ``public.properties``."""
    area_c = _value_for_keys(specs, "construi", "construida")
    area_t = _value_for_keys(specs, "total")
    for candidate in (area_c, area_t):
        if candidate:
            m2 = _area_m2_from_text(candidate)
            if m2 is not None:
                partial["area"] = m2
                break

    hab = _value_for_keys(specs, "habitacion")
    if hab:
        h = _int_from_text(hab)
        if h is not None:
            partial["habitaciones"] = h

    ban = _value_for_keys(specs, "bano", "baos")
    if ban:
        b = _int_from_text(ban)
        if b is not None:
            partial["banos"] = b

    est = _value_for_keys(specs, "estacionamiento", "parqueadero")
    if est:
        p = _int_from_text(est)
        if p is not None:
            partial["parqueaderos"] = p

    dep = _value_for_keys(specs, "deposito", "depsito")
    if dep:
        d = _int_from_text(dep)
        if d is not None and d > 0:
            partial["tiene_cuarto_util"] = True

    estr = _value_for_keys(specs, "estrato")
    if estr:
        e = _int_from_text(estr)
        if e is not None:
            partial["estrato"] = e

    anti = _value_for_keys(specs, "antigedad", "antig")
    if anti:
        partial["antiguedad_rango"] = anti[:120]
        years = _int_from_text(anti)
        if years is not None and years <= 120:
            partial["antiguedad"] = years

    adm = _value_for_keys(specs, "administraci", "administracin")
    if adm:
        ac = _administracion_cop(adm)
        if ac is not None:
            partial["administracion"] = ac


def _attribute_items_from_table(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Respaldo: filas ``andes-table`` (misma semántica id/text que el JSON)."""
    items: list[dict[str, str]] = []
    for row in soup.select("tr.andes-table__row"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(" ", strip=True)
        val = cells[1].get_text(" ", strip=True)
        if not label or not val:
            continue
        items.append({"id": label, "text": val})
    return items


def _apply_items_to_partial(items: list[dict[str, Any]], partial: dict[str, Any]) -> None:
    specs = _specs_dict_from_attributes(items)
    _merge_specs_into_partial(specs, partial)
    _apply_tiene_flags_from_specs(specs, partial)
    dc = partial.setdefault("datos_crudos", {})
    dc["technical_sheet"] = _technical_sheet_display(items)
    dc["comodidades"] = _comodidades_si_labels(items)
    dc["ml_attributes"] = items[:400]


def _apply_breadcrumb_to_row(soup: BeautifulSoup, partial: dict[str, Any]) -> None:
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string or "BreadcrumbList" not in script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("@type") != "BreadcrumbList":
            continue
        items = data.get("itemListElement") or []
        names: list[str] = []
        for el in items:
            if not isinstance(el, dict):
                continue
            it = el.get("item") or {}
            if isinstance(it, dict):
                n = it.get("name")
                if isinstance(n, str) and n.strip():
                    names.append(n.strip())
        if not names:
            continue
        # típico: Inmuebles, Venta, Antioquia, Medellín, El Poblado, ...
        skip = {"inmuebles", "venta", "arriendo", "apartamentos", "casas"}
        loc = [n for n in names if _norm_label(n) not in skip]
        if len(loc) >= 2:
            partial["barrio"] = loc[-1][:120]
            partial["ciudad"] = loc[-2][:120]
        elif len(loc) == 1:
            partial["ciudad"] = loc[0][:120]
        if len(loc) >= 3:
            partial["zona"] = loc[-3][:120]
        return


def parse_detail_html(html: str, url: str) -> dict[str, Any] | None:
    ext = _external_id_from_url(url)
    if not ext:
        return None
    soup = BeautifulSoup(html, "html.parser")

    title = None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = str(og["content"]).strip()
    if not title:
        t = soup.find("title")
        if t and t.string:
            title = t.string.strip()

    price: float | None = None
    ogd = soup.find("meta", itemprop="price") or soup.find("meta", property="product:price:amount")
    if ogd and ogd.get("content"):
        price = _first_num_from_text(str(ogd["content"]))
    if price is None:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                off = data.get("offers")
                if isinstance(off, dict) and "price" in off:
                    price = _first_num_from_text(str(off["price"]))
                    break

    desc = None
    ogdesc = soup.find("meta", property="og:description")
    if ogdesc and ogdesc.get("content"):
        desc = str(ogdesc["content"])[:8000]

    items: list[dict[str, Any]] = []
    try:
        items = _extract_all_ml_attribute_items(html)
    except Exception:
        log.debug("ML attributes JSON: error", exc_info=True)

    partial: dict[str, Any] = {
        "external_id": ext,
        "platform": "mercado_libre",
        "url": url.split("#")[0],
        "title": (title or "Sin título")[:500],
        "price": price,
        "descripcion": desc,
        "es_remodelado": False,
        "datos_crudos": {"source": "mercado_libre_html"},
    }

    if not items:
        items = _attribute_items_from_table(soup)

    if items:
        try:
            _apply_items_to_partial(items, partial)
        except Exception:
            log.debug("ML merge specs / datos_crudos", exc_info=True)

    _apply_breadcrumb_to_row(soup, partial)

    if partial.get("area") is None:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                # algunas fichas añaden additionalProperty en el futuro
                add = data.get("additionalProperty")
                if isinstance(add, list):
                    for p in add:
                        if not isinstance(p, dict):
                            continue
                        n = str(p.get("name", ""))
                        v = str(p.get("value", ""))
                        if _norm_label(n) in ("superficie", "area", "metros"):
                            m2 = _area_m2_from_text(v)
                            if m2 is not None:
                                partial["area"] = m2
                                break

    return partial


def fetch_detail_row(client: Any, url: str) -> dict[str, Any] | None:
    html = fetch_html_after_challenge(client, url)
    if len(html) < 2000 and "verifyChallenge" in html:
        return None
    return parse_detail_html(html, url)
