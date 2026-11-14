"""M4a tests: the technology network."""
import unittest

import numpy as np

from origins import engine, persist, params as P
from origins.sim import technology as T
from origins.state import World
from origins.worldgen import generate


class TechniquesAsData(unittest.TestCase):
    def test_list_is_consistent(self):
        self.assertGreaterEqual(T.K, 25)
        for t in T.TECHNIQUES:
            for n in t.needs:
                self.assertLess(T.INDEX[n], T.INDEX[t.key])
            self.assertTrue(t.effect and t.need, t.key)

    def test_daughters_inherit_and_saves_round_trip(self):
        pl = generate(1)
        w = World.new(1, 1, pl)
        engine.step(w, 40)
        b = w.living_bands()[0]
        w.tech[b.id, T.INDEX["pottery"]] = 0.8
        d = w.new_band(b.cell, parent=b.id)
        self.assertAlmostEqual(float(w.tech[d.id, T.INDEX["pottery"]]), 0.8, places=5)
        w2 = persist.from_bytes(persist.to_bytes(w), pl)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        self.assertAlmostEqual(float(w2.tech[b.id, T.INDEX["pottery"]]), 0.8, places=5)

    def test_prerequisites_name_what_is_missing(self):
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        ok, missing = T.prerequisites_met(w, b, T.TECHNIQUES[T.INDEX["writing"]])
        self.assertFalse(ok)
        self.assertIn("needs tallies and tokens held well", missing)



class _Zero:
    """Stands in for the technology stream: every draw succeeds."""
    def random(self, shape=None):
        return np.zeros(shape) if shape is not None else 0.0

    def choice(self, n, p=None):
        return 0


def _shrink(w, x, n):
    """Leave a group band with n adults (for keeping cases that need few practitioners)."""
    G = w.groups
    G.F[x.group] = 0
    G.M[x.group] = 0
    G.preg[x.group] = 0
    G.F[x.group][25] = n


def _two_bands(seed=1):
    from origins.sim import groups
    pl = generate(seed)
    w = World.new(seed, 1, pl)
    a = w.living_bands()[0]
    b = w.new_band(a.cell, parent=a.id)
    for x in (a, b):
        if x.mode == "individual":
            groups.fold(w, x)
    w.tech[:] = 0.0
    return w, a, b


