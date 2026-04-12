from __future__ import annotations

import unittest

from app.scraper.barrio_llm import infer_barrio_from_context
from app.scraper.medellin_neighborhoods import whitelist_barrios


class TestBarrioLlmStub(unittest.TestCase):
    def test_disabled_returns_null_barrio(self) -> None:
        out = infer_barrio_from_context({"barrio_resuelto": "X"}, "desc", whitelist_barrios())
        self.assertIsNone(out["barrio"])
        self.assertLess(out["confidence"], 0.01)


if __name__ == "__main__":
    unittest.main()
