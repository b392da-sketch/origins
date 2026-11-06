"""Surplus, specialists, property and inequality (M2, behaviour 4).

Once a year, after the harvest, each band counts its surplus: stored food beyond
what it needs to reach the next harvest. Surplus can feed people who do not
produce food: specialists (a leader, then ritual specialists, then craft
workers). Their number follows the surplus, not a rule; when the surplus fails,
they go back to the fields. Specialists eat but do not forage or farm.

Property: in bands that farm and store, fields and stores belong to households
(a woman of childbearing age or older, her partner and their young children).
Each year a household's holdings grow or shrink with its luck in the harvest
(a multiplicative draw, larger where there is more surplus to gain or lose);
when a household head dies, her holdings pass to her daughters' and sons'
households in equal shares. Foragers, and anyone without storage, share food
and hold nothing that can accumulate. Inequality is measured between households
by the Gini coefficient.

reads: bands (store, size, farm_share), people (band, sex, age, partner, mother, father, alive)
writes: specialists (per band), people.role, people.wealth, inequality samples, events (none)
"""
from __future__ import annotations

import numpy as np

from .. import params as P

ROLES = ["", "leader", "ritual specialist", "craft worker"]
ANNUAL = 365.0 * 0.95                         # food units a typical person needs in a year


def init(w):
    w.spec = np.zeros(64)                      # specialists per band (counts, also for groups)
    w.gini_log = []                            # [year, band, gini, surplus per person, households, village age]
    w.spec_log = []                            # every 50 years: [year, band, surplus per person, specialist share, farm share]


def ensure(w, band_id: int, parent: int):
    if band_id >= len(w.spec):
        cap = len(w.spec)
        while cap <= band_id:
            cap *= 2
        s = np.zeros(cap)
        s[:len(w.spec)] = w.spec
        w.spec = s


def gini(x) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n < 2 or x.sum() <= 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def yearly(w):
    """After the harvest: surplus, specialists, and households' holdings."""
    from .bands import _households
    p = w.people
    rng = w.rng["surplus"]
    sizes = w.band_sizes()
    idx = w.alive_idx()
    p.role[idx] = 0
    for b in w.living_bands():
        n = float(sizes[b.id])
        if n <= 0:
            continue
        surplus = max(0.0, b.store - P.SURPLUS_RESERVE * n * ANNUAL)
        per_person = surplus / n
        spec = min(np.floor(surplus / ANNUAL), np.floor(P.SPECIALIST_MAX * n)) if P.STORAGE else 0.0
        w.spec[b.id] = spec
        if w.year % 50 == 0 and (b.store > 0 or spec > 0):
            w.spec_log.append([w.year, b.id, round(per_person, 1), round(spec / n, 4), round(float(w.farm_share[b.id]), 3)])
        if b.mode != "individual":
            continue
        mem = w.members(b.id)
        if len(mem) == 0:
            continue
        farming_band = P.STORAGE and w.farm_share[b.id] >= P.PROPERTY_SHARE
        if not farming_band:
            p.wealth[mem] = 0.0
            continue
        units = _households(w, mem)
        heads = np.array([u[0] for u in units])                 # the woman (or lone person) heading each
        hw = p.wealth[heads].astype(float)
        hw[hw <= 0] = 1.0                                       # new households start with an equal share
        sigma = P.WEALTH_LUCK * min(1.0, per_person / P.SURPLUS_FOR_FULL_LUCK)
        hw *= np.exp(rng.normal(-0.5 * sigma ** 2, sigma, size=len(hw)))
        p.wealth[heads] = hw
        # specialists: the richest household's head leads; others are drawn from adults
        adults = mem[w.ages(mem) >= 18]
        k = int(min(spec, len(adults)))
        if k > 0:
            leader = int(heads[int(np.argmax(hw))])
            pool = [int(a) for a in adults if a != leader]
            chosen = [leader] + [int(x) for x in rng.choice(pool, size=min(k - 1, len(pool)), replace=False)] if pool else [leader]
            p.role[chosen[0]] = 1
            for j, i in enumerate(chosen[1:]):
                p.role[i] = 2 if j % 4 == 0 else 3
        if len(heads) >= 3:
            age = (w.t - b.village_since) // P.TICKS_PER_YEAR if b.village_since >= 0 else 0
            w.gini_log.append([w.year, b.id, round(gini(hw), 4), round(per_person, 1), len(heads), int(age)])
    del w.gini_log[:-20000]
    del w.spec_log[:-20000]


def inherit(w, dead_ids):
    """A household head's holdings pass in equal shares to her living children's households."""
    p = w.people
    for i in dead_ids:
        i = int(i)
        v = float(p.wealth[i])
        if v <= 0:
            continue
        p.wealth[i] = 0.0
        kids = np.nonzero(((p.mother[:p.n] == i) | (p.father[:p.n] == i)) & p.alive[:p.n])[0] if p.n < 3_000_000 else []
        if len(kids):
            # each child's household head receives a share (a daughter heads her own; a son's goes to his partner)
            heirs = [int(k) if p.sex[k] == 0 or p.partner[k] < 0 else int(p.partner[k]) for k in kids]
            share = v / len(heirs)
            for h in heirs:
                p.wealth[h] += share
        else:
            pa = int(p.partner[i])
            if pa >= 0 and p.alive[pa]:
                p.wealth[pa] += v


def work_share(w, ids):
    """Share of each band's people who work at producing food (specialists do not)."""
    sizes = w.band_sizes()[ids]
    return np.where(sizes > 0, 1 - np.minimum(w.spec[ids], sizes) / np.maximum(sizes, 1e-9), 1.0)


def to_json(w):
    return {"gini_log": w.gini_log[-5000:], "spec_log": w.spec_log[-5000:]}


def from_json(w, d):
    w.gini_log = d.get("gini_log", [])
    w.spec_log = d.get("spec_log", [])
