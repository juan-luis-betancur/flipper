# Railway Cron — disparo diario del scraping

Servicio **efímero**: al arrancar hace un `POST` a `…/api/cron/daily-scrape` y sale. En Railway se configura con **Cron Schedule** en este servicio (no en el del API FastAPI).

## Variables (solo en Railway, nunca en Git)

En el servicio cuyo **Root Directory** es `railway-cron`:

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `FLIPPER_API_BASE_URL` | `https://tu-api.up.railway.app` | Base pública del **backend** FastAPI, **sin** barra final. |
| `CRON_SECRET` | *(valor largo aleatorio)* | **El mismo** que en el servicio del backend (`CRON_SECRET`). |

No marques estas variables como **Docker build secrets** salvo que tu Dockerfile las use en `RUN --mount` (este Dockerfile **no** las usa en build; solo en runtime). Si Railway falla con `secret CRON_SECRET: not found`, revisa que no tengas referencias a build secrets en otro sitio.

## Pasos en Railway

1. **New service** → mismo repositorio GitHub que el monorepo.
2. **Settings → Root Directory** → `railway-cron`.
3. Railway detectará el `Dockerfile` y construirá la imagen.
4. **Variables** → añade `FLIPPER_API_BASE_URL` y `CRON_SECRET` (mismo secreto que en el backend).
5. **Settings → Cron Schedule** → expresión en **UTC**, por ejemplo:
   - `0 12 * * *` → cada día 12:00 UTC (= 07:00 en Bogotá UTC−5).
6. Guarda y deja que el cron ejecute; revisa **Logs** del servicio y en Supabase la tabla `scraper_runs`.

## Probar localmente

```bash
cd railway-cron
docker build -t flipper-cron .
docker run --rm -e FLIPPER_API_BASE_URL="https://tu-api" -e CRON_SECRET="tu-secreto" flipper-cron
```

## Referencia

- [Railway Cron Jobs](https://docs.railway.com/reference/cron-jobs)
- Endpoint del API: `POST /api/cron/daily-scrape` con header `X-Cron-Secret`.
