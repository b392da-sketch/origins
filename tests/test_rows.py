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


class Review040(unittest.TestCase):
    """Codex review 040."""

    def test_finding1_sparse_saves_carry_a_schema_older_readers_refuse(self):
        import io
        import json
        import zipfile
        from origins import state
        w = World.new(1, 1, generate(1))
        meta = json.loads(zipfile.ZipFile(io.BytesIO(persist.to_bytes(w))).read("meta.json"))
        self.assertEqual(meta["schema"], 4)
        self.assertNotIn(4, (1, 2, 3))                     # the schema-3 reader's READABLE_SCHEMAS
        self.assertIn(4, state.READABLE_SCHEMAS)

    def test_finding2_a_narrow_sparse_save_widens_to_the_cap(self):
        from origins import params as P
        old = P.PARTNERS_CAP
        try:
            P.PARTNERS_CAP = 4
            w = World.new(1, 1, generate(1))
            a = w.living_bands()[0]
            others = [w.new_band(a.cell, parent=a.id) for _ in range(5)]
            for o in others[:4]:
                trade._link(w, a.id, o.id)
            self.assertEqual(w.partner_of.shape[1], 4)
            data = persist.to_bytes(w)
            P.PARTNERS_CAP = 16
            w2 = persist.from_bytes(data, w.planet)
        finally:
            P.PARTNERS_CAP = old
        self.assertEqual(w2.partner_of.shape[1], max(16, old))
        self.assertEqual(sorted(trade.partners(w2, a.id)), sorted(o.id for o in others[:4]))
        trade._link(w2, a.id, others[4].id)                # a fifth link has room
        self.assertIn(others[4].id, trade.partners(w2, a.id))

    def test_finding3_an_ended_band_without_rows_cannot_get_one(self):
        import io
        import zipfile
        from origins.sim import bands
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        bands.end_band(w, b, "test", log=False)
        data = persist.to_bytes(w)                            # rewritten as a save from before the arrays
        zin, out = zipfile.ZipFile(io.BytesIO(data)), io.BytesIO()
        with zipfile.ZipFile(out, "w") as zo:
            for n in zin.namelist():
                blob = zin.read(n)
                if n == "arrays.npz":
                    arrs = dict(np.load(io.BytesIO(blob)))
                    for k in [k for k in arrs if k.startswith(("dz_slots", "partner_slots", "dz_imm", "dz_last",
                                                                 "partner_")) or k == "dz_gone_last"]:
                        arrs.pop(k)
                    buf = io.BytesIO()
                    np.savez(buf, **arrs)
                    blob = buf.getvalue()
                zo.writestr(n, blob)
        w2 = persist.from_bytes(out.getvalue(), w.planet)
        for m in (w2.dz_slots, w2.partner_slots):
            self.assertEqual(int(m.slot[b.id]), -2)
            with self.assertRaises(KeyError):
                m.assign(b.id)
        m = SlotMap()
        m.release(7)                                          # released without ever holding a row
        with self.assertRaises(KeyError):
            m.assign(7)

    def test_owner_slots_grow_by_doubling(self):
        m = SlotMap()
        for i in range(5000):
            m.assign(i)
        self.assertEqual(m.n, 5000)
        self.assertGreaterEqual(len(m._owner), 5000)
        self.assertEqual(m.owner[4999], 4999)


class LoadFromFile(unittest.TestCase):
    """G4a pilot 3 (26 November 2026): saves load from a path without holding the save and its arrays as bytes."""

    def test_from_file_and_from_bytes_give_the_same_world(self):
        import tempfile
        from pathlib import Path
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 20)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w.zip"
            persist.to_file(w, p, fast=True)
            a = persist.from_file(p, w.planet)
            b = persist.from_bytes(p.read_bytes(), w.planet)
        self.assertEqual(persist.digest(a), persist.digest(w))
        self.assertEqual(persist.digest(b), persist.digest(w))
        engine.step(a, 4 * 3)
        engine.step(b, 4 * 3)
        self.assertEqual(persist.digest(a), persist.digest(b))

    def test_memory_trace_only_when_asked(self):
        import contextlib
        import io
        import os
        w = World.new(1, 1, generate(1))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            persist.from_bytes(persist.to_bytes(w), w.planet)
        self.assertNotIn("[mem]", out.getvalue())
        os.environ["ORIGINS_MEM_TRACE"] = "1"
        try:
            with contextlib.redirect_stdout(out):
                persist.from_bytes(persist.to_bytes(w), w.planet)
        finally:
            del os.environ["ORIGINS_MEM_TRACE"]
        self.assertIn("[mem] load: world built", out.getvalue())
        self.assertIn("[mem] save, largest arrays", out.getvalue())
