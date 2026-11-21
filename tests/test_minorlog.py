"""The compact log (Ben, 22 November 2026; docs/COMPACT_LOG_PROPOSAL.md): help, partnerships, first gifts and land
moves as rows, read back as the events they replace."""
import json
import unittest

import numpy as np

from origins import explain, persist
from origins.sim import minorlog
from origins.state import World
from origins.worldgen import generate
from origins import engine


def _world(years=60):
    w = World.new(1, 1, generate(1))
    engine.step(w, 4 * years)
    return w


class CompactLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = _world()

    def test_rows_are_recorded_and_counted(self):
        w = self.w
        total = sum(minorlog.size(w, k) for k in minorlog.KINDS)
        self.assertGreater(total, 0)
        for k in minorlog.KINDS:
            self.assertEqual(w.counts.get(k, 0), minorlog.size(w, k))
            self.assertFalse(any(w.events[i]["kind"] == k for i in range(len(w.events))))

    def test_every_row_resolves_and_reads_as_an_event(self):
        w = self.w
        good = set()
        for k in minorlog.KINDS:
            for i in range(min(minorlog.size(w, k), 50)):
                e = minorlog.as_event(w, k, i)
                self.assertEqual(e["kind"], k)
                self.assertTrue(any("note" in c for c in e["causes"]))
                self.assertTrue(explain.resolvable(w, {"log": [k, i]}, good=good))
                self.assertTrue(explain.describe(w, {"log": [k, i]})["title"])

    def test_bad_references_do_not_resolve(self):
        w = self.w
        self.assertFalse(explain.resolvable(w, {"log": ["no_such_kind", 0]}))
        self.assertFalse(explain.resolvable(w, {"log": ["land_move", 10 ** 9]}))

    def test_saved_and_digested(self):
        w = self.w
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w2), persist.digest(w))
        for k in minorlog.KINDS:
            self.assertTrue(np.array_equal(w2.minor[k].array(), w.minor[k].array()))
        d0 = persist.digest(w)
        k = next(k for k in minorlog.KINDS if minorlog.size(w, k))
        w.minor[k]._a[0, 0] += 1                                       # a changed row changes the digest
        try:
            self.assertNotEqual(persist.digest(w), d0)
        finally:
            w.minor[k]._a[0, 0] -= 1

    def test_a_fresh_world_and_a_reloaded_one_digest_alike(self):
        w = World.new(1, 1, generate(1))
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w2), persist.digest(w))

    def test_shadow_mode_writes_the_old_events_with_the_same_history(self):
        """The same history with and without shadow events (shadow events are the rows written as the old code's
        events; against the code before the compact log, digests and an all-event hash matched after 20 years from
        the planet-3 save, 22 November 2026)."""
        a = World.new(1, 1, generate(1))
        b = World.new(1, 1, generate(1))
        engine.step(a, 4 * 40)
        minorlog.SHADOW = True
        try:
            engine.step(b, 4 * 40)
        finally:
            minorlog.SHADOW = False
        shadow = [e for e in b.events if e["kind"] in minorlog.KINDS]
        self.assertEqual(len(shadow), sum(minorlog.size(a, k) for k in minorlog.KINDS))
        self.assertEqual(a.population(), b.population())
        self.assertEqual({k: g.bit_generator.state["state"] for k, g in a.rng.items()},
                         {k: g.bit_generator.state["state"] for k, g in b.rng.items()})
        rows = {k: [minorlog.as_event(a, k, i) for i in range(minorlog.size(a, k))] for k in minorlog.KINDS}
        for k in minorlog.KINDS:
            got = [e for e in shadow if e["kind"] == k]
            self.assertEqual([json.dumps([e["t"], e["band"], e["cell"], e["data"]], sort_keys=True) for e in got],
                             [json.dumps([e["t"], e["band"], e["cell"], e["data"]], sort_keys=True) for e in rows[k]])

    def test_givers_list_grows_past_its_first_size(self):
        g = minorlog.Ints()
        g.extend(range(1023))
        g.extend([5, 6, 7])
        g.extend(range(5000))
        self.assertEqual(g.n, 1023 + 3 + 5000)
        self.assertEqual(g.array()[1023:1026].tolist(), [5, 6, 7])


if __name__ == "__main__":
    unittest.main()
