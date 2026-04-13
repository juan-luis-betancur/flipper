from __future__ import annotations

import unittest

from app.telegram_bot import (
    format_property_message,
    format_scan_summary_html,
    is_guardar_command,
    parse_reply_external_id,
)


class TestFormatScanSummary(unittest.TestCase):
    def test_contains_counts_and_structure(self) -> None:
        s = format_scan_summary_html(21, 2)
        self.assertIn("Resumen del Escaneo", s)
        self.assertIn("<b>21</b>", s)
        self.assertIn("<b>2</b>", s)
        self.assertIn("Encontradas", s)
        self.assertIn("Cumplen reglas", s)
        self.assertIn("Estas son las que cumplen", s)


class TestFormatPropertyMessage(unittest.TestCase):
    def test_link_href_and_id_for_guardar(self) -> None:
        row = {
            "external_id": "193618833",
            "title": "Apartamento en Venta",
            "url": "https://www.fincaraiz.com.co/x/193618833",
            "price": 420_000_000,
            "precio_por_m2": 6_000_000,
            "area": 70,
        }
        html = format_property_message(row, index=1)
        self.assertIn("Apto #1", html)
        self.assertIn('href="https://www.fincaraiz.com.co/x/193618833"', html)
        self.assertIn("Ver publicación", html)
        self.assertIn("ID: finca_raiz:193618833", html)
        self.assertIn("$420.000.000", html)
        self.assertIn("GUARDAR", html)

    def test_parse_reply_still_works(self) -> None:
        body = format_property_message(
            {
                "external_id": "99",
                "title": "T",
                "url": "https://example.com",
                "price": 1,
                "area": 1,
                "precio_por_m2": 1,
            },
            index=1,
        )
        ext = parse_reply_external_id(body.replace("<code>", "").replace("</code>", ""))
        self.assertEqual(ext, "99")


class TestIsGuardarCommand(unittest.TestCase):
    def test_plain_and_case(self) -> None:
        self.assertTrue(is_guardar_command("guardar"))
        self.assertTrue(is_guardar_command("GUARDAR"))
        self.assertTrue(is_guardar_command("  Guardar  "))

    def test_punctuation(self) -> None:
        self.assertTrue(is_guardar_command("guardar!"))
        self.assertTrue(is_guardar_command("…guardar…"))
        self.assertTrue(is_guardar_command("guardar."))

    def test_rejects_extra_words(self) -> None:
        self.assertFalse(is_guardar_command("quiero guardar"))
        self.assertFalse(is_guardar_command("guardar esto"))
        self.assertFalse(is_guardar_command(""))

    def test_parse_reply_with_code_tags(self) -> None:
        body = format_property_message(
            {
                "external_id": "77",
                "title": "T",
                "url": "https://example.com",
                "price": 1,
                "area": 1,
                "precio_por_m2": 1,
            },
            index=2,
        )
        ext = parse_reply_external_id(body)
        self.assertEqual(ext, "77")


if __name__ == "__main__":
    unittest.main()
