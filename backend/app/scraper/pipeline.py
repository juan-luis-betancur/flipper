from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx

from ..config import get_settings
from ..filters import property_matches_alert
from ..supabase_client import get_supabase
from ..telegram_bot import format_property_message, format_scan_summary_html, send_message
from .finca_raiz import build_list_url, scrape_source

log = logging.getLogger(__name__)


def _merge_row(user_id: str, partial: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    raw = partial.get("datos_crudos") or {}
    try:
        raw_json = json.loads(json.dumps(raw, default=str))
    except (TypeError, ValueError):
        raw_json = {}
    base = {
        "user_id": user_id,
        "external_id": partial["external_id"],
        "platform": "finca_raiz",
        "url": partial["url"],
        "title": partial.get("title"),
        "price": partial.get("price"),
        "area": partial.get("area"),
        "descripcion": partial.get("descripcion"),
        "es_remodelado": partial.get("es_remodelado", False),
        "datos_crudos": raw_json,
        "fecha_scrapeo": now,
    }
    for k, v in partial.items():
        if k in base or k in ("external_id", "platform", "url"):
            continue
        if v is not None:
            base[k] = v
    return base


def run_pipeline(user_id: str, run_id: str) -> None:
    sb = get_supabase()
    settings = get_settings()
    lines: list[str] = []

    def upd(**kwargs):
        sb.table("scraper_runs").update(kwargs).eq("id", run_id).execute()

    try:
        upd(etapa="Scrapeando listado…", estado="running")
        res = (
            sb.table("scraping_sources")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        sources = res.data or []
        if not sources:
            lines.append("No hay fuentes activas.")
            upd(
                estado="success",
                fecha_fin=datetime.now(timezone.utc).isoformat(),
                total_encontradas=0,
                nuevas=0,
                enviadas_a_telegram=0,
                log_resumen="\n".join(lines),
                etapa="Listo",
            )
            return

        headers = {"User-Agent": settings.user_agent}
        total_new = 0
        total_sent = 0
        total_seen = 0
        remaining = settings.scrape_max_properties
        new_external_ids: list[str] = []

        with httpx.Client(headers=headers, follow_redirects=True) as client:
            for src in sources:
                if remaining <= 0:
                    break
                list_url = build_list_url(src.get("neighborhoods") or [], src.get("publication_filter") or "today")
                lines.append(f"Fuente «{src.get('name')}»: {list_url}")
                upd(etapa=f"Scrapeando listado ({src.get('name')})…")
                rows = scrape_source(client, list_url, max_props=remaining, delay=settings.scrape_delay_seconds)
                total_seen += len(rows)
                upd(etapa="Extrayendo detalles / guardando…")
                for row in rows:
                    ext = row["external_id"]
                    ex = (
                        sb.table("properties")
                        .select("id")
                        .eq("user_id", user_id)
                        .eq("platform", "finca_raiz")
                        .eq("external_id", ext)
                        .limit(1)
                        .execute()
                    )
                    is_new = len(ex.data or []) == 0
                    payload = _merge_row(user_id, row)
                    sb.table("properties").upsert(
                        payload,
                        on_conflict="platform,external_id,user_id",
                    ).execute()
                    if is_new:
                        total_new += 1
                        new_external_ids.append(ext)
                remaining = max(0, remaining - len(rows))
                sb.table("scraping_sources").update(
                    {
                        "last_run_at": datetime.now(timezone.utc).isoformat(),
                        "last_run_properties_count": len(rows),
                        "last_run_error": None,
                    }
                ).eq("id", src["id"]).execute()

        filt_res = (
            sb.table("alert_filters")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        filt = (filt_res.data or [None])[0]
        tg_res = sb.table("telegram_settings").select("*").eq("user_id", user_id).limit(1).execute()
        tg = (tg_res.data or [None])[0]

        upd(etapa="Enviando a Telegram…")
        if (
            filt
            and filt.get("send_telegram")
            and tg
            and tg.get("bot_token")
            and tg.get("chat_id")
            and new_external_ids
        ):
            matches: list[dict] = []
            for ext in new_external_ids:
                pr = (
                    sb.table("properties")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("platform", "finca_raiz")
                    .eq("external_id", ext)
                    .limit(1)
                    .execute()
                )
                p = (pr.data or [None])[0]
                if p and property_matches_alert(p, filt):
                    matches.append(p)
            if matches:
                try:
                    send_message(
                        tg["bot_token"],
                        str(tg["chat_id"]),
                        format_scan_summary_html(total_seen, len(matches)),
                    )
                except Exception as e:
                    lines.append(f"Telegram error (resumen): {e}")
                for i, p in enumerate(matches, start=1):
                    try:
                        send_message(
                            tg["bot_token"],
                            str(tg["chat_id"]),
                            format_property_message(p, index=i),
                            disable_web_page_preview=False,
                        )
                        total_sent += 1
                    except Exception as e:
                        lines.append(f"Telegram error: {e}")
        elif not new_external_ids:
            lines.append("Sin propiedades nuevas; no se envía Telegram.")
        else:
            lines.append("Telegram o filtros no configurados para envío.")

        upd(
            estado="success",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            total_encontradas=total_seen,
            nuevas=total_new,
            enviadas_a_telegram=total_sent,
            log_resumen="\n".join(lines[-40:]),
            etapa="Listo",
            mensaje_error=None,
        )
    except Exception as e:
        log.exception("pipeline failed")
        upd(
            estado="failed",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            mensaje_error=str(e),
            log_resumen="\n".join(lines + [str(e)]),
            etapa="Error",
        )
        sb.table("scraping_sources").update({"last_run_error": str(e)}).eq("user_id", user_id).execute()
