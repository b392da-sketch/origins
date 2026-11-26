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


# check 10's meeting of herds and dense populations (Ben, 21 November 2026): counted per spell when the record is
# built, so the record does not keep a pair per spell-year (Codex review 037, finding 2)
SPELL_HERDERS = 100
SPELL_AROUND = 5000


def disease_spells(a, H, D):
    """Unbroken runs of a disease on a cell from the per-cell log array (rows: year, disease, cell, how at column H,
    ..., herders, people around, deaths at column D): [disease, cell, first year, last year, years, deaths, years where
    herds and dense populations met, people around in the first year]. A run continues while the next row of the
    same disease and cell is the next year and kept (how 3)."""
    if not len(a):
        return []
    o = np.lexsort((a[:, 0], a[:, 2], a[:, 1]))                          # by disease, cell, year
    yr, dz, cl, how = a[o, 0], a[o, 1], a[o, 2], a[o, H]
    start = np.ones(len(o), dtype=bool)
    start[1:] = (dz[1:] != dz[:-1]) | (cl[1:] != cl[:-1]) | (yr[1:] != yr[:-1] + 1) | (how[1:] != 3)
    first = np.flatnonzero(start)
    last = np.r_[first[1:], len(o)] - 1
    near = a[o, -2]
    dense = ((a[o, -3] >= SPELL_HERDERS) & (near >= SPELL_AROUND)).astype(np.int64)
    deaths = np.add.reduceat(a[o, D], first)
    nd = np.add.reduceat(dense, first)
    return [[int(dz[i]), int(cl[i]), int(yr[i]), int(yr[j]), int(j - i + 1), int(dd), int(n), int(near[i])]
            for i, j, dd, n in zip(first.tolist(), last.tolist(), deaths.tolist(), nd.tolist())]


def kept_polities(w, pl, rng) -> set:
    """Polities whose whole histories the record keeps: all of them up to 1,500; beyond, a sample of 1,500, plus every
    polity that ever held 5+ settlements, was ever a complex chiefdom or state, or had a band holding writing or
    scribes, so writing can be set against tenure (Codex review 033, finding 3)."""
    pids = sorted({r[1] for r in pl})
    if len(pids) <= 1500:
        return set(pids)
    keep = set(int(x) for x in rng.choice(pids, 1500, replace=False))
    keep |= {r[1] for r in pl if r[2] >= 5}
    keep |= {r[1] for r in pl if r[8] >= 2}
    keep |= {int(r[2]) for r in getattr(w, "tech_writing_log", []) if r[2] >= 0}
    return keep


