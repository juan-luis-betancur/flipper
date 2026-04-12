from __future__ import annotations

import unittest

from app.scraper.finca_raiz_age import (
    match_antiquity_range,
    parse_construction_year_only,
    parse_fr_antiquity,
)


class TestMatchAntiquityRange(unittest.TestCase):
    def test_ranges(self) -> None:
        self.assertEqual(match_antiquity_range("Menor a 1 año"), ("Menor a 1 año", 1))
        self.assertEqual(match_antiquity_range("De 1 a 8 años"), ("De 1 a 8 años", 8))
        self.assertEqual(match_antiquity_range("de 9 a 15 años"), ("De 9 a 15 años", 15))
        self.assertEqual(match_antiquity_range("De 16 a 30 años"), ("De 16 a 30 años", 30))
        self.assertEqual(match_antiquity_range("Más de 30 años"), ("Más de 30 años", 45))


class TestParseFrAntiquity(unittest.TestCase):
    def test_technical_sheet_range(self) -> None:
        sheet_list = [
            {"field": "constructionYear", "value": "De 9 a 15 años", "text": "Antigüedad"},
        ]
        r, m = parse_fr_antiquity(sheet_list, {}, {}, None)
        self.assertEqual(r, "De 9 a 15 años")
        self.assertEqual(m, 15)

    def test_antiquity_zero(self) -> None:
        r, m = parse_fr_antiquity(None, {}, {"antiquity": 0}, None)
        self.assertEqual(r, "Menor a 1 año")
        self.assertEqual(m, 1)

    def test_description_fallback(self) -> None:
        r, m = parse_fr_antiquity(
            None,
            {},
            {},
            "Bonito apto de 16 a 30 años en buen estado",
        )
        self.assertEqual(r, "De 16 a 30 años")
        self.assertEqual(m, 30)


class TestParseConstructionYearOnly(unittest.TestCase):
    def test_year(self) -> None:
        self.assertEqual(parse_construction_year_only("2018"), 2018)

    def test_range_not_year(self) -> None:
        self.assertIsNone(parse_construction_year_only("De 9 a 15 años"))


if __name__ == "__main__":
    unittest.main()
