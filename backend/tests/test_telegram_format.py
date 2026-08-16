from __future__ import annotations

import unittest

from app.telegram_bot import (
    format_digest_html,
    format_property_block,
    split_telegram_html,
)

APTO_1 = {
    "platform": "mercado_libre",
    "external_id": "123456",
    "title": "Apartamento en Venta",
    "url": "https://apartamento.mercadolibre.com.co/MCO-123456-x-_JM",
    "price": 680_000_000,
    "area": 136,
    "precio_por_m2": 5_000_000,
}

APTO_2 = {
    "platform": "finca_raiz",
    "external_id": "194121768",
    "title": "Apartamento en Venta en El Poblado",
    "url": "https://www.fincaraiz.com.co/x/194121768",
    "price": 500_000_000,
    "area": 89,
    "precio_por_m2": 5_617_978,
}


class TestFormatPropertyBlock(unittest.TestCase):
    def test_fields_and_link(self) -> None:
        html = format_property_block(APTO_1, index=1)
        self.assertIn("Apto #1", html)
        self.assertIn('href="https://apartamento.mercadolibre.com.co/MCO-123456-x-_JM"', html)
        self.assertIn("Ver Publicación", html)
        self.assertIn("$680.000.000", html)
        self.assertIn("136 m²", html)
        self.assertIn("$5.000.000", html)

    def test_no_guardar_leftovers(self) -> None:
        html = format_property_block(APTO_1, index=1)
        self.assertNotIn("ID:", html)
        self.assertNotIn("GUARDAR", html)

    def test_omits_missing_fields(self) -> None:
        html = format_property_block(
            {"url": "https://example.com", "price": None, "area": None, "precio_por_m2": None},
            index=3,
        )
        self.assertIn("Apto #3", html)
        self.assertNotIn("Precio:", html)
        self.assertNotIn("Área:", html)


class TestFormatDigest(unittest.TestCase):
    def test_breakdown_and_counts(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 9, "finca_raiz": 5},
            total_encontradas=14,
            matches=[APTO_1, APTO_2],
        )
        self.assertIn("Resumen del Escaneo", s)
        self.assertIn("Encontradas:</b> 14", s)
        self.assertIn("Mercado Libre: 9", s)
        self.assertIn("Finca Raíz: 5", s)
        self.assertIn("Cumplen reglas:</b> 2", s)
        self.assertIn("Estas son las que cumplen", s)
        self.assertIn("Apto #1", s)
        self.assertIn("Apto #2", s)

    def test_platform_order_is_stable(self) -> None:
        s = format_digest_html(
            por_plataforma={"finca_raiz": 5, "mercado_libre": 9},
            total_encontradas=14,
            matches=[],
        )
        self.assertLess(s.index("Mercado Libre"), s.index("Finca Raíz"))

    def test_hides_platforms_with_zero(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 0, "finca_raiz": 5},
            total_encontradas=5,
            matches=[],
        )
        self.assertNotIn("Mercado Libre", s)
        self.assertIn("Finca Raíz: 5", s)

    def test_found_but_none_match(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 9, "finca_raiz": 5},
            total_encontradas=14,
            matches=[],
        )
        self.assertIn("Cumplen reglas:</b> 0", s)
        self.assertIn("Ninguna de las encontradas cumple", s)
        self.assertNotIn("Estas son las que cumplen", s)

    def test_found_nothing_at_all(self) -> None:
        s = format_digest_html(por_plataforma={}, total_encontradas=0, matches=[])
        self.assertIn("Encontradas:</b> 0", s)
        self.assertIn("no encontré publicaciones nuevas", s)


class TestSplitTelegramHtml(unittest.TestCase):
    def test_short_digest_is_one_message(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 9, "finca_raiz": 5},
            total_encontradas=14,
            matches=[APTO_1, APTO_2],
        )
        self.assertEqual(len(split_telegram_html(s)), 1)

    def test_long_digest_splits_within_limit(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 60},
            total_encontradas=60,
            matches=[APTO_1] * 60,
        )
        partes = split_telegram_html(s)
        self.assertGreater(len(partes), 1)
        for parte in partes:
            self.assertLessEqual(len(parte), 4096)

    def test_split_preserves_every_apto(self) -> None:
        s = format_digest_html(
            por_plataforma={"mercado_libre": 60},
            total_encontradas=60,
            matches=[APTO_1] * 60,
        )
        unido = "".join(split_telegram_html(s))
        self.assertEqual(unido.count("Apto #"), 60)


if __name__ == "__main__":
    unittest.main()
