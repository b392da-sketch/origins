"""M4a tests: the technology network."""
import unittest

import numpy as np

from origins import engine, persist, params as P
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
        self.assertIn("needs tallies and tokens held well", missing)



class _Zero:
    """Stands in for the technology stream: every draw succeeds."""
    def random(self, shape):
        return np.zeros(shape)


def _shrink(w, x, n):
    """Leave a group band with n adults (for keeping cases that need few practitioners)."""
    G = w.groups
    G.F[x.group] = 0
    G.M[x.group] = 0
    G.preg[x.group] = 0
    G.F[x.group][25] = n


def _two_bands(seed=1):
    from origins.sim import groups
    pl = generate(seed)
    w = World.new(seed, 1, pl)
    a = w.living_bands()[0]
    b = w.new_band(a.cell, parent=a.id)
    for x in (a, b):
        if x.mode == "individual":
            groups.fold(w, x)
    w.tech[:] = 0.0
    return w, a, b


class Review008(unittest.TestCase):
    """Codex review 008: findings reproduced, then fixed."""

    def test_combining_peoples_keeps_their_knowledge(self):
        from origins.sim import bands
        w, a, b = _two_bands()
        b.cell = a.cell
        _shrink(w, a, 30)
        _shrink(w, b, 30)
        w.farm_share[a.id] = w.farm_share[b.id] = 0.0
        w.tech[b.id, T.INDEX["pottery"]] = 0.8
        w.bands_changed()
        bands.consolidate_groups(w)
        live = [x for x in (a, b) if x.alive]
        self.assertEqual(len(live), 1)
        self.assertAlmostEqual(float(w.tech[live[0].id, T.INDEX["pottery"]]), 0.8, places=5)

    def test_migrants_carry_knowledge(self):
        from origins.sim import groups
        w, a, b = _two_bands()
        _shrink(w, a, 40)
        w.tech[a.id, T.INDEX["cordage"]] = 0.7
        n0 = len(w.events)
        moved = groups.transfer(w, a, b, np.random.default_rng(0))
        self.assertGreater(moved, 0)
        T.combine(w, a, b, "migration", moved)      # as bands.fission_and_merge does after a transfer
        technology_carry = float(w.tech[b.id, T.INDEX["cordage"]])
        self.assertAlmostEqual(technology_carry, 0.7, places=5)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_adopted"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["data"]["route"], "migration")

    def _phase(self, w, live):
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        sizes = w.band_sizes()[ids]
        connected = T._reach(w, cells, np.bincount(cells, weights=sizes, minlength=w.planet.n)[:, None])[:, 0]
        w.rng["technology"] = _Zero()
        T.keep_and_spread(w, live, ids, cells, sizes, connected, np.ones((len(live), T.K)))

    def test_a_people_does_not_learn_from_itself(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 1)
        k = T.INDEX["fire_hardening"]
        w.tech[a.id, k] = 0.5
        n0 = len(w.events)
        self._phase(w, [a])
        for i in range(n0, len(w.events)):
            e = w.events[i]
            if e["kind"] == "technique_adopted":
                self.assertNotEqual(e["data"]["source"], a.id)
        # with only itself practising and too few people to keep it, the skill declines and is not refreshed
        self.assertLess(float(w.tech[a.id, k]), 0.5)

    def test_adoption_checks_prerequisites_after_this_years_drift(self):
        w, a, b = _two_bands()
        _shrink(w, a, 2)
        _shrink(w, b, 2)
        cord, bow = T.INDEX["cordage"], T.INDEX["bow"]
        w.tech[a.id, cord] = w.tech[b.id, cord] = 0.5
        w.tech[a.id, bow] = 0.8
        self._phase(w, [a, b])
        self.assertLess(float(w.tech[b.id, cord]), 0.5)     # the case under test: cordage fell this year
        self.assertLess(float(w.tech[b.id, bow]), 0.5)        # so the bow cannot be adopted

    def test_prerequisite_helpers_follow_the_working_level(self):
        from origins import params as P
        w, a, b = _two_bands()
        w.tech[a.id, T.INDEX["tallies"]] = 0.6
        old = P.TECH_WORKING
        try:
            P.TECH_WORKING = 0.7
            ok, _ = T.prerequisites_met(w, a, T.TECHNIQUES[T.INDEX["writing"]])
            vec = T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["writing"]]
            self.assertEqual(ok, bool(vec))
        finally:
            P.TECH_WORKING = old



