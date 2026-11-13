"""Gate G3 — 'scale needs institutions; conflict has causes and costs'. See docs/M3_SPECIFICATION_v1.md section 8.

Each history runs until AFTER_FIRST years after its first farming village (6,000 for G3; a request can set
"after_first" for a shorter trial), or to 30,000 years. Knock-out histories ("--no-institutions") run with
institutions switched off.

  python -m gates.g3 run --jobs 1:1,2:1 [--no-institutions]
  python -m gates.g3 report

Results go to gates/results_g3/. The records include everything G2 records (so M0-M2 can be re-checked), plus
polity logs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gates import g2  # noqa: E402
from gates.g0 import _planet  # noqa: E402

OUT = ROOT / "gates" / "results_g3"
MAX_YEARS = 30_000
POLITY_EVENTS = ("polity_founded", "polity_joined", "secession", "flight", "polity_ended", "seat_moved", "succession",
                 "institution_founded", "institution_lost", "first_simple_chiefdom", "first_complex_chiefdom",
                 "first_state", "war", "conquest")


def after_first() -> int:
    return int(os.environ.get("ORIGINS_AFTER_FIRST", "6000"))


def done(w) -> bool:
    from origins import engine
    if engine.extinct(w) or len(w.yearly) >= MAX_YEARS:
        return True
    fv = w.first_village
    return fv is not None and w.year >= w.events[fv]["data"]["year"] + after_first()


def finish(w, ws, rs, seconds, pr, institutions):
    from origins import explain, params
    rec = g2.finish(w, ws, rs, seconds, pr, params.STORAGE, write=False)
    rec["institutions"] = institutions
    rec["after_first"] = after_first()
    pl = w.polity_log
    rng = np.random.default_rng([ws, rs, 11])
    # keep whole polity histories: sample polities, not rows
    pids = sorted({r[1] for r in pl})
    if len(pids) > 1500:
        keep = set(int(x) for x in rng.choice(pids, 1500, replace=False))
        big = {r[1] for r in pl if r[2] >= 5}                  # always keep polities that ever held 5+ settlements
        keep |= big
        pl = [r for r in pl if r[1] in keep]
    rec["polity_log"] = pl
    rec["sec_stats"] = {str(k): v for k, v in w.sec_stats.items()}
    rec["polity_firsts"] = {k: w.events[e]["t"] // 4 for k, e in w.polity_firsts.items()}
    rec["polities_total"] = w.next_polity
    # chains of rule must be trees: count members whose chain loops (expected 0; Codex review 003 asked how the
    # depth helpers treat cycles, which should never occur)
    loops = 0
    for b in w.living_bands():
        pid = int(w.polity_of[b.id])
        if pid < 0 or pid not in w.polities:
            continue
        seat, seen, j = w.polities[pid].seat, set(), b.id
        while j != seat:
            if j in seen:
                loops += 1
                break
            seen.add(j)
            k = int(w.polity_via[j])
            if k < 0 or int(w.polity_of[k]) != pid:
                break
            j = k
    rec["polity_chain_loops"] = loops
    # conflict
    from origins.state import CAUSES
    fv = pr.get("fv_deaths")
    if fv:
        bc = (w.accum["deaths_by_cause"] - np.array(fv["by_cause"] + [0] * (len(CAUSES) - len(fv["by_cause"])))).tolist()
        ba = (w.accum["deaths"] - np.array(fv["by_age"])).tolist()
        rec["deaths_since_village"] = {"by_cause": dict(zip(CAUSES, bc)), "by_age": ba}
    rec["war_stats"] = {k: {str(b): v for b, v in d.items()} for k, d in w.war_stats.items()}
    wl = w.war_log
    if len(wl) > 8000:
        wl = [wl[i] for i in sorted(rng.choice(len(wl), 8000, replace=False))]
    rec["war_log"] = wl
    sample = [{"event": e["id"]} for e in w.events if e["kind"] in POLITY_EVENTS]
    if len(sample) > 400:
        sample = [sample[i] for i in sorted(rng.choice(len(sample), 400, replace=False))]
    ok = [explain.resolvable(w, r) for r in sample]
    rec["polity_explain_checked"], rec["polity_explain_resolvable"] = len(ok), int(sum(ok))
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "" if institutions else "_noinst"
    (OUT / f"run_w{ws}_s{rs}{tag}.json").write_text(json.dumps(rec))


def worker(jobs, budget, ckpt: Path, institutions: bool):
    from origins import engine, params, persist
    from origins.state import World
    g2.apply_overrides()
    params.INSTITUTIONS = institutions
    tag = "" if institutions else "_noinst"
    t_end = time.time() + budget
    for ws, rs in jobs:
        if (OUT / f"run_w{ws}_s{rs}{tag}.json").exists():
            continue
        cp, meta = ckpt / f"w{ws}_s{rs}{tag}.zip", ckpt / f"w{ws}_s{rs}{tag}.json"
        start = time.time()
        if cp.exists():
            w = persist.from_bytes(cp.read_bytes(), g2.resume_planet(cp, ws))
            m = json.loads(meta.read_text())
            spent, pr = m["seconds"], m["probe"]
        else:
            w = World.new(ws, rs, _planet(ws))
            spent, pr = 0.0, g2.new_probe()
        import resource
        while not done(w):
            engine.step(w, 4)
            g2.probe(w, pr)
            if w.year % 500 == 0:
                print(f"w{ws} s{rs}{tag}: year {w.year}, {w.population():,} people, {len(w.events):,} events, "
                      f"peak memory {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
            if w.first_village is not None and "fv_deaths" not in pr:
                # deaths so far, to measure causes of death in the farming era (check 7)
                pr["fv_deaths"] = {"by_cause": w.accum["deaths_by_cause"].tolist(), "by_age": w.accum["deaths"].tolist()}
            if time.time() > t_end:
                g2.save_planet(cp, w.planet)
                tmp = cp.with_suffix(".tmp")
                import gc
                gc.collect()
                t0 = time.time()
                persist.to_file(w, tmp, fast=True)
                print(f"checkpoint written in {time.time() - t0:.0f} s; peak memory "
                      f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
                tmp.replace(cp)
                meta.write_text(json.dumps({"seconds": spent + time.time() - start, "year": w.year, "probe": pr}))
                print(f"w{ws} s{rs}{tag}: checkpoint at year {w.year}", flush=True)
                return
        finish(w, ws, rs, spent + time.time() - start, pr, institutions)
        print(f"w{ws} s{rs}{tag}: completed at year {w.year} in {spent + time.time() - start:.0f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "report"])
    ap.add_argument("--jobs", default="")
    ap.add_argument("--years", type=int, default=MAX_YEARS)        # accepted for the workflow; the gate sets its own end
    ap.add_argument("--budget", type=float, default=20000)
    ap.add_argument("--ckpt", default=str(ROOT / "gates" / "ckpt_g3"))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--no-institutions", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g3_report import report
        print(report(OUT))
        return
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    worker(jobs, a.budget, ck, not a.no_institutions)


if __name__ == "__main__":
    main()
