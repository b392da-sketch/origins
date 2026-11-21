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

    def test_fallow_gives_way_to_need(self):
        """Farmers crop as much land as they can work; the rest rests (Ben, 19 November 2026, after review 020)."""
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        c = 2
        b.cell = c
        w.bands_changed()
        _, suit = farming.land_tables(w)
        k = [i for i in farming.PLANTS if suit[c, i] > 0][0]
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[c]), P.FALLOW_MAX)      # nobody farms: long fallow
        w.skill[b.id, :] = 0
        w.skill[b.id, k] = 3
        w.farm_share[:] = 0.0
        w.farm_share[b.id] = 1.0
        ids, cells = np.array([b.id]), np.array([c])
        farming.season_food_live(w, ids, cells, np.array([1e9]))      # more hands than land: they need it all
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[c]), P.FALLOW_MIN)
        self.assertAlmostEqual(float(land.cropped_share(w, cells)[0]), 1 - P.FALLOW_MIN)
        farming.season_food_live(w, ids, cells, np.array([1e-3]))     # a few hands: most of the land rests
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[c]), P.FALLOW_MAX)

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
        from origins.sim import minorlog
        n0 = minorlog.size(w, "land_move")
        foraging.move(w)
        moves = minorlog.since(w, "land_move", n0)                   # rows of the compact log (Ben, 22 Nov 2026)
        self.assertEqual(len(moves), 1)
        self.assertIn({"event": ev}, moves[0]["causes"])
        mid = n0
        self.assertTrue(explain.resolvable(w, {"log": ["land_move", mid]}))
        self.assertIn(f"land move {mid}", b.last_move)
        b.cell = c
        w.bands_changed()
        w._binfo = None
        idx = w.alive_idx()
        mine = idx[w.people.band[idx] == b.id]
        # the land as a contributing cause, with the amounts (Ben, 20 November 2026, after Codex review 022): a
        # loss short of the shortfall is cited too, through one land_hunger event that states both
        land.note_account(w, np.array([b.id]), np.array([5.0]), np.array([2.0]))
        demography.kill(w, mine[:1], np.array([demography.C["hunger"]]))
        lh = int(w.people.death_land[mine[0]])
        self.assertGreaterEqual(lh, 0)
        self.assertEqual(w.events[lh]["kind"], "land_hunger")
        self.assertIn({"event": lh}, explain.describe(w, {"death": int(mine[0])})["causes"])
        self.assertIn({"event": ev}, w.events[lh]["causes"])
        self.assertIn("lacked 5", w.events[lh]["causes"][0]["note"])
        self.assertIn("took 2 from its wild food", w.events[lh]["causes"][0]["note"])
        self.assertTrue(explain.resolvable(w, {"death": int(mine[0])}))
        w.t += 1                                                        # next season: no land loss, no citation
        land.note_account(w, np.array([b.id]), np.array([5.0]), np.array([0.0]))
        w._binfo = None
        demography.kill(w, mine[1:2], np.array([demography.C["hunger"]]))
        self.assertEqual(int(w.people.death_land[mine[1]]), -1)

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


