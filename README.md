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

## Scraping diario (cron HTTP)

El backend expone **`POST /api/cron/daily-scrape`**: para cada usuario con al menos una **`scraping_sources`** activa (`is_active = true`), crea una ejecución en **`scraper_runs`** y lanza el mismo pipeline que el botón manual de la web. La respuesta HTTP vuelve enseguida (`{"users": N}`) mientras el trabajo sigue en segundo plano.

### 1. `CRON_SECRET` en producción

1. Genera un valor aleatorio largo, por ejemplo en terminal: `openssl rand -hex 32`.
2. En el panel de variables de entorno de tu PaaS (Railway, Render, Fly.io, etc.), define **`CRON_SECRET`** con ese valor y vuelve a desplegar el servicio si hace falta.
3. El mismo valor debe usarse solo en el programador (header abajo), no en el frontend.

### 2. Programador diario

Configura **un** disparador HTTP (nativo del PaaS o servicio externo como [cron-job.org](https://cron-job.org)):

| Campo | Valor |
|--------|--------|
| Método | `POST` |
| URL | `https://TU_DOMINIO_PUBLICO/api/cron/daily-scrape` (misma base que `VITE_API_URL` en la web) |
| Header | `X-Cron-Secret: <mismo CRON_SECRET que en el servidor>` |
| Hora | La que prefieras; revisa la **zona horaria** del panel (UTC vs `America/Bogota`). |

**Render:** crea un [Cron Job](https://render.com/docs/cronjobs) que ejecute un `curl` contra esa URL con el header, o usa su integración HTTP si la ofrece.

**Railway:** usa [Cron Jobs](https://docs.railway.com/reference/cron-jobs) o un servicio externo que haga el `POST` periódico.

### 3. Comprobar que funciona

Desde tu máquina (sustituye URL y secreto):

```bash
curl -X POST "https://TU_DOMINIO_PUBLICO/api/cron/daily-scrape" -H "X-Cron-Secret: TU_CRON_SECRET"
```

Debes obtener **HTTP 200** y un JSON como `{"users":1}`. **403** indica secreto incorrecto o `CRON_SECRET` no definido en el servidor.

Scripts en el repo (mismas variables de entorno):

```bash
cd backend
export FLIPPER_API_BASE_URL="https://TU_DOMINIO_PUBLICO"
export CRON_SECRET="TU_CRON_SECRET"
./scripts/test_daily_scrape_endpoint.sh
```

En PowerShell (Windows):

```powershell
cd backend
$env:FLIPPER_API_BASE_URL = "https://TU_DOMINIO_PUBLICO"
$env:CRON_SECRET = "TU_CRON_SECRET"
.\scripts\test_daily_scrape_endpoint.ps1
```

En Supabase, revisa la tabla **`scraper_runs`**: deberían aparecer filas nuevas con `etapa` / `estado` tras cada disparo.

## Legal

Revisa los términos de uso de Finca Raíz antes de scrapear en producción. El scraper incluye pausas y un tope de propiedades por ejecución.
