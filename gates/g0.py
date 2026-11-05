"""Gate G0 — 'the first people survive' (behaviour 1). See M0_SPECIFICATION_v1 section 11.

Usage (from the project folder):
  python -m gates.g0 runs  --worlds 1-5 --seeds 1-20 --years 2000 --workers 2
  python -m gates.g0 shock --worlds 1-5
  python -m gates.g0 report

Each run is written to gates/results/ as it finishes, so an interrupted gate
can be resumed; completed runs are not repeated.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "gates" / "results"

_planets = {}


def _planet(ws):
    from origins.worldgen import generate
    if ws not in _planets:
        _planets[ws] = generate(ws)
    return _planets[ws]


def _env():
    return {"python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.platform(),
            "machine": platform.machine()}


def run_one(ws: int, rs: int, years: int) -> dict:
    from origins import engine, explain, persist
    from origins.sim import observe
    from origins.state import World
    path = OUT / f"run_w{ws}_s{rs}_{years}y.json"
    if path.exists():
        old = json.loads(path.read_text())
        if old.get("status") == "completed":
            return {"file": path.name, "status": "kept"}
    start = time.perf_counter()
    w = World.new(ws, rs, _planet(ws))
    rec = {"world_seed": ws, "run_seed": rs, "requested_years": years, "env": _env(),
           "planet_fingerprint": w.planet.fingerprint, "start_cell": w.planet.start_cell}
    replay = None
    for y in range(years):
        engine.step(w, 4)
        if engine.extinct(w):
            break
        if rs == 1 and y + 1 == min(1000, years):
            twin = persist.from_bytes(persist.to_bytes(w), w.planet)
            engine.step(w, 40)
            engine.step(twin, 40)
            replay = persist.digest(w) == persist.digest(twin)
            del twin
    rec["completed_years"] = len(w.yearly)
    rec["extinct"] = engine.extinct(w)
    rec["extinct_year"] = w.year if rec["extinct"] else None
    rec["seconds"] = round(time.perf_counter() - start, 1)
    rec["invariant_failures"] = len(w.invariant_failures)
    rec["invariant_examples"] = w.invariant_failures[:5]
    rec["replay_check"] = replay
    keys = ["population", "individuals", "groups", "bands", "occupied_cells", "known_cells",
            "capacity_occupied", "food_ratio", "mean_condition", "births", "deaths", "median_band"]
    rec["yearly"] = {k: [r[k] for r in w.yearly] for k in keys}
    rec["life_table"] = observe.life_table(w)
    rec["counts"] = w.counts
    rec["events"] = {}
    for e in w.events:
        rec["events"][e["kind"]] = rec["events"].get(e["kind"], 0) + 1
    # explainability sample
    rng = np.random.default_rng([ws, rs, 99])
    p = w.people
    dead = np.nonzero(p.death[:p.n] >= 0)[0]
    sample = [{"death": int(i)} for i in (rng.choice(dead, size=min(100, len(dead)), replace=False) if len(dead) else [])]
    sample += [{"event": e["id"]} for e in w.events if e["kind"] in ("fission", "group_hunger_deaths", "merge", "band_extinct")][:150]
    ok = [explain.resolvable(w, r) for r in sample]
    rec["explain_checked"] = len(ok)
    rec["explain_resolvable"] = int(sum(ok))
    hunger = [r for r in sample if "death" in r and p.cause[r["death"]] == 2]
    rec["example_hunger_chain"] = explain.chain(w, hunger[0]) if hunger else None
    rec["status"] = "completed"
    path.write_text(json.dumps(rec))
    return {"file": path.name, "status": "completed", "seconds": rec["seconds"]}


def run_shock(ws: int, rs: int = 1, at_year: int = 800, horizon: int = 900) -> dict:
    """Paired runs: identical until the shock; then wild food x0.6 for 3 years in one populated region.
    Uses the first history (from rs upward) on this planet that is still alive at the shock year."""
    from origins import engine, interventions, persist
    from origins.state import World
    path = OUT / (f"shock_w{ws}.json" if at_year == 800 else f"shock_w{ws}_y{at_year}.json")
    if path.exists():
        return {"file": path.name, "status": "kept"}
    for rs in range(rs, rs + 20):
        w = World.new(ws, rs, _planet(ws))
        engine.step(w, 4 * at_year)
        if not engine.extinct(w):
            break
    sizes = w.band_sizes()
    occ = {}
    for b in w.living_bands():
        occ[b.cell] = occ.get(b.cell, 0) + sizes[b.id]
    centre = max(occ, key=lambda c: (occ[c], -c))
    cells = interventions.cells_within(w, centre, 2)
    control = persist.from_bytes(persist.to_bytes(w), w.planet)
    interventions.food_shock(w, cells, 0.6, 12, "gate G0 shock test: three-year 40% drop in wild food")
    cellset = set(int(c) for c in cells)
    pre_pop = float(sum(sizes[b.id] for b in control.living_bands() if b.cell in cellset))

    def area_stats(x):
        s = x.band_sizes()
        pop = sum(s[b.id] for b in x.living_bands() if b.cell in cellset)
        return float(pop)

    def track(x, years):
        series, hunger, births = [], [], []
        p = x.people
        idx = np.array(sorted(cellset))
        for _ in range(years):
            d0 = x.cell_hunger[idx].sum()
            b0 = x.cell_births[idx].sum()
            engine.step(x, 4)
            series.append(area_stats(x))
            hunger.append(float(x.cell_hunger[idx].sum() - d0))      # in the shocked area only
            births.append(float(x.cell_births[idx].sum() - b0))
        return series, hunger, births

    yrs = horizon - at_year
    s_ser, s_h, s_b = track(w, yrs)
    c_ser, c_h, c_b = track(control, yrs)
    rec = {"world_seed": ws, "run_seed": rs, "at_year": at_year, "cells": len(cells),
           "pre_shock_area_pop": pre_pop,
           "shocked_area_pop": s_ser, "control_area_pop": c_ser,
           "shock_hunger_deaths_3y": sum(s_h[:3]), "control_hunger_deaths_3y": sum(c_h[:3]),
           "shock_births_3y": sum(s_b[:3]), "control_births_3y": sum(c_b[:3]),
           "intervened_flag": w.intervened, "status": "completed"}
    path.write_text(json.dumps(rec))
    return {"file": path.name, "status": "completed"}


def _range(s: str):
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["runs", "shock", "report", "one"])
    ap.add_argument("--worlds", default="1-5")
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--years", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--at", type=int, default=800, help="shock year")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g0_report import report
        print(report(OUT))
        return
    if a.what == "one":
        ws, rs = _range(a.worlds)[0], _range(a.seeds)[0]
        print(run_one(ws, rs, a.years), flush=True)
        return
    jobs = ([(ws, rs, a.years) for ws in _range(a.worlds) for rs in _range(a.seeds)] if a.what == "runs"
            else [(ws, 1, a.at, a.at + 100) for ws in _range(a.worlds)])
    fn = run_one if a.what == "runs" else run_shock
    with cf.ProcessPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(fn, *j): j for j in jobs}
        for f in cf.as_completed(futs):
            try:
                print(futs[f], f.result(), flush=True)
            except Exception as exc:
                print(futs[f], "FAILED", repr(exc), flush=True)


if __name__ == "__main__":
    main()
