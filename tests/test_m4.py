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
        w.tech[a.id, T.INDEX["cordage"]] = 0.7
        n0 = len(w.events)
        moved = groups.transfer(w, a, b, np.random.default_rng(0))
        self.assertGreater(moved, 0)
        T.combine(w, a, b, "migration", moved=moved)      # as bands.fission_and_merge does after a transfer
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
        possible = T._possible(w, ids, cells)
        w.rng["technology"] = _Zero()
        T.keep_and_spread(w, live, ids, cells, sizes, connected, possible, np.ones((len(live), T.K)))

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


if __name__ == "__main__":
    unittest.main()
