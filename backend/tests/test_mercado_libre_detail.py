from __future__ import annotations

import unittest
from pathlib import Path

from app.scraper.mercado_libre_detail import parse_detail_html

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mercado_libre" / "id_1897276025.html"
_FIXTURE_URL = (
    "https://apartamento.mercadolibre.com.co/MCO-1897276025-venta-de-apartaestudio-en-el-poblado-_JM"
)


class TestParseDetailHtml(unittest.TestCase):
    def test_og_title_and_price_meta(self) -> None:
        url = "https://apartamento.mercadolibre.com.co/MCO-5555555-titulo-_JM"
        html = """
        <html><head>
        <meta property="og:title" content="Apto en venta" />
        <meta itemprop="price" content="350000000" />
        <meta property="og:description" content="Lindo apto" />
        </head><body></body></html>
        """
        row = parse_detail_html(html, url)
        assert row is not None
        self.assertEqual(row["external_id"], "5555555")
        self.assertEqual(row["platform"], "mercado_libre")
        self.assertEqual(row["title"], "Apto en venta")
        self.assertEqual(row["price"], 350000000.0)
        self.assertIn("Lindo", row.get("descripcion") or "")

    def test_fixture_real_estate_attributes_and_breadcrumb(self) -> None:
        if not _FIXTURE.is_file():
            self.skipTest(f"fixture missing: {_FIXTURE}")
        html = _FIXTURE.read_text(encoding="utf-8", errors="replace")
        row = parse_detail_html(html, _FIXTURE_URL)
        assert row is not None
        self.assertEqual(row["external_id"], "1897276025")
        self.assertEqual(row["price"], 620_000_000.0)
        self.assertEqual(row["habitaciones"], 1)
        self.assertEqual(row["banos"], 2)
        self.assertEqual(row["parqueaderos"], 1)
        self.assertTrue(row.get("tiene_cuarto_util"))
        self.assertEqual(row["administracion"], 833_000.0)
        self.assertAlmostEqual(row["area"], 53.0, places=0)
        self.assertEqual(row.get("barrio"), "El Poblado")
        self.assertEqual(row.get("ciudad"), "Medellín")
        self.assertEqual(row.get("zona"), "Antioquia")
        raw = row.get("datos_crudos") or {}
        self.assertIn("ml_attributes", raw)
        self.assertGreaterEqual(len(raw["ml_attributes"]), 4)
        # Misma familia que FR: ficha completa + comodidades con valor Sí
        self.assertIn("technical_sheet", raw)
        ts = raw["technical_sheet"]
        self.assertIsInstance(ts, dict)
        self.assertGreaterEqual(len(ts), 8)
        self.assertIn("comodidades", raw)
        self.assertIsInstance(raw["comodidades"], list)


if __name__ == "__main__":
    unittest.main()
