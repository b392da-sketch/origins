"""M2 observatory tests: the historical clock and the farming views. Run: python -m pytest tests/test_m2.py"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from origins import engine, explain, server  # noqa: E402
from origins.state import World  # noqa: E402
from origins.worldgen import generate  # noqa: E402


class Observatory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = World.new(1, 1, generate(1))
        engine.step(cls.w, 4 * 300)

    def test_clock_switches_at_first_village(self):
        w = self.w
        self.assertEqual(server.years_per_day(w), 300)
        b = w.living_bands()[0]
        old = w.first_village
        w.first_village = w.event("first_farming_village", cell=b.cell, band=b.id,
                                  causes=[{"note": "test"}], species="grain", year=w.year)
        try:
            self.assertEqual(server.years_per_day(w), 20)
            self.assertAlmostEqual(server.HISTORICAL_RATE * 86400 / 4, 20)
            fv = server.first_village(w)
            self.assertIn("first farming village", fv["title"])
            self.assertTrue(explain.resolvable(w, {"event": fv["event"]}))
        finally:
            w.first_village = old

    def test_farming_views_serialise(self):
        w = self.w
        json.dumps(server.bands_view(w))
        json.dumps(server.summary(w))
        json.dumps(server.farming_story(w), default=float)
        json.dumps(server.band_detail(w, w.living_bands()[0].id), default=float)


if __name__ == "__main__":
    unittest.main()