class Review021(unittest.TestCase):
    """Codex review 021 and Ben's decisions of 20 November 2026."""

    def test_wood_is_taken_where_it_grows(self):
        from origins.sim import technology as T, trade
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 5020
        w.bands_changed()
        for k in ("pottery", "kilns", "copper_working", "smelting"):
            w.tech[b.id, T.INDEX[k]] = 0.9
        keep = float(w.forest[5039])
        w.forest[:] = 0.0
        w.forest[5039] = keep
        w._forest_near = None
        T.refresh(w)
        trade.yearly(w)
        self.assertEqual(float(w.land_fuel[5020]), 0.0)
        self.assertGreater(float(w.land_fuel[5039]), 0.0)          # the only wooded cell within reach
        land.yearly(w)
        self.assertLess(float(w.forest[5039]), keep)

    def test_wood_is_gathered_across_the_woods_within_reach(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        land.note_fuel(w, np.array([c]), np.array([1000.0]))
        from origins.sim.language import ring2
        near = [int(x) for x in ring2(w)[c] if w.forest[int(x)] > 0]
        self.assertGreater(len(near), 1)
        self.assertAlmostEqual(float(w.land_fuel.sum()), 1000.0)
        self.assertLess(float(w.land_fuel.max()), 1000.0)            # spread, not all on one cell
        self.assertLessEqual(P.FOREST_FUEL * 1000.0, 0.005)

    def test_a_band_that_left_farming_judges_fresh_land_afresh(self):
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 2
        w.bands_changed()
        _, suit = farming.land_tables(w)
        k = [i for i in farming.PLANTS if suit[2, i] > 0][0]
        w.skill[b.id] = 0
        w.skill[b.id, k] = 3
        w.forage_rr[b.id] = 1.0
        w.farm_rr_real[b.id], w.farm_rr_cell[b.id] = 0.05, 2
        w.farm_share[b.id] = 0.011
        farming.yearly(w)
        self.assertEqual(float(w.farm_share[b.id]), 0.0)
        farming.yearly(w)
        self.assertGreater(float(w.farm_share[b.id]), 0.1)
        w.farm_rr_real[b.id], w.farm_rr_cell[b.id] = 0.05, 999        # earned elsewhere: not this land's return
        self.assertTrue(np.isnan(farming._real_rr(w, np.array([b.id]), np.array([2]))[0]))

    def test_crop_use_is_measured_against_crop_land(self):
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 778
        w.bands_changed()
        g = farming.SPECIES.index("wild_grain")
        w.skill[:] = 0
        w.skill[b.id, g] = 3
        w.farm_share[:] = 0
        w.farm_share[b.id] = 1.0
        w.fallow[:] = 0.1
        _, suit = farming.land_tables(w)
        _kp, vp, _ka, _va = farming.best_all(w, np.array([b.id]), np.array([778]))
        eff = 0.5 * P.FARM_CAPACITY * suit[778, g] * P.SEASON_DAYS / (P.FARM_RATE * vp[0]) * P.FORAGE_RATE
        land._clear_year(w)
        farming.season_food_live(w, np.array([b.id]), np.array([778]), np.array([eff]))
        self.assertAlmostEqual(float(land.use(w)[778]), 0.5, places=3)
        land.yearly(w)
        self.assertAlmostEqual(float(w.fallow[778]), 0.5, places=3)

    def test_idle_irrigators_do_not_salt_the_land(self):
        from origins.sim import farming, technology as T
        w, _ = world()
        a, c2 = w.living_bands()[0], w.living_bands()[1]
        for x in (a, c2):
            x.cell = 778
        w.bands_changed()
        g = farming.SPECIES.index("wild_grain")
        w.skill[:] = 0
        w.skill[[a.id, c2.id], g] = 3
        w.farm_share[:] = 0
        w.farm_share[[a.id, c2.id]] = 1.0
        w.tech[c2.id, T.INDEX["irrigation"]] = 0.9
        T.refresh(w)
        w.fallow[:] = 0.1
        land._clear_year(w)
        farming.season_food_live(w, np.array([a.id, c2.id]), np.array([778, 778]), np.array([1e9, 0.0]))
        s0 = float(w.salt[778])
        land.yearly(w)
        self.assertEqual(float(w.salt[778]), s0)

    def test_a_band_that_would_leave_anyway_is_not_moved_by_the_land(self):
        from origins.sim import foraging
        w, c = world()
        b = w.living_bands()[0]
        j = land.KINDS.index("game")
        w.land_flags[c, j], w.land_event[c, j] = True, 0
        n = w.planet.n
        cache = {"natural": np.full(n, 100.0), "wf": np.full(n, 0.8)}
        # Codex's case: 89 per person here after regrowth, 100 with natural regrowth, 121.47 next door
        self.assertEqual(foraging._land_move(w, b, 89.0, 121.47, 1.0, cache), -1)
        self.assertGreaterEqual(foraging._land_move(w, b, 89.0, 112.0, 1.0, cache), 0)

    def test_famine_cites_only_the_food_the_band_used(self):
        w, c = world()
        b = w.living_bands()[0]
        js, jg, jf = land.KINDS.index("soil"), land.KINDS.index("game"), land.KINDS.index("forest")
        w.fertility[c] = 0.5
        w.land_flags[c, js], w.land_event[c, js] = True, 7
        land.note_account(w, np.array([b.id]), np.array([5.0]), np.array([0.0]))
        self.assertEqual(land.felt(w, b.id, c), [])                   # grew no crops: soil not cited
        w.game[c], w.forest[c] = 0.1, 0.95 * float(land.forest_max(w)[c])
        w.land_flags[c, jf], w.land_event[c, jf] = True, 1            # forest event first by number
        w.land_flags[c, jg], w.land_event[c, jg] = True, 2
        land.note_account(w, np.array([b.id]), np.array([5.0]), np.array([6.0]))
        self.assertEqual(land.felt(w, b.id, c)[0], 2)                  # the larger loss first

    def test_wood_and_imports_lost_together_are_recorded(self):
        from origins.sim import technology as T, trade
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 2
        w.bands_changed()
        n = float(w.band_sizes()[b.id])
        for k in ("pottery", "kilns", "copper_working", "smelting", "bronze"):
            w.tech[b.id, T.INDEX[k]] = 0.9
        w.goods[b.id, trade.GI["copper"]] = 0.01 * n
        w.goods[b.id, trade.GI["tin"]] = 0.01 * n
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        T._mark(w, live, ids, cells)
        w.goods[b.id, trade.GI["tin"]] = 0.0
        w.forest[:] = 0.0
        w._forest_near = None
        T.refresh(w)
        n0 = len(w.events)
        T._cut_off(w, live, ids, cells)
        ev = {e["data"]["technique"]: e for e in w.events[n0:] if e["band"] == b.id and e["kind"] == "technique_cut_off"}
        self.assertIn("bronze", ev)
        self.assertEqual(ev["bronze"]["data"]["materials"], ["tin"])
        self.assertTrue(ev["bronze"]["data"]["wood"])

    def test_taking_up_wood_work_again_needs_more_forest(self):
        from origins.sim import technology as T
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = int(np.nonzero(land.forest_max(w) > 0)[0][0])
        w.bands_changed()
        k = T.INDEX["canoes"]
        w.tech[b.id, k] = 0.9
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        T._prev_arrays(w)
        w.forest[:] = 0.15 * land.forest_max(w)
        w._forest_near = None
        if float(land.forest_near(w)[b.cell]) < P.FUEL_MIN:
            self.skipTest("no forest near this band")
        i = list(ids).index(b.id)
        w.tech_prev_prac[b.id, :] = False
        w.tech_prev_wood[b.id] = False
        self.assertFalse(T._possible(w, ids, cells)[i, k])            # not practised: needs 20%
        w.tech_prev_prac[b.id, k] = True
        w.tech_prev_wood[b.id] = True
        self.assertTrue(T._possible(w, ids, cells)[i, k])             # practised: keeps going down to 10%


class Review022(unittest.TestCase):
    """Codex review 022 and Ben's decision of 20 November 2026 (the land as a contributing cause of hunger)."""

    def test_a_herd_does_not_enlarge_the_fields(self):
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = 778
        w.bands_changed()
        w.skill[:] = 0
        w.skill[b.id, farming.SPECIES.index("wild_grain")] = 3
        w.skill[b.id, farming.SPECIES.index("wild_goat")] = 1.0      # tended goats, wild here (Codex's case)
        w.farm_share[:] = 0
        w.farm_share[b.id] = 1.0
        wild, suit = farming.land_tables(w)
        wild = wild.copy()
        wild[778, farming.SPECIES.index("wild_goat")] = True
        real = farming.land_tables
        farming.land_tables = lambda _w: (wild, suit)
        try:
            kp, vp, ka, va = farming.best_all(w, np.array([b.id]), np.array([778]))
            self.assertGreater(va[0], 0)
            self.assertGreater(suit[778, int(ka[0])], suit[778, int(kp[0])])
            w.fallow[:] = 0.2
            land._clear_year(w)
            farming.season_food_live(w, np.array([b.id]), np.array([778]), np.array([1e12]))
        finally:
            farming.land_tables = real
        self.assertLessEqual(float(w.land_work[778]), 0.8 + 1e-9)     # no more than the land under crops
        self.assertLessEqual(float(w.land_need[778]), 1.0)

    def test_the_wild_loss_is_the_same_harvest_run_again(self):
        from origins.sim import foraging
        dm, db = foraging.wild_gain(np.array([100.0]), np.array([20.0]), np.array([100.0]), np.array([0.0]),
                                    np.array([0.0]))
        self.assertAlmostEqual(float(dm[0]), 4.64, places=2)           # Codex's figure, not 12.64
        self.assertEqual(float(db[0]), 0.0)
        dm, db = foraging.wild_gain(np.array([100.0]), np.array([20.0]), np.array([300.0]), np.array([300.0]),
                                    np.array([100.0]))
        self.assertLess(float(db[0]), 0.0)                              # more ordinary food, less effort left for broad

    def test_the_harvest_turns_the_year_even_when_nobody_farms(self):
        from origins.sim import farming
        w, c = world()
        b = w.living_bands()[0]
        land._band_rows(w, b.id + 1)
        w.land_lost_crop[b.id] = 10.0
        w.farm_share[:] = 0
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR
        farming.season_food_live(w, np.array([b.id]), np.array([c]), np.array([100.0]))
        self.assertEqual(float(w.land_lost_crop[b.id]), 0.0)

    def test_the_crop_loss_goes_with_the_people(self):
        w, c = world()
        a, d = w.living_bands()[0], w.living_bands()[1]
        land._band_rows(w, max(a.id, d.id) + 1)
        w.land_crop_acc[a.id], w.land_lost_crop[a.id] = 40.0, 10.0
        w.land_crop_ev[a.id] = [7, -1]
        w.land_crop_k[a.id] = [10.0, 0.0]
        w.land_crop_ev[d.id] = -1
        land.move_crop_loss(w, a.id, d.id, 0.25)
        self.assertAlmostEqual(float(w.land_crop_acc[d.id]), 10.0)
        self.assertAlmostEqual(float(w.land_crop_acc[a.id]), 30.0)
        self.assertAlmostEqual(float(w.land_lost_crop[d.id]), 2.5)
        self.assertEqual(w.land_crop_ev[d.id].tolist(), [7, -1])

    def test_abandonment_restores_only_what_the_soil_took(self):
        from origins.sim import farming
        w, c = world()
        b = w.living_bands()[0]
        b.village = True
        js = land.KINDS.index("soil")
        w.land_flags[c, js], w.land_event[c, js] = True, 0
        w.fertility[c] = 0.0
        w.forage_rr[b.id] = 0.5
        n0 = len(w.events)
        # Codex's case: 0.50 realised, of which 0.02 from crops at a crop factor of 0.4, so 0.03 lost; fresh soil
        # gives 0.53, not 0.7143
        farming._land_abandoned(w, b, 0, 1.0, 0.7, 1.0, 0.50, 0.03, 0.5)
        self.assertEqual([e for e in w.events[n0:] if e["kind"] == "land_abandoned"], [])
        farming._land_abandoned(w, b, 0, 1.0, 0.7, 1.0, 0.50, 0.40, 0.5)
        self.assertEqual(len([e for e in w.events[n0:] if e["kind"] == "land_abandoned"]), 1)

    def test_soil_is_cited_where_the_crops_grew_and_every_loss_is_kept(self):
        from origins.sim import demography
        from origins import explain
        w, c = world()
        b = w.living_bands()[0]
        nb = int(w.planet.grid.neighbours[c][0])
        js, jg = land.KINDS.index("soil"), land.KINDS.index("game")
        w.fertility[[c, nb]] = 0.5
        e_old = w.event("land_soil", cell=c)
        e_new = w.event("land_soil", cell=nb)
        e_game = w.event("land_game", cell=nb)
        w.land_flags[c, js], w.land_event[c, js] = True, e_old
        w.land_flags[nb, js], w.land_event[nb, js] = True, e_new
        w.game[nb] = 0.1
        w.land_flags[nb, jg], w.land_event[nb, jg] = True, e_game
        land._band_rows(w, b.id + 1)
        w.land_lost_crop[b.id] = 6.0                                    # crops grown on the land it left
        w.land_crop_ev[b.id] = [e_old, -1]
        w.land_crop_k[b.id] = [6.0, 0.0]
        b.cell = nb
        w.bands_changed()
        land.note_account(w, np.array([b.id]), np.array([10.0]), np.array([5.0]))
        self.assertEqual(sorted(land.felt(w, b.id, nb)), sorted([e_old, e_game]))
        idx = w.alive_idx()
        mine = idx[w.people.band[idx] == b.id]
        w._binfo = None
        demography.kill(w, mine[:1], np.array([demography.C["hunger"]]))
        lh = int(w.people.death_land[mine[0]])
        cited = [x["event"] for x in w.events[lh]["causes"] if "event" in x]
        self.assertEqual(sorted(cited), sorted([e_old, e_game]))      # both pools, not only the first
        self.assertTrue(explain.resolvable(w, {"death": int(mine[0])}))

    def test_coal_smelting_is_not_wood_work(self):
        from origins.sim import technology as T
        w, _ = world()
        coal = T._cell_materials(w)[:, T.MATERIALS.index("coal")]
        if not coal.any():
            self.skipTest("no coal on this planet")
        c = int(np.nonzero(coal)[0][0])
        b = w.living_bands()[0]
        prac = np.zeros((1, T.K), dtype=bool)
        prac[0, T.INDEX["smelting"]] = True
        self.assertFalse(T._wood_used(w, np.array([b.id]), np.array([c]), prac)[0])
        nc = int(np.nonzero(~coal)[0][0])
        self.assertTrue(T._wood_used(w, np.array([b.id]), np.array([nc]), prac)[0])
        prac[0] = False
        prac[0, T.INDEX["canoes"]] = True
        self.assertTrue(T._wood_used(w, np.array([b.id]), np.array([c]), prac)[0])

    def test_the_explanation_uses_the_same_wood_rule(self):
        from origins.sim import technology as T
        w, _ = world()
        b = w.living_bands()[0]
        b.cell = int(np.nonzero(land.forest_max(w) > 0)[0][0])
        w.bands_changed()
        T._prev_arrays(w)
        w.forest[:] = 0.15 * land.forest_max(w)
        w._forest_near = None
        if float(land.forest_near(w)[b.cell]) < P.FUEL_MIN:
            self.skipTest("no forest near this band")
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        i = list(ids).index(b.id)
        t = T.TECHNIQUES[T.INDEX["canoes"]]
        for wood in (False, True):
            w.tech_prev_wood[b.id] = wood
            ok, missing = T.prerequisites_met(w, b, t)
            self.assertEqual(ok, bool(T._possible(w, ids, cells)[i, T.INDEX["canoes"]]))
            self.assertEqual(ok, wood)

    def test_fuel_cutting_starts_the_forest_record(self):
        w, _ = world()
        fm = land.forest_max(w)
        c = int(np.nonzero(fm > 0)[0][0])
        b = w.living_bands()[0]
        b.cell = c
        w.bands_changed()
        w.forest[c] = 0.01
        w.land_fuel[c] = 1.0
        land.yearly(w)
        ev = [e for e in w.events if e["kind"] == "land_forest" and e["cell"] == c]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["data"]["since"], w.year)


