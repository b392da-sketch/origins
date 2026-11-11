"""Gate G1 — 'spreading and drifting apart'. See docs/M1_SPECIFICATION_v1.md section 7.

Histories run in time-limited slices with checkpoints, so the gate can run on
machines where one process cannot run for hours; save/load is exact, so a
sliced history is the same history.

  python -m gates.g1 run    --jobs 1:1,1:2,... --years 5000 --budget 1500 --ckpt DIR --workers 2
  python -m gates.g1 groups --worlds 1-5           (check 10: groups vs individuals at the food limit)
  python -m gates.g1 report

Measurements taken while a history runs (the "probe") are kept beside the
checkpoint and written into the result file when the history finishes.
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

OUT = ROOT / "gates" / "results_g1"
HAZARD_KINDS = ("flood", "wildfire", "eruption", "earthquake", "outbreak")


# ---------------------------------------------------------------- geography
_landmass = {}


def reachable(pl, mask) -> np.ndarray:
    """Cells of a land mass (mask) that can be walked to from the starting cell through land with food."""
    ok = mask & (pl.capacity > 0)
    seen = np.zeros(pl.n, dtype=bool)
    seen[pl.start_cell] = True
    stack = [int(pl.start_cell)]
    nb = pl.grid.neighbours
    while stack:
        c = stack.pop()
        for m in nb[c]:
            if m >= 0 and ok[m] and not seen[m]:
                seen[m] = True
                stack.append(int(m))
    return seen


def landmass(pl) -> np.ndarray:
    """Connected land areas (walking only)."""
    if pl.seed in _landmass:
        return _landmass[pl.seed]
    lab = -np.ones(pl.n, dtype=np.int64)
    nb = pl.grid.neighbours
    k = 0
    for s in np.nonzero(pl.land)[0]:
        if lab[s] >= 0:
            continue
        stack = [int(s)]
        lab[s] = k
        while stack:
            c = stack.pop()
            for m in nb[c]:
                if m >= 0 and pl.land[m] and lab[m] < 0:
                    lab[m] = k
                    stack.append(int(m))
        k += 1
    _landmass[pl.seed] = lab
    return lab


def sea_reachable(pl) -> dict:
    """Land areas reachable from the start area on foot or by one-cell sea crossings, and their sizes."""
    lab = landmass(pl)
    nb = pl.grid.neighbours
    start = int(lab[pl.start_cell])
    reach, frontier = {start}, [start]
    while frontier:
        k = frontier.pop()
        cells = np.nonzero(lab == k)[0]
        for c in cells:
            for x in nb[c]:
                if x >= 0 and not pl.land[x]:
                    for y in nb[x]:
                        if y >= 0 and pl.land[y] and lab[y] not in reach:
                            reach.add(int(lab[y]))
                            frontier.append(int(lab[y]))
    sizes = {int(k): int((lab == k).sum()) for k in reach}
    return {"start": start, "areas": sizes}


# ---------------------------------------------------------------- probe
def new_probe():
    return {"snapshots": {}, "hazard_watch": [], "hazard_after": [], "samples": {}}


def _km(pl, a, b):
    xyz = pl.grid.xyz
    return float(np.arccos(np.clip(xyz[a] @ xyz[b], -1, 1)) * pl.grid.radius_km)


def probe_year(w, pr):
    """Called once a year after the year's last tick."""
    from origins.sim import language as L
    y = w.year
    # hazard responses: watch peopled hazards, measure the area 1 and 20 years later
    sizes = None
    if pr.get("last_event", 0) < len(w.events):
        for e in w.events[pr.get("last_event", 0):]:
            if e["kind"] in HAZARD_KINDS and e["cell"] >= 0 and len(pr["hazard_watch"]) < 400:
                sizes = w.band_sizes() if sizes is None else sizes
                pr["hazard_watch"].append({"id": e["id"], "kind": e["kind"], "cell": e["cell"], "year": y,
                                           "deaths": e["data"].get("deaths", 0),
                                           "before": _area_pop(w, e["cell"], sizes),
                                           "births_before": _area_births(w, e["cell"])})
        pr["last_event"] = len(w.events)
    keep = []
    for h in pr["hazard_watch"]:
        age = y - h["year"]
        if age in (1, 20) and f"after{age}" not in h:
            sizes = w.band_sizes() if sizes is None else sizes
            h[f"after{age}"] = _area_pop(w, h["cell"], sizes)
            h[f"births{age}"] = _area_births(w, h["cell"]) - h["births_before"]
        if age >= 20:
            pr["hazard_after"].append(h)
        else:
            keep.append(h)
    pr["hazard_watch"] = keep
    # vocabulary snapshots every 500 years (roots of every living language)
    if y % 500 == 0 and y > 0:
        pr["snapshots"][str(y)] = {str(l.id): [l.lexicon[m][1] for m in L.MEANINGS]
                                   for l in w.languages.values() if l.alive}
    if y % 1000 == 0 and y > 0:
        pr["samples"][str(y)] = sample_state(w)


