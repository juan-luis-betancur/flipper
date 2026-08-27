from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auth_jwt import bearer_dep
from .config import get_settings
from .scraper.pipeline import (
    run_pipeline,
    run_scrape_finca_raiz,
    run_scrape_mercado_libre,
    send_daily_digest,
    send_ml_reminder,
)
from .supabase_client import get_supabase
from .telegram_bot import send_message

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Flipper API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/scrape/run")
def scrape_run(background_tasks: BackgroundTasks, user_id: str = Depends(bearer_dep)):
    sb = get_supabase()
    ins = (
        sb.table("scraper_runs")
        .insert(
            {
                "user_id": user_id,
                "estado": "running",
                "etapa": "Iniciando…",
                "fecha_inicio": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    rows = ins.data or []
    if not rows:
        raise HTTPException(500, "No se pudo crear ejecución")
    run_id = rows[0]["id"]
    background_tasks.add_task(run_pipeline, user_id, run_id)
    return {"run_id": run_id}


def _require_cron_secret(x_cron_secret: str | None) -> None:
    s = get_settings()
    if not s.cron_secret or x_cron_secret != s.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")


def _active_user_ids_for_platform(platform: str | None) -> list[str]:
    sb = get_supabase()
    q = sb.table("scraping_sources").select("user_id").eq("is_active", True)
    if platform:
        q = q.eq("platform", platform)
    res = q.execute()
    return list({r["user_id"] for r in (res.data or [])})


def _enqueue_run(uid: str, etapa: str, fn, background_tasks: BackgroundTasks) -> None:
    sb = get_supabase()
    ins = (
        sb.table("scraper_runs")
        .insert(
            {
                "user_id": uid,
                "estado": "running",
                "etapa": etapa,
                "fecha_inicio": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    rows = ins.data or []
    if rows:
        background_tasks.add_task(fn, uid, rows[0]["id"])


@app.post("/api/cron/scrape-mercado-libre")
def cron_scrape_ml(
    background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)
):
    """Corre cada noche (23:50 Bogotá). Scrapea ML pero NO envía Telegram.

    Las propiedades quedan con notificada_at=NULL; las entrega el digest de la mañana.
    """
    _require_cron_secret(x_cron_secret)
    user_ids = _active_user_ids_for_platform("mercado_libre")
    for uid in user_ids:
        _enqueue_run(uid, "Cron ML (23:50)…", run_scrape_mercado_libre, background_tasks)
    return {"users": len(user_ids), "platform": "mercado_libre"}


@app.post("/api/cron/scrape-finca-raiz")
def cron_scrape_fr(
    background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)
):
    """Corre cada madrugada (05:30 Bogotá) con URL ``publicado-ayer``. NO envía Telegram.

    El digest (05:35) consolida ML de anoche + FR de esta madrugada.
    """
    _require_cron_secret(x_cron_secret)
    user_ids = _active_user_ids_for_platform("finca_raiz")
    for uid in user_ids:
        _enqueue_run(uid, "Cron FR (05:30)…", run_scrape_finca_raiz, background_tasks)
    return {"users": len(user_ids), "platform": "finca_raiz"}


@app.post("/api/cron/send-daily-digest")
def cron_send_digest(
    background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)
):
    """Envía el resumen consolidado a Telegram (05:35 Bogotá).

    Recorre todos los usuarios con cualquier fuente activa y dispara
    ``send_daily_digest`` en background. Idempotente vía ``notificada_at``.
    """
    _require_cron_secret(x_cron_secret)
    user_ids = _active_user_ids_for_platform(None)
    for uid in user_ids:
        background_tasks.add_task(send_daily_digest, uid)
    return {"users": len(user_ids), "action": "digest"}


@app.post("/api/cron/ml-reminder")
def cron_ml_reminder(
    background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)
):
    """Recordatorio para revisar Mercado Libre a mano (18:00 Bogotá = 23:00 UTC).

    ML bloquea el escaneo automático con su muro anti-bot, así que en lugar de
    reportar 0 cada día se envía el link de la búsqueda para revisarla manualmente.
    """
    _require_cron_secret(x_cron_secret)
    user_ids = _active_user_ids_for_platform("mercado_libre")
    for uid in user_ids:
        background_tasks.add_task(send_ml_reminder, uid)
    return {"users": len(user_ids), "action": "ml_reminder"}


@app.post("/api/cron/daily-scrape")
def cron_daily(background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)):
    """Legacy — corre todo en un solo paso (ML + FR + digest).

    Se mantiene por compatibilidad con el servicio ``railway-cron`` antiguo
    hasta que se migren los 3 nuevos servicios. Úsese para pruebas locales.
    """
    _require_cron_secret(x_cron_secret)
    user_ids = _active_user_ids_for_platform(None)
    for uid in user_ids:
        _enqueue_run(uid, "Cron diario (legacy)…", run_pipeline, background_tasks)
    return {"users": len(user_ids)}


@app.post("/api/telegram/test")
def telegram_test(user_id: str = Depends(bearer_dep)):
    sb = get_supabase()
    tg = sb.table("telegram_settings").select("*").eq("user_id", user_id).limit(1).execute()
    row = (tg.data or [None])[0]
    if not row or not row.get("bot_token") or not row.get("chat_id"):
        raise HTTPException(status_code=400, detail="Configura bot_token y chat_id")
    send_message(row["bot_token"], str(row["chat_id"]).strip(), "👋 Flipper conectado correctamente")
    return {"ok": True}


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str):
    """Ack de updates de Telegram.

    El guardado por Telegram (responder GUARDAR citando el aviso) se retiró: el
    digest ahora llega en un solo mensaje y guardar se hace desde la web. El
    endpoint se mantiene para que Telegram no reintente ni acumule updates
    pendientes mientras el webhook siga registrado.
    """
    s = get_settings()
    if secret != s.telegram_webhook_secret:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}