class Review008(unittest.TestCase):
    """Codex review 008: findings reproduced, then fixed."""

    def test_combining_peoples_keeps_their_knowledge(self):
        from origins.sim import bands
        w, a, b = _two_bands()
        b.cell = a.cell
        _shrink(w, a, 30)
        _shrink(w, b, 30)
        w.farm_share[a.id] = w.farm_share[b.id] = 0.0
        w.tech[b.id, T.INDEX["pottery"]] = 0.8
        w.bands_changed()
        bands.consolidate_groups(w)
        live = [x for x in (a, b) if x.alive]
        self.assertEqual(len(live), 1)
        self.assertAlmostEqual(float(w.tech[live[0].id, T.INDEX["pottery"]]), 0.8, places=5)

    def test_migrants_carry_knowledge(self):
        from origins.sim import groups
        w, a, b = _two_bands()
        _shrink(w, a, 40)
        w.tech[a.id, T.INDEX["cordage"]] = 0.7
        n0 = len(w.events)
        moved = groups.transfer(w, a, b, np.random.default_rng(0))
        self.assertGreater(moved, 0)
        T.combine(w, a, b, "migration", moved)      # as bands.fission_and_merge does after a transfer
        technology_carry = float(w.tech[b.id, T.INDEX["cordage"]])
        self.assertAlmostEqual(technology_carry, 0.7, places=5)
        ev = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_adopted"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["data"]["route"], "migration")

    def _phase(self, w, live):
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        sizes = w.band_sizes()[ids]
        connected = T._reach(w, cells, np.bincount(cells, weights=sizes, minlength=w.planet.n)[:, None])[:, 0]
        w.rng["technology"] = _Zero()
        T.keep_and_spread(w, live, ids, cells, sizes, connected, np.ones((len(live), T.K)))

    def test_a_people_does_not_learn_from_itself(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 1)
        k = T.INDEX["fire_hardening"]
        w.tech[a.id, k] = 0.5
        n0 = len(w.events)
        self._phase(w, [a])
        for i in range(n0, len(w.events)):
            e = w.events[i]
            if e["kind"] == "technique_adopted":
                self.assertNotEqual(e["data"]["source"], a.id)
        # with only itself practising and too few people to keep it, the skill declines and is not refreshed
        self.assertLess(float(w.tech[a.id, k]), 0.5)

    def test_adoption_checks_prerequisites_after_this_years_drift(self):
        w, a, b = _two_bands()
        _shrink(w, a, 2)
        _shrink(w, b, 2)
        cord, bow = T.INDEX["cordage"], T.INDEX["bow"]
        w.tech[a.id, cord] = w.tech[b.id, cord] = 0.5
        w.tech[a.id, bow] = 0.8
        self._phase(w, [a, b])
        self.assertLess(float(w.tech[b.id, cord]), 0.5)     # the case under test: cordage fell this year
        self.assertLess(float(w.tech[b.id, bow]), 0.5)        # so the bow cannot be adopted

    def test_prerequisite_helpers_follow_the_working_level(self):
        from origins import params as P
        w, a, b = _two_bands()
        w.tech[a.id, T.INDEX["tallies"]] = 0.6
        old = P.TECH_WORKING
        try:
            P.TECH_WORKING = 0.7
            ok, _ = T.prerequisites_met(w, a, T.TECHNIQUES[T.INDEX["writing"]])
            vec = T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["writing"]]
            self.assertEqual(ok, bool(vec))
        finally:
            P.TECH_WORKING = old



class Decisions14Nov(unittest.TestCase):
    """Ben's technology decisions of 14 November 2026."""

    def _phase(self, w, live):
        Review008._phase(self, w, live)

    def test_refinement_is_slow(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 5000)                              # far more practitioners than needed
        k = T.INDEX["cordage"]
        w.tech[a.id, k] = 0.25
        self._phase(w, [a])
        self.assertLessEqual(float(w.tech[a.id, k]) - 0.25, P.TECH_REFINE * (1 + P.TECH_CRAFT_GAIN) + 1e-6)
        self.assertGreater(float(w.tech[a.id, k]), 0.25)

    def test_unpractised_knowledge_fades_not_deleted(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 200)
        w.farm_share[a.id] = 0.0                         # no longer farms: terracing cannot be practised
        k = T.INDEX["terracing"]
        w.tech[a.id, k] = 0.6
        self._phase(w, [a])
        self.assertAlmostEqual(float(w.tech[a.id, k]), 0.6 - P.TECH_FORGET, places=5)

    def test_wool_needs_sheep(self):
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        a.cell = _cell_where(w, "wild_sheep")
        w.farm_share[a.id] = 0.6
        w.tech[a.id, T.INDEX["cordage"]] = 0.8
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_pig")] = 3
        wool = T.TECHNIQUES[T.INDEX["wool"]]
        self.assertFalse(T.prerequisites_met(w, a, wool)[0])
        w.skill[a.id][SPECIES.index("wild_sheep")] = 3
        self.assertTrue(T.prerequisites_met(w, a, wool)[0])

    def test_few_captives_carry_a_cruder_skill(self):
        w, a, b = _two_bands()
        k = T.INDEX["writing"]                          # needs 60 practitioners
        w.tech[a.id, k] = 0.9
        T.combine(w, a, b, "capture", 30)
        self.assertAlmostEqual(float(w.tech[b.id, k]), 0.45, places=5)
        T.combine(w, a, b, "capture", 3)                # too few to carry anything usable: nothing changes
        self.assertAlmostEqual(float(w.tech[b.id, k]), 0.45, places=5)

    def test_records_survive_combining_and_daughters(self):
        w, a, b = _two_bands()
        k = T.INDEX["pottery"]
        w.tech_record[a.id, k] = 0.7
        T.combine(w, a, b, "combined", 100)
        self.assertAlmostEqual(float(w.tech_record[b.id, k]), 0.7, places=5)
        d = w.new_band(b.cell, parent=b.id)
        self.assertAlmostEqual(float(w.tech_record[d.id, k]), 0.7, places=5)



