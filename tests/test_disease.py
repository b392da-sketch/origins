"""M4a: diseases from animals (M4 specification section 6; Ben, 20 November 2026)."""
import unittest

import numpy as np

from origins import params as P
from origins.state import World
from origins.worldgen import generate
from origins.sim import disease


def world():
    w = World.new(1, 1, generate(1))
    disease.ensure(w, max(b.id for b in w.living_bands()), -1)
    return w


def add(w, cell, **traits):
    """A disease with given traits, arriving on a cell: its first year's epidemic runs at the next yearly pass
    (k is applied after that year)."""
    active = np.zeros((w.planet.n, disease.ND_CAP), dtype=bool)
    disease._new(w, w.rng["disease"], cell, "wild", active, {}, "test", None)
    d = len(w.diseases) - 1
    k = traits.pop("k", None)
    w.diseases[d].update(traits)
    w.diseases[d]["k"] = 1e-12                       # sure to keep going into the first pass
    w.diseases[d]["k_after"] = k
    w.dz_active[cell, d] = True
    return d


def first_year(w):
    disease.yearly(w)
    for dz in w.diseases:
        if dz.get("k_after") is not None:
            dz["k"] = dz.pop("k_after")


class Disease(unittest.TestCase):

    def test_a_disease_keeps_going_only_where_enough_people_can_catch_it(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)             # needs far more people than live here
        first_year(w)                                               # first epidemic
        self.assertTrue(w.dz_active[b.cell, d])
        gone = 0
        for _ in range(5):
            disease.yearly(w)
            gone += not w.dz_active[:, d].any()
        self.assertGreater(gone, 0)
        w2 = world()
        b2 = w2.living_bands()[0]
        d2 = add(w2, b2.cell, k=1e-9, attack=0.9, cfr=0.0)          # any susceptible keeps it going
        first_year(w2)
        for _ in range(5):
            disease.yearly(w2)
        self.assertTrue(w2.dz_active[b2.cell, d2])

    def test_survivors_are_immune_and_new_children_are_not(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e9, attack=1.0, cfr=0.0, lasting=True)
        first_year(w)
        self.assertAlmostEqual(float(w.dz_imm[b.id, d, disease.ADULT]), 1.0, places=5)
        for _ in range(12):
            disease._age_and_wane(w, np.array([b.id]))
        self.assertLess(float(w.dz_imm[b.id, d, disease.CHILD]), 0.5)   # children born since can catch it
        self.assertGreater(float(w.dz_imm[b.id, d, disease.ADULT]), 0.8)

    def test_herds_bring_new_diseases_only_after_domestication(self):
        from origins.sim import farming
        w = world()
        b = w.living_bands()[0]
        _, suit = farming.land_tables(w)
        k = [i for i in farming.ANIMALS if suit[b.cell, i] > 0]
        if not k:
            self.skipTest("no animal can live here")
        k = k[0]
        w.skill[:] = 0
        w.skill[b.id, k] = 3
        w.farm_share[b.id] = 1.0
        old = P.DZ_EMERGE_HERD, P.DZ_EMERGE_WILD
        P.DZ_EMERGE_HERD, P.DZ_EMERGE_WILD = 1.0, 0.0
        try:
            disease.yearly(w)
            self.assertEqual(len(w.diseases), 0)                      # no domestication recorded yet: no time together
            name = farming.SPECIES[k]
            w.farm_firsts[name] = {"domestication": w.event("first_domestication", cell=b.cell, band=b.id)}
            w.t += int(P.DZ_DOM_YEARS * P.TICKS_PER_YEAR)
            disease.yearly(w)
            self.assertEqual([dz["host"] for dz in w.diseases], [name])
        finally:
            P.DZ_EMERGE_HERD, P.DZ_EMERGE_WILD = old

    def _deaths(self, hunger, trait, adults_immune=0.0):
        w = world()
        b = w.living_bands()[0]
        for x in w.living_bands():
            x.last_ratio = 1.0 - hunger
        d = add(w, b.cell, k=1e9, attack=1.0, cfr=0.2, hunger=trait, child=1.0)
        w.dz_imm[:, d, disease.ADULT] = adults_immune
        n0 = w.counts["deaths"]
        first_year(w)
        return w.counts["deaths"] - n0

    def test_hunger_raises_deaths_only_for_diseases_that_depend_on_food(self):
        np.random.seed(0)
        fed = self._deaths(0.0, 1.5)
        hungry = self._deaths(0.5, 1.5)
        self.assertGreater(hungry, fed)
        a = self._deaths(0.0, 0.0)
        b = self._deaths(0.5, 0.0)
        self.assertEqual(a, b)                                          # same draws, no hunger effect

    def test_too_many_adults_ill_at_once_raises_deaths(self):
        many = self._deaths(0.0, 0.0, adults_immune=0.0)                # all adults ill: crisis
        few = self._deaths(0.0, 0.0, adults_immune=0.9)                 # most adults immune
        self.assertGreater(many, few)

    def test_isolating_the_sick_means_fewer_caught(self):
        from origins.sim import customs
        k = customs.NAMES.index("response to epidemics")
        res = []
        for variant in (0, 2):
            w = world()
            b = w.living_bands()[0]
            w.customs[:, k] = variant
            d = add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)
            first_year(w)
            res.append(float(w.dz_imm[b.id, d, disease.ADULT]))
        self.assertLess(res[1], res[0])

    def test_saves_keep_the_diseases(self):
        from origins import persist
        w = world()
        b = w.living_bands()[0]
        add(w, b.cell, k=1e9, attack=0.9, cfr=0.05)
        first_year(w)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(w2.diseases, w.diseases)
        self.assertTrue(np.array_equal(w2.dz_imm, w.dz_imm))
        self.assertEqual(persist.digest(w2), persist.digest(w))

    def test_a_disease_that_died_out_can_pass_again_from_its_animals(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e-12, attack=0.9, cfr=0.0)
        first_year(w)
        w.dz_active[:] = False                                          # gone from people
        old = P.DZ_RESPILL_WILD, P.DZ_EMERGE_WILD
        P.DZ_RESPILL_WILD, P.DZ_EMERGE_WILD = 1.0, 0.0
        try:
            n0 = len(w.events)
            disease.yearly(w)
        finally:
            P.DZ_RESPILL_WILD, P.DZ_EMERGE_WILD = old
        self.assertTrue(w.dz_active[b.cell, d])                         # back where people live in its region
        ob = [e for e in w.events[n0:] if e["kind"] == "outbreak"]
        self.assertEqual(len(ob), 1)
        self.assertIn("passed again from its animals", ob[0]["causes"][1]["note"])
        self.assertEqual(len(w.diseases), 1)                            # the same disease, not a new one
        far = w.planet.region != w.planet.region[w.diseases[d]["cell"]]
        self.assertFalse(w.dz_active[far, d].any())                     # only within its reservoir's range

    def test_switched_off_m1_outbreaks_run(self):
        from origins.sim import hazards
        w = world()
        old = P.DISEASE
        P.DISEASE = False
        try:
            hazards.yearly(w)
            self.assertEqual(len(w.diseases), 0)
        finally:
            P.DISEASE = old



