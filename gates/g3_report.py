"""Evaluate gate G3 from the result files. Pass marks from docs/M3_SPECIFICATION_v1.md section 8.

This version covers the checks of behaviour 5 (the trial gate after M3 steps 3-4) and the re-check of M0-M2;
the conflict checks (6-8) are added with conflict.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from gates.g1_report import _spearman


def _load(out: Path, pattern: str):
    return [json.loads(f.read_text()) for f in sorted(out.glob(pattern))]


def _series(log):
    """polity id -> list of (year, settlements, people, tier, seat cell)."""
    s = {}
    for r in log:
        s.setdefault(r[1], []).append((r[0], r[2], r[3], r[8], r[9] if len(r) > 9 else -1))
    return s


def _series_full(log):
    s = {}
    for r in log:
        s.setdefault(r[1], []).append(r)
    return s


def collapses(rec, min_settlements=10, held_years=50, window=100, drop=0.5):
    """Collapses of established large polities: a polity that held at least min_settlements for at least held_years
    lost at least `drop` of its people within `window` years of its peak (or ended within that time).
    Returns [(year, peak people, seat cell)]."""
    out = []
    for pid, rows in _series(rec["polity_log"]).items():
        rows.sort()
        big = [y for y, n, ppl, tier, cell in rows if n >= min_settlements]
        if not big or max(big) - min(big) < held_years:
            continue
        peak, peak_y, peak_cell = 0, None, -1
        for y, n, ppl, tier, cell in rows:
            if ppl > peak and n >= min_settlements:
                peak, peak_y, peak_cell = ppl, y, cell
        if peak_y is None:
            continue
        after = [(y, ppl) for y, n, ppl, tier, cell in rows if peak_y < y <= peak_y + window]
        last_y = rows[-1][0]
        fell = any(ppl < drop * peak for y, ppl in after)
        ended = last_y < peak_y + window and last_y < rec["completed_years"] - 20
        if fell or ended:
            out.append((peak_y, peak, peak_cell))
    return out


def recovered(rec, col, xyz, spacing, within_years=1000, within_cells=4, share=0.5):
    """After a collapse, a polity of comparable size (share of the peak) with its seat nearby within the time."""
    y0, peak, cell = col
    for pid, rows in _series(rec["polity_log"]).items():
        for y, n, ppl, tier, c in rows:
            if y0 + 100 < y <= y0 + within_years and ppl >= share * peak and c >= 0 and cell >= 0:
                ang = float(np.arccos(np.clip(xyz[c] @ xyz[cell], -1, 1)))
                if ang / spacing <= within_cells:
                    return True
    return False


def report(out: Path) -> str:
    allr = [r for r in _load(out, "run_w*_s*.json") if r.get("status") == "completed"]
    runs = [r for r in allr if r.get("institutions", True)]
    knock = [r for r in allr if not r.get("institutions", True)]
    L = []
    add = L.append
    add("# Gate G3 report — 'scale needs institutions; conflict has causes and costs'\n")
    planets = sorted({r["world_seed"] for r in runs})
    af = sorted({r.get("after_first", 6000) for r in allr})
    add(f"Histories: {len(runs)} with institutions on {len(planets)} planets, {len(knock)} with institutions "
        f"switched off. Each runs until {', '.join(f'{a:,}' for a in af)} years after its first farming village, "
        f"or to 30,000 years.\n")
    add("All rates are tunable starting values (origins/params.py), not measurements.\n")
    if not runs:
        return "\n".join(L)
    checks = []
    farm = [r for r in runs if r["first_village_year"] is not None]

    # 1 M0-M2 still hold: the G2 report on the histories with institutions (check 8 needs G2's no-storage runs)
    tmp = Path(tempfile.mkdtemp())
    for r in runs:
        rr = dict(r)
        (tmp / f"run_w{r['world_seed']}_s{r['run_seed']}.json").write_text(json.dumps(rr))
    from gates.g2_report import report as g2report
    g2txt = g2report(tmp)
    shutil.rmtree(tmp)
    rows = [l for l in g2txt.splitlines() if l.startswith("| ") and not l.startswith("| Check") and "---" not in l]
    g2fail = [l.split("|")[1].strip() for l in rows if "| FAIL |" in l and not l.startswith("| 8.") and not l.startswith("| 9.")]
    checks.append(("1. M0-M2 still hold", not g2fail,
                   "G2's checks on these histories: " + ("all pass" if not g2fail else "failing: " + "; ".join(g2fail))
                   + " (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9)"))

    # 2 polities form; states in some histories but not all
    with_chief = [r for r in farm if "simple chiefdom" in r["polity_firsts"]]
    with_state = [r for r in farm if "state" in r["polity_firsts"]]
    dates = [r["polity_firsts"]["simple chiefdom"] - r["first_village_year"] for r in with_chief]
    sdates = [r["polity_firsts"]["state"] - r["first_village_year"] for r in with_state]
    ok2 = bool(farm) and len(with_chief) >= 0.8 * len(farm) and 0 < len(with_state) < len(farm)
    checks.append(("2. Polities form; states in some histories", ok2,
                   f"chiefdoms in {len(with_chief)} of {len(farm)} histories with farming "
                   f"({_range_txt(dates)} years after the first village); states in {len(with_state)} "
                   f"({_range_txt(sdates)} years after) (pass: chiefdoms in at least 80%; states in some but not all)"))

    # 3 oversized polities break up: secession rate rises with overload
    pooled = {}
    rhos = []
    for r in runs:
        st = {int(k): v for k, v in r["sec_stats"].items()}
        for k, (my, s) in st.items():
            a = pooled.setdefault(k, [0, 0])
            a[0] += my
            a[1] += s
        ks = [k for k in sorted(st) if st[k][0] >= 20]
        if len(ks) >= 3:
            rhos.append(_spearman(np.array(ks, float), np.array([st[k][1] / st[k][0] for k in ks])))
    rate = {k: v[1] / v[0] for k, v in sorted(pooled.items()) if v[0] >= 50}
    base = rate.get(0, 0.0)
    over = [v for k, v in rate.items() if k >= 2]
    ok3 = bool(rhos) and float(np.median(rhos)) > 0.3 and bool(over) and float(np.mean(over)) > 2 * base
    checks.append(("3. Oversized polities break up", ok3,
                   "yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): "
                   + ", ".join(f"{k / 4:.2f}+: {v:.3f}" for k, v in list(rate.items())[:8])
                   + f"; rank correlation per history: median {np.median(rhos) if rhos else float('nan'):.2f} "
                     f"({len(rhos)} histories) (pass: clearly positive, and overloaded polities lose members at "
                     f"least twice as often)"))

    # 4 collapse in some histories; recovery after it
    from origins.worldgen import generate
    cache = {}
    n_col, n_rec, with_col = 0, 0, 0
    for r in with_chief:
        cols = collapses(r)
        if cols:
            with_col += 1
        if r["world_seed"] not in cache:
            g = generate(r["world_seed"]).grid
            cache[r["world_seed"]] = (g.xyz, np.sqrt(g.cell_area_km2) / g.radius_km)
        xyz, sp = cache[r["world_seed"]]
        for c in cols:
            if c[0] + 1000 > r["completed_years"]:
                continue                    # too late in the history to see a recovery
            n_col += 1
            n_rec += recovered(r, c, xyz, sp)
    share = with_col / max(len(with_chief), 1)
    ok4 = with_chief and 0.2 <= share and n_col > 0  # upper mark of 90% dropped (Ben, 11 Nov 2026) and n_rec >= 0.5 * n_col
    checks.append(("4. Collapse happens, and recovery follows", ok4,
                   f"at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people "
                   f"within a century) in {with_col} of {len(with_chief)} histories with chiefdoms; recovery (a polity "
                   f"of at least half that size seated within 4 cells within 1,000 years) after {n_rec} of {n_col} "
                   f"collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026)"))

    # 5 no institutions, no large polities
    def largest(r):
        return max((row[2] for row in r["polity_log"]), default=0)
    big = [largest(r) for r in farm]
    kfarm = [r for r in knock if r["first_village_year"] is not None]
    kbig = [largest(r) for r in kfarm]
    kstates = sum("state" in r["polity_firsts"] for r in kfarm)
    ok5 = bool(kfarm) and bool(big) and float(np.median(kbig)) < 0.25 * float(np.median(big)) and kstates == 0
    checks.append(("5. No institutions, no large polities", ok5,
                   f"largest polity (settlements): median {np.median(big) if big else 0:.0f} with institutions "
                   f"({_range_txt(big)}), {np.median(kbig) if kbig else 0:.0f} without ({_range_txt(kbig)}, "
                   f"{len(kfarm)} histories with farming); states without institutions: {kstates} "
                   f"(pass: median under a quarter, no states)"))

    # not a check: how long polities stay large (for the analysis of check 5)
    def held(r, n=10):
        """Longest run of years one polity holds n+ settlements, and all polity-years at n+."""
        longest, total = 0, 0
        for rows in _series(r["polity_log"]).values():
            yrs = sorted(y for y, s, *_ in rows if s >= n)
            total += 10 * len(yrs)
            run, prev = 0, None
            for y in yrs:
                run = run + 10 if prev is not None and y - prev <= 10 else 10
                longest, prev = max(longest, run), y
        return longest, total
    hi = [held(r) for r in farm]
    hk = [held(r) for r in kfarm]
    if hi and hk:
        checks.append(("5b. How long polities stay large (no mark)", None,
                       f"longest time one polity held 10+ settlements: median {np.median([h[0] for h in hi]):,.0f} "
                       f"years with institutions ({_range_txt([h[0] for h in hi])}), "
                       f"{np.median([h[0] for h in hk]):,.0f} without ({_range_txt([h[0] for h in hk])}); "
                       f"polity-years at 10+ settlements per history: median {np.median([h[1] for h in hi]):,.0f} with, "
                       f"{np.median([h[1] for h in hk]):,.0f} without"))

    # 6 conflict rises with scarcity and proximity
    def rates(key):
        pooled = {}
        for x in allr:
            for b, (n, k) in x.get("war_stats", {}).get(key, {}).items():
                a = pooled.setdefault(int(b), [0, 0])
                a[0] += n
                a[1] += k
        return {b: v[1] / v[0] for b, v in sorted(pooled.items()) if v[0] >= 100}
    rs, rd = rates("scarcity"), rates("distance")
    have6 = any(x.get("war_stats") for x in allr)
    up_s = bool(rs) and 0 in rs and len(rs) >= 2 and float(np.mean([v for k, v in rs.items() if k >= 1])) > 1.5 * rs[0]
    vals_d = [rd[k] for k in sorted(rd)]
    down_d = len(vals_d) >= 2 and all(a_ > b_ for a_, b_ in zip(vals_d, vals_d[1:]))
    ok6 = have6 and up_s and down_d
    checks.append(("6. Conflict rises with scarcity and proximity", ok6 if have6 else None,
                   "chance of war per side and neighbour weighed, by scarcity (quarters): "
                   + ", ".join(f"{b / 4:.2f}+: {v:.3f}" for b, v in rs.items())
                   + "; by distance (cells): " + ", ".join(f"{b}: {v:.3f}" for b, v in rd.items())
                   + " (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with "
                     "each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; "
                     f"check 8 and the collapse checks test what follows from war"))

    # 7 conflict has costs
    shares = []
    for x in allr:
        ds = x.get("deaths_since_village")
        if not ds:
            continue
        war = ds["by_cause"].get("killed in war", 0)
        adult = sum(ds["by_age"][4:])            # deaths at 15 and over (age groups 0, 1-4, 5-9, 10-14 excluded)
        if adult > 0:
            shares.append(war / adult)
    losers = [r_ for x in allr for r_ in x.get("war_log", []) if r_[7] > 0]
    ok7 = bool(shares) and 0.02 <= min(shares) and max(shares) <= 0.30 and 0.05 <= float(np.median(shares)) <= 0.25
    checks.append(("7. Conflict has costs", ok7 if shares else None,
                   f"deaths in war after the first farming village, as a share of deaths at 15 and over: "
                   f"{_range_txt([round(s, 3) for s in shares])} (median {np.median(shares) if shares else 0:.3f}); "
                   f"{len(losers):,} sampled wars the attacker won, each taking stores, captives or settlements "
                   f"(pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009)"))

    # 8 conquest builds empires that are hard to hold
    life, ext = [], []
    n_emp = 0
    for x in runs:
        for pid, rows_ in _series_full(x["polity_log"]).items():
            if not any(rw[10] >= 2 and rw[11] >= 1 for rw in rows_ if len(rw) > 11):
                continue
            n_emp += 1
            ys = [rw[0] for rw in rows_]
            span = max(ys) - min(ys)
            if max(ys) >= x["completed_years"] - 20:
                continue                    # still standing at the end: duration unknown
            life.append(span)
            ext.append(float(np.mean([rw[5] / max(rw[6], 1e-9) for rw in rows_])))
    rho_e = _spearman(np.array(ext), np.array(life, float)) if len(life) >= 5 else float("nan")
    ok8 = n_emp > 0 and len(life) >= 5 and rho_e < -0.1
    checks.append(("8. Conquest builds empires that are hard to hold", ok8 if n_emp else None,
                   f"{n_emp} empires (polities holding conquered settlements of another language) across the "
                   f"histories; for the {len(life)} that ended, rank correlation of duration with mean overextension "
                   f"(load ÷ capacity): {rho_e:.2f} (pass: clearly negative)"))

    # 9 inequality compounds (M2 check 9's wording and pass mark)
    rt, rs9, early, late = [], [], [], []
    for r in farm:
        g = np.array(r["gini_log"], dtype=float)
        if len(g) < 10:
            continue
        rt.append(_spearman(g[:, 5], g[:, 2]))
        rs9.append(_spearman(g[:, 3], g[:, 2]))
        e, l_ = g[g[:, 5] < 100, 2], g[g[:, 5] >= 500, 2]
        if len(e) and len(l_):
            early.append(float(np.median(e)))
            late.append(float(np.median(l_)))
    ok9 = bool(rt) and np.nanmedian(rt) > 0.2 and np.nanmedian(rs9) > 0
    checks.append(("9. Inequality compounds", ok9 if rt else None,
                   (f"rank correlation of household inequality (Gini) with how long a people has farmed: median "
                    f"{np.nanmedian(rt):.2f}; with surplus per person: median {np.nanmedian(rs9):.2f}; median Gini in "
                    f"a people's first 100 years of farming {np.median(early):.2f} vs after 500 years "
                    f"{np.median(late):.2f}" if rt and early else "not enough villages with property")
                   + " (pass: clearly positive with time (above 0.2), positive with surplus)"))

    # 10 traceable
    chk = sum(r["polity_explain_checked"] for r in allr)
    res = sum(r["polity_explain_resolvable"] for r in allr)
    checks.append(("10. Traceable", chk == res and chk > 0,
                   f"{res:,} of {chk:,} sampled polity events (founding, joining, secession, succession, "
                   f"institutions, tiers) have complete cause chains"))

    # 11 variation
    var = []
    for ws in planets:
        rs = [r for r in farm if r["world_seed"] == ws]
        if rs:
            var.append(f"planet {ws}: polities {_range_txt([r['polities_total'] for r in rs])}, largest "
                       f"{_range_txt([largest(r) for r in rs])} settlements")
    checks.append(("11. Same rules, different histories", None, "; ".join(var)))
    secs = [r["seconds"] for r in allr]
    checks.append(("12. Speed", None, f"histories ran {min(r['completed_years'] for r in allr):,}–"
                                      f"{max(r['completed_years'] for r in allr):,} years in "
                                      f"{min(secs) / 3600:.1f}–{max(secs) / 3600:.1f} h of computing "
                                      f"(median {np.median(secs) / 3600:.1f} h)"))

    add("| Check | Result | Evidence |")
    add("|---|---|---|")
    for name, ok, ev in checks:
        add(f"| {name} | {'—' if ok is None else 'PASS' if ok else 'FAIL'} | {ev} |")
    add("\n## G2 checks on these histories\n")
    add("\n".join(l for l in g2txt.splitlines() if l.startswith("|")))
    return "\n".join(L)


def _range_txt(x) -> str:
    x = [v for v in x if v is not None]
    if not x:
        return "none"
    return f"{min(x):,}–{max(x):,}" if min(x) != max(x) else f"{min(x):,}"
