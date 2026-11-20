"""Gate G4a — 'knowledge and exchange'. See docs/M4_SPECIFICATION_v1.md section 9 and docs/G4A_GATE_PLAN.md.

Each history runs as in G3 (until 6,000 years after its first farming village, or 30,000 years). Knock-out histories
("--no-pop") run with the population term of invention off (TECH_POP_EXPONENT 0; check 6).

  python -m gates.g4 run --jobs 1:1,2:1 [--no-pop]
  python -m gates.g4 report

Results go to gates/results_g4/. Each record is a G3 record (so G3's checks, and through them M0-M2, can be re-run on
it) plus the measurements of docs/G4A_GATE_PLAN.md. Nothing here draws from the simulation's random streams or
changes its state: the census uses its own generator, seeded from the history.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gates import g2, g3  # noqa: E402
from gates.g0 import _planet  # noqa: E402

OUT = ROOT / "gates" / "results_g4"
CENSUS_YEARS = 100
CENSUS_BANDS = 2000
SAMPLE_CHAINS = 200
ADOPTION_ROWS = 20000


# --------------------------------------------------------------------------------------------- during the run

def census(w, pr):
    """Every CENSUS_YEARS: up to CENSUS_BANDS living bands with what invention and loss depend on (checks 2, 3, 5).
    Rows: [year, band, cell, people within reach, skilled practitioners within reach, strongest need, techniques
    known, farm share]. Also, yearly, which cells are farmed by villages and irrigated (check 9)."""
    from origins.sim import technology as T
    if getattr(w, "tech", None) is None:
        return
    live = w.living_bands()
    if not live:
        return
    short = pr.setdefault("short_by_year", [])        # check 7: share of bands short of food, yearly
    short.append([int(w.year), round(float(np.mean([b.last_ratio < 1.0 for b in live])), 4)])
    farm = pr.setdefault("farm_years", {})          # cell -> [years farmed by a village, current run, irrigated years]
    irr_k = T.INDEX.get("irrigation")
    seen = set()
    for b in live:
        if w.farm_share[b.id] >= 0.5 and b.cell not in seen:
            seen.add(b.cell)
            r = farm.setdefault(str(b.cell), [0, 0, 0])
            r[0] += 1
            r[1] += 1
            if irr_k is not None and w.tech[b.id, irr_k] > 0:
                r[2] += 1
    for c, r in farm.items():
        if int(c) not in seen:
            r[1] = 0
    if w.year % CENSUS_YEARS:
        return
    ids = np.array([b.id for b in live])
    cells = np.array([b.cell for b in live])
    sizes = np.asarray(w.live_sizes(), dtype=float)
    cell_pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
    connected = T._reach(w, cells, cell_pop[:, None])[:, 0]
    sk = T.skilled(w, live, ids)
    sk_cell = np.bincount(cells, weights=sk, minlength=w.planet.n)
    sk_reach = T._reach(w, cells, sk_cell[:, None])[:, 0]
    needs = T._needs(w, live, ids, cells, sizes, cell_pop)
    need = np.max(np.stack(list(needs.values()), axis=1), axis=1)
    known = (w.tech[ids] > 0).sum(axis=1)
    rng = np.random.default_rng([int(w.world_seed), int(w.run_seed), int(w.year)])
    pick = np.arange(len(ids)) if len(ids) <= CENSUS_BANDS else np.sort(rng.choice(len(ids), CENSUS_BANDS, replace=False))
    rows = pr.setdefault("census", [])
    for i in pick.tolist():
        rows.append([int(w.year), int(ids[i]), int(cells[i]), round(float(connected[i]), 1), round(float(sk_reach[i]), 1),
                     round(float(need[i]), 3), int(known[i]), round(float(w.farm_share[ids[i]]), 3)])


# --------------------------------------------------------------------------------------------- at the end

def _ancestors(w, bid) -> list:
    out, seen = [], set()
    while bid is not None and bid >= 0 and bid not in seen:
        seen.add(bid)
        out.append(bid)
        b = w.bands.get(bid)
        bid = getattr(b, "parent", -1) if b is not None else -1
    return out


def _steps(w, sources) -> np.ndarray:
    """Cell steps over land from the nearest source cell (-1 where unreachable)."""
    pl = w.planet
    nb = pl.grid.neighbours
    d = np.full(pl.n, -1, dtype=np.int64)
    front = [int(c) for c in sources]
    for c in front:
        d[c] = 0
    k = 0
    while front:
        k += 1
        nxt = []
        for c in front:
            for x in nb[c]:
                if x >= 0 and d[x] < 0 and (pl.land[x] or pl.coast[x]):
                    d[x] = k
                    nxt.append(int(x))
        front = nxt
    return d


def extras(w, pr, rec, rng):
    """The G4a measurements added to a G3 record (docs/G4A_GATE_PLAN.md)."""
    from origins import explain
    from origins.sim import technology as T
    live = w.living_bands()
    ids = [b.id for b in live]
    # checks 2, 3, 5: the census, and inventions and losses per band and century
    rec["census_fields"] = ["year", "band", "cell", "people within reach", "skilled within reach", "strongest need",
                            "techniques known", "farm share"]
    rec["census"] = pr.get("census", [])
    inv, lost, adopt, firsts = [], [], [], {}
    for e in w.events:
        k = e["kind"]
        if k == "invention":
            inv.append([e["t"] // 4, e["band"], e["data"].get("technique")])
            firsts.setdefault(e["data"].get("technique"), (e["t"] // 4, e["cell"]))
        elif k == "technique_lost":
            lost.append([e["t"] // 4, e["band"], e["data"].get("technique"), bool(e["data"].get("practised"))])
        elif k == "technique_adopted":
            adopt.append([e["t"] // 4, e["band"], e["data"].get("technique"), e["cell"], e["data"].get("route")])
    rec["inventions_by_band"] = inv
    rec["losses_by_band"] = lost
    # check 4a: where each technique a living band knows came from (its own line invented it, or others)
    inventors: dict = {}
    for y, b, t in inv:
        inventors.setdefault(t, set()).add(b)
    share = []
    for b in live:
        known = [T.KEYS[k] for k in np.nonzero(w.tech[b.id] > 0)[0]]
        if not known:
            continue
        line = set(_ancestors(w, b.id))
        own = sum(1 for t in known if inventors.get(t, set()) & line)
        share.append([b.id, len(known), len(known) - own])
    rec["learned_share_fields"] = ["band", "techniques known", "came from others"]
    rec["learned_share"] = share
    # check 4b: first adoption of each technique by each band, with cell steps from the first invention
    first_adopt, seen = [], set()
    for y, b, t, c, route in adopt:
        if (b, t) in seen or t not in firsts:
            continue
        seen.add((b, t))
        first_adopt.append([y, b, t, c])
    if len(first_adopt) > ADOPTION_ROWS:
        first_adopt = [first_adopt[i] for i in sorted(rng.choice(len(first_adopt), ADOPTION_ROWS, replace=False))]
    steps_from = {t: _steps(w, [c]) for t, (y, c) in firsts.items()}
    rec["first_invention"] = {t: [y, c] for t, (y, c) in firsts.items()}
    rec["first_adoptions_fields"] = ["year", "band", "technique", "cell", "cell steps from first invention",
                                     "years after first invention"]
    rec["first_adoptions"] = [[y, b, t, c, int(steps_from[t][c]), y - firsts[t][0]] for y, b, t, c in first_adopt]
    # check 7: goods per person by cell steps from the source, at the end; partner help against shortfall, yearly
    if getattr(w, "goods", None) is not None:
        from origins.sim import trade
        sizes = w.band_sizes()
        cells = np.array([b.cell for b in live])
        allc = np.arange(w.planet.n)
        fall = {}
        for g in ("fine_stone", "salt", "shell"):
            where, _tech = trade.SOURCES[g]
            src = allc[trade._deposit(w, allc, where) & (w.planet.land | w.planet.coast)]
            if not len(src):
                continue
            d = _steps(w, src)
            per = w.goods[ids, trade.GI[g]] / np.maximum(sizes[ids], 1.0)
            by = {}
            for dd, v in zip(d[cells].tolist(), per.tolist()):
                if dd >= 0:
                    by.setdefault(dd, []).append(v)
            fall[g] = {str(k): [len(v), float(np.mean(v))] for k, v in sorted(by.items())}
        rec["goods_falloff"] = fall
    help_by_year: dict = {}
    for e in w.events:
        if e["kind"] == "helped_by_partners":
            y = e["t"] // 4
            help_by_year[y] = help_by_year.get(y, 0.0) + float(e["data"].get("amount", 0.0))
    rec["partner_help_by_year"] = {str(k): round(v, 2) for k, v in sorted(help_by_year.items())}
    rec["short_by_year"] = pr.get("short_by_year", [])
    # check 9: the land on lived-in cells, with years farmed by villages (continuous and in all) and irrigated
    if getattr(w, "fertility", None) is not None:
        lived = sorted({b.cell for b in live})
        farm = pr.get("farm_years", {})
        rain = w.planet.rain
        rec["land_cells_fields"] = ["cell", "fertility", "salt", "slow game", "fast game", "forest", "years farmed",
                                    "years farmed without a break", "years irrigated", "rain mm"]
        rec["land_cells"] = [[c, round(float(w.fertility[c]), 3), round(float(w.salt[c]), 3), round(float(w.game[c]), 3),
                              round(float(w.game_fast[c]), 3), round(float(w.forest[c]), 3)]
                             + farm.get(str(c), [0, 0, 0]) + [int(rain[c])] for c in lived]
        rec["land_exposure"] = {k: v for k, v in w.counts.items() if k.startswith("land_exp")}
        rec["land_events"] = {k: int(sum(1 for e in w.events if e["kind"] == k)) for k in ("land_hunger", "land_move")}
    # writing against tenure (Ben, 21 November 2026): already in the G3 record (writing_log, polity_log kept whole)
    # check 11: sampled cause chains by kind
    kinds = {"invention": "invention", "technique_lost": "loss", "technique_adopted": "adoption",
             "good_arrived": "goods", "trade_route_opened": "trade route", "new_disease": "new disease",
             "place_named": "place name"}
    by_kind: dict = {}
    for e in w.events:
        k = kinds.get(e["kind"])
        if k is not None:
            by_kind.setdefault(k, []).append(e["id"])
    chains = {}
    for k, evs in by_kind.items():
        smp = evs if len(evs) <= SAMPLE_CHAINS else [evs[i] for i in sorted(rng.choice(len(evs), SAMPLE_CHAINS, replace=False))]
        chains[k] = [len(smp), int(sum(explain.resolvable(w, {"event": int(i)}) for i in smp))]
    rec["chains"] = chains
    rec["tech_pop_exponent"] = float(__import__("origins.params", fromlist=["x"]).TECH_POP_EXPONENT)


def finish(w, ws, rs, seconds, pr, tag):
    """The G3 record (written by g3.finish to a string, not a file), plus the G4a measurements."""
    rec = g3.finish(w, ws, rs, seconds, pr, True, write=False)
    extras(w, pr, rec, np.random.default_rng([ws, rs, 41]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"run_w{ws}_s{rs}{tag}.json").write_text(json.dumps(rec))


def worker(jobs, budget, ckpt: Path, pop: bool):
    from origins import engine, params, persist
    from origins.state import World
    g2.apply_overrides()
    params.INSTITUTIONS = True
    if not pop:
        params.TECH_POP_EXPONENT = 0.0
    tag = "" if pop else "_nopop"
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
        while not g3.done(w):
            engine.step(w, 4)
            g2.probe(w, pr)
            census(w, pr)
            if w.year % 500 == 0:
                print(f"w{ws} s{rs}{tag}: year {w.year}, {w.population():,} people, {len(w.events):,} events, "
                      f"peak memory {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
            if w.first_village is not None and "fv_deaths" not in pr:
                pr["fv_deaths"] = {"by_cause": w.accum["deaths_by_cause"].tolist(), "by_age": w.accum["deaths"].tolist()}
            if time.time() > t_end:
                g2.save_planet(cp, w.planet)
                tmp = cp.with_suffix(".tmp")
                import gc
                gc.collect()
                persist.to_file(w, tmp, fast=True)
                tmp.replace(cp)
                meta.write_text(json.dumps({"seconds": spent + time.time() - start, "year": w.year, "probe": pr}))
                print(f"w{ws} s{rs}{tag}: checkpoint at year {w.year}", flush=True)
                return
        finish(w, ws, rs, spent + time.time() - start, pr, tag)
        print(f"w{ws} s{rs}{tag}: completed at year {w.year} in {spent + time.time() - start:.0f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "report"])
    ap.add_argument("--jobs", default="")
    ap.add_argument("--years", type=int, default=g3.MAX_YEARS)
    ap.add_argument("--budget", type=float, default=20000)
    ap.add_argument("--ckpt", default=str(ROOT / "gates" / "ckpt_g4"))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--no-pop", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g4_report import report
        print(report(OUT))
        return
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    worker(jobs, a.budget, ck, not a.no_pop)


if __name__ == "__main__":
    main()
