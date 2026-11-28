"""Saving and loading worlds; exact replay.

A save is a zip with meta.json (small state, events, random-generator states)
and arrays.npz (people, groups, wild food, map knowledge). The planet itself
is regenerated from its seed and checked against the stored fingerprint.
Writes are atomic (temporary file, then replace) and the previous saves are
kept as numbered backups.
"""
from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np

from .state import READABLE_SCHEMAS, SCHEMA, VERSION, Band, Bands, EventStore, People, World, new_accumulators
from .sim import conflict, farming, language, polity, surplus
from .sim.groups import Groups
from .worldgen import generate

BACKUPS = 3


BAND_ROW_ARRAYS = ("customs", "neutral", "skill", "farm_share", "crop_store", "still_years", "forage_rr", "spec",
                   "herder_since", "farm_rr_real", "farm_rr_cell", "farm_rr_lost", "tech", "tech_record",
                   "tech_scribes", "goods", "goods_reached", "tech_prev_prac", "tech_prev_mats", "tech_prev_dep",
                   "tech_prev_wood", "trade_in", "land_short", "land_lost_wild", "land_lost_crop", "land_crop_acc",
                   "land_crop_k", "land_crop_ev", "land_acc_k", "land_acc_kev", "land_acc_ktop")


def _band_rows_state(w) -> dict:
    """The band rows as saved: the slot map, and each per-band array's rows in slot order (with its fill)."""
    m = getattr(w, "band_rows", None)
    if m is None:
        return {}
    out = m.state("band_rows")
    for k in BAND_ROW_ARRAYS:
        a = getattr(w, k, None)
        if a is not None:
            out["br_" + k] = a.rows()
            out["brfill_" + k] = np.asarray([a.fill], dtype=a.dtype)
    return out


def _band_rows_digest(w, h):
    """Each per-band array by band id (ascending) with its rows: the same however slots were assigned."""
    for k in BAND_ROW_ARRAYS:
        a = getattr(w, k, None)
        if a is not None:
            ids, rows = a.by_id()
            h.update(k.encode())
            h.update(np.ascontiguousarray(ids).tobytes())
            h.update(np.ascontiguousarray(rows).tobytes())


_ROW_FILL = {"forage_rr": None, "herder_since": -1.0, "farm_rr_real": np.nan, "farm_rr_cell": -1,
             "land_crop_ev": -1, "land_acc_kev": -1}     # the rest start at 0 (False); forage_rr at FORAGE_RATE


def _set_rows(w, k, a):
    """Put band rows `a` (or None) at w.k, unregistering whatever rows were there."""
    old = getattr(w, k, None)
    if old is not None and old is not a and hasattr(old, "slots") and old in old.slots.arrays:
        old.slots.arrays.remove(old)
    setattr(w, k, a)


def _rows_like(w, tail, dtype, fill):
    from .rows import new_rows
    return new_rows(w, tail, dtype, fill)


def _copy_rows(w, a):
    b = _rows_like(w, a.tail, a.dtype, a.fill)
    b.data[:len(a.data)] = a.data
    return b


