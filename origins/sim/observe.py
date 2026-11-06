"""Observations and invariant checks.

reads: everything
writes: yearly, invariant_failures, accum['band_sizes'], _food_check
"""
from __future__ import annotations

import numpy as np

from .. import params as P


def food_total(w) -> float:
    return float(w.stock.sum() + sum(b.store for b in w.living_bands()))


def begin_tick(w):
    w._check = {"food": food_total(w), "regrowth": w.ledger["regrowth"], "harvest": w.ledger["harvest"],
                "eaten": w.ledger["eaten"], "spoiled": w.ledger["spoiled"], "farmed": w.ledger.get("farmed", 0.0)}


def end_tick(w):
    p = w.people
    # people: nobody appears or disappears without a recorded birth or death
    from . import groups
    G = w.groups
    rows = G.rows()
    if len(rows) and (G.F[rows].min() < 0 or G.M[rows].min() < 0 or
                      np.abs(G.F[rows] - np.rint(G.F[rows])).max() > 1e-9):
        w.invariant_failures.append(f"t={w.t}: group counts negative or fractional")
    alive = int(p.alive[:p.n].sum()) + int(round(groups.sizes(w).sum()))
    expected = w.counts["founders"] + w.counts["births"] - w.counts["deaths"]
    rows_expected = w.counts["founders"] + w.counts["births_ind"] + w.counts["unfolded"]
    if alive != expected or p.n != rows_expected:
        w.invariant_failures.append(f"t={w.t}: people {alive} alive vs {expected} expected")
    # food: every unit from regrowth, to eating or spoilage
    c = w._check
    d_food = food_total(w) - c["food"]
    flows = ((w.ledger["regrowth"] - c["regrowth"]) + (w.ledger.get("farmed", 0.0) - c["farmed"])
             - (w.ledger["eaten"] - c["eaten"])
             - (w.ledger["spoiled"] - c["spoiled"]))
    if abs(d_food - flows) > 1e-6 * max(1.0, abs(c["food"])):
        w.invariant_failures.append(f"t={w.t}: food change {d_food:.3f} vs flows {flows:.3f}")
    if (w.stock < -1e-9).any():
        w.invariant_failures.append(f"t={w.t}: negative wild food")
    cond = p.condition[:p.n][p.alive[:p.n]]
    if len(cond) and (cond.min() < -1e-9 or cond.max() > 1 + 1e-9):
        w.invariant_failures.append(f"t={w.t}: body condition out of range")
    alive_band = np.zeros(w.next_band, dtype=bool)
    for b in w.living_bands():
        alive_band[b.id] = True
    idx = w.alive_idx()
    if len(idx) and not alive_band[p.band[idx]].all():
        w.invariant_failures.append(f"t={w.t}: people in ended bands")
    if w.quarter == P.TICKS_PER_YEAR - 1:
        record_year(w)


def record_year(w):
    p = w.people
    idx = w.alive_idx()
    bands = w.living_bands()
    bs = w.band_sizes()
    sizes = [int(bs[b.id]) for b in bands]
    w.accum["band_sizes"].extend(int(bs[b.id]) for b in bands if b.mode == "individual")
    cells = sorted({b.cell for b in bands})
    cap = float(w.planet.capacity[cells].sum()) if cells else 0.0
    prev = w.yearly[-1] if w.yearly else {"births_total": 0, "deaths_total": w.counts["founders"] * 0}
    row = {
        "year": w.year, "years_bp": w.years_bp, "population": w.population(),
        "individuals": int(len(idx)), "groups": sum(b.mode == "group" for b in bands), "bands": len(bands),
        "births_total": w.counts["births"], "deaths_total": w.counts["deaths"],
        "births": w.counts["births"] - prev.get("births_total", 0),
        "deaths": w.counts["deaths"] - prev.get("deaths_total", 0),
        "mean_condition": _mean_condition(w),
        "food_ratio": float(np.mean([b.last_ratio for b in bands])) if bands else 0.0,
        "occupied_cells": len(cells), "known_cells": int(w.known.sum()),
        "capacity_occupied": cap,
        "median_band": float(np.median(sizes)) if sizes else 0.0,
    }
    w.yearly.append(row)


def life_table(w) -> dict:
    """Period life table and fertility from accumulated exposure."""
    a = w.accum
    py, d = a["person_years"], a["deaths"]
    mx = np.where(py > 0, d / np.maximum(py, 1e-9), 0.0)
    widths = np.array([1, 4] + [5] * 15 + [10.0])
    qx = 1 - np.exp(-mx * widths)
    qx[-1] = 1.0
    lx = np.concatenate([[1.0], np.cumprod(1 - qx)[:-1]])
    # person-years lived per interval (simple average of start and end survivors)
    Lx = widths * (lx + np.concatenate([lx[1:], [0.0]])) / 2
    Lx[-1] = lx[-1] / max(mx[-1], 1e-9) if mx[-1] > 0 else lx[-1] * 5
    e0 = float(Lx.sum())
    asfr = np.where(a["woman_years"] > 0, a["births_by_age"] / np.maximum(a["woman_years"], 1e-9), 0.0)
    tfr = float(5 * asfr.sum())
    return {"e0": e0, "tfr": tfr, "infant_q": float(qx[0]), "survive_to_15": float(lx[4]),
            "survive_15_to_60": float(lx[13] / lx[4]) if lx[4] > 0 else 0.0,
            "person_years": float(py.sum()), "deaths": float(d.sum()),
            "median_band": float(np.median(a["band_sizes"])) if a["band_sizes"] else 0.0,
            "deaths_by_cause": {k: int(v) for k, v in zip(_causes(), a["deaths_by_cause"])}}


def _causes():
    from ..state import CAUSES
    return CAUSES


def _mean_condition(w):
    p = w.people
    idx = w.alive_idx()
    tot = float(p.condition[idx].sum())
    n = len(idx)
    G = w.groups
    rows = G.rows()
    if len(rows):
        kids = G.F[rows, :5].sum(1) + G.M[rows, :5].sum(1)
        rest = G.F[rows].sum(1) + G.M[rows].sum(1) - kids
        tot += float((kids * G.cond_child[rows] + rest * G.cond_rest[rows]).sum())
        n += float((kids + rest).sum())
    return tot / n if n else 0.0