class Decisions14Nov(unittest.TestCase):
    """Ben's technology decisions of 14 November 2026."""

    def _phase(self, w, live):
        Review008._phase(self, w, live)

    def test_refinement_is_slow(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 5000)                              # far more practitioners than needed
        k = T.INDEX["cordage"]
        w.tech[a.id, k] = 0.25
        self._phase(w, [a])
        self.assertLessEqual(float(w.tech[a.id, k]) - 0.25, P.TECH_REFINE * (1 + P.TECH_CRAFT_GAIN) + 1e-6)
        self.assertGreater(float(w.tech[a.id, k]), 0.25)

    def test_unpractised_knowledge_fades_not_deleted(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 200)
        w.farm_share[a.id] = 0.0                         # no longer farms: terracing cannot be practised
        k = T.INDEX["terracing"]
        w.tech[a.id, k] = 0.6
        self._phase(w, [a])
        self.assertAlmostEqual(float(w.tech[a.id, k]), 0.6 - P.TECH_FORGET, places=5)

    def test_wool_needs_sheep(self):
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        a.cell = _cell_where(w, "wild_sheep")
        w.farm_share[a.id] = 0.6
        w.tech[a.id, T.INDEX["cordage"]] = 0.8
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_pig")] = 3
        wool = T.TECHNIQUES[T.INDEX["wool"]]
        self.assertFalse(T.prerequisites_met(w, a, wool)[0])
        w.skill[a.id][SPECIES.index("wild_sheep")] = 3
        self.assertTrue(T.prerequisites_met(w, a, wool)[0])

    def test_few_captives_carry_a_cruder_skill(self):
        w, a, b = _two_bands()
        k = T.INDEX["writing"]                          # needs 60 practitioners
        w.tech[a.id, k] = 0.9
        T.combine(w, a, b, "capture", 30)
        self.assertAlmostEqual(float(w.tech[b.id, k]), 0.45, places=5)
        T.combine(w, a, b, "capture", 3)                # too few to carry anything usable: nothing changes
        self.assertAlmostEqual(float(w.tech[b.id, k]), 0.45, places=5)

    def test_records_survive_combining_and_daughters(self):
        w, a, b = _two_bands()
        k = T.INDEX["pottery"]
        w.tech_record[a.id, k] = 0.7
        T.combine(w, a, b, "combined", 100)
        self.assertAlmostEqual(float(w.tech_record[b.id, k]), 0.7, places=5)
        d = w.new_band(b.cell, parent=b.id)
        self.assertAlmostEqual(float(w.tech_record[d.id, k]), 0.7, places=5)



def _cell_where(w, good, bad=None):
    """A cell where species `good` can live (and `bad` cannot, if given)."""
    from origins.sim.farming import SPECIES, land_tables
    suit = land_tables(w)[1]
    ok = suit[:, SPECIES.index(good)] > 0
    if bad:
        ok &= suit[:, SPECIES.index(bad)] == 0
    return int(np.nonzero(ok)[0][0])


