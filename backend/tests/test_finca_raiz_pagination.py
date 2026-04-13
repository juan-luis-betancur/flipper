from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.scraper.finca_raiz import (
    _gather_listing_urls_across_pages,
    _listing_url_for_page,
    _strip_listing_pagination,
    parsed_total_listing_pages,
)


def _html_with_summary(summary: str, extra: str = "") -> str:
    return f"<html><body>{summary}{extra}</body></html>"


def _html_with_listing_link(ext: str) -> str:
    return (
        f'<html><body><a href="https://www.fincaraiz.com.co/apartamento-en-venta-x/{ext}">x</a></body></html>'
    )


class TestStripListingPagination(unittest.TestCase):
    def test_removes_pagina_suffix(self) -> None:
        self.assertEqual(
            _strip_listing_pagination("https://www.fincaraiz.com.co/venta/apartamentos/x/publicado-hoy/pagina2"),
            "https://www.fincaraiz.com.co/venta/apartamentos/x/publicado-hoy",
        )

    def test_removes_trailing_slash_before_strip(self) -> None:
        self.assertEqual(
            _strip_listing_pagination("https://www.fincaraiz.com.co/foo/pagina12/"),
            "https://www.fincaraiz.com.co/foo",
        )

    def test_preserves_base_without_pagina(self) -> None:
        u = "https://www.fincaraiz.com.co/venta/apartamentos/antioquia/el-poblado/publicado-ultimos-15-dias"
        self.assertEqual(_strip_listing_pagination(u), u)


class TestListingUrlForPage(unittest.TestCase):
    def test_page_one_is_base(self) -> None:
        b = "https://www.fincaraiz.com.co/venta/apartamentos/antioquia/x/y"
        self.assertEqual(_listing_url_for_page(b, 1), b)

    def test_page_two_suffix(self) -> None:
        b = "https://www.fincaraiz.com.co/venta/apartamentos/antioquia/x/y"
        self.assertEqual(_listing_url_for_page(b, 2), f"{b}/pagina2")

    def test_strips_double_slash_from_base(self) -> None:
        b = "https://example.com/path/"
        self.assertEqual(_listing_url_for_page(b, 2), "https://example.com/path/pagina2")


