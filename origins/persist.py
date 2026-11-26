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
    now = 0.0
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS"):
                now = int(line.split()[1]) / 1e6
    except OSError:
        pass
    print(f"[mem] {label}: {now:.2f} GB in use, {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB peak",
          flush=True)


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
        "farming": farming.to_json(w), "surplus": surplus.to_json(w), "polity": polity.to_json(w), "trade": __import__("origins.sim.trade", fromlist=["x"]).to_json(w),
        "conflict": conflict.to_json(w), "timing": w.timing, "first_herders": getattr(w, "first_herders", None), "tech_firsts": getattr(w, "tech_firsts", {}), "tech_writing_log": getattr(w, "tech_writing_log", []), "goods_ledger": getattr(w, "goods_ledger", None), "log_strides": w.log_strides,
        "disease": __import__("origins.sim.disease", fromlist=["x"]).to_json(w),
        "places": __import__("origins.sim.places", fromlist=["x"]).to_json(w),
        "dz_counts_split": True,      # named diseases count G1 exposure under their own keys (review 031; review 034)
    }
    arrays = {"stock": w.stock, "stock_broad": w.stock_broad, "known": w.known, "discovered_by": w.discovered_by,
              "discovered_at": w.discovered_at, "food_modifier": w.food_modifier,
              "intervention_event": w.intervention_event, "cell_hunger": w.cell_hunger, "cell_births": w.cell_births,
              "customs": w.customs, "neutral": w.neutral, "hazard_food": w.hazard_food,
              "hazard_event": w.hazard_event, "immune": w.immune,
              "skill": w.skill, "farm_share": w.farm_share, "crop_store": w.crop_store,
              "still_years": w.still_years, "forage_rr": w.forage_rr, "spec": w.spec,
              "polity_of": w.polity_of, "polity_via": w.polity_via, "conquered_at": w.conquered_at,
              "herder_since": w.herder_since, "farm_rr_real": w.farm_rr_real, "farm_rr_cell": w.farm_rr_cell,
              "farm_rr_lost": w.farm_rr_lost if getattr(w, "farm_rr_lost", None) is not None else np.zeros(0), "tech": w.tech, "tech_record": w.tech_record, "tech_scribes": _tech_scribes(w),
              "goods": w.goods,
              "goods_reached": w.goods_reached, "treasury": w.treasury,
              "tech_prev_prac": w.tech_prev_prac if getattr(w, "tech_prev_prac", None) is not None else np.zeros((0, 0), bool),
              "tech_prev_dep": w.tech_prev_dep if getattr(w, "tech_prev_dep", None) is not None else np.zeros((0, 0), bool),
              "tech_prev_mats": w.tech_prev_mats if getattr(w, "tech_prev_mats", None) is not None else np.zeros((0, 0), bool),
              "tech_prev_wood": w.tech_prev_wood if getattr(w, "tech_prev_wood", None) is not None else np.zeros(0, bool),
              "trade_in": w.trade_in if getattr(w, "trade_in", None) is not None else np.zeros(0)}
    from .sim import land as _land
    arrays.update({"land_" + k: getattr(w, k) for k in _land.ARRAYS if getattr(w, k, None) is not None})
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
    arrays.update({"p_" + k: v for k, v in w.people.arrays().items()})
    arrays.update({"g_" + k: v for k, v in w.groups.arrays().items()})
    arrays.update({"b_" + k: v for k, v in w.bands.arrays().items()})
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED, compresslevel=1 if fast else None) as z:
        # meta.json is written part by part: the same bytes as one json.dumps, without the whole string in memory
        # at once, and each part's size known as written (Codex review 041, finding 2)
        parts = []
        with z.open("meta.json", "w", force_zip64=True) as out:
            out.write(b"{")
            for j, (k, v) in enumerate(_jsonable(meta).items()):
                b = (("," if j else "") + json.dumps(k) + ":" + json.dumps(v, separators=(",", ":"))).encode()
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
    import shutil
    import tempfile
    _trace("load: start")
    with zipfile.ZipFile(src) as z:
        meta = json.loads(z.read("meta.json"))
        _trace("load: meta.json parsed")
        with tempfile.TemporaryFile() as tmp:
            with z.open("arrays.npz") as f:
                shutil.copyfileobj(f, tmp, 16 << 20)
            tmp.seek(0)
            with np.load(tmp) as npz:
                arrays = {k: npz[k] for k in npz.files}
        _trace("load: arrays read")
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
    w.bands.load_arrays({k[2:]: v for k, v in arrays.items() if k.startswith("b_")}, meta.get("band_strings", []))
    _drop(arrays, prefix="b_")
    _trace("load: bands built")
    w.reveal_pending = set(meta["reveal_pending"])
    w.pending_restore = [(a, list(b), c) for a, b, c in meta.get("pending_restore", [])]
    for k in ("stock", "known", "discovered_by", "discovered_at", "food_modifier", "intervention_event",
              "cell_hunger", "cell_births", "customs", "neutral", "hazard_food", "hazard_event", "immune",
              "skill", "farm_share", "crop_store", "still_years", "forage_rr", "spec", "polity_of", "polity_via", "conquered_at",
              "herder_since", "stock_broad", "farm_rr_real", "farm_rr_cell", "farm_rr_lost"):
        if k in arrays:                      # older saves of this schema may lack optional arrays
            setattr(w, k, arrays[k])
    if getattr(w, "farm_rr_real", None) is None or len(w.farm_rr_real) != len(w.farm_share):
        w.farm_rr_real = np.full(len(w.farm_share), np.nan)      # before choices saw real yields (19 Nov 2026)
    if getattr(w, "farm_rr_cell", None) is None or len(w.farm_rr_cell) != len(w.farm_rr_real):
        w.farm_rr_cell = np.full(len(w.farm_rr_real), -1, dtype=np.int64)   # before review 021 (20 Nov 2026)
    if getattr(w, "farm_rr_lost", None) is None or len(w.farm_rr_lost) != len(w.farm_rr_real):
        w.farm_rr_lost = np.zeros(len(w.farm_rr_real))                  # before review 022 (20 Nov 2026)
    if getattr(w, "stock_broad", None) is None or len(w.stock_broad) != len(w.stock):
        from .sim import climate as _climate            # saves from before the broad-spectrum pool (14 Nov 2026)
        w.stock_broad = _climate.broad_max(w).copy()
    _trace("load: per-band arrays built")
    from .sim import technology as _tech
    if "tech" in arrays:
        w.tech = arrays["tech"]
    if getattr(w, "tech", None) is None or w.tech.shape[0] < len(w.farm_share) or w.tech.shape[1] != _tech.K:
        t = np.zeros((len(w.farm_share), _tech.K), dtype=np.float32)    # saves from before the technology network
        old = getattr(w, "tech", None)
        if old is not None and old.shape[1] == _tech.K:
            t[:len(old)] = old
        w.tech = t
    rec = arrays.get("tech_record")                  # saves from before written records (14 Nov 2026): none kept
    w.tech_record = np.zeros_like(w.tech)
    if rec is not None and rec.shape[1] == _tech.K:
        w.tech_record[:min(len(rec), len(w.tech))] = rec[:len(w.tech)]
    rec = None
    _drop(arrays, "tech_record")
    sc = arrays.get("tech_scribes")                  # saves from before scribes (20 Nov 2026): today's specialists
    w.tech_scribes = None
    if sc is not None and np.asarray(sc).size:
        w.tech_scribes = np.array(sc, dtype=float)
    if len(getattr(w, "herder_since", ())) < len(w.farm_share):    # saves from before pastoralism (M4a)
        h = np.full(len(w.farm_share), -1.0)
        h[:len(getattr(w, "herder_since", ()))] = getattr(w, "herder_since", np.zeros(0))
        w.herder_since = h
    w.first_herders = meta.get("first_herders")
    w.tech_firsts = dict(meta.get("tech_firsts", {}))
    w.tech_writing_log = [list(r) for r in meta.get("tech_writing_log", [])]    # from review 032; older saves: none
    _trace("load: technology built")
    from .sim import trade as _trade                  # goods (M4a trade); saves from before have none
    g = arrays.get("goods")
    led = meta.get("goods_ledger")
    _trade.init(w)
    if g is not None and g.shape[1] == _trade.G:
        w.goods = np.array(g, dtype=np.float64)        # exactly as saved (replay digest)
    else:
        _trade.grow(w, len(w.farm_share) - 1)
    alive_ids = [b.id for b in w.bands.live.values() if b.alive]
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
    _trade.grow(w, len(w.goods) - 1)                 # keeps every goods row (Codex review 013)
    g = None
    _drop(arrays, "goods", prefix="partner_")
    if "goods_reached" in arrays:                       # trade stage 3, after review 014
        w.goods_reached = np.asarray(arrays["goods_reached"], dtype=bool)
    else:
        w.goods_reached = None
        _trade.grow(w, len(w.goods) - 1)             # older saves: what a band holds has reached it
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
    _minor.load(w, {k: v for k, v in arrays.items() if k.startswith("minor_")})
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
    _disease.load_rows(w, arrays, [b.id for b in w.bands.live.values() if b.alive])   # per-band rows (22 Nov 2026)
    from .sim import customs as _customs
    _customs.widen(w)                                    # "response to epidemics" (M4a) for older saves
    from .sim import land as _land                       # the land answers back (M4a): older saves start untouched
    _land.init(w)
    for k in _land.ARRAYS:
        if "land_" + k in arrays:
            setattr(w, k, np.asarray(arrays["land_" + k], dtype=getattr(w, k).dtype))
    if "trade_in" in arrays and np.asarray(arrays["trade_in"]).size:   # last year's goods received (stage 5)
        w.trade_in = np.asarray(arrays["trade_in"], dtype=np.float64)
    for n_ in ("tech_prev_prac", "tech_prev_mats", "tech_prev_wood"):   # last year's practice, goods-held materials
        if n_ in arrays and np.asarray(arrays[n_]).size:                # (review 018) and wood work (review 022)
            setattr(w, n_, np.asarray(arrays[n_], dtype=bool))
    if "tech_prev_dep" in arrays and np.asarray(arrays["tech_prev_dep"]).size:   # practised on imports (review 035)
        w.tech_prev_dep = np.asarray(arrays["tech_prev_dep"], dtype=bool)
    elif getattr(w, "tech_prev_prac", None) is not None:
        w.tech_prev_dep = w.tech_prev_prac.copy()       # older saves: as before, any practice counts
    if getattr(w, "tech_prev_prac", None) is not None and getattr(w, "tech_prev_wood", None) is None:
        from .sim import technology as _tech                            # older saves: any wood technique practised
        w.tech_prev_wood = w.tech_prev_prac[:, _tech.WOOD_TECHS].any(axis=1)
    if "treasury" in arrays:                            # rulers' stores (trade stage 4b)
        w.treasury = np.asarray(arrays["treasury"], dtype=np.float64)
    if led:
        w.goods_ledger = {k: dict(v) for k, v in led.items()}
    from .sim import customs as _customs
    if w.customs.shape[1] < len(_customs.NAMES):          # saves from before a custom was added: it starts at variant 0
        c = np.zeros((len(w.customs), len(_customs.NAMES)), dtype=w.customs.dtype)
        c[:, :w.customs.shape[1]] = w.customs
        w.customs = c
    w.people = People.from_arrays({k[2:]: v for k, v in arrays.items() if k.startswith("p_")})
    _drop(arrays, prefix="p_")
    _trace("load: people built")
    w.groups = Groups.from_arrays({k[2:]: v for k, v in arrays.items() if k.startswith("g_")})
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
        polity.from_json(w, meta["polity"])
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
    for arr in (w.stock, w.stock_broad, w.known, w.region_z, w.customs, w.neutral, w.hazard_food, w.immune, w.skill, w.farm_share,
                w.crop_store, w.still_years, w.forage_rr, w.spec, w.polity_of, w.polity_via, w.conquered_at, w.herder_since, w.farm_rr_real, w.farm_rr_cell,
                getattr(w, "farm_rr_lost", None) if getattr(w, "farm_rr_lost", None) is not None else np.zeros(0), w.tech,
                w.tech_record, _tech_scribes(w), w.goods, *__import__("origins.sim.trade", fromlist=["x"]).partner_state(w).values(), w.goods_reached, w.treasury,
              *[getattr(w, n_, None) if getattr(w, n_, None) is not None else np.zeros((0, 0), bool)
                for n_ in ("tech_prev_prac", "tech_prev_mats", "tech_prev_dep")],
              getattr(w, "tech_prev_wood", None) if getattr(w, "tech_prev_wood", None) is not None else np.zeros(0, bool),
              getattr(w, "trade_in", None) if getattr(w, "trade_in", None) is not None else np.zeros(0),
              *[getattr(w, k) for k in __import__("origins.sim.land", fromlist=["ARRAYS"]).ARRAYS
                if getattr(w, k, None) is not None],
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
             "polity": polity.to_json(w), "conflict": conflict.to_json(w),
             "partner_dropped": getattr(w, "partner_dropped", {}),
             "routes_seen": sorted(getattr(w, "routes_seen", set())),
             "trade_links": getattr(w, "trade_links", []),
             "evaded_seen": sorted(getattr(w, "evaded_seen", set()))}
    h.update(json.dumps(_jsonable(small), sort_keys=True).encode())
    return h.hexdigest()[:20]
