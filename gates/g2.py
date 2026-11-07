"""Gate G2 — 'farming is an option, not a destiny'. See docs/M2_SPECIFICATION_v1.md section 11.

Each history runs until 3,000 years after its first farming village, or to 25,000 years.
Knock-out histories ("--no-storage") run with food storage turned off.

  python -m gates.g2 run --jobs 1:1,2:1 --workers 2 [--no-storage]
  python -m gates.g2 report

Results go to gates/results_g2/. Checkpoints make sliced runs exact, as in G1.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gates.g0 import _env, _planet  # noqa: E402
from gates.g1 import landmass, sample_state  # noqa: E402

OUT = ROOT / "gates" / "results_g2"
MAX_YEARS = 25_000
AFTER_FIRST = 3_000
FARM_EVENTS = ("first_tending", "first_cultivation", "first_domestication", "first_farming_village")


def new_probe():
    return {"demog": [], "villages": [], "samples": {}, "violations": 0}


def probe(w, pr):
    """Every 25 years: farmers vs foragers (people, births, cells); villages and their farming."""
    from origins.sim import farming
    if w.year % 25:
        return
    sizes = w.band_sizes()
    cells_f, cells_v = set(), set()
    pop_f = pop_v = 0.0
    nv = 0
    for b in w.living_bands():
        if w.farm_share[b.id] >= 0.5:
            cells_v.add(b.cell)
            pop_v += sizes[b.id]
            nv += 1
            kp, vp, ka, va = farming.best(w, b)
            if max(vp, va) <= 0:
                pr["violations"] += 1          # a village with nothing to farm
        elif w.farm_share[b.id] < 0.1:
            cells_f.add(b.cell)
            pop_f += sizes[b.id]
    births_v = float(w.cell_births[sorted(cells_v)].sum()) if cells_v else 0.0
    births_f = float(w.cell_births[sorted(cells_f)].sum()) if cells_f else 0.0
    c = w.counts
    pr["demog"].append([w.year, round(pop_f), len(cells_f), births_f, round(pop_v), len(cells_v), births_v, nv,
                        c.get("births_forager", 0), c.get("py_forager", 0.0), c.get("births_village", 0),
                        c.get("py_village", 0.0)])
    if w.year % 500 == 0:
        wild, suit = farming.land_tables(w)
        not_wild = 0
        for b in w.living_bands():
            if w.farm_share[b.id] >= 0.5:
                kp, vp, ka, va = farming.best(w, b)
                k = kp if vp >= va else ka
                not_wild += int(not wild[b.cell, k])
        pr["villages"].append([w.year, nv, not_wild])
    if w.year % 1000 == 0:
        pr["samples"][str(w.year)] = sample_state(w)


def finish(w, ws, rs, seconds, pr, storage, status="completed"):
    from origins import engine, explain
    from origins.sim import farming, observe
    pl = w.planet
    rec = {"world_seed": ws, "run_seed": rs, "storage": storage, "env": _env(), "planet_fingerprint": pl.fingerprint,
           "completed_years": len(w.yearly), "extinct": engine.extinct(w), "seconds": round(seconds, 1),
           "invariant_failures": len(w.invariant_failures), "invariant_examples": w.invariant_failures[:5],
           "status": status}
    keys = ["population", "individuals", "groups", "bands", "occupied_cells", "food_ratio", "births", "deaths"]
    rec["yearly"] = {k: [r[k] for r in w.yearly][::10] for k in keys}
    rec["life_table"] = observe.life_table(w)
    rec["counts"] = w.counts
    rec["events"] = {}
    for e in w.events:
        rec["events"][e["kind"]] = rec["events"].get(e["kind"], 0) + 1
    fv = w.first_village
    rec["first_village_year"] = w.events[fv]["data"]["year"] if fv is not None else None
    rec["firsts"] = {sp: {st: w.events[e]["t"] // 4 for st, e in v.items()} for sp, v in w.farm_firsts.items()}
    # check 2: tending begins only where the species grows wild
    wild, suit = farming.land_tables(w)
    bad = 0
    for e in w.events:
        if e["kind"] == "first_tending":
            k = [farming.NAMES[s] for s in farming.SPECIES].index(e["data"]["species"])
            bad += int(not wild[e["cell"], k])
    rec["tending_outside_wild"] = bad
    rec["villages_without_crop"] = pr["violations"]
    rec["demog"] = pr["demog"]
    rec["villages"] = pr["villages"]
    rec["samples"] = pr["samples"]
    rec["samples"][str(w.year)] = sample_state(w)
    # foragers left at the end: land held by bands that do not farm, and its wild food capacity
    lab = landmass(pl)
    forager_cells = sorted({b.cell for b in w.living_bands() if w.farm_share[b.id] < 0.1})
    rec["forager_cells_end"] = len(forager_cells)
    rec["forager_capacity_end"] = float(pl.capacity[forager_cells].sum()) if forager_cells else 0.0
    rec["village_cells_end"] = len({b.cell for b in w.living_bands() if w.farm_share[b.id] >= 0.5})
    rec["spec_log"] = w.spec_log[-6000:]
    rec["gini_log"] = w.gini_log[-6000:]
    rec["village_since"] = {str(b.id): b.village_since for b in w.living_bands() if b.village}
    # explainability of farming events
    sample = [{"event": e["id"]} for e in w.events if e["kind"] in FARM_EVENTS][:60]
    p = w.people
    rng = np.random.default_rng([ws, rs, 99])
    dead = np.nonzero(p.death[:p.n] >= 0)[0]
    sample += [{"death": int(i)} for i in (rng.choice(dead, size=min(100, len(dead)), replace=False) if len(dead) else [])]
    ok = [explain.resolvable(w, r) for r in sample]
    rec["explain_checked"], rec["explain_resolvable"] = len(ok), int(sum(ok))
    rec["landmasses"] = int(lab.max()) + 1
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "" if storage else "_nostore"
    (OUT / f"run_w{ws}_s{rs}{tag}.json").write_text(json.dumps(rec))


def done(w) -> bool:
    from origins import engine
    if engine.extinct(w) or len(w.yearly) >= MAX_YEARS:
        return True
    fv = w.first_village
    return fv is not None and w.year >= w.events[fv]["data"]["year"] + AFTER_FIRST


def apply_overrides():
    """Parameter overrides for a gate run, from the ORIGINS_PARAMS environment variable (JSON)."""
    import os
    from origins import params
    for k, v in json.loads(os.environ.get("ORIGINS_PARAMS", "{}") or "{}").items():
        if not hasattr(params, k):
            raise SystemExit(f"unknown parameter {k}")
        setattr(params, k, v)


def worker(jobs, budget, ckpt: Path, storage: bool):
    from origins import engine, params, persist
    from origins.state import World
    apply_overrides()
    params.STORAGE = storage
    tag = "" if storage else "_nostore"
    t_end = time.time() + budget
    for ws, rs in jobs:
        if (OUT / f"run_w{ws}_s{rs}{tag}.json").exists():
            continue
        cp, meta = ckpt / f"w{ws}_s{rs}{tag}.zip", ckpt / f"w{ws}_s{rs}{tag}.json"
        start = time.time()
        if cp.exists():
            w = persist.from_bytes(cp.read_bytes(), _planet(ws))
            m = json.loads(meta.read_text())
            spent, pr = m["seconds"], m["probe"]
        else:
            w = World.new(ws, rs, _planet(ws))
            spent, pr = 0.0, new_probe()
        while not done(w):
            engine.step(w, 4)
            probe(w, pr)
            if time.time() > t_end:
                tmp = cp.with_suffix(".tmp")
                tmp.write_bytes(persist.to_bytes(w, fast=True))
                tmp.replace(cp)
                meta.write_text(json.dumps({"seconds": spent + time.time() - start, "year": w.year, "probe": pr}))
                print(f"w{ws} s{rs}{tag}: checkpoint at year {w.year}", flush=True)
                return
        finish(w, ws, rs, spent + time.time() - start, pr, storage)
        print(f"w{ws} s{rs}{tag}: completed at year {w.year} in {spent + time.time() - start:.0f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "report"])
    ap.add_argument("--jobs", default="")
    ap.add_argument("--worlds", default="1-5")
    ap.add_argument("--years", type=int, default=MAX_YEARS)        # accepted for the workflow; the gate sets its own end
    ap.add_argument("--budget", type=float, default=20000)
    ap.add_argument("--ckpt", default=str(ROOT / "gates" / "ckpt_g2"))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--no-storage", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g2_report import report
        print(report(OUT))
        return
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    storage = not a.no_storage
    if a.workers == 1:
        worker(jobs, a.budget, ck, storage)
        return
    shares = [jobs[k::a.workers] for k in range(a.workers)]
    procs = [mp.Process(target=worker, args=(s, a.budget, ck, storage)) for s in shares]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


if __name__ == "__main__":
    main()
