"""Gate G4a's code (Codex review 034): the planner's arms, the report's readings, and the records they rest on."""
import unittest

import numpy as np

from gates import g4, g4_report as R, plan


def _rec(**kw):
    """A minimal completed G4a record."""
    r = {"status": "completed", "world_seed": 1, "run_seed": 1, "arm": "", "seconds": 10.0, "record_seconds": 1.0,
         "end_year": 5000, "polity_firsts": {}, "first_village_year": None, "invariant_failures": 0}
    r.update(kw)
    return r


class Review034(unittest.TestCase):
    def setUp(self):
        self._g3 = R._g3
        R._g3 = lambda runs: ("| Check | Result | Evidence |\n|---|---|---|\n| 1. M0-M2 still hold | PASS | x |\n"
                              "| 7. Conflict has costs | — | none |\n| 11. Same rules | — | x |")

    def tearDown(self):
        R._g3 = self._g3

    def _report(self, recs):
        import tempfile, json
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        for i, r in enumerate(recs):
            (d / f"run_w{r['world_seed']}_s{r['run_seed']}_{i}.json").write_text(json.dumps(r))
        return R.report(d)

    def _row(self, txt, num):
        return next(l for l in txt.splitlines() if l.startswith(f"| {num}. "))

    def test_finding1_the_planner_launches_the_arms(self):
        p = plan._plan({"gate": "g4", "planets": "1-5", "seeds": "1-10", "arms": {"nopop": "1-4", "nocuration": "1-2"}})
        kinds = [j["kind"] for j in p["include"]]
        self.assertEqual(kinds.count("run"), 50)
        self.assertEqual(kinds.count("run_nopop"), 20)
        self.assertEqual(kinds.count("run_nocuration"), 10)
        self.assertEqual(set(g4.ARMS), {"nopop", "nocuration", "noprestige", "fourpartners"})
        sh = open("gates/run_job.sh").read()
        self.assertIn('FLAG="--arm ${KIND#run_}"', sh)
        self.assertIn('TAG="_${KIND#run_}"', sh)

    def test_finding2_one_dense_year_does_not_make_a_short_spell_persistent(self):
        spell = [0, 5, 100, 104, 5, 3, [[0, 10], [0, 10], [0, 10], [0, 10], [500, 9000]]]
        txt = self._report([_rec(disease_spells=[spell], diseases=[{"id": 0, "host": "cattle"}])])
        self.assertNotIn("| 10. Diseases from animals | PASS", txt)
        self.assertIn("— |", self._row(txt, 10))

    def test_finding3_soil_alone_does_not_pass_the_land(self):
        cells = [[c, True, 1 - c / 10, 0, 0.5, 0.5, 0.5, 1.0, 1 - c / 10, 20 + c, 0, 20 + c, 20 + c, None, 0, 800]
                 for c in range(10)]
        txt = self._report([_rec(land_cells=cells, land_events={"land_hunger": 1, "land_move": 1})])
        self.assertNotIn("| 9. The land answers back | PASS", txt)

    def test_finding4_an_unmeasured_earlier_check_is_not_a_pass(self):
        txt = self._report([_rec()])
        row = self._row(txt, 1)
        self.assertIn("| — |", row)
        self.assertIn("without a verdict: 7. Conflict has costs", row)

    def test_finding5_the_census_uses_what_invention_uses(self):
        from origins.sim import technology as T
        from origins.state import World
        from origins.worldgen import generate
        from origins import params as P
        w = World.new(1, 1, generate(1))
        live = w.living_bands()
        a = live[0]
        far = next(c for c in range(w.planet.n) if w.planet.land[c] and
                   np.linalg.norm(w.planet.grid.xyz[c] - w.planet.grid.xyz[a.cell]) > 0.5)
        b = live[1]
        b.cell = far
        w.bands_changed()
        ids = np.array([x.id for x in w.living_bands()])
        cells = np.array([x.cell for x in w.living_bands()])
        sizes = np.asarray(w.live_sizes(), float)
        pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
        before = T.connected_people(w, ids, cells, pop)
        w.trade_links = [[a.id, b.id]]
        old = P.TRADE
        P.TRADE = True
        try:
            after = T.connected_people(w, ids, cells, pop)
        finally:
            P.TRADE = old
        i, j = list(ids).index(a.id), list(ids).index(b.id)
        self.assertAlmostEqual(after[i] - before[i], P.TECH_TRADE_REACH * before[j], places=6)

    def test_finding5_the_knock_out_cannot_pass_on_a_negative_main_median(self):
        rows = []
        inv = []
        for k in range(60):                              # main: more connected, fewer inventions
            rows.append([0, k, 0, 100 + k, 0, 0.5, 3, 5, 0.0, True])
            inv += [[0, k, "x"]] * (60 - k)
        knock = [[0, k, 0, 100 + k, 0, 0.5, 3, 5, 0.0, True] for k in range(60)]
        kinv = [[0, k, "x"] for k in range(60) for _ in range(1 + (k % 3))]
        txt = self._report([_rec(census=rows, inventions_by_band=inv),
                            _rec(arm="nopop", census=knock, inventions_by_band=kinv)])
        self.assertNotIn("| 6. Knock-out: no population effect | PASS", txt)

    def test_finding6_lost_and_relearned_counts_as_learned(self):
        class W:
            events = [{"kind": "invention", "band": 1, "t": 0, "cell": 0, "data": {"technique": "pottery"}},
                      {"kind": "technique_lost", "band": 1, "t": 4, "cell": 0, "data": {"technique": "pottery"}},
                      {"kind": "invention", "band": 2, "t": 4, "cell": 5, "data": {"technique": "pottery"}},
                      {"kind": "technique_adopted", "band": 1, "t": 8, "cell": 0,
                       "data": {"technique": "pottery", "source": 2, "route": "trade"}}]
        hold, first, firsts = g4.transmission(W())
        self.assertEqual(hold[1]["pottery"], ["others", 1])
        self.assertEqual(first[0][4], 1)

    def test_finding6_loss_fifths_have_no_empty_bins(self):
        rows = [[0, k, 0, 1.0, 0, 0.5, 1, 5, 0.0, True] for k in range(48)]
        rows += [[0, 100 + k, 0, 1000.0, 0, 0.5, 1, 9, 0.0, True] for k in range(12)]
        losses = [[10, 100 + k, "x", True, 0] for k in range(12)]
        rates, rq, rk, nloss = R.loss_by_reach(_rec(census=rows, losses_by_band=losses))
        self.assertFalse(any(np.isnan(x) for x in rates))
        self.assertGreater(rq, 0)                         # losses where reach is high: the check must not pass

    def test_finding7_no_help_is_not_a_pass(self):
        fall = {g: {str(k): [5, 1.0 / (k + 1)] for k in range(6)} for g in ("fine_stone", "salt", "shell")}
        txt = self._report([_rec(goods_falloff=fall, help_by_year={})])
        self.assertNotIn("| 7. Trade follows supply and distance | PASS", txt)

    def test_finding9_absent_kinds_are_not_a_pass(self):
        txt = self._report([_rec(chains={"invention": [1, 1, 1]})])
        row = self._row(txt, 11)
        self.assertNotIn("| PASS |", row)
        self.assertIn("Never happened in any history", row)

    def test_finding10_a_current_save_keeps_its_m1_counts(self):
        from origins import persist
        from origins.state import World
        from origins.worldgen import generate
        w = World.new(1, 1, generate(1))
        w.diseases = [{"id": 0, "host": "wild"}]
        w.counts["ob_new_starts"] = 2
        w.counts["unattributed_ob_new_starts"] = 17
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(w2.counts.get("ob_new_starts"), 2)
        self.assertEqual(w2.counts.get("unattributed_ob_new_starts"), 17)
        self.assertEqual(persist.digest(w), persist.digest(w2))


