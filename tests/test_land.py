"""M4a: the land answers back (M4 specification section 5; Ben, 19 November 2026)."""
import unittest

import numpy as np

from origins import params as P
from origins.state import World
from origins.worldgen import generate
from origins.sim import land


def world():
    w = World.new(1, 1, generate(1))
    return w, w.living_bands()[0].cell


class Land(unittest.TestCase):

    def test_hunting_draws_game_down_and_it_recovers_slowly(self):
        w, c = world()
        for _ in range(40):
            w.land_wild[c] = 100.0
            w.land_take[c] = 60.0                      # heavy hunting: 60% of the year's maxima
            land.yearly(w)
        low = float(w.game[c])
        self.assertLess(low, P.LAND_GAME_LOW)
        for _ in range(20):
            land.yearly(w)                             # hunting stops
        mid = float(w.game[c])
        self.assertGreater(mid, low)
        self.assertLess(mid, 0.9)                      # slow breeders: not back in 20 years
        self.assertLess(float(land.wild_factor(w)[c]), 1.0)

    def test_fields_clear_forest_which_regrows_over_centuries(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        for _ in range(10):
            w.land_crop[c], w.land_cap[c] = 100.0, 100.0
            land.yearly(w)
        cleared = float(w.forest[c])
        self.assertLess(cleared, 0.1)
        for _ in range(100):
            land.yearly(w)
        self.assertGreater(float(w.forest[c]), cleared)
        self.assertLess(float(w.forest[c]), 0.7)       # a century on, still well short of natural cover

    def test_cropping_wears_soil_manure_slows_it_fallow_restores_it(self):
        w, c = world()
        w2, _ = world()
        for _ in range(30):
            for x, man in ((w, 0.0), (w2, 1.0)):
                x.land_crop[c], x.land_cap[c], x.land_manure[c] = 100.0, 100.0, man
                land.yearly(x)
        self.assertLess(float(w.fertility[c]), float(w2.fertility[c]))
        worn = float(w.fertility[c])
        self.assertLess(float(land.crop_factor(w, np.array([c]))[0]), 1.0)
        for _ in range(20):
            land.yearly(w)
        self.assertGreater(float(w.fertility[c]), worn)

    def test_irrigation_on_dry_land_salts_it_and_cuts_yields(self):
        w, _ = world()
        dry = np.nonzero(w.planet.land & (w.planet.rain < 200))[0]
        if not len(dry):
            self.skipTest("no dry land on this planet")
        c = int(dry[0])
        for _ in range(40):
            w.land_crop[c], w.land_cap[c], w.land_irr[c] = 100.0, 100.0, 1.0
            land.yearly(w)
        self.assertGreater(float(w.salt[c]), P.SALT_THRESH)
        before = float(land.crop_factor(w, np.array([c]))[0])
        self.assertLess(before, P.FERT_FLOOR + (1 - P.FERT_FLOOR) * float(w.fertility[c]))
        wet = int(np.nonzero(w.planet.land & (w.planet.rain > 1500))[0][0])
        for _ in range(40):
            w.land_crop[wet], w.land_cap[wet], w.land_irr[wet] = 100.0, 100.0, 1.0
            land.yearly(w)
        self.assertEqual(float(w.salt[wet]), 0.0)      # wet land does not salt

    def test_a_crossing_is_recorded_once_with_its_history_and_named_when_people_leave(self):
        w, c = world()
        n0 = len(w.events)
        for _ in range(40):
            w.land_wild[c] = 100.0
            w.land_take[c] = 60.0
            land.yearly(w)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "land_game"]
        self.assertEqual(len(ev), 1)
        self.assertIn("since year", ev[0]["causes"][0]["note"])
        self.assertIn("game hunted out", land.history(w, c))

    def test_save_and_load_keep_the_land(self):
        from origins import persist
        w, c = world()
        w.land_wild[c], w.land_take[c] = 100.0, 60.0
        land.yearly(w)
        w.land_take[c] = 5.0                           # mid-year accounts are kept too
        w2 = persist.from_bytes(persist.to_bytes(w), planet=w.planet)
        for k in land.ARRAYS:
            self.assertTrue(np.array_equal(getattr(w2, k), getattr(w, k)), k)
        self.assertEqual(persist.digest(w2), persist.digest(w))

    def test_switched_off_the_land_changes_nothing(self):
        w, c = world()
        w.game[c] = 0.1
        w.fertility[c] = 0.1
        old = P.LAND
        P.LAND = False
        try:
            self.assertEqual(land.wild_factor(w), 1.0)
            self.assertEqual(float(land.crop_factor(w, np.array([c]))[0]), 1.0)
        finally:
            P.LAND = old


if __name__ == "__main__":
    unittest.main()