def _load_band_rows(w, arrays, alive_ids, meta) -> bool:
    """The band rows: from a save of 27 November 2026 or later, as saved; from an older save's dense per-band arrays,
    each living band's row (the rows of bands that had ended are dropped, and their ids marked ended)."""
    from .rows import SlotMap, SparseRows, rows_from_dense
    from . import params as _P
    m = w.band_rows = SlotMap()
    new = "band_rows_slot" in arrays
    w.rows_kept = set(int(i) for i in meta.get("rows_kept", []))
    if new:
        m.load("band_rows", arrays)
        _drop(arrays, "band_rows_slot", "band_rows_owner", "band_rows_free")
    else:
        # ended seats of living polities keep their rows as they stood (release_rows), as the polity pass reads them
        alive_set = set(int(i) for i in alive_ids)
        seats = {int(x["seat"]) for x in (meta.get("polity") or {}).get("polities", [])
                 if x.get("alive") and int(x.get("seat", -1)) >= 0}
        w.rows_kept = {i for i in seats if i not in alive_set and i < w.next_band}
        alive_ids = sorted(alive_set | w.rows_kept)
        m.grow_ids(max(w.next_band, 1) - 1)
        for i in alive_ids:
            m.assign(int(i))
        m.mark_ended(np.setdiff1d(np.arange(w.next_band, dtype=np.int64), np.asarray(alive_ids, dtype=np.int64)))
    for k in BAND_ROW_ARRAYS:
        setattr(w, k, None)
        if new:
            if "br_" + k not in arrays:
                continue
            d = arrays["br_" + k]
            fill = np.asarray(arrays["brfill_" + k]).reshape(-1)[0].item()
            a = SparseRows(m, d.shape[1:], d.dtype, fill)
            a._grow_rows(max(m.n, 1))
            a.data[:len(d)] = d
            d = None
            setattr(w, k, a)
            _drop(arrays, "br_" + k, "brfill_" + k)
        else:
            key = ("land_" + k) if k.startswith("land_") else k
            if key not in arrays:
                continue
            d = np.asarray(arrays[key])
            if not d.size:                                  # an empty placeholder, of any shape: none kept (review
                _drop(arrays, key)                          # 043, finding 1); land accounts then start at their fill
                continue
            fill = _ROW_FILL.get(k, False if d.dtype == bool else 0)
            if k == "forage_rr":
                fill = _P.FORAGE_RATE
            if k == "customs":
                fill = 0
            setattr(w, k, rows_from_dense(w, d, fill, alive_ids))
            d = None
            _drop(arrays, key)
    return new


def _band_row_defaults(w):
    """Per-band arrays an older save does not hold start as in a new world: at their fill, the customs at the
    founders' row (as the constructor's arrays did before 27 November 2026: Codex review 043, finding 2)."""
    from .sim import customs as _cu, farming as _fa
    from . import params as _P
    fills = {"neutral": ((_cu.N_NEUTRAL,), np.float32, 0.0), "skill": ((len(_fa.SPECIES),), np.float32, 0.0),
             "farm_share": ((), np.float64, 0.0), "crop_store": ((), np.float64, 0.0),
             "still_years": ((), np.float64, 0.0), "forage_rr": ((), np.float64, _P.FORAGE_RATE),
             "spec": ((), np.float64, 0.0)}
    for k, (tail, dt, fill) in fills.items():
        if getattr(w, k, None) is None:
            setattr(w, k, _rows_like(w, tail, dt, fill))
    if getattr(w, "customs", None) is None:
        c = _rows_like(w, (len(_cu.NAMES),), np.int8, 0)
        ids = w.band_rows.held()
        c.load_rows(ids, np.tile(_cu._founders_row(), (len(ids), 1)))
        w.customs = c


def _tech_scribes(w):
    from .sim import technology as _t
    return _t._scribes(w) if getattr(w, "tech", None) is not None else np.zeros(0)


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    return x


def environment() -> dict:
    import platform
    return {"python": platform.python_version(), "numpy": np.__version__}


def to_bytes(w: World, fast: bool = False) -> bytes:
    """The whole world as bytes. fast=True (checkpoints) compresses lightly: much quicker for very large worlds."""
    buf = io.BytesIO()
    to_file(w, buf, fast)
    return buf.getvalue()


class _LazyArrays:
    """The arrays of a save, read from the unpacked npz only when asked for (G4a pilot 3, 26 November 2026: loading
    read every array before building the world, so all of them sat in memory beside the world being built). Each
    access reads the array afresh; nothing is kept here. items() reads one array at a time."""

    def __init__(self, npz):
        self._npz = npz
        self._keys = list(npz.files)
        self._gone: set = set()
        self._last = (None, None)        # the array last read, returned again if asked for next (review 042, 3)

    def __contains__(self, k):
        return k in self._npz.files and k not in self._gone

    def __getitem__(self, k):
        if k not in self:
            raise KeyError(k)
        if self._last[0] == k:
            return self._last[1]
        self._last = (None, None)        # the previous array is released before the next is read
        a = self._npz[k]
        self._last = (k, a)
        return a

    def get(self, k, default=None):
        return self[k] if k in self else default

    def keys(self):
        return [k for k in self._keys if k not in self._gone]

    def __iter__(self):
        return iter(self.keys())

    def items(self):
        for k in self.keys():
            yield k, self[k]

    def pop(self, k, default=None):
        self.__delitem__(k)
        return default

    def __delitem__(self, k):
        self._gone.add(k)
        if self._last[0] == k:
            self._last = (None, None)

    @property
    def files(self):
        return self.keys()