def finish(w, ws, rs, seconds, pr, institutions, write=True):
    from origins import explain, params
    rec = g2.finish(w, ws, rs, seconds, pr, params.STORAGE, write=False)
    rec["institutions"] = institutions
    rec["after_first"] = after_first()
    pl = w.polity_log
    # the polity log keeps its newest 3,000,000 rows (polity.yearly): say how far back it reaches (Codex review 037)
    rec["polity_log_coverage"] = {"rows": len(pl), "truncated": len(pl) >= 3_000_000,
                                  "from_year": int(pl[0][0]) if pl else None}
    rng = np.random.default_rng([ws, rs, 11])
    keep = kept_polities(w, pl, rng)                        # whole polity histories: sample polities, not rows
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
    # M4a pastoralism: herding peoples now, and how many ever took up a herding life
    hs = getattr(w, "herder_since", None)
    live = [b.id for b in w.living_bands()]
    from origins.sim import pastoral
    rec["herders_alive"] = int(sum(1 for b in w.living_bands() if pastoral.is_herder(w, b)))   # herding now
    rec["ever_herded_alive"] = int(sum(1 for i in live if hs is not None and i < len(hs) and hs[i] >= 0))
    rec["farming_bands_alive"] = int(sum(1 for i in live if w.farm_share[i] >= 0.5))
    rec["took_up_herding"] = int(sum(1 for e in w.events if e["kind"] == "took_up_herding"))
    rec["flights"] = int(sum(1 for e in w.events if e["kind"] == "flight"))
    # M4a technology: inventions, adoptions by route, losses (with the people within reach), what is held now
    if hasattr(w, "tech"):
        from origins.sim import technology as T
        tk = {"invention": [], "technique_adopted": [], "technique_lost": [], "technique_recovered": []}
        for e in w.events:
            if e["kind"] in tk:
                d = e["data"]
                tk[e["kind"]].append([e["t"] // 4, d.get("technique"), d.get("route"), d.get("practised"),
                                      d.get("skilled"), d.get("connected"), d.get("band", e.get("band"))])
        rec["tech_inventions"] = tk["invention"]
        rec["tech_losses"] = tk["technique_lost"]
        rec["tech_recovered"] = tk["technique_recovered"]
        routes = {}
        for r in tk["technique_adopted"]:
            routes[r[2] or "contact"] = routes.get(r[2] or "contact", 0) + 1
        rec["tech_adoption_routes"] = routes
        ids = np.array(live, dtype=int)
        if len(ids):
            lv = w.tech[ids]
            rec["tech_held"] = {k: [int((lv[:, i] > 0).sum()), int((lv[:, i] >= params.TECH_WORKING).sum()),
                                    round(float(np.median(lv[lv[:, i] > 0, i])), 3) if (lv[:, i] > 0).any() else 0.0]
                                for i, k in enumerate(T.KEYS)}
        rec["tech_firsts"] = {k: w.events[e]["t"] // 4 for k, e in getattr(w, "tech_firsts", {}).items()}
        # writing in use against writing remembered, with the polity's tier and scribes (Codex review 032, finding 4):
        # every 10 years, [year, band, polity, tier, is seat, scribes, writing level, practised now]
        rec["writing_log_fields"] = ["year", "band", "polity", "tier", "seat", "scribes", "writing", "practised"]
        rec["writing_log"] = getattr(w, "tech_writing_log", [])
        rec["writing_inventions"] = [[e["t"] // 4, e["band"], e["data"].get("stimulus", -1),
                                      e["data"].get("stimulus_needed")] for e in w.events
                                     if e["kind"] == "invention" and e["data"].get("technique") == "writing"]
        tsample = [{"event": e["id"]} for e in w.events if e["kind"] in tk]
        if len(tsample) > 400:
            tsample = [tsample[i] for i in sorted(rng.choice(len(tsample), 400, replace=False))]
        tok = [explain.resolvable(w, r, good=w.__dict__.setdefault("_gate_good", set())) for r in tsample]
        rec["tech_explain_checked"], rec["tech_explain_resolvable"] = len(tok), int(sum(tok))
    # M4a place names: every place with its layers (year, language, how, heard from), no forms
    if getattr(w, "places", None) is not None:
        rec["places"] = [{"kind": p["kind"], "size": round(float(p["size"]), 3),
                          "layers": [[l[0] // 4, l[1], l[3], l[4]] for l in p["layers"]]} for p in w.places]
    # M4a diseases: the named diseases, and each year's epidemic of each (year, disease, cells, deaths, new/passed
    # again/by contact/kept), with whether its cause chain resolves (sampled)
    if getattr(w, "diseases", None) is not None:
        rec["diseases"] = [{k: v for k, v in dz.items() if k != "event"} for dz in w.diseases]
        # diseases whose slot was freed for a new one (review 037): the slot number in the log is reused, so
        # a row's disease is the one whose years [year, retired) hold the row's year
        rec["diseases_retired"] = [{k: v for k, v in dz.items() if k != "event"}
                                   for dz in (getattr(w, "diseases_retired", None) or [])]
        rec["disease_counts"] = {k: v for k, v in w.counts.items() if k in ("dz_retired", "dz_blocked_starts")}
        obs = [e for e in w.events if e["kind"] == "outbreak" and "disease" in e["data"]]
        rec["disease_outbreaks"] = [[e["t"] // 4, e["data"]["disease"], e["data"]["cells"], e["data"]["deaths"]]
                                    for e in obs]
        # the per-cell record (Codex reviews 028-030; disease.LOG_FIELDS). Every arrival row is kept (new, again
        # from its animals, by contact). Years kept on a cell are summed into spells: each unbroken run of a disease
        # on a cell, so long-lasting diseases are not under-sampled and nothing is thinned.
        from origins.sim import disease as _dz
        a = _dz.log_array(w)                     # the array itself, not lists (Codex review 037, finding 2)
        H = _dz.LOG_FIELDS.index("how (0 new, 1 again from its animals, 2 contact, 3 kept)")
        arr = a[a[:, H] != 3]
        rec["disease_log"] = [[float(v) if j == _dz.LOG_FLOAT else int(v) for j, v in enumerate(r)] for r in arr.tolist()]
        rec["disease_log_fields"] = _dz.LOG_FIELDS
        spells = disease_spells(a, H, _dz.LOG_DEATHS)
        rec["disease_spells"] = spells
        # each spell counts its years where herds and dense populations met (Codex review 031, finding 2; counted
        # here rather than kept year by year since review 037)
        rec["disease_spell_fields"] = ["disease", "cell", "first year", "last year", "years", "deaths",
                                       f"years with {SPELL_HERDERS}+ people herding domesticated animals on the cell "
                                       f"and {SPELL_AROUND:,}+ people on the cell and its neighbours",
                                       "people on the cell and its neighbours in the first year"]
        rec["disease_spillovers"] = int(w.counts.get("dz_spillovers", 0))
        smp = [{"event": e["id"]} for e in obs]
        if len(smp) > 200:
            smp = [smp[i] for i in sorted(rng.choice(len(smp), 200, replace=False))]
        rec["disease_explain_checked"] = len(smp)
        rec["disease_explain_resolvable"] = int(sum(explain.resolvable(w, r, good=w.__dict__.setdefault("_gate_good", set())) for r in smp))
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
    ok = [explain.resolvable(w, r, good=w.__dict__.setdefault("_gate_good", set())) for r in sample]
    rec["polity_explain_checked"], rec["polity_explain_resolvable"] = len(ok), int(sum(ok))
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "" if institutions else "_noinst"
    if not write:                                       # G4a adds its own measurements first (gates/g4.py)
        return rec
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
            w = persist.from_file(cp, g2.resume_planet(cp, ws))
            m = json.loads(meta.read_text())
            if "t" in m and int(m["t"]) != int(w.t):        # a world and probes from different checkpoints (review 036)
                raise RuntimeError(f"checkpoint {cp.name}: world at tick {w.t}, probes at tick {m['t']}")
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
                meta.write_text(json.dumps({"t": int(w.t), "seconds": spent + time.time() - start, "year": w.year, "probe": pr}))
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
