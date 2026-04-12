from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .auth_jwt import bearer_dep
from .config import get_settings
from .scraper.pipeline import run_pipeline
from .supabase_client import get_supabase
from .telegram_bot import parse_reply_external_id, send_message

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


@app.post("/api/cron/daily-scrape")
def cron_daily(background_tasks: BackgroundTasks, x_cron_secret: str | None = Header(None)):
    s = get_settings()
    if not s.cron_secret or x_cron_secret != s.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    sb = get_supabase()
    res = sb.table("scraping_sources").select("user_id").eq("is_active", True).execute()
    user_ids = list({r["user_id"] for r in (res.data or [])})
    for uid in user_ids:
        ins = (
            sb.table("scraper_runs")
            .insert(
                {
                    "user_id": uid,
                    "estado": "running",
                    "etapa": "Cron diario…",
                    "fecha_inicio": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        rows = ins.data or []
        if rows:
            background_tasks.add_task(run_pipeline, uid, rows[0]["id"])
    return {"users": len(user_ids)}


@app.post("/api/telegram/test")
def telegram_test(user_id: str = Depends(bearer_dep)):
    sb = get_supabase()
    tg = sb.table("telegram_settings").select("*").eq("user_id", user_id).limit(1).execute()
    row = (tg.data or [None])[0]
    if not row or not row.get("bot_token") or not row.get("chat_id"):
        raise HTTPException(status_code=400, detail="Configura bot_token y chat_id")
    send_message(row["bot_token"], str(row["chat_id"]), "👋 Flipper conectado correctamente")
    return {"ok": True}


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    s = get_settings()
    if secret != s.telegram_webhook_secret:
        raise HTTPException(status_code=404, detail="Not found")
    body = await request.json()
    msg = body.get("message") or body.get("edited_message") or {}
    text = (msg.get("text") or "").strip().lower()
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    reply = msg.get("reply_to_message") or {}
    reply_text = reply.get("text") or reply.get("caption") or ""

    if text not in ("guardar", "guardar."):
        return {"ok": True}

    ext = parse_reply_external_id(reply_text)
    if not ext or chat_id is None:
        return {"ok": True}

    sb = get_supabase()
    tg = (
        sb.table("telegram_settings")
        .select("user_id")
        .eq("chat_id", str(chat_id))
        .limit(1)
        .execute()
    )
    row = (tg.data or [None])[0]
    if not row:
        return {"ok": True}
    uid = row["user_id"]
    prop = (
        sb.table("properties")
        .select("id")
        .eq("user_id", uid)
        .eq("platform", "finca_raiz")
        .eq("external_id", ext)
        .limit(1)
        .execute()
    )
    pr = (prop.data or [None])[0]
    if not pr:
        return {"ok": True}
    sb.table("saved_properties").upsert(
        {
            "user_id": uid,
            "property_id": pr["id"],
            "guardada_via": "telegram",
        },
        on_conflict="user_id,property_id",
    ).execute()

    bot_token_row = sb.table("telegram_settings").select("bot_token").eq("user_id", uid).limit(1).execute()
    bt = (bot_token_row.data or [None])[0]
    if bt and bt.get("bot_token"):
        try:
            send_message(
                bt["bot_token"],
                str(chat_id),
                "✅ Guardada. Puedes verla en Flipper en la sección Propiedades Guardadas.",
            )
        except Exception as e:
            log.warning("reply telegram failed: %s", e)

    return {"ok": True}