def _prefixed(arrays, prefix: str, strip: bool = True) -> dict:
    """The arrays whose names start with prefix (read now; the others are not touched)."""
    n = len(prefix) if strip else 0
    return {k[n:]: arrays[k] for k in arrays.keys() if k.startswith(prefix)}


def _drop(arrays: dict, *names, prefix: str | None = None):
    """Forget decoded arrays a section has finished with, so the next section's copies do not sit beside them
    (Codex review 041, finding 1). Only lifetimes change: every value is read exactly as before."""
    for k in names:
        arrays.pop(k, None)
    if prefix is not None:
        for k in [k for k in arrays if k.startswith(prefix)]:
            del arrays[k]


def _trace(label: str):
    """With ORIGINS_MEM_TRACE set, print memory in use and the peak so far (G4a pilot 3: what fills memory when a
    large save is loaded). A measuring aid only."""
    import os
    if not os.environ.get("ORIGINS_MEM_TRACE"):
        return
    import resource
    now = anon = 0.0
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS"):
                now = int(line.split()[1]) / 1e6
            if line.startswith("RssAnon"):
                anon = int(line.split()[1]) / 1e6
    except OSError:
        pass
    # (in use includes pages of mapped files, origins/spill.py, which the system can drop; anon cannot be)
    print(f"[mem] {label}: {now:.2f} GB in use ({anon:.2f} GB anon), "
          f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB peak", flush=True)


def _trace_sizes(w, arrays: dict):
    """The save's largest arrays by size in memory, and the row counts of the largest metadata (no second
    serialisation: Codex review 041, finding 2). The members' sizes as written follow from _trace_members."""
    import os
    if not os.environ.get("ORIGINS_MEM_TRACE"):
        return
    ar = sorted(((np.asarray(v).nbytes, k) for k, v in arrays.items()), reverse=True)[:15]
    print("[mem] save, largest arrays (MB): " + ", ".join(f"{k} {n / 1e6:.0f}" for n, k in ar), flush=True)
    rows = {"polity_log": len(getattr(w, "polity_log", []) or []), "band records": len(w.bands.live),
            "band strings": len(w.bands.strings), "events": len(w.events),
            "places": len(getattr(w, "places", {}) or {}), "languages": len(getattr(w, "languages", {}) or {})}
    print("[mem] save, metadata rows: " + ", ".join(f"{k} {n:,}" for k, n in rows.items()), flush=True)


def _trace_meta(parts):
    import os
    if not os.environ.get("ORIGINS_MEM_TRACE"):
        return
    print("[mem] save, largest parts of meta.json as written (MB): " + ", ".join(
        f"{k} {n / 1e6:.0f}" for n, k in sorted(parts, reverse=True)[:12]), flush=True)


def _trace_members(z):
    import os
    if not os.environ.get("ORIGINS_MEM_TRACE"):
        return
    print("[mem] save, members as written (MB, unpacked/packed): " + ", ".join(
        f"{i.filename} {i.file_size / 1e6:.0f}/{i.compress_size / 1e6:.0f}" for i in z.infolist()), flush=True)


def to_file(w: World, f, fast: bool = False) -> None:
    """Write the whole world to a path or file object, streaming the large parts (events, customs log, arrays)
    so that saving a big world needs little memory beyond the world itself."""
    meta = {
        "schema": SCHEMA, "version": VERSION, "world_seed": w.world_seed, "run_seed": w.run_seed,
        "planet_fingerprint": w.planet.fingerprint, "t": w.t, "counts": w.counts, "ledger": w.ledger,
        "next_band": w.next_band, "follow": w.follow, "intervened": w.intervened,
        "invariant_failures": w.invariant_failures,
        "rng": {k: g.bit_generator.state for k, g in w.rng.items()},
        "region_z": w.region_z, "region_factor": w.region_factor, "region_bad_event": w.region_bad_event,
        "yearly": w.yearly, "accum": w.accum, "season_stats": w.season_stats,
        "bands": [dataclasses.asdict(b) for b in w.bands.live.values()], "band_strings": w.bands.strings,
        "reveal_pending": sorted(w.reveal_pending), "pending_restore": w.pending_restore,
        "env": environment(),
        "language": language.to_json(w), "hazards": w.hazards,
        "farming": farming.to_json(w), "surplus": surplus.to_json(w), "polity": polity.to_json(w, with_log=False), "trade": __import__("origins.sim.trade", fromlist=["x"]).to_json(w),
        "conflict": conflict.to_json(w), "timing": w.timing, "first_herders": getattr(w, "first_herders", None), "tech_firsts": getattr(w, "tech_firsts", {}), "tech_writing_log": getattr(w, "tech_writing_log", []), "goods_ledger": getattr(w, "goods_ledger", None), "log_strides": w.log_strides,
        "disease": __import__("origins.sim.disease", fromlist=["x"]).to_json(w),
        "places": __import__("origins.sim.places", fromlist=["x"]).to_json(w),
        "rows_kept": sorted(getattr(w, "rows_kept", set())),   # ended seats still holding rows (27 Nov 2026)
        "dz_counts_split": True,      # named diseases count G1 exposure under their own keys (review 031; review 034)
    }
    arrays = {"stock": w.stock, "stock_broad": w.stock_broad, "known": w.known, "discovered_by": w.discovered_by,
              "discovered_at": w.discovered_at, "food_modifier": w.food_modifier,
              "intervention_event": w.intervention_event, "cell_hunger": w.cell_hunger, "cell_births": w.cell_births,
              "hazard_food": w.hazard_food, "hazard_event": w.hazard_event, "immune": w.immune,
              "polity_of": w.polity_of, "polity_via": w.polity_via, "conquered_at": w.conquered_at,
              "treasury": w.treasury}
    _tech_scribes(w)
    arrays.update(_band_rows_state(w))                 # every per-band array, for living bands only (27 Nov 2026)
    from .sim import land as _land
    arrays.update({"land_" + k: getattr(w, k) for k in _land.ARRAYS
                   if k not in _land.BAND_ARRAYS and getattr(w, k, None) is not None})
    from .sim import disease as _disease
    arrays.update({k: getattr(w, k) for k in _disease.ARRAYS if getattr(w, k, None) is not None})
    from .sim import trade as _trade_s
    arrays.update(_trade_s.partner_state(w))             # partner rows, for bands holding one (22 November 2026)
    if getattr(w, "dz_slots", None) is not None:
        arrays.update(_disease.save_rows(w))              # per-band rows, for bands holding one (22 November 2026)
    if getattr(w, "dz_log", None) is not None:
        arrays["dz_log"] = _disease.log_array(w)          # the per-cell disease record, as an array (review 037)
    from .sim import minorlog as _minor
    arrays.update(_minor.arrays(w))                       # the compact log (Ben, 22 November 2026)
    arrays.update(polity.log_arrays(w))                   # the polity log, as a table (29 November 2026)
    arrays.update({"p_" + k: v for k, v in w.people.arrays().items()})
    arrays.update({"g_" + k: v for k, v in w.groups.arrays().items()})
    arrays.update({"b_" + k: v for k, v in w.bands.arrays().items()})
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED, compresslevel=1 if fast else None) as z:
        # meta.json is written part by part: the same bytes as one json.dumps, without the whole string in memory
        # at once, and each part's size known as written (Codex review 041, finding 2)
        parts = []
        with z.open("meta.json", "w", force_zip64=True) as out:
            out.write(b"{")
            for j, (k, v) in enumerate(meta.items()):        # each part converted as it is written (29 Nov 2026)
                b = (("," if j else "") + json.dumps(str(k)) + ":" + json.dumps(_jsonable(v), separators=(",", ":"))).encode()
                out.write(b)
                parts.append((len(b), k))
            out.write(b"}")
        _trace_meta(parts)
        # events are written one per line, streamed, so a history of millions of events never becomes one huge string
        for name, rows in (("events.jsonl", w.events),
                           ("custom_log.jsonl", ([int(k), v] for k, v in w.custom_log.items()))):
            with z.open(name, "w", force_zip64=True) as out:
                chunk = []
                for e in rows:
                    chunk.append(json.dumps(_jsonable(e), separators=(",", ":")))
                    if len(chunk) >= 5000:
                        out.write(("\n".join(chunk) + "\n").encode())
                        chunk = []
                if chunk:
                    out.write(("\n".join(chunk) + "\n").encode())
        _trace_sizes(w, arrays)
        with z.open("arrays.npz", "w", force_zip64=True) as out:
            (np.savez if fast else np.savez_compressed)(out, **arrays)
        _trace_members(z)


