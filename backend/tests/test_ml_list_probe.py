"""Tests unitarios Mercado Libre (PoW + extracción de listado)."""
from __future__ import annotations

import unittest

from app.scraper.mercado_libre_challenge import solve_bmstate_pow
from app.scraper.mercado_libre_list import extract_listing_items, listing_url_for_page, strip_listing_pagination


class TestSolveBmstatePow(unittest.TestCase):
    def test_difficulty_zero(self) -> None:
        self.assertEqual(solve_bmstate_pow("abc", "0"), 0)

    def test_small_difficulty(self) -> None:
        import hashlib

        token = "9044fc2b1b47a10eeeba4899dbc6ca22889423b72704469b26ea0f9e6bb2"
        a = solve_bmstate_pow(token, "2")
        h = hashlib.sha256((token + str(a)).encode()).hexdigest()
        self.assertTrue(h.startswith("00"))


class TestExtractItems(unittest.TestCase):
    def test_from_anchor_and_embedded_url(self) -> None:
        html = """
        <html><body>
        <a href="https://apartamento.mercadolibre.com.co/MCO-111-foo-bar-_JM">Título A</a>
        <script>var x="https://apartamento.mercadolibre.com.co/MCO-222-otro-slug-_JM"</script>
        </body></html>
        """
        items = extract_listing_items(html)
        ids = {x["id"] for x in items}
        self.assertEqual(ids, {"111", "222"})


class TestListingPaginationUrls(unittest.TestCase):
    def test_strip_and_pages(self) -> None:
        base = "https://listado.mercadolibre.com.co/foo/bar"
        p1 = f"{base}/_Desde_49_NoIndex_True"
        self.assertEqual(strip_listing_pagination(p1), base)
        self.assertEqual(listing_url_for_page(base, 0), base)
        self.assertEqual(listing_url_for_page(p1, 1), f"{base}/_Desde_49_NoIndex_True")
        self.assertEqual(listing_url_for_page(base, 2), f"{base}/_Desde_97_NoIndex_True")


if __name__ == "__main__":
    unittest.main()