class TestParsedTotalListingPages(unittest.TestCase):
    def test_mas_de_400_uses_max_pagina_href(self) -> None:
        """El resumen «más de 400» no casa con el regex numérico; el máximo /paginaN define las páginas."""
        base = "https://www.fincaraiz.com.co/venta/apartamentos/medellin/x"
        html = _html_with_summary(
            "Mostrando 1 - 21 de más de 400 resultados",
            extra=(
                f'<nav><a href="{base}/pagina2">2</a>'
                f'<a href="{base}/pagina7">7</a>'
                f'<a href="{base}/pagina42">42</a>'
                f'<a href="#">next</a></nav>'
            ),
        )
        self.assertEqual(parsed_total_listing_pages(html), 42)

    def test_pagina_href_relative_paths(self) -> None:
        html = (
            "<html><body>"
            '<a href="/venta/apartamentos/antioquia/foo/publicado-hoy/pagina3">3</a>'
            '<a href="/venta/apartamentos/antioquia/foo/publicado-hoy/pagina11/">11</a>'
            "</body></html>"
        )
        self.assertEqual(parsed_total_listing_pages(html), 11)

    def test_pagina_href_capped_at_100(self) -> None:
        u = "https://www.fincaraiz.com.co/venta/apartamentos/x/y/pagina150"
        html = f'<html><body><a href="{u}">150</a></body></html>'
        self.assertEqual(parsed_total_listing_pages(html), 100)

    def test_href_priority_over_summary(self) -> None:
        """Si hay enlaces pagina, prevalecen sobre el cálculo por texto (p. ej. última página visible en UI)."""
        base = "https://www.fincaraiz.com.co/venta/apartamentos/z"
        html = _html_with_summary(
            "Mostrando 1 - 21 de 225 resultados",
            extra=f'<a href="{base}/pagina42">42</a>',
        )
        self.assertEqual(parsed_total_listing_pages(html), 42)

    def test_typical_summary_225_and_21(self) -> None:
        html = _html_with_summary("Mostrando 1 - 21 de 225 resultados")
        self.assertEqual(parsed_total_listing_pages(html), 11)

    def test_thousands_in_total(self) -> None:
        html = _html_with_summary("Mostrando 1 - 21 de 1.225 resultados")
        self.assertEqual(parsed_total_listing_pages(html), 59)

    def test_case_insensitive(self) -> None:
        html = _html_with_summary("mostrando 22 - 42 de 225 resultados")
        self.assertEqual(parsed_total_listing_pages(html), 11)

    def test_caps_at_max_listing_pages(self) -> None:
        # 5000 / 10 = 500 páginas -> tope 100
        html = _html_with_summary("Mostrando 1 - 10 de 5000 resultados")
        self.assertEqual(parsed_total_listing_pages(html), 100)

    def test_no_match_returns_none(self) -> None:
        self.assertIsNone(parsed_total_listing_pages("<html></html>"))

    def test_pagina_on_non_listing_href_ignored_uses_summary(self) -> None:
        """Solo cuentan hrefs bajo /venta/apartamentos/."""
        html = _html_with_summary(
            "Mostrando 1 - 21 de 225 resultados",
            extra='<a href="https://www.fincaraiz.com.co/foo/pagina99">bad</a>',
        )
        self.assertEqual(parsed_total_listing_pages(html), 11)

    def test_invalid_range_returns_none(self) -> None:
        self.assertIsNone(parsed_total_listing_pages("Mostrando 30 - 10 de 100 resultados"))


class TestGatherListingUrlsAcrossPages(unittest.TestCase):
    def test_known_pages_fetches_until_max_props(self) -> None:
        first = _html_with_listing_link("100001")
        p2 = _html_with_listing_link("100002")
        p3 = _html_with_listing_link("100003")
        client = MagicMock()

        with patch("app.scraper.finca_raiz.fetch_url", side_effect=[p2, p3]) as mock_fetch:
            urls = _gather_listing_urls_across_pages(client, "https://example.com/list", 2, first, known_pages=5)

        self.assertEqual(len(urls), 2)
        self.assertIn("100001", urls[0])
        self.assertIn("100002", urls[1])
        self.assertEqual(mock_fetch.call_count, 1)

    def test_fallback_stops_on_empty_second_page(self) -> None:
        first = _html_with_listing_link("200001")
        client = MagicMock()

        with patch("app.scraper.finca_raiz.fetch_url", return_value="<html></html>") as mock_fetch:
            urls = _gather_listing_urls_across_pages(
                client, "https://example.com/list", 50, first, known_pages=None
            )

        self.assertEqual(len(urls), 1)
        mock_fetch.assert_called_once()

    def test_fallback_stops_when_no_new_unique(self) -> None:
        first = _html_with_listing_link("300001")
        dup = first  # mismo enlace otra vez
        client = MagicMock()

        with patch("app.scraper.finca_raiz.fetch_url", return_value=dup) as mock_fetch:
            urls = _gather_listing_urls_across_pages(
                client, "https://example.com/list", 50, first, known_pages=None
            )

        self.assertEqual(len(urls), 1)
        mock_fetch.assert_called_once()

    def test_known_pages_no_extra_fetch_when_first_page_fills_max(self) -> None:
        first = _html_with_listing_link("400001") + _html_with_listing_link("400002")
        client = MagicMock()

        with patch("app.scraper.finca_raiz.fetch_url") as mock_fetch:
            urls = _gather_listing_urls_across_pages(
                client, "https://example.com/list", 1, first, known_pages=10
            )

        self.assertEqual(len(urls), 1)
        mock_fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
