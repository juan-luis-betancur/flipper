from __future__ import annotations

import unittest
from pathlib import Path

from app.scraper.finca_raiz import parse_detail


_FIX = Path(__file__).resolve().parent / "fixtures" / "finca_raiz" / "id_193618833.txt"


class TestFincaRaizDetailFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _FIX.exists():
            raise unittest.SkipTest(f"Missing fixture {_FIX}")

    def test_parse_fixture_next_data(self) -> None:
        html = _FIX.read_text(encoding="utf-8", errors="replace")
        url = "https://www.fincaraiz.com.co/apartamento-en-venta-en-el-poblado-medellin/193618833"
        row = parse_detail(html, url)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["external_id"], "193618833")
        self.assertEqual(row["price"], 720_000_000)
        self.assertEqual(row["habitaciones"], 3)
        self.assertEqual(row["banos"], 2)
        self.assertEqual(row["parqueaderos"], 1)
        self.assertEqual(row["piso"], 7)
        self.assertEqual(row["estrato"], 4)
        self.assertEqual(row["area"], 75)
        self.assertEqual(row.get("antiguedad_rango"), "Menor a 1 año")
        self.assertEqual(row.get("antiguedad_max_anos"), 1)
        self.assertEqual(row.get("antiguedad"), 1)
        self.assertEqual(row["barrio"], "El Poblado")
        self.assertEqual(row["ciudad"], "Medellín")
        self.assertAlmostEqual(row["latitud"], 6.2226615, places=6)
        self.assertAlmostEqual(row["longitud"], -75.5774838, places=6)
        self.assertTrue(row.get("tiene_ascensor"))
        self.assertTrue(row.get("tiene_piscina"))
        self.assertTrue(row.get("tiene_porteria"))
        self.assertTrue(row.get("tiene_porteria_24h"))
        fotos = row.get("fotos") or []
        self.assertGreaterEqual(len(fotos), 11)
        dc = row.get("datos_crudos") or {}
        self.assertIn("comodidades", dc)
        self.assertGreater(len(dc["comodidades"]), 10)
        ub = dc.get("ubicacion") or {}
        self.assertEqual(ub.get("schema_version"), 1)
        self.assertIn("fr_locations", ub)
        self.assertEqual(ub.get("barrio_resuelto"), "El Poblado")


if __name__ == "__main__":
    unittest.main()