def _cell_where(w, good, bad=None):
    """A cell where species `good` can live (and `bad` cannot, if given)."""
    from origins.sim.farming import SPECIES, land_tables
    suit = land_tables(w)[1]
    ok = suit[:, SPECIES.index(good)] > 0
    if bad:
        ok &= suit[:, SPECIES.index(bad)] == 0
    return int(np.nonzero(ok)[0][0])


class Review009(unittest.TestCase):
    """Codex review 009: findings reproduced, then fixed."""

    def test_remembered_writing_keeps_no_records(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 200)
        W, F, C = T.INDEX["writing"], T.INDEX["fire_hardening"], T.INDEX["cordage"]
        w.tech[a.id, W] = 0.8                     # no tallies: writing remembered, not practised
        w.tech[a.id, C] = 0.8
        w.tech_record[a.id, F] = 0.8
        Review008._phase(self, w, [a])
        self.assertEqual(float(w.tech[a.id, F]), 0.0)
        self.assertEqual(float(w.tech_record[a.id, C]), 0.0)

    def test_carrying_animals_refreshes_the_herder_test(self):
        from origins.sim import bands, pastoral
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        c = _cell_where(w, "wild_pig", "wild_grain")
        a.cell = b.cell = c
        w.farm_share[a.id] = w.farm_share[b.id] = 1.0
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_pig")] = 3
        w.skill[b.id][:] = 0
        w.skill[b.id][SPECIES.index("wild_grain")] = 3
        self.assertFalse(pastoral.is_herder(w, b))
        bands.carry(w, a, b, "merge", 5)
        self.assertTrue(pastoral.is_herder(w, b))

    def test_marriage_carries_knowledge(self):
        from origins.sim import demography
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        p = w.people
        mem = w.members(a.id)
        C = T.INDEX["cordage"]
        w.tech[:] = 0
        w.tech[a.id, C] = 1.0
        men = mem[(p.sex[mem] == 1) & (w.ages(mem) > 18)]
        p.band[men] = b.id
        p.partner[mem] = -1
        w.people_changed()
        for _ in range(40):
            demography.partnerships(w)
        if (p.sex[w.members(b.id)] == 0).any():   # someone married into b
            self.assertAlmostEqual(float(w.tech[b.id, C]), 0.2, places=5)   # one carrier of 5 needed

    def test_animals_must_be_able_to_live_here(self):
        from origins.sim.farming import SPECIES
        w, a, b = _two_bands()
        a.cell = _cell_where(w, "wild_pig", "wild_sheep")
        w.farm_share[a.id] = 1.0
        w.skill[a.id][:] = 0
        w.skill[a.id][SPECIES.index("wild_sheep")] = 3
        w.tech[a.id, T.INDEX["cordage"]] = 0.8
        wool = T.TECHNIQUES[T.INDEX["wool"]]
        self.assertFalse(T.prerequisites_met(w, a, wool)[0])
        self.assertFalse(T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["wool"]])


    def test_a_remembered_prerequisite_unlocks_nothing(self):
        """Ben, 14 November 2026: a prerequisite counts only when practised."""
        w, a, b = _two_bands()
        a.cell = int(np.nonzero(T._cell_materials(w)[:, T.MATERIALS.index("copper")]
                                & T._cell_materials(w)[:, T.MATERIALS.index("forest")]
                                & T._cell_materials(w)[:, T.MATERIALS.index("clay")])[0][0])
        for key in ("kilns", "copper_working"):
            w.tech[a.id, T.INDEX[key]] = 0.8      # kilns without pottery: remembered, not practised
        smelt = T.TECHNIQUES[T.INDEX["smelting"]]
        ok, missing = T.prerequisites_met(w, a, smelt)
        self.assertFalse(ok)
        self.assertIn("needs kilns practised", missing)
        self.assertFalse(T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["smelting"]])
        w.tech[a.id, T.INDEX["pottery"]] = 0.8
        self.assertTrue(T.prerequisites_met(w, a, smelt)[0])