class Review028(unittest.TestCase):
    """Codex review 028."""

    def test_joining_people_are_counted_once_in_the_weight(self):
        w = world()
        a, b = w.living_bands()[0], w.living_bands()[1]
        d = add(w, a.cell, k=1e9, attack=0.9, cfr=0.0)
        w.dz_imm[a.id, d] = 0.0
        w.dz_imm[b.id, d] = 1.0
        mb = w.members(b.id)
        na, nb_ = len(w.members(a.id)), len(mb)
        w.people.band[mb] = a.id                                        # the people move first, as in bands.py
        w.people_changed()
        disease.combine(w, b, a, nb_)
        self.assertAlmostEqual(float(w.dz_imm[a.id, d, disease.ADULT]), nb_ / (na + nb_), places=5)

    def test_deaths_never_exceed_cases_and_immunity_is_among_survivors(self):
        ill, dead, imm = disease.cohort(np.array([0.5]), np.array([0.2]), np.array([0.2]))
        self.assertAlmostEqual(float(ill[0]), 0.4)
        self.assertAlmostEqual(float(dead[0]), 0.08)
        self.assertAlmostEqual(float(imm[0]), 0.52 / 0.92, places=6)    # Codex's 0.5652, not 0.60
        ill, dead, _ = disease.cohort(np.array([0.5]), np.array([0.0]), np.array([2.0]))
        self.assertAlmostEqual(float(dead[0]), 0.5)                     # not 1.0

    def test_a_group_with_no_women_left_delivers_no_one(self):
        from origins.sim import groups
        w = world()
        b = w.living_bands()[0]
        groups.fold(w, b)
        G = w.groups
        G.preg[b.group, 0] = 1.0
        disease._kill(w, w.rng["disease"], [b], np.array([b.id]), np.array([1.0]), np.array([1.0]),
                      np.array([1.0]), -1)
        self.assertEqual(float(G.total(b.group)), 0.0)
        n0 = w.counts["births"]
        groups.births(w)
        self.assertEqual(w.counts["births"], n0)

    def test_kept_pregnancies_stay_whole(self):
        from origins.sim import groups
        w = world()
        b = w.living_bands()[0]
        groups.fold(w, b)
        G = w.groups
        g = b.group
        G.preg[g, :] = 1.0
        before = groups.women(G, np.array([g]))
        G.F[g, 15:50] = np.floor(G.F[g, 15:50] * 0.6)                  # some women die
        groups.keep_pregnancies(G, np.array([g]), before)
        self.assertTrue(np.all(G.preg[g] == np.rint(G.preg[g])))
        self.assertTrue(np.all(G.preg[g] >= 0))
        groups.split(w, b, b.cell, w.rng["fission"])
        self.assertTrue(np.all(G.preg[g] >= 0))

    def test_contact_counts_are_in_matched_units_and_cells_are_logged(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e-9, attack=0.9, cfr=0.0)              # keeps going: a source next year
        old = P.DZ_SPREAD
        P.DZ_SPREAD = 1e9
        try:
            c0 = dict(w.counts)
            first_year(w)
        finally:
            P.DZ_SPREAD = old
        cy = w.counts["dz_contact_cell_years"] - c0.get("dz_contact_cell_years", 0)
        ci = w.counts["dz_contact_arrivals"] - c0.get("dz_contact_arrivals", 0)
        self.assertGreater(ci, 0)
        self.assertLessEqual(ci, cy)                                     # arrivals among the cells counted
        rows = [r for r in w.dz_log if r[1] == d]
        self.assertTrue(any(r[3] == 2 and r[4] >= 0 for r in rows))     # a contact row names its source cell
        self.assertTrue(any(r[2] == b.cell and r[8] > 0 and r[10] + r[12] == 0 for r in rows))   # never met



