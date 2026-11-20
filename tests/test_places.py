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
        self.assertIn("named the river", w.events[ev[0]]["causes"][1]["note"])

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
        w.spec[b.id] = 50.0                              # specialists of a band that is no polity's seat: no scribes
        w.polities = {0: Polity(0, a.id, 0, "test")}
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
        d = w.new_band(a.cell, parent=a.id)
        self.assertEqual(float(T._scribes(w)[d.id]), 0.0)
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
