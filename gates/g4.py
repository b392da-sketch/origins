"""Gate G4a — 'knowledge and exchange'. See docs/M4_SPECIFICATION_v1.md section 9 and docs/G4A_GATE_PLAN.md (approved
by Ben, 21 November 2026, with the review-034 decisions).

Each history runs as in G3 (until 6,000 years after its first farming village, or 30,000 years). Arms (ARMS) run the
same histories with one mechanism changed: no population effect on invention (check 6), no curation, no prestige
goods, and a fixed four partners per band (the comparisons agreed for the gate in November).

  python -m gates.g4 run --jobs 1:1,2:1 [--arm nopop]
  python -m gates.g4 report

Results go to gates/results_g4/. Each record is a G3 record (so G3's checks, and through them M0-M2, can be re-run
on it) plus the measurements of docs/G4A_GATE_PLAN.md. Nothing here draws from the simulation's random streams or
changes its state. The census uses its own generator; two observers (on the land's yearly accounts and on help
between partners) read values the simulation has computed and record them in the probe, changing nothing.
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
# the arms: name -> parameters changed (Ben, 21 November 2026, after Codex review 034)
ARMS = {
    "nopop": {"TECH_POP_EXPONENT": 0.0},          # check 6
    "nocuration": {"CURATION": False},            # the curation knock-out (Ben, 15-16 November 2026)
    "noprestige": {"PRESTIGE_HOLD": 0.0},         # the prestige-goods knock-out (trade stage 5)
    "fourpartners": {"PARTNERS_CAP": 4},          # a fixed four partners per band, against the square-root allowance
}
# event kinds whose cause chains the gate samples (check 11); each must appear in some history
CHAIN_KINDS = {"invention": "invention", "technique_lost": "loss", "technique_adopted": "adoption",
               "good_arrived": "goods arrival", "gift_exchange": "gift exchange", "trade_route_opened": "trade route",
               "helped_by_partners": "help in need", "technique_cut_off": "import cut off",
               "new_disease": "new disease", "outbreak": "outbreak", "land_hunger": "land and hunger",
               "land_move": "land and moves", "place_named": "place name"}

_PR = {"pr": None}                                  # the probe the observers write to (one history at a time)


# --------------------------------------------------------------------------------------------- observers

def install_observers():
    """Wrap two functions so the gate sees values the simulation computes and then discards. Neither wrapper
    changes an argument, a result or the world (Codex review 034, findings 3 and 7)."""
    from origins.sim import land, trade
    if getattr(land, "_g4_wrapped", False):
        return
    clear0 = land._clear_year

    def clear_year(w):
        pr = _PR["pr"]
        if pr is not None and getattr(w, "land_wild", None) is not None and w.land_wild.sum() > 0:
            # hunting pressure (the year's take against the year's maxima) and the crop factor (fertility x salt)
            # on cells farmed this year, as land.yearly used them, just before the year's accounts are cleared
            hunt = pr.setdefault("hunt", {})
            hc = np.nonzero((w.land_wild > 0) & (w.land_take > 0))[0]
            h = w.land_take[hc] / w.land_wild[hc]
            for c, v in zip(hc.tolist(), h.tolist()):
                r = hunt.setdefault(str(c), [0.0, 0])
                r[0] += v
                r[1] += 1
            fc = np.nonzero(w.land_seasons > 0)[0]
            if len(fc):
                cf = land.crop_factor(w, fc)
                irr = w.land_irr[fc] > 0
                crops = pr.setdefault("crops", {})
                for c, v, ir in zip(fc.tolist(), cf.tolist(), irr.tolist()):
                    r = crops.setdefault(str(c), [None, 0.0, 0, 0])      # first factor, last, years, irrigated years
                    if r[0] is None:
                        r[0] = round(v, 4)
                    r[1] = round(v, 4)
                    r[2] += 1
                    r[3] += int(ir)
        return clear0(w)

    share0 = trade.share_in_need

    def share_in_need(w, bands, ids, avail, need_now, keep_need):
        pr = _PR["pr"]
        out = share0(w, bands, ids, avail, need_now, keep_need)
        if pr is not None and getattr(w, "partner_of", None) is not None and len(ids):
            short = np.maximum(need_now - avail, 0.0)                      # need before any transfer
            has = np.array([int(b) < len(w.partner_of) and (w.partner_of[int(b)] >= 0).any() for b in ids])
            elig = (short > 0) & has
            got = np.maximum(out - avail, 0.0)
            y = str(int(w.year))
            r = pr.setdefault("help", {}).setdefault(y, [0, 0, 0.0, 0.0, 0])
            # [band-seasons with partners, of them short before help, food short before help, food given, helped]
            r[0] += int(has.sum())
            r[1] += int(elig.sum())
            r[2] += float(short[elig].sum())
            r[3] += float(got[elig].sum())
            r[4] += int((got[elig] > 0).sum())
        return out

    land._clear_year = clear_year
    trade.share_in_need = share_in_need             # foraging calls it as trade.share_in_need, so this is seen
    land._g4_wrapped = True


# --------------------------------------------------------------------------------------------- during the run

def census(w, pr):
    """Yearly: villages' unbroken cropping by cell (check 9). Every CENSUS_YEARS: a panel of up to CENSUS_BANDS living
    bands, kept from one census to the next while they live and topped up at random (checks 2, 3, 5). Rows:
    [year, band, cell, connected people (as invention uses them), skilled within reach, mean need over the
    techniques it could invent, how many it could invent, techniques known, farm share, alive at the next census]."""
    from origins.sim import technology as T
    if getattr(w, "tech", None) is None:
        return
    live = w.living_bands()
    if not live:
        return
    farm = pr.setdefault("farm_years", {})          # cell -> [years farmed by a village, current unbroken run]
    seen = set()
    for b in live:
        if w.farm_share[b.id] >= 0.5 and b.cell not in seen:
            seen.add(b.cell)
            r = farm.setdefault(str(b.cell), [0, 0])
            r[0] += 1
            r[1] += 1
    for c, r in farm.items():
        if int(c) not in seen:
            r[1] = 0
    if w.year % CENSUS_YEARS:
        return
    ids = np.array([b.id for b in live])
    cells = np.array([b.cell for b in live])
    sizes = np.asarray(w.live_sizes(), dtype=float)
    cell_pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
    connected = T.connected_people(w, ids, cells, cell_pop)          # exactly what invention uses (finding 5)
    sk = T.skilled(w, live, ids)
    sk_cell = np.bincount(cells, weights=sk, minlength=w.planet.n)
    sk_reach = T._reach(w, cells, sk_cell[:, None])[:, 0]
    ti = getattr(w, "trade_in", None)                 # the trade-need accessor may make this array: put it back
    ti_copy = None if ti is None else ti.data.copy()   # as it was, so the census changes nothing (review 036)
    needs = T._needs(w, live, ids, cells, sizes, cell_pop)
    if ti is None:
        made = getattr(w, "trade_in", None)
        if made is not None:
            made.slots.arrays.remove(made)
        w.trade_in = None
    else:
        w.trade_in = ti
        ti.data[:len(ti_copy)] = ti_copy
    need = np.stack([needs[t.need] for t in T.TECHNIQUES], axis=1)
    eligible = T._possible(w, ids, cells) & (w.tech[ids] <= 0)        # what it could invent now (finding 5)
    n_elig = eligible.sum(axis=1)
    mean_need = np.where(n_elig > 0, (need * eligible).sum(axis=1) / np.maximum(n_elig, 1), np.nan)
    known = (w.tech[ids] > 0).sum(axis=1)
    alive = set(ids.tolist())
    rows = pr.setdefault("census", [])
    last = pr.get("census_panel", [])
    for r in rows:                                   # did last census's bands live to this one?
        if r[0] == w.year - CENSUS_YEARS and r[-1] is None:
            r[-1] = r[1] in alive
    keep = [b for b in last if b in alive]
    rng = np.random.default_rng([int(w.world_seed), int(w.run_seed), int(w.year)])
    others = sorted(alive - set(keep))
    room = CENSUS_BANDS - len(keep)
    if room > 0 and others:
        keep += [int(x) for x in rng.choice(others, min(room, len(others)), replace=False)]
    pr["census_panel"] = sorted(keep)
    pos = {int(b): i for i, b in enumerate(ids.tolist())}
    for b in pr["census_panel"]:
        i = pos[b]
        rows.append([int(w.year), int(b), int(cells[i]), round(float(connected[i]), 1), round(float(sk_reach[i]), 1),
                     None if np.isnan(mean_need[i]) else round(float(mean_need[i]), 3), int(n_elig[i]),
                     int(known[i]), round(float(w.farm_share[b]), 3), None])


# --------------------------------------------------------------------------------------------- at the end

def _steps(w, sources) -> np.ndarray:
    """Cell steps over land and coast from the nearest source cell (-1 where unreachable)."""
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


def transmission(w):
    """One pass over the events, in order, following each band's holding of each technique (Codex review 034,
    finding 6): how it came by it last (invented by its own line, or from others: an adoption names its source),
    and how many transmission steps it lies from an invention (an invention 0; an adoption one more than its
    source's holding at the time). A daughter band takes her mother's records at the split; a loss clears the
    record, so a technique lost and learned again counts as learned. Returns (holdings now, first adoptions)."""
    hold: dict = {}                                  # band -> {technique: [how, steps]}
    first = []                                       # [year, band, technique, cell, steps, route]
    firsts: dict = {}                                # technique -> (year, cell) of its first invention
    seen = set()
    for e in w.events:
        k = e["kind"]
        if k == "fission":
            nb_ = e["data"].get("new_band")
            if nb_ is not None and e["band"] in hold:
                hold[int(nb_)] = {t: list(v) for t, v in hold[e["band"]].items()}
            continue
        t = e["data"].get("technique")
        if t is None:
            continue
        b = e["band"]
        if k == "invention":
            hold.setdefault(b, {})[t] = ["own", 0]
            firsts.setdefault(t, (e["t"] // 4, e["cell"]))
        elif k == "technique_adopted":
            src = e["data"].get("source")
            prev = hold.get(int(src), {}).get(t) if src is not None else None
            steps = prev[1] + 1 if prev is not None and prev[1] is not None else None
            hold.setdefault(b, {})[t] = ["others", steps]
            if (b, t) not in seen:
                seen.add((b, t))
                first.append([e["t"] // 4, b, t, e["cell"], steps, e["data"].get("route")])
        elif k in ("technique_lost",):
            hold.get(b, {}).pop(t, None)
    return hold, first, firsts


def extras(w, pr, rec, rng):
    """The G4a measurements added to a G3 record (docs/G4A_GATE_PLAN.md)."""
    from origins import explain
    from origins.sim import technology as T
    from origins import params as P
    live = w.living_bands()
    ids = [b.id for b in live]
    rec["end_year"] = int(w.year)
    # checks 2, 3, 5: the census panel, and inventions and losses per band and century
    rec["census_fields"] = ["year", "band", "cell", "connected people", "skilled within reach", "mean need of what it "
                            "could invent", "techniques it could invent", "techniques known", "farm share",
                            "alive at the next census"]
    rec["census"] = pr.get("census", [])
    inv, lost = [], []
    for e in w.events:
        if e["kind"] == "invention":
            inv.append([e["t"] // 4, e["band"], e["data"].get("technique")])
        elif e["kind"] == "technique_lost":
            lost.append([e["t"] // 4, e["band"], e["data"].get("technique"), bool(e["data"].get("practised")),
                         e["data"].get("connected")])
    rec["inventions_by_band"] = inv
    rec["losses_by_band"] = lost
    # check 4: provenance and transmission steps from the events (finding 6)
    hold, first, firsts = transmission(w)
    share = []
    for b in live:
        known = [T.KEYS[k] for k in np.nonzero(w.tech[b.id] > 0)[0]]
        rec_b = hold.get(b.id, {})
        own = sum(1 for t in known if rec_b.get(t, ["?"])[0] == "own")
        oth = sum(1 for t in known if rec_b.get(t, ["?"])[0] == "others")
        if own + oth:
            share.append([b.id, own + oth, oth])
    rec["learned_share_fields"] = ["band", "techniques known with a recorded acquisition", "came from others"]
    rec["learned_share"] = share
    if len(first) > ADOPTION_ROWS:
        first = [first[i] for i in sorted(rng.choice(len(first), ADOPTION_ROWS, replace=False))]
    rec["first_invention"] = {t: [y, c] for t, (y, c) in firsts.items()}
    rec["first_adoptions_fields"] = ["year", "band", "technique", "cell", "transmission steps from an invention",
                                     "route", "years after first invention"]
    rec["first_adoptions"] = [r + [r[0] - firsts[r[2]][0]] if r[2] in firsts else r + [None] for r in first]
    # check 7: goods per person by cell steps from the source; help between partners against need before it
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
    rec["help_fields"] = ["band-seasons with partners", "of them short before help", "food short before help",
                          "food given to them", "band-seasons helped"]
    rec["help_by_year"] = pr.get("help", {})
    # check 9: every cell ever cropped or hunted, with its land now, its crop factor first and last, years cropped,
    # years irrigated, unbroken cropping by villages, mean hunting pressure and rain
    if getattr(w, "fertility", None) is not None:
        crops, hunt, farm = pr.get("crops", {}), pr.get("hunt", {}), pr.get("farm_years", {})
        cellset = sorted({int(c) for c in crops} | {int(c) for c in hunt} | {b.cell for b in live})
        lived = {b.cell for b in live}
        rain = w.planet.rain
        rec["land_cells_fields"] = ["cell", "lived in now", "fertility", "salt", "slow game", "fast game", "forest",
                                    "crop factor first", "crop factor last", "years cropped", "years irrigated",
                                    "years farmed by villages", "unbroken village years at the end",
                                    "mean hunting pressure", "years hunted", "rain mm"]
        rows = []
        for c in cellset:
            cr = crops.get(str(c), [None, None, 0, 0])
            hu = hunt.get(str(c), [0.0, 0])
            fa = farm.get(str(c), [0, 0])
            rows.append([c, c in lived, round(float(w.fertility[c]), 3), round(float(w.salt[c]), 3),
                         round(float(w.game[c]), 3), round(float(w.game_fast[c]), 3), round(float(w.forest[c]), 3),
                         cr[0], cr[1], cr[2], cr[3], fa[0], fa[1],
                         round(hu[0] / hu[1], 4) if hu[1] else None, hu[1], int(rain[c])])
        rec["land_cells"] = rows
        rec["land_exposure"] = {k: v for k, v in w.counts.items() if k.startswith("land_exp")}
        from origins.sim import minorlog
        rec["land_events"] = {k: int(sum(1 for e in w.events if e["kind"] == k))
                              for k in ("land_hunger", "land_move", "land_abandoned", "land_game", "land_forest",
                                        "land_soil", "land_salt")}
        rec["land_events"]["land_move"] += minorlog.size(w, "land_move")   # older events and rows (review 039)
    # M1's carried-forward items, re-measured (Ben, 21 November 2026): language pairs across the sea and on the
    # same land (G1 check 5), and the share of deaths from disease after the first village
    from gates import g1
    try:
        rec["g1_language_pairs"] = g1.sample_state(w)["language_pairs"]
    except Exception as ex:                          # noqa: BLE001 (recorded, never silent)
        rec["g1_language_pairs_error"] = repr(ex)
    # check 11: sampled cause chains by kind, and which kinds never happened
    from origins.sim import minorlog
    by_kind: dict = {}                                # label -> event ids; the compact log's rows follow them
    for e in w.events:
        k = CHAIN_KINDS.get(e["kind"])
        if k is not None:
            by_kind.setdefault(k, []).append(int(e["id"]))
    rows_of = {k: [(kind, minorlog.size(w, kind)) for kind in minorlog.KINDS if CHAIN_KINDS.get(kind) == k]
               for k in set(CHAIN_KINDS.values())}    # (Ben, 22 November 2026: millions of rows, not listed one by one)

    def ref_at(k, j):
        evs = by_kind.get(k, [])
        if j < len(evs):
            return {"event": evs[j]}
        j -= len(evs)
        for kind, n in rows_of[k]:
            if j < n:
                return {"log": [kind, j]}
            j -= n
        raise IndexError(j)
    chains = {}
    good = w.__dict__.setdefault("_gate_good", set())
    for k in sorted(set(CHAIN_KINDS.values())):
        total = len(by_kind.get(k, [])) + sum(n for _, n in rows_of[k])
        pos = range(total) if total <= SAMPLE_CHAINS else sorted(rng.choice(total, SAMPLE_CHAINS, replace=False))
        smp = [ref_at(k, int(j)) for j in pos]
        chains[k] = [total, len(smp), int(sum(explain.resolvable(w, r, good=good) for r in smp))]
    rec["chains_fields"] = ["events or compact-log rows of this kind", "sampled", "resolved"]
    rec["chains"] = chains
    rec["arm"] = pr.get("arm", "")
    rec["arm_params"] = ARMS.get(rec["arm"], {})
    rec["tech_pop_exponent"] = float(P.TECH_POP_EXPONENT)


def finish(w, ws, rs, seconds, pr, tag):
    """The G3 record (built by g3.finish, not written), plus the G4a measurements."""
    t0 = time.time()
    rec = g3.finish(w, ws, rs, seconds, pr, True, write=False)
    extras(w, pr, rec, np.random.default_rng([ws, rs, 41]))
    rec["record_seconds"] = round(time.time() - t0, 1)        # building the record (check 13; finding in review 034)
    rec["stage_envs"] = pr.get("stage_envs", [])               # the machine of each stage (review 040)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"run_w{ws}_s{rs}{tag}.json").write_text(json.dumps(rec))


def _rss():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def worker(jobs, budget, ckpt: Path, arm: str):
    from origins import engine, params, persist
    from origins.state import World
    g2.apply_overrides()
    params.INSTITUTIONS = True
    for k, v in ARMS.get(arm, {}).items():
        setattr(params, k, v)
    install_observers()
    tag = f"_{arm}" if arm else ""
    t_end = time.time() + budget
    for ws, rs in jobs:
        if (OUT / f"run_w{ws}_s{rs}{tag}.json").exists():
            continue
        cp, meta = ckpt / f"w{ws}_s{rs}{tag}.zip", ckpt / f"w{ws}_s{rs}{tag}.json"
        start = time.time()
        if cp.exists():
            t0 = time.time()
            w = persist.from_file(cp, g2.resume_planet(cp, ws))
            print(f"w{ws} s{rs}{tag}: restored year {w.year} ({cp.stat().st_size / 2 ** 20:.0f} MiB) in "
                  f"{time.time() - t0:.0f} s, {_rss():.2f} GB peak", flush=True)        # sizing (review 037)
            m = json.loads(meta.read_text())
            if "t" in m and int(m["t"]) != int(w.t):        # a world and probes from different checkpoints (review 036)
                raise RuntimeError(f"checkpoint {cp.name}: world at tick {w.t}, probes at tick {m['t']}")
            spent, pr = m["seconds"], m["probe"]
        else:
            w = World.new(ws, rs, _planet(ws))
            spent, pr = 0.0, g2.new_probe()
            pr["arm"] = arm
        from gates.g0 import _env
        pr.setdefault("stage_envs", []).append({**_env(), "from_year": int(w.year)})   # each stage's machine (review 040)
        _PR["pr"] = pr
        import resource
        while not g3.done(w):
            engine.step(w, 4)
            g2.probe(w, pr)
            census(w, pr)
            if w.year % 500 == 0:
                print(f"w{ws} s{rs}{tag}: year {w.year}, {w.population():,} people, {len(w.events):,} events, "
                      f"{len(w.living_bands()):,} bands living, {w.band_rows.n:,} band rows, "
                      f"{len(getattr(w, 'dz_log', [])):,} disease rows, {time.time() - start:.0f} s, "
                      f"peak memory {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
            if w.first_village is not None and "fv_deaths" not in pr:
                pr["fv_deaths"] = {"by_cause": w.accum["deaths_by_cause"].tolist(), "by_age": w.accum["deaths"].tolist()}
            if time.time() > t_end:
                g2.save_planet(cp, w.planet)
                tmp = cp.with_suffix(".tmp")
                import gc
                gc.collect()
                t0 = time.time()
                persist.to_file(w, tmp, fast=True)
                tmp.replace(cp)
                print(f"w{ws} s{rs}{tag}: saved {cp.stat().st_size / 2 ** 20:.0f} MiB in {time.time() - t0:.0f} s, "
                      f"{_rss():.2f} GB peak", flush=True)
                meta.write_text(json.dumps({"t": int(w.t), "seconds": spent + time.time() - start, "year": w.year, "probe": pr}))
                print(f"w{ws} s{rs}{tag}: checkpoint at year {w.year}", flush=True)
                return
        t0 = time.time()
        finish(w, ws, rs, spent + time.time() - start, pr, tag)
        f = OUT / f"run_w{ws}_s{rs}{tag}.json"
        print(f"w{ws} s{rs}{tag}: record {f.stat().st_size / 2 ** 20:.0f} MiB built in {time.time() - t0:.0f} s, "
              f"{_rss():.2f} GB peak", flush=True)
        _PR["pr"] = None
        print(f"w{ws} s{rs}{tag}: completed at year {w.year} in {spent + time.time() - start:.0f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "report"])
    ap.add_argument("--jobs", default="")
    ap.add_argument("--years", type=int, default=g3.MAX_YEARS)
    ap.add_argument("--budget", type=float, default=20000)
    ap.add_argument("--ckpt", default=str(ROOT / "gates" / "ckpt_g4"))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--arm", default="", choices=[""] + sorted(ARMS))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.what == "report":
        from gates.g4_report import report, INCOMPLETE
        print(report(OUT))
        if INCOMPLETE["flag"]:
            sys.exit(3)                 # published, but the workflow marks the run failed (Codex review 037)
        return
    ck = Path(a.ckpt)
    ck.mkdir(parents=True, exist_ok=True)
    jobs = [tuple(int(x) for x in j.split(":")) for j in a.jobs.split(",")]
    worker(jobs, a.budget, ck, a.arm)


if __name__ == "__main__":
    main()
