"""
Heurísticas sobre la descripción (ES). Resultado en datos_crudos y relleno
selectivo cuando falten datos estructurados.

Reservado: enrich_description_with_llm para un agente LLM futuro.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm_extract(s: str) -> str:
    return _strip_accents(str(s).strip().lower())


def porteria_24h_from_text(text: str | None) -> bool:
    """
    Heurística ES: portería / vigilancia / recepción / conserjería 24h, 24/7, etc.
    Evita coincidencias sueltas tipo «calle 24» sin contexto de portería.
    """
    if not text or not str(text).strip():
        return False
    n = _norm_extract(text)
    # Token «24 horas» / 24h / 24/7 (tras _norm, tildes ya quitadas).
    tok24 = (
        r"(?:24/7|24x7|24\s*\*\s*7|24-7|"
        r"\b24\s*horas\b|las\s+24\s*horas|24hrs|\b24h\b)"
    )
    concierge = r"(?:porteria|vigilancia|recepcion|conserjeria|conserje|porteros)"
    if re.search(rf"{concierge}.{{0,50}}?{tok24}", n, re.I):
        return True
    if re.search(rf"{tok24}.{{0,50}}?{concierge}", n, re.I):
        return True
    if re.search(r"(?:porteria|recepcion|vigilancia)\s*24\b", n, re.I):
        return True
    return False


def extract_from_description(text: str | None) -> dict[str, Any]:
    if not text or not str(text).strip():
        return {}
    low = _strip_accents(str(text).strip().lower())
    out: dict[str, Any] = {}

    m = re.search(r"\ben\s+([a-záéíóúñ]{3,})\b", low, re.I)
    if m:
        frag = m.group(1)
        if frag not in ("el", "la", "los", "las", "un", "una", "este", "esta", "pleno", "hermoso", "venta", "arriendo"):
            out["ciudad_desde_descripcion"] = m.group(1).title()

    m = re.search(r"sector\s+([^,.;]+)", low, re.I)
    if m:
        out["sector_desde_descripcion"] = m.group(1).strip().title()

    m = re.search(r"edificio\s+([^,.;]+)", low, re.I)
    if m:
        out["edificio_desde_descripcion"] = m.group(1).strip().title()

    m = re.search(r"\bpiso\s*(\d{1,2})\b", low, re.I)
    if m:
        try:
            out["piso_desde_descripcion"] = int(m.group(1))
        except ValueError:
            pass

    if porteria_24h_from_text(str(text)):
        out["porteria_24_desde_descripcion"] = True

    if "domotiz" in low or "domotic" in low:
        out["menciona_domotica"] = True

    return out


def merge_description_extract(
    row: dict[str, Any],
    extract: dict[str, Any],
    *,
    fill_if_missing: bool = True,
) -> None:
    if not extract:
        return
    dc = row.get("datos_crudos")
    if not isinstance(dc, dict):
        dc = {}
    dc["description_extract"] = extract
    row["datos_crudos"] = dc

    if not fill_if_missing:
        return

    if extract.get("porteria_24_desde_descripcion"):
        row["tiene_porteria_24h"] = True

    piso_d = extract.get("piso_desde_descripcion")
    if piso_d is not None and row.get("piso") is None:
        row["piso"] = int(piso_d)

    if extract.get("sector_desde_descripcion") and not row.get("zona"):
        row["zona"] = str(extract["sector_desde_descripcion"])[:200]

    if extract.get("ciudad_desde_descripcion") and not row.get("ciudad"):
        row["ciudad"] = str(extract["ciudad_desde_descripcion"])[:120]


def enrich_description_with_llm(_text: str) -> dict[str, Any]:
    return {}
