"""M0 regression tests. Run from the project folder:  python -m unittest discover -s tests -v"""
import copy
import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from origins import engine, explain, interventions, persist  # noqa: E402
from origins import names as N  # noqa: E402
from origins import params as P  # noqa: E402
from origins.sim import bands, groups, observe  # noqa: E402
from origins.state import World  # noqa: E402
from origins.worldgen import BIOMES, generate  # noqa: E402

_PLANET = {}


def planet(seed=1):
    if seed not in _PLANET:
        _PLANET[seed] = generate(seed)
    return _PLANET[seed]


def world(ws=1, rs=1, years=0):
    w = World.new(ws, rs, planet(ws))
    if years:
        engine.step(w, 4 * years)
    return w


class WorldGeneration(unittest.TestCase):
    def test_grid_shape_and_neighbours(self):
        p = planet()
        self.assertEqual(p.n, 40962)
        self.assertTrue(set(np.unique(p.grid.n_neighbours)) <= {5, 6})
        self.assertEqual(int((p.grid.n_neighbours == 5).sum()), 12)
        nb = p.grid.neighbours
        for c in range(0, p.n, 997):
            for m in nb[c][nb[c] >= 0]:
                self.assertIn(c, nb[m])
        self.assertAlmostEqual(p.grid.cell_area_km2, 3113, delta=5)

    def test_deterministic_and_plausible(self):
        a, b = generate(5), generate(5)
        self.assertEqual(a.fingerprint, b.fingerprint)
        self.assertNotEqual(a.fingerprint, planet(1).fingerprint)
        land = (a.land | a.lake).mean()
        self.assertAlmostEqual(land, 0.30, delta=0.01)
        self.assertTrue(a.river.any() and a.lake.any())
        s = a.start_cell
        self.assertTrue(a.land[s] and a.capacity[s] > 0)
        self.assertNotIn(BIOMES[a.biome[s]], ("ice", "desert", "ocean"))
        self.assertTrue(np.allclose(a.season_food.mean(1)[a.land], 1.0))


class Founding(unittest.TestCase):
    def test_founding_band(self):
        w = world()
        p = w.people
        self.assertEqual(p.n, 30)
        self.assertEqual(len(w.living_bands()), 1)
        for i in range(p.n):
            m = p.mother[i]
            if m >= 0:
                self.assertGreaterEqual(w.ages(m) - w.ages(i), 16)
            if p.partner[i] >= 0:
                self.assertEqual(p.partner[p.partner[i]], i)
                self.assertNotEqual(p.sex[i], p.sex[p.partner[i]])


class Simulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = world(2, 3, 400)

    def test_invariants_hold(self):
        self.assertEqual(self.w.invariant_failures, [])

    def test_population_accounting(self):
        w = self.w
        alive = len(w.alive_idx()) + int(round(groups.sizes(w).sum()))
        self.assertEqual(alive, w.counts["founders"] + w.counts["births"] - w.counts["deaths"])

    def test_no_close_kin_partnerships(self):
        p = self.w.people
        for i in np.nonzero(p.partner[:p.n] >= 0)[0]:
            j = p.partner[i]
            self.assertFalse(p.mother[i] >= 0 and p.mother[i] == p.mother[j])
            self.assertFalse(p.father[i] >= 0 and p.father[i] == p.father[j])
            self.assertNotIn(j, (p.mother[i], p.father[i]))

    def test_births_need_living_partnered_mothers(self):
        p = self.w.people
        kids = np.nonzero(p.mother[:p.n] >= 0)[0]
        kids = kids[p.birth[kids] > 0]
        m = p.mother[kids]
        self.assertTrue((p.sex[m] == 0).all())
        dead_before = (p.death[m] >= 0) & (p.death[m] < p.birth[kids])
        self.assertFalse(dead_before.any())
        age_at = (p.birth[kids] - p.birth[m]) / P.TICKS_PER_YEAR
        self.assertTrue((age_at >= P.FEMALE_MIN_AGE - 1).all() and (age_at <= P.FEMALE_MAX_AGE + 1).all())

    def test_explanations_resolve(self):
        w = self.w
        p = w.people
        dead = np.nonzero(p.death[:p.n] >= 0)[0][:300]
        for i in dead:
            self.assertTrue(explain.resolvable(w, {"death": int(i)}), i)
        for e in w.events:
            self.assertTrue(explain.resolvable(w, {"event": e["id"]}), e)

    def test_demography_plausible(self):
        lt = observe.life_table(self.w)
        self.assertTrue(25 <= lt["e0"] <= 40, lt)
        self.assertTrue(4 <= lt["tfr"] <= 7, lt)


