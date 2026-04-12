from __future__ import annotations

import json
import unittest

from app.scraper.location_snapshot import (
    build_ubicacion_snapshot,
    json_safe,
    patch_ubicacion_from_description_extract,
)
from app.scraper.medellin_neighborhoods import fuzzy_suggest_barrio, whitelist_barrios


class TestJsonSafe(unittest.TestCase):
    def test_nested(self) -> None:
        x = {"a": [1, 2.5, None], "b": {"c": True}}
        self.assertEqual(json_safe(x), x)


class TestBuildUbicacionSnapshot(unittest.TestCase):
    def test_roundtrip_json(self) -> None:
        loc = {
            "location_main": {"name": "El Poblado", "id": 1},
            "neighbourhood": [{"name": "El Poblado"}],
            "zone": [{"name": "Zona rosa"}],
            "city": [{"name": "Medellín"}],
            "commune": [],
        }
        data = {
            "latitude": 6.21,
            "longitude": -75.57,
            "address": "CR 1 2 3",
            "showAddress": True,
            "country_id": 3,
            "locations": loc,
        }
        ub = build_ubicacion_snapshot(
            data=data,
            loc=loc,
            url="https://example.com/1",
            titulo="Apto test",
            barrio="El Poblado",
            zona="Zona rosa",
            ciudad="Medellín",
            direccion="CR 1 2 3",
            latitud=6.21,
            longitud=-75.57,
            lat_raw=6.21,
            lng_raw=-75.57,
            communes=[],
            neighbourhood_names=["El Poblado"],
        )
        json.dumps(ub)
        self.assertEqual(ub["barrio_resuelto"], "El Poblado")
        self.assertIn("fr_locations", ub)
        self.assertIn("city", ub["fr_locations"])


class TestPatchUbicacionFromDescription(unittest.TestCase):
    def test_merges_extract(self) -> None:
        row = {
            "datos_crudos": {
                "ubicacion": {"descripcion_extract": {}},
                "description_extract": {
                    "sector_desde_descripcion": "Guayabal",
                    "ciudad_desde_descripcion": "Medellin",
                },
            }
        }
        patch_ubicacion_from_description_extract(row)
        ub = row["datos_crudos"]["ubicacion"]
        self.assertEqual(ub["descripcion_extract"]["sector_desde_descripcion"], "Guayabal")


class TestWhitelistFuzzy(unittest.TestCase):
    def test_whitelist_non_empty(self) -> None:
        self.assertIn("El Poblado", whitelist_barrios())

    def test_fuzzy_typo(self) -> None:
        self.assertEqual(fuzzy_suggest_barrio("El Poblao"), "El Poblado")


if __name__ == "__main__":
    unittest.main()
