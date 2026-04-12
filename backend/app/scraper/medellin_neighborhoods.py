"""
Lista canónica de barrios / zonas frecuentes (Medellín y cercanías) para fuzzy match y LLM.

Mantener alineada con [web/src/constants/neighborhoods.ts](web/src/constants/neighborhoods.ts).
"""

from __future__ import annotations

import difflib

# Misma lista que PRESET_NEIGHBORHOODS en la web (fuentes de scraping y filtros).
MEDELLIN_NEIGHBORHOODS_WHITELIST: tuple[str, ...] = (
    "El Poblado",
    "Envigado",
    "Zúñiga",
    "Laureles",
    "Belén",
    "Sabaneta",
    "La Estrella",
    "Calasanz",
    "Ciudad del Río",
    "Altos del Poblado",
    "Las Palmas",
    "San Lucas",
    "El Tesoro",
)


def whitelist_barrios() -> list[str]:
    return list(MEDELLIN_NEIGHBORHOODS_WHITELIST)


def fuzzy_suggest_barrio(candidate: str | None, *, cutoff: float = 0.72) -> str | None:
    """
    Si `candidate` (p. ej. barrio devuelto por FR) se parece a un ítem de la whitelist, devuelve ese ítem.
    Sin red; útil para normalizar antes de LLM o para mostrar sugerencia en `datos_crudos.ubicacion`.
    """
    if not candidate or not str(candidate).strip():
        return None
    c = str(candidate).strip()
    w = whitelist_barrios()
    m = difflib.get_close_matches(c, w, n=1, cutoff=cutoff)
    return m[0] if m else None
