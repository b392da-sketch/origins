"""Evaluate gate G0 from the run files and write a readable report."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def _load(out: Path, pattern: str):
    return [json.loads(f.read_text()) for f in sorted(out.glob(pattern))]


def _recovered_dips(pop, start, depth=0.05, within=150):
    """Count declines of at least `depth` from a running peak that return to that peak within `within` years."""
    n, k = 0, start
    while k < len(pop) - 1:
        peak = pop[k]
        j = k + 1
        while j < len(pop) and pop[j] >= peak:
            peak = pop[j]
            k = j
            j += 1
        if j >= len(pop):
            break
        low_i = j
        while j < len(pop) and pop[j] < peak and j - k <= within:
            if pop[j] < pop[low_i]:
                low_i = j
            j += 1
        if pop[low_i] <= peak * (1 - depth) and j < len(pop) and pop[j] >= peak:
            n += 1
        k = max(j, k + 1)
    return n


def report(out: Path) -> str:
    runs = [r for r in _load(out, "run_w*_2000y.json") if r.get("status") == "completed"]
    shocks_all = [r for r in _load(out, "shock_w*.json") if r.get("status") == "completed"]
    years = sorted({s["at_year"] for s in shocks_all})
    shocks = [s for s in shocks_all if s["at_year"] == max(years)] if years else []
    early = [s for s in shocks_all if years and s["at_year"] != max(years)]
    L = []
    add = L.append
    n = len(runs)
    add(f"# Gate G0 report — 'the first people survive'\n")
    add(f"Runs found: {n} (target 100: 5 planets × 20 histories × 2,000 years). Shock pairs: {len(shocks)}.\n")
    if not n:
        return "\n".join(L)
    env = sorted({(r["env"]["python"], r["env"]["numpy"]) for r in runs})
    add(f"Environment: " + "; ".join(f"Python {a}, NumPy {b}" for a, b in env) + "\n")
    checks = []

    # 1 survival
    survived = [r for r in runs if not r["extinct"] and r["completed_years"] == r["requested_years"]]
    ext = [r for r in runs if r["extinct"]]
    ok1 = len(survived) >= 90 and n >= 100
    checks.append(("1. Survival", ok1, f"{len(survived)} of {n} runs survived 2,000 years (pass mark 90 of 100). "
                   f"Extinctions: " + (", ".join(f"planet {r['world_seed']} history {r['run_seed']} in year {r['extinct_year']}"
                                                   for r in ext) or "none")))
    # 2 no explosion
    ratios = [max((p / c for p, c in zip(r["yearly"]["population"], r["yearly"]["capacity_occupied"]) if c > 0), default=0)
              for r in survived]
    ok2 = bool(ratios) and max(ratios) <= 1.0
    checks.append(("2. No explosion", ok2, f"highest population ÷ capacity of occupied land in any year of any run: "
                   f"{max(ratios):.3f} (must stay ≤ 1.0); median of run maxima {np.median(ratios):.3f}"))
    # 3 fluctuation and recovery
    dips = [_recovered_dips(r["yearly"]["population"], 300) for r in survived]
    with_dips = sum(d >= 1 for d in dips)
    ok3 = with_dips >= 0.8 * len(survived)
    checks.append(("3. Fluctuation and recovery", ok3,
                   f"{with_dips} of {len(survived)} surviving runs show at least one population fall of 5% or more "
                   f"(after year 300) that recovers to its earlier peak within 150 years (pass mark 80%); "
                   f"median number of such recoveries per run {np.median(dips) if dips else 0:.0f}"))
    # 4 demography (pooled exposure across runs)
    lts = [r["life_table"] for r in survived]
    e0 = np.array([x["e0"] for x in lts])
    tfr = np.array([x["tfr"] for x in lts])
    s1560 = np.array([x["survive_15_to_60"] for x in lts])
    band = np.array([x["median_band"] for x in lts])
    in_range = [(25 <= a <= 40) and (4 <= b <= 7) and (15 <= c <= 60) for a, b, c in zip(e0, tfr, band)]
    ok4 = all(in_range)
    checks.append(("4. Plausible demography", ok4,
                   f"life expectancy at birth {e0.min():.1f}–{e0.max():.1f} (median {np.median(e0):.1f}; range 25–40); "
                   f"births per woman {tfr.min():.2f}–{tfr.max():.2f} (median {np.median(tfr):.2f}; range 4–7); "
                   f"median band size {band.min():.0f}–{band.max():.0f} (range 15–60); "
                   f"survival from 15 to 60: median {np.median(s1560):.2f}. "
                   f"{sum(in_range)} of {len(in_range)} runs inside all three ranges."))
    # 5 shock
    if shocks:
        rows = []
        good = 0
        for s in shocks:
            sh, co = np.array(s["shocked_area_pop"]), np.array(s["control_area_pop"])
            more_hunger = s["shock_hunger_deaths_3y"] > s["control_hunger_deaths_3y"]
            fewer_births = s["shock_births_3y"] < s["control_births_3y"]
            dip = sh[:4].min() < co[:4].min()
            y60 = min(59, len(sh) - 1)
            rec = abs(sh[y60] - co[y60]) <= 0.10 * max(co[y60], 1)
            ok = more_hunger and fewer_births and rec
            good += ok
            rows.append(f"planet {s['world_seed']}: hunger deaths in 3 years {s['shock_hunger_deaths_3y']:.0f} vs "
                        f"{s['control_hunger_deaths_3y']:.0f} without the shock; births {s['shock_births_3y']:.0f} vs "
                        f"{s['control_births_3y']:.0f}; area population after 60 years {sh[y60]:.0f} vs {co[y60]:.0f}"
                        f" ({'recovered' if rec else 'not recovered'} within 10%)")
        ok5 = good == len(shocks)
        note = ""
        if early:
            eh = sum(s["shock_hunger_deaths_3y"] for s in early)
            note = (f" (An earlier version of this test, with the shock in year {early[0]['at_year']} while land was still "
                    f"mostly empty, produced {eh:.0f} hunger deaths in {len(early)} pairs: food was not scarce, so it could "
                    f"not test the response and was replaced by this one.)")
        checks.append(("5. Shock response", ok5, f"shock in year {shocks[0]['at_year']}: {good} of {len(shocks)} paired tests pass. "
                       + "; ".join(rows) + note))
    else:
        checks.append(("5. Shock response", False, "not run"))
    # 6 spread
    spread = [r["yearly"]["occupied_cells"][-1] for r in survived]
    ok6 = all(s > 1 for s in spread)
    checks.append(("6. Spread begins", ok6, f"occupied land cells at year 2,000: {min(spread)}–{max(spread)} "
                   f"(median {np.median(spread):.0f}), from 1 at the start"))
    # 7 nothing from nothing
    fails = sum(r["invariant_failures"] for r in runs)
    checks.append(("7. Nothing from nothing", fails == 0, f"{fails} accounting failures in {n} runs "
                   f"(people checked every season against births and deaths; food against regrowth, eating and spoilage)"))
    # 8 replay
    rp = [r["replay_check"] for r in runs if r.get("replay_check") is not None]
    ok8 = bool(rp) and all(rp)
    checks.append(("8. Exact replay", ok8, f"save, reload and continue identical to uninterrupted run in {sum(rp)} of {len(rp)} "
                   f"checks at year 1,000; also covered by automated tests (reload, and different Python hash seeds)"))
    # 9 explainability
    chk = sum(r["explain_checked"] for r in runs)
    res = sum(r["explain_resolvable"] for r in runs)
    checks.append(("9. Explainability", chk > 0 and chk == res, f"{res} of {chk} sampled deaths and band events have complete cause chains"))
    # 10 speed
    secs = np.array([r["seconds"] for r in survived])
    checks.append(("10. Speed", None, f"2,000 years took {secs.min():.0f}–{secs.max():.0f} s (median {np.median(secs):.0f} s) "
                   f"in this test environment, two runs in parallel; the target was to be fixed once the first version existed"))

    add("| Check | Result | Evidence |\n|---|---|---|")
    for name, ok, ev in checks:
        mark = "PASS" if ok else ("—" if ok is None else "FAIL")
        add(f"| {name} | {mark} | {ev} |")
    pops = np.array([r["yearly"]["population"][-1] for r in survived])
    add(f"\nFinal populations at year 2,000: {pops.min():,}–{pops.max():,} (median {np.median(pops):,.0f}).")
    hunger = [r["life_table"]["deaths_by_cause"].get("hunger", 0) / max(1, r["life_table"]["deaths"]) for r in survived]
    add(f"Share of all deaths from hunger: {min(hunger):.0%}–{max(hunger):.0%} (median {np.median(hunger):.0%}).")
    return "\n".join(L)
