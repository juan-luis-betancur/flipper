from __future__ import annotations

import unittest

from app.scraper.description_extract import (
    extract_from_description,
    porteria_24h_from_text,
)


class TestPorteria24hFromText(unittest.TestCase):
    def test_positives(self) -> None:
        self.assertTrue(porteria_24h_from_text("Portería 24 horas con cámaras"))
        self.assertTrue(porteria_24h_from_text("vigilancia 24/7"))
        self.assertTrue(porteria_24h_from_text("24x7 vigilancia privada"))
        self.assertTrue(porteria_24h_from_text("recepción las 24 horas"))
        self.assertTrue(porteria_24h_from_text("conserjería 24h"))
        self.assertTrue(porteria_24h_from_text("Vigilancia 24 horas"))

    def test_negatives(self) -> None:
        self.assertFalse(porteria_24h_from_text(""))
        self.assertFalse(porteria_24h_from_text("calle 24 sur"))
        self.assertFalse(porteria_24h_from_text("solo vigilancia"))
        self.assertFalse(porteria_24h_from_text("portería sin turno nocturno"))


class TestExtractFromDescriptionPorteria(unittest.TestCase):
    def test_flag_in_extract(self) -> None:
        ex = extract_from_description("Unidad con portería 24 horas.")
        self.assertTrue(ex.get("porteria_24_desde_descripcion"))


if __name__ == "__main__":
    unittest.main()
