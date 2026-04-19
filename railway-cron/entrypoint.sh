#!/bin/sh
# Dispara POST /api/cron/daily-scrape (variables solo en runtime; no en build).
set -eu
BASE="${FLIPPER_API_BASE_URL:?FLIPPER_API_BASE_URL is required}"
BASE="${BASE%/}"
SECRET="${CRON_SECRET:?CRON_SECRET is required}"
exec curl -fsS -X POST "${BASE}/api/cron/daily-scrape" \
  -H "X-Cron-Secret: ${SECRET}"
