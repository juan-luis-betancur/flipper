from __future__ import annotations

from html import escape
from typing import Any

import httpx

TG_API = "https://api.telegram.org"

# Separador entre bloques de apartamento. También es el punto de corte que usa
# ``split_telegram_html`` para no partir un apto a la mitad.
BLOCK_SEP = "--------------------"

_HEADER_SEP = "--------------------------"

_PLATFORM_LABELS = {
    "mercado_libre": "Mercado Libre",
    "finca_raiz": "Finca Raíz",
}

# Orden fijo en el desglose para que el mensaje se vea igual cada día.
_PLATFORM_ORDER = ("mercado_libre", "finca_raiz")

# Mensaje de fallo: sin detalle técnico, a propósito.
FALLO_ESCANEO_HTML = (
    "⚠️ <b>No pude completar el escaneo</b>\n"
    "Ocurrió algo al consultar los portales y no logré revisar las publicaciones. "
    "Lo intento de nuevo en la próxima corrida."
)


def send_message(
    bot_token: str,
    chat_id: str,
    text: str,
    *,
    disable_web_page_preview: bool = True,
) -> dict[str, Any]:
    url = f"{TG_API}/bot{bot_token}/sendMessage"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": disable_web_page_preview,
            },
        )
        r.raise_for_status()
        return r.json()


def format_cop_colombian(n: float | int | None) -> str | None:
    """Precio en pesos: $420.000.000 (separador de miles con punto)."""
    if n is None:
        return None
    try:
        x = int(round(float(n)))
    except (TypeError, ValueError):
        return None
    s = f"{x:,}".replace(",", ".")
    return f"${s}"


def format_property_block(row: dict[str, Any], *, index: int) -> str:
    """Bloque compacto de un apartamento dentro del mensaje único."""
    url = str(row.get("url") or "").strip()
    price = row.get("price")
    m2 = row.get("precio_por_m2")
    area = row.get("area")

    lines: list[str] = [f"🏢 <b>Apto #{index}</b>"]

    pc = format_cop_colombian(price)
    if pc:
        lines.append(f"💰 <b>Precio:</b> {pc}")

    if area is not None:
        try:
            ar = float(area)
            lines.append(f"📏 <b>Área:</b> {ar:g} m²")
        except (TypeError, ValueError):
            lines.append(f"📏 <b>Área:</b> {escape(str(area))} m²")

    pm = format_cop_colombian(m2)
    if pm:
        lines.append(f"📊 <b>Precio/m²:</b> {pm}")

    if url:
        lines.append(f'🔗 <a href="{escape(url, quote=True)}">Ver Publicación</a>')

    return "\n".join(lines)


def _platform_label(platform: str) -> str:
    return _PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())


def format_digest_html(
    *,
    por_plataforma: dict[str, int],
    total_encontradas: int,
    matches: list[dict[str, Any]],
) -> str:
    """Arma el resumen completo del escaneo en un solo mensaje.

    ``por_plataforma`` es el conteo de publicaciones vistas por portal
    (p. ej. ``{"mercado_libre": 9, "finca_raiz": 5}``); ``total_encontradas`` es
    el total escaneado y ``matches`` las que pasaron los filtros.
    """
    lines: list[str] = [
        "📊 <b>Resumen del Escaneo</b>",
        _HEADER_SEP,
        f"🔍 <b>Encontradas:</b> {total_encontradas}",
    ]

    # Primero las plataformas conocidas en orden fijo, después cualquier otra.
    conocidas = [p for p in _PLATFORM_ORDER if por_plataforma.get(p)]
    otras = sorted(p for p, n in por_plataforma.items() if n and p not in _PLATFORM_ORDER)
    for plat in conocidas + otras:
        lines.append(f"   • {_platform_label(plat)}: {por_plataforma[plat]}")

    lines.append(f"✅ <b>Cumplen reglas:</b> {len(matches)}")
    lines.append(_HEADER_SEP)
    lines.append("")

    if not total_encontradas:
        lines.append("😴 Hoy no encontré publicaciones nuevas en los portales.")
        return "\n".join(lines)

    if not matches:
        lines.append("😴 Ninguna de las encontradas cumple tus filtros hoy.")
        return "\n".join(lines)

    lines.append("👇 <b>Estas son las que cumplen:</b> 👇")
    lines.append("")

    bloques = [format_property_block(p, index=i) for i, p in enumerate(matches, start=1)]
    lines.append(f"\n{BLOCK_SEP}\n".join(bloques))

    return "\n".join(lines)


def split_telegram_html(text: str, limit: int = 3900) -> list[str]:
    """Parte el mensaje en trozos que quepan en Telegram (tope real: 4096).

    Corta solo en los separadores de bloque para no romper un apto por la mitad.
    Con pocas coincidencias devuelve una sola parte, que es el caso normal.
    """
    if len(text) <= limit:
        return [text]

    sep = f"\n{BLOCK_SEP}\n"
    partes: list[str] = []
    actual = ""
    for bloque in text.split(sep):
        candidato = f"{actual}{sep}{bloque}" if actual else bloque
        if actual and len(candidato) > limit:
            partes.append(actual)
            actual = bloque
        else:
            actual = candidato
    if actual:
        partes.append(actual)
    return partes