if __name__ == "__main__":
    unittest.main()


class Review035(unittest.TestCase):
    """Codex review 035 (state and per-band arrays): findings reproduced, then fixed."""

    def _world(self, years=20):
        from origins import engine
        from origins.state import World
        from origins.worldgen import generate
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * years)
        return w

    def test_finding1_an_ended_group_does_not_erase_a_living_groups_needs(self):
        from origins.sim import bands, groups
        w = self._world()
        live = [b for b in w.living_bands() if b.mode != "group"]
        if len(live) < 2:
            self.skipTest("need two bands")
        last = max(live, key=lambda b: b.id)
        other = next(b for b in live if b.id != last.id)
        groups.fold(w, last)
        groups.fold(w, other)                            # the second band's group row comes after the last's
        ids, pos = w.live_index()
        before = groups.needs_and_work(w, pos, len(ids))
        G = w.groups
        G.F[other.group] = 0
        G.M[other.group] = 0
        bands.end_band(w, other, "test", log=False)
        ids, pos = w.live_index()
        after = groups.needs_and_work(w, pos, len(ids))
        i = list(ids).index(last.id)
        self.assertGreater(after[1][i], 0)
        self.assertFalse(G.active[other.group] if other.group >= 0 else False)

    def test_finding2_the_digest_sees_still_years_firsts_and_recent_events(self):
        from origins import persist
        w = self._world(5)
        b = w.living_bands()[0]
        d0 = persist.digest(w)
        w.still_years[b.id] += 25
        self.assertNotEqual(persist.digest(w), d0)
        d1 = persist.digest(w)
        w.tech_firsts = dict(getattr(w, "tech_firsts", {}), pottery=1)
        self.assertNotEqual(persist.digest(w), d1)
        # two worlds alike but for whom an earlier conquest moved, each followed by another event
        w1 = persist.from_bytes(persist.to_bytes(w), w.planet)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        for x, moved in ((w1, [b.id]), (w2, [b.id, 5])):
            x.event("conquest", cell=b.cell, band=b.id, polity=1, moved=moved)
            x.event("note", cell=b.cell, band=b.id)
        self.assertNotEqual(persist.digest(w1), persist.digest(w2))

    def test_finding3_an_empty_trade_attempt_is_no_contact(self):
        import inspect
        from origins.sim import traders
        src = inspect.getsource(traders.yearly)
        self.assertIn("if _carry(", src)
        self.assertIn("return False", inspect.getsource(traders._carry))

    def test_finding4_captives_and_spouses_bring_their_immunity(self):
        import inspect
        from origins.sim import conflict, demography
        self.assertIn("disease.combine(w, t, b, caps)", inspect.getsource(conflict))
        self.assertIn("disease.combine(w, w.bands[src], w.bands[dst], movers)", inspect.getsource(demography))

    def test_finding5_a_merger_cannot_make_up_a_dependence(self):
        from origins.sim import technology as T
        from origins import params as P
        w = self._world(5)
        live = w.living_bands()
        a, b = live[0], live[1]
        T._prev_arrays(w)
        k = T.INDEX["copper_working"]
        w.tech_prev_prac[a.id, k] = True                 # a practised copper working on local copper
        w.tech_prev_dep[a.id, k] = False
        w.tech_prev_mats[b.id, T.MATERIALS.index("copper")] = True   # b had traded copper, never practised
        T.combine(w, b, a, "merge", 30)
        self.assertFalse(w.tech_prev_dep[a.id, k])

    def test_finding6_consolidation_keeps_receipts_and_herding_history(self):
        from origins.sim import bands
        w = self._world(5)
        a, b = w.living_bands()[0], w.living_bands()[1]
        from origins.sim import trade
        trade._trade_in_size(w)
        w.trade_in[b.id] = 3.0
        w.herder_since[b.id] = 40
        w.herder_since[a.id] = -1
        bands.carry(w, b, a, "combined", 10)
        self.assertEqual(float(w.trade_in[a.id]), 3.0)
        self.assertEqual(int(w.herder_since[a.id]), 40)

    def test_finding7_unfolding_keeps_a_single_womans_pregnancy(self):
        from origins.sim import groups
        w = self._world(1)
        b = next(x for x in w.living_bands() if x.mode != "group")
        groups.fold(w, b)
        G = w.groups
        G.F[b.group] = 0
        G.M[b.group] = 0
        G.F[b.group, 25] = 1
        G.preg[b.group] = 0
        G.preg[b.group, 0] = 1
        ids = groups.unfold(w, b)
        self.assertEqual(len(ids), 1)
        self.assertGreaterEqual(int(w.people.preg_due[ids[0]]), 0)