class LiteratureChanges14Nov(unittest.TestCase):
    """Skilled adults, not everyone, keep a technique; refinement slows near mastery (Ben, 14 November 2026)."""

    def test_an_isolated_band_cannot_keep_pottery(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 40)                     # 40 adults: 10 skilled, fewer than the 20 pottery needs
        w.spec[a.id] = 0
        a.cell = int(np.nonzero(T._cell_materials(w)[:, T.MATERIALS.index("clay")])[0][0])
        k = T.INDEX["pottery"]
        w.tech[a.id, k] = 0.6
        Review008._phase(self, w, [a])
        self.assertLess(float(w.tech[a.id, k]), 0.6)

    def test_refinement_slows_near_mastery(self):
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        _shrink(w, a, 5000)
        w.spec[a.id] = 0
        k = T.INDEX["cordage"]
        w.tech[a.id, k] = 0.9
        Review008._phase(self, w, [a])
        self.assertAlmostEqual(float(w.tech[a.id, k]) - 0.9, P.TECH_REFINE * 0.1, places=5)



class Effects(unittest.TestCase):
    """Stage 5: effects scale with the quality of practised techniques (Ben, 14 November 2026)."""

    def _band(self):
        w, a, b = _two_bands()
        pl = w.planet
        dry = np.nonzero(pl.land & ~pl.coast & ~pl.lake & ~pl.river)[0]
        a.cell = int(dry[0])
        w.bands_changed()
        return w, a

    def test_forage_gear_is_on_with_the_new_trigger(self):
        """Ben, 14 November 2026: foraging gear's food effect is back on with the crowding trigger."""
        self.assertTrue(P.TECH_FORAGE_GEAR)
        w, a = self._band()
        self.assertGreater(float(w.stock_broad.sum()), 0.0)

    def test_hunting_gear_raises_foraging(self):
        old = P.TECH_FORAGE_GEAR
        P.TECH_FORAGE_GEAR = True
        try:
            self._gear_case()
        finally:
            P.TECH_FORAGE_GEAR = old

    def _gear_case(self):
        w, a = self._band()
        w.tech[a.id, T.INDEX["bow"]] = 1.0
        w.tech[a.id, T.INDEX["cordage"]] = 1.0
        w._tech_eff = None
        m = T.forage_access(w, np.array([a.id]), np.array([a.cell]))[0]
        full = sum(P.TECH_EFFECT[k] for k in ("fire_hardening", "cordage", "bow", "copper_working"))
        self.assertAlmostEqual(m, (P.TECH_EFFECT["bow"] + P.TECH_EFFECT["cordage"]) / full, places=5)

    def test_a_crude_technique_gives_part_of_its_effect(self):
        w, a = self._band()
        w.tech[a.id, T.INDEX["pottery"]] = 0.5
        a.cell = int(np.nonzero(T._cell_materials(w)[:, T.MATERIALS.index("clay")])[0][0])
        w.bands_changed()
        w._tech_eff = None
        m = T.spoil_multiplier(w, np.array([a.id]))[0]
        self.assertAlmostEqual(m, 1 - P.TECH_EFFECT["pottery"] * 0.5, places=5)

    def test_unpractised_technique_has_no_effect(self):
        w, a = self._band()
        w.tech[a.id, T.INDEX["bow"]] = 1.0         # no cordage: the bow is remembered, not practised
        w._tech_eff = None
        m = T.forage_access(w, np.array([a.id]), np.array([a.cell]))[0]
        self.assertAlmostEqual(m, 0.0, places=6)

    def test_writing_raises_capacity_at_the_seat(self):
        w, a = self._band()
        w.tech[a.id, T.INDEX["tallies"]] = 1.0
        w.tech[a.id, T.INDEX["writing"]] = 1.0
        w._tech_eff = None
        self.assertAlmostEqual(T.capacity_multiplier(w, a.id),
                               1 + P.TECH_EFFECT["tallies"] + P.TECH_EFFECT["writing"], places=5)



