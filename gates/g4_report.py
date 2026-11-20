"""Evaluate gate G4a from the result files. Checks and pass marks: docs/M4_SPECIFICATION_v1.md section 9; how each is
measured: docs/G4A_GATE_PLAN.md. All rates in the simulation are tunable starting values, not measurements.

The proposed readings of "falls clearly" (check 6: below half the main arm's median) and "most histories" (two thirds
of those where a check can be measured) are Claude's proposals in the gate plan, awaiting Ben's approval.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from gates.g1_report import _spearman

MOST = 2 / 3                    # "most histories" (proposed)
KNOCK_SHARE = 0.5               # check 6: the knock-out's median below this share of the main arm's (proposed)


def _load(out: Path):
    return [json.loads(f.read_text()) for f in sorted(out.glob("run_w*_s*.json"))]


def _med(x):
    x = [v for v in x if v is not None and not np.isnan(v)]
    return float(np.median(x)) if x else float("nan")


def _most(flags):
    flags = [f for f in flags if f is not None]
    return (sum(flags) >= MOST * len(flags)) if flags else None, f"{sum(flags)} of {len(flags)}"


def invention_rho(r, col):
    """Spearman over band-centuries: inventions in the century after a census row against column col of the row.
    Also (foragers, farmers) apart, split at farm share 0.5."""
    inv = {}
    for y, b, t in r.get("inventions_by_band", []):
        inv[(b, y // 100)] = inv.get((b, y // 100), 0) + 1
    xs, ys, farm = [], [], []
    for row in r.get("census", []):
        y, b = row[0], row[1]
        xs.append(row[col])
        ys.append(inv.get((b, y // 100), 0))
        farm.append(row[7] >= 0.5)
    xs, ys, farm = np.array(xs), np.array(ys), np.array(farm, dtype=bool)
    if not len(xs):
        return float("nan"), float("nan"), float("nan")
    return (_spearman(xs, ys), _spearman(xs[~farm], ys[~farm]) if (~farm).sum() else float("nan"),
            _spearman(xs[farm], ys[farm]) if farm.sum() else float("nan"))


def loss_by_reach(r):
    """Losses for want of skill per band-century, by quintile of people within reach: (rates, Spearman of quintile
    against rate, Spearman of reach against techniques known)."""
    lost = {}
    for y, b, t, practised in r.get("losses_by_band", []):
        if practised:                                   # the Henrich kind, not forgetting
            lost[(b, y // 100)] = lost.get((b, y // 100), 0) + 1
    rows = r.get("census", [])
    if len(rows) < 10:
        return None, float("nan"), float("nan")
    reach = np.array([row[3] for row in rows], float)
    rate = np.array([lost.get((row[1], row[0] // 100), 0) for row in rows], float)
    known = np.array([row[6] for row in rows], float)
    q = np.quantile(reach, [0.2, 0.4, 0.6, 0.8])
    bins = np.digitize(reach, q)
    rates = [float(rate[bins == k].mean()) if (bins == k).any() else float("nan") for k in range(5)]
    return rates, _spearman(np.arange(5), rates), _spearman(reach, known)


def report(out: Path) -> str:
    allr = [r for r in _load(out) if r.get("status") == "completed"]
    runs = [r for r in allr if r.get("tech_pop_exponent", 1.0) != 0.0]
    knock = [r for r in allr if r.get("tech_pop_exponent", 1.0) == 0.0]
    L = []
    add = L.append
    add("# Gate G4a report — 'knowledge and exchange'\n")
    planets = sorted({r["world_seed"] for r in runs})
    add(f"Histories: {len(runs)} on {len(planets)} planets, and {len(knock)} with no population effect on invention "
        f"(the knock-out). All rates are tunable starting values (origins/params.py), not measurements.\n")
    if not runs:
        return "\n".join(L)
    checks = []

    # 1 M0-M3 still hold: G3's report on the main histories (its knock-out check 5 needs G3's no-institution runs)
    tmp = Path(tempfile.mkdtemp())
    for r in runs:
        (tmp / f"run_w{r['world_seed']}_s{r['run_seed']}.json").write_text(json.dumps(r))
    from gates.g3_report import report as g3report
    g3txt = g3report(tmp)
    shutil.rmtree(tmp)
    rows = [l for l in g3txt.splitlines() if l.startswith("| ") and not l.startswith("| Check") and "---" not in l]
    g3fail = [l.split("|")[1].strip() for l in rows if "| FAIL |" in l and not l.startswith("| 5.")]
    checks.append(("1. M0-M3 still hold", not g3fail,
                   "G3's checks (and through them G2's) on these histories: "
                   + ("all pass" if not g3fail else "failing: " + "; ".join(g3fail))
                   + " (G3 check 5 needs no-institution histories, not run in G4a)"))

    # 2 innovation tracks connected population; 3 need beside it
    rho2 = [invention_rho(r, 4) for r in runs]
    rho3 = [invention_rho(r, 5) for r in runs]
    m2 = _med([x[0] for x in rho2])
    checks.append(("2. Innovation tracks connected population", m2 > 0.3 if not np.isnan(m2) else None,
                   f"median Spearman of inventions per band-century with skilled practitioners within reach: {m2:.2f} "
                   f"(foragers {_med([x[1] for x in rho2]):.2f}, farmers {_med([x[2] for x in rho2]):.2f}) "
                   f"(pass: median above 0.3)"))
    checks.append(("3. Risk matters too, or doesn't (no mark)", None,
                   f"median Spearman of inventions with the strongest need: {_med([x[0] for x in rho3]):.2f} "
                   f"(foragers {_med([x[1] for x in rho3]):.2f}, farmers {_med([x[2] for x in rho3]):.2f})"))

    # 4 diffusion follows contact
    shares, rhos4 = [], []
    for r in runs:
        s = [(k - own) / k if k else None for b, k, own in [(x[0], x[1], x[1] - x[2]) for x in r.get("learned_share", [])]]
        shares.append(_med(s))
        fa = r.get("first_adoptions", [])
        per = {}
        for y, b, t, c, steps, after in fa:
            if steps >= 0:
                per.setdefault(t, []).append((steps, after))
        tr = [_spearman([a for a, _ in v], [b for _, b in v]) for v in per.values() if len(v) >= 10]
        rhos4.append(_med(tr))
    m4a = _med(shares)
    ok4b, n4b = _most([x > 0 if not np.isnan(x) else None for x in rhos4])
    checks.append(("4. Diffusion follows contact", (m4a > 0.6 and bool(ok4b)) if not np.isnan(m4a) and ok4b is not None else None,
                   f"(a) median share of a people's techniques that came from others: {m4a:.2f} (pass: above 0.6); "
                   f"(b) time to reach a people rises with cell steps from the first invention in {n4b} histories "
                   f"(median per-technique Spearman {_med(rhos4):.2f}; pass: most)"))

    # 5 isolation causes loss
    flags, lines = [], []
    for r in runs:
        rates, rq, rk = loss_by_reach(r)
        if rates is None:
            flags.append(None)
            continue
        any_loss = any(x[3] for x in r.get("losses_by_band", []))
        flags.append(bool(any_loss) and rq < 0 and rk > 0)
        lines.append(rq)
    ok5, n5 = _most(flags)
    checks.append(("5. Isolation causes loss", ok5,
                   f"losses for want of skill occur, fall as people within reach rise (by quintile), and techniques "
                   f"known rise with reach, in {n5} histories (median Spearman of loss rate with reach quintile "
                   f"{_med(lines):.2f}) (pass: most)"))

    # 6 knock-out
    mk = _med([invention_rho(r, 4)[0] for r in knock])
    ok6 = (mk < KNOCK_SHARE * m2) if knock and not np.isnan(mk) and not np.isnan(m2) else None
    checks.append(("6. Knock-out: no population effect", ok6,
                   f"check 2's median correlation with the population term off: {mk:.2f}, against {m2:.2f} with it "
                   f"(pass, proposed: below half)" if knock else "no knock-out histories"))

    # 7 trade follows supply and distance
    fl, hl, rf = [], [], []
    for r in runs:
        fo = r.get("goods_falloff", {}).get("fine_stone")
        if fo:
            d = [int(k) for k in fo]
            v = [fo[k][1] for k in fo]
            x = _spearman(d, v)
            rf.append(x)
            fl.append(x < 0 if not np.isnan(x) else None)
        help_ = r.get("partner_help_by_year", {})
        short = {str(row[0]): row[1] for row in r.get("short_by_year", [])}
        ys = [k for k in help_ if k in short]
        if len(ys) >= 10:
            x = _spearman([short[k] for k in ys], [help_[k] for k in ys])
            hl.append(x > 0 if not np.isnan(x) else None)
    okf, nf = _most(fl)
    okh, nh = _most(hl)
    checks.append(("7. Trade follows supply and distance", (okf and okh) if okf is not None and okh is not None else okf,
                   f"fine stone per person falls with cell steps from its source in {nf} histories (median Spearman "
                   f"{_med(rf):.2f}); partner help rises with the share of bands short of food in {nh} (pass: most)"))

    # 8 conserved
    inv = sum(r.get("invariant_failures", 0) for r in allr)
    checks.append(("8. Goods are conserved", inv == 0, f"{inv} accounting failures (goods, food, people) in "
                                                       f"{len(allr)} histories (pass: none)"))

    # 9 the land answers back
    fl9 = []
    for r in runs:
        cells = r.get("land_cells", [])
        if not cells:
            fl9.append(None)
            continue
        dry_irr = [c for c in cells if c[8] > 0 and c[9] < 500]
        salt_ok = (_spearman([c[8] for c in dry_irr], [c[2] for c in dry_irr]) > 0) if len(dry_irr) >= 5 else None
        farmed = [c for c in cells if c[6] > 0]
        fert_ok = (_spearman([c[7] for c in farmed], [c[1] for c in farmed]) < 0) if len(farmed) >= 5 else None
        ev = r.get("land_events", {})
        happened = ev.get("land_hunger", 0) > 0 and ev.get("land_move", 0) > 0
        parts = [p for p in (salt_ok, fert_ok) if p is not None]
        fl9.append((all(parts) and happened) if parts else None)
    ok9, n9 = _most(fl9)
    checks.append(("9. The land answers back", ok9,
                   f"fertility falls with years of unbroken cropping, salt rises with years irrigated in dry land "
                   f"(where measurable), and land-linked hunger and moves occur, in {n9} histories; stated as "
                   f"exposure, not cause (Ben, 20 November 2026) (pass: most)"))

    # 10 diseases from animals: from the disease record (spells and arrival rows)
    persist_herd, persist_all, fc = 0, 0, {"never": [0, 0], "recent": [0, 0], "long ago": [0, 0]}
    for r in runs:
        for sp in r.get("disease_spells", []):
            yrs = sp[4]
            if yrs >= 5:
                persist_all += yrs
                if any(h > 0 and n >= 1000 for h, n in sp[6]):
                    persist_herd += yrs
        fields = r.get("disease_log_fields", [])
        if len(fields) != 17:
            continue
        # fields (disease.LOG_FIELDS): 3 how (2 = by contact), 5 the source's years of unbroken circulation,
        # 8/9 never met: people, deaths; 10/11 met within a generation; 12/13 met longer ago
        for row in r.get("disease_log", []):
            if row[3] != 2 or row[5] < 25:
                continue
            for key, (pi, di) in {"never": (8, 9), "recent": (10, 11), "long ago": (12, 13)}.items():
                fc[key][0] += max(row[pi], 0)
                fc[key][1] += max(row[di], 0)
    rate = {k: (v[1] / v[0] if v[0] else float("nan")) for k, v in fc.items()}
    share_h = persist_herd / persist_all if persist_all else float("nan")
    ok10 = (share_h > 0.5 and rate["never"] > max(rate["recent"], rate["long ago"])) \
        if not np.isnan(share_h) and not np.isnan(rate["never"]) else None
    checks.append(("10. Diseases from animals", ok10,
                   f"years of diseases circulating 5+ years on a cell with herders and 1,000+ people around: "
                   f"{share_h:.0%} of all such years; deaths per person after first contact (source circulating "
                   f"25+ years): never met {rate['never']:.3f}, met within a generation {rate['recent']:.3f}, longer "
                   f"ago {rate['long ago']:.3f} (pass, proposed reading: most persistence where herds and dense "
                   f"populations meet, and the never-met heaviest)"))

    # 11 traceable
    tot = {}
    for r in allr:
        for k, (n, ok) in r.get("chains", {}).items():
            t = tot.setdefault(k, [0, 0])
            t[0] += n
            t[1] += ok
    bad = {k: v for k, v in tot.items() if v[0] != v[1]}
    checks.append(("11. Traceable", not bad and bool(tot),
                   "; ".join(f"{k}: {v[1]:,} of {v[0]:,}" for k, v in sorted(tot.items()))))

    # 12 variation; 13 speed
    firsts = {}
    for r in runs:
        for t in r.get("first_invention", {}):
            firsts[t] = firsts.get(t, 0) + 1
    checks.append(("12. Same rules, different histories (no mark)", None,
                   "histories in which each technique appeared: "
                   + ", ".join(f"{t} {n}" for t, n in sorted(firsts.items(), key=lambda x: -x[1]))))
    secs = [r["seconds"] for r in allr]
    checks.append(("13. Speed (no mark)", None, f"{min(secs) / 3600:.1f}–{max(secs) / 3600:.1f} h of computing per "
                                                f"history (median {np.median(secs) / 3600:.1f} h)"))
    add("| Check | Result | Evidence |")
    add("|---|---|---|")
    for name, ok, ev in checks:
        add(f"| {name} | {'—' if ok is None else 'PASS' if ok else 'FAIL'} | {ev} |")

    # historical comparisons and writing (no marks)
    add("\n## Beside the checks (no marks)\n")
    order = {}
    for r in runs:
        fi = r.get("first_invention", {})
        seq = [t for t in ("pottery", "copper_working", "bronze", "iron", "writing") if t in fi]
        order[" < ".join(sorted(seq, key=lambda t: fi[t][0]))] = order.get(" < ".join(sorted(seq, key=lambda t: fi[t][0])), 0) + 1
    add("- **Order of first appearance** (pottery, copper, bronze, iron, writing), by history: "
        + "; ".join(f"{k or 'none'} ({v})" for k, v in sorted(order.items(), key=lambda x: -x[1])))
    lag = [r["polity_firsts"]["state"] - r["first_village_year"] for r in runs
           if r.get("first_village_year") is not None and "state" in r.get("polity_firsts", {})]
    add(f"- **First village to first state:** {len(lag)} histories with a state; years {_med(lag):,.0f} median "
        f"(range {min(lag) if lag else 0:,}–{max(lag) if lag else 0:,}); historically 2.7–3.1 millennia (Borcan, "
        f"Olsson & Putterman 2021)")
    wr = [r for r in runs if any(row[7] for row in r.get("writing_log", []))]
    add(f"- **Writing in use:** in {len(wr)} of {len(runs)} histories some band practised writing at a 10-year sample")
    kept = {"small": [0, 0], "middle": [0, 0], "large": [0, 0]}
    for r in runs:
        for p in r.get("places", []):
            band = "small" if p["size"] < 1 / 3 else "middle" if p["size"] < 2 / 3 else "large"
            for l in p["layers"]:
                if l[2] in ("kept", "replaced"):
                    kept[band][0] += 1
                    kept[band][1] += l[2] == "kept"
    add("- **Place names, kept by newcomers:** " + "; ".join(
        f"{k} features {v[1] / v[0]:.0%} of {v[0]:,}" if v[0] else f"{k} features none" for k, v in kept.items()))
    add("\n## G3 checks on these histories\n")
    add("\n".join(l for l in g3txt.splitlines() if l.startswith("|")))
    return "\n".join(L)