class Replay(unittest.TestCase):
    def test_save_load_continue_is_exact(self):
        a = world(3, 4, 150)
        engine.step(a, 2)
        b = persist.from_bytes(persist.to_bytes(a), a.planet)
        self.assertEqual(persist.digest(a), persist.digest(b))
        engine.step(a, 41)
        engine.step(b, 41)
        self.assertEqual(persist.digest(a), persist.digest(b))
        c = world(3, 4)
        engine.step(c, 4 * 150 + 2 + 41)
        self.assertEqual(persist.digest(a), persist.digest(c))

    def test_histories_independent_across_planets(self):
        """The same history seed on different planets must not replay the same births and deaths."""
        a, b = world(1, 9, 60), world(2, 9, 60)
        pa, pb = a.people, b.people
        self.assertFalse(pa.n == pb.n and (pa.birth[:pa.n] == pb.birth[:pb.n]).all()
                         and (pa.death[:pa.n] == pb.death[:pb.n]).all())

    def test_hash_seed_independent(self):
        code = ("import sys; sys.path.insert(0, %r); from origins.state import World; from origins import engine, persist;"
                "w = World.new(4, 2); engine.step(w, 400); print(persist.digest(w))") % str(ROOT)
        outs = [subprocess.check_output([sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": s},
                                        text=True).strip() for s in ("1", "77")]
        self.assertEqual(outs[0], outs[1])

    def test_file_save_keeps_backups(self):
        import tempfile
        w = world(1, 2, 20)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "w.zip"
            for _ in range(4):
                persist.save(w, path)
                engine.step(w, 4)
            names = sorted(f.name for f in Path(d).iterdir())
            self.assertEqual(names, ["w.bak1.zip", "w.bak2.zip", "w.bak3.zip", "w.zip"])
            self.assertEqual(persist.load(path).t, w.t - 4)

    def test_wrong_schema_rejected(self):
        import io
        import json
        import zipfile
        data = persist.to_bytes(world())
        zin = zipfile.ZipFile(io.BytesIO(data))
        meta = json.loads(zin.read("meta.json"))
        meta["schema"] = 99
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("meta.json", json.dumps(meta))
            z.writestr("arrays.npz", zin.read("arrays.npz"))
        with self.assertRaises(ValueError):
            persist.from_bytes(out.getvalue())


class GroupsMatchIndividuals(unittest.TestCase):
    def test_rates_match(self):
        """Folding everyone into groups should not change birth and death rates beyond chance."""
        base = world(1, 5, 650)
        ind = persist.from_bytes(persist.to_bytes(base), base.planet)
        grp = persist.from_bytes(persist.to_bytes(base), base.planet)
        for b in list(grp.living_bands()):
            groups.fold(grp, b)
        self.assertEqual(ind.population(), grp.population())
        stats = []
        for w in (ind, grp):
            b0, d0 = w.counts["births"], w.counts["deaths"]
            py0 = w.accum["person_years"].sum()
            engine.step(w, 4 * 150)
            py = w.accum["person_years"].sum() - py0
            stats.append(((w.counts["births"] - b0) / py, (w.counts["deaths"] - d0) / py))
            self.assertEqual(w.invariant_failures, [])
        (bi, di), (bg, dg) = stats
        self.assertAlmostEqual(bg / bi, 1.0, delta=0.15, msg=stats)
        self.assertAlmostEqual(dg / di, 1.0, delta=0.15, msg=stats)

    def test_unfold_preserves_people(self):
        w = world(1, 6, 300)
        b = max(w.living_bands(), key=lambda b: len(w.members(b.id)))
        pop = w.population()
        groups.fold(w, b)
        self.assertEqual(w.population(), pop)
        ids = groups.unfold(w, b)
        self.assertEqual(w.population(), pop)
        self.assertEqual(b.mode, "individual")
        self.assertTrue(len(ids) > 0)
        engine.step(w, 8)
        self.assertEqual(w.invariant_failures, [])

    def test_threshold_folds_distant_bands(self):
        w = world(1, 1, 300)
        old = P.INDIVIDUAL_THRESHOLD
        try:
            n = len(w.alive_idx())
            P.INDIVIDUAL_THRESHOLD = n // 2
            bands.fold_distant(w)
            self.assertLessEqual(len(w.alive_idx()), n // 2)
            self.assertTrue(any(b.mode == "group" for b in w.living_bands()))
            engine.step(w, 8)
            self.assertEqual(w.invariant_failures, [])
        finally:
            P.INDIVIDUAL_THRESHOLD = old


class Interventions(unittest.TestCase):
    def test_food_shock_logged_and_restored(self):
        w = world(2, 2, 200)
        cell = w.living_bands()[0].cell
        cells = interventions.cells_within(w, cell, 1)
        before = w.food_modifier[cells].copy()
        eid = interventions.food_shock(w, cells, 0.5, 4, "test")
        self.assertTrue(w.intervened)
        self.assertEqual(w.events[eid]["kind"], "intervention")
        engine.step(w, 4)
        self.assertTrue(np.allclose(w.food_modifier[cells], before * 0.5))   # still in force for its 4 seasons
        engine.step(w, 1)
        self.assertTrue(np.allclose(w.food_modifier[cells], before))
        self.assertTrue((w.intervention_event[cells] == -1).all())
        self.assertEqual(w.invariant_failures, [])


class Names(unittest.TestCase):
    def test_all_names_render(self):
        for a in range(len(N.FIRST)):
            for b in [-1] + list(range(len(N.SECOND))):
                for female in (True, False):
                    s = N.render(a, b, female)
                    self.assertTrue(s and s[0].isupper() and s.isalpha(), s)
                self.assertIn("*", N.etymology(a, b))


class Observatory(unittest.TestCase):
    def test_views(self):
        from origins import server
        w = world(1, 1, 120)
        server.state["world"] = w
        s = server.summary(w)
        self.assertEqual(s["population"], w.population())
        g = server.geometry(w)
        self.assertEqual(len(g["poly"]), w.planet.n)
        bid = w.living_bands()[0].id
        d = server.band_detail(w, bid)
        self.assertEqual(d["size"], len(w.members(bid)))
        pid = int(w.members(bid)[0])
        self.assertEqual(server.person_detail(w, pid)["id"], pid)
        self.assertTrue(server.recent_events(w))
        server.control({"action": "follow", "band": bid, "rate": 3})
        self.assertEqual(w.follow, bid)
        server.control({"action": "unfollow"})
        self.assertEqual(w.follow, -1)
        with self.assertRaises(ValueError):
            server.control({"action": "fast", "years": 999999})


if __name__ == "__main__":
    unittest.main()
