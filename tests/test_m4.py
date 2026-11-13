"""M4a tests: the technology network."""
import unittest

import numpy as np

from origins import engine, persist
from origins.sim import technology as T
from origins.state import World
from origins.worldgen import generate


class TechniquesAsData(unittest.TestCase):
    def test_list_is_consistent(self):
        self.assertGreaterEqual(T.K, 25)
        for t in T.TECHNIQUES:
            for n in t.needs:
                self.assertLess(T.INDEX[n], T.INDEX[t.key])
            self.assertTrue(t.effect and t.need, t.key)

    def test_daughters_inherit_and_saves_round_trip(self):
        pl = generate(1)
        w = World.new(1, 1, pl)
        engine.step(w, 40)
        b = w.living_bands()[0]
        w.tech[b.id, T.INDEX["pottery"]] = 0.8
        d = w.new_band(b.cell, parent=b.id)
        self.assertAlmostEqual(float(w.tech[d.id, T.INDEX["pottery"]]), 0.8, places=5)
        w2 = persist.from_bytes(persist.to_bytes(w), pl)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        self.assertAlmostEqual(float(w2.tech[b.id, T.INDEX["pottery"]]), 0.8, places=5)

    def test_prerequisites_name_what_is_missing(self):
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        ok, missing = T.prerequisites_met(w, b, T.TECHNIQUES[T.INDEX["writing"]])
        self.assertFalse(ok)
        self.assertIn("needs tallies and tokens", missing)


if __name__ == "__main__":
    unittest.main()
