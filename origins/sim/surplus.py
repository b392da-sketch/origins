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
from ..state import log_row

ROLES = ["", "leader", "ritual specialist", "craft worker"]
ANNUAL = 365.0 * 0.95                         # food units a typical person needs in a year


def init(w):
    w.spec = np.zeros(64)                      # specialists per band (counts, also for groups)
    w.gini_log = []                            # [year, band, gini, surplus per person, households, years its people have farmed]
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
    # farming people per cell: land is scarce when everyone farming a cell, not one village, presses on it
    cell_farmers: dict = {}
    for b in w.living_bands():
        if w.farm_share[b.id] >= P.PROPERTY_SHARE:
            cell_farmers[b.cell] = cell_farmers.get(b.cell, 0.0) + float(sizes[b.id])
    for b in w.living_bands():
        n = float(sizes[b.id])
        if n <= 0:
            continue
        surplus = max(0.0, b.store - P.SURPLUS_RESERVE * n * ANNUAL)
        per_person = surplus / n
        spec = min(np.floor(surplus / ANNUAL), np.floor(P.SPECIALIST_MAX * n)) if P.STORAGE else 0.0
        w.spec[b.id] = spec
        if w.year % 50 == 0 and (b.store > 0 or spec > 0):
            log_row(w, "spec_log", [w.year, b.id, round(per_person, 1), round(spec / n, 4), round(float(w.farm_share[b.id]), 3)], 20000)
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
        # for property, a household is founded at partnership: a single adult with no partner or children of their
        # own stays in their mother's household (and their holdings with hers) while she heads one in the village.
        # (Until 12 November 2026 every woman from 15, and every lone man, held property as a household of their
        # own, taking a share of their mother's holdings: many tiny households and a Gini far above the literature.)
        head_at = {u[0]: k for k, u in enumerate(units)}
        mset = set(int(x) for x in mem)
        keep = []
        for k, u in enumerate(units):
            h = u[0]
            m = int(p.mother[h])
            if len(u) == 1 and int(p.partner[h]) not in mset and m != h and m in head_at and len(units[head_at[m]]) > 0 \
                    and units[head_at[m]][0] == m:
                p.wealth[m] += p.wealth[h]
                p.wealth[h] = 0.0
                units[head_at[m]].append(h)
            else:
                keep.append(u)
        units = keep
        heads = np.array([u[0] for u in units])                 # the woman (or lone person) heading each
        hw = p.wealth[heads].astype(float)
        new = np.nonzero(hw <= 0)[0]
        if len(new):
            # a new household takes a share of her mother's holdings (land and stores pass down the generations);
            # without a mother to endow it (or after an heir took all), it starts poor: a small share of the mean
            avg = float(np.mean(hw[hw > 0])) if (hw > 0).any() else 1.0
            pos = {int(h): k for k, h in enumerate(heads)}
            for k in new:
                m = int(p.mother[heads[k]])
                if m >= 0 and m in pos and hw[pos[m]] > 0:
                    give = P.DOWRY_SHARE * hw[pos[m]]
                    hw[pos[m]] -= give
                    hw[k] = give
                else:
                    hw[k] = P.NEW_HOUSEHOLD_START * avg
        sigma = P.WEALTH_LUCK * min(1.0, per_person / P.SURPLUS_FOR_FULL_LUCK)
        # M3 (option c from the M2 gate): advantage compounds where good land is scarce and where herds breed.
        # Scarce land: in a crowded village, households with more land weather bad years and take over the land of
        # those that fail, so a household's holdings grow with its size relative to the village mean.
        # Herds: animals are wealth that breeds in good years and dies in bad ones.
        crowd, animals = _land_and_herds(w, b, cell_farmers.get(b.cell, n))
        rel = hw / max(float(hw.mean()), 1e-12) - 1
        # the land advantage applies to fields; on pasture it is scaled by LAND_HERDS (1: as fields; 0: pasture held
        # in common, so crowding gives the richer no extra land). Under calibration, 13 November 2026.
        from . import technology
        land = (P.LAND_ADVANTAGE * technology.land_advantage_multiplier(w, b.id)      # the plough (M4a)
                * crowd * np.clip(rel, -1, 3) * (1 - animals * (1 - P.LAND_HERDS)))
        land -= float((hw * land).sum() / max(hw.sum(), 1e-12))     # land changes hands: what some gain, others lose
        # herds breed for households with enough animals; below a threshold a household eats into its breeding
        # stock and its herd shrinks: a poverty trap with two paths (Lybbert et al. 2004, Boran pastoralists).
        # (Until 12 November 2026 herds grew alike for every household, which cannot spread households apart.)
        herd = P.HERD_GROWTH * animals * np.where(rel + 1 >= P.HERD_THRESHOLD, 1.0, -1.0)
        drift = land + herd
        s2 = sigma * (1 + P.HERD_RISK * animals)
        hw *= np.exp(drift + rng.normal(-0.5 * s2 ** 2, s2, size=len(hw)))
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
        if len(heads) >= 3 and w.year % 10 == 0:          # sampled every 10 years so the log spans the whole history
            age = (w.t - b.farming_since) // P.TICKS_PER_YEAR if b.farming_since >= 0 else 0
            log_row(w, "gini_log", [w.year, b.id, round(gini(hw), 4), round(per_person, 1), len(heads), int(age),
                                    round(float(crowd), 3), round(float(animals), 3)], 20000)


