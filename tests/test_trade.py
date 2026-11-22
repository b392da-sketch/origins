"""M4a trade, stage 1: goods and their ledgers."""
import unittest

import numpy as np

from origins import engine, persist, params as P
from origins.sim import minorlog, technology as T, trade
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
                    for k_ in [k_ for k_ in arrs if k_.startswith("partner_")]:   # a save without partner rows
                        arrs.pop(k_)
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
        n0 = minorlog.size(w, "gift_exchange")
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_FORM = old
        ev = minorlog.since(w, "gift_exchange", n0)
        self.assertEqual(len(ev), 1)
        self.assertAlmostEqual(ev[0]["data"]["goods"][str(a.id)]["shell"], 5.0)

    def test_consolidation_drops_partnerships(self):
        import inspect
        from origins.sim import bands
        self.assertIn("trade._unlink_all(w, b.id", inspect.getsource(bands.consolidate_groups))



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


class PartnersTrade(unittest.TestCase):
    """Trade stage 4a: partners trade working goods; links grow with size; settled bands favour well-supplied partners."""
    _bands_on, _step, _line_cells = Review014._bands_on, Review014._step, Review014._line_cells

    def test_partners_beyond_neighbours_trade_working_goods_only(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, (a, b) = self._bands_on([c[0], c[2]])               # two rings apart: not neighbours
        trade._link(w, a.id, b.id)
        F, T = trade.GI["fine_stone"], trade.GI["textiles"]
        w.goods[a.id, F] = w.goods[a.id, T] = 100.0
        n0 = len(w.events)
        self._step(w)
        self.assertGreater(w.goods[b.id, F], 0.0)
        self.assertEqual(w.goods[b.id, T], 0.0)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "good_arrived"]
        self.assertTrue(any(e["band"] == b.id and e["data"]["route"] == "partner" for e in ev))
        trade._unlink(w, a.id, b.id)                               # without the link, nothing passes
        w2, (a2, b2) = self._bands_on([c[0], c[2]])
        w2.goods[a2.id, F] = 100.0
        self._step(w2)
        self.assertEqual(w2.goods[b2.id, F], 0.0)

    def test_larger_bands_hold_more_links(self):
        w0 = World.new(1, 1, generate(1))
        w, bs = self._bands_on([w0.living_bands()[0].cell] * 4)
        sizes = np.zeros(len(w.band_sizes()), dtype=int)
        for b, n in zip(bs, (10, 30, 120, 3000)):
            sizes[b.id] = n
        w.band_sizes = lambda: sizes
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        self.assertEqual(trade.allowance(w, [b.id for b in bs]).tolist(), [4, 4, 8, 16])

    def test_a_settled_band_trades_up_to_a_better_supplied_partner(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, bs = self._bands_on([c[0]] + [c[1]] * 4 + [c[2]])
        a, poor, rich = bs[0], bs[1:5], bs[5]
        for o in poor:
            trade._link(w, a.id, o.id)
        F = trade.GI["fine_stone"]
        for k, o in enumerate(poor):
            w.goods[o.id, F] = 1.0 + k
        w.goods[rich.id, F] = 50.0
        w.farm_share[a.id] = 0.6                                   # settled
        old = P.PARTNER_SWITCH
        P.PARTNER_SWITCH = 1.0
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_SWITCH = old
        mine = trade.partners(w, a.id)
        self.assertIn(rich.id, mine)
        self.assertNotIn(poor[0].id, mine)                         # the worst-supplied partner was dropped
        self.assertEqual(len(mine), 4)

    def test_older_saves_widen_to_the_new_link_cap(self):
        from origins import persist
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 2)
        w, (a, b) = self._bands_on(c)
        trade._link(w, a.id, b.id)
        w.goods[a.id, trade.GI["salt"]] = 7.0
        import io
        import zipfile
        data = persist.to_bytes(w)                        # rewritten as a save from before stage 4a: dense, four links
        zin, out = zipfile.ZipFile(io.BytesIO(data)), io.BytesIO()
        with zipfile.ZipFile(out, "w") as zo:
            for n in zin.namelist():
                blob = zin.read(n)
                if n == "arrays.npz":
                    arrs = dict(np.load(io.BytesIO(blob)))
                    for k_ in [k_ for k_ in arrs if k_.startswith("partner_")]:
                        arrs.pop(k_)
                    arrs["partner_of"] = w.partner_of.dense()[:, :4].copy()
                    arrs["partner_since"] = w.partner_since.dense()[:, :4].copy()
                    buf = io.BytesIO()
                    np.savez(buf, **arrs)
                    blob = buf.getvalue()
                zo.writestr(n, blob)
        w2 = persist.from_bytes(out.getvalue(), planet=w.planet)
        self.assertEqual(w2.partner_of.shape[1], P.PARTNERS_CAP)
        self.assertEqual(trade.partners(w2, a.id), [b.id])
        self.assertEqual(w2.goods[a.id, trade.GI["salt"]], 7.0)


