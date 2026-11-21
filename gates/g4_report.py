"""Evaluate gate G4a from the result files. Checks and pass marks: docs/M4_SPECIFICATION_v1.md section 9; how each is
measured: docs/G4A_GATE_PLAN.md (approved by Ben, 21 November 2026, with the review-034 decisions). All rates in the
simulation are tunable starting values, not measurements.

Ben's readings (21 November 2026): "falls clearly" (check 6) is below half the main arm's median; "most histories" is
two thirds of those where a check can be measured; a check counts as measured only if at least half the histories can
measure it (MIN_COVERAGE). Check 10: a disease persists if a spell on a cell lasts PERSIST_YEARS or more; herds and
dense populations meet in a spell-year with HERDERS or more herding on the cell and AROUND or more people around.

A check is PASS or FAIL only when it is measured; otherwise "—" with the reason, never a pass by default (Codex
review 034).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from gates.g1_report import _spearman

MOST = 2 / 3                    # "most histories" (Ben, 21 November 2026)
MIN_COVERAGE = 0.5              # a check is measured only if at least half the histories can measure it (Ben, 21 Nov)
KNOCK_SHARE = 0.5               # check 6: the knock-out's median below this share of the main arm's (Ben, 21 Nov 2026)
PERSIST_YEARS = 10              # check 10 (Ben, 21 November 2026)
HERDERS = 100
AROUND = 5000
CENSUS_YEARS = 100
REQUIRED_CHAINS = ("invention", "loss", "adoption", "goods arrival", "gift exchange", "trade route", "help in need",
                   "new disease", "outbreak", "land and hunger", "land and moves", "place name")


def _load(out: Path):
    return [json.loads(f.read_text()) for f in sorted(out.glob("run_w*_s*.json"))]


def _med(x):
    x = [v for v in x if v is not None and not (isinstance(v, float) and np.isnan(v))]
    return float(np.median(x)) if x else float("nan")


def _verdict(flags, n_hist):
    """(PASS/FAIL/None, text): two thirds of the measurable histories, if at least half the histories are measurable."""
    m = [f for f in flags if f is not None]
    if not m or len(m) < MIN_COVERAGE * n_hist:
        return None, f"measurable in {len(m)} of {n_hist} histories (needs at least half)"
    return sum(m) >= MOST * len(m), f"{sum(m)} of {len(m)} measurable histories (of {n_hist})"


def _rows(r):
    """Census rows that cover a whole century: the band lived to the next census and the century ended before the
    history did (Codex review 034, finding 5)."""
    end = r.get("end_year", 10 ** 9)
    return [row for row in r.get("census", []) if row[-1] is True and row[0] + CENSUS_YEARS <= end]


def invention_rho(r, col):
    """Spearman over whole band-centuries: inventions in the century against census column col (3 connected people,
    5 mean need of what it could invent); foragers and farmers apart (farm share 0.5). Rows with nothing it could
    invent are left out."""
    inv = {}
    for y, b, t in r.get("inventions_by_band", []):
        inv[(b, (y // CENSUS_YEARS) * CENSUS_YEARS)] = inv.get((b, (y // CENSUS_YEARS) * CENSUS_YEARS), 0) + 1
    xs, ys, farm = [], [], []
    for row in _rows(r):
        if row[6] <= 0 or row[col] is None:
            continue
        xs.append(row[col])
        ys.append(inv.get((row[1], row[0]), 0))
        farm.append(row[8] >= 0.5)
    xs, ys, farm = np.array(xs, float), np.array(ys, float), np.array(farm, dtype=bool)
    if len(xs) < 20 or ys.sum() == 0:
        return float("nan"), float("nan"), float("nan"), len(xs)
    sp = lambda m: _spearman(xs[m], ys[m]) if m.sum() >= 20 and ys[m].sum() > 0 else float("nan")   # noqa: E731
    return _spearman(xs, ys), sp(~farm), sp(farm), len(xs)


def loss_by_reach(r):
    """Henrich-kind losses (practised, for want of skill) per whole band-century, by fifth of connected people (equal
    counts; empty fifths dropped), and the change in techniques known against the change in connected people
    between consecutive censuses of the same band (knowledge falls where contact falls)."""
    lost = {}
    for y, b, t, practised, _c in r.get("losses_by_band", []):
        if practised:
            key = (b, (y // CENSUS_YEARS) * CENSUS_YEARS)
            lost[key] = lost.get(key, 0) + 1
    rows = _rows(r)
    if len(rows) < 50:
        return None, float("nan"), float("nan"), 0
    reach = np.array([row[3] for row in rows], float)
    rate = np.array([lost.get((row[1], row[0]), 0) for row in rows], float)
    order = np.argsort(reach, kind="stable")
    fifths = np.array_split(order, 5)
    rates = [float(rate[f].mean()) for f in fifths if len(f)]
    by = {}
    for row in r.get("census", []):
        by.setdefault(row[1], []).append(row)
    dr, dk = [], []
    for b, rs in by.items():
        rs.sort(key=lambda x: x[0])
        for a, c in zip(rs, rs[1:]):
            if c[0] - a[0] == CENSUS_YEARS:
                dr.append(np.log1p(c[3]) - np.log1p(a[3]))
                dk.append(c[7] - a[7])
    rk = _spearman(dr, dk) if len(dr) >= 20 else float("nan")
    return rates, _spearman(np.arange(len(rates)), rates), rk, int(rate.sum())


def _g3(runs):
    tmp = Path(tempfile.mkdtemp())
    for r in runs:
        (tmp / f"run_w{r['world_seed']}_s{r['run_seed']}.json").write_text(json.dumps(r))
    from gates.g3_report import report as g3report
    txt = g3report(tmp)
    shutil.rmtree(tmp)
    return txt


def report(out: Path) -> str:
    allr = [r for r in _load(out) if r.get("status") == "completed"]
    runs = [r for r in allr if not r.get("arm")]
    arms = {}
    for r in allr:
        if r.get("arm"):
            arms.setdefault(r["arm"], []).append(r)
    n = len(runs)
    L = []
    add = L.append
    add("# Gate G4a report — 'knowledge and exchange'\n")
    add(f"Main histories: {n} on {len(sorted({r['world_seed'] for r in runs}))} planets. Arms: "
        + (", ".join(f"{a} {len(v)}" for a, v in sorted(arms.items())) or "none")
        + ". All rates are tunable starting values (origins/params.py), not measurements.\n")
    if not runs:
        return "\n".join(L)
    checks = []

    # 1 M0-M3 still hold: G3's own table; a check without a verdict is unmeasured, not passed (finding 4)
    g3txt = _g3(runs)
    main = g3txt.split("\n## G2 checks")[0]
    rows = [l for l in main.splitlines() if l.startswith("| ") and not l.startswith("| Check") and "---" not in l]
    waived = {"5": "needs no-institution histories, not run in G4a (waived in G3 run 3 too)"}
    nomark = {"11", "12"}
    fails, unmeasured = [], []
    for l in rows:
        name = l.split("|")[1].strip()
        num = name.split(".")[0]
        res = l.split("|")[2].strip()
        if num in waived or num in nomark:
            continue
        if res == "FAIL":
            fails.append(name)
        elif res != "PASS":
            unmeasured.append(name)
    ok1 = False if fails else (None if unmeasured else True)
    checks.append(("1. M0-M3 still hold", ok1,
                   "G3's checks on these histories (each carrying G2's, and G2's carrying M0-M1's survival, accounting "
                   "and cause chains): " + ("failing: " + "; ".join(fails) if fails else "none failing")
                   + ("; without a verdict: " + "; ".join(unmeasured) if unmeasured else "")
                   + ". Not re-measured: G3 check 5 (" + waived["5"] + "). Carried forward from M3: check 9's herd half "
                   "(see G3's check 9 below). M1's carried-forward items are re-measured beside the checks."))

    # 2 innovation tracks connected population; 3 need beside it (finding 5)
    rho2 = [invention_rho(r, 3) for r in runs]
    rho3 = [invention_rho(r, 5) for r in runs]
    meas2 = [x[0] for x in rho2 if not np.isnan(x[0])]
    m2 = _med(meas2)
    ok2 = (m2 > 0.3) if len(meas2) >= MIN_COVERAGE * n else None
    checks.append(("2. Innovation tracks connected population", ok2,
                   f"median Spearman, over whole band-centuries, of inventions with the connected people invention "
                   f"uses: {m2:.2f} in {len(meas2)} of {n} measurable histories (foragers {_med([x[1] for x in rho2]):.2f}, "
                   f"farmers {_med([x[2] for x in rho2]):.2f}) (pass: median above 0.3)"))
    checks.append(("3. Risk matters too, or doesn't (no mark)", None,
                   f"median Spearman of inventions with the mean need of what the band could invent: "
                   f"{_med([x[0] for x in rho3]):.2f} (foragers {_med([x[1] for x in rho3]):.2f}, farmers "
                   f"{_med([x[2] for x in rho3]):.2f})"))

    # 4 diffusion follows contact (finding 6)
    shares, rhos4 = [], []
    for r in runs:
        s = [o / k for _b, k, o in r.get("learned_share", []) if k]
        shares.append(_med(s) if len(s) >= 10 else None)
        per = {}
        for row in r.get("first_adoptions", []):
            steps, after = row[4], row[6]
            if steps is not None and after is not None:
                per.setdefault(row[2], []).append((steps, after))
        tr = [_spearman([a for a, _ in v], [b for _, b in v]) for v in per.values() if len(v) >= 10]
        rhos4.append(_med(tr) if tr else None)
    m4a = _med(shares)
    ok4a = (m4a > 0.6) if sum(x is not None for x in shares) >= MIN_COVERAGE * n else None
    ok4b, t4b = _verdict([None if x is None or np.isnan(x) else x > 0 for x in rhos4], n)
    ok4 = None if ok4a is None or ok4b is None else (ok4a and ok4b)
    checks.append(("4. Diffusion follows contact", ok4,
                   f"(a) median share of a people's techniques that its line last acquired from others (recorded "
                   f"acquisitions; lost and relearned counts as learned): {m4a:.2f} (pass: above 0.6); (b) time to "
                   f"reach a people rises with transmission steps from an invention, through any route (contact, "
                   f"partners, trade, migrants, captives), in {t4b} (median per-technique Spearman {_med(rhos4):.2f}; "
                   f"pass: most)"))

    # 5 isolation causes loss (finding 6)
    flags, rq_all, rk_all = [], [], []
    for r in runs:
        rates, rq, rk, nloss = loss_by_reach(r)
        if rates is None or np.isnan(rq) or np.isnan(rk):
            flags.append(None)
            continue
        flags.append(nloss > 0 and rq < 0 and rk > 0)
        rq_all.append(rq)
        rk_all.append(rk)
    ok5, t5 = _verdict(flags, n)
    checks.append(("5. Isolation causes loss", ok5,
                   f"losses for want of skill occur, their rate falls across fifths of connected people (median "
                   f"Spearman {_med(rq_all):.2f}), and a band's techniques fall when its contact falls between censuses "
                   f"(median Spearman of the changes {_med(rk_all):.2f}), in {t5} (pass: most)"))

    # 6 knock-out (finding 5): the approved rule on all histories, and the paired change as a robustness check
    knock = arms.get("nopop", [])
    mk = _med([invention_rho(r, 3)[0] for r in knock])
    pair = {(r["world_seed"], r["run_seed"]): invention_rho(r, 3)[0] for r in runs}
    diffs = [invention_rho(r, 3)[0] - pair[(r["world_seed"], r["run_seed"])] for r in knock
             if (r["world_seed"], r["run_seed"]) in pair]
    ok6 = None
    if knock and not np.isnan(mk) and not np.isnan(m2):
        ok6 = bool(m2 > 0 and mk < KNOCK_SHARE * m2)
    checks.append(("6. Knock-out: no population effect", ok6,
                   (f"check 2's median with the population term off: {mk:.2f} ({len(knock)} histories), against "
                    f"{m2:.2f} with it (pass: below half, and the main arm's median positive); paired change on the "
                    f"same planet and seed: median {_med(diffs):+.2f} over {len(diffs)} pairs") if knock
                   else "no knock-out histories"))

    # 7 trade follows supply and distance (finding 7)
    fl, hl, rf, rh = [], [], {}, []
    for r in runs:
        fo = r.get("goods_falloff", {})
        ok_goods = []
        for g in ("fine_stone", "salt", "shell"):
            b = fo.get(g)
            if not b or len(b) < 4:
                continue
            x = _spearman([int(k) for k in b], [b[k][1] for k in b])
            rf.setdefault(g, []).append(x)
            ok_goods.append(x < 0)
        fl.append(all(ok_goods) if ok_goods else None)
        h = r.get("help_by_year", {})
        ys = [y for y, v in h.items() if v[0] > 0]                     # years with any band holding partners
        if len(ys) >= 20:
            need = [h[y][1] / h[y][0] for y in ys]                        # share of partnered band-seasons short
            gave = [h[y][3] / max(h[y][0], 1) for y in ys]                # food given per partnered band-season
            x = _spearman(need, gave)
            rh.append(x)
            hl.append(x > 0 if not np.isnan(x) else None)
        else:
            hl.append(None)
    okf, tf = _verdict(fl, n)
    okh, th = _verdict(hl, n)
    ok7 = None if okf is None or okh is None else (okf and okh)
    checks.append(("7. Trade follows supply and distance", ok7,
                   f"fine stone, salt and shell per person all fall with cell steps from their sources in {tf} "
                   f"(median Spearman: " + ", ".join(f"{g} {_med(v):.2f}" for g, v in rf.items())
                   + f"); among bands with partners, food given per band-season rises with the share short before "
                   f"help, year by year (zero years kept), in {th} (median Spearman {_med(rh):.2f}) (pass: both, most)"))

    # 8 conserved, over the whole roster
    inv = sum(r.get("invariant_failures", 0) for r in allr)
    checks.append(("8. Goods are conserved", inv == 0 if allr else None,
                   f"{inv} accounting failures (goods, food, people) in the {len(allr)} completed histories (pass: none). "
                   f"Histories missing from the roster are listed under 'Roster'."))

    # 9 the land answers back (finding 3), as exposure, not cause (Ben, 20 November 2026)
    fl9, det = [], {"yield": [], "salt": [], "game": []}
    for r in runs:
        cells = r.get("land_cells", [])
        if not cells:
            fl9.append(None)
            continue
        # fields: 0 cell, 1 lived, 2 fertility, 3 salt, 4 slow game, 5 fast game, 6 forest, 7 crop factor first,
        # 8 last, 9 years cropped, 10 years irrigated, 11 village years, 12 unbroken, 13 hunting pressure,
        # 14 years hunted, 15 rain
        crop = [c for c in cells if c[9] >= 20 and c[7] is not None]
        y_ok = (_spearman([c[9] for c in crop], [c[8] for c in crop]) < 0
                and np.mean([c[8] < c[7] for c in crop]) > 0.5) if len(crop) >= 10 else None
        dry = [c for c in cells if c[10] > 0 and c[15] < 500]
        s_ok = (_spearman([c[10] for c in dry], [c[3] for c in dry]) > 0) if len(dry) >= 5 else None
        hunted = [c for c in cells if c[13] is not None and c[14] >= 20]
        g_ok = (_spearman([c[13] for c in hunted], [c[4] for c in hunted]) < 0) if len(hunted) >= 10 else None
        ev = r.get("land_events", {})
        happened = ev.get("land_hunger", 0) > 0 and (ev.get("land_move", 0) + ev.get("land_abandoned", 0)) > 0
        parts = [p for p in (y_ok, g_ok) if p is not None]
        if len(parts) < 2:
            fl9.append(None)
        else:
            fl9.append(all(parts) and (s_ok is not False) and happened)
        det["yield"].append(y_ok)
        det["salt"].append(s_ok)
        det["game"].append(g_ok)
    ok9, t9 = _verdict(fl9, n)
    cnt = lambda v: f"{sum(1 for x in v if x)} of {sum(1 for x in v if x is not None)}"   # noqa: E731
    checks.append(("9. The land answers back", ok9,
                   f"crop yields fall with years cropped (yields in {cnt(det['yield'])} histories), slow game is lower "
                   f"where hunting pressure is high ({cnt(det['game'])}), salt rises with years irrigated on dry land "
                   f"where any is irrigated ({cnt(det['salt'])}), and land-linked hunger and moves or abandoned fields "
                   f"occur: all together in {t9}. Stated as exposure, not cause (Ben, 20 November 2026) (pass: most)"))

    # 10 diseases from animals (finding 2; Ben's numbers, 21 November 2026)
    p_years = p_dense = 0
    short_wild, n_wild = 0, 0
    fc = {"never": [0.0, 0.0], "recent": [0.0, 0.0], "long ago": [0.0, 0.0]}
    mixed = {"never": [0.0, 0.0], "met": [0.0, 0.0]}
    meas10 = 0
    for r in runs:
        spells = r.get("disease_spells", [])
        periods = {}                                     # slot -> [(first year, end year, host)] (slots reused: review 037)
        for i, d in enumerate(r.get("diseases", [])):
            periods.setdefault(d.get("id", i), []).append((d.get("year", 0), 10 ** 9, d.get("host")))
        for d in r.get("diseases_retired", []):
            periods.setdefault(d.get("id"), []).append((d.get("year", 0), d.get("retired", 10 ** 9), d.get("host")))
        host_of = lambda slot, y: next((h for a, b, h in periods.get(slot, []) if a <= y < b), None)   # noqa: E731
        end = r.get("end_year", 10 ** 9)
        if spells:
            meas10 += 1
        for sp in spells:
            d, cell, y0, y1, yrs, deaths, yearly = sp
            open_end = y1 >= end - 1
            if yrs >= PERSIST_YEARS:
                p_years += len(yearly)
                p_dense += sum(1 for h, around in yearly if h >= HERDERS and around >= AROUND)
            wild = host_of(d, y0) == "wild"
            small = bool(yearly) and yearly[0][1] < AROUND
            if (wild or small) and not open_end:
                n_wild += 1
                short_wild += yrs < PERSIST_YEARS
        f = r.get("disease_log_fields", [])
        if len(f) != 17:
            continue
        # 3 how (2 = contact), 5 source's years of unbroken circulation, 8/9 never met, 10/11 within a generation,
        # 12/13 longer ago or unknown
        for row in r.get("disease_log", []):
            if row[3] != 2 or row[5] < 25:
                continue
            for key, (pi, di) in {"never": (8, 9), "recent": (10, 11), "long ago": (12, 13)}.items():
                fc[key][0] += max(row[pi], 0)
                fc[key][1] += max(row[di], 0)
            if row[8] > 0 and (row[10] + row[12]) > 0:                  # the same arrival reached both
                mixed["never"][0] += row[8]
                mixed["never"][1] += max(row[9], 0)
                mixed["met"][0] += row[10] + row[12]
                mixed["met"][1] += max(row[11], 0) + max(row[13], 0)
    rate = {k: (v[1] / v[0] if v[0] > 0 else float("nan")) for k, v in fc.items()}
    mrate = {k: (v[1] / v[0] if v[0] > 0 else float("nan")) for k, v in mixed.items()}
    share = p_dense / p_years if p_years else float("nan")
    fade = short_wild / n_wild if n_wild else float("nan")
    half1 = None if np.isnan(share) or np.isnan(fade) else (share > 0.5 and fade > 0.5)
    others = [rate["recent"], rate["long ago"]]
    half2 = None
    if not np.isnan(rate["never"]) and any(not np.isnan(x) for x in others) and not any(np.isnan(x) for x in mrate.values()):
        half2 = rate["never"] > max(x for x in others if not np.isnan(x)) and mrate["never"] > mrate["met"]
    ok10 = None if half1 is None or half2 is None or meas10 < MIN_COVERAGE * n else (half1 and half2)
    checks.append(("10. Diseases from animals", ok10,
                   f"of the spell-years of diseases circulating {PERSIST_YEARS}+ years on a cell, {share:.0%} had "
                   f"{HERDERS}+ herders on the cell and {AROUND:,}+ people around; of finished wild-origin or "
                   f"small-group spells, {fade:.0%} ended within {PERSIST_YEARS} years ({n_wild}). After first contact "
                   f"(a source circulating 25+ years), deaths per person: never met {rate['never']:.3f}, met within a "
                   f"generation {rate['recent']:.3f}, longer ago {rate['long ago']:.3f}; in arrivals reaching both, "
                   f"never met {mrate['never']:.3f} against met {mrate['met']:.3f}. Spells with diseases in {meas10} of "
                   f"{n} histories (pass: most persistence where herds and dense populations meet, wild and small "
                   f"starts mostly fade, and the never-met heaviest; Ben, 20-21 November 2026)"))

    # 11 traceable: every required kind present, and every sampled chain resolving (finding 9)
    tot = {}
    for r in allr:
        for k, v in r.get("chains", {}).items():
            t = tot.setdefault(k, [0, 0, 0])
            for i in range(3):
                t[i] += v[i]
    absent = [k for k in REQUIRED_CHAINS if tot.get(k, [0])[0] == 0]
    bad = {k: v for k, v in tot.items() if v[1] != v[2]}
    ok11 = False if bad else (None if absent else bool(tot))
    checks.append(("11. Traceable", ok11,
                   "; ".join(f"{k}: {v[2]:,} of {v[1]:,} sampled resolve ({v[0]:,} events)" for k, v in sorted(tot.items()))
                   + (f". Never happened in any history: {', '.join(absent)}" if absent else "")))

    # 12 variation: which, where and when; 13 speed
    first = {}
    for r in runs:
        for t, (y, c) in r.get("first_invention", {}).items():
            first.setdefault(t, []).append((y, r["world_seed"]))
    checks.append(("12. Same rules, different histories (no mark)", None,
                   "first invention by technique, histories with it, earliest-median-latest year, planets: "
                   + "; ".join(f"{t} {len(v)} ({min(y for y, _ in v):,}/{int(np.median([y for y, _ in v])):,}/"
                               f"{max(y for y, _ in v):,}, planets {sorted({p for _, p in v})})"
                               for t, v in sorted(first.items(), key=lambda x: -len(x[1])))))
    secs = [r["seconds"] for r in allr]
    recs = [r.get("record_seconds", 0) for r in allr]
    checks.append(("13. Speed (no mark)", None,
                   f"simulation {min(secs) / 3600:.1f}–{max(secs) / 3600:.1f} h per history (median "
                   f"{np.median(secs) / 3600:.1f} h); building the record {max(recs) / 60:.0f} min at most"))
    add("| Check | Result | Evidence |")
    add("|---|---|---|")
    for name, ok, ev in checks:
        add(f"| {name} | {'—' if ok is None else 'PASS' if ok else 'FAIL'} | {ev} |")

    # the arms agreed for the gate (Ben, 21 November 2026)
    add("\n## The agreed comparisons (arms, no marks)\n")
    for arm, label in (("nocuration", "no curation"), ("noprestige", "no prestige goods"),
                       ("fourpartners", "fixed four partners")):
        rs = arms.get(arm, [])
        if not rs:
            add(f"- **{label}:** no histories")
            continue
        pairs = [(r, next((m for m in runs if (m["world_seed"], m["run_seed"]) == (r["world_seed"], r["run_seed"])), None))
                 for r in rs]
        def fs_at(rec, k):
            b = rec.get("goods_falloff", {}).get("fine_stone", {}) if rec else {}
            return b.get(str(k), [0, float("nan")])[1]
        lines = []
        for r, m in pairs:
            lines.append(f"planet {r['world_seed']} seed {r['run_seed']}: fine stone per person at 8 / 12 cells "
                         f"{fs_at(r, 8):.2g} / {fs_at(r, 12):.2g} (main {fs_at(m, 8):.2g} / {fs_at(m, 12):.2g}); "
                         f"largest polity {max((x[2] for x in r.get('polity_log', [])), default=0)} "
                         f"(main {max((x[2] for x in m.get('polity_log', [])), default=0) if m else '—'})")
        add(f"- **{label}** ({len(rs)} histories): " + "; ".join(lines))
    cuts = sum(r.get("events", {}).get("technique_cut_off", 0) for r in runs)
    metal = sum(1 for r in runs if any(t in r.get("first_invention", {}) for t in ("copper_working", "smelting", "bronze", "iron")))
    add(f"- **Dependence on imports:** {cuts:,} techniques cut off by lost imports across the main histories; "
        f"{metal} of {n} histories worked metal")

    # beside the checks
    add("\n## Beside the checks (no marks)\n")
    seqs = {}
    gaps = {}
    order_keys = ("pottery", "copper_working", "bronze", "iron", "writing")
    for r in runs:
        fi = r.get("first_invention", {})
        seq = sorted([t for t in order_keys if t in fi], key=lambda t: fi[t][0])
        seqs[" < ".join(seq)] = seqs.get(" < ".join(seq), 0) + 1
        for a, b in zip(seq, seq[1:]):
            gaps.setdefault(f"{a} to {b}", []).append(fi[b][0] - fi[a][0])
    add("- **Order of first appearance** (pottery, copper, bronze, iron, writing), by history: "
        + "; ".join(f"{k or 'none'} ({v})" for k, v in sorted(seqs.items(), key=lambda x: -x[1])))
    add("- **Spacing:** " + ("; ".join(f"{k} median {_med(v):,.0f} years ({len(v)})" for k, v in gaps.items()) or "none"))
    lag = [r["polity_firsts"]["state"] - r["first_village_year"] for r in runs
           if r.get("first_village_year") is not None and "state" in r.get("polity_firsts", {})]
    add(f"- **First village to first state:** {len(lag)} histories with a state; median {_med(lag):,.0f} years; "
        f"historically 2.7–3.1 millennia (Borcan, Olsson & Putterman 2021)")
    # writing against tenure (finding 8): each polity's years at tier 2+, and whether its seat practised writing then
    ten, wr = [], []
    for r in runs:
        rows = r.get("polity_log", [])
        if not rows:
            continue
        tier = {}
        for row in rows:
            if row[8] >= 2:
                tier.setdefault(row[1], set()).add(row[0])
        practised = {}
        for row in r.get("writing_log", []):
            if row[4] and row[7]:
                practised.setdefault(row[2], set()).add(row[0])
        for pid, ys in tier.items():
            ten.append(len(ys) * 10)
            wr.append(bool(practised.get(pid, set()) & ys))
    if ten:
        ten, wr = np.array(ten), np.array(wr)
        bins = [(0, 50), (50, 200), (200, 10 ** 9)]
        add("- **Writing against tenure** (polities that reached tier 2+; years there, from 10-year samples): "
            + "; ".join(f"{a}–{b if b < 10 ** 9 else ''} years: {int(wr[(ten >= a) & (ten < b)].sum())} of "
                        f"{int(((ten >= a) & (ten < b)).sum())} practised writing at the seat"
                        for a, b in bins))
    # M1's carried-forward items (Ben, 21 November 2026)
    cs, ss = [], []
    for r in runs:
        for split, shared, km, diff in r.get("g1_language_pairs", []):
            (cs if diff else ss).append((split, shared))
    if cs and ss:
        cs, ss = np.array(cs), np.array(ss)
        parts = []
        for a, b in ((0, 1000), (1000, 3000), (3000, 10 ** 6)):
            c = cs[(cs[:, 0] >= a) & (cs[:, 0] < b)]
            s = ss[(ss[:, 0] >= a) & (ss[:, 0] < b)]
            if len(c) >= 3 and len(s) >= 3:
                parts.append(f"{a}–{b if b < 10 ** 6 else ''} years apart: {c[:, 1].mean():.0%} across the sea vs "
                             f"{s[:, 1].mean():.0%} on the same land")
        add("- **M1: island peoples diverge faster?** Shared words: " + ("; ".join(parts) or "too few pairs"))
    else:
        add("- **M1: island peoples diverge faster?** no language pairs across the sea")
    dshare = []
    for r in runs:
        dc = r.get("deaths_since_village", {}).get("by_cause", {})
        tot_d = sum(dc.values())
        if tot_d:
            dshare.append(dc.get("disease outbreak", 0) / tot_d)
    add(f"- **M1: share of deaths from epidemics** (after the first village): median {_med(dshare):.1%} "
        f"({len(dshare)} histories), against about 9% from M1's outbreaks in G1")
    add("- **M1: barren land** (G1 check 2's spread across uncrossable country) is about the first 5,000 years and is "
        "not re-measured here")
    kept = {"small": [0, 0], "middle": [0, 0], "large": [0, 0]}
    lay = []
    for r in runs:
        for p in r.get("places", []):
            band = "small" if p["size"] < 1 / 3 else "middle" if p["size"] < 2 / 3 else "large"
            lay.append(len(p["layers"]))
            for l in p["layers"]:
                if l[2] in ("kept", "replaced"):
                    kept[band][0] += 1
                    kept[band][1] += l[2] == "kept"
    add("- **Place names:** layers per place median " + f"{_med(lay):.0f} (mean {np.mean(lay) if lay else 0:.2f}); kept "
        "by newcomers: " + "; ".join(f"{k} features {v[1] / v[0]:.0%} of {v[0]:,}" if v[0] else f"{k} features none"
                                     for k, v in kept.items())
        + " (size is the feature's size at the end; a settlement's can differ from its size when named)")
    add("- **Not reported:** the Seshat comparison of technology against scale (no measure of it is recorded)")
    # roster
    seen = {(r["world_seed"], r["run_seed"], r.get("arm", "")) for r in allr}
    add(f"\n## Roster\n\n{len(allr)} completed histories: {sorted(seen)}")
    add("\n## G3 checks on these histories\n")
    add("\n".join(l for l in g3txt.splitlines() if l.startswith("|")))
    return "\n".join(L)