def _land_and_herds(w, b, n):
    """How crowded a village's farmland is (0: room to spare, 1: full or beyond), given n, the people farming
    its cell, and the share of its farming in animals. (Until 12 November 2026 n was the village alone, which
    never reached half its cell's capacity, so land never counted as scarce.)"""
    from . import farming
    kp, vp, ka, va = farming.best(w, b)
    _, suit = farming.land_tables(w)
    cap = P.FARM_CAPACITY * max(float(suit[b.cell, kp]), float(suit[b.cell, ka]))
    crowd = float(np.clip((n / max(cap, 1.0) - P.LAND_SCARCE) / (1 - P.LAND_SCARCE), 0, 1))
    animals = float(va / max(vp + va, 1e-9))
    return crowd, animals


def inherit(w, dead_ids):
    """A household head's holdings pass to her heirs, by her people's custom of succession.

    "to a son": all to the eldest living son; "to a daughter": all to the eldest living daughter; "to a sister's
    son": all to the eldest living son of a sister; "chosen by the council": equal shares to all living children.
    Where the custom's heir does not exist, equal shares to the children. A son's share goes to his partner's
    household if he has one (women head households). With no children, to the partner. Holdings with no heir
    at all are lost, as before.
    """
    from . import customs
    p = w.people
    n = p.n
    dead = np.asarray(dead_ids, dtype=np.int64)
    alive = np.nonzero(p.alive[:n])[0]
    mo, fa = p.mother[alive], p.father[alive]
    kid = np.isin(mo, dead) | np.isin(fa, dead)
    kids_of: dict = {}
    for k, m, f in zip(alive[kid].tolist(), mo[kid].tolist(), fa[kid].tolist()):
        for par in (m, f):
            if par >= 0:
                kids_of.setdefault(par, []).append(k)
    by_custom = getattr(P, "INHERITANCE_BY_CUSTOM", False)
    nephews_of: dict = {}
    if by_custom:
        # sons of sisters: living men whose maternal grandmother is the dead person's mother
        dm = p.mother[dead]
        dm = dm[dm >= 0]
        if len(dm):
            male = alive[p.sex[alive] == 1]
            mm = p.mother[male]
            gm = np.where(mm >= 0, p.mother[np.clip(mm, 0, None)], -1)
            sel = np.isin(gm, dm)
            for k, m, g in zip(male[sel].tolist(), mm[sel].tolist(), gm[sel].tolist()):
                nephews_of.setdefault(g, []).append((k, m))

    def head(k):
        return int(k) if p.sex[k] == 0 or p.partner[k] < 0 else int(p.partner[k])

    def eldest(ks):
        return min(ks, key=lambda k: (int(p.birth[k]), k))

    for i in dead.tolist():
        v = float(p.wealth[i])
        if v <= 0:
            continue
        p.wealth[i] = 0.0
        kids = kids_of.get(i, [])
        heirs = None
        if by_custom:
            band = int(p.band[i])
            rule = customs.CUSTOMS["succession"][int(w.customs[band, customs.SUCCESSION])] if band >= 0 else ""
            if rule == "to a son":
                sons = [k for k in kids if p.sex[k] == 1]
                heirs = [eldest(sons)] if sons else None
            elif rule == "to a daughter":
                ds = [k for k in kids if p.sex[k] == 0]
                heirs = [eldest(ds)] if ds else None
            elif rule == "to a sister's son" and p.mother[i] >= 0:
                nep = [k for k, m in nephews_of.get(int(p.mother[i]), []) if m != i]
                heirs = [eldest(nep)] if nep else None
        if heirs is None and kids:
            heirs = kids
        if heirs:
            share = v / len(heirs)
            for h in heirs:
                p.wealth[head(h)] += share
        else:
            pa = int(p.partner[i])
            if pa >= 0 and p.alive[pa]:
                p.wealth[pa] += v


def work_share(w, ids, sizes=None):
    """Share of each band's people who work at producing food (specialists do not)."""
    sizes = w.band_sizes()[ids] if sizes is None else sizes
    return np.where(sizes > 0, 1 - np.minimum(w.spec[ids], sizes) / np.maximum(sizes, 1e-9), 1.0)


def to_json(w):
    return {"gini_log": w.gini_log, "spec_log": w.spec_log}          # whole logs (until 12 Nov 2026 the last 5,000 rows: checkpoints lost the early ones)


def from_json(w, d):
    w.gini_log = d.get("gini_log", [])
    w.spec_log = d.get("spec_log", [])
