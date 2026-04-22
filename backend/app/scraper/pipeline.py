from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Callable, Iterable

import httpx

from ..config import get_settings
from ..filters import property_matches_alert
from ..supabase_client import get_supabase
from ..telegram_bot import format_property_message, format_scan_summary_html, send_message
from .finca_raiz import build_list_url, scrape_source
from .mercado_libre import scrape_mercado_libre

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
        "platform": partial.get("platform") or "finca_raiz",
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


def _resolve_fr_list_url(src: dict) -> str:
    """Usa source.list_url si existe (nuevo modelo URL-directa), si no construye desde barrios+filtro."""
    direct = (src.get("list_url") or "").strip()
    if direct:
        return direct
    return build_list_url(
        src.get("neighborhoods") or [],
        src.get("publication_filter") or "today",
    )


def _run_platform_pipeline(
    user_id: str,
    run_id: str,
    platform: str,
    scrape_fn: Callable[[dict, int, float, httpx.Client | None], Iterable[dict]],
    *,
    etapa_label: str,
) -> None:
    """Núcleo compartido: scrapea solo las fuentes de ``platform`` y persiste en BD.

    NO envía Telegram: eso lo hace ``send_daily_digest`` como paso separado.
    Las propiedades nuevas quedan con ``notificada_at = NULL``.
    """
    sb = get_supabase()
    settings = get_settings()
    lines: list[str] = []

    def upd(**kwargs):
        sb.table("scraper_runs").update(kwargs).eq("id", run_id).execute()

    try:
        upd(etapa=f"Scrapeando {etapa_label}…", estado="running")
        res = (
            sb.table("scraping_sources")
            .select("*")
            .eq("user_id", user_id)
            .eq("platform", platform)
            .eq("is_active", True)
            .execute()
        )
        sources = res.data or []
        if not sources:
            lines.append(f"No hay fuentes activas para {etapa_label}.")
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
        total_seen = 0
        remaining = settings.scrape_max_properties
        source_failures = 0

        with httpx.Client(headers=headers, follow_redirects=True) as client:
            for src in sources:
                if remaining <= 0:
                    break
                try:
                    lines.append(f"Fuente «{src.get('name')}» ({etapa_label})")
                    upd(etapa=f"Scrapeando listado ({src.get('name')})…")
                    rows = list(
                        scrape_fn(
                            src,
                            remaining,
                            settings.scrape_delay_seconds,
                            client,
                        )
                    )
                    total_seen += len(rows)
                    upd(etapa="Extrayendo detalles / guardando…")
                    for row in rows:
                        ext = row["external_id"]
                        plat = row.get("platform") or platform
                        ex = (
                            sb.table("properties")
                            .select("id")
                            .eq("user_id", user_id)
                            .eq("platform", plat)
                            .eq("external_id", ext)
                            .limit(1)
                            .execute()
                        )
                        is_new = len(ex.data or []) == 0
                        payload = _merge_row(user_id, row)
                        # Las nuevas propiedades quedan pendientes de notificar
                        # (notificada_at NULL). Las existentes conservan su estado;
                        # no pisamos notificada_at en upsert (no está en el payload).
                        sb.table("properties").upsert(
                            payload,
                            on_conflict="platform,external_id,user_id",
                        ).execute()
                        if is_new:
                            total_new += 1
                    remaining = max(0, remaining - len(rows))
                    sb.table("scraping_sources").update(
                        {
                            "last_run_at": datetime.now(timezone.utc).isoformat(),
                            "last_run_properties_count": len(rows),
                            "last_run_error": None,
                        }
                    ).eq("id", src["id"]).execute()
                except Exception as src_err:
                    log.exception("fuente %s (%s) falló", src.get("name"), platform)
                    err_msg = str(src_err)
                    source_failures += 1
                    lines.append(
                        f"Fuente «{src.get('name')}» ({platform}) falló: {err_msg}"
                    )
                    sb.table("scraping_sources").update(
                        {
                            "last_run_at": datetime.now(timezone.utc).isoformat(),
                            "last_run_error": err_msg,
                        }
                    ).eq("id", src["id"]).execute()
                    continue

        all_failed = source_failures > 0 and source_failures == len(sources)
        partial_fail_msg = (
            f"{source_failures} de {len(sources)} fuentes fallaron"
            if source_failures and not all_failed
            else None
        )
        upd(
            estado="failed" if all_failed else "success",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            total_encontradas=total_seen,
            nuevas=total_new,
            enviadas_a_telegram=0,  # el digest suma después
            log_resumen="\n".join(lines[-40:]),
            etapa="Listo" if not all_failed else "Error",
            mensaje_error=(
                "Todas las fuentes fallaron" if all_failed else partial_fail_msg
            ),
        )
    except Exception as e:
        log.exception("pipeline %s failed", platform)
        upd(
            estado="failed",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            mensaje_error=str(e),
            log_resumen="\n".join(lines + [str(e)]),
            etapa="Error",
        )
        sb.table("scraping_sources").update({"last_run_error": str(e)}).eq(
            "user_id", user_id
        ).eq("platform", platform).execute()


