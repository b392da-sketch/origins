"""Evaluate gate G2 from the result files. Pass marks from docs/M2_SPECIFICATION_v1.md section 11."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from gates.g1_report import _spearman


def _load(out: Path, pattern: str):
    return [json.loads(f.read_text()) for f in sorted(out.glob(pattern))]


def report(out: Path) -> str:
    allr = [r for r in _load(out, "run_w*_s*.json") if r.get("status") == "completed"]
    runs = [r for r in allr if r["storage"]]
    knock = [r for r in allr if not r["storage"]]
    L = []
    add = L.append
    add("# Gate G2 report — 'farming is an option, not a destiny'\n")
    planets = sorted({r["world_seed"] for r in runs})
    add(f"Histories: {len(runs)} with storage on {len(planets)} planets (target 50), {len(knock)} with storage turned off "
        f"(target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.\n")
    if not runs:
        return "\n".join(L)
    env = sorted({(r["env"]["python"], r["env"]["numpy"]) for r in allr})
    add("Environment: " + "; ".join(f"Python {a}, NumPy {b}" for a, b in env) + "\n")
    add("All rates are tunable starting values (origins/params.py), not measurements.\n")
    checks = []
    farm = [r for r in runs if r["first_village_year"] is not None]

    # 1 M0/M1 still hold (the parts that apply)
    surv = sum(not r["extinct"] for r in allr)
    fails = sum(r["invariant_failures"] for r in allr)
    chk = sum(r["explain_checked"] for r in allr)
    res = sum(r["explain_resolvable"] for r in allr)
    e0 = [r["life_table"]["e0"] for r in runs]
    ok1 = surv == len(allr) and fails == 0 and chk == res
    checks.append(("1. M0 and M1 still hold", ok1,
                   f"{surv} of {len(allr)} histories survived; {fails} accounting failures (people, and food including "
                   f"harvests); life expectancy {min(e0):.1f}–{max(e0):.1f}; cause chains complete for {res:,} of {chk:,} "
                   f"sampled deaths and farming events"))

    # 2 conditions
    tw = sum(r["tending_outside_wild"] for r in runs)
    vw = sum(r["villages_without_crop"] for r in runs)
    checks.append(("2. Farming needs its conditions", tw == 0 and vw == 0,
                   f"tending begun where the species does not grow wild: {tw}; village-years with nothing to farm: {vw}"))

    # 3 adoption dates vary widely; some histories without farming
    rows3, ok3 = [], True
    for ws in planets:
        yrs = [r["first_village_year"] for r in runs if r["world_seed"] == ws and r["first_village_year"] is not None]
        none = sum(1 for r in runs if r["world_seed"] == ws and r["first_village_year"] is None)
        if yrs:
            rows3.append(f"planet {ws}: first farming village in years {min(yrs):,}–{max(yrs):,} (spread "
                         f"{max(yrs) - min(yrs):,}), none in {none} of {len(yrs) + none}")
        else:
            rows3.append(f"planet {ws}: no farming village in {none} histories")
    all_yrs = [r["first_village_year"] for r in farm]
    none_total = len(runs) - len(farm)
    spread = (max(all_yrs) - min(all_yrs)) if all_yrs else 0
    ok3 = spread >= 3000 and none_total >= 1
    checks.append(("3. Adoption dates vary widely", ok3,
                   "; ".join(rows3) + f". Across all histories: {spread:,} years between earliest and latest first village; "
                   f"{none_total} histories with no farming village by their end (pass: spread of several thousand years "
                   f"and at least one history without farming)"))

    # 4 some regions stay foraging
    kept = [r for r in farm if r["forager_cells_end"] > 0 and r["forager_capacity_end"] > 0]
    ok4 = bool(farm) and len(kept) >= 0.8 * len(farm)
    fc = [r["forager_cells_end"] for r in farm]
    checks.append(("4. Some regions stay foraging", ok4,
                   f"in {len(kept)} of {len(farm)} histories with farming, foragers still hold land at the end "
                   f"({min(fc) if fc else 0}–{max(fc) if fc else 0} areas; pass mark 80%)"))

    # 5 spread by people and example; crops beyond their wild range
    grow, beyond = 0, 0
    for r in farm:
        v = [x for x in r["villages"] if x[1] > 0]
        if len(v) >= 2 and v[-1][1] > v[0][1]:
            grow += 1
        if any(x[2] > 0 for x in r["villages"]):
            beyond += 1
    ok5 = bool(farm) and grow >= 0.8 * len(farm) and beyond >= 0.5 * len(farm)
    checks.append(("5. Farming spreads", ok5,
                   f"number of villages grows after the first in {grow} of {len(farm)} histories; crops or herds raised "
                   f"where they never grew wild in {beyond} of {len(farm)}"))

    # 6 demographic transition: farmers' births per person and density vs foragers'
    br_ratio, dens_ratio = [], []
    for r in farm:
        d = np.array(r["demog"], dtype=float)
        if len(d) < 3:
            continue
        # births between samples, per person-year, in village cells vs forager cells (last half of the history)
        h = d[len(d) // 2:]
        db_f = np.diff(h[:, 3]) / np.maximum(h[1:, 1] * 25, 1)
        db_v = np.diff(h[:, 6]) / np.maximum(h[1:, 4] * 25, 1)
        ok_rows = (h[1:, 4] > 0) & (h[1:, 1] > 0)
        if ok_rows.sum() >= 2:
            br_ratio.append(float(np.mean(db_v[ok_rows]) / max(np.mean(db_f[ok_rows]), 1e-9)))
            dens_ratio.append(float(np.mean(h[ok_rows, 4] / np.maximum(h[ok_rows, 5], 1)) /
                                    max(np.mean(h[ok_rows, 1] / np.maximum(h[ok_rows, 2], 1)), 1e-9)))
    ok6 = bool(br_ratio) and np.median(br_ratio) > 1 and np.median(dens_ratio) > 1
    checks.append(("6. Demographic transition", ok6,
                   (f"births per person in farming land ÷ foraging land: median {np.median(br_ratio):.2f} "
                    f"({min(br_ratio):.2f}–{max(br_ratio):.2f}); people per area, farming ÷ foraging: median "
                    f"{np.median(dens_ratio):.1f}" if br_ratio else "not enough farming to compare")
                   + " (both must exceed 1)"))

    # 7 specialists follow surplus
    rhos = []
    for r in farm:
        s = np.array(r["spec_log"], dtype=float)
        if len(s) >= 10:
            rhos.append(_spearman(s[:, 2], s[:, 3]))
    rhos = np.array(rhos) if rhos else np.array([np.nan])
    ok7 = np.nanmedian(rhos) > 0.3
    checks.append(("7. Specialists follow surplus", ok7,
                   f"rank correlation between surplus per person and the share of specialists, across bands and years: "
                   f"median {np.nanmedian(rhos):.2f} ({np.nanmin(rhos):.2f}–{np.nanmax(rhos):.2f}) (pass: above 0.3)"))

    # 8 knock-out
    if knock:
        spec_k = sum(sum(x[3] for x in r["spec_log"]) for r in knock)
        g_k = [x[2] for r in knock for x in r["gini_log"]]
        ok8 = spec_k == 0 and (not g_k or np.median(g_k) < 0.1)
        checks.append(("8. No storage, no specialists", ok8,
                       f"{len(knock)} histories with storage turned off: specialists recorded {spec_k:.0f}; household "
                       f"inequality {('median %.2f' % np.median(g_k)) if g_k else 'none recorded (no property)'}"))
    else:
        checks.append(("8. No storage, no specialists", False, "knock-out histories not run"))

    # 9 inequality rises with time and surplus
    rt, rs = [], []
    for r in farm:
        g = np.array(r["gini_log"], dtype=float)
        if len(g) < 10:
            continue
        age = g[:, 5]                                     # years since the band became a village
        rt.append(_spearman(age, g[:, 2]))
        rs.append(_spearman(g[:, 3], g[:, 2]))
    ok9 = bool(rt) and np.nanmedian(rt) > 0.2 and np.nanmedian(rs) > 0
    checks.append(("9. Property and inequality", ok9,
                   (f"rank correlation of household inequality with the age of the village: median {np.nanmedian(rt):.2f}; "
                    f"with surplus per person: median {np.nanmedian(rs):.2f}" if rt else "not enough villages with property")
                   + " (pass: clearly positive with age, positive with surplus)"))

    # 10 traceable transitions
    checks.append(("10. Traceable transition", ok1 and chk == res,
                   f"every sampled first-tending, first-cultivation, first-domestication and first-village event has a "
                   f"complete cause chain ({res:,} of {chk:,} references resolved, including deaths)"))

    # 11 speed
    secs = np.array([r["seconds"] for r in allr])
    yrs = np.array([r["completed_years"] for r in allr])
    checks.append(("11. Speed", None, f"histories ran {yrs.min():,}–{yrs.max():,} years in {secs.min():.0f}–{secs.max():.0f} s "
                   f"of computing (median {np.median(secs):.0f} s), one history per GitHub machine"))

    add("| Check | Result | Evidence |\n|---|---|---|")
    for name, ok, ev in checks:
        add(f"| {name} | {'PASS' if ok else ('—' if ok is None else 'FAIL')} | {ev} |")
    return "\n".join(L)
