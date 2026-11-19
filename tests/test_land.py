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


def hunt(w, pressure):
    """A peopled region: every land cell hunted at this pressure."""
    w.land_wild[w.planet.land] = 100.0
    w.land_take[w.planet.land] = 100.0 * pressure


class Land(unittest.TestCase):

    def test_hunting_draws_game_down_and_it_recovers_slowly(self):
        w, c = world()
        for _ in range(60):
            hunt(w, 0.49)                              # ordinary pressure on lived-in land
            land.yearly(w)
        low = float(w.game[c])
        self.assertLess(low, P.LAND_GAME_LOW)
        for _ in range(20):
            land.yearly(w)                             # hunting stops
        mid = float(w.game[c])
        self.assertGreater(mid, low)
        self.assertLess(mid, 0.9)                      # slow breeders: not back in 20 years
        self.assertLess(float(land.wild_factor(w)[c]), 1.0)

    def test_faster_breeders_hold_up_under_the_same_hunting(self):
        w, c = world()
        for _ in range(60):
            hunt(w, 0.49)
            land.yearly(w)
        self.assertLess(float(w.game[c]), P.LAND_GAME_LOW)
        self.assertGreater(float(w.game_fast[c]), 0.6)              # calibrated to settle near 0.7

    def test_fields_clear_forest_which_regrows_over_centuries(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        for _ in range(10):
            w.land_work[c], w.land_seasons[c] = 1.0, 1.0
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
                x.land_work[c], x.land_seasons[c], x.land_manure[c] = 1.0, 1.0, man
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
            w.land_work[c], w.land_seasons[c], w.land_irr[c] = 1.0, 1.0, 1.0
            land.yearly(w)
        self.assertGreater(float(w.salt[c]), P.SALT_THRESH)
        before = float(land.crop_factor(w, np.array([c]))[0])
        self.assertLess(before, P.FERT_FLOOR + (1 - P.FERT_FLOOR) * float(w.fertility[c]))
        wet = int(np.nonzero(w.planet.land & (w.planet.rain > 1500))[0][0])
        for _ in range(40):
            w.land_work[wet], w.land_seasons[wet], w.land_irr[wet] = 1.0, 1.0, 1.0
            land.yearly(w)
        self.assertEqual(float(w.salt[wet]), 0.0)      # wet land does not salt

    def test_a_crossing_is_recorded_once_with_its_history_and_named_when_people_leave(self):
        w, c = world()
        n0 = len(w.events)
        for _ in range(60):
            hunt(w, 0.49)
            land.yearly(w)
        ev = [w.events[i] for i in range(n0, len(w.events))
              if w.events[i]["kind"] == "land_game" and w.events[i]["cell"] == c]
        self.assertEqual(len(ev), 1)
        self.assertIn("since year", ev[0]["causes"][0]["note"])
        self.assertIn("game hunted out", land.history(w, c))

    def test_save_and_load_keep_the_land(self):
        from origins import persist
        w, c = world()
        hunt(w, 0.49)
        land.yearly(w)
        w.land_take[c] = 5.0                           # mid-year accounts are kept too
        w2 = persist.from_bytes(persist.to_bytes(w), planet=w.planet)
        for k in land.ARRAYS:
            self.assertTrue(np.array_equal(getattr(w2, k), getattr(w, k)), k)
        self.assertEqual(persist.digest(w2), persist.digest(w))

    def test_crowding_shortens_fallow(self):
        """Farmers on cropland set fallow (Ben, 19 November 2026; Codex review 020): foragers do not."""
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        c = 2
        b.cell = c
        w.bands_changed()
        _, suit = farming.land_tables(w)
        k = [i for i in farming.PLANTS if suit[c, i] > 0][0]
        land.yearly(w)
        open_land = float(w.fallow[c])
        self.assertAlmostEqual(open_land, P.FALLOW_MAX)
        sizes = np.zeros(len(w.bands) + 64, dtype=int)
        sizes[b.id] = int(3 * P.FARM_CAPACITY * 7)            # beyond what the farmland of the cell and ring feeds
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.farm_share[b.id] = 0.0
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[c]), P.FALLOW_MAX)     # many foragers: fallow unchanged
        w.skill[b.id, :] = 0
        w.skill[b.id, k] = 3
        w.farm_share[b.id] = 1.0
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[c]), P.FALLOW_MIN)     # as many crop farmers: annual cropping
        self.assertAlmostEqual(float(land.cropped_share(w, np.array([c]))[0]), 1 - P.FALLOW_MIN)

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


