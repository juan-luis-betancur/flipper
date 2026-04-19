#!/usr/bin/env bash
# Prueba POST /api/cron/daily-scrape (mismo contrato que el programador diario).
# Uso:
#   export FLIPPER_API_BASE_URL="https://tu-backend.example.com"
#   export CRON_SECRET="el-mismo-valor-que-en-produccion"
#   ./scripts/test_daily_scrape_endpoint.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -z "${FLIPPER_API_BASE_URL:-}" ]]; then
  echo "Falta FLIPPER_API_BASE_URL (ej. https://tu-servicio.railway.app, sin barra final)" >&2
  exit 1
fi
if [[ -z "${CRON_SECRET:-}" ]]; then
  echo "Falta CRON_SECRET (debe coincidir con el del servidor)" >&2
  exit 1
fi
URL="${FLIPPER_API_BASE_URL%/}/api/cron/daily-scrape"
echo "POST $URL"
curl -sS -w "\nHTTP %{http_code}\n" -X POST "$URL" -H "X-Cron-Secret: ${CRON_SECRET}"