def _area_pop(w, cell, sizes):
    nb = w.planet.grid.neighbours
    area = {cell} | {int(x) for x in nb[cell] if x >= 0}
    return float(sum(sizes[b.id] for b in w.living_bands() if b.cell in area))


def _area_births(w, cell):
    nb = w.planet.grid.neighbours
    area = [cell] + [int(x) for x in nb[cell] if x >= 0]
    return float(w.cell_births[area].sum())


def sample_state(w) -> dict:
    """Cultural distance vs geographic distance, language pairs, and counts."""
    from origins.sim import customs
    from origins.sim import language as L
    pl = w.planet
    rng = np.random.default_rng([w.world_seed, w.run_seed, w.year])
    bands = w.living_bands()
    lab = landmass(pl)
    pairs = []
    if len(bands) > 2:
        for _ in range(400):
            i, j = rng.choice(len(bands), 2, replace=False)
            a, b = bands[int(i)], bands[int(j)]
            shared = L.shared_roots(w.languages[a.language], w.languages[b.language])
            pairs.append([round(_km(pl, a.cell, b.cell)), round(customs.distance(w, a.id, b.id), 4),
                          round(shared, 4), int(lab[a.cell] != lab[b.cell])])
    alive = [l for l in w.languages.values() if l.alive]
    centre = {}
    sizes = w.band_sizes()
    for b in bands:
        centre.setdefault(b.language, []).append(b.cell)
    lpairs = []
    if len(alive) > 1:
        for _ in range(min(400, len(alive) * (len(alive) - 1) // 2)):
            i, j = rng.choice(len(alive), 2, replace=False)
            a, b = alive[int(i)], alive[int(j)]
            ca, cb = centre.get(a.id, [0])[0], centre.get(b.id, [0])[0]
            lpairs.append([round((w.t - L.common_ancestor_time(w, a.id, b.id)) / 4), round(L.shared_roots(a, b), 4),
                           round(_km(pl, ca, cb)), int(lab[ca] != lab[cb])])
    # language "families": living languages grouped by common ancestors older than 2,500 years
    fam = set()
    for l in alive:
        chain = L.lineage(w, l.id)
        root = next((x.id for x in reversed(chain) if (w.t - x.born) / 4 >= 2500), chain[0].id)
        fam.add(root)
    return {"bands": len(bands), "population": w.population(), "languages_alive": len(alive),
            "languages_ever": len(w.languages), "families_2500y": len(fam), "band_pairs": pairs,
            "language_pairs": lpairs,
            "speakers": sorted([int(sum(sizes[b.id] for b in w.living_bands() if b.language == l.id)) for l in alive])}


# ---------------------------------------------------------------- finishing
def finish(w, ws, rs, years, seconds, pr, replay=None):
    from origins import engine, explain
    from origins.lang.proto import MEANINGS, show
    from origins.sim import language as L
    from origins.sim import observe
    pl = w.planet
    rec = {"world_seed": ws, "run_seed": rs, "requested_years": years, "env": _env(),
           "planet_fingerprint": pl.fingerprint, "start_cell": pl.start_cell,
           "completed_years": len(w.yearly), "extinct": engine.extinct(w),
           "extinct_year": w.year if engine.extinct(w) else None, "seconds": round(seconds, 1),
           "invariant_failures": len(w.invariant_failures), "invariant_examples": w.invariant_failures[:5],
           "replay_check": replay}
    keys = ["population", "individuals", "groups", "bands", "occupied_cells", "known_cells",
            "capacity_occupied", "food_ratio", "mean_condition", "births", "deaths", "median_band"]
    rec["yearly"] = {k: [r[k] for r in w.yearly][::5] for k in keys}       # every 5th year
    rec["life_table"] = observe.life_table(w)
    rec["counts"] = w.counts
    rec["events"] = {}
    for e in w.events:
        rec["events"][e["kind"]] = rec["events"].get(e["kind"], 0) + 1
    # hazards: every logged hazard in a possible place?
    wrong = {k: 0 for k in HAZARD_KINDS}
    for e in w.events:
        k, c = e["kind"], e["cell"]
        if k == "flood" and not pl.river[c]:
            wrong[k] += 1
        if k == "wildfire" and pl.biome[c] not in __import__("origins.sim.hazards", fromlist=["x"]).FIRE_BIOMES:
            wrong[k] += 1
        if k == "eruption" and not pl.volcanic[c]:
            wrong[k] += 1
        if k == "earthquake" and not pl.seismic[c]:
            wrong[k] += 1
    rec["hazard_wrong_place"] = wrong
    land = pl.land
    rec["hazard_eligible_cells"] = {
        "flood": int((pl.river & land).sum()), "eruption": int((pl.volcanic & land).sum()),
        "earthquake": int((pl.seismic & land).sum()),
        "wildfire": int((np.isin(pl.biome, __import__("origins.sim.hazards", fromlist=["x"]).FIRE_BIOMES) & land).sum())}
    rec["hazard_summary"] = hazard_summary(pr["hazard_after"])
    rec["hazard_after"] = [h for k in HAZARD_KINDS for h in [x for x in pr["hazard_after"] if x["kind"] == k][:20]]
    # regular sound change and traceability: rebuild every word of up to 20 living languages
    alive = [l for l in w.languages.values() if l.alive]
    bad = checked = 0
    for lang in alive[:20]:
        for m in MEANINGS:
            checked += 1
            if L.word_history(w, lang.id, m)[-1][1] != show(tuple(lang.lexicon[m][0])):
                bad += 1
    rec["words_checked"], rec["words_untraceable"] = checked, bad
    rec["sound_changes"] = sum(1 for l in w.languages.values() for e in l.history if e[1] == "rule")
    rec["rules_used"] = sorted({e[2] for l in w.languages.values() for e in l.history if e[1] == "rule"})
    p = w.people
    names_bad = 0
    idx = w.alive_idx()
    for i in idx[:200]:
        i = int(i)
        lg = int(p.lang[i])
        if lg < 0 or p.name(i) != L.compose_name(w.languages[lg], int(p.name_a[i]), int(p.name_b[i]), p.sex[i] == 0):
            names_bad += 1
    rec["names_checked"], rec["names_untraceable"] = min(200, len(idx)), names_bad
    # retention per 1,000 years from snapshots
    rec["retention"] = retention(w, pr["snapshots"])
    rec["samples"] = pr["samples"]
    rec["samples"][str(w.year)] = sample_state(w)
    rec["sea"] = sea_reachable(pl)
    lab = landmass(pl)
    occ_areas = sorted({int(lab[b.cell]) for b in w.living_bands()})
    rec["sea"]["occupied_areas"] = occ_areas
    # explainability
    rng = np.random.default_rng([ws, rs, 99])
    dead = np.nonzero(p.death[:p.n] >= 0)[0]
    sample = [{"death": int(i)} for i in (rng.choice(dead, size=min(100, len(dead)), replace=False) if len(dead) else [])]
    hz_dead = np.nonzero(p.death_hazard[:p.n] >= 0)[0]
    sample += [{"death": int(i)} for i in hz_dead[:50]]
    kinds = ("fission", "group_hunger_deaths", "merge", "band_extinct", "language_split", "sea_crossing") + HAZARD_KINDS
    for k in kinds:
        sample += [{"event": e["id"]} for e in w.events if e["kind"] == k][:25]
    ok = [explain.resolvable(w, r) for r in sample]
    rec["explain_checked"], rec["explain_resolvable"] = len(ok), int(sum(ok))
    rec["status"] = "completed"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"run_w{ws}_s{rs}_{years}y.json").write_text(json.dumps(rec))


def hazard_summary(hs) -> dict:
    """Totals per hazard kind over peopled hazards with deaths, watched for 20 years."""
    out = {}
    for h in hs:
        if h["deaths"] <= 0 or h["before"] <= 0 or "after20" not in h or "after1" not in h:
            continue
        s = out.setdefault(h["kind"], {"n": 0, "death_share": 0.0, "lower_after_1": 0, "recovered_20": 0})
        s["n"] += 1
        s["death_share"] += h["deaths"] / h["before"]
        s["lower_after_1"] += int(h["after1"] < h["before"])
        s["recovered_20"] += int(h["after20"] >= 0.9 * h["before"])
    return out


def retention(w, snaps) -> list:
    """Share of core-vocabulary roots kept by each living language over each 1,000-year span."""
    from origins.sim import language as L
    out = []
    years = sorted(int(y) for y in snaps)
    for y1 in years:
        y0 = y1 - 1000
        if str(y0) not in snaps:
            continue
        s0, s1 = snaps[str(y0)], snaps[str(y1)]
        vals = []
        for lid, roots in s1.items():
            chain = [l.id for l in L.lineage(w, int(lid))]
            anc = next((a for a in reversed(chain) if str(a) in s0), None)
            if anc is None:
                continue
            old = s0[str(anc)]
            vals.append(float(np.mean([a == b for a, b in zip(old, roots)])))
        if vals:
            out.append({"from": y0, "to": y1, "languages": len(vals), "mean": float(np.mean(vals)),
                        "p10": float(np.percentile(vals, 10)), "p90": float(np.percentile(vals, 90))})
    return out


# ---------------------------------------------------------------- slicing
def apply_overrides():
    """Parameter overrides for a gate run, from the ORIGINS_PARAMS environment variable (JSON)."""
    import os
    from origins import params
    for k, v in json.loads(os.environ.get("ORIGINS_PARAMS", "{}") or "{}").items():
        if not hasattr(params, k):
            raise SystemExit(f"unknown parameter {k}")
        setattr(params, k, v)


def resume_planet(cp, ws):
    """The planet a checkpointed history ran on. Different GitHub machines compute the same planet slightly
    differently, so the planet is saved with each checkpoint and reused when continuing elsewhere; the log
    reports how the planet computed on this machine differs from it."""
    import pickle
    pf = cp.with_suffix(".planet")
    here = _planet(ws)
    if not pf.exists():
        return here
    saved = pickle.loads(pf.read_bytes())
    if saved.fingerprint != here.fingerprint:
        diffs = []
        for k in ("elevation", "land", "river", "biome", "capacity", "rain", "temp_mean", "region", "plate"):
            a, b = np.asarray(getattr(saved, k)), np.asarray(getattr(here, k))
            n = int((a != b).sum())
            if n:
                diffs.append(f"{k}: {n} cells, largest {float(np.abs(a.astype(float) - b.astype(float)).max()):.3g}")
        print(f"planet {ws} computed differently on this machine ({'; '.join(diffs) or 'no array differs'}); "
              f"continuing on the saved planet", flush=True)
    return saved


def save_planet(cp, planet):
    import pickle
    pf = cp.with_suffix(".planet")
    if not pf.exists():
        pf.write_bytes(pickle.dumps(planet, protocol=4))


def worker(jobs, years, budget, ckpt: Path):
    from origins import engine, persist
    from origins.state import World
    apply_overrides()
    t_end = time.time() + budget
    for ws, rs in jobs:
        if (OUT / f"run_w{ws}_s{rs}_{years}y.json").exists():
            continue
        if time.time() > t_end - 5:
            return
        cp, meta = ckpt / f"w{ws}_s{rs}.zip", ckpt / f"w{ws}_s{rs}.json"
        start = time.time()
        if cp.exists():
            w = persist.from_bytes(cp.read_bytes(), resume_planet(cp, ws))
            m = json.loads(meta.read_text())
            spent, pr, replay = m["seconds"], m["probe"], m.get("replay")
        else:
            w = World.new(ws, rs, _planet(ws))
            spent, pr, replay = 0.0, new_probe(), None
        while len(w.yearly) < years and not engine.extinct(w):
            engine.step(w, 4)
            probe_year(w, pr)
            if rs == 1 and replay is None and len(w.yearly) == 2500:
                twin = persist.from_bytes(persist.to_bytes(w), w.planet)
                engine.step(w, 40)
                engine.step(twin, 40)
                replay = persist.digest(w) == persist.digest(twin)
                del twin
                for _ in range(10):
                    probe_year(w, pr)
            if time.time() > t_end:
                save_planet(cp, w.planet)
                tmp = cp.with_suffix(".tmp")
                persist.to_file(w, tmp, fast=True)
                tmp.replace(cp)
                meta.write_text(json.dumps({"seconds": spent + time.time() - start, "year": len(w.yearly),
                                            "probe": pr, "replay": replay}))
                print(f"w{ws} s{rs}: checkpoint at year {len(w.yearly)}", flush=True)
                return
        finish(w, ws, rs, years, spent + time.time() - start, pr, replay)
        print(f"w{ws} s{rs}: completed ({'extinct' if engine.extinct(w) else 'survived'}) "
              f"in {spent + time.time() - start:.0f} s", flush=True)


# ---------------------------------------------------------------- check 10
def groups_at_limit(ws: int, years: int = 800, horizon: int = 300, food: float = 0.2):
    """Check 10. Paired runs from the same world, made crowded by halving the wild food everywhere
    (a gate experiment, not part of any history): everyone as individuals vs everyone folded into groups."""
    from origins import engine, persist
    from origins.sim import groups
    from origins.state import C, World
    path = OUT / f"groups_w{ws}.json"
    if path.exists():
        return
    w = World.new(ws, 1, _planet(ws))
    engine.step(w, 4 * years)
    while w.population() < 15_000 and w.year < 3000:     # a world small at year 800 is still spreading
        engine.step(w, 4 * 10)
    w.food_modifier[:] = food
    w.intervened = True
    ind = persist.from_bytes(persist.to_bytes(w), w.planet)
    grp = persist.from_bytes(persist.to_bytes(w), w.planet)
    for b in list(grp.living_bands()):
        if b.mode == "individual":
            groups.fold(grp, b)
    out = {"world_seed": ws, "at_year": w.year, "horizon": horizon, "food": food}
    for name, x in (("individuals", ind), ("groups", grp)):
        b0, d0 = x.counts["births"], x.accum["deaths_by_cause"][:C["flood"]].sum()
        hz0 = x.accum["deaths_by_cause"][C["flood"]:].sum()
        py0 = x.accum["person_years"].sum()
        ratios, pops, margins = [], [], []
        for _ in range(horizon):
            engine.step(x, 4)
            ratios.append(float(np.mean([b.last_ratio for b in x.living_bands()])))
            sz = x.band_sizes()
            margins.append(float(np.average([b.margin for b in x.living_bands()],
                                            weights=[sz[b.id] + 1e-9 for b in x.living_bands()])))
            if len(pops) == horizon // 3:          # measure rates over the last two thirds, once crowded
                b0, d0 = x.counts["births"], x.accum["deaths_by_cause"][:C["flood"]].sum()
                hz0 = x.accum["deaths_by_cause"][C["flood"]:].sum()
                py0 = x.accum["person_years"].sum()
            pops.append(x.population())
        py = x.accum["person_years"].sum() - py0
        out[name] = {"birth_rate": (x.counts["births"] - b0) / py,
                     "death_rate": float(x.accum["deaths_by_cause"][:C["flood"]].sum() - d0) / py,
                     "hazard_death_rate": float(x.accum["deaths_by_cause"][C["flood"]:].sum() - hz0) / py,
                     "mean_food_ratio": float(np.mean(ratios)), "population": pops[::10],
                     "food_margin_late": float(np.mean(margins[horizon // 2:])),
                     "invariant_failures": len(x.invariant_failures)}
    path.write_text(json.dumps(out))


def _range(s: str):
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "groups", "report"])
    ap.add_argument("--jobs", default="")
    ap.add_argument("--worlds", default="1-5")
    ap.add_argument("--years", type=int, default=5000)
    ap.add_argument("--budget", type=float, default=1500)
    ap.add_argument("--ckpt", default=str(ROOT / "gates" / "ckpt_g1"))
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g1_report import report
        print(report(OUT))
        return
    if a.what == "groups":
        apply_overrides()
        for ws in _range(a.worlds):
            groups_at_limit(ws)
            print(f"groups w{ws} done", flush=True)
        return
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    if a.workers == 1:
        worker(jobs, a.years, a.budget, ck)
        return
    shares = [jobs[k::a.workers] for k in range(a.workers)]
    procs = [mp.Process(target=worker, args=(s, a.years, a.budget, ck)) for s in shares]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


if __name__ == "__main__":
    main()