class Review020(unittest.TestCase):
    """Codex review 020 and Ben's decisions of 19 November 2026."""

    def _farmer(self, cell=2):
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = cell
        w.bands_changed()
        _, suit = farming.land_tables(w)
        k = [i for i in farming.PLANTS if suit[cell, i] > 0][0]
        w.skill[:] = 0
        w.skill[b.id, k] = 3
        w.farm_share[:] = 0
        w.farm_share[b.id] = 1.0
        return w, b, farming

    def test_a_poor_harvest_is_not_resting_land(self):
        w, b, farming = self._farmer()
        w.fallow[:] = 0.1
        uses = []
        for fert in (1.0, 0.25):
            land._clear_year(w)
            w.fertility[2] = fert
            farming.season_food_live(w, np.array([b.id]), np.array([2]), np.array([1e9]))
            uses.append(float(land.use(w)[2]))
        self.assertAlmostEqual(uses[0], 0.9)
        self.assertAlmostEqual(uses[1], 0.9)

    def test_without_fuel_no_smelting(self):
        from origins.sim import technology as T, trade
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 5020
        w.bands_changed()
        for k in ("pottery", "kilns", "copper_working", "smelting"):
            w.tech[b.id, T.INDEX[k]] = 0.9
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        T._mark(w, live, ids, cells)
        self.assertTrue(w.tech_prev_prac[b.id, T.INDEX["smelting"]])
        t0 = w.goods_ledger["tin"]["produced"]
        trade.yearly(w)
        self.assertGreater(w.goods_ledger["tin"]["produced"] - t0, 0.0)
        w.forest[:] = 0.0
        w._forest_near = None
        T.refresh(w)
        self.assertEqual(float(T.practised_quality(w)[b.id, T.INDEX["smelting"]]), 0.0)
        t0 = w.goods_ledger["tin"]["produced"]
        trade.yearly(w)
        self.assertEqual(w.goods_ledger["tin"]["produced"] - t0, 0.0)
        n0 = len(w.events)
        T._cut_off(w, live, ids, cells)
        kinds = [(e["kind"], e["data"].get("technique")) for e in w.events[n0:] if e["band"] == b.id]
        self.assertIn(("technique_no_fuel", "smelting"), kinds)

    def test_thinned_forest_gives_less_fuel(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        full = float(land.fuel(w, np.array([c]))[0])
        w.forest[:] = w.forest * 0.1
        w._forest_near = None
        thin = float(land.fuel(w, np.array([c]))[0])
        self.assertLess(thin, full)

    def test_lost_game_leaves_the_broad_pool_alone(self):
        from origins.sim import climate
        w, _ = world()
        old = P.TECH_FORAGE_GEAR
        P.TECH_FORAGE_GEAR = True
        try:
            fm = land.forest_max(w)
            c = int(np.nonzero(fm > 0)[0][0])
            before = float(climate.broad_max(w)[c])
            w.game[c], w.game_fast[c], w.forest[c] = 0.1, 0.5, 0.0
            self.assertAlmostEqual(float(climate.broad_max(w)[c]), before)
            self.assertLess(float(climate.seasonal_max(w)[c]), float(climate.seasonal_max(w, land=False)[c]))
        finally:
            P.TECH_FORAGE_GEAR = old

    def test_people_arriving_on_poor_land_record_the_crossing(self):
        w, _ = world()
        self.assertNotIn(2, {x.cell for x in w.living_bands()})
        w.game[2] = 0.1
        land.yearly(w)
        self.assertFalse(w.land_flags[2, 0])
        b = w.living_bands()[0]
        b.cell = 2
        w.bands_changed()
        w.game[2] = 0.1
        land.yearly(w)
        self.assertTrue(w.land_flags[2, 0])
        self.assertGreaterEqual(int(w.land_event[2, 0]), 0)
        self.assertIn("game hunted out", land.history(w, 2))
        w.game[2] = 0.9
        land.yearly(w)                                    # recovered: no stale event left in the slot
        self.assertEqual(int(w.land_event[2, 0]), -1)

    def test_a_move_and_a_famine_trace_to_the_land(self):
        from origins.sim import foraging, demography
        from origins import explain
        w, c = world()
        b = w.living_bands()[0]
        w.game[c], w.game_fast[c] = 0.05, 0.1
        land.yearly(w)
        w.game[c], w.game_fast[c] = 0.05, 0.1
        ev = int(w.land_event[c, 0])
        self.assertGreaterEqual(ev, 0)
        nb = [int(x) for x in w.planet.grid.neighbours[c] if x >= 0 and w.planet.land[x]]
        for other in w.living_bands():
            if other.id != b.id:
                other.cell = c                             # the others stay here, settled
        w.bands_changed()
        w.farm_share[:] = 1.0
        w.farm_share[b.id] = 0.0
        sizes = w.band_sizes()
        occ = float(sum(sizes[x.id] for x in w.living_bands()))
        sz = float(sizes[b.id])
        wf = float(land.wild_factor(w)[c])
        self.assertLess(wf, 0.8)
        w.stock[nb] = 0.0
        w.stock[c] = 100.0 * occ
        # better next door than here, but not better than here with game as it once was
        w.stock[nb[0]] = 100.0 * P.MOVE_THRESHOLD * (1 + 0.5 * (1 / wf - 1)) * sz
        n0 = len(w.events)
        foraging.move(w)
        moves = [e for e in w.events[n0:] if e["kind"] == "land_move"]
        self.assertEqual(len(moves), 1)
        self.assertIn({"event": ev}, moves[0]["causes"])
        mid = [i for i in range(n0, len(w.events)) if w.events[i]["kind"] == "land_move"][0]
        self.assertTrue(explain.resolvable(w, {"event": mid}))
        self.assertIn(f"event {mid}", b.last_move)
        b.cell = c
        w.bands_changed()
        w._binfo = None
        idx = w.alive_idx()
        one = idx[w.people.band[idx] == b.id][:1]
        demography.kill(w, one, np.array([demography.C["hunger"]]))
        causes = explain.describe(w, {"death": int(one[0])})["causes"]
        self.assertIn({"event": ev}, causes)

    def test_the_cut_off_names_only_what_was_needed(self):
        from origins.sim import technology as T, trade
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 2
        w.bands_changed()
        n = float(w.band_sizes()[b.id])
        for k in ("pottery", "kilns", "copper_working", "smelting", "bronze"):
            w.tech[b.id, T.INDEX[k]] = 0.9
        for g in ("copper", "tin", "iron"):
            w.goods[b.id, trade.GI[g]] = 0.01 * n
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        T._mark(w, live, ids, cells)
        for g in ("copper", "tin", "iron"):
            w.goods[b.id, trade.GI[g]] = 0.0
        n0 = len(w.events)
        T._cut_off(w, live, ids, cells)
        ev = {e["data"]["technique"]: e["data"]["materials"] for e in w.events[n0:]
              if e["kind"] == "technique_cut_off" and e["band"] == b.id}
        self.assertEqual(sorted(ev["bronze"]), ["copper", "tin"])

    def test_fields_clear_only_the_land_they_take(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        for _ in range(40):
            w.land_work[c], w.land_seasons[c] = 0.3, 1.0
            land.yearly(w)
        self.assertAlmostEqual(float(w.forest[c]), 0.7, delta=0.02)

    def test_switched_off_the_accounts_do_not_pile_up(self):
        w, c = world()
        old = P.LAND
        P.LAND = False
        try:
            w.land_wild[:] = 5.0
            w.land_take[:] = 5.0
            w.land_work[:] = 1.0
            land.yearly(w)
            self.assertEqual(float(w.land_wild.sum() + w.land_take.sum() + w.land_work.sum()), 0.0)
        finally:
            P.LAND = old

    def test_farmers_see_real_yields(self):
        from origins.sim import farming
        w, b, _ = self._farmer()
        nb = [int(x) for x in w.planet.grid.neighbours[2] if x >= 0 and w.planet.land[x]]
        fresh = farming.best_farm_cell(w, b, {})
        self.assertIsNotNone(fresh)
        w.fertility[fresh] = 0.0
        w.salt[fresh] = 1.0
        self.assertNotEqual(farming.best_farm_cell(w, b, {}), fresh)
        # the labour choice takes the realised return when it is lower
        w.farm_rr_real[b.id] = 0.0
        w.forage_rr[b.id] = P.FORAGE_RATE
        w.farm_share[b.id] = 1.0
        farming.yearly(w)
        self.assertLess(float(w.farm_share[b.id]), 1.0)


if __name__ == "__main__":
    unittest.main()