class Review023(unittest.TestCase):
    """Codex review 023."""

    def test_crops_already_grown_are_brought_in_when_nobody_farms(self):
        from origins.sim import farming
        w, c = world()
        b = w.living_bands()[0]
        w.farm_share[:] = 0
        w.crop_store[b.id] = 25.0
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR
        _eff, food = farming.season_food_live(w, np.array([b.id]), np.array([c]), np.array([100.0]))
        self.assertEqual(float(food[0]), 25.0)
        self.assertEqual(float(w.crop_store[b.id]), 0.0)

    def test_a_remnant_brings_its_crops_and_their_loss(self):
        from origins.sim import bands
        w, _ = world()
        live = w.living_bands()
        o = live[0]
        b = [x for x in live if x.id != o.id and x.mode == o.mode == "individual"][0]
        b.cell = o.cell
        w.bands_changed()
        idx = w.alive_idx()
        mine = idx[w.people.band[idx] == b.id]
        keep = mine[:9]
        w.people.band[mine[9:]] = o.id                                  # a remnant of 9
        w.people_changed()
        land._band_rows(w, max(x.id for x in w.living_bands()) + 1)
        w.crop_store[b.id], w.land_crop_acc[b.id], b.store = 40.0, 16.0, 20.0
        before = {x.id: (x.store, float(w.crop_store[x.id]), float(w.land_crop_acc[x.id])) for x in w.living_bands()}
        n0 = len(w.events)
        bands.fission_and_merge(w)
        m = [e for e in w.events[n0:] if e["kind"] == "merge" and e["band"] == b.id]
        if not m:
            self.skipTest("the remnant did not merge here")
        r = w.bands[m[0]["data"]["into"]]
        s0, c0, a0 = before[r.id]
        self.assertAlmostEqual(r.store - s0, 20.0)
        self.assertAlmostEqual(float(w.crop_store[r.id]) - c0, 40.0)
        self.assertAlmostEqual(float(w.land_crop_acc[r.id]) - a0, 16.0)
        self.assertEqual(float(w.crop_store[b.id]), 0.0)
        self.assertEqual(float(w.land_crop_acc[b.id]), 0.0)
        self.assertEqual(len(keep), 9)

    def test_a_later_sowing_does_not_move_the_last_harvests_loss(self):
        w, _ = world()
        b = w.living_bands()[0]
        js = land.KINDS.index("soil")
        e2, e778 = w.event("land_soil", cell=2), w.event("land_soil", cell=778)
        w.land_flags[2, js], w.land_event[2, js] = True, e2
        w.land_flags[778, js], w.land_event[778, js] = True, e778
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR
        land.note_crop_loss(w, np.array([b.id]), np.array([40.0]), np.array([2]),
                            (np.array([40.0]), np.array([0.0])))                     # the harvest: 40 from cell 2
        w.t += 1
        land.note_crop_loss(w, np.array([b.id]), np.array([1.0]), np.array([778]),
                            (np.array([1.0]), np.array([0.0])))                      # next season, 1 on 778
        land.note_account(w, np.array([b.id]), np.array([20.0]), np.array([0.0]))
        self.assertEqual(land.felt(w, b.id, b.cell), [e2])
        w.land_flags[2, js] = False                                    # the old fields recover: the record stands
        w.land_event[2, js] = -1
        self.assertEqual(land.felt(w, b.id, b.cell), [e2])

    def test_only_linked_losses_are_counted_as_the_lands(self):
        w, c = world()
        b = w.living_bands()[0]
        es = w.event("land_soil", cell=c)
        land._band_rows(w, b.id + 1)
        w.land_lost_crop[b.id] = 6.0
        w.land_crop_ev[b.id] = [es, -1]
        w.land_crop_k[b.id] = [6.0, 0.0]
        land.note_account(w, np.array([b.id]), np.array([10.0]), np.array([5.0]))      # 5 wild, no wild event
        e = land.hunger_event(w, b.id, c)
        d = w.events[e]["data"]
        self.assertEqual((d["lost_wild"], d["lost_crop"], d["unlinked"]), (0.0, 6.0, 5.0))
        self.assertNotIn("at most", w.events[e]["causes"][0]["note"])
        self.assertIn("not tied to a recorded land event", w.events[e]["causes"][0]["note"])

    def test_every_band_season_of_exposure_is_counted(self):
        w, c = world()
        b = w.living_bands()[0]
        es = w.event("land_soil", cell=c)
        land._band_rows(w, b.id + 1)
        w.land_lost_crop[b.id] = 6.0
        w.land_crop_ev[b.id] = [es, -1]
        w.land_crop_k[b.id] = [6.0, 0.0]
        n0 = len(w.events)
        land.note_account(w, np.array([b.id]), np.array([10.0]), np.array([0.0]), np.array([c]))
        self.assertEqual(w.counts["land_exp_short"], 1)
        self.assertEqual(w.counts["land_exp_crop_only"], 1)
        self.assertAlmostEqual(w.counts["land_exp_linked_sum"], 6.0)
        self.assertEqual(len(w.events), n0)                             # counted, no event without a death


