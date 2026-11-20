"""M4a tests: place names, and the writing refinements (Ben, 20 November 2026)."""
import unittest

import numpy as np

from origins import explain, persist, params as P
from origins.sim import places, technology as T
from origins.state import World
from origins.worldgen import generate


class _Draw:
    """Stands in for the places stream: random() gives `u`; integers give 0."""
    def __init__(self, u=0.0):
        self.u = u

    def random(self, shape=None):
        return np.full(shape, self.u) if shape is not None else self.u

    def integers(self, lo, hi=None):
        return 0


def _river_world():
    pl = generate(1)
    w = World.new(1, 1, pl)
    feats, _near = places.features(pl)
    river = max((f for f in feats if f[0] == "river"), key=lambda f: len(f[4]))
    founders = w.living_bands()
    for o in founders:                                  # everyone moves to the river's mouth
        o.cell = river[4][0]
    b = founders[0]
    w.bands_changed()
    places.init(w)
    return w, b, river


class Features(unittest.TestCase):
    def test_every_river_cell_in_one_stream_that_follows_the_larger_branch(self):
        pl = generate(1)
        feats, near = places.features(pl)
        rivers = [f for f in feats if f[0] == "river"]
        cells = [c for f in rivers for c in f[4]]
        self.assertEqual(len(cells), len(set(cells)))
        self.assertEqual(set(cells), set(np.nonzero(pl.river)[0].tolist()))
        for f in rivers:                                # the stream's head (mouth) has the stream's largest flow
            self.assertEqual(max(f[4], key=lambda c: pl.flow[c]), f[1])
            self.assertTrue(0.0 <= f[3] <= 1.0)
        self.assertIs(places.features(pl), places.features(pl))   # cached, no draws

    def test_kinds_present(self):
        feats, _ = places.features(generate(1))
        kinds = {f[0] for f in feats}
        for k in ("river", "coast"):
            self.assertIn(k, kinds)


class Keeping(unittest.TestCase):
    def test_keep_chance_follows_size_remoteness_newcomers_and_conquest(self):
        base = places.keep_chance(0.5, 0.5, 0.5, False)
        self.assertGreater(places.keep_chance(0.9, 0.5, 0.5, False), base)
        self.assertGreater(places.keep_chance(0.5, 0.9, 0.5, False), base)
        self.assertLess(places.keep_chance(0.5, 0.5, 0.9, False), base)
        self.assertLess(places.keep_chance(0.5, 0.5, 0.5, True), base)


