"""M4a trade, stage 1: goods and their ledgers."""
import unittest

import numpy as np

from origins import engine, persist, params as P
from origins.sim import technology as T, trade
from origins.state import World
from origins.worldgen import generate


class GoodsStage1(unittest.TestCase):

    def test_goods_are_conserved_and_replay_exactly(self):
        w = World.new(1, 1, generate(1))
        for b in w.living_bands():
            w.tech[b.id, T.INDEX["cordage"]] = 1.0
        b = w.living_bands()[0]
        w.planet.minerals["flint"][b.cell] = True        # a source on its own land
        engine.step(w, 40)
        self.assertEqual(w.invariant_failures, [])
        self.assertGreater(w.goods_ledger["fine_stone"]["produced"], 0.0)
        d0 = persist.digest(w)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w2), d0)

    def test_no_source_no_goods(self):
        w = World.new(1, 1, generate(1))
        ids = np.array([x.id for x in w.living_bands()])
        w.t = P.HARVEST_QUARTER
        trade.yearly(w)
        self.assertEqual(float(w.goods[ids, trade.GI["copper"]].sum()), 0.0)   # nobody practises copper working

    def test_moving_and_ending_keep_the_balance(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        w.goods[a.id, trade.GI["salt"]] = 10.0
        w.goods_ledger["salt"]["produced"] += 10.0
        trade.check_begin(w)
        trade.move_share(w, a.id, b.id, 0.3)
        self.assertAlmostEqual(float(w.goods[b.id, trade.GI["salt"]]), 3.0)
        trade.band_ended(w, b.id)
        trade.check_end(w)
        self.assertEqual(w.invariant_failures, [])
        self.assertAlmostEqual(w.goods_ledger["salt"]["lost"], 3.0)



class Review012(unittest.TestCase):
    """Codex review 012: findings reproduced, then fixed."""

    def test_marriage_moves_carry_goods(self):
        from origins.sim import demography
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        p = w.people
        mem = w.members(a.id)
        men = mem[(p.sex[mem] == 1) & (w.ages(mem) > 18)]
        p.band[men] = b.id
        p.partner[mem] = -1
        w.people_changed()
        S = trade.GI["salt"]
        w.goods[a.id, S], w.goods[b.id, S] = 10.0, 20.0
        before = w.goods_ledger["salt"]["moved_in"]
        for _ in range(40):
            demography.partnerships(w)
        moved = w.goods_ledger["salt"]["moved_in"] - before
        married_in = int((p.sex[w.members(b.id)] == 0).sum()) + int((p.sex[w.members(a.id)] == 1).sum())
        self.assertGreater(married_in, 0)
        self.assertGreater(moved, 0.0)                      # whoever moved took a share of their band's goods
        self.assertAlmostEqual(float(w.goods[:, S].sum()), 30.0, places=6)   # moved, not made or lost


    def test_raid_loot_takes_goods(self):
        """Ben, 15 November 2026: a winning raid takes RAID_TAKE of the loser's goods, as of its food."""
        import inspect
        from origins.sim import conflict
        src = inspect.getsource(conflict)
        self.assertIn("trade.move_share(w, t.id, b.id, P.RAID_TAKE)", src)



class Partnerships(unittest.TestCase):
    """Trade stage 2: gift partnerships (Ben, 15 November 2026)."""

    def _world(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        return w, a, b

    def test_partners_form_within_reach_and_lapse_out_of_it(self):
        w, a, b = self._world()
        old = P.PARTNER_FORM
        P.PARTNER_FORM = 10.0                       # certain, for the test
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_FORM = old
        self.assertIn(b.id, trade.partners(w, a.id))
        self.assertIn(a.id, trade.partners(w, b.id))
        from origins.sim.language import ring2
        far = [c for c in range(w.planet.n) if w.planet.land[c] and c not in set(int(x) for x in ring2(w)[a.cell])]
        b.cell = far[0]
        w.bands_changed()
        trade.partnerships_yearly(w, [a, b])
        self.assertNotIn(b.id, trade.partners(w, a.id))

    def test_partners_share_food_in_need_without_making_any(self):
        w, a, b = self._world()
        trade._link(w, a.id, b.id)
        ids = np.array([a.id, b.id])
        avail = np.array([5.0, 100.0])
        need = np.array([10.0, 10.0])
        out = trade.share_in_need(w, [a, b], ids, avail, need, need)
        self.assertAlmostEqual(out.sum(), avail.sum())                 # moved, not made
        self.assertAlmostEqual(out[0], 10.0)                           # the shortfall met from the partner's spare
        self.assertGreaterEqual(out[1], 10.0)                          # the giver keeps its own needs

    def test_partnerships_round_trip(self):
        w, a, b = self._world()
        trade._link(w, a.id, b.id)
        engine.step(w, 8)
        d0 = persist.digest(w)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w2), d0)
        self.assertEqual(w.invariant_failures, [])


if __name__ == "__main__":
    unittest.main()
