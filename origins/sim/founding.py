"""The founding people: three bands of 30 (FOUNDING_BANDS x FOUNDING_BAND) of mixed ages in neighbouring land.

reads: planet.start_cell
writes: people, bands, known, events (founding)
"""
from __future__ import annotations

import numpy as np

from .. import params as P


def _survival(age):
    mu = P.SILER_A1 * np.exp(-P.SILER_B1 * age) + P.SILER_A2 + P.SILER_A3 * np.exp(P.SILER_B3 * age)
    return np.exp(-np.cumsum(mu))


def found(w):
    cells = [w.planet.start_cell]
    nb = w.planet.grid.neighbours
    for m in nb[w.planet.start_cell]:
        if len(cells) >= P.FOUNDING_BANDS:
            break
        if m >= 0 and w.planet.land[m]:
            cells.append(int(m))
    for k, cell in enumerate(cells[:P.FOUNDING_BANDS]):
        _found_band(w, cell, first=(k == 0))
    from .bands import reveal
    reveal(w)


def _found_band(w, cell, first=True):
    rng = w.rng["founding"]
    band = w.new_band(cell)
    ages_all = np.arange(0, 70)
    weights = _survival(ages_all)
    weights /= weights.sum()
    k = P.FOUNDING_BAND
    ages = np.sort(rng.choice(ages_all, size=k, p=weights))[::-1]
    sexes = rng.integers(0, 2, size=k).astype(np.int8)
    ids = w.add_people(sexes, np.full(k, -1), np.full(k, -1), np.full(k, band.id),
                       np.full(k, 0.8), np.full(k, cell))
    p = w.people
    p.birth[ids] = w.t - ages * P.TICKS_PER_YEAR - rng.integers(0, 4, size=k)
    age = w.ages(ids)
    women = [int(i) for i, a in zip(ids, age) if p.sex[i] == 0 and a >= P.FEMALE_MIN_AGE]
    men = [int(i) for i, a in zip(ids, age) if p.sex[i] == 1 and a >= P.MALE_MIN_AGE]
    for wmn in sorted(women, key=lambda i: p.birth[i]):
        if not men:
            break
        j = min(men, key=lambda m: abs(p.birth[m] - p.birth[wmn] + 3 * P.TICKS_PER_YEAR))
        if abs(p.birth[j] - p.birth[wmn]) > 20 * P.TICKS_PER_YEAR:
            continue
        men.remove(j)
        p.partner[wmn], p.partner[j] = j, wmn
        p.partner_since[wmn] = p.partner_since[j] = w.t
    for i, a in zip(ids, age):
        if a >= 15:
            continue
        cands = [m for m in women if 16 <= (w.ages(m) - a) <= 40]
        if not cands:
            continue
        m = cands[int(rng.integers(len(cands)))]
        p.mother[i] = m
        p.father[i] = p.partner[m]
        y = p.youngest[m]
        if y < 0 or p.birth[i] > p.birth[y]:
            p.youngest[m] = i
    w.counts["founders"] += k
    band.leader = int(ids[0])          # eldest
    w.event("founding", cell=cell, band=band.id,
            causes=[{"note": f"the world begins: a band of {k} people of mixed ages"
                             + ("" if P.FOUNDING_BANDS == 1 else f" (one of {P.FOUNDING_BANDS} founding bands)")}],
            size=int(k))