def from_bytes(data: bytes, planet=None) -> World:
    return from_file(io.BytesIO(data), planet)


def from_file(src, planet=None) -> World:
    """A world from a save given as a path or a file object. From a path, the save is read from disk as it is
    parsed, and its arrays are unpacked to a temporary file and read one by one, not held as bytes beside the
    arrays (G4a pilot 2, 22 November 2026: loading a 1.1 GB checkpoint from bytes peaked at 13 GB)."""
    import contextlib
    import shutil
    import tempfile
    _trace("load: start")
    with contextlib.ExitStack() as stack:
        with zipfile.ZipFile(src) as z:
            meta = json.loads(z.read("meta.json"))
            _trace("load: meta.json parsed")
            tmp = stack.enter_context(tempfile.TemporaryFile())
            with z.open("arrays.npz") as f:
                shutil.copyfileobj(f, tmp, 16 << 20)
            tmp.seek(0)
            # each array is read when its part of the world is built, not all at once beforehand (G4a pilot 3)
            arrays = _LazyArrays(stack.enter_context(np.load(tmp)))
            _trace("load: arrays opened")
            if "events.jsonl" in z.namelist():
                with z.open("events.jsonl") as f:
                    meta["events"] = EventStore(json.loads(line) for line in io.TextIOWrapper(f, encoding="utf-8") if line.strip())
            if "custom_log.jsonl" in z.namelist():
                with z.open("custom_log.jsonl") as f:
                    meta["_custom_log"] = {int(r[0]): r[1] for r in (json.loads(line) for line in io.TextIOWrapper(f, encoding="utf-8") if line.strip())}
        _trace("load: events and logs read")
        if meta.get("schema") not in READABLE_SCHEMAS:
            raise ValueError(f"unsupported save schema {meta.get('schema')} (this version reads {READABLE_SCHEMAS})")
        planet = planet if planet is not None and planet.seed == meta["world_seed"] else generate(meta["world_seed"])
        from .worldgen import legacy_fingerprint
        if meta["planet_fingerprint"] not in (planet.fingerprint, legacy_fingerprint(planet)):
            raise ValueError("planet fingerprint mismatch: this save was made with different world-generation code")
        w = World(planet, meta["run_seed"])
        saved_env = meta.get("env")
        w.load_warning = ""
        if saved_env and saved_env != environment():
            w.load_warning = (f"saved with Python {saved_env['python']} / NumPy {saved_env['numpy']}, now running "
                              f"{environment()['python']} / {environment()['numpy']}: the world continues normally, but its "
                              f"future may differ slightly from the same save continued on the original versions")
        w.t = meta["t"]
        w.counts = meta["counts"]
        w.ledger = meta["ledger"]
        w.next_band = meta["next_band"]
        w.follow = meta["follow"]
        w.intervened = meta["intervened"]
        w.invariant_failures = meta["invariant_failures"]
        for k, st in meta["rng"].items():
            w.rng[k].bit_generator.state = st
        w.region_z = np.array(meta["region_z"])
        w.region_factor = np.array(meta["region_factor"])
        w.region_bad_event = np.array(meta["region_bad_event"], dtype=np.int64)
        w.yearly = meta["yearly"]
        acc = new_accumulators()
        for k, v in meta["accum"].items():
            if isinstance(acc[k], np.ndarray):
                arr = np.array(v)
                if arr.shape[0] < acc[k].shape[0]:          # saves from before a cause of death was added
                    pad = np.zeros_like(acc[k])
                    pad[:arr.shape[0]] = arr
                    arr = pad
                acc[k] = arr
            else:
                acc[k] = list(v)
        w.accum = acc
        w.season_stats = meta["season_stats"]
        w.events = meta["events"] if isinstance(meta["events"], EventStore) else EventStore(meta["events"])
        w.bands = Bands()
        for d in meta["bands"]:
            d["trail"] = [tuple(x) for x in d["trail"]]
            b = Band(**d)
            w.bands[b.id] = b
        w.bands.load_arrays(_prefixed(arrays, "b_"), meta.get("band_strings", []))
        _drop(arrays, prefix="b_")
        _trace("load: bands built")
        w.reveal_pending = set(meta["reveal_pending"])
        w.pending_restore = [(a, list(b), c) for a, b, c in meta.get("pending_restore", [])]
        for k in ("stock", "known", "discovered_by", "discovered_at", "food_modifier", "intervention_event",
                  "cell_hunger", "cell_births", "hazard_food", "hazard_event", "immune",
                  "polity_of", "polity_via", "conquered_at", "stock_broad"):
            if k in arrays:                      # older saves of this schema may lack optional arrays
                setattr(w, k, arrays[k])
        if getattr(w, "stock_broad", None) is None or len(w.stock_broad) != len(w.stock):
            from .sim import climate as _climate            # saves from before the broad-spectrum pool (14 Nov 2026)
            w.stock_broad = _climate.broad_max(w).copy()
        alive_ids = sorted(b.id for b in w.bands.live.values() if b.alive)
        new_rows_format = _load_band_rows(w, arrays, alive_ids, meta)
        _band_row_defaults(w)                  # arrays an older save lacks start as a new world's (review 043)
        from .sim import farming as _farming
        _farming._farm_rows(w)                 # saves from before real yields (19-20 Nov 2026) or pastoralism (M4a)
        _trace("load: per-band arrays built")
        from .sim import technology as _tech
        if getattr(w, "tech", None) is None or w.tech.tail != (_tech.K,):
            _set_rows(w, "tech", _rows_like(w, (_tech.K,), np.float32, 0.0))   # saves from before the network;
            # the records and scribes are kept if they fit (review 043, finding 4)
        if getattr(w, "tech_record", None) is None or w.tech_record.tail != (_tech.K,):
            _set_rows(w, "tech_record", _rows_like(w, (_tech.K,), np.float32, 0.0))   # before written records: none
        # (saves from before scribes, 20 Nov 2026, have none: _scribes starts them from today's specialists)
        w.first_herders = meta.get("first_herders")
        w.tech_firsts = dict(meta.get("tech_firsts", {}))
        w.tech_writing_log = [list(r) for r in meta.get("tech_writing_log", [])]    # from review 032; older saves: none
        _trace("load: technology built")
        from .sim import trade as _trade                  # goods (M4a trade); saves from before have none
        led = meta.get("goods_ledger")
        goods, reached = getattr(w, "goods", None), getattr(w, "goods_reached", None)
        w.goods = w.goods_reached = None
        _trade.init(w)
        if goods is not None and goods.tail == (_trade.G,):
            _set_rows(w, "goods", goods)                 # exactly as saved (replay digest)
        elif goods is not None:
            goods.slots.arrays.remove(goods)
        if reached is not None and reached.tail == (_trade.G,):
            _set_rows(w, "goods_reached", reached)       # trade stage 3, after review 014
        else:
            if reached is not None:
                reached.slots.arrays.remove(reached)
            _set_rows(w, "goods_reached", None)          # older saves: what a band holds has reached it
        if "partner_slots_slot" in arrays:                  # partner rows for bands holding one (22 November 2026)
            _trade.partner_load(w, arrays)
        elif "partner_of" in arrays:                        # gift partnerships (trade stage 2), a row for every band id
            of = np.asarray(arrays["partner_of"], dtype=np.int64)
            gave = np.asarray(arrays["partner_gave"], dtype=np.float64) if "partner_gave" in arrays else None
            _trade.partner_rows_from_dense(w, of, np.asarray(arrays["partner_since"], dtype=np.int64), gave, alive_ids)
            of = gave = None
        else:                                               # older saves have none: every living band starts without
            for i in alive_ids:
                w.partner_slots.assign(i)
            _trade.mark_partner_ended(w, alive_ids)
        _trade.grow(w, max(w.next_band, 1) - 1)
        _drop(arrays, "goods", prefix="partner_")
        _trace("load: trade built")
        from .sim import disease as _disease                 # diseases from animals (M4a): older saves start with none
        _disease.from_json(w, meta.get("disease", {}))
        from .sim import places as _places                   # place names (M4a): older saves start with none
        _places.from_json(w, meta.get("places", {}))
        if "dz_log" in arrays and np.asarray(arrays["dz_log"]).size:
            w.dz_log = _disease.RowLog.from_array(arrays["dz_log"])
        _drop(arrays, "dz_log")
        _trace("load: disease and places built")
        from .sim import minorlog as _minor                  # the compact log: older saves start with it empty
        _minor.load(w, arrays)          # table by table, each read and released in turn (review 042, finding 2)
        _drop(arrays, prefix="minor_")
        _trace("load: compact log built")
        for k in _disease.ARRAYS:
            if k in arrays and np.asarray(arrays[k]).size:
                setattr(w, k, np.asarray(arrays[k], dtype=getattr(w, k).dtype))
        if w.diseases and not meta.get("dz_counts_split") and any(k.startswith("ob_") for k in w.counts):
            # a save made with named diseases before review 031 wrote their G1 counts under M1's keys: they cannot be
            # told apart, so they are set aside, not reported as M1's (Codex review 031, finding 4). Only such saves:
            # a current save marks itself, so M1's own counts in it are kept (Codex review 034, finding 10), and any
            # earlier set-aside counts are added to, never overwritten.
            for k in [k for k in w.counts if k.startswith("ob_")]:
                w.counts["unattributed_" + k] = w.counts.get("unattributed_" + k, 0) + w.counts.pop(k)
        _disease.load_rows(w, arrays, alive_ids)             # per-band rows (22 Nov 2026)
        from .sim import customs as _customs
        _customs.widen(w)                                    # "response to epidemics" (M4a) for older saves
        from .sim import land as _land                       # the land answers back (M4a): older saves start untouched
        kept = {k: getattr(w, k, None) for k in _land.BAND_ARRAYS}
        for k in _land.BAND_ARRAYS:
            setattr(w, k, None)
        _land.init(w)
        for k in _land.ARRAYS:
            if k in _land.BAND_ARRAYS:
                a = kept[k]
                if a is not None:
                    _set_rows(w, k, a)
            elif "land_" + k in arrays:
                setattr(w, k, np.asarray(arrays["land_" + k], dtype=getattr(w, k).dtype))
        _land._band_rows(w)                                  # (rows of another shape start afresh)
        if getattr(w, "tech_prev_prac", None) is not None and getattr(w, "tech_prev_dep", None) is None:
            _set_rows(w, "tech_prev_dep", _copy_rows(w, w.tech_prev_prac))   # older saves: any practice counts
        if getattr(w, "tech_prev_prac", None) is not None and getattr(w, "tech_prev_wood", None) is None:
            ids, rows = w.tech_prev_prac.by_id()                            # older saves: any wood technique practised
            a = _rows_like(w, (), bool, False)
            a.load_rows(ids, rows[:, _tech.WOOD_TECHS].any(axis=1))
            _set_rows(w, "tech_prev_wood", a)
        if "treasury" in arrays:                            # rulers' stores (trade stage 4b)
            w.treasury = np.asarray(arrays["treasury"], dtype=np.float64)
        if led:
            w.goods_ledger = {k: dict(v) for k, v in led.items()}
        w.people = People.from_arrays(_prefixed(arrays, "p_"))
        _drop(arrays, prefix="p_")
        _trace("load: people built")
        w.groups = Groups.from_arrays(_prefixed(arrays, "g_"))
        _drop(arrays, prefix="g_")
        _trace("load: groups built")
        if "language" in meta:                   # schema 1 (M0) saves: everyone speaks the proto-language
            language.from_json(w, meta["language"])
            w.custom_log = ({int(k): v for k, v in meta["custom_log"].items()} if "custom_log" in meta
                            else meta.get("_custom_log", {}))
            w.hazards = meta["hazards"]
            w.timing = meta.get("timing", {})
            w.log_strides = meta.get("log_strides", {})
        if "farming" in meta:
            farming.from_json(w, meta["farming"])
        if "surplus" in meta:
            surplus.from_json(w, meta["surplus"])
        from .sim import trade as _tr
        _tr.from_json(w, meta.get("trade"))
        if "polity" in meta:
            polity.from_json(w, meta["polity"], arrays)      # the log from its arrays (schema 7) or the old rows
            _drop(arrays, "polity_log_i", "polity_log_f")
        if "conflict" in meta:
            conflict.from_json(w, meta["conflict"])
        w.people.languages = w.languages
        w.people_changed()
        w._pool = None
        w.bands_changed()
        _trace("load: world built")
        return w


