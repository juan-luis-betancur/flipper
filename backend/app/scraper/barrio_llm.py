"""
Inferencia opcional de barrio vía LLM (placeholder).

Si BARIO_LLM_ENABLED=1, se puede enchufar un proveedor; por defecto no llama red ni API.
"""

from __future__ import annotations

import os
from typing import Any


def infer_barrio_from_context(
    ubicacion: dict[str, Any] | None,
    descripcion: str | None,
    whitelist: list[str],
) -> dict[str, Any]:
    """
    Devuelve JSON estable: barrio elegido (solo whitelist), confianza, motivo.

    Implementación futura: prompt + modelo con salida acotada a `whitelist`.
    """
    _ = (ubicacion, descripcion, whitelist)
    if os.getenv("BARIO_LLM_ENABLED", "").lower() not in ("1", "true", "yes"):
        return {
            "barrio": None,
            "confidence": 0.0,
            "rationale": "BARIO_LLM_ENABLED no activado o inferencia no implementada",
        }
    return {
        "barrio": None,
        "confidence": 0.0,
        "rationale": "BARIO_LLM_ENABLED sin cliente LLM configurado aún",
    }


def enrich_ubicacion_llm_placeholder(row: dict[str, Any], whitelist: list[str]) -> None:
    """Escribe `ubicacion.llm_inferencia` cuando el flag está activo (sin API real por defecto)."""
    if os.getenv("BARIO_LLM_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    dc = row.get("datos_crudos")
    if not isinstance(dc, dict):
        return
    ub = dc.get("ubicacion")
    if not isinstance(ub, dict):
        return
    desc = row.get("descripcion")
    ub["llm_inferencia"] = infer_barrio_from_context(ub, str(desc) if desc else None, whitelist)
