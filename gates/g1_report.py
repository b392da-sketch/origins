"""Evaluate gate G1 from the result files and write a readable report.

Pass marks are those proposed in docs/M1_SPECIFICATION_v1.md section 7. Where
the specification left a number to be set from the first runs (check 5, check 11),
the report gives the measurement and marks the check "—" for Ben to decide.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# plausibility ranges for hazard frequency, per eligible land cell (about 3,100 km²) per year
HAZARD_RANGES = {"flood": (1 / 200, 1 / 15), "wildfire": (1 / 2000, 1 / 50), "eruption": (1 / 20000, 1 / 1000),
                 "earthquake": (1 / 3000, 1 / 100)}


def _spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 5 or x.std() == 0 or y.std() == 0:
        return float("nan")
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def _load(out: Path, pattern: str):
    return [json.loads(f.read_text()) for f in sorted(out.glob(pattern))]


def report(out: Path, years: int | None = None) -> str:
    if years is None:                       # the length most histories were run for
        found = [int(f.stem.split("_")[-1][:-1]) for f in out.glob("run_w*_*y.json")]
        years = max(set(found), key=found.count) if found else 5000
    runs = [r for r in _load(out, f"run_w*_{years}y.json") if r.get("status") == "completed"]
    grp = _load(out, "groups_w*.json")
    L = []
    add = L.append
    n = len(runs)
    planets = sorted({r["world_seed"] for r in runs})
    add("# Gate G1 report — 'spreading and drifting apart'\n")
    add(f"Histories found: {n} of {years:,} years on {len(planets)} planets (target 75 = 5 × 15; minimum 50).\n")
    if not n:
        return "\n".join(L)
    env = sorted({(r["env"]["python"], r["env"]["numpy"]) for r in runs})
    add("Environment: " + "; ".join(f"Python {a}, NumPy {b}" for a, b in env) + "\n")
    add("All rates are tunable starting values (origins/params.py), not measurements.\n")
    checks = []
    survived = [r for r in runs if not r["extinct"] and r["completed_years"] >= r["requested_years"]]

    # 1 M0 still holds
    ratios = [max((p / c for p, c in zip(r["yearly"]["population"], r["yearly"]["capacity_occupied"]) if c > 0), default=0)
              for r in survived]
    lts = [r["life_table"] for r in survived]
    e0 = np.array([x["e0"] for x in lts]) if lts else np.zeros(1)
    tfr = np.array([x["tfr"] for x in lts]) if lts else np.zeros(1)
    band = np.array([x["median_band"] for x in lts]) if lts else np.zeros(1)
    demo_ok = [(25 <= a <= 40) and (4 <= b <= 7) and (15 <= c <= 60) for a, b, c in zip(e0, tfr, band)]
    fails = sum(r["invariant_failures"] for r in runs)
    rp = [r["replay_check"] for r in runs if r.get("replay_check") is not None]
    chk = sum(r["explain_checked"] for r in runs)
    res = sum(r["explain_resolvable"] for r in runs)
    ok1 = (len(survived) >= 0.9 * n and max(ratios, default=2) <= 1.0 and all(demo_ok) and fails == 0
           and bool(rp) and all(rp) and chk == res)
    checks.append(("1. M0 still holds", ok1,
                   f"survival {len(survived)} of {n}; highest population ÷ capacity {max(ratios, default=0):.3f} (≤ 1.0); "
                   f"life expectancy {e0.min():.1f}–{e0.max():.1f}, births per woman {tfr.min():.2f}–{tfr.max():.2f}, "
                   f"median band {band.min():.0f}–{band.max():.0f} ({sum(demo_ok)} of {len(demo_ok)} in all ranges); "
                   f"{fails} accounting failures; exact replay {sum(rp)} of {len(rp)}; "
                   f"cause chains complete for {res:,} of {chk:,} sampled deaths and events"))

    # 2 spread and sea crossings. "Full" is measured by food capacity: much land (ice, desert, high
    # mountains) supports almost no foragers, so a share of cells would understate how full the land is.
    from origins.worldgen import generate
    from gates.g1 import landmass
    cap_share, cell_share = [], []
    for r in survived:
        pl = generate(r["world_seed"])
        m = landmass(pl) == r["sea"]["start"]
        cap_share.append(r["yearly"]["capacity_occupied"][-1] / pl.capacity[m].sum())
        cell_share.append(r["yearly"]["occupied_cells"][-1] / m.sum())
    crossed = [r for r in survived if r["events"].get("sea_crossing", 0) > 0]
    other = [r for r in survived if len(r["sea"]["occupied_areas"]) > 1]
    full = sum(c >= 0.8 for c in cap_share)
    ok2 = bool(survived) and full >= 0.9 * len(survived) and len(other) >= 0.5 * len(survived)
    checks.append(("2. Spread", ok2,
                   f"at year {years:,}, occupied land holds {min(cap_share):.0%}–{max(cap_share):.0%} of the starting "
                   f"land mass's food capacity (median {np.median(cap_share):.0%}; at least 80% in {full} of "
                   f"{len(survived)} histories, pass mark 90%), on {min(cell_share):.0%}–{max(cell_share):.0%} of its "
                   f"cells (the rest is mostly ice, desert and high mountains); {len(crossed)} of {len(survived)} "
                   f"histories made at least one sea crossing (median "
                   f"{np.median([r['events'].get('sea_crossing', 0) for r in survived]):.0f}), and {len(other)} have "
                   f"people on more than one land mass at the end (every planet has islands within one sea cell)"))

    # 3 drift with distance. Cultural distance = mean of customs distance (named customs and neutral drift)
    # and language distance (share of core words not shared); each part is also reported on its own.
    rc_, rl_, rb_ = [], [], []
    for r in survived:
        last = r["samples"][max(r["samples"], key=int)]
        bp = np.array(last["band_pairs"]) if last["band_pairs"] else np.zeros((0, 4))
        if len(bp):
            rc_.append(_spearman(bp[:, 0], bp[:, 1]))
            rl_.append(_spearman(bp[:, 0], 1 - bp[:, 2]))
            rb_.append(_spearman(bp[:, 0], 0.5 * bp[:, 1] + 0.5 * (1 - bp[:, 2])))
    rhos = np.array(rb_) if rb_ else np.array([np.nan])
    clear = int(np.nansum(rhos > 0.2))
    ok3 = clear >= 0.9 * len(survived)
    checks.append(("3. Drift with distance", ok3,
                   f"rank correlation between distance apart and cultural distance (400 random band pairs per history, "
                   f"final year): {np.nanmin(rhos):.2f}–{np.nanmax(rhos):.2f} (median {np.nanmedian(rhos):.2f}); "
                   f"clearly positive (above 0.2) in {clear} of {len(survived)} histories (pass mark 90%). "
                   f"Parts on their own: customs median {np.nanmedian(rc_):.2f}, language median {np.nanmedian(rl_):.2f}"))

    # 4 drift with time
    rts = [x["mean"] for r in survived for x in r["retention"] if x["from"] >= 1000]
    sp = []
    for r in survived:
        last = r["samples"][max(r["samples"], key=int)]
        lp = np.array(last["language_pairs"]) if last["language_pairs"] else np.zeros((0, 4))
        if len(lp) >= 5:
            sp.append(_spearman(lp[:, 0], lp[:, 1]))
    sp = np.array(sp) if sp else np.array([np.nan])
    ok4 = bool(rts) and 0.70 <= np.median(rts) <= 0.90 and np.nanmedian(sp) < -0.3
    checks.append(("4. Drift with time", ok4,
                   f"core vocabulary kept per 1,000 years: median {np.median(rts):.0%} (range across languages and spans "
                   f"{min(rts):.0%}–{max(rts):.0%}; pass band 70–90%); rank correlation between time since sister "
                   f"languages split and words they share: median {np.nanmedian(sp):.2f} (must be clearly negative)"
                   if rts else "no retention measurements"))

    # 5 languages multiply, islands diverge fastest
    finals = [r["samples"][max(r["samples"], key=int)] for r in survived]
    alive = np.array([f["languages_alive"] for f in finals])
    ever = np.array([f["languages_ever"] for f in finals])
    fams = np.array([f["families_2500y"] for f in finals])
    spk = np.concatenate([f["speakers"] for f in finals]) if finals else np.zeros(1)
    same_sea, cross_sea = [], []
    for f in finals:
        for split_years, shared, km, diff in f["language_pairs"]:
            (cross_sea if diff else same_sea).append((split_years, shared))
    isl = ""
    if cross_sea and same_sea:
        cs, ss = np.array(cross_sea), np.array(same_sea)
        bins = [0, 500, 1000, 2000, 3000, 5000]
        rows = []
        for a, b in zip(bins[:-1], bins[1:]):
            c = cs[(cs[:, 0] >= a) & (cs[:, 0] < b)]
            s = ss[(ss[:, 0] >= a) & (ss[:, 0] < b)]
            if len(c) >= 3 and len(s) >= 3:
                rows.append(f"{a}–{b} years apart: {c[:, 1].mean():.0%} across the sea vs {s[:, 1].mean():.0%} on the same land")
        isl = ("; shared words for language pairs split the same time ago: " + "; ".join(rows)) if rows else \
              "; too few language pairs across the sea to compare"
    else:
        isl = "; no languages across the sea to compare"
    checks.append(("5. Languages multiply", None,
                   f"living languages at year {years:,}: {alive.min()}–{alive.max()} (median {np.median(alive):.0f}); "
                   f"ever spoken {ever.min()}–{ever.max()}; families (languages sharing an ancestor less than 2,500 years "
                   f"back): {fams.min()}–{fams.max()} (median {np.median(fams):.0f}); speakers per language median "
                   f"{np.median(spk):,.0f}{isl}. The pass count is for Ben to set from these runs."))

    # 6 regular sound change
    wb = sum(r["words_untraceable"] for r in runs)
    wc = sum(r["words_checked"] for r in runs)
    nb_ = sum(r["names_untraceable"] for r in runs)
    nc = sum(r["names_checked"] for r in runs)
    sc = [r["sound_changes"] for r in runs]
    checks.append(("6. Regular sound change", wb == 0 and nb_ == 0 and wc > 0,
                   f"{wc - wb:,} of {wc:,} words rebuilt exactly from the proto-language by replaying every recorded "
                   f"change (each rule is applied to the whole vocabulary at once); {nc - nb_:,} of {nc:,} living people's "
                   f"names rebuilt from their language's words; sound changes per history {min(sc)}–{max(sc)}"))

    # 7 hazards in the right places, frequencies
    wrong = {k: sum(r["hazard_wrong_place"].get(k, 0) for r in runs) for k in HAZARD_RANGES}
    freq_rows, freq_ok = [], True
    for k, (lo, hi) in HAZARD_RANGES.items():
        cy = sum(r["hazard_eligible_cells"][k] * r["completed_years"] for r in runs)
        cnt = sum(r["counts"].get("hz_" + k, 0) for r in runs)
        f = cnt / max(cy, 1)
        ok = lo <= f <= hi
        freq_ok &= ok
        freq_rows.append(f"{k} once per {1 / f:,.0f} years per affected cell" if f else f"{k} never")
    ok7 = sum(wrong.values()) == 0 and freq_ok
    checks.append(("7. Hazards in the right places", ok7,
                   f"hazards logged in impossible places: {sum(wrong.values())}; frequencies (all land, peopled or not): "
                   + "; ".join(freq_rows) + "; plausibility ranges: "
                   + "; ".join(f"{k} 1/{1 / hi:,.0f}–1/{1 / lo:,.0f}" for k, (lo, hi) in HAZARD_RANGES.items())))

    # 8 hazard responses
    from gates.g1 import hazard_summary
    tot = {}
    for r in runs:
        s = r.get("hazard_summary") or hazard_summary(r["hazard_after"])
        for k, v in s.items():
            t = tot.setdefault(k, {"n": 0, "death_share": 0.0, "lower_after_1": 0, "recovered_20": 0})
            for kk in t:
                t[kk] += v[kk]
    rows8, good8, tot8 = [], 0, 0
    for k in ("flood", "wildfire", "eruption", "earthquake", "outbreak"):
        t = tot.get(k)
        if not t or not t["n"]:
            rows8.append(f"{k}: none with deaths among people")
            continue
        n = t["n"]
        rec = t["recovered_20"] / n
        rows8.append(f"{k}: {n:,} with deaths (mean {t['death_share'] / n:.1%} of the area's people); local population "
                     f"lower a year later in {t['lower_after_1'] / n:.0%}, back to 90% within 20 years in {rec:.0%}")
        tot8 += 1
        good8 += rec >= 0.6
    ok8 = tot8 > 0 and good8 == tot8
    checks.append(("8. Hazard responses", ok8, "; ".join(rows8) +
                   ". Every hazard death names its hazard in its cause chain (check 1)."))

    # 9 outbreaks by contact
    ci = sum(r["counts"].get("ob_contact_infections", 0) for r in runs)
    cy = sum(r["counts"].get("ob_contact_cell_years", 0) for r in runs)
    ns = sum(r["counts"].get("ob_new_starts", 0) for r in runs)
    oy = sum(r["counts"].get("ob_other_cell_years", 0) for r in runs)
    rc, ro = ci / max(cy, 1), ns / max(oy, 1)
    ok9 = cy > 0 and rc >= 10 * max(ro, 1e-12)
    checks.append(("9. Outbreaks spread by contact", ok9,
                   f"yearly chance a peopled area falls ill: {rc:.1%} when in contact with an outbreak ({ci:,} of {cy:,} "
                   f"area-years) vs {ro:.3%} otherwise ({ns:,} new outbreaks in {oy:,} area-years): "
                   f"{rc / max(ro, 1e-12):,.0f} times higher (pass mark 10×)"))

    # 10 groups vs individuals at the food limit
    if grp:
        rows, ok10 = [], True
        for g in grp:
            i, q = g["individuals"], g["groups"]
            br, dr = q["birth_rate"] / i["birth_rate"], q["death_rate"] / i["death_rate"]
            pi = i["population"]
            ok10 &= abs(br - 1) <= 0.15 and abs(dr - 1) <= 0.15 and i["food_margin_late"] < 1.5
            rows.append(f"planet {g['world_seed']} (from year {g['at_year']:,}): births {br:.2f}×, deaths {dr:.2f}× "
                        f"(food gathered ÷ needed {i['food_margin_late']:.2f} for individuals, "
                        f"{q['food_margin_late']:.2f} for groups; population {pi[0]:,} → {pi[-1]:,})")
        checks.append(("10. Groups match individuals at the food limit", ok10,
                       "groups ÷ individuals from the same world made crowded (wild food cut to 20% from year 800, or later once 15,000 people live there; rates over years 100–300 of the test): "
                       + "; ".join(rows) + " (pass: within 15%, with food gathered ÷ needed below 1.5, where food holds births down)"))
    else:
        checks.append(("10. Groups match individuals at the food limit", False, "not run"))

    # 11 speed
    secs = np.array([r["seconds"] for r in runs])
    per_planet = {ws: np.median([r["seconds"] for r in runs if r["world_seed"] == ws]) for ws in planets}
    checks.append(("11. Speed", None,
                   f"{years:,} years took {secs.min():.0f}–{secs.max():.0f} s (median {np.median(secs):.0f} s) of computing "
                   f"per history; median by planet: " + ", ".join(f"{k}: {v:.0f} s" for k, v in per_planet.items())))

    add("| Check | Result | Evidence |\n|---|---|---|")
    for name, ok, ev in checks:
        mark = "PASS" if ok else ("—" if ok is None else "FAIL")
        add(f"| {name} | {mark} | {ev} |")
    pops = np.array([r["yearly"]["population"][-1] for r in survived])
    if len(pops):
        add(f"\nFinal populations at year {years:,}: {pops.min():,}–{pops.max():,} (median {np.median(pops):,.0f}).")
    causes = {}
    for r in survived:
        for k, v in r["life_table"]["deaths_by_cause"].items():
            causes[k] = causes.get(k, 0) + v
    tot = sum(causes.values())
    add("Deaths by cause, all histories: " + ", ".join(f"{k} {v / tot:.1%}" for k, v in
                                                        sorted(causes.items(), key=lambda kv: -kv[1]) if v) + ".")
    return "\n".join(L)