def save(w: World, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = to_bytes(w)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        for k in range(BACKUPS - 1, 0, -1):
            older = path.with_name(f"{path.stem}.bak{k}{path.suffix}")
            newer = path.with_name(f"{path.stem}.bak{k + 1}{path.suffix}")
            if older.exists():
                os.replace(older, newer)
        os.replace(path, path.with_name(f"{path.stem}.bak1{path.suffix}"))
    os.replace(tmp, path)
    return path


def load(path, planet=None) -> World:
    return from_file(path, planet)       # read from disk as it is parsed (Codex review 041, finding 3)


def _recent_events(w) -> str:
    h = hashlib.sha256()
    from . import params as P
    since = w.t - P.PLACE_CHECK_YEARS * P.TICKS_PER_YEAR
    i = len(w.events) - 1
    while i >= 0:
        e = w.events[i]
        if e["t"] < since:
            break
        h.update(json.dumps(_jsonable(e), sort_keys=True).encode())
        i -= 1
    return h.hexdigest()


def digest(w: World) -> str:
    """Fingerprint of the complete simulation state, for exact-replay checks."""
    h = hashlib.sha256()
    for k, v in sorted(w.people.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    for k, v in sorted(w.groups.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    _tech_scribes(w)
    _band_rows_digest(w, h)
    _land_mod = __import__("origins.sim.land", fromlist=["ARRAYS"])
    for arr in (w.stock, w.stock_broad, w.known, w.region_z, w.hazard_food, w.immune,
                w.polity_of, w.polity_via, w.conquered_at,
                *__import__("origins.sim.trade", fromlist=["x"]).partner_state(w).values(), w.treasury,
              *[getattr(w, k) for k in _land_mod.ARRAYS
                if k not in _land_mod.BAND_ARRAYS and getattr(w, k, None) is not None],
              *[getattr(w, k) for k in __import__("origins.sim.disease", fromlist=["ARRAYS"]).ARRAYS
                if getattr(w, k, None) is not None],
              *(__import__("origins.sim.disease", fromlist=["x"]).save_rows(w).values()
                if getattr(w, "dz_slots", None) is not None else ()),
              __import__("origins.sim.disease", fromlist=["x"]).log_array(w)):
        h.update(np.ascontiguousarray(arr).tobytes())
    for k, v in sorted(__import__("origins.sim.minorlog", fromlist=["x"]).arrays(w).items()):   # the compact log
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    for k, v in sorted(w.bands.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    small = {"t": w.t, "counts": w.counts, "ledger": w.ledger, "goods_ledger": getattr(w, "goods_ledger", None),
             "bands": [dataclasses.asdict(b) for b in w.bands.live.values()], "band_strings": w.bands.strings,
             "rng": {k: g.bit_generator.state for k, g in w.rng.items()}, "n_events": len(w.events),
             "last_event": w.events[-1] if w.events else None,
             "language": language.to_json(w), "hazards": w.hazards, "farming": farming.to_json(w),
             "disease": __import__("origins.sim.disease", fromlist=["x"]).to_json(w),
             "places": __import__("origins.sim.places", fromlist=["x"]).to_json(w),
             "tech_writing_log": getattr(w, "tech_writing_log", []),
             "tech_firsts": getattr(w, "tech_firsts", {}),
             # the events of the last PLACE_CHECK_YEARS, which the places pass reads (conquests and whom they moved),
             # not only the count and the last event (Codex review 035, finding 2)
             "recent_events": _recent_events(w),
             "polity": polity.to_json(w, with_log=False), "conflict": conflict.to_json(w),
             "partner_dropped": getattr(w, "partner_dropped", {}),
             "routes_seen": sorted(getattr(w, "routes_seen", set())),
             "trade_links": getattr(w, "trade_links", []),
             "evaded_seen": sorted(getattr(w, "evaded_seen", set())),
             "rows_kept": sorted(getattr(w, "rows_kept", set()))}
    h.update(json.dumps(_jsonable(small), sort_keys=True).encode())
    for a in polity.log_arrays(w).values():               # the polity log, by its table (29 November 2026)
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()[:20]
