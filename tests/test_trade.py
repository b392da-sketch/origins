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



class Review013(unittest.TestCase):
    """Codex review 013: findings reproduced, then fixed."""

    def test_loading_a_stage1_save_keeps_the_last_goods_row(self):
        import io, zipfile, json
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        while len(w.goods) < 128:
            w.new_band(a.cell, parent=a.id)
        last = len(w.goods) - 1
        w.goods[last] = np.arange(1, trade.G + 1) * 10.0
        data = persist.to_bytes(w)
        zin = zipfile.ZipFile(io.BytesIO(data))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zo:
            for n in zin.namelist():
                blob = zin.read(n)
                if n == "arrays.npz":
                    arrs = dict(np.load(io.BytesIO(blob)))
                    arrs.pop("partner_of"); arrs.pop("partner_since")
                    buf = io.BytesIO(); np.savez(buf, **arrs); blob = buf.getvalue()
                zo.writestr(n, blob)
        w2 = persist.from_bytes(out.getvalue(), w.planet)
        self.assertEqual(w2.goods[last].tolist(), w.goods[last].tolist())

    def test_help_only_from_partners_within_reach(self):
        from origins.sim.language import ring2
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        trade._link(w, a.id, b.id)
        far = [c for c in range(w.planet.n) if w.planet.land[c] and c not in set(int(x) for x in ring2(w)[a.cell])]
        b.cell = far[0]
        w.bands_changed()
        ids = np.array([a.id, b.id])
        out = trade.share_in_need(w, [a, b], ids, np.array([5.0, 100.0]), np.array([10.0, 10.0]), np.array([10.0, 10.0]))
        self.assertEqual(out.tolist(), [5.0, 100.0])

    def test_gifts_are_recorded(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        trade._link(w, a.id, b.id)
        w.goods[a.id, trade.GI["shell"]] = 100.0
        old = P.PARTNER_FORM
        P.PARTNER_FORM = 0.0
        n0 = len(w.events)
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_FORM = old
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "gift_exchange"]
        self.assertEqual(len(ev), 1)
        self.assertAlmostEqual(ev[0]["data"]["goods"][str(a.id)]["shell"], 5.0)

    def test_consolidation_drops_partnerships(self):
        import inspect
        from origins.sim import bands
        self.assertIn("trade._unlink_all(w, b.id)", inspect.getsource(bands.consolidate_groups))



class DownTheLine(unittest.TestCase):
    """Trade stage 3: exchange between neighbours (Ben, 15 November 2026)."""

    def _line(self, n=6):
        """A chain of bands on adjacent land cells, the first holding salt."""
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        nb = w.planet.grid.neighbours
        cells, c = [a.cell], a.cell
        while len(cells) < n:
            nxt = [int(x) for x in nb[c] if x >= 0 and w.planet.land[x] and int(x) not in cells
                   and all(int(x) not in set(int(y) for y in nb[p]) for p in cells[:-1])]
            if not nxt:
                break
            c = nxt[0]
            cells.append(c)
        bs = [a] + [w.new_band(c, parent=a.id) for c in cells[1:]]
        for o in w.living_bands():
            if o not in bs:
                o.alive = False
        w.bands_changed()
        return w, bs

    def test_goods_thin_out_with_distance_and_are_conserved(self):
        w, bs = self._line()
        S = trade.GI["salt"]
        w.goods[bs[0].id, S] = 1000.0
        live = w.living_bands()
        ids = np.array([b.id for b in live])
        cells = np.array([b.cell for b in live])
        for _ in range(10):
            trade.down_the_line(w, live, ids, cells)
        held = [float(w.goods[b.id, S]) for b in bs]
        self.assertAlmostEqual(sum(held), 1000.0, places=6)
        self.assertTrue(all(held[k] >= held[k + 1] for k in range(len(held) - 1)), held)
        self.assertGreater(held[1], 0.0)

    def test_first_arrival_is_recorded(self):
        w, bs = self._line(3)
        w.goods[bs[0].id, trade.GI["salt"]] = 1000.0
        live = w.living_bands()
        n0 = len(w.events)
        trade.down_the_line(w, live, np.array([b.id for b in live]), np.array([b.cell for b in live]))
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "good_arrived"]
        self.assertTrue(any(e["band"] == bs[1].id and e["data"]["good"] == "salt" for e in ev))


class Review014(unittest.TestCase):
    """Codex review 014: dense inflows, repeated first arrivals, net-only logs."""

    def _bands_on(self, cells):
        w = World.new(1, 1, generate(1))
        founders = w.living_bands()
        bs = [w.new_band(c, parent=founders[0].id) for c in cells]
        for o in founders:                                  # every founding band, not just one
            o.alive = False
        w.bands_changed()
        return w, bs

    def _step(self, w):
        live = w.living_bands()
        trade.down_the_line(w, live, np.array([b.id for b in live]), np.array([b.cell for b in live]))

    def _line_cells(self, w0, n):
        nb = w0.planet.grid.neighbours
        c = w0.living_bands()[0].cell
        cells = [c]
        while len(cells) < n:
            nxt = [int(x) for x in nb[c] if x >= 0 and w0.planet.land[x] and int(x) not in cells
                   and all(int(x) not in set(int(y) for y in nb[p]) for p in cells[:-1])]
            c = nxt[0]
            cells.append(c)
        return cells

    def test_many_inflows_do_not_push_a_receiver_past_its_donors(self):
        w0 = World.new(1, 1, generate(1))
        cell = w0.living_bands()[0].cell
        w, bs = self._bands_on([cell] * 101)
        F = trade.GI["fine_stone"]
        for b in bs[1:]:
            w.goods[b.id, F] = 100.0
        sizes = np.maximum(w.band_sizes()[[b.id for b in bs]].astype(float), 1.0)
        x0 = w.goods[[b.id for b in bs], F] / sizes
        self._step(w)
        x1 = w.goods[[b.id for b in bs], F] / sizes
        self.assertAlmostEqual(float(w.goods[[b.id for b in bs], F].sum()), 10000.0, places=6)
        self.assertLessEqual(x1[0], x1[1:].min() + 1e-9)          # the poor band does not overtake its donors
        self.assertLessEqual(float(x1.var()), float(x0.var()))    # and the step moves towards equality

    def test_a_good_first_arrives_only_once(self):
        w0 = World.new(1, 1, generate(1))
        w, bs = self._bands_on(self._line_cells(w0, 2))
        S = trade.GI["salt"]
        n0 = len(w.events)
        for _ in range(20):
            w.goods[bs[0].id, S] += 0.008
            self._step(w)
            w.goods[:, S] *= 0.5                                     # wear
        ev = [w.events[i] for i in range(n0, len(w.events))
              if w.events[i]["kind"] == "good_arrived" and w.events[i]["band"] == bs[1].id]
        self.assertLessEqual(len(ev), 1)

    def test_the_log_counts_goods_passed_on(self):
        w0 = World.new(1, 1, generate(1))
        w, (a, b, c) = self._bands_on(self._line_cells(w0, 3))
        F = trade.GI["fine_stone"]
        w.goods[a.id, F], w.goods[b.id, F] = 100.0, 50.0
        w.exchange_log = []
        self._step(w)
        rows = {r[1]: r for r in w.exchange_log}
        self.assertIn(b.id, rows)
        self.assertAlmostEqual(rows[b.id][2], 2.5, places=4)
        self.assertAlmostEqual(rows[b.id][3], 2.5, places=4)


if __name__ == "__main__":
    unittest.main()
