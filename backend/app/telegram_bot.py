from __future__ import annotations

import re
from html import escape
from typing import Any

import httpx

TG_API = "https://api.telegram.org"


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


def format_scan_summary_html(encontradas: int, cumplen: int) -> str:
    sep = "---------------------"
    return (
        f"📊 <b>Resumen del Escaneo</b>\n"
        f"{sep}\n"
        f"🔍 Encontradas: <b>{encontradas}</b>\n"
        f"✅ Cumplen reglas: <b>{cumplen}</b>\n"
        f"{sep}\n"
        f"👇 <b>Estas son las que cumplen:</b> 👇"
    )


def format_property_message(row: dict[str, Any], *, index: int | None = None) -> str:
    ext = row.get("external_id")
    title = str(row.get("title") or "Propiedad").strip()
    url = str(row.get("url") or "").strip()
    price = row.get("price")
    m2 = row.get("precio_por_m2")
    area = row.get("area")

    if index is not None:
        head = f"🏢 <b>Apto #{index}</b>"
        sub = f"<i>{escape(title[:200])}</i>" if title else ""
    else:
        head = f"🏢 <b>{escape(title[:200])}</b>"
        sub = ""

    lines: list[str] = [head]
    if sub:
        lines.append(sub)

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
        lines.append(f'🔗 <a href="{escape(url, quote=True)}">Ver publicación</a>')
    lines.append("")
    lines.append(f"<code>ID: finca_raiz:{escape(str(ext))}</code>")
    lines.append("")
    lines.append("Responde <b>GUARDAR</b> a este mensaje para guardarla en Flipper.")
    return "\n".join(lines)


def parse_reply_external_id(reply_text: str) -> str | None:
    m = re.search(r"ID:\s*finca_raiz:([^\s<]+)", reply_text, re.I)
    return m.group(1) if m else None