class Review029(unittest.TestCase):
    """Codex review 029."""

    def _group(self):
        from origins.sim import groups
        w = world()
        b = w.living_bands()[0]
        groups.fold(w, b)
        return w, b, w.groups, b.group

    def test_a_pregnancy_goes_with_the_woman(self):
        from origins.sim import groups
        w, b, G, g = self._group()
        G.F[g] = 0
        G.M[g] = 0
        G.F[g, 25], G.M[g, 30] = 1, 1
        G.preg[g] = 0
        G.preg[g, 0] = 1
        hF = np.zeros_like(G.F[g])
        hF[25] = 1                                                      # Codex's case: the woman moves
        self.assertEqual(int(groups._split_pregnancies(G, g, hF, w.rng["fission"]).sum()), 1)
        self.assertEqual(int(groups._split_pregnancies(G, g, np.zeros_like(hF), w.rng["fission"]).sum()), 0)

    def test_no_more_pregnancies_than_women(self):
        from origins.sim import groups
        w, b, G, g = self._group()
        G.F[g] = 0
        G.F[g, 20:23] = 1
        G.preg[g] = 0
        G.preg[g, :3] = 1
        before = groups.women(G, np.array([g]))
        G.F[g, 22] = 0                                                  # one of three women dies
        groups.keep_pregnancies(G, np.array([g]), before)
        self.assertEqual(float(G.preg[g].sum()), 2.0)                   # Codex's case: was 3

    def test_adults_immunity_counts_the_deaths_of_the_old(self):
        im = disease.adult_immune(np.array([0.2]), np.array([0.2]), np.array([0.04]), np.array([0.08]), old_share=1.0)
        self.assertAlmostEqual(float(im[0]), 0.32 / 0.92, places=6)     # Codex's 0.347826 for a band of the old

    def test_a_later_epidemic_starts_from_the_people_left(self):
        w = world()
        b = w.living_bands()[0]
        d1 = add(w, b.cell, k=1e9, attack=1.0, cfr=0.3, child=1.0, hunger=0.0)
        d2 = add(w, b.cell, k=1e9, attack=1.0, cfr=0.3, child=1.0, hunger=0.0)
        first_year(w)
        rows = {r[1]: r for r in w.dz_log if r[2] == b.cell}
        P_, D_ = disease.LOG_PEOPLE, disease.LOG_DEATHS
        self.assertGreater(rows[d1][D_], 0)
        self.assertEqual(rows[d2][P_], rows[d1][P_] - rows[d1][D_])    # people at the second's start

    def test_a_return_from_animals_is_not_counted_as_contact(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e-9, attack=0.9, cfr=0.0)
        first_year(w)
        w.dz_active[:, d] = False
        w.dz_active[b.cell, d] = True                                   # only the first cell circulates
        w.dz_imm[:, d] = 0.0
        old = P.DZ_SPREAD, P.DZ_RESPILL_WILD
        P.DZ_SPREAD, P.DZ_RESPILL_WILD = 0.0, 1.0                       # no contact spread; the reservoir seeds all
        try:
            c0 = dict(w.counts)
            disease.yearly(w)
        finally:
            P.DZ_SPREAD, P.DZ_RESPILL_WILD = old
        self.assertGreater(w.counts["dz_contact_cell_years"] - c0.get("dz_contact_cell_years", 0), 0)
        self.assertGreater(w.counts["dz_other_starts"] - c0.get("dz_other_starts", 0)
                           + sum(1 for r in w.dz_log if r[3] == 1), 0)    # the reservoir did seed cells
        self.assertEqual(w.counts["dz_contact_arrivals"] - c0.get("dz_contact_arrivals", 0), 0)

    def test_the_record_can_measure_check_10(self):
        n = len(disease.LOG_FIELDS)
        w = world()
        b = w.living_bands()[0]
        add(w, b.cell, k=1e9, attack=0.9, cfr=0.1)
        first_year(w)
        r = w.dz_log[-1]
        self.assertEqual(len(r), n)
        self.assertEqual(r[8] + r[10] + r[12], r[disease.LOG_PEOPLE])  # people split by when they had met it



