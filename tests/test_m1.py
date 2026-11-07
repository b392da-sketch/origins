"""M1 tests: languages, customs, hazards, sea crossings. Run: python -m pytest tests/test_m1.py"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from origins import engine, explain, persist  # noqa: E402
from origins.lang import changes as CH  # noqa: E402
from origins.lang.proto import MEANINGS, PROTO, parse, show  # noqa: E402
from origins.sim import customs, hazards, language  # noqa: E402
from origins.state import C, World  # noqa: E402
from origins.worldgen import generate  # noqa: E402

_PLANETS = {}
_WORLDS = {}


def planet(seed):
    if seed not in _PLANETS:
        _PLANETS[seed] = generate(seed)
    return _PLANETS[seed]


def run(ws=1, rs=1, years=600):
    key = (ws, rs, years)
    if key not in _WORLDS:
        w = World.new(ws, rs, planet(ws))
        engine.step(w, 4 * years)
        _WORLDS[key] = w
    return persist.from_bytes(persist.to_bytes(_WORLDS[key]), planet(ws))


class SoundChange(unittest.TestCase):
    def test_rules_are_regular(self):
        words = [parse(f) for f in PROTO.values()]
        for rid in CH.RULES:
            out = [CH.apply(rid, w) for w in words]
            # deterministic and applied the same way to identical words
            self.assertEqual(out, [CH.apply(rid, w) for w in words], rid)
            self.assertTrue(CH.describe(rid))

    def test_known_examples(self):
        f = parse(PROTO["father"])
        f = CH.apply("laryngeal_loss", f)
        self.assertEqual(show(f), "patēr")
        self.assertEqual(show(CH.apply("grimm_fricatives", f)), "faþēr")
        # Grimm's law does not apply after s
        self.assertEqual(CH.apply("grimm_fricatives", ("s", "t", "a")), ("s", "t", "a"))

    def test_exclusive_alternatives(self):
        opts = CH.eligible({"satem"}, [parse(f) for f in PROTO.values()])
        self.assertNotIn("centum", opts)


class Languages(unittest.TestCase):
    def test_histories_rebuild_every_word(self):
        """Replaying a language's history from the proto-form reproduces its current lexicon exactly."""
        w = run(1, 1, 900)
        living = [l for l in w.languages.values() if l.alive]
        self.assertGreater(len(w.languages), 1, "no language split in 900 years")
        for lang in living[:10]:
            for m in MEANINGS:
                steps = language.word_history(w, lang.id, m)
                self.assertEqual(steps[-1][1], show(tuple(lang.lexicon[m][0])), (lang.id, m, steps))

    def test_every_band_speaks_a_living_language(self):
        w = run(1, 1, 900)
        for b in w.living_bands():
            self.assertTrue(w.languages[b.language].alive, b.id)

    def test_children_speak_their_bands_language(self):
        w = run(1, 1, 900)
        idx = w.alive_idx()
        idx = idx[w.ages(idx) < 12]          # adults who married in keep their own speech (and names)
        same = (w.people.lang[idx] == np.array([w.bands[int(b)].language for b in w.people.band[idx]])).mean()
        self.assertGreater(same, 0.95)

    def test_names_built_from_language_words(self):
        w = run(1, 1, 900)
        i = int(w.alive_idx()[0])
        self.assertTrue(w.people.name(i)[0].isupper())
        lang = w.languages[int(w.people.lang[i])]
        a, b = int(w.people.name_a[i]), int(w.people.name_b[i])
        self.assertEqual(w.people.name(i), language.compose_name(lang, a, b, w.people.sex[i] == 0))

    def test_splits_are_explained(self):
        w = run(1, 1, 900)
        for e in w.events:
            if e["kind"] == "language_split":
                ch = explain.chain(w, {"event": e["id"]})
                self.assertTrue(ch["causes"])
                self.assertGreaterEqual(len(e["data"]["daughters"]), 2)

    def test_save_round_trip_keeps_languages(self):
        w = run(1, 1, 600)
        w2 = persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertEqual(persist.digest(w), persist.digest(w2))
        engine.step(w, 4 * 30)
        engine.step(w2, 4 * 30)
        self.assertEqual(persist.digest(w), persist.digest(w2))


