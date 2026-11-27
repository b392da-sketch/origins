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
        self.assertGreaterEqual(meta["schema"], 4)         # 4 since review 040; 5 since review 042
        self.assertNotIn(meta["schema"], (1, 2, 3))        # the schema-3 reader's READABLE_SCHEMAS
        self.assertIn(meta["schema"], state.READABLE_SCHEMAS)

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


class Review041(unittest.TestCase):
    """Codex review 041."""

    def test_finding1_decoded_arrays_are_dropped_after_their_section(self):
        import inspect
        src = inspect.getsource(persist.from_file)
        self.assertIn('_drop(arrays, "br_" + k, "brfill_" + k)', inspect.getsource(persist._load_band_rows))
        self.assertIn('_drop(arrays, key)', inspect.getsource(persist._load_band_rows))   # older dense saves
        for k in ('_drop(arrays, prefix="b_")', '_drop(arrays, "dz_log")',
                  '_drop(arrays, prefix="minor_")', '_drop(arrays, prefix="p_")', '_drop(arrays, prefix="g_")',
                  '_drop(arrays, "goods", prefix="partner_")'):
            self.assertIn(k, src)

    def test_finding2_meta_is_written_part_by_part_with_the_same_bytes(self):
        import io
        import json
        import zipfile
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 10)
        m = zipfile.ZipFile(io.BytesIO(persist.to_bytes(w))).read("meta.json")
        self.assertEqual(m, json.dumps(persist._jsonable(json.loads(m)), separators=(",", ":")).encode())
        import inspect
        self.assertNotIn("json.dumps(v, default=str)", inspect.getsource(persist))   # no second serialisation

    def test_finding3_load_from_a_path_streams(self):
        import inspect
        self.assertIn("return from_file(path, planet)", inspect.getsource(persist.load))


class BandRows(unittest.TestCase):
    """Every per-band array kept as band rows, for living bands only (27 November 2026, after G4a pilot 3: the
    dense arrays doubled to 4,194,304 rows with about 26,000 bands alive)."""

    def test_every_per_band_array_is_band_rows_and_sized_by_living_bands(self):
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 40)
        from origins.rows import is_rows
        for k in persist.BAND_ROW_ARRAYS:
            a = getattr(w, k, None)
            if a is not None:
                self.assertTrue(is_rows(a), k)
                self.assertIs(a.slots, w.band_rows, k)
        live = sorted(b.id for b in w.living_bands())
        held = w.band_rows.held().tolist()
        self.assertEqual(sorted(set(held) - set(live)), sorted(getattr(w, "rows_kept", set())))
        self.assertLessEqual(len(w.band_rows.owner), 2 * max(len(live), 32))

    def test_an_ended_band_gives_up_its_rows_and_reading_them_raises(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        b = w.new_band(a.cell, parent=a.id)
        w.tech[b.id, 0] = 0.5
        w.goods[b.id] = 0.0
        from origins.sim import bands
        bands.end_band(w, b, "test", log=False)
        self.assertEqual(int(w.band_rows.slot[b.id]), -2)
        for k in ("tech", "goods", "customs", "farm_share", "spec", "skill", "land_short"):
            with self.assertRaises(KeyError):
                getattr(w, k)[b.id]
        c = w.new_band(a.cell, parent=a.id)               # the freed slot, at each array's fill
        self.assertEqual(float(w.tech[c.id, 0]), float(w.tech[a.id, 0]))   # (a daughter knows what her mother knew)
        self.assertTrue(np.isnan(w.farm_rr_real[c.id]))
        self.assertEqual(int(w.farm_rr_cell[c.id]), -1)

    def test_an_ended_seat_keeps_its_rows_until_its_polity_moves_on(self):
        w = World.new(1, 1, generate(1))
        a = w.living_bands()[0]
        s = w.new_band(a.cell, parent=a.id)
        from origins.sim import bands
        from origins.sim.polity import Polity
        import dataclasses
        fields = {f.name for f in dataclasses.fields(Polity)}
        p = Polity(**{k: v for k, v in {"id": 0, "seat": s.id, "founded": w.t, "name": "Test"}.items() if k in fields})
        w.polities = {0: p}
        w.polity_of[s.id] = 0                              # a seat belongs to its own polity
        w.customs[s.id, 0] = 1
        bands.end_band(w, s, "test", log=False)
        self.assertEqual(int(w.customs[s.id, 0]), 1)       # read as it stood when the band ended
        bands.sweep_rows(w)
        self.assertEqual(int(w.customs[s.id, 0]), 1)       # still the seat of a living polity
        data = persist.to_bytes(w)
        w2 = persist.from_bytes(data, w.planet)
        self.assertEqual(w2.rows_kept, {s.id})
        self.assertEqual(persist.digest(w2), persist.digest(w))
        p.alive = False
        bands.sweep_rows(w)
        with self.assertRaises(KeyError):
            w.customs[s.id]
        self.assertEqual(w.rows_kept, set())

    def test_round_trip_and_an_older_dense_save(self):
        w = World.new(1, 1, generate(1))
        engine.step(w, 4 * 60)
        data = persist.to_bytes(w)
        w2 = persist.from_bytes(data, w.planet)
        self.assertEqual(persist.digest(w2), persist.digest(w))
        engine.step(w, 4 * 5)
        engine.step(w2, 4 * 5)
        self.assertEqual(persist.digest(w2), persist.digest(w))   # and the slots replay exactly
        # a save from before (schema 5): a dense array for every band id ever issued
        import io
        import zipfile
        zin = zipfile.ZipFile(io.BytesIO(data))
        out = io.BytesIO()
        w0 = persist.from_bytes(data, w.planet)
        with zipfile.ZipFile(out, "w") as zo:
            for n in zin.namelist():
                blob = zin.read(n)
                if n == "arrays.npz":
                    arrs = dict(np.load(io.BytesIO(blob)))
                    for k in [k for k in arrs if k.startswith(("br_", "brfill_", "band_rows_"))]:
                        arrs.pop(k)
                    for k in persist.BAND_ROW_ARRAYS:
                        a = getattr(w0, k, None)
                        if a is not None:
                            d = a.dense()
                            d[w0.next_band:] = a.fill
                            arrs[("land_" + k) if k.startswith("land_") else k] = d
                    buf = io.BytesIO()
                    np.savez(buf, **arrs)
                    blob = buf.getvalue()
                zo.writestr(n, blob)
        w3 = persist.from_bytes(out.getvalue(), w.planet)
        self.assertEqual(persist.digest(w3), persist.digest(w0))  # the same rows, by band id
        engine.step(w3, 4 * 5)
        engine.step(w0, 4 * 5)
        self.assertEqual(persist.digest(w3), persist.digest(w0))  # and the same history after

    def test_a_schema_5_reader_refuses_these_saves(self):
        from origins import state
        self.assertEqual(state.SCHEMA, 6)
        self.assertIn(5, state.READABLE_SCHEMAS)