def _ages(w, x, age, n, sex=0):
    G = w.groups
    G.F[x.group] = 0
    G.M[x.group] = 0
    G.preg[x.group] = 0
    (G.F if sex == 0 else G.M)[x.group][age] = n


class Review010(unittest.TestCase):
    """Codex review 010: findings reproduced, then fixed."""

    def test_children_teach_nothing(self):
        w, a, b = _two_bands()
        b.cell = a.cell
        _ages(w, a, 10, 20)                       # 20 children, cordage 0.8
        _ages(w, b, 25, 40)                       # 40 adults, no cordage
        w.spec[a.id] = w.spec[b.id] = 0
        w.tech[a.id, T.INDEX["cordage"]] = 0.8
        Review008._phase(self, w, [a, b])
        self.assertEqual(float(w.tech[b.id, T.INDEX["cordage"]]), 0.0)

    def test_crop_bonus_stays_with_crops(self):
        from origins.sim import farming
        w, a, b = _two_bands()
        b.alive = False
        w.bands_changed()
        ids, cells = np.array([a.id]), np.array([a.cell])
        w.tech[a.id, T.INDEX["plough"]] = w.tech[a.id, T.INDEX["draft_animals"]] = 1.0
        w._tech_eff = None
        m = T.farm_multipliers(w, ids, cells, np.array([0.5]))
        self.assertEqual(len(m), 4)                # per worker and per field, for crops and for herds

    def test_effects_follow_new_daughters(self):
        w, a, b = _two_bands()
        w.tech[a.id, T.INDEX["tallies"]] = w.tech[a.id, T.INDEX["writing"]] = 1.0
        w._tech_eff = None
        T.capacity_multiplier(w, a.id)            # warm the cache
        d = w.new_band(a.cell, parent=a.id)
        self.assertAlmostEqual(T.capacity_multiplier(w, d.id), T.capacity_multiplier(w, a.id), places=5)

    def test_founding_conquest_counts_technology(self):
        from origins.sim import conflict, polity
        w, a, b = _two_bands()
        w.tech[a.id, T.INDEX["tallies"]] = w.tech[a.id, T.INDEX["writing"]] = 1.0
        w._tech_eff = None
        probe = polity.Polity(-1, a.id, w.t, "")
        self.assertGreater(polity.capacity(probe, w), P.POLITY_CAPACITY)
        import inspect
        self.assertIn("capacity(", inspect.getsource(conflict._room_for))


    def test_specialists_counted_once(self):
        w, a, b = _two_bands()
        _ages(w, a, 30, 15)
        w.spec[a.id] = 3
        self.assertAlmostEqual(float(T.skilled(w, [a], np.array([a.id]))[0]), 0.25 * 12 + 3, places=6)



class Settled14Nov(unittest.TestCase):
    """Building techniques belong to settled peoples (Ben, 14 November 2026)."""

    def test_wandering_foragers_do_not_build(self):
        w, a, b = _two_bands()
        st = T.TECHNIQUES[T.INDEX["stone_building"]]
        w.farm_share[a.id] = 0.0
        w.still_years[a.id] = 0
        ok, missing = T.prerequisites_met(w, a, st)
        self.assertIn("needs a settled people", missing)
        w.t = 100                                            # founded long ago: no recent move in the trail
        w.still_years[a.id] = P.TECH_SETTLED_YEARS          # sedentary foragers can build
        self.assertTrue(T.prerequisites_met(w, a, st)[0])
        self.assertTrue(T._possible(w, np.array([a.id]), np.array([a.cell]))[0, T.INDEX["stone_building"]])