class Review009(unittest.TestCase):
    """Codex review 009: findings reproduced, then fixed."""

    def test_remembered_writing_keeps_no_records(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 200)
        W, F, C = T.INDEX["writing"], T.INDEX["fire_hardening"], T.INDEX["cordage"]
        w.tech[a.id, W] = 0.8                     # no tallies: writing remembered, not practised
        w.tech[a.id, C] = 0.8
        w.tech_record[a.id, F] = 0.8
        Review008._phase(self, w, [a])
        self.assertEqual(float(w.tech[a.id, F]), 0.0)
        self.assertEqual(float(w.tech_record[a.id, C]), 0.0)

    def test_carrying_animals_refreshes_the_herder_test(self):
        from origins.sim import bands, pastoral
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        c = _cell_where(w, "wild_pig", "wild_grain")
        a.cell = b.cell = c
        w.farm_share[a.id] = w.farm_share[b.id] = 1.0
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_pig")] = 3
        w.skill[b.id][:] = 0
        w.skill[b.id][SPECIES.index("wild_grain")] = 3
        self.assertFalse(pastoral.is_herder(w, b))
        bands.carry(w, a, b, "merge", 5)
        self.assertTrue(pastoral.is_herder(w, b))

    def test_marriage_carries_knowledge(self):
        from origins.sim import demography
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        p = w.people
        mem = w.members(a.id)
        C = T.INDEX["cordage"]
        w.tech[:] = 0
        w.tech[a.id, C] = 1.0
        men = mem[(p.sex[mem] == 1) & (w.ages(mem) > 18)]
        p.band[men] = b.id
        p.partner[mem] = -1
        w.people_changed()
        for _ in range(40):
            demography.partnerships(w)
        if (p.sex[w.members(b.id)] == 0).any():   # someone married into b
            self.assertAlmostEqual(float(w.tech[b.id, C]), 0.2, places=5)   # one carrier of 5 needed

    def test_animals_must_be_able_to_live_here(self):
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        a.cell = _cell_where(w, "wild_pig", "wild_sheep")
        w.farm_share[a.id] = 1.0
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_sheep")] = 3
        w.tech[a.id, T.INDEX["cordage"]] = 0.8
        wool = T.TECHNIQUES[T.INDEX["wool"]]
        self.assertFalse(T.prerequisites_met(w, a, wool)[0])
        self.assertFalse(T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["wool"]])


    def test_a_remembered_prerequisite_unlocks_nothing(self):
        """Ben, 14 November 2026: a prerequisite counts only when practised."""
        w, a, b = _two_bands()
        a.cell = int(np.nonzero(T._cell_materials(w)[:, T.MATERIALS.index("copper")]
                                & T._cell_materials(w)[:, T.MATERIALS.index("forest")]
                                & T._cell_materials(w)[:, T.MATERIALS.index("clay")])[0][0])
        for key in ("kilns", "copper_working"):
            w.tech[a.id, T.INDEX[key]] = 0.8      # kilns without pottery: remembered, not practised
        smelt = T.TECHNIQUES[T.INDEX["smelting"]]
        ok, missing = T.prerequisites_met(w, a, smelt)
        self.assertFalse(ok)
        self.assertIn("needs kilns practised", missing)
        self.assertFalse(T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["smelting"]])
        w.tech[a.id, T.INDEX["pottery"]] = 0.8
        self.assertTrue(T.prerequisites_met(w, a, smelt)[0])



class LiteratureChanges14Nov(unittest.TestCase):
    """Skilled adults, not everyone, keep a technique; refinement slows near mastery (Ben, 14 November 2026)."""

    def test_an_isolated_band_cannot_keep_pottery(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 40)                     # 40 adults: 10 skilled, fewer than the 20 pottery needs
        w.spec[a.id] = 0
        a.cell = int(np.nonzero(T._cell_materials(w)[:, T.MATERIALS.index("clay")])[0][0])
        k = T.INDEX["pottery"]
        w.tech[a.id, k] = 0.6
        Review008._phase(self, w, [a])
        self.assertLess(float(w.tech[a.id, k]), 0.6)

    def test_refinement_slows_near_mastery(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 5000)
        w.spec[a.id] = 0
        k = T.INDEX["cordage"]
        w.tech[a.id, k] = 0.9
        Review008._phase(self, w, [a])
        self.assertAlmostEqual(float(w.tech[a.id, k]) - 0.9, P.TECH_REFINE * 0.1, places=5)


if __name__ == "__main__":
    unittest.main()
