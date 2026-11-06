"""Deaths, partnerships and births.

Births, deaths and partnerships are recorded on person rows (with their
causes' inputs: body condition, the band's food share, the bad-year event,
the mother's death) and turned into readable cause chains by origins.explain.

reads: people, bands, region_bad_event, planet.region
writes: people, counts, accum, events (separation)
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from . import customs
from ..state import C, age_group

_COMPONENT_CAUSE = np.array([C["infancy and early childhood"], C["hunger"], C["accident or illness"],
                             C["old age"], C["orphaned infant"]], dtype=np.int8)


def _fecundity(age):
    up = 0.4 + 0.6 * np.clip((age - P.FEMALE_MIN_AGE) / 5.0, 0, 1)
    down = np.clip((P.FEMALE_MAX_AGE - age) / 13.0, 0, 1)
    ok = (age >= P.FEMALE_MIN_AGE) & (age <= P.FEMALE_MAX_AGE)
    return np.where(ok, np.minimum(up, 1.0) * np.minimum(down, 1.0), 0.0)


def margin_factor(m):
    lo, span, floor = P.FERTILE_MARGIN
    return np.clip(floor + (1 - floor) * (np.asarray(m) - lo) / span, floor, 1.0)


def _band_info(w):
    key = (w.t, w.next_band)
    if w._binfo is not None and w._binfo[0] == key:
        return w._binfo[1], w._binfo[2]
    nb = w.next_band
    cell = np.full(nb, -1, dtype=np.int64)
    ratio = np.ones(nb)
    for b in w.living_bands():
        cell[b.id] = b.cell
        ratio[b.id] = b.last_ratio
    w._binfo = (key, cell, ratio)
    return cell, ratio


def kill(w, ids: np.ndarray, causes: np.ndarray):
    """Record deaths with the inputs needed to explain them."""
    if len(ids) == 0:
        return
    p = w.people
    cell, ratio = _band_info(w)
    b = p.band[ids]
    p.alive[ids] = False
    p.death[ids] = w.t
    p.cause[ids] = causes
    p.death_cond[ids] = p.condition[ids]
    p.death_ratio[ids] = ratio[b]
    c = cell[b]
    p.death_cell[ids] = c
    p.death_bad[ids] = np.where(c >= 0, w.region_bad_event[w.planet.region[np.clip(c, 0, None)]], -1)
    p.death_interv[ids] = np.where(c >= 0, w.intervention_event[np.clip(c, 0, None)], -1)
    rich = ids[p.wealth[ids] > 0]
    if len(rich):
        from .surplus import inherit
        inherit(w, rich)
    hung = (causes == C["hunger"]) & (c >= 0)
    np.add.at(w.cell_hunger, c[hung], 1)
    p.preg_due[ids] = -1
    partners = p.partner[ids]
    has = partners >= 0
    p.partner[partners[has]] = -1
    p.partner[ids] = -1
    w.counts["deaths"] += len(ids)
    w.accum["deaths_by_cause"] += np.bincount(causes, minlength=len(w.accum["deaths_by_cause"]))
    w.accum["deaths"] += np.bincount(age_group(w.ages(ids)), minlength=18)
    w.people_changed()


def deaths(w):
    p = w.people
    idx = w.alive_idx()
    if len(idx) == 0:
        return
    age = w.ages(idx)
    c = p.condition[idx].astype(float)
    mu_inf = P.SILER_A1 * np.exp(-P.SILER_B1 * age)
    mu_acc = np.full(len(idx), P.SILER_A2)
    mu_old = P.SILER_A3 * np.exp(P.SILER_B3 * age)
    vuln = np.where((age < 5) | (age >= 60), P.HUNGER_VULNERABLE, 1.0)
    mu_hun = P.HUNGER_HAZARD * np.clip((P.HUNGER_ONSET - c) / P.HUNGER_ONSET, 0, 1) ** P.HUNGER_POWER * vuln
    mother = p.mother[idx]
    mother_dead = (mother >= 0) & ~p.alive[np.clip(mother, 0, None)]
    mu_orph = np.where((age < 1) & mother_dead, P.ORPHAN_INFANT_HAZARD, 0.0)
    comps = np.stack([mu_inf, mu_hun, mu_acc, mu_old, mu_orph], axis=1)
    total = comps.sum(1)
    w.accum["person_years"] += np.bincount(age_group(age), minlength=18) / P.TICKS_PER_YEAR
    rng = w.rng["deaths"]
    u = rng.random(len(idx))
    pick = rng.random(len(idx))
    die = u < 1 - np.exp(-total / P.TICKS_PER_YEAR)
    if not die.any():
        return
    k = np.nonzero(die)[0]
    share = np.cumsum(comps[k], axis=1) / total[k, None]
    j = (share < pick[k, None]).sum(1)
    kill(w, idx[k], _COMPONENT_CAUSE[np.minimum(j, 4)])


def _kin(p, a, b) -> bool:
    ma, fa, mb, fb = p.mother[a], p.father[a], p.mother[b], p.father[b]
    if (ma >= 0 and ma == mb) or (fa >= 0 and fa == fb):
        return True
    return ma == b or fa == b or mb == a or fb == a


def _ring(nb, c, rings):
    cells, frontier = {c}, {c}
    for _ in range(rings):
        frontier = {int(x) for f in frontier for x in nb[f] if x >= 0} - cells
        cells |= frontier
    return sorted(cells)


def partnerships(w):
    p = w.people
    rng = w.rng["partners"]
    idx = w.alive_idx()
    if len(idx) == 0:
        return
    age = w.ages(idx)
    sex = p.sex[idx]
    partner = p.partner[idx]
    # separations (rare)
    wp = idx[(sex == 0) & (partner >= 0)]
    sep = wp[rng.random(len(wp)) < P.SEPARATION]
    for i in sep:
        j = p.partner[i]
        p.partner[i] = p.partner[j] = -1
    w.counts["separations"] = w.counts.get("separations", 0) + len(sep)
    single_w = idx[(sex == 0) & (partner < 0) & (age >= P.FEMALE_MIN_AGE) & (age <= P.FEMALE_MAX_AGE)]
    single_m = idx[(sex == 1) & (partner < 0) & (age >= P.MALE_MIN_AGE) & (age <= P.MALE_MAX_AGE)]
    if len(single_w) == 0 or len(single_m) == 0:
        return
    seekers = single_w[rng.random(len(single_w)) < P.PAIRING]
    if len(seekers) == 0:
        return
    cell, _ = _band_info(w)
    nb = w.planet.grid.neighbours
    by_cell: dict[int, list] = {}
    for m in single_m:
        by_cell.setdefault(int(cell[p.band[m]]), []).append(int(m))
    taken = set()
    rings: dict[int, list] = {}
    from .language import ring2
    r2 = ring2(w)
    for i in rng.permutation(seekers):
        i = int(i)
        c = int(cell[p.band[i]])
        near = rings.get(c)
        if near is None:
            # the partner network is two rings of land; the planet keeps those cells cached (same cells, same order)
            near = rings[c] = (r2[c].tolist() if P.PARTNER_RINGS == 2 else _ring(nb, c, P.PARTNER_RINGS))
        cand = [m for cc in near for m in by_cell.get(cc, ()) if m not in taken and not _kin(p, i, m)]
        if not cand:
            continue
        cand = np.array(cand)
        diff = (p.birth[i] - p.birth[cand]) / P.TICKS_PER_YEAR      # man older -> positive
        wt = np.exp(-np.abs(diff - 3) / 6.0) * np.where(p.band[cand] == p.band[i], 1.0, 0.6)
        j = int(cand[int(rng.choice(len(cand), p=wt / wt.sum()))])
        taken.add(j)
        p.partner[i], p.partner[j] = j, i
        p.partner_since[i] = p.partner_since[j] = w.t
        if p.band[i] != p.band[j]:
            if rng.random() < customs.residence_share(w, int(p.band[j])):   # the husband's people's custom
                kids = idx[(p.mother[idx] == i) & (age < 12)]
                p.band[i] = p.band[j]
                p.band[kids] = p.band[j]
                p.lang[kids] = w.bands[int(p.band[j])].language     # young children grow up speaking it
            else:
                p.band[j] = p.band[i]


def births(w):
    p = w.people
    rng = w.rng["births"]
    idx = w.alive_idx()
    if len(idx) == 0:
        return
    due = idx[p.preg_due[idx] == w.t]
    if len(due):
        cell, _ = _band_info(w)
        sex = rng.integers(0, 2, size=len(due)).astype(np.int8)
        cond = np.maximum(0.4, p.condition[due])
        kids = w.add_people(sex, due, p.preg_father[due], p.band[due], cond, cell[p.band[due]])
        bc = cell[p.band[due]]
        np.add.at(w.cell_births, bc[bc >= 0], 1)
        p.preg_due[due] = -1
        p.youngest[due] = kids
        w.counts["births"] += len(kids)
        w.counts["births_ind"] += len(kids)
        age_m = w.ages(due)
        g = np.clip(((age_m - 15) // 5).astype(np.int64), 0, 6)
        w.accum["births_by_age"] += np.bincount(g, minlength=7)
        md = due[rng.random(len(due)) < P.MATERNAL_DEATH]
        kill(w, md, np.full(len(md), C["childbirth"], dtype=np.int8))
    idx = w.alive_idx()
    age = w.ages(idx)
    women = (p.sex[idx] == 0) & (age >= 15) & (age < 50)
    g = np.clip(((age[women] - 15) // 5).astype(np.int64), 0, 6)
    w.accum["woman_years"] += np.bincount(g, minlength=7) / P.TICKS_PER_YEAR
    elig = women & (p.partner[idx] >= 0) & (p.preg_due[idx] < 0)
    if not elig.any():
        return
    ei = idx[elig]
    y = p.youngest[ei]
    yy = np.where(y >= 0, y, 0)
    yage = np.where((y >= 0) & p.alive[yy], (w.t - p.birth[yy]) / P.TICKS_PER_YEAR, 99.0)
    settled = w.farm_share[p.band[ei]] >= 0.5          # weaning foods in farming villages shorten birth spacing
    sup1 = np.where(settled, P.FARMER_NURSING_1, P.NURSING_SUPPRESS_1)
    nurse = np.where(yage < 2, sup1, np.where(yage < 3, P.NURSING_SUPPRESS_2, 1.0))
    cond = np.clip((p.condition[ei] - P.FERTILE_CONDITION[0]) / P.FERTILE_CONDITION[1], 0, 1)
    marg = np.ones(w.next_band)
    for b in w.living_bands():
        marg[b.id] = b.margin
    cond = cond * margin_factor(marg[p.band[ei]])
    prob = P.CONCEPTION * _fecundity(age[elig]) * cond * nurse
    conceive = ei[rng.random(len(ei)) < prob]
    p.preg_due[conceive] = w.t + P.PREGNANCY_TICKS
    p.preg_father[conceive] = p.partner[conceive]
