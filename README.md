# Flipper MVP — Búsqueda de propiedades

Monorepo: **Supabase** (Postgres + Auth + RLS), **web** (Vite + React + TypeScript + Tailwind + Recharts + Leaflet) y **backend** (FastAPI + scraper Python + Telegram).

## Requisitos

- Node 20+
- Python 3.11+ (para el backend)
- Proyecto [Supabase](https://supabase.com) con la migración aplicada

## Supabase

1. Crea un proyecto y ejecuta el SQL en `supabase/migrations/20260111000000_init_flipper.sql` (SQL editor o CLI).
2. En **Authentication**, crea un usuario con email/contraseña.
3. (Opcional) **Database → Replication**: habilita `properties` para Realtime en el ACM.

## Web (`web/`)

```bash
cd web
cp .env.example .env
# Rellena VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY; VITE_API_URL=http://127.0.0.1:8000
npm install
npm run dev
```

## Backend (`backend/`)

```bash
cd backend
# Crea .env con:
# SUPABASE_URL=
# SUPABASE_SERVICE_ROLE_KEY=
# SUPABASE_JWT_SECRET=   (Settings → API → JWT Secret)
# CRON_SECRET=           (para POST /api/cron/daily-scrape)
# TELEGRAM_WEBHOOK_SECRET=
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Configura el webhook de Telegram a:

`https://TU_DOMINIO/telegram/webhook/TU_TELEGRAM_WEBHOOK_SECRET`

Cron diario (7:00): tu PaaS debe llamar `POST /api/cron/daily-scrape` con header `X-Cron-Secret: TU_CRON_SECRET`.

## Legal

Revisa los términos de uso de Finca Raíz antes de scrapear en producción. El scraper incluye pausas y un tope de propiedades por ejecución.
