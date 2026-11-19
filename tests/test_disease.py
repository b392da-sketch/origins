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


if __name__ == "__main__":
    unittest.main()
