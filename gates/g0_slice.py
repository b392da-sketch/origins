"""Run gate G0 histories in time-limited slices with checkpoints.

For machines where a process cannot run for long: each call works for at most
--budget seconds, saves a checkpoint, and the next call continues exactly
where it stopped (save/load is exact). Finished histories are written in the
same format as gates/g0.py.

  python -m gates.g0_slice --jobs 5:1,5:2,... --budget 160 --ckpt /path/to/dir --workers 2
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
from gates.g0 import OUT, _env, _planet  # noqa: E402


def finish(w, ws, rs, years, seconds):
    from origins import engine, explain
    from origins.sim import observe
    rec = {"world_seed": ws, "run_seed": rs, "requested_years": years, "env": _env(),
           "planet_fingerprint": w.planet.fingerprint, "start_cell": w.planet.start_cell,
           "completed_years": len(w.yearly), "extinct": engine.extinct(w),
           "extinct_year": w.year if engine.extinct(w) else None, "seconds": round(seconds, 1),
           "invariant_failures": len(w.invariant_failures), "invariant_examples": w.invariant_failures[:5],
           "replay_check": None, "sliced": True}
    keys = ["population", "individuals", "groups", "bands", "occupied_cells", "known_cells",
            "capacity_occupied", "food_ratio", "mean_condition", "births", "deaths", "median_band"]
    rec["yearly"] = {k: [r[k] for r in w.yearly] for k in keys}
    rec["life_table"] = observe.life_table(w)
    rec["counts"] = w.counts
    rec["events"] = {}
    for e in w.events:
        rec["events"][e["kind"]] = rec["events"].get(e["kind"], 0) + 1
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
    (OUT / f"run_w{ws}_s{rs}_{years}y.json").write_text(json.dumps(rec))


def worker(jobs, years, budget, ckpt: Path):
    from origins import engine, persist
    from origins.state import World
    t_end = time.time() + budget
    for ws, rs in jobs:
        if (OUT / f"run_w{ws}_s{rs}_{years}y.json").exists():
            continue
        if time.time() > t_end - 5:
            return
        cp, meta = ckpt / f"w{ws}_s{rs}.zip", ckpt / f"w{ws}_s{rs}.json"
        start = time.time()
        if cp.exists():
            w = persist.from_bytes(cp.read_bytes(), _planet(ws))
            spent = json.loads(meta.read_text())["seconds"]
        else:
            w = World.new(ws, rs, _planet(ws))
            spent = 0.0
        while len(w.yearly) < years and not engine.extinct(w):
            engine.step(w, 4)
            if time.time() > t_end:
                tmp = cp.with_suffix(".tmp")
                tmp.write_bytes(persist.to_bytes(w))
                tmp.replace(cp)
                meta.write_text(json.dumps({"seconds": spent + time.time() - start, "year": len(w.yearly)}))
                print(f"w{ws} s{rs}: checkpoint at year {len(w.yearly)}", flush=True)
                return
        finish(w, ws, rs, years, spent + time.time() - start)
        print(f"w{ws} s{rs}: completed ({'extinct' if engine.extinct(w) else 'survived'})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--years", type=int, default=2000)
    ap.add_argument("--budget", type=float, default=160)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    shares = [jobs[k::a.workers] for k in range(a.workers)]
    procs = [mp.Process(target=worker, args=(s, a.years, a.budget, ck)) for s in shares]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


if __name__ == "__main__":
    main()
