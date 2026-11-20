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