class Review030(unittest.TestCase):
    """Codex review 030 and Ben's definition of first contact (20 November 2026)."""

    def _group(self):
        from origins.sim import groups
        w = world()
        b = w.living_bands()[0]
        groups.fold(w, b)
        return w, b, w.groups, b.group

    def test_a_move_never_leaves_more_pregnancies_than_women(self):
        from origins.sim import groups
        w, b, G, g = self._group()
        G.F[g] = 0
        G.F[g, 25:27] = 1                                               # two women, both pregnant
        G.preg[g] = 0
        G.preg[g, 0] = 2
        hF = np.zeros_like(G.F[g])
        hF[25] = 1                                                      # one of them moves
        for _ in range(50):
            moved = groups._split_pregnancies(G, g, hF, w.rng["fission"])
            self.assertEqual(int(moved.sum()), 1)                       # exactly hers, never both

    def test_conceptions_never_exceed_the_women_not_yet_pregnant(self):
        from origins.sim import groups
        w, b, G, g = self._group()
        G.F[g] = 0
        G.M[g] = 0
        G.F[g, 25] = 1
        G.M[g, 30] = 1
        G.preg[g] = 0
        G.cond_rest[g] = 1.0
        old = P.CONCEPTION
        P.CONCEPTION = 1e6                                              # a huge draw
        try:
            for _ in range(5):
                groups.births(w)
                self.assertLessEqual(float(G.preg[g].sum()), float(G.F[g, 15:50].sum()))
        finally:
            P.CONCEPTION = old

    def test_older_rows_are_upgraded(self):
        rows = disease.upgrade_log([[2, 0, 5, 3, -1, 30, 0.8, True, 1]])
        self.assertEqual(len(rows[0]), len(disease.LOG_FIELDS))
        self.assertEqual(rows[0][disease.LOG_DEATHS], 1)
        self.assertEqual(rows[0][8], 30)                                # never met: all 30

    def test_met_at_an_unknown_time_is_not_turned_into_never(self):
        w = world()
        a, b = w.living_bands()[0], w.living_bands()[1]
        d = add(w, a.cell, k=1e9, attack=0.9, cfr=0.0)
        w.dz_last[a.id, d] = -1
        w.dz_last[b.id, d] = -2
        mb = w.members(b.id)
        w.people.band[mb] = a.id
        w.people_changed()
        disease.combine(w, b, a, len(mb))
        self.assertEqual(int(w.dz_last[a.id, d]), -2)

    def test_first_contact_rows_say_how_long_the_source_had_it(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e-9, attack=0.9, cfr=0.0)
        first_year(w)
        for _ in range(3):                                              # it circulates on at the first cell
            w.t += P.TICKS_PER_YEAR
            disease.yearly(w)
        w.dz_active[:, d] = False
        w.dz_active[b.cell, d] = True
        w.dz_last[:, d] = -1                                            # the neighbours had never met it
        w.dz_last[b.id, d] = int(w.year)
        w.dz_imm[:, d] = 0.0
        old = P.DZ_SPREAD
        P.DZ_SPREAD = 1e9
        try:
            w.t += P.TICKS_PER_YEAR
            disease.yearly(w)
        finally:
            P.DZ_SPREAD = old
        rows = [r for r in w.dz_log if r[1] == d and r[3] == 2 and r[0] == w.year]
        self.assertTrue(rows)
        self.assertTrue(all(r[5] >= 3 for r in rows))                  # years it had circulated at the source



