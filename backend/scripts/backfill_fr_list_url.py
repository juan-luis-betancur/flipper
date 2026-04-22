"""Backfill: poblar ``scraping_sources.list_url`` para fuentes Finca Raíz antiguas.

Antes de este cambio, las fuentes FR se definían con ``neighborhoods[]`` +
``publication_filter`` y el backend construía la URL en runtime con
``build_list_url``. La nueva UI guarda la URL directamente en ``list_url``.
Este script computa la URL legacy para cada fuente FR existente sin ``list_url``
y la persiste, para no depender del fallback indefinidamente.

Uso:
    cd backend
    python -m scripts.backfill_fr_list_url            # dry-run
    python -m scripts.backfill_fr_list_url --apply    # ejecuta el UPDATE
"""
from __future__ import annotations

import argparse
import sys

from app.scraper.finca_raiz import build_list_url
from app.supabase_client import get_supabase


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Persistir cambios (sin esto, dry-run)")
    args = ap.parse_args()

    sb = get_supabase()
    res = (
        sb.table("scraping_sources")
        .select("id, name, user_id, neighborhoods, publication_filter, list_url")
        .eq("platform", "finca_raiz")
        .execute()
    )
    rows = res.data or []
    pending = [r for r in rows if not (r.get("list_url") or "").strip()]
    print(f"fuentes FR totales: {len(rows)}; sin list_url: {len(pending)}")

    updated = 0
    for r in pending:
        url = build_list_url(
            r.get("neighborhoods") or [],
            r.get("publication_filter") or "today",
        )
        print(f"  - {r['name']} ({r['id']}): -> {url}")
        if args.apply:
            sb.table("scraping_sources").update({"list_url": url}).eq("id", r["id"]).execute()
            updated += 1

    if args.apply:
        print(f"OK: {updated} fuentes actualizadas.")
    else:
        print("Dry-run. Ejecuta con --apply para persistir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
