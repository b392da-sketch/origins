"""M3 tests: polities, institutions, succession. Run: python -m pytest tests/test_m3.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from origins import engine, explain, persist  # noqa: E402
from origins.sim import polity  # noqa: E402
from origins.state import World  # noqa: E402
from origins.worldgen import generate  # noqa: E402

_W = {}


def farming_world():
    """A world whose bands are made to farm (so polities can form quickly), run for 80 years."""
    if "w" not in _W:
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 700)
        for b in w.living_bands()[:200]:
            w.farm_share[b.id] = 0.8
            w.skill[b.id, :4] = 3.0
            b.village = True
            b.village_since = b.farming_since = w.t
        engine.step(w, 4 * 80)
        _W["w"] = w
    return _W["w"]


class Polities(unittest.TestCase):
    def test_polities_form_and_conserve(self):
        w = farming_world()
        self.assertTrue(w.polities, "no polity formed among 200 farming villages in 80 years")
        self.assertEqual(w.invariant_failures, [])

    def test_membership_consistent(self):
        w = farming_world()
        for p in w.polities.values():
            if not p.alive:
                continue
            self.assertEqual(int(w.polity_of[p.seat]), p.id)
            self.assertEqual(int(w.polity_via[p.seat]), -1)
            for b in polity.members_of(w, p.id):
                if b.id != p.seat:
                    self.assertGreaterEqual(int(w.polity_via[b.id]), 0)

    def test_events_explained(self):
        w = farming_world()
        evs = [e for e in w.events if e["kind"] in ("polity_founded", "polity_joined", "secession", "succession",
                                                     "institution_founded", "polity_ended")]
        self.assertTrue(evs)
        for e in evs[:200]:
            self.assertTrue(explain.resolvable(w, {"event": e["id"]}), e)
            self.assertTrue(explain.describe(w, {"event": e["id"]})["title"])

    def test_round_trip(self):
        w = farming_world()
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        engine.step(w2, 8)
        w3 = persist.from_bytes(persist.to_bytes(w), w.planet)
        engine.step(w3, 8)
        self.assertEqual(persist.digest(w2), persist.digest(w3))


if __name__ == "__main__":
    unittest.main()


class Conflict(unittest.TestCase):
    def test_wars_happen_and_are_explained(self):
        from origins.state import C
        w = farming_world()
        wars = [e for e in w.events if e["kind"] == "war"]
        self.assertTrue(wars, "no war in 80 years among 200 farming villages and their neighbours")
        for e in wars[:100]:
            self.assertTrue(explain.resolvable(w, {"event": e["id"]}), e)
        p = w.people
        import numpy as np
        dead = np.nonzero(p.cause[:p.n] == C["killed in war"])[0]
        for i in dead[:50]:
            ch = explain.chain(w, {"death": int(i)})
            self.assertTrue(any(c.get("ref", {}).get("event") is not None for c in ch["causes"]), ch)


class WatchingChangesNothing(unittest.TestCase):
    def test_following_a_band_does_not_change_history(self):
        """Ben, 9 November 2026: what the observer follows must not change what happens."""
        w = farming_world()
        a = persist.from_bytes(persist.to_bytes(w), w.planet)
        b = persist.from_bytes(persist.to_bytes(w), w.planet)
        b.follow = b.living_bands()[-1].id
        engine.step(a, 4 * 10)
        engine.step(b, 4 * 10)
        b.follow = a.follow
        self.assertEqual(persist.digest(a), persist.digest(b))


class Review005(unittest.TestCase):
    """Regression tests for Codex review 005 (13 November 2026)."""

    def test_groups_of_different_polities_or_ways_of_life_stay_separate(self):
        from origins import engine
        from origins.sim import bands, groups, polity
        from origins.state import World
        from origins.worldgen import generate
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 20)
        live = [b for b in w.living_bands() if b.mode != "group"][:2]
        if len(live) < 2:
            self.skipTest("need two bands")
        a, b = live
        for x in (a, b):
            groups.fold(w, x)
        b.cell = a.cell
        w.farm_share[a.id] = w.farm_share[b.id] = 1.0
        polity._new_polity(w, a, "test")
        bands.consolidate_groups(w)
        self.assertTrue(a.alive and b.alive, "groups in different polities must not merge")
        w.polity_of[a.id] = w.polity_of[b.id] = -1
        from origins.sim import pastoral
        real = pastoral.is_herder
        pastoral.is_herder = lambda w_, x, *rest: x.id == b.id       # b herds now, a farms crops
        try:
            w.herder_since[a.id] = w.t                               # a once herded: history must not count
            bands.consolidate_groups(w)
            self.assertTrue(a.alive and b.alive, "herders and crop farmers must not merge")
            self.assertEqual(bands.group_key(w, a)[2], False)
            pastoral.is_herder = lambda w_, x, *rest: False          # same way of life, same polity, same cell
            bands.consolidate_groups(w)
            self.assertFalse(a.alive and b.alive, "groups of the same kind in one cell still merge")
        finally:
            pastoral.is_herder = real
