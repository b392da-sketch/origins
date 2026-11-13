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
        "farming": farming.to_json(w), "surplus": surplus.to_json(w), "polity": polity.to_json(w),
        "conflict": conflict.to_json(w), "timing": w.timing, "first_herders": getattr(w, "first_herders", None), "tech_firsts": getattr(w, "tech_firsts", {}), "log_strides": w.log_strides,
    }
    arrays = {"stock": w.stock, "known": w.known, "discovered_by": w.discovered_by,
              "discovered_at": w.discovered_at, "food_modifier": w.food_modifier,
              "intervention_event": w.intervention_event, "cell_hunger": w.cell_hunger, "cell_births": w.cell_births,
              "customs": w.customs, "neutral": w.neutral, "hazard_food": w.hazard_food,
              "hazard_event": w.hazard_event, "immune": w.immune,
              "skill": w.skill, "farm_share": w.farm_share, "crop_store": w.crop_store,
              "still_years": w.still_years, "forage_rr": w.forage_rr, "spec": w.spec,
              "polity_of": w.polity_of, "polity_via": w.polity_via, "conquered_at": w.conquered_at,
              "herder_since": w.herder_since, "tech": w.tech}
    arrays.update({"p_" + k: v for k, v in w.people.arrays().items()})
    arrays.update({"g_" + k: v for k, v in w.groups.arrays().items()})
    arrays.update({"b_" + k: v for k, v in w.bands.arrays().items()})
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED, compresslevel=1 if fast else None) as z:
        z.writestr("meta.json", json.dumps(_jsonable(meta), separators=(",", ":")))
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
        with z.open("arrays.npz", "w", force_zip64=True) as out:
            (np.savez if fast else np.savez_compressed)(out, **arrays)


def from_bytes(data: bytes, planet=None) -> World:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        meta = json.loads(z.read("meta.json"))
        arrays = dict(np.load(io.BytesIO(z.read("arrays.npz"))))
        if "events.jsonl" in z.namelist():
            with z.open("events.jsonl") as f:
                meta["events"] = EventStore(json.loads(line) for line in io.TextIOWrapper(f, encoding="utf-8") if line.strip())
        if "custom_log.jsonl" in z.namelist():
            with z.open("custom_log.jsonl") as f:
                meta["_custom_log"] = {int(r[0]): r[1] for r in (json.loads(line) for line in io.TextIOWrapper(f, encoding="utf-8") if line.strip())}
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
    w.reveal_pending = set(meta["reveal_pending"])
    w.pending_restore = [(a, list(b), c) for a, b, c in meta.get("pending_restore", [])]
    for k in ("stock", "known", "discovered_by", "discovered_at", "food_modifier", "intervention_event",
              "cell_hunger", "cell_births", "customs", "neutral", "hazard_food", "hazard_event", "immune",
              "skill", "farm_share", "crop_store", "still_years", "forage_rr", "spec", "polity_of", "polity_via", "conquered_at",
              "herder_since"):
        if k in arrays:                      # older saves of this schema may lack optional arrays
            setattr(w, k, arrays[k])
    from .sim import technology as _tech
    if "tech" in arrays:
        w.tech = arrays["tech"]
    if getattr(w, "tech", None) is None or w.tech.shape[0] < len(w.farm_share) or w.tech.shape[1] != _tech.K:
        t = np.zeros((len(w.farm_share), _tech.K), dtype=np.float32)    # saves from before the technology network
        old = getattr(w, "tech", None)
        if old is not None and old.shape[1] == _tech.K:
            t[:len(old)] = old
        w.tech = t
    if len(getattr(w, "herder_since", ())) < len(w.farm_share):    # saves from before pastoralism (M4a)
        h = np.full(len(w.farm_share), -1.0)
        h[:len(getattr(w, "herder_since", ()))] = getattr(w, "herder_since", np.zeros(0))
        w.herder_since = h
    w.first_herders = meta.get("first_herders")
    w.tech_firsts = dict(meta.get("tech_firsts", {}))
    from .sim import customs as _customs
    if w.customs.shape[1] < len(_customs.NAMES):          # saves from before a custom was added: it starts at variant 0
        c = np.zeros((len(w.customs), len(_customs.NAMES)), dtype=w.customs.dtype)
        c[:, :w.customs.shape[1]] = w.customs
        w.customs = c
    w.people = People.from_arrays({k[2:]: v for k, v in arrays.items() if k.startswith("p_")})
    w.groups = Groups.from_arrays({k[2:]: v for k, v in arrays.items() if k.startswith("g_")})
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
    if "polity" in meta:
        polity.from_json(w, meta["polity"])
    if "conflict" in meta:
        conflict.from_json(w, meta["conflict"])
    w.people.languages = w.languages
    w.people_changed()
    w._pool = None
    w.bands_changed()
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
    with open(path, "rb") as f:
        return from_bytes(f.read(), planet)


def digest(w: World) -> str:
    """Fingerprint of the complete simulation state, for exact-replay checks."""
    h = hashlib.sha256()
    for k, v in sorted(w.people.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    for k, v in sorted(w.groups.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    for arr in (w.stock, w.known, w.region_z, w.customs, w.neutral, w.hazard_food, w.immune, w.skill, w.farm_share,
                w.crop_store, w.spec, w.polity_of, w.polity_via, w.conquered_at, w.herder_since, w.tech):
        h.update(np.ascontiguousarray(arr).tobytes())
    for k, v in sorted(w.bands.arrays().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    small = {"t": w.t, "counts": w.counts, "ledger": w.ledger,
             "bands": [dataclasses.asdict(b) for b in w.bands.live.values()], "band_strings": w.bands.strings,
             "rng": {k: g.bit_generator.state for k, g in w.rng.items()}, "n_events": len(w.events),
             "last_event": w.events[-1] if w.events else None,
             "language": language.to_json(w), "hazards": w.hazards, "farming": farming.to_json(w),
             "polity": polity.to_json(w), "conflict": conflict.to_json(w)}
    h.update(json.dumps(_jsonable(small), sort_keys=True).encode())
    return h.hexdigest()[:20]
