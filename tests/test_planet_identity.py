"""Every machine must build the same planets, to the last digit. Run: python -m pytest tests/test_planet_identity.py

The expected values were computed on 9 November 2026. If world generation is changed on purpose, update them
(and say so in the build notes): every save made before the change will no longer load.
"""
import hashlib
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from origins.worldgen import generate  # noqa: E402

FIELDS = ["elevation", "land", "lake", "downstream", "flow", "river", "coast", "temp_mean", "temp_season", "rain",
          "biome", "capacity", "season_food", "region", "plate", "volcanic", "seismic"]
EXPECTED = {1: "678dafc917", 2: "84f93b3c2c", 3: "70749bf427", 4: "7407f2d325", 5: "f1ed677f05"}


def exact(p) -> str:
    h = hashlib.sha256()
    for k in FIELDS:
        h.update(np.ascontiguousarray(getattr(p, k)).tobytes())
    for k in sorted(p.domesticables):
        h.update(p.domesticables[k].tobytes())
    h.update(str(p.start_cell).encode())
    return h.hexdigest()[:10]


class PlanetIdentity(unittest.TestCase):
    def test_same_planets_everywhere(self):
        for seed, want in EXPECTED.items():
            self.assertEqual(exact(generate(seed)), want, f"planet {seed} differs on this machine")


if __name__ == "__main__":
    unittest.main()