def _scrape_one_fr(src: dict, remaining: int, delay: float, client: httpx.Client | None):
    assert client is not None
    list_url = _resolve_fr_list_url(src)
    return scrape_source(client, list_url, max_props=remaining, delay=delay)


def _scrape_one_ml(src: dict, remaining: int, delay: float, client: httpx.Client | None):
    list_url = (src.get("list_url") or "").strip()
    if not list_url:
        raise RuntimeError("mercado_libre sin list_url")
    return scrape_mercado_libre(list_url, max_props=remaining, delay=delay)


def run_scrape_finca_raiz(user_id: str, run_id: str) -> None:
    _run_platform_pipeline(
        user_id, run_id, platform="finca_raiz",
        scrape_fn=_scrape_one_fr, etapa_label="Finca Raíz",
    )


def run_scrape_mercado_libre(user_id: str, run_id: str) -> None:
    _run_platform_pipeline(
        user_id, run_id, platform="mercado_libre",
        scrape_fn=_scrape_one_ml, etapa_label="Mercado Libre",
    )


def send_daily_digest(user_id: str) -> dict:
    """Envía a Telegram las propiedades pendientes de notificar (``notificada_at IS NULL``).

    Consolida ML (scrapeado anoche) + FR (scrapeado esta madrugada) en un solo
    resumen. Idempotente: cada propiedad se marca ``notificada_at = now()`` tras
    enviarse, así que una segunda llamada en el mismo día no reenvía nada.
    """
    sb = get_supabase()

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

    if not (filt and filt.get("send_telegram") and tg and tg.get("bot_token") and tg.get("chat_id")):
        log.info("digest: user_id=%s sin filtro/telegram configurado, skip", user_id)
        return {"sent": 0, "reason": "not_configured"}

    # Ventana de 36h para absorber corrimientos de cron (ML 23:50 + FR 05:30).
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
    pending = (
        sb.table("properties")
        .select("*")
        .eq("user_id", user_id)
        .is_("notificada_at", "null")
        .gte("fecha_scrapeo", cutoff.isoformat())
        .execute()
    )
    fresh = pending.data or []
    matches = [p for p in fresh if property_matches_alert(p, filt)]
    total_seen = len(fresh)

    if not fresh:
        log.info("digest: user_id=%s sin propiedades pendientes", user_id)
        return {"sent": 0, "reason": "no_pending"}

    sent = 0
    if matches:
        try:
            send_message(
                tg["bot_token"],
                str(tg["chat_id"]),
                format_scan_summary_html(total_seen, len(matches)),
            )
        except Exception as e:
            log.warning("digest resumen falló user_id=%s: %s", user_id, e)
        for i, p in enumerate(matches, start=1):
            try:
                send_message(
                    tg["bot_token"],
                    str(tg["chat_id"]),
                    format_property_message(p, index=i),
                    disable_web_page_preview=False,
                )
                sent += 1
            except Exception as e:
                log.warning("digest item falló user_id=%s id=%s: %s", user_id, p.get("id"), e)

    # Marcar TODAS las pendientes (incluso las que no matchean) para no reprocesarlas.
    now_iso = datetime.now(timezone.utc).isoformat()
    ids = [p["id"] for p in fresh]
    if ids:
        # supabase-py permite filtrar con .in_ en updates
        sb.table("properties").update({"notificada_at": now_iso}).in_("id", ids).execute()

    return {"sent": sent, "matches": len(matches), "pending_marked": len(ids)}