class Review031(unittest.TestCase):
    """Codex review 031 (fixed before the comprehensive review, Ben's decision of 20 November 2026)."""

    def test_a_return_after_dying_out_starts_a_new_spell(self):
        w = world()
        b = w.living_bands()[0]
        d = add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)
        first_year(w)
        w.dz_active[:, d] = False
        w.dz_active[b.cell, d] = True
        w.t += 40 * P.TICKS_PER_YEAR
        w.dz_since[b.cell, d] = int(w.year) - 30                        # an old spell
        w.diseases[d]["k"] = 1e-30                                      # it fails to keep going
        old = P.DZ_RESPILL_WILD, P.DZ_SPREAD
        P.DZ_RESPILL_WILD, P.DZ_SPREAD = 1.0, 0.0                       # and comes back from its animals
        try:
            w.diseases[d]["k"] = 1e30
            disease.yearly(w)
        finally:
            P.DZ_RESPILL_WILD, P.DZ_SPREAD = old
        self.assertTrue(w.dz_active[b.cell, d])
        self.assertEqual(int(w.dz_since[b.cell, d]), int(w.year))      # Codex's case: not the old start

    def test_older_named_counts_are_set_aside(self):
        from origins import persist
        w = world()
        b = w.living_bands()[0]
        add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)
        w.counts["ob_contact_infections"] = 5
        w2 = persist.from_bytes(_unmarked(persist.to_bytes(w)), w.planet)   # a save from before review 031
        self.assertNotIn("ob_contact_infections", w2.counts)
        self.assertEqual(w2.counts["unattributed_ob_contact_infections"], 5)