class Review024(unittest.TestCase):
    """Codex review 024."""

    def test_an_older_save_with_the_land_off_can_end_a_band(self):
        from origins.sim import bands
        w, _ = world()
        b = w.living_bands()[0]
        w.land_crop_acc, w.land_lost_crop = np.zeros(64), np.zeros(64)     # review-023 save: new arrays absent
        w.land_crop_k = w.land_acc_k = w.land_acc_ktop = np.zeros(0)
        w.land_crop_ev = w.land_acc_kev = -np.ones(0, dtype=np.int64)
        old = P.LAND
        P.LAND = False
        try:
            bands.end_band(w, b, "test")
        finally:
            P.LAND = old
        self.assertEqual(w.land_crop_k.shape[1:], (2,))

    def test_a_merge_keeps_each_example_event_with_its_own_loss(self):
        w, _ = world()
        a, d = w.living_bands()[0], w.living_bands()[1]
        js = land.KINDS.index("soil")
        e2, e778 = w.event("land_soil", cell=2), w.event("land_soil", cell=778)
        w.land_flags[2, js], w.land_event[2, js] = True, e2
        w.land_flags[778, js], w.land_event[778, js] = True, e778
        for _ in range(2):                                              # the receiver: 12 twice at cell 2
            land.note_crop_loss(w, np.array([d.id]), np.array([12.0]), np.array([2]), (np.array([12.0]), np.array([0.0])))
        land.note_crop_loss(w, np.array([a.id]), np.array([20.0]), np.array([778]), (np.array([20.0]), np.array([0.0])))
        land.move_crop_loss(w, a.id, d.id, 1.0)
        self.assertAlmostEqual(float(w.land_acc_k[d.id, 0]), 44.0)
        ev, top = int(w.land_acc_kev[d.id, 0]), float(w.land_acc_ktop[d.id, 0])
        self.assertEqual((ev, top), (e2, 24.0))     # the pair stays together (24: both seasons cite e2; review 026)

    def test_salt_below_its_yield_threshold_links_nothing(self):
        from origins.sim import farming
        w, _ = world()
        b = w.living_bands()[0]
        jt = land.KINDS.index("salt")
        es = w.event("land_salt", cell=2)
        w.land_flags[2, jt], w.land_event[2, jt] = True, es
        w.salt[2], w.fertility[2] = 0.2, 0.7
        fert, salt = land.crop_parts(w, np.array([2]))
        self.assertAlmostEqual(float(1 - fert[0]) * 100, 18.0)        # Codex's case: fertility takes 18 of 100
        self.assertEqual(float(salt[0]), 1.0)                          # salt takes nothing
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR
        land.note_crop_loss(w, np.array([b.id]), np.array([18.0]), np.array([2]),
                            (np.array([100 * (1 - fert[0])]), np.array([100 * fert[0] * (1 - salt[0])])))
        land.note_account(w, np.array([b.id]), np.array([10.0]), np.array([0.0]))
        self.assertEqual(land.felt(w, b.id, b.cell), [])

    def test_each_seasons_link_is_kept_by_amount(self):
        w, _ = world()
        b = w.living_bands()[0]
        js = land.KINDS.index("soil")
        e2 = w.event("land_soil", cell=2)
        w.land_flags[2, js], w.land_event[2, js] = True, e2
        land.note_crop_loss(w, np.array([b.id]), np.array([49.0]), np.array([2]), (np.array([49.0]), np.array([0.0])))
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR or P.TICKS_PER_YEAR
        land.note_crop_loss(w, np.array([b.id]), np.array([51.0]), np.array([778]), (np.array([51.0]), np.array([0.0])))
        self.assertAlmostEqual(float(w.land_lost_crop[b.id]), 25.0)
        self.assertAlmostEqual(land.crop_linked(w, b.id), 49.0 / 4)    # Codex's case: 49 linked of 100

    def test_the_census_uses_the_same_factor_test_as_the_events(self):
        w, _ = world()
        b = w.living_bands()[0]
        c = int(np.nonzero(land.forest_max(w) > 0)[0][0])
        b.cell = c
        w.bands_changed()
        jg = land.KINDS.index("game")
        w.land_flags[c, jg], w.land_event[c, jg] = True, w.event("land_game", cell=c)
        w.game[c], w.game_fast[c], w.forest[c] = 0.1, 0.1, 0.1
        old = P.GAME_SHARE, P.GAME_FAST_SHARE
        P.GAME_SHARE = P.GAME_FAST_SHARE = 0.0                          # game knocked out of wild food
        try:
            n0 = w.counts.get("land_exp_wild_only", 0)
            land.note_account(w, np.array([b.id]), np.array([9.0]), np.array([6.0]), np.array([c]))
            self.assertEqual(w.counts.get("land_exp_wild_only", 0), n0)
            self.assertEqual(land.felt(w, b.id, c), [])
        finally:
            P.GAME_SHARE, P.GAME_FAST_SHARE = old



