"""Per-band rows kept only for bands that hold one (origins/rows.py; Ben, 22 November 2026)."""
import unittest

import numpy as np

from origins import engine, persist
from origins.rows import SlotMap, SparseRows
from origins.sim import disease, trade
from origins.state import World
from origins.worldgen import generate


class Rows(unittest.TestCase):
    def test_slots_are_reused_and_ended_rows_refuse(self):
        m = SlotMap()
        a = SparseRows(m, (3,), np.float32, 0.0)
        m.assign(5)
        a[5] = [1, 2, 3]
        m.assign(9)
        a[9] = 7
        self.assertEqual(a[[9, 5]].tolist(), [[7, 7, 7], [1, 2, 3]])
        m.release(5)
        with self.assertRaises(KeyError):
            a[5]
        with self.assertRaises(KeyError):
            m.assign(5)                                   # an ended band never comes back
        s = m.assign(11)
        self.assertEqual(s, 0)                            # the freed slot, at the fill value
        self.assertEqual(a[11].tolist(), [0, 0, 0])
        self.assertEqual(len(a), len(m))
        d = a.dense()
        self.assertEqual(d[9].tolist(), [7, 7, 7])
        self.assertEqual(d[5].tolist(), [0, 0, 0])
        with self.assertRaises(TypeError):
            a[np.array([True, False])]

    def test_ended_bands_free_their_rows_and_count_in_the_last_years(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        w.diseases = [{"name": "x", "year": 0}]
        w.dz_last[b.id, 0] = 123
        from origins.sim import bands
        bands.end_band(w, b, "test", log=False)
        self.assertEqual(int(w.dz_slots.slot[b.id]), -2)
        self.assertEqual(int(w.partner_slots.slot[b.id]), -2)
        self.assertEqual(int(disease.last_any(w)[0]), 123)
        self.assertEqual(trade.partners(w, b.id), [])

    def test_save_round_trip_and_older_dense_saves(self):
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 40)
        data = persist.to_bytes(w)
        w2 = persist.from_bytes(data, w.planet)
        self.assertEqual(persist.digest(w2), persist.digest(w))
        for a, b in ((w.dz_imm, w2.dz_imm), (w.dz_last, w2.dz_last), (w.partner_of, w2.partner_of),
                     (w.partner_gave, w2.partner_gave)):
            self.assertTrue(np.array_equal(a.dense(), b.dense()))
        # a save holding a row for every band id (before 22 November 2026) loads into rows for the living bands
        import io
        import zipfile
        zin = zipfile.ZipFile(io.BytesIO(data))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zo:
            for n in zin.namelist():
                blob = zin.read(n)
                if n == "arrays.npz":
                    arrs = dict(np.load(io.BytesIO(blob)))
                    for k in [k for k in arrs if k.startswith(("dz_slots", "partner_slots")) or k.endswith("_rows")
                              or k == "dz_gone_last"]:
                        arrs.pop(k)
                    arrs["dz_imm"], arrs["dz_last"] = w.dz_imm.dense(), w.dz_last.dense()
                    arrs["partner_of"], arrs["partner_since"] = w.partner_of.dense(), w.partner_since.dense()
                    arrs["partner_gave"] = w.partner_gave.dense()
                    buf = io.BytesIO()
                    np.savez(buf, **arrs)
                    blob = buf.getvalue()
                zo.writestr(n, blob)
        w3 = persist.from_bytes(out.getvalue(), w.planet)
        live = [b.id for b in w.living_bands()]
        self.assertTrue(np.array_equal(w3.dz_imm[live], w.dz_imm[live]))
        self.assertTrue(np.array_equal(w3.partner_of[live], w.partner_of[live]))
        engine.step(w3, 4 * 5)                            # and runs on


if __name__ == "__main__":
    unittest.main()
