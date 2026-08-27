#!/bin/sh
# Dispara un POST al endpoint indicado por $TARGET_ENDPOINT.
#
# Diseñado para ser clonado en Railway como 3 servicios cron distintos, cada uno
# con su propio horario + su propio TARGET_ENDPOINT:
#
#   Servicio "ML scrape"    -> TARGET_ENDPOINT=/api/cron/scrape-mercado-libre   cron: 50 4 * * * (23:50 Bogotá)
#   Servicio "FR scrape"    -> TARGET_ENDPOINT=/api/cron/scrape-finca-raiz      cron: 30 10 * * * (05:30 Bogotá)
#   Servicio "Daily digest" -> TARGET_ENDPOINT=/api/cron/send-daily-digest      cron: 35 10 * * * (05:35 Bogotá)
#   Servicio "ML reminder"  -> TARGET_ENDPOINT=/api/cron/ml-reminder            cron: 0 23 * * *  (18:00 Bogotá)
#
# El recordatorio de ML existe porque Mercado Libre bloquea el escaneo automático
# con su muro anti-bot: en vez de reportar 0 cada día, manda el link para revisar
# la búsqueda a mano.
#
# Si TARGET_ENDPOINT no está definido, usa el legacy /api/cron/daily-scrape para
# no romper despliegues existentes.
set -eu
BASE="${FLIPPER_API_BASE_URL:?FLIPPER_API_BASE_URL is required}"
BASE="${BASE%/}"
SECRET="${CRON_SECRET:?CRON_SECRET is required}"
ENDPOINT="${TARGET_ENDPOINT:-/api/cron/daily-scrape}"
case "$ENDPOINT" in
  /*) ;;
  *) ENDPOINT="/${ENDPOINT}" ;;
esac
echo "[railway-cron] POST ${BASE}${ENDPOINT}"
exec curl -fsS -X POST "${BASE}${ENDPOINT}" \
  -H "X-Cron-Secret: ${SECRET}"