class Review025(unittest.TestCase):
    """Codex review 025."""

    def test_a_partial_move_shares_the_examples_season_loss(self):
        w, _ = world()
        a, d = w.living_bands()[0], w.living_bands()[1]
        js = land.KINDS.index("soil")
        e2, e778 = w.event("land_soil", cell=2), w.event("land_soil", cell=778)
        w.land_flags[2, js], w.land_event[2, js] = True, e2
        w.land_flags[778, js], w.land_event[778, js] = True, e778
        land.note_crop_loss(w, np.array([a.id]), np.array([100.0]), np.array([2]), (np.array([100.0]), np.array([0.0])))
        land.move_crop_loss(w, a.id, d.id, 0.1)
        self.assertAlmostEqual(float(w.land_acc_ktop[d.id, 0]), 10.0)
        self.assertAlmostEqual(float(w.land_acc_ktop[a.id, 0]), 90.0)
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR or P.TICKS_PER_YEAR
        land.note_crop_loss(w, np.array([d.id]), np.array([20.0]), np.array([778]), (np.array([20.0]), np.array([0.0])))
        self.assertEqual(int(w.land_crop_ev[d.id, 0]), e778)          # the larger share now

    def test_rounding_between_the_total_and_its_parts_is_not_unlinked(self):
        w, c = world()
        b = w.living_bands()[0]
        land._band_rows(w, b.id + 1)
        es = w.event("land_soil", cell=c)
        w.land_lost_crop[b.id] = 68.05714285714286 / 4
        w.land_crop_k[b.id] = [68.05714285714285 / 4, 0.0]
        w.land_crop_ev[b.id] = [es, -1]
        land.note_account(w, np.array([b.id]), np.array([30.0]), np.array([0.0]))
        e = land.hunger_event(w, b.id, c)
        self.assertEqual(w.events[e]["data"]["unlinked"], 0.0)


    def test_rejoined_parts_of_the_same_loss_keep_their_example(self):
        w, _ = world()
        a, d = w.living_bands()[0], w.living_bands()[1]
        js = land.KINDS.index("soil")
        e2, e778 = w.event("land_soil", cell=2), w.event("land_soil", cell=778)
        w.land_flags[2, js], w.land_event[2, js] = True, e2
        w.land_flags[778, js], w.land_event[778, js] = True, e778
        land.note_crop_loss(w, np.array([a.id]), np.array([100.0]), np.array([2]), (np.array([100.0]), np.array([0.0])))
        land.move_crop_loss(w, a.id, d.id, 0.5)
        land.move_crop_loss(w, a.id, d.id, 1.0)
        self.assertAlmostEqual(float(w.land_acc_ktop[d.id, 0]), 100.0)   # Codex's case: was 50
        w.t += (P.HARVEST_QUARTER - w.quarter) % P.TICKS_PER_YEAR or P.TICKS_PER_YEAR
        land.note_crop_loss(w, np.array([d.id]), np.array([75.0]), np.array([778]), (np.array([75.0]), np.array([0.0])))
        self.assertEqual(int(w.land_crop_ev[d.id, 0]), e2)


    def test_between_different_events_the_larger_example_wins(self):
        w, _ = world()
        a, d = w.living_bands()[0], w.living_bands()[1]
        js = land.KINDS.index("soil")
        cells = [2, 778, 300, 5020]
        evs = []
        for c in cells:
            evs.append(w.event("land_soil", cell=c))
            w.land_flags[c, js], w.land_event[c, js] = True, evs[-1]
        land.note_crop_loss(w, np.array([d.id]), np.array([60.0]), np.array([2]), (np.array([60.0]), np.array([0.0])))
        for c, x in zip(cells[1:], (40.0, 35.0, 30.0)):                  # Codex's case: 105 over three events
            land.note_crop_loss(w, np.array([a.id]), np.array([x]), np.array([c]), (np.array([x]), np.array([0.0])))
        land.move_crop_loss(w, a.id, d.id, 1.0)
        self.assertEqual(int(w.land_acc_kev[d.id, 0]), evs[0])         # 60 at cell 2 beats the source's 40
        self.assertAlmostEqual(float(w.land_acc_k[d.id, 0]), 165.0)


if __name__ == "__main__":
    unittest.main()