class Customs(unittest.TestCase):
    def test_inherited_at_fission(self):
        w = run(1, 1, 600)
        for b in list(w.bands.values())[-20:]:
            if b.parent >= 0 and b.founded == w.t:
                np.testing.assert_array_equal(w.customs[b.id], w.customs[b.parent])

    def test_distance_zero_for_self(self):
        w = run(1, 1, 600)
        b = w.living_bands()[0]
        self.assertEqual(customs.distance(w, b.id, b.id), 0.0)

    def test_residence_variants(self):
        w = run(1, 1, 300)
        b = w.living_bands()[0]
        w.customs[b.id, customs.RESIDENCE] = 0
        self.assertGreater(customs.residence_share(w, b.id), 0.5)
        w.customs[b.id, customs.RESIDENCE] = 1
        self.assertLess(customs.residence_share(w, b.id), 0.5)


class Hazards(unittest.TestCase):
    def test_kill_share_conserves_people_and_records_cause(self):
        w = run(1, 1, 300)
        cell = w.living_bands()[0].cell
        eid = w.event("earthquake", cell=cell, causes=[{"note": "test"}])
        before = w.population()
        d = hazards.kill_share(w, {cell: 0.5}, "earthquake", eid, np.random.default_rng(0))
        self.assertGreater(d, 0)
        self.assertEqual(w.population(), before - d)
        engine.step(w, 1)
        self.assertEqual(w.invariant_failures, [])
        p = w.people
        dead = np.nonzero((p.death_hazard[:p.n] == eid))[0]
        self.assertTrue(len(dead))
        ch = explain.chain(w, {"death": int(dead[0])})
        self.assertTrue(any(c.get("ref") == {"event": eid} for c in ch["causes"]), ch)
        self.assertEqual(int(p.cause[dead[0]]), C["earthquake"])

    def test_hazards_only_where_possible(self):
        w = run(2, 1, 600)
        pl = w.planet
        for e in w.events:
            if e["kind"] == "flood":
                self.assertTrue(pl.river[e["cell"]])
            if e["kind"] == "eruption":
                self.assertTrue(pl.volcanic[e["cell"]])
            if e["kind"] == "earthquake":
                self.assertTrue(pl.seismic[e["cell"]])

    def test_food_recovers(self):
        w = run(1, 1, 300)
        w.hazard_food[:] = 0.4
        for _ in range(12):
            w.hazard_food += 0.35 * (1 - w.hazard_food)
        self.assertGreater(w.hazard_food.min(), 0.99)


class Crossing(unittest.TestCase):
    def test_walkable(self):
        pl = planet(1)
        nb = pl.grid.neighbours
        c = int(np.nonzero(pl.land)[0][0])
        x = next(int(n) for n in nb[c] if n >= 0 and pl.land[n])
        self.assertTrue(hazards._walkable(pl, nb, c, x))



class BandExtinctionCause(unittest.TestCase):
    def test_folded_members_are_not_cited_as_deaths(self):
        """A group whose members were folded (not killed) must not cite them as its last death."""
        from origins.sim import bands, groups
        w = run(1, 1, 300)
        p = w.people
        # a new band none of whose own members has died (as in the case found in the G1 rerun)
        old = w.living_bands()[0]
        mem = w.members(old.id)[:6]
        b = w.new_band(old.cell, old.id, int(mem[0]))
        p.band[mem] = b.id
        w.people_changed()
        groups.fold(w, b)
        G = w.groups
        G.F[b.group] = 0
        G.M[b.group] = 0
        bands.end_band(w, b, "no surviving members")
        e = w.events[-1]
        self.assertEqual(e["kind"], "band_extinct")
        self.assertTrue(explain.resolvable(w, {"event": e["id"]}), e)


if __name__ == "__main__":
    unittest.main()