# ---------------------------------------------------------------------------
# Compatibilidad retroactiva: run_pipeline orquesta ML + FR + digest.
# ---------------------------------------------------------------------------


def run_pipeline(user_id: str, run_id: str) -> None:
    """Legacy / manual: corre ambos scrapers **agregando stats al mismo run_id**
    y dispara el digest al final.

    Usado por el botón manual ``/api/scrape/run`` y el cron legacy
    ``/api/cron/daily-scrape``. El frontend observa este run_id y espera ver
    totales que incluyan ambas plataformas; por eso no se delega a los dos
    pipelines por plataforma (que cierran el run con sus propios counts).
    """
    sb = get_supabase()
    settings = get_settings()
    lines: list[str] = []

    def upd(**kwargs):
        sb.table("scraper_runs").update(kwargs).eq("id", run_id).execute()

    try:
        upd(etapa="Cargando fuentes…", estado="running")
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

        total_new = 0
        total_seen = 0
        remaining = settings.scrape_max_properties
        source_failures = 0

        headers = {"User-Agent": settings.user_agent}
        with httpx.Client(headers=headers, follow_redirects=True) as client:
            for src in sources:
                if remaining <= 0:
                    break
                platform = (src.get("platform") or "finca_raiz").strip()
                try:
                    lines.append(f"Fuente «{src.get('name')}» ({platform})")
                    upd(etapa=f"Scrapeando listado ({src.get('name')})…")
                    if platform == "mercado_libre":
                        rows = list(_scrape_one_ml(src, remaining, settings.scrape_delay_seconds, client))
                    else:
                        rows = list(_scrape_one_fr(src, remaining, settings.scrape_delay_seconds, client))
                    total_seen += len(rows)
                    upd(etapa="Extrayendo detalles / guardando…")
                    for row in rows:
                        ext = row["external_id"]
                        plat = row.get("platform") or platform
                        ex = (
                            sb.table("properties")
                            .select("id")
                            .eq("user_id", user_id)
                            .eq("platform", plat)
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
                    remaining = max(0, remaining - len(rows))
                    sb.table("scraping_sources").update(
                        {
                            "last_run_at": datetime.now(timezone.utc).isoformat(),
                            "last_run_properties_count": len(rows),
                            "last_run_error": None,
                        }
                    ).eq("id", src["id"]).execute()
                except Exception as src_err:
                    log.exception("fuente %s (%s) falló", src.get("name"), platform)
                    err_msg = str(src_err)
                    source_failures += 1
                    lines.append(
                        f"Fuente «{src.get('name')}» ({platform}) falló: {err_msg}"
                    )
                    sb.table("scraping_sources").update(
                        {
                            "last_run_at": datetime.now(timezone.utc).isoformat(),
                            "last_run_error": err_msg,
                        }
                    ).eq("id", src["id"]).execute()
                    continue

        # Digest inmediato: el botón manual históricamente envía Telegram al
        # final. Idempotente vía notificada_at.
        digest_result = {"sent": 0}
        try:
            digest_result = send_daily_digest(user_id) or digest_result
        except Exception:
            log.exception("legacy run_pipeline: digest falló")

        all_failed = source_failures > 0 and source_failures == len(sources)
        partial_fail_msg = (
            f"{source_failures} de {len(sources)} fuentes fallaron"
            if source_failures and not all_failed
            else None
        )
        upd(
            estado="failed" if all_failed else "success",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            total_encontradas=total_seen,
            nuevas=total_new,
            enviadas_a_telegram=int(digest_result.get("sent", 0)),
            log_resumen="\n".join(lines[-40:]),
            etapa="Listo" if not all_failed else "Error",
            mensaje_error=(
                "Todas las fuentes fallaron" if all_failed else partial_fail_msg
            ),
        )
    except Exception as e:
        log.exception("legacy run_pipeline failed")
        upd(
            estado="failed",
            fecha_fin=datetime.now(timezone.utc).isoformat(),
            mensaje_error=str(e),
            log_resumen="\n".join(lines + [str(e)]),
            etapa="Error",
        )