class GiftTotals(unittest.TestCase):
    """Ben, 15 November 2026: gifts kept as running totals per partnership; one event for the first exchange;
    swaps need a partner at least PARTNER_SWITCH_GAIN times as well supplied."""
    _bands_on, _step, _line_cells = Review014._bands_on, Review014._step, Review014._line_cells

    def _pair(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 2)
        w, (a, b) = self._bands_on(c)
        trade._link(w, a.id, b.id)
        w.goods[a.id, trade.GI["shell"]] = 100.0
        return w, a, b

    def _years(self, w, n):
        old = P.PARTNER_FORM
        P.PARTNER_FORM = 0.0
        try:
            for _ in range(n):
                trade.partnerships_yearly(w, w.living_bands())
                w.t += 4
        finally:
            P.PARTNER_FORM = old

    def test_totals_add_up_and_only_the_first_exchange_is_an_event(self):
        w, a, b = self._pair()
        n0 = minorlog.size(w, "gift_exchange")
        self._years(w, 3)
        ev = minorlog.since(w, "gift_exchange", n0)
        self.assertEqual(len(ev), 1)
        tot = trade.gift_totals(w, a.id, b.id)
        self.assertEqual(tot["years"], 3)
        # a gives 5% of its shell each year and receives 5% of b's back
        held = w.goods[a.id, trade.GI["shell"]] + w.goods[b.id, trade.GI["shell"]]
        self.assertAlmostEqual(held, 100.0, places=9)
        gave_a, gave_b = tot[str(a.id)]["shell"], tot[str(b.id)]["shell"]
        self.assertAlmostEqual(100.0 - gave_a + gave_b, w.goods[a.id, trade.GI["shell"]], places=5)
        self.assertGreater(len(w.gift_log), 0)

    def test_a_lapse_carries_the_totals_and_a_new_link_starts_at_zero(self):
        w, a, b = self._pair()
        self._years(w, 2)
        tot = trade.gift_totals(w, a.id, b.id)
        far = [c for c in range(w.planet.grid.n) if w.planet.land[c]
               and c not in set(int(x) for x in __import__("origins.sim.language", fromlist=["ring2"]).ring2(w)[a.cell])]
        b.cell = far[0]
        w.bands_changed()
        n0 = minorlog.size(w, "partnership_lapsed")
        self._years(w, 1)
        lap = minorlog.since(w, "partnership_lapsed", n0)
        self.assertEqual(len(lap), 1)
        self.assertEqual(lap[0]["data"]["gifts"], tot)
        self.assertFalse(w.partner_gave[a.id].any())

    def test_totals_survive_save_and_load(self):
        from origins import persist
        w, a, b = self._pair()
        self._years(w, 2)
        w2 = persist.from_bytes(persist.to_bytes(w), planet=w.planet)
        self.assertEqual(trade.gift_totals(w2, a.id, b.id), trade.gift_totals(w, a.id, b.id))
        self.assertEqual(w2.gift_log, w.gift_log)
        self.assertEqual(persist.digest(w2), persist.digest(w))

    def test_a_swap_needs_a_clear_gain(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, bs = self._bands_on([c[0]] + [c[1]] * 4 + [c[2]])
        a, mine, other = bs[0], bs[1:5], bs[5]
        for o in mine:
            trade._link(w, a.id, o.id)
        F = trade.GI["fine_stone"]
        for o in mine:
            w.goods[o.id, F] = 10.0
        w.goods[other.id, F] = 15.0                               # better, but not twice as well supplied
        w.farm_share[a.id] = 0.6
        old = (P.PARTNER_SWITCH, P.PARTNER_FORM)
        P.PARTNER_SWITCH, P.PARTNER_FORM = 1.0, 0.0
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_SWITCH, P.PARTNER_FORM = old
        self.assertNotIn(other.id, trade.partners(w, a.id))


class Review015(unittest.TestCase):
    """Codex review 015."""
    _bands_on, _step, _line_cells = Review014._bands_on, Review014._step, Review014._line_cells

    def test_a_sail_pair_is_not_counted_again_as_partners(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, (a, b) = self._bands_on([c[0], c[2]])
        trade._link(w, a.id, b.id)
        live = w.living_bands()
        ids = np.array([x.id for x in live]); cells = np.array([x.cell for x in live])
        I, J, K = np.array([0]), np.array([1]), np.array([2])          # already paired across a sea cell
        I2, J2, K2 = trade._partner_pairs(w, live, ids, cells, I, J, K)
        self.assertEqual(list(zip(I2.tolist(), J2.tolist(), K2.tolist())), [(0, 1, 2)])

    def test_links_that_carry_no_pottery_do_not_slow_pottery(self):
        w0 = World.new(1, 1, generate(1))
        from origins.sim.language import ring2
        nb = w0.planet.grid.neighbours
        c = self._line_cells(w0, 2)
        near0 = set(int(x) for x in nb[c[0]] if x >= 0)
        near1 = set(int(x) for x in nb[c[1]] if x >= 0)
        far = [int(x) for x in ring2(w0)[c[0]] if x >= 0 and w0.planet.land[x] and int(x) not in near0
               and int(x) not in near1 and int(x) not in c][0]       # within partner reach of the giver only
        w, bs = self._bands_on([c[0], c[1]] + [far] * 16)
        giver, nbr, far = bs[0], bs[1], bs[2:]
        for o in far:
            trade._link(w, giver.id, o.id)
        Pt = trade.GI["pottery"]
        w.goods[giver.id, Pt] = 100.0
        self._step(w)
        self.assertAlmostEqual(w.goods[nbr.id, Pt], 5.0, places=6)
        self.assertEqual(float(w.goods[[o.id for o in far], Pt].sum()), 0.0)

    def _gifts(self):
        w0 = World.new(1, 1, generate(1))
        w, (a, b) = self._bands_on(self._line_cells(w0, 2))
        trade._link(w, a.id, b.id)
        w.goods[a.id, trade.GI["shell"]] = 100.0
        GiftTotals._years(self, w, 2)
        return w, a, b, trade.gift_totals(w, a.id, b.id)

    def test_a_band_that_ends_keeps_its_gift_record(self):
        w, a, b, tot = self._gifts()
        n0 = minorlog.size(w, "partnership_lapsed")
        trade.band_ended(w, b.id)
        lap = minorlog.since(w, "partnership_lapsed", n0)
        self.assertEqual(len(lap), 1)
        self.assertEqual(lap[0]["data"]["gifts"], tot)

    def test_consolidation_keeps_the_gift_record(self):
        w, a, b, tot = self._gifts()
        n0 = minorlog.size(w, "partnership_lapsed")
        trade._unlink_all(w, b.id, joined=a.id)
        lap = minorlog.since(w, "partnership_lapsed", n0)
        self.assertEqual(len(lap), 1)
        self.assertEqual(lap[0]["data"]["gifts"], tot)

    def test_goods_held_without_neighbours_count_as_reached(self):
        w0 = World.new(1, 1, generate(1))
        land = [x for x in range(w0.planet.grid.n) if w0.planet.land[x]]
        w, (a,) = self._bands_on([land[0]])
        w.goods[a.id, trade.GI["salt"]] = 5.0
        self._step(w)                                                # no pairs at all
        self.assertTrue(w.goods_reached[a.id, trade.GI["salt"]])

    def test_exactly_twice_the_supply_is_enough(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, bs = self._bands_on([c[0]] + [c[1]] * 4 + [c[2]])
        a, mine, other = bs[0], bs[1:5], bs[5]
        for o in mine:
            trade._link(w, a.id, o.id)
        F = trade.GI["fine_stone"]
        for o in mine:
            w.goods[o.id, F] = 1.0
        w.goods[other.id, F] = 2.0
        w.farm_share[a.id] = 0.6
        old = (P.PARTNER_SWITCH, P.PARTNER_FORM)
        P.PARTNER_SWITCH, P.PARTNER_FORM = 1.0, 0.0
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_SWITCH, P.PARTNER_FORM = old
        self.assertIn(other.id, trade.partners(w, a.id))


class ReformWait(unittest.TestCase):
    """Ben, 15 November 2026: two bands parted by a swap wait PARTNER_REFORM_WAIT years before linking again."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def test_a_swapped_out_partner_cannot_return_at_once(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 3)
        w, bs = self._bands_on([c[0]] + [c[1]] * 4 + [c[2]])
        a, mine, rich = bs[0], bs[1:5], bs[5]
        for o in mine:
            trade._link(w, a.id, o.id)
        F = trade.GI["fine_stone"]
        for k, o in enumerate(mine):
            w.goods[o.id, F] = 1.0 + k
        w.goods[rich.id, F] = 50.0
        w.farm_share[a.id] = 0.6
        old = (P.PARTNER_SWITCH, P.PARTNER_FORM)
        P.PARTNER_SWITCH, P.PARTNER_FORM = 1.0, 0.0
        try:
            trade.partnerships_yearly(w, w.living_bands())
        finally:
            P.PARTNER_SWITCH, P.PARTNER_FORM = old
        dropped = mine[0].id
        self.assertNotIn(dropped, trade.partners(w, a.id))
        trade._unlink(w, a.id, mine[1].id)                         # make room again
        self.assertTrue(trade._parted(w, a.id, dropped))
        old = (P.PARTNER_SWITCH, P.PARTNER_FORM)
        P.PARTNER_SWITCH, P.PARTNER_FORM = 0.0, 1e9                # any allowed pair would link
        try:
            trade.partnerships_yearly(w, w.living_bands())
            self.assertNotIn(dropped, trade.partners(w, a.id))
            w.t += 4 * P.PARTNER_REFORM_WAIT
            self.assertFalse(trade._parted(w, a.id, dropped))
        finally:
            P.PARTNER_SWITCH, P.PARTNER_FORM = old


class Traders(unittest.TestCase):
    """Trade stage 4b (Ben, 15 November 2026): traders of polities carry goods between seats."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def _world(self, n_between=0):
        from origins.sim import polity, traders
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 5)
        w, bs = self._bands_on([c[0], c[4]])
        A = polity._new_polity(w, bs[0], [{"note": "test"}], why="test")
        B = polity._new_polity(w, bs[1], [{"note": "test"}], why="test")
        sizes = np.zeros(len(w.band_sizes()) + 64, dtype=int)
        sizes[bs[0].id] = sizes[bs[1].id] = 200
        w.band_sizes = lambda: sizes[:len(w.bands)] if len(w.bands) <= len(sizes) else np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        w.spec[bs[0].id] = 10.0                                  # two traders at A's seat
        return w, bs, A, B, c, sizes

    def _year(self, w):
        from origins.sim import minorlog, trade, traders
        trade.check_begin(w)
        traders.yearly(w, w.living_bands())
        w.invariant_failures = getattr(w, "invariant_failures", [])
        trade.check_end(w)

    def test_a_route_carries_goods_with_losses_picks_and_shares(self):
        from origins.sim import traders
        w, (a, b), A, B, c, _ = self._world()
        F = trade.GI["fine_stone"]
        w.goods[a.id, F] = 100.0
        n0 = len(w.events)
        w.invariant_failures = []
        self._year(w)
        self.assertEqual(w.invariant_failures, [])
        self.assertGreater(w.goods[b.id, F], 0.0)                 # delivered
        self.assertGreater(w.treasury[B.id, F], 0.0)              # the destination's ruler's levy
        self.assertGreater(w.goods_ledger["fine_stone"]["lost"], 0.0)   # lost on the road
        load = 2 * P.TRADER_LOAD
        q0 = (0.0, 0.0, 0.0, 0.0)
        there = traders.path(w.planet, a.cell, b.cell, q0)[0]
        back = traders.path(w.planet, b.cell, a.cell, q0)[0]             # each way its own road
        home = P.TRADER_KEEP * load * np.exp(-P.ROAD_LOSS * there) * (1 - P.RULER_LEVY) * np.exp(-P.ROAD_LOSS * back)
        self.assertAlmostEqual(100.0 - w.goods[a.id, F], load - home, places=6)
        kinds = [w.events[i]["kind"] for i in range(n0, len(w.events))]
        self.assertEqual(kinds.count("trade_route_opened"), 1)
        self.assertIn("good_arrived", kinds)
        self._year(w)
        kinds = [w.events[i]["kind"] for i in range(n0, len(w.events))]
        self.assertEqual(kinds.count("trade_route_opened"), 1)    # opened once

    def test_a_polity_on_the_road_takes_a_toll_or_is_gone_round(self):
        from origins.sim import polity, traders
        w, (a, b), A, B, c, sizes = self._world()
        cost, cells = traders.path(w.planet, a.cell, b.cell, (0.0, 0.0, 0.0, 0.0))
        nb = w.planet.grid.neighbours
        strip = set(cells[1:-1])
        for x in cells[1:-1]:                                     # K holds the road and the land either side of it
            strip |= {int(y) for y in nb[x] if y >= 0 and w.planet.land[y]}
        strip -= {a.cell, b.cell}
        mid = [w.new_band(x, parent=a.id) for x in sorted(strip)]
        K = polity._new_polity(w, mid[0], [{"note": "test"}], why="test")
        for m in mid:
            w.polity_of[m.id] = K.id
            sizes[m.id] = 1
        w.bands_changed()
        F = trade.GI["fine_stone"]
        old = (P.TOLL, P.ROUTES_MAX)
        try:
            P.ROUTES_MAX = 1
            rows = {}
            for toll in (0.001, 0.9):
                P.TOLL = toll
                w.goods[a.id, F] = 100.0
                w.route_log = []
                w.log_strides.pop("route_log", None)
                self._year(w)
                rows[toll] = [r for r in w.route_log if r[1] == A.id and r[2] == B.id]
            self.assertEqual(len(rows[0.001]), 1)
            self.assertEqual(rows[0.001][0][8:], [1, 0])          # a small toll is paid ...
            self.assertGreater(rows[0.001][0][5], 0.0)
            self.assertEqual(rows[0.9][0][8:], [0, 1])            # ... a ruinous one is gone round
            ev = [e for e in w.events if e["kind"] == "toll_evaded"]
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"]["around"], K.id)
        finally:
            P.TOLL, P.ROUTES_MAX = old

    def test_rulers_stores_pass_on_and_survive_save_and_load(self):
        from origins import persist
        from origins.sim import polity, traders
        w, (a, b), A, B, c, _ = self._world()
        w.goods[a.id, trade.GI["salt"]] = 50.0
        self._year(w)
        self.assertGreater(w.treasury[B.id].sum(), 0.0)
        w2 = persist.from_bytes(persist.to_bytes(w), planet=w.planet)
        self.assertTrue(np.array_equal(w2.treasury, w.treasury))
        self.assertEqual(w2.routes_seen, w.routes_seen)
        held = float(w.treasury[B.id].sum())
        before = float(w.goods[b.id].sum())
        polity._end_polity(w, B, "test", [{"note": "test"}])
        self.assertEqual(float(w.treasury[B.id].sum()), 0.0)
        self.assertAlmostEqual(float(w.goods[b.id].sum()), before + held, places=9)

    def test_no_sea_crossing_without_sail(self):
        from origins.sim import traders
        pl = generate(1)
        land = np.nonzero(pl.land)[0]
        sea = [int(x) for x in pl.grid.neighbours[int(np.nonzero(pl.coast)[0][0])] if x >= 0 and not pl.land[x] and not pl.lake[x]]
        self.assertTrue(sea)
        cost, cells = traders.path(pl, int(np.nonzero(pl.coast)[0][0]), sea[0], (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(cells, ())
        cost, cells = traders.path(pl, int(np.nonzero(pl.coast)[0][0]), sea[0], (0.0, 0.0, 0.0, 1.0))
        self.assertAlmostEqual(cost, P.SEA_COST)


class TreasuryWear(unittest.TestCase):
    def test_rulers_stores_wear_like_everyone_elses(self):
        w = World.new(1, 1, generate(1))
        from origins.sim import traders
        traders.grow(w, 3)
        w.treasury[3, trade.GI["salt"]] = 10.0
        w.invariant_failures = []
        trade.check_begin(w)
        trade.yearly(w)
        trade.check_end(w)
        self.assertEqual(w.invariant_failures, [])
        self.assertAlmostEqual(w.treasury[3, trade.GI["salt"]], 10.0 * (1 - P.GOOD_WEAR["salt"]))


class Review016(unittest.TestCase):
    """Codex review 016."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def test_landing_from_the_sea_starts_at_sea_level(self):
        from origins.sim import traders
        pl = generate(1)
        u, v = 4997, 19931                                       # sea cell (-1,764 m) next to land (45 m)
        self.assertFalse(pl.land[u]); self.assertTrue(pl.land[v])
        foot, water, sea = traders._step_costs(pl, (0.0, 0.0, 1.0, 1.0))
        c = traders._cost(u, v, pl, foot, water, sea)
        self.assertAlmostEqual(c, foot + P.MOUNTAIN_COST * max(0.0, float(pl.elevation[v])) / 1000.0, places=6)

    def test_going_round_one_toll_does_not_skip_the_next(self):
        from origins.sim import polity, traders
        w0 = World.new(1, 1, generate(1))
        pl = w0.planet
        nb = pl.grid.neighbours
        # A and B two cells apart with exactly the cells between them as the ways through
        land = set(int(x) for x in np.nonzero(pl.land)[0])
        for a_ in sorted(land):
            ring1 = set(int(x) for x in nb[a_] if x >= 0)
            if not ring1 <= land:
                continue
            ring2 = set(int(y) for x in ring1 for y in nb[x] if y >= 0) - ring1 - {a_}
            if not ring2 <= land:
                continue
            b_ = sorted(ring2)[0]
            mids = sorted(x for x in ring1 if b_ in set(int(y) for y in nb[x]))
            if len(mids) >= 2:
                break
        w, bs = self._bands_on([a_, b_])
        a, b = bs
        A = polity._new_polity(w, a, [{"note": "t"}], why="t")
        B = polity._new_polity(w, b, [{"note": "t"}], why="t")
        sizes = np.zeros(len(w.band_sizes()) + 64, dtype=int)
        sizes[a.id] = sizes[b.id] = 200
        # two third polities: K holds half the ring round A, L the other half, so every road crosses one of them
        ring1 = sorted(set(int(x) for x in nb[a_] if x >= 0))
        half = len(ring1) // 2
        others = []
        for cells_, name in ((ring1[:half], "K"), (ring1[half:], "L")):
            bands_ = [w.new_band(x, parent=a.id) for x in cells_]
            Q = polity._new_polity(w, bands_[0], [{"note": "t"}], why="t")
            for m in bands_:
                w.polity_of[m.id] = Q.id
                sizes[m.id] = 1
            others.append(Q)
        w.bands_changed()
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        w.spec[a.id] = 10.0
        F = trade.GI["fine_stone"]
        w.goods[a.id, F] = 100.0
        old = (P.TOLL, P.ROUTES_MAX)
        try:
            P.TOLL, P.ROUTES_MAX = 0.5, 1
            w.route_log = []
            traders.yearly(w, w.living_bands())
            row = [r for r in w.route_log if r[1] == A.id and r[2] == B.id][0]
            self.assertGreaterEqual(row[8], 1)                    # some toll is paid: no road avoids both
            self.assertGreater(sum(float(w.treasury[Q.id, F]) for Q in others), 0.0)
        finally:
            P.TOLL, P.ROUTES_MAX = old

    def test_the_route_cache_depends_on_range_and_grid(self):
        from origins.sim import traders
        traders._COST_CACHE.clear()
        pl6 = generate(1)
        old = P.TRADE_RANGE
        try:
            P.TRADE_RANGE = 0.01
            self.assertEqual(traders.path(pl6, 2, 21890, (0.0, 0.0, 0.0, 0.0))[1], ())
            P.TRADE_RANGE = old
            self.assertEqual(traders.path(pl6, 2, 21890, (0.0, 0.0, 0.0, 0.0))[1], (2, 21890))
        finally:
            P.TRADE_RANGE = old
        pl5 = generate(1, level=5)
        q = (1.0, 1.0, 1.0, 1.0)
        c5 = traders.path(pl5, 2, 5506, q)
        c6 = traders.path(pl6, 2, 5506, q)
        traders._COST_CACHE.clear()
        self.assertEqual(traders.path(pl6, 2, 5506, q), c6)
        self.assertNotEqual(c5, c6)


class Decisions16Nov(unittest.TestCase):
    """Ben, 16 November 2026: the ruler's take is a levy; each way its own road; shortlist by gravity."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def test_a_large_centre_further_off_is_shortlisted(self):
        from origins.sim import polity, traders
        w0 = World.new(1, 1, generate(1))
        pl = w0.planet
        nb = pl.grid.neighbours
        c = self._line_cells(w0, 5)
        ring1 = set(int(x) for x in nb[c[0]] if x >= 0)
        ring2 = set(int(y) for x in ring1 for y in nb[x] if y >= 0) - ring1 - {c[0]}
        near = sorted(x for x in (ring1 | ring2) if pl.land[x] and x not in c)[:12]
        self.assertEqual(len(near), 12)
        w, bs = self._bands_on([c[0], c[4]] + near)
        pols = [polity._new_polity(w, b, [{"note": "t"}], why="t") for b in bs]
        sizes = np.zeros(len(w.bands) + 64, dtype=int)
        sizes[bs[0].id], sizes[bs[1].id] = 100, 5000
        for b in bs[2:]:
            sizes[b.id] = 5
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        w.spec[bs[0].id] = 10.0
        w.goods[bs[0].id, trade.GI["salt"]] = 50.0
        old = P.ROUTES_MAX
        try:
            P.ROUTES_MAX = 1
            w.route_log = []
            traders.yearly(w, w.living_bands())
        finally:
            P.ROUTES_MAX = old
        self.assertEqual({(r[1], r[2]) for r in w.route_log if r[1] == pols[0].id}, {(pols[0].id, pols[1].id)})


class Curation(unittest.TestCase):
    """Ben, 16 November 2026: scarce tools wear more slowly; salt does not; switched off, wear is as before."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def _wear(self, on):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 5)
        w, (rich, poor) = self._bands_on([c[0], c[4]])            # far apart: no exchange between them
        sizes = np.zeros(len(w.bands) + 64, dtype=int)
        sizes[rich.id] = sizes[poor.id] = 100
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        F, S = trade.GI["fine_stone"], trade.GI["salt"]
        w.goods[rich.id, F], w.goods[poor.id, F] = 100.0, 0.1     # 1 and 0.001 per person
        w.goods[rich.id, S], w.goods[poor.id, S] = 100.0, 0.1
        old = (P.CURATION, P.GOOD_YIELD)
        P.CURATION, P.GOOD_YIELD = on, {g: 0.0 for g in P.GOOD_YIELD}
        try:
            w.invariant_failures = []
            trade.check_begin(w)
            trade.yearly(w)
            trade.check_end(w)
        finally:
            P.CURATION, P.GOOD_YIELD = old
        self.assertEqual(w.invariant_failures, [])
        return w, rich, poor, F, S

    def test_scarce_tools_wear_more_slowly(self):
        w, rich, poor, F, S = self._wear(True)
        k = P.GOOD_WEAR["fine_stone"]
        self.assertAlmostEqual(w.goods[rich.id, F], 100.0 * (1 - k * 1.0 / (1.0 + P.CURATION_HALF)), places=9)
        self.assertAlmostEqual(w.goods[poor.id, F], 0.1 * (1 - k * max(P.CURATION_MIN, 0.001 / (0.001 + P.CURATION_HALF))), places=12)
        self.assertAlmostEqual(w.goods[poor.id, S], 0.1 * (1 - P.GOOD_WEAR["salt"]), places=12)   # salt is eaten

    def test_switched_off_wear_is_as_before(self):
        w, rich, poor, F, S = self._wear(False)
        k = P.GOOD_WEAR["fine_stone"]
        self.assertAlmostEqual(w.goods[poor.id, F], 0.1 * (1 - k), places=12)


class Review017(unittest.TestCase):
    """Codex review 017."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def test_no_road_home_means_no_route(self):
        from origins.sim import traders
        w, (a, b), A, B, c, _ = Traders._world(self)
        w.goods[b.id, trade.GI["salt"]] = 100.0
        real = traders.path

        def one_way(pl, x, y, tq, blocked=frozenset()):
            if (x, y) == (b.cell, a.cell):
                return (float("inf"), ())                          # uphill all the way: no road home in range
            return real(pl, x, y, tq, blocked)
        traders.path = one_way
        try:
            w.route_log = []
            traders.yearly(w, w.living_bands())
        finally:
            traders.path = real
        self.assertEqual([r for r in w.route_log if r[1] == A.id and r[2] == B.id], [])
        self.assertEqual(w.goods[b.id, trade.GI["salt"]], 100.0)

    def test_a_road_within_range_with_one_toll_beats_none_found(self):
        from origins.sim import traders
        # S=0; prefixes to J=7: 0-1-2-7 (3 travel, tolls K1,K2), 0-3-7 (4 travel, toll K3), 0-4-5-7 (5 travel, none)
        # then J-T=6 costs 26; range 30
        edges = {(0, 1): 1, (1, 2): 1, (2, 7): 1, (0, 3): 2, (3, 7): 2, (0, 4): 2.5, (4, 5): 1.25, (5, 7): 1.25,
                 (7, 6): 26}
        edges.update({(v, u): c for (u, v), c in list(edges.items())})
        n = 8
        nb = -np.ones((n, 6), dtype=np.int64)
        for u in range(n):
            vs = sorted(v for (x, v) in edges if x == u)
            nb[u, :len(vs)] = vs

        class G:
            pass
        g = G(); g.neighbours = nb; g.xyz = np.tile([1.0, 0.0, 0.0], (n, 1)); g.radius_km = 1.0; g.spacing_km = 1.0
        pl = G(); pl.grid = g
        holder = {1: 101, 2: 102, 3: 103}
        real = traders._cost
        traders._cost = lambda u, v, pl_, f, wa, se: edges[(u, v)]
        old = P.TRADE_RANGE
        try:
            P.TRADE_RANGE = 30.0
            tau = -np.log(1 - P.TOLL) / P.ROAD_LOSS
            cost, cells, paid = traders.road(pl, 0, 6, (0.0, 0.0, 0.0, 0.0), holder, set(), tau)
        finally:
            traders._cost = real
            P.TRADE_RANGE = old
        self.assertEqual(cells, (0, 3, 7, 6))
        self.assertAlmostEqual(cost, 30.0)
        self.assertEqual(paid, [103])

    def test_leaving_a_lake_climbs_from_its_surface(self):
        from origins.sim import traders
        pl = generate(1)
        u, v = 4991, 19836
        self.assertTrue(pl.lake[u]); self.assertTrue(pl.land[v])
        self.assertAlmostEqual(float(pl.water_level[u]), 671.26, places=1)
        foot, water, sea = traders._step_costs(pl, (0.0, 0.0, 1.0, 0.0))
        self.assertAlmostEqual(traders._cost(u, v, pl, foot, water, sea), 1.31908, places=4)


class GoodsEffects(unittest.TestCase):
    """Trade stage 5 (Ben, 16 November 2026): what goods change; GOODS_EFFECTS False is the knock-out."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def _one(self, need_no=None, size=100):
        from origins.sim import technology as T
        w0 = World.new(1, 1, generate(1))
        mats = T._cell_materials(w0)
        cell = next(c for c in range(w0.planet.n) if w0.planet.land[c]
                    and (need_no is None or not mats[c, T.MATERIALS.index(need_no)]))
        w, (b,) = self._bands_on([cell])
        sizes = np.zeros(len(w.bands) + 64, dtype=int)
        sizes[b.id] = size
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        return w, b, T

    def test_imported_copper_lets_a_band_work_it_and_its_loss_is_recorded(self):
        w, b, T = self._one(need_no="copper")
        k = T.INDEX["copper_working"]
        w.tech[b.id, k] = 0.8
        ids, cells = np.array([b.id]), np.array([b.cell])
        self.assertFalse(T._possible(w, ids, cells)[0, k])          # no copper within reach
        w.goods[b.id, trade.GI["copper"]] = 2.0                       # 0.02 per person, brought by trade
        self.assertTrue(T._possible(w, ids, cells)[0, k])
        T._mark(w, w.living_bands(), ids, cells)                      # end of the year: practised on imports
        self.assertTrue(w.tech_prev_prac[b.id, k])
        w.goods[b.id, trade.GI["copper"]] = 0.0                       # the trade stops and the stock is gone
        n0 = len(w.events)
        T._cut_off(w, w.living_bands(), ids, cells)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_cut_off"]
        self.assertEqual(len(ev), 1)
        self.assertIn("by trade ran out", ev[0]["causes"][0]["note"])

    def test_metal_tools_need_metal(self):
        w, b, T = self._one()
        w.tech[b.id, T.INDEX["copper_working"]] = 1.0
        w.goods[b.id, trade.GI["copper"]] = 2.0                       # enough to work (as above)
        T.refresh(w)
        if not T._possible(w, np.array([b.id]), np.array([b.cell]))[0, T.INDEX["copper_working"]]:
            self.skipTest("copper working not possible here")
        full = T.farm_multipliers(w, [b.id], np.array([b.cell]))[0][0]
        w.goods[b.id, trade.GI["copper"]] = 0.6                       # 0.006: workable, but tools thin
        T.refresh(w)
        thin = T.farm_multipliers(w, [b.id], np.array([b.cell]))[0][0]
        self.assertAlmostEqual(full, 1 + P.TECH_EFFECT["copper_working"], places=6)
        self.assertAlmostEqual(thin, 1 + P.TECH_EFFECT["copper_working"] * 0.006 / P.METAL_NEED, places=6)

    def test_salt_preserves_and_helps_herds(self):
        w, b, T = self._one()
        base_spoil = T.spoil_multiplier(w, [b.id])[0]
        base_herd = T.farm_multipliers(w, [b.id], np.array([b.cell]))[2][0]
        w.goods[b.id, trade.GI["salt"]] = 10.0                        # 0.1 per person: more than SALT_NEED
        self.assertAlmostEqual(T.spoil_multiplier(w, [b.id])[0], base_spoil * (1 - P.SALT_SPOIL), places=6)
        self.assertAlmostEqual(T.farm_multipliers(w, [b.id], np.array([b.cell]))[2][0], base_herd * (1 + P.SALT_HERD), places=6)

    def test_a_rulers_prestige_goods_raise_capacity_a_little(self):
        from origins.sim import polity, traders
        w, b, T = self._one()
        p = polity._new_polity(w, b, [{"note": "t"}], why="t")
        base = T.capacity_multiplier(w, b.id)
        traders.grow(w, p.id)
        w.treasury[p.id, trade.GI["gold"]] = 100.0                    # 1 per member: more than PRESTIGE_NEED
        self.assertAlmostEqual(T.capacity_multiplier(w, b.id), base * (1 + P.PRESTIGE_HOLD), places=9)

    def test_making_goods_costs_food_time(self):
        w = World.new(1, 1, generate(1))                   # a real band with adults, moved to the coast (salt, shell)
        b = w.living_bands()[0]
        b.cell = int(np.nonzero(w.planet.coast)[0][0])
        w.bands_changed()
        share = trade.craft_share(w, np.array([b.id]))[0]
        self.assertGreater(share, 0.0)                              # craft years of ordinary makers

    def _at_source(self):
        from origins.sim import technology as T
        w0 = World.new(1, 1, generate(1))
        cell = int(np.nonzero(w0.planet.coast)[0][0])
        w, (b,) = self._bands_on([cell])
        return w, b, T

    def test_traders_roads_carry_techniques(self):
        from origins.sim import technology as T
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 5)
        w, (a, b) = self._bands_on([c[0], c[4]])
        k = T.INDEX["fire_hardening"]
        w.tech[a.id, k] = 1.0
        w.trade_links = [[a.id, b.id]]
        live = w.living_bands()
        ids = np.array([x.id for x in live]); cells = np.array([x.cell for x in live])
        new = w.tech[ids].astype(float)
        poss = T._possible(w, ids, cells)
        prac = (new > 0) & poss
        old = (P.TRADE_TEACH, P.TECH_FOREIGN)
        P.TRADE_TEACH, P.TECH_FOREIGN = 1e9, 1.0
        try:
            T._trade_lessons(w, live, ids, new, poss, prac, None, w.rng["technology"])
        finally:
            P.TRADE_TEACH, P.TECH_FOREIGN = old
        self.assertGreater(new[list(ids).index(b.id), k], 0.0)
        ev = [e for e in w.events if e["kind"] == "technique_adopted" and e["data"].get("route") == "trade"]
        self.assertEqual(len(ev), 1)

    def test_trade_need_follows_goods_received(self):
        w0 = World.new(1, 1, generate(1))
        c = self._line_cells(w0, 2)
        w, (a, b) = self._bands_on(c)
        sizes = np.zeros(len(w.bands) + 64, dtype=int)
        sizes[a.id] = sizes[b.id] = 100
        w.band_sizes = lambda: np.resize(sizes, len(w.bands))
        w.sizes_of = lambda ids, w=w: w.band_sizes()[np.asarray(ids, dtype=int)]   # stubbed alike (sizes_of: G4a pilot)
        ids, cells = np.array([a.id, b.id]), np.array([a.cell, b.cell])
        self.assertEqual(trade.trade_need(w, ids, cells).tolist(), [0.0, 0.0])
        w.goods[a.id, trade.GI["pottery"]] = 100.0                 # pottery counts too
        old = P.GOOD_YIELD
        P.GOOD_YIELD = {g: 0.0 for g in P.GOOD_YIELD}
        try:
            trade.yearly(w)
        finally:
            P.GOOD_YIELD = old
        got = 0.1 * 100.0 / 2                                       # one year's exchange towards equal holdings
        need = trade.trade_need(w, ids, cells)
        self.assertAlmostEqual(need[1], min(1.0, got / 100 / P.TRADE_NEED_REF), places=9)
        self.assertEqual(need[0], 0.0)

    def test_the_knock_out_switches_every_effect_off(self):
        w, b, T = self._one(need_no="copper")
        w.goods[b.id, trade.GI["copper"]] = 2.0
        w.goods[b.id, trade.GI["salt"]] = 10.0
        old = P.GOODS_EFFECTS
        P.GOODS_EFFECTS = False
        try:
            ids = np.array([b.id])
            self.assertFalse(trade.goods_materials(w, ids, T.MATERIALS).any())
            self.assertEqual(trade.metal_factor(w, ids)[0], 1.0)
            self.assertEqual(trade.salt_factor(w, ids)[0], 0.0)
            self.assertEqual(trade.craft_share(w, ids)[0], 0.0)
        finally:
            P.GOODS_EFFECTS = old


class Review018(unittest.TestCase):
    """Codex review 018."""
    _bands_on, _line_cells = Review014._bands_on, Review014._line_cells

    def _children(self, w, band_id):
        idx = w.alive_idx()
        mine = idx[w.people.band[idx] == band_id]
        w.people.birth[mine] = w.t - 10 * P.TICKS_PER_YEAR
        w._live = None

    def test_a_band_of_children_cannot_teach_along_a_road(self):
        from origins.sim import technology as T
        w = World.new(1, 1, generate(1))
        live = w.living_bands()
        a, b = live[0], live[1]
        self._children(w, a.id)
        k = T.INDEX["fire_hardening"]
        w.tech[:, k] = 0.0
        w.tech[a.id, k] = 1.0
        w.trade_links = [[a.id, b.id]]
        ids = np.array([x.id for x in live]); cells = np.array([x.cell for x in live])
        self.assertEqual(T.skilled(w, live, ids)[0], 0.0)
        old = (P.TRADE_TEACH, P.TECH_FOREIGN, P.TECH_SPREAD)
        P.TRADE_TEACH, P.TECH_FOREIGN, P.TECH_SPREAD = 1e9, 1.0, 1.0
        try:
            T.keep_and_spread(w, live, ids, cells, w.band_sizes()[ids], np.full(len(ids), 1e6), np.ones((len(ids), T.K)))
        finally:
            P.TRADE_TEACH, P.TECH_FOREIGN, P.TECH_SPREAD = old
        ev = [e for e in w.events if e["kind"] == "technique_adopted" and e["data"].get("route") == "trade"]
        self.assertEqual(ev, [])

    def test_children_who_make_nothing_lose_no_food_time(self):
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        self._children(w, b.id)
        w.spec[b.id] = 0.0
        coast = int(np.nonzero(w.planet.coast)[0][0])
        b.cell = coast
        w.bands_changed()
        self.assertEqual(trade.craft_share(w, np.array([b.id]))[0], 0.0)

    def _copper_world(self, per_person):
        """A real founding band moved to a cell with clay and forest but no copper within reach, holding copper."""
        from origins.sim import technology as T
        w = World.new(1, 1, generate(1))
        mats = T._cell_materials(w)
        M = T.MATERIALS
        cell = next(c for c in range(w.planet.n) if w.planet.land[c] and not mats[c, M.index("copper")]
                    and mats[c, M.index("clay")] and mats[c, M.index("forest")])
        b = w.living_bands()[0]
        b.cell = cell
        w.bands_changed()
        n = float(w.band_sizes()[b.id])
        w.goods[b.id, trade.GI["copper"]] = per_person * n
        return w, b, T

    def test_a_technique_learned_this_year_on_imports_is_recorded_when_cut_off(self):
        w, b, T = self._copper_world(0.00505)
        k = T.INDEX["copper_working"]
        real = T.keep_and_spread

        def learn(w_, live, ids, cells, sizes, connected, need=None):
            real(w_, live, ids, cells, sizes, connected, need)
            w_.tech[b.id, k] = 0.8                           # acquired during the year, after the yearly sample
        T.keep_and_spread = learn
        try:
            T.yearly(w)
        finally:
            T.keep_and_spread = real
        w.goods[b.id, trade.GI["copper"]] = 0.0049 * float(w.band_sizes()[b.id])   # worn below the threshold
        n0 = len(w.events)
        T.yearly(w)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_cut_off"]
        self.assertEqual([e["data"]["technique"] for e in ev], ["copper_working"])

    def test_a_failed_prerequisite_is_not_called_imports_running_out(self):
        w, b, T = self._copper_world(0.02)
        for key in ("pottery", "kilns", "copper_working", "smelting"):
            w.tech[b.id, T.INDEX[key]] = 0.8
        ids, cells = np.array([b.id]), np.array([b.cell])
        T._mark(w, w.living_bands(), ids, cells)
        w.tech[b.id, T.INDEX["kilns"]] = P.TECH_WORKING * 0.5
        n0 = len(w.events)
        T._cut_off(w, w.living_bands(), ids, cells)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_cut_off"]
        self.assertEqual(ev, [])

    def test_the_prerequisite_check_accepts_imported_materials(self):
        w, b, T = self._copper_world(0.02)
        t = T.TECHNIQUES[T.INDEX["copper_working"]]
        self.assertTrue(T._possible(w, np.array([b.id]), np.array([b.cell]))[0, T.INDEX["copper_working"]])
        self.assertEqual(T.prerequisites_met(w, b, t), (True, []))


class DependenceCase(unittest.TestCase):
    """Ben, 16 November 2026: a small controlled case of dependence on imports (local/scripts/dependence_case.py)."""

    def _case(self):
        import importlib.util, os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local", "scripts", "dependence_case.py")
        spec = importlib.util.spec_from_file_location("dependence_case", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_cutting_the_tin_stops_bronze_with_the_cause_and_supply_keeps_it(self):
        m = self._case()
        m.START_TIN = 0.0052                                     # just above the threshold: the cut comes soon
        kept, ev_kept = m.run(12, supply=True)
        cut, ev_cut = m.run(12, supply=False)
        self.assertTrue(all(prac for _, _, prac, _ in kept))
        self.assertEqual([e for e in ev_kept if e["kind"] == "technique_cut_off"], [])
        stop = next(y for y, _, prac, _ in cut if not prac)
        tin_at_stop = next(t for y, t, _, _ in cut if y == stop)
        self.assertLess(tin_at_stop, P.MATERIAL_HELD)
        cuts = [e for e in ev_cut if e["kind"] == "technique_cut_off"]
        self.assertEqual([e["data"]["technique"] for e in cuts], ["bronze"])
        self.assertIn("tin", cuts[0]["causes"][-1]["note"])
        self.assertGreater(cut[-1][3], 0.0)                       # remembered, though no longer practised


class Review019(unittest.TestCase):
    """Codex review 019."""

    def _at(self, cell, chain, goods):
        from origins.sim import technology as T
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        b.cell = cell
        w.bands_changed()
        n = float(w.band_sizes()[b.id])
        for k in chain:
            w.tech[b.id, T.INDEX[k]] = 0.9
        for g, pp in goods.items():
            w.goods[b.id, trade.GI[g]] = pp * n
        return w, b, T, n

    def _cuts(self, w, T, b):
        n0 = len(w.events)
        T._cut_off(w, w.living_bands(), np.array([x.id for x in w.living_bands()]),
                   np.array([x.cell for x in w.living_bands()]))
        return [w.events[i] for i in range(n0, len(w.events))
                if w.events[i]["kind"] == "technique_cut_off" and w.events[i]["band"] == b.id]

    def _mark(self, w, T):
        live = w.living_bands()
        T._mark(w, live, np.array([x.id for x in live]), np.array([x.cell for x in live]))

    def test_restoring_a_lost_import_keeps_a_new_one(self):
        chain = ("pottery", "kilns", "copper_working", "smelting", "bronze")
        w, b, T, n = self._at(86, chain, {"tin": 0.01})
        self._mark(w, T)
        self.assertTrue(w.tech_prev_prac[b.id, T.INDEX["bronze"]])
        b.cell = 2                                                   # no copper or tin within reach here
        w.bands_changed()
        w.goods[b.id, trade.GI["copper"]] = 0.01 * n                 # copper now imported
        w.goods[b.id, trade.GI["tin"]] = 0.0                         # tin gone
        ev = self._cuts(w, T, b)
        self.assertIn("bronze", [e["data"]["technique"] for e in ev])
        self.assertEqual([e for e in ev if e["data"]["technique"] == "bronze"][0]["data"]["materials"], ["tin"])

    def test_joining_brings_the_record_of_practice(self):
        from origins.sim import technology as T
        w = World.new(1, 1, generate(1))
        src, dst = w.living_bands()[0], w.living_bands()[1]
        for b in (src, dst):
            b.cell = 2
        w.bands_changed()
        k = T.INDEX["copper_working"]
        w.tech[:, k] = 0.0
        w.tech[src.id, k] = 0.9
        w.goods[src.id, trade.GI["copper"]] = 0.02 * float(w.band_sizes()[src.id])
        self._mark(w, T)
        self.assertTrue(w.tech_prev_prac[src.id, k])
        self.assertFalse(w.tech_prev_prac[dst.id, k])
        T.combine(w, src, dst, "merge", 9)
        trade.move_share(w, src.id, dst.id, 1.0)
        n = float(w.band_sizes()[dst.id])
        w.goods[dst.id, trade.GI["copper"]] = 0.003 * n             # taken in a raid, below the threshold
        ev = self._cuts(w, T, dst)
        self.assertEqual([e["data"]["technique"] for e in ev], ["copper_working"])

    def test_the_cut_off_names_the_material_that_caused_it(self):
        chain = ("pottery", "kilns", "copper_working", "smelting", "iron")
        w, b, T, n = self._at(148, chain, {"copper": 0.01, "iron": 0.01})
        mats = T._cell_materials(w)[148]
        self.assertTrue(mats[T.MATERIALS.index("iron")])
        self.assertFalse(mats[T.MATERIALS.index("copper")])
        self._mark(w, T)
        w.goods[b.id, trade.GI["copper"]] = 0.0
        w.goods[b.id, trade.GI["iron"]] = 0.0
        ev = {e["data"]["technique"]: e for e in self._cuts(w, T, b)}
        self.assertIn("iron", ev)
        self.assertEqual(ev["iron"]["data"]["materials"], ["copper"])
        self.assertNotIn("the iron it had", ev["iron"]["causes"][0]["note"])

    def test_craft_time_grows_with_the_makers(self):
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        b.cell = int(np.nonzero(w.planet.coast)[0][0])
        w.bands_changed()
        w.spec[b.id] = 0.0
        one = trade.craft_share(w, np.array([b.id]))[0]
        idx = w.alive_idx()
        mine = idx[w.people.band[idx] == b.id]
        adults = mine[w.ages(mine) >= 16]
        w.people.birth[adults[: len(adults) // 2]] = w.t - 10 * P.TICKS_PER_YEAR   # half the adults made children
        w._live = None
        w._craft = None
        fewer = trade.craft_share(w, np.array([b.id]))[0]
        self.assertGreater(one, fewer)
        self.assertGreater(fewer, 0.0)


if __name__ == "__main__":
    unittest.main()


class Review038(unittest.TestCase):
    """Codex review 038: the speed fixes from the G4a pilot must not change what any routine returns."""

    def test_finding1_prestige_keeps_its_size_snapshot_within_a_tick(self):
        from origins.sim import demography, polity, traders
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        trade.ensure(w, w.next_band - 1, -1)
        p = polity._new_polity(w, b, [{"note": "t"}], why="t")
        traders.grow(w, p.id)
        n = w.band_size(b.id)
        w.treasury[p.id, trade.GI["gold"]] = 0.5 * n * P.PRESTIGE_NEED     # half the need per member
        first = trade.prestige_factor(w, p.id)
        self.assertAlmostEqual(first, 0.5, places=9)
        mem = w.members(b.id)
        demography.kill(w, mem[:len(mem) // 2], np.zeros(len(mem) // 2, dtype=int))   # deaths within the tick
        self.assertEqual(trade.prestige_factor(w, p.id), first)          # not seen until the next tick (as before)
        w.t += 1
        self.assertGreater(trade.prestige_factor(w, p.id), first)

    def test_finding2_size_helpers_refuse_absent_and_non_integer_ids(self):
        w = World.new(1, 1, generate(1))
        for bad in (-1, w.next_band):
            with self.assertRaises(IndexError):
                w.band_size(bad)
            with self.assertRaises(IndexError):
                w.sizes_of([bad])
        with self.assertRaises(TypeError):
            w.sizes_of([1.9])
        with self.assertRaises(TypeError):
            w.band_size(1.9)
        ids = [b.id for b in w.living_bands()]
        self.assertEqual(w.sizes_of(ids + ids[:1]).tolist(), w.band_sizes()[ids + ids[:1]].tolist())
        self.assertEqual([w.band_size(i) for i in ids], w.band_sizes()[ids].tolist())

    def test_finding3_closeness_is_kept_only_within_one_pass(self):
        import copy
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        la = w.languages[a.language]
        lb = copy.deepcopy(la)
        lb.id = 10 ** 6
        w.languages[lb.id] = lb
        b = copy.copy(a)
        b.language = lb.id
        cache = {}
        self.assertEqual(trade._closeness(w, a, b, cache), 1.0)
        m = next(iter(lb.lexicon))
        lb.lexicon[m] = [lb.lexicon[m][0], -12345] + list(lb.lexicon[m][2:])   # a root changed in place
        self.assertEqual(trade._closeness(w, a, b, cache), 1.0)          # within one pass: kept
        self.assertLess(trade._closeness(w, a, b), 1.0)                  # a new pass sees the change
        src = __import__("inspect").getsource(trade.partnerships_yearly)
        self.assertIn("close_cache: dict = {}", src)
