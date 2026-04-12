"""
Antigüedad Finca Raíz: rango (texto UI) y límite superior numérico para filtros.
Rangos: Menor a 1 año (1), De 1 a 8 (8), De 9 a 15 (15), De 16 a 30 (30), Más de 30 (45).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm(s: str) -> str:
    return _strip_accents(s.lower().strip())


def match_antiquity_range(text: str | None) -> tuple[str | None, int | None] | None:
    """
    Si el texto coincide con un rango conocido de FR, devuelve (etiqueta_canónica, max_años).
    """
    if not text or not str(text).strip():
        return None
    n = _norm(str(text))

    # Rangos acotados primero: evita que "30 años" dentro de "De 16 a 30 años" dispare +30.
    if "de 16 a 30" in n or "16 a 30" in n:
        return ("De 16 a 30 años", 30)
    if "de 9 a 15" in n or "9 a 15" in n:
        return ("De 9 a 15 años", 15)
    if "de 1 a 8" in n or "1 a 8" in n:
        return ("De 1 a 8 años", 8)
    # Tras _norm(), "año(s)" pasa a "ano(s)"; evitar "menor a 12…" con límite en el 1.
    if re.search(r"menor\s+a\s+1(?!\d)", n) and ("año" in n or "ano" in n):
        return ("Menor a 1 año", 1)
    if re.match(r"^0\s*(años?|anos?)?$", n) or n == "0":
        return ("Menor a 1 año", 1)
    if re.search(r"mas\s+de\s+30|más\s+de\s+30|\+\s*30", n):
        return ("Más de 30 años", 45)

    return None


def _technical_antiquity_value(technical_sheet: list[Any] | None) -> str | None:
    """Valor crudo de ficha: field constructionYear o fila cuyo text mencione Antigüedad."""
    if not technical_sheet:
        return None
    for row in technical_sheet:
        if not isinstance(row, dict):
            continue
        field = str(row.get("field") or "")
        text = str(row.get("text") or "")
        val = row.get("value")
        if val is None:
            continue
        s = str(val).strip()
        if not s:
            continue
        sl = s.lower()
        if "pregúntale" in sl or "preguntale" in sl:
            continue
        if field in ("constructionYear", "construction_year", "antiquity"):
            return s
        if "antigüedad" in text.lower() or "antiguedad" in text.lower():
            return s
    return None


def parse_fr_antiquity(
    technical_sheet: list[Any] | None,
    sheet_flat: dict[str, str],
    data: dict[str, Any],
    descripcion: str | None,
) -> tuple[str | None, int | None]:
    """
    Devuelve (antiguedad_rango, antiguedad_max_anos).
    Prioridad: texto ficha → descripción → número data.antiquity (sin inventar rango).
    """
    candidates: list[str] = []
    tv = _technical_antiquity_value(technical_sheet)
    if tv:
        candidates.append(tv)
    cy = sheet_flat.get("constructionYear") or sheet_flat.get("construction_year")
    if cy and cy not in candidates:
        candidates.append(cy)

    for c in candidates:
        m = match_antiquity_range(c)
        if m:
            return m

    if descripcion:
        nd = _norm(descripcion)
        for m in re.finditer(
            r"(menor\s+a\s+1\s+ano|de\s+1\s+a\s+8|de\s+9\s+a\s+15|de\s+16\s+a\s+30|mas\s+de\s+30)",
            nd,
            re.I,
        ):
            m2 = match_antiquity_range(m.group(0))
            if m2:
                return m2

    # Valor numérico API sin rango explícito
    aq = data.get("antiquity")
    if aq is not None and str(aq).strip() != "":
        try:
            n = int(float(aq))
        except (TypeError, ValueError):
            n = None
        if n is not None:
            if n == 0:
                return ("Menor a 1 año", 1)
            if 0 < n <= 150:
                return (None, n)

    return (None, None)


def parse_construction_year_only(s: str | None) -> int | None:
    """Solo año calendario (4 dígitos); no interpreta rangos como año."""
    if not s or not str(s).strip():
        return None
    t = str(s).strip()
    if match_antiquity_range(t):
        return None
    if re.match(r"^\d{4}$", t):
        y = int(t)
        if 1800 <= y <= 2100:
            return y
    return None