def _unmarked(data: bytes) -> bytes:
    """A save as written before review 034: without the mark that named diseases count under their own keys."""
    import io, json, zipfile
    src, out = zipfile.ZipFile(io.BytesIO(data)), io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in src.namelist():
            raw = src.read(name)
            if name == "meta.json":
                meta = json.loads(raw)
                meta.pop("dz_counts_split", None)
                raw = json.dumps(meta).encode()
            z.writestr(name, raw)
    return out.getvalue()


if __name__ == "__main__":
    unittest.main()


class Review037(unittest.TestCase):
    """Codex review 037: the 64th disease ended emergence (finding 4); the per-cell log grew as Python lists in the
    save's metadata (finding 2)."""

    def _full(self, gone_since):
        w = world()
        b = w.living_bands()[0]
        for _ in range(disease.ND_CAP):
            add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)
        w.dz_active[:] = False
        for dz in w.diseases:
            dz["year"] = 0
        disease._last_rows(w)
        w.dz_last[:] = gone_since
        w.t = (gone_since + P.DZ_RETIRE_YEARS + 10) * P.TICKS_PER_YEAR
        return w, b

    def _wild(self, w):
        pop = np.zeros(w.planet.n)
        pop[w.living_bands()[0].cell] = 1e12                         # sure to draw a wild start
        active = np.zeros((w.planet.n, disease.ND_CAP), dtype=bool)
        disease._emerge(w, w.rng["disease"], [], np.array([], int), np.array([], int), np.zeros(0), pop, active, {},
                        herders={})

    def test_finding4_a_long_gone_disease_frees_its_slot(self):
        w, b = self._full(gone_since=100)
        w.dz_last[:, 5] = 50                                          # the longest gone
        self._wild(w)
        self.assertEqual(len(w.diseases), disease.ND_CAP)
        self.assertEqual(w.counts.get("dz_retired"), 1)
        self.assertEqual(w.diseases_retired[0]["id"], 5)
        self.assertEqual(int(w.diseases[5]["year"]), int(w.year))     # a new disease in slot 5
        self.assertNotEqual(w.diseases[5]["uid"], w.diseases_retired[0].get("uid", 5))
        self.assertTrue(any(e["kind"] == "disease_retired" for e in w.events))

    def test_finding4_starts_are_counted_when_every_slot_is_recent(self):
        w, b = self._full(gone_since=100)
        w.dz_last[:] = int(w.year) - 5                               # all circulated recently
        self._wild(w)
        self.assertEqual(w.counts.get("dz_blocked_starts"), 1)
        self.assertFalse(w.counts.get("dz_retired"))

    def test_finding2_the_log_is_an_array_saved_beside_the_others(self):
        import io
        import json
        import zipfile
        from origins import persist
        w = world()
        b = w.living_bands()[0]
        add(w, b.cell, k=1e9, attack=0.9, cfr=0.0)
        for i in range(1000):
            w.dz_log.append([i, 0, b.cell, 3, -1, -1, 200, .45, 60, 1, 70, 1, 70, 0, 130, 790, 2])
        data = persist.to_bytes(w)
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertNotIn("dz_log", json.dumps(json.loads(z.read("meta.json")))[:10 ** 7].split('"diseases"')[0])
        w2 = persist.from_bytes(data, w.planet)
        self.assertEqual(len(w2.dz_log), len(w.dz_log))
        self.assertEqual(list(w2.dz_log[999]), list(w.dz_log[999]))
        self.assertEqual(persist.digest(w2), persist.digest(w))
        d0 = persist.digest(w)
        w.dz_log.append([2000, 0, b.cell, 3, -1, -1, 200, .45, 60, 1, 70, 1, 70, 0, 130, 790, 2])
        self.assertNotEqual(persist.digest(w), d0)                    # the log is in the digest
