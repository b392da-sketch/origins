"""Large arrays in mapped files, and the polity log as a table (Ben, 29 November 2026, after G4a pilot 5)."""
import io
import json
import unittest
import zipfile

import numpy as np

from origins import engine, persist, spill
from origins.sim import polity
from origins.state import World
from origins.worldgen import generate


class Spill(unittest.TestCase):
    def setUp(self):
        self.old = spill.SPILL_MIN
        spill.SPILL_MIN = 4096

    def tearDown(self):
        spill.SPILL_MIN = self.old

    def test_a_large_array_is_mapped_and_grows_in_place_keeping_every_value(self):
        a = spill.alloc((1000, 3), np.int32, -1)
        self.assertTrue(spill.is_spilled(a))
        self.assertTrue((a == -1).all())
        a[:] = np.arange(3000, dtype=np.int32).reshape(1000, 3)
        b = spill.regrow(a, 4000, -1)
        self.assertEqual(spill.filename(b), spill.filename(a))  # the same file, grown
        self.assertIs(type(b), np.ndarray)                      # a plain array (np.memmap's methods are slow)
        self.assertTrue((b[:1000] == np.arange(3000).reshape(1000, 3)).all())
        self.assertTrue((b[1000:] == -1).all())
        small = spill.alloc(10, np.float64, 0.5)
        self.assertFalse(spill.is_spilled(small))
        c = spill.regrow(small, 2000, 0.25)                      # an ordinary array that becomes large moves out
        self.assertTrue(spill.is_spilled(c))
        self.assertTrue((c[:10] == 0.5).all() and (c[10:] == 0.25).all())

    def test_a_world_with_mapped_arrays_saves_replays_and_digests_as_one_without(self):
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 40)
        data = persist.to_bytes(w)
        spill.SPILL_MIN = 2 ** 62                                # nothing mapped
        w0 = persist.from_bytes(data, w.planet)
        spill.SPILL_MIN = 256
        w1 = persist.from_bytes(data, w.planet)
        self.assertTrue(spill.is_spilled(w1.people.birth) or spill.is_spilled(w1.minor["land_move"]._i))
        self.assertFalse(spill.is_spilled(w0.people.alive))
        self.assertEqual(persist.digest(w0), persist.digest(w1))
        engine.step(w0, 4 * 10)
        engine.step(w1, 4 * 10)
        self.assertEqual(persist.digest(w0), persist.digest(w1))
        self.assertEqual(len(w0.events), len(w1.events))


class PolityLogTable(unittest.TestCase):
    ROWS = [[100, 3, 4, 250, 2, 1.25, 3.5, 5, 2, 812, 2, 1], [110, 3, 5, 260, 2, 0.75, 3.25, 5, 2, 812, 1, 0],
            [110, 7, 3, 90, 1, 2.0, 1.0, 0, 1, 77, 1, 3]]

    def test_it_behaves_as_the_list_of_rows(self):
        g = polity.PolityLog(self.ROWS)
        self.assertEqual(list(g), self.ROWS)
        self.assertEqual(g[1], self.ROWS[1])
        self.assertEqual(g[-1], self.ROWS[-1])
        self.assertEqual(g[0:2], self.ROWS[0:2])
        self.assertEqual(len(g), 3)
        self.assertEqual(json.dumps(list(g)), json.dumps(self.ROWS))      # the same values, types and all
        del g[:-2]
        self.assertEqual(list(g), self.ROWS[-2:])
        with self.assertRaises(ValueError):
            g.append([1, 2, 3])
        with self.assertRaises(ValueError):
            g.append([1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        for _ in range(3000):                                    # grows
            g.append(self.ROWS[0])
        self.assertEqual(g[-1], self.ROWS[0])

    def test_saves_keep_it_as_arrays_and_older_saves_load_their_rows(self):
        w = World.new(1, 1, generate(1))
        w.polity_log = polity.PolityLog(self.ROWS)
        data = persist.to_bytes(w)
        z = zipfile.ZipFile(io.BytesIO(data))
        meta = json.loads(z.read("meta.json"))
        self.assertNotIn("polity_log", meta["polity"])
        self.assertIn("polity_log_i.npy", zipfile.ZipFile(io.BytesIO(z.read("arrays.npz"))).namelist())
        w2 = persist.from_bytes(data, w.planet)
        self.assertEqual(list(w2.polity_log), self.ROWS)
        self.assertEqual(persist.digest(w2), persist.digest(w))
        old = polity.to_json(w)                                  # an older save: the rows in meta.json
        self.assertEqual(old["polity_log"], self.ROWS)
        w3 = World.new(1, 1, generate(1))
        polity.from_json(w3, old)
        self.assertEqual(list(w3.polity_log), self.ROWS)


if __name__ == "__main__":
    unittest.main()