class Naming(unittest.TestCase):
    def _name(self, w, u=0.0):
        real = w.rng["places"]
        w.rng["places"] = _Draw(u)
        try:
            places.yearly(w)
        finally:
            w.rng["places"] = real

    def test_a_people_by_a_river_names_it_with_a_cause(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        ps = [p for p in w.places if p["kind"] == "river" and p["key"] == river[1]]
        self.assertEqual(len(ps), 1)
        layer = ps[0]["layers"][0]
        self.assertEqual((layer[1], layer[3]), (b.language, "new"))
        ev = [i for i, e in enumerate(w.events) if e["kind"] == "place_named"]
        self.assertTrue(ev)
        self.assertTrue(all(explain.resolvable(w, {"event": i}) for i in ev))
        rv = [i for i in ev if w.events[i]["data"]["feature"] == "river"]
        self.assertIn("named the river", w.events[rv[0]]["causes"][-1]["note"])
        self.assertEqual(layer[6], rv[0])                 # the layer knows its event

    def test_a_named_place_is_not_renamed_by_the_same_people_or_its_daughters(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        n = sum(len(p["layers"]) for p in w.places)
        from origins.sim import language
        lang = w.languages[b.language]
        language.split(w, lang, [{b.cell}], "test")    # the band now speaks a daughter language
        w.t = 80
        self._name(w)
        self.assertEqual(sum(len(p["layers"]) for p in w.places), n)
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        self.assertIsNotNone(places.name_in(w, p, b.language))

    def test_newcomers_keep_the_heard_name_then_reshape_it(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        heard = places.current(w, p["layers"][0])
        # a second people of an unrelated language arrives on the same cell
        from origins.sim.language import Language
        new_id = w.next_lang
        w.next_lang += 1
        other = Language(new_id, -1, w.t, lexicon={m: [list(e[0]), e[1], e[2]]
                                                    for m, e in w.languages[b.language].lexicon.items()})
        w.languages[new_id] = other
        c = w.living_bands()[1]
        c.language = new_id
        for o in w.living_bands()[2:]:
            o.language = new_id
        b_lang = b.language
        w.bands_changed()
        w.t = 80
        self._name(w, u=0.0)                            # every chance taken: named, and kept
        layer = places.name_in(w, p, new_id)
        self.assertEqual(layer[3], "kept")
        self.assertEqual(tuple(layer[2]), tuple(heard))
        self.assertEqual(layer[4], b.language)
        # a later sound change of the newcomers reshapes the kept name; one from before it was kept does not
        from origins.lang import changes as CH
        form = tuple(layer[2])
        rid = next(r for r in CH.RULES if CH.apply(r, form) != form)
        other.history.append([layer[0], "rule", rid])  # same tick as the naming: already in the heard form
        self.assertEqual(places.current(w, layer), form)
        other.history.append([layer[0] + 1, "rule", rid])
        self.assertEqual(places.current(w, layer), CH.apply(rid, form))

    def test_newcomers_who_do_not_keep_give_their_own_name(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        from origins.sim.language import Language
        new_id = w.next_lang
        w.next_lang += 1
        w.languages[new_id] = Language(new_id, -1, w.t, lexicon={m: [list(e[0]), e[1], e[2]]
                                                                for m, e in w.languages[b.language].lexicon.items()})
        c = w.living_bands()[1]
        c.language = new_id
        for o in w.living_bands()[2:]:
            o.language = new_id
        b_lang = b.language
        w.bands_changed()
        w.t = 80
        old = P.PLACE_KEEP_BASE, P.PLACE_KEEP_SIZE, P.PLACE_KEEP_REMOTE
        P.PLACE_KEEP_BASE = P.PLACE_KEEP_SIZE = P.PLACE_KEEP_REMOTE = 0.0
        try:
            self._name(w)
        finally:
            P.PLACE_KEEP_BASE, P.PLACE_KEEP_SIZE, P.PLACE_KEEP_REMOTE = old
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        self.assertEqual(places.name_in(w, p, new_id)[3], "replaced")
        self.assertEqual(len(places.history(w, w.places.index(p))), 2)

    def test_places_round_trip_in_saves_and_digest(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        self.assertEqual(w2.places, w.places)
        d = persist.digest(w)
        w.places[0]["layers"][0][3] = "kept"
        self.assertNotEqual(persist.digest(w), d)


class Writing(unittest.TestCase):
    def _two(self):
        from origins.sim import groups
        pl = generate(1)
        w = World.new(1, 1, pl)
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        for x in (a, b):
            if x.mode == "individual":
                groups.fold(w, x)
        w.tech[:] = 0.0
        return w, a, b

    def test_writing_is_practised_by_scribes_only(self):
        w, a, b = self._two()
        T._scribes(w)[a.id] = 3.0
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        S = T.skilled_by_technique(w, live, ids)
        i = list(ids).index(a.id)
        self.assertEqual(S[i, T.WRITING], 3.0)
        self.assertAlmostEqual(S[i, T.INDEX["pottery"]], float(T.skilled(w, live, ids)[i]))
        self.assertEqual(T.keep_needed()[T.WRITING], P.TECH_SCRIBES_KEEP)
        self.assertEqual(T.keep_needed()[T.INDEX["pottery"]], T.TECHNIQUES[T.INDEX["pottery"]].keep)

    def test_a_people_without_scribes_cannot_write(self):
        w, a, b = self._two()
        w.tech[a.id, T.INDEX["tallies"]] = 1.0
        T._scribes(w)[a.id] = 0.5
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        self.assertFalse(T._possible(w, ids, cells)[list(ids).index(a.id), T.WRITING])
        ok, missing = T.prerequisites_met(w, a, T.TECHNIQUES[T.WRITING])
        self.assertFalse(ok)
        self.assertTrue(any("scribes" in m for m in missing))
        T._scribes(w)[a.id] = 2.0
        self.assertTrue(T._possible(w, ids, cells)[list(ids).index(a.id), T.WRITING])

    def test_scribes_follow_specialists_over_a_generation(self):
        from origins.sim.polity import Polity
        w, a, b = self._two()
        T._scribes(w)[:] = 0.0
        w.spec[b.id] = 50.0                              # specialists at a small polity's seat: no scribes
        w.polities = {0: Polity(0, a.id, 0, "test", tier=P.TECH_SCRIBE_TIER),
                      1: Polity(1, b.id, 0, "small", tier=P.TECH_SCRIBE_TIER - 1)}   # too small to keep scribes
        w.spec[a.id] = 50.0
        T.yearly(w)
        self.assertAlmostEqual(float(T._scribes(w)[a.id]), 50.0 / P.TECH_SCRIBE_YEARS, places=6)
        self.assertEqual(float(T._scribes(w)[b.id]), 0.0)
        w.spec[b.id] = 0.0
        w.spec[a.id] = 0.0                               # one year without specialists: most scribes remain
        before = float(T._scribes(w)[a.id])
        T.yearly(w)
        self.assertAlmostEqual(float(T._scribes(w)[a.id]), before * (1 - 1 / P.TECH_SCRIBE_YEARS), places=6)

    def test_scribes_join_with_their_people_and_daughters_start_without(self):
        w, a, b = self._two()
        sc = T._scribes(w)
        sc[a.id], sc[b.id] = 10.0, 5.0
        T.combine(w, b, a, "merge")
        self.assertEqual((float(sc[a.id]), float(sc[b.id])), (15.0, 0.0))
        w.tech[a.id, T.WRITING] = 0.7
        d = w.new_band(a.cell, parent=a.id)
        self.assertEqual(float(T._scribes(w)[d.id]), 0.0)
        self.assertEqual(float(w.tech[d.id, T.WRITING]), 0.0)          # writing stays with the scribes
        T.combine(w, a, d, "migration", 1000)                        # migrants do not carry it either
        self.assertEqual(float(w.tech[d.id, T.WRITING]), 0.0)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        self.assertEqual(float(T._scribes(w2)[a.id]), 15.0)
        old = persist.digest(w)
        T._scribes(w)[a.id] = 14.0
        self.assertNotEqual(persist.digest(w), old)

    def test_knowing_others_write_raises_the_chance_and_is_recorded(self):
        w, a, b = self._two()
        w.tech[a.id, T.INDEX["tallies"]] = 1.0
        w.tech[a.id, T.WRITING] = 1.0
        T._scribes(w)[:] = 0.0
        T._scribes(w)[a.id] = 5.0
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        ok = T._possible(w, ids, cells)
        self.assertTrue(ok[list(ids).index(a.id), T.WRITING])
        seen = T._stimulus(w, live, ids, cells)
        ib, ia = list(ids).index(b.id), list(ids).index(a.id)
        if ok[ia, T.WRITING]:
            self.assertEqual(int(seen[ib, T.WRITING]), a.id)
            self.assertEqual(int(seen[ia, T.WRITING]), -1)      # a people is not stimulated by itself
        else:
            self.assertEqual(int(seen[ib, T.WRITING]), -1)      # writing that cannot be practised here is not seen

    def test_tallies_with_record_keepers_give_part_of_writings_capacity(self):
        w, a, b = self._two()
        w.tech[a.id, T.INDEX["tallies"]] = 1.0
        w.spec[a.id] = 0.0
        no_keepers = T.capacity_multiplier(w, a.id)
        w.spec[a.id] = P.TECH_RECORD_KEEPERS
        q = T.band_quality(w, a.id, "tallies")
        kept = T.capacity_multiplier(w, a.id)
        self.assertAlmostEqual(kept - no_keepers, T._e("writing") * P.TECH_RECORDS_SHARE * q, places=6)
        w.tech[a.id, T.WRITING] = 1.0                    # writing and kept tallies are not added
        T.refresh(w)
        qw = T.band_quality(w, a.id, "writing")
        self.assertAlmostEqual(T.capacity_multiplier(w, a.id),
                               1.0 + T._e("tallies") * q + T._e("writing") * max(qw, P.TECH_RECORDS_SHARE * q), places=6)


if __name__ == "__main__":
    unittest.main()


class Review032(unittest.TestCase):
    """Codex review 032: findings reproduced, then fixed."""

    def _name(self, w, u=0.0):
        real = w.rng["places"]
        w.rng["places"] = _Draw(u)
        try:
            places.yearly(w)
        finally:
            w.rng["places"] = real

    def _second_people(self, w, b, bands):
        from origins.sim.language import Language
        new_id = w.next_lang
        w.next_lang += 1
        w.languages[new_id] = Language(new_id, -1, w.t, lexicon={m: [list(e[0]), e[1], e[2]]
                                                                for m, e in w.languages[b.language].lexicon.items()})
        for o in bands:
            o.language = new_id
        w.bands_changed()
        return new_id

    def test_a_rule_on_the_naming_tick_is_in_the_name(self):
        from origins.sim import language
        w = World.new(1, 1, generate(1))
        lid = w.living_bands()[0].language
        language._apply_rule(w.languages[lid], "laryngeal_loss", 42)
        self.assertNotIn("h2", places.generic(w, lid, "river", 42))
        self.assertIn("h2", places.generic(w, lid, "river", 41))

    def test_conquest_is_seen_in_any_band_of_the_holders(self):
        from origins.sim.polity import Polity
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        bands = w.living_bands()
        self.assertGreaterEqual(len(bands), 3)
        holder2, newcomer = bands[1], bands[2]
        nid = self._second_people(w, b, bands[2:])
        from origins.sim import conflict, polity
        conflict.ensure(w, max(x.id for x in bands), -1)
        polity.ensure(w, max(x.id for x in bands), -1)
        pid = 999
        w.polities[pid] = Polity(pid, newcomer.id, 0, "conquerors")
        w.polity_of[holder2.id] = pid
        w.conquered_at[holder2.id] = 79                  # the second holder band, not the first, was conquered
        seen = []
        real = places.keep_chance
        places.keep_chance = lambda size, remote, newcomers, conquest: (seen.append(conquest), real(size, remote, newcomers, conquest))[1]
        try:
            w.t = 80
            self._name(w)
        finally:
            places.keep_chance = real
        self.assertIn(True, seen)

    def test_conquered_people_may_take_their_conquerors_name(self):
        from origins.sim.polity import Polity
        from origins.sim import conflict, polity
        w, b, river = _river_world()
        bands = w.living_bands()
        conq = bands[1]
        nid = self._second_people(w, b, [conq])
        w.t = 40
        self._name(w)                                    # both peoples name the river, each in its own speech
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        self.assertIsNotNone(places.name_in(w, p, nid))
        conflict.ensure(w, max(x.id for x in bands), -1)
        polity.ensure(w, max(x.id for x in bands), -1)
        w.polities[999] = Polity(999, conq.id, 0, "conquerors")
        w.polity_of[b.id] = 999
        w.conquered_at[b.id] = 75
        w.t = 75
        war = w.event("war", cell=b.cell, band=conq.id, target=b.id)
        w.event("conquest", cell=b.cell, band=b.id, causes=[{"event": war}], polity=999, settlements=1,
                whole_polity=False, moved=[b.id])
        w.t = 80
        self._name(w)
        layer = places.name_in(w, p, b.language)
        self.assertEqual(layer[3], "imposed")
        self.assertEqual(layer[4], nid)
        self.assertEqual(tuple(layer[2]), tuple(places.current(w, places.name_in(w, p, nid), nid)))
        self.assertTrue(explain.resolvable(w, {"event": layer[6]}))

    def test_a_kept_name_cites_the_naming_it_was_heard_from(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        first = p["layers"][0][6]
        nid = self._second_people(w, b, w.living_bands()[1:])
        w.t = 80
        self._name(w)
        layer = places.name_in(w, p, nid)
        self.assertEqual(layer[3], "kept")
        self.assertIn({"event": first}, w.events[layer[6]]["causes"])

    def test_regions_are_named_as_the_land_of_a_people_or_described(self):
        w, b, river = _river_world()
        w.t = 40
        self._name(w)
        feats, near = places.features(w.planet)
        self.assertTrue(any(f[0] == "region" for f in feats))
        regs = [p for p in w.places if p["kind"] == "region"]
        self.assertTrue(regs)
        self.assertIn("land", w.events[regs[0]["layers"][0][6]]["causes"][-1]["note"])

    def test_the_stimulus_is_named_only_where_it_was_needed(self):
        from origins.sim import groups
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        for x in (a, b):
            if x.mode == "individual":
                groups.fold(w, x)
        w.tech[:] = 0.0
        for x in (a, b):
            w.tech[x.id, T.INDEX["tallies"]] = 1.0
            T._scribes(w)[x.id] = 5.0
        w.tech[a.id, T.WRITING] = 1.0
        w.spec[:] = 0.0

        class Zero:
            def random(self, shape=None):
                return np.zeros(shape) if shape is not None else 0.0

            def choice(self, n, p=None):
                return 0
        real = w.rng["technology"]
        w.rng["technology"] = Zero()
        try:
            T.yearly(w)
        finally:
            w.rng["technology"] = real
        ev = [e for e in w.events if e["kind"] == "invention" and e["data"].get("technique") == "writing"]
        self.assertTrue(ev)
        self.assertEqual(ev[0]["data"]["stimulus"], a.id)
        self.assertFalse(ev[0]["data"]["stimulus_needed"])        # a zero draw succeeds without the stimulus

    def test_the_writing_log_tells_practice_from_memory(self):
        from origins.sim import groups
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        if a.mode == "individual":
            groups.fold(w, a)
        w.tech[:] = 0.0
        w.tech[a.id, T.INDEX["tallies"]] = 1.0
        w.tech[a.id, T.WRITING] = 0.8
        live = w.living_bands()
        ids = np.array([x.id for x in live])
        cells = np.array([x.cell for x in live])
        T._scribes(w)[:] = 0.0
        T._log_writing(w, live, ids, cells)
        T._scribes(w)[a.id] = 5.0
        T._log_writing(w, live, ids, cells)
        rows = [r for r in w.tech_writing_log if r[1] == a.id]
        self.assertEqual([r[7] for r in rows], [False, True])
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w), persist.digest(w2))


class Review033(unittest.TestCase):
    """Codex review 033: findings reproduced, then fixed."""

    def _name(self, w, u=0.0):
        real = w.rng["places"]
        w.rng["places"] = _Draw(u)
        try:
            places.yearly(w)
        finally:
            w.rng["places"] = real

    def _conquered_world(self, n_conquered=2):
        """A river with one conquering people (one band) and n_conquered bands of another, each naming it."""
        from origins.sim.language import Language
        from origins.sim.polity import Polity
        from origins.sim import conflict, polity
        w, b, river = _river_world()
        bands = w.living_bands()
        self.assertGreaterEqual(len(bands), n_conquered + 1)
        conq, victims = bands[0], bands[1:1 + n_conquered]
        nid = w.next_lang
        w.next_lang += 1
        w.languages[nid] = Language(nid, -1, w.t, lexicon={m: [list(e[0]), e[1], e[2]]
                                                          for m, e in w.languages[b.language].lexicon.items()})
        conq.language = nid
        from origins.sim import language
        language._apply_rule(w.languages[nid], "laryngeal_loss", 1)    # so the two peoples' words differ
        w.bands_changed()
        w.t = 40
        old = P.PLACE_KEEP_BASE, P.PLACE_KEEP_SIZE, P.PLACE_KEEP_REMOTE
        P.PLACE_KEEP_BASE = P.PLACE_KEEP_SIZE = P.PLACE_KEEP_REMOTE = 0.0   # each people gives its own name
        try:
            self._name(w)
        finally:
            P.PLACE_KEEP_BASE, P.PLACE_KEEP_SIZE, P.PLACE_KEEP_REMOTE = old
        conflict.ensure(w, max(x.id for x in bands), -1)
        polity.ensure(w, max(x.id for x in bands), -1)
        w.polities[999] = Polity(999, conq.id, 0, "conquerors")
        return w, conq, victims, river

    def test_one_conquest_of_two_bands_imposes_the_name_once(self):
        w, conq, victims, river = self._conquered_world(2)
        w.t = 75
        war = w.event("war", cell=conq.cell, band=conq.id, target=victims[0].id)
        for v in victims:
            w.polity_of[v.id] = 999
            w.conquered_at[v.id] = 75
        w.event("conquest", cell=victims[0].cell, band=victims[0].id, causes=[{"event": war}], polity=999,
                settlements=2, whole_polity=True, moved=[v.id for v in victims])
        w.t = 80
        self._name(w)
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        self.assertEqual(sum(1 for l in p["layers"] if l[3] == "imposed"), 1)

    def test_an_imposed_name_cites_its_own_conquest(self):
        w, conq, victims, river = self._conquered_world(1)
        v = victims[0]
        w.t = 75
        war = w.event("war", cell=conq.cell, band=conq.id, target=v.id)
        mine = w.event("conquest", cell=v.cell, band=v.id, causes=[{"event": war}], polity=999, settlements=1,
                       whole_polity=False, moved=[v.id])
        other = w.event("conquest", cell=v.cell, band=conq.id, causes=[{"event": war}], polity=999, settlements=1,
                        whole_polity=False, moved=[conq.id])          # same polity and tick, another target
        w.polity_of[v.id] = 999
        w.conquered_at[v.id] = 75
        w.t = 80
        self._name(w)
        p = next(p for p in w.places if p["kind"] == "river" and p["key"] == river[1])
        layer = next(l for l in p["layers"] if l[3] == "imposed")
        cites = [c.get("event") for c in w.events[layer[6]]["causes"]]
        self.assertIn(mine, cites)
        self.assertNotIn(other, cites)

    def test_the_gate_record_keeps_every_complex_chiefdom_and_writer(self):
        from gates import g3
        w = World.new(1, 1, generate(1))
        pl = [[0, pid, 3, 2, 0, 0, 0, 0, 2 if pid == 7 else 0, 0] for pid in range(1601)]
        w.tech_writing_log = [[0, 1, 1600, 0, True, 5.0, 0.6, True]]
        keep = g3.kept_polities(w, pl, np.random.default_rng(0))
        self.assertIn(7, keep)                            # a complex chiefdom of three settlements
        self.assertIn(1600, keep)                         # a polity with a writer

    def test_a_cell_panel_names_a_place_in_the_cells_own_speech(self):
        from origins import server
        w, conq, victims, river = self._conquered_world(1)
        v = victims[0]
        here = river[4][0]
        other = next(c for c in river[4] if c != here)
        conq.cell = here
        for o in w.living_bands():
            if o.id != conq.id:
                o.cell = other                           # the other people, more of them, elsewhere on the river
        w.bands_changed()
        p_i = next(i for i, p in enumerate(w.places) if p["kind"] == "river" and p["key"] == river[1])
        p = w.places[p_i]
        mine = places.show(places.current(w, places.name_in(w, p, conq.language), conq.language))
        got = next(x for x in server.cell_places(w, here) if x["id"] == p_i)
        self.assertEqual(got["name"], mine)

    def test_a_stimulus_that_was_not_needed_is_not_a_cause(self):
        from origins.sim import groups
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        for x in (a, b):
            if x.mode == "individual":
                groups.fold(w, x)
        w.tech[:] = 0.0
        for x in (a, b):
            w.tech[x.id, T.INDEX["tallies"]] = 1.0
            T._scribes(w)[x.id] = 5.0
        w.tech[a.id, T.WRITING] = 1.0
        w.spec[:] = 0.0

        class Zero:
            def random(self, shape=None):
                return np.zeros(shape) if shape is not None else 0.0

            def choice(self, n, p=None):
                return 0
        real = w.rng["technology"]
        w.rng["technology"] = Zero()
        try:
            T.yearly(w)
        finally:
            w.rng["technology"] = real
        ev = next(e for e in w.events if e["kind"] == "invention" and e["data"].get("technique") == "writing")
        self.assertFalse(ev["data"]["stimulus_needed"])
        self.assertNotIn({"band": a.id}, ev["causes"])
