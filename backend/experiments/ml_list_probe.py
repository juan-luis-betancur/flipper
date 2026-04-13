#!/usr/bin/env python3
"""
Spike CLI: listado Mercado Libre (PoW + BS4). La lógica vive en ``app.scraper.mercado_libre_*``.

Atajo: ``ML_COOKIE`` (header Cookie del navegador). Ver ``app.scraper.mercado_libre_list`` para
notas de smoke (Railway / IP).

Uso:
  cd backend
  python experiments/ml_list_probe.py
  python experiments/ml_list_probe.py --url "https://listado.mercadolibre.com.co/..."
  python experiments/ml_list_probe.py --save-json experiments/ml_sample.json
  python experiments/ml_list_probe.py --api-probe
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

# Ejecutar como script: asegurar import de ``app``
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.scraper.mercado_libre_challenge import ML_BROWSER_HEADERS  # noqa: E402
from app.scraper.mercado_libre_list import (  # noqa: E402
    extract_listing_items,
    fetch_listing_html,
    ml_client_with_optional_cookie,
)

DEFAULT_LIST_URL = (
    "https://listado.mercadolibre.com.co/inmuebles/apartamentos/venta/antioquia/"
    "medellin/el-poblado-o-altos-del-poblado-o-el-tesoro-o-gonzalez-o-las-palmas-o-san-lucas/"
    "_PublishedToday_YES"
)

API_JSON_HEADERS = {
    "User-Agent": ML_BROWSER_HEADERS["User-Agent"],
    "Accept": "application/json",
    "Accept-Language": "es-CO,es;q=0.9",
}


def _print_api_response(label: str, r: httpx.Response) -> None:
    print(f"\n=== {label} ===", file=sys.stderr)
    print(f"HTTP {r.status_code}  URL final: {r.url}", file=sys.stderr)
    body = (r.text or "")[:800]
    print(body if body else "(vacío)", file=sys.stderr)


def run_api_probe(search_q: str, limit: int, item_id: str | None) -> int:
    token = os.getenv("ML_ACCESS_TOKEN", "").strip()
    headers = {**API_JSON_HEADERS}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("[info] Usando ML_ACCESS_TOKEN (Bearer).", file=sys.stderr)

    ok_any = False
    with httpx.Client(headers=headers, follow_redirects=True, timeout=45.0) as client:
        r_site = client.get("https://api.mercadolibre.com/sites/MCO")
        _print_api_response("GET /sites/MCO", r_site)
        if r_site.status_code == 200:
            ok_any = True
            try:
                data = r_site.json()
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1200], file=sys.stderr)
            except json.JSONDecodeError:
                pass

        r_cat = client.get("https://api.mercadolibre.com/sites/MCO/categories")
        _print_api_response("GET /sites/MCO/categories (primeros bytes)", r_cat)
        if r_cat.status_code == 200:
            ok_any = True

        params = {"q": search_q, "limit": str(limit)}
        r_search = client.get("https://api.mercadolibre.com/sites/MCO/search", params=params)
        _print_api_response("GET /sites/MCO/search", r_search)
        if r_search.status_code == 200:
            ok_any = True
            try:
                data = r_search.json()
                results = data.get("results") or []
                paging = data.get("paging") or {}
                print(
                    f"\n[ok] Búsqueda: {len(results)} resultados en esta página. paging={paging}",
                    file=sys.stderr,
                )
                for i, it in enumerate(results[: min(10, len(results))], 1):
                    iid = it.get("id", "?")
                    title = (it.get("title") or "")[:80]
                    perm = it.get("permalink") or ""
                    price = it.get("price")
                    print(f"{i:2}  id={iid}  price={price}\n    {title}\n    {perm}")
            except json.JSONDecodeError as e:
                print(f"[warn] JSON inválido: {e}", file=sys.stderr)

        if item_id:
            rid = item_id if item_id.upper().startswith("MCO") else f"MCO{item_id}"
            r_item = client.get(f"https://api.mercadolibre.com/items/{rid}")
            _print_api_response(f"GET /items/{rid}", r_item)
            if r_item.status_code == 200:
                ok_any = True
                try:
                    it = r_item.json()
                    print(
                        f"\n[ok] Ítem: {it.get('title')} | price={it.get('price')} | {it.get('permalink')}",
                        file=sys.stderr,
                    )
                except json.JSONDecodeError:
                    pass

    if not ok_any:
        print(
            "\n[resultado] Ningún endpoint devolvió 200. "
            "403 + PolicyAgent suele indicar bloqueo de IP (datacenter/VPN).",
            file=sys.stderr,
        )
        return 3
    print("\n[resultado] Al menos un endpoint de la API respondió 200.", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Spike listado Mercado Libre (PoW + BS4).")
    ap.add_argument(
        "--api-probe",
        action="store_true",
        help="Solo probar API REST api.mercadolibre.com (sin scraping de listado)",
    )
    ap.add_argument(
        "--api-q",
        default="apartamento venta medellin poblado",
        help="Query para /sites/MCO/search (con --api-probe)",
    )
    ap.add_argument(
        "--api-item",
        default=None,
        help="Opcional: id ítem ej. MCO1897276025 para GET /items/{id} (con --api-probe)",
    )
    ap.add_argument("--url", default=os.getenv("ML_LIST_URL", DEFAULT_LIST_URL))
    ap.add_argument("--limit", type=int, default=20, help="Máximo ítems a mostrar")
    ap.add_argument("--save-html", type=Path, help="Guardar HTML crudo")
    ap.add_argument("--save-json", type=Path, help="Guardar JSON con id/url/title")
    args = ap.parse_args()

    if args.api_probe:
        return run_api_probe(args.api_q, min(args.limit, 50), args.api_item)

    ml_cookie = os.getenv("ML_COOKIE", "").strip() or None
    with ml_client_with_optional_cookie(ml_cookie) as client:
        html = fetch_listing_html(client, args.url)

    if args.save_html:
        args.save_html.parent.mkdir(parents=True, exist_ok=True)
        args.save_html.write_text(html, encoding="utf-8")
        print(f"HTML guardado: {args.save_html}", file=sys.stderr)

    if len(html) < 10_000 and "verifyChallenge" in html:
        print(
            "El HTML sigue siendo la página de reto. Prueba ML_COOKIE desde el navegador.",
            file=sys.stderr,
        )
        return 2

    items = extract_listing_items(html, limit=args.limit)
    if not items:
        print("No se extrajeron ítems (selectores / HTML cambió).", file=sys.stderr)
        return 1

    for i, it in enumerate(items, 1):
        print(f"{i:3}  id={it['id']}\n     {it['url']}\n     {it['title'][:100]}")

    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {args.save_json} ({len(items)} ítems)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