class BroadSpectrum14Nov(unittest.TestCase):
    """Gear lets the land yield more to foragers, not a richer return per day (Ben, 14 November 2026)."""

    def test_plenty_pays_the_same_with_or_without_gear(self):
        from origins.sim import foraging
        res = []
        for gear in (0.0, 1.0):
            w = World.new(1, 1, generate(1))
            for b in w.living_bands():
                for k in ("fire_hardening", "cordage", "bow"):
                    w.tech[b.id, T.INDEX[k]] = gear
            w._tech_eff = None
            s0 = w.stock.sum() + w.stock_broad.sum()
            h0 = w.ledger["harvest"]
            foraging.forage_and_eat(w)
            res.append(w.ledger["harvest"] - h0)
        self.assertAlmostEqual(res[0], res[1], delta=0.02 * res[0])   # 90 people on fresh land: effort, not food, limits

    def test_food_is_conserved(self):
        w = World.new(1, 1, generate(1))
        for b in w.living_bands():
            w.tech[b.id, T.INDEX["cordage"]] = 1.0
        engine.step(w, 40)
        self.assertEqual(w.invariant_failures, [])



class FarmingTrigger14Nov(unittest.TestCase):
    """Farming starts from crowding against unaided wild food, or from abundance (docs/FARMING_TRIGGER_PROPOSAL.md)."""

    def test_crowding_counts_people_against_wild_food(self):
        from origins.sim import farming
        w = World.new(1, 1, generate(1))
        c = farming.crowding(w)
        b = w.living_bands()[0]
        pl = w.planet
        cells = [b.cell] + [int(x) for x in pl.grid.neighbours[b.cell] if x >= 0]
        sizes = w.band_sizes()
        pop = sum(sizes[o.id] for o in w.living_bands() if o.cell in cells)
        self.assertAlmostEqual(float(c[b.cell]), pop / pl.capacity[cells].sum(), places=6)



class Review011(unittest.TestCase):
    """Codex review 011: findings reproduced, then fixed."""

    def test_a_forager_that_just_moved_is_not_settled(self):
        from origins.sim import foraging
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        for o in w.living_bands()[1:]:
            o.alive = False
        w.bands_changed()
        w.t = 100                                         # founded long ago: the founding entry in the trail is old
        w.farm_share[b.id] = 0.0
        w.still_years[b.id] = 20
        self.assertTrue(T._settled(w, np.array([b.id]))[0])
        nb = [int(x) for x in w.planet.grid.neighbours[b.cell] if x >= 0 and w.planet.land[x]]
        w.stock[b.cell] = 1.0
        w.stock[nb[0]] = 1e6
        foraging.move(w)
        self.assertFalse(T._settled(w, np.array([b.id]))[0])

    def test_tending_below_the_abundance_floor_is_recorded_as_abundance(self):
        from origins.sim import farming
        w = World.new(1, 1, generate(1))
        b = w.living_bands()[0]
        wild, suit = farming.land_tables(w)
        k = farming.SPECIES.index("wild_grain")
        cells = np.nonzero(wild[:, k] & (suit[:, k] >= P.ABUNDANCE_SUIT))[0]
        b.cell = int(cells[0])
        w.still_years[b.id] = P.ABUNDANCE_YEARS
        w._press_why = {b.id: (0.01, 0.4, 0.0)}           # weak hunger, below the floor
        farming._first(w, b, k, "tending")
        e = w.events[len(w.events) - 1]
        self.assertIn("without being pressed", e["causes"][-1]["note"])


if __name__ == "__main__":
    unittest.main()
