"""Bands move, forage, share food and eat.

reads: stock, bands, people (age, sex, pregnancy, nursing, condition)
writes: bands (cell, store, last_ratio, trail, last_move), stock, people.condition,
        ledger (harvest, eaten, spoiled), season_stats
"""
from __future__ import annotations

import numpy as np

from .. import params as P


def nursing(w, idx):
    p = w.people
    y = p.youngest[idx]
    yy = np.where(y >= 0, y, 0)
    return (y >= 0) & p.alive[yy] & ((w.t - p.birth[yy]) < 2 * P.TICKS_PER_YEAR)


def move(w):
    """Each band compares food per person here and in neighbouring land cells."""
    planet = w.planet
    nb = planet.grid.neighbours
    bands = w.living_bands()
    if not bands:
        return
    sizes = w.band_sizes()
    ids = np.array([b.id for b in bands])
    cells = np.array([b.cell for b in bands])
    s = sizes[ids]
    occ = np.zeros(planet.n)
    np.add.at(occ, cells, s)
    cur = w.stock[cells] / np.maximum(occ[cells], 1)
    nbs = nb[cells]
    valid = (nbs >= 0) & planet.land[np.clip(nbs, 0, None)]
    vals = np.where(valid, w.stock[np.clip(nbs, 0, None)] / (occ[np.clip(nbs, 0, None)] + s[:, None]), -1.0)
    settled = w.farm_share[ids] >= 0.5                 # villages stay with their fields
    want = (vals.max(1) > cur * P.MOVE_THRESHOLD) & (s > 0) & ~settled
    cand = np.nonzero(want)[0]
    # a local population (group) moves only into land without one of its own kind: moving into another group's
    # land would simply merge the two, which splitting and sharing already handle
    has_group = {}
    for b in bands:
        if b.mode == "group":
            has_group[b.cell] = True
    for k in cand[w.rng["movement"].permutation(len(cand))]:
        b = bands[int(k)]
        sz = s[k]
        here = w.stock[b.cell] / max(occ[b.cell], 1)
        ns = nbs[k][valid[k]]
        if b.mode == "group":
            ns = np.array([m for m in ns if not has_group.get(int(m))], dtype=ns.dtype)
            if len(ns) == 0:
                continue
        v = w.stock[ns] / (occ[ns] + sz)
        j = int(np.argmax(v))
        if v[j] > here * P.MOVE_THRESHOLD:
            best = int(ns[j])
            occ[b.cell] -= sz
            occ[best] += sz
            b.last_move = (f"moved for food: {v[j] / P.SEASON_DAYS:.2f} vs "
                           f"{here / P.SEASON_DAYS:.2f} food units per person-day available")
            if b.mode == "group":
                has_group.pop(b.cell, None)
                has_group[best] = True
            b.cell = best
            b.trail = (b.trail + [(w.t, best)])[-40:]
            w.reveal_pending.add(b.id)


def forage_and_eat(w):
    from . import groups
    p = w.people
    bands = w.living_bands()
    idx = w.alive_idx()
    if not bands:
        w.season_stats = {"ratio": 1.0, "harvest": 0.0, "need": 0.0}
        return
    age = w.ages(idx)
    nurse = nursing(w, idx)
    need = P.need(age, p.sex[idx], p.preg_due[idx] >= 0, nurse) * P.SEASON_DAYS
    work = P.work(age, nurse) * P.SEASON_DAYS * P.FORAGE_RATE
    bid = p.band[idx]
    nb_ = w.next_band
    effort = np.bincount(bid, weights=work, minlength=nb_)
    child = age < 5
    need_child = np.bincount(bid, weights=np.where(child, need, 0.0), minlength=nb_)
    need_rest = np.bincount(bid, weights=np.where(child, 0.0, need), minlength=nb_)
    g_nc, g_nr, g_ef = groups.needs_and_work(w)
    effort, need_child, need_rest = effort + g_ef, need_child + g_nc, need_rest + g_nr

    ids = np.array([b.id for b in bands])
    cells = np.array([b.cell for b in bands])
    from . import farming, surplus
    effort[ids] *= surplus.work_share(w, ids)            # specialists eat but do not produce food
    effort, farm_food = farming.season_food(w, ids, cells, effort)
    cell_effort = np.zeros(w.planet.n)
    np.add.at(cell_effort, cells, effort[ids])
    used = np.nonzero(cell_effort)[0]
    a = w.stock[used]
    e = cell_effort[used]
    h = np.where(a > 1e-9, a * (1 - np.exp(-e / np.maximum(a, 1e-9))), 0.0)
    w.stock[used] = a - h
    cell_h = np.zeros(w.planet.n)
    cell_h[used] = h
    band_h = np.zeros(nb_)
    band_h[ids] = np.where(cell_effort[cells] > 0, cell_h[cells] * effort[ids] / np.maximum(cell_effort[cells], 1e-12), 0.0)
    w.ledger["harvest"] += float(h.sum())

    store = np.zeros(nb_)
    for b in bands:
        store[b.id] = b.store
    farming.record_forage_return(w, ids, effort, band_h)
    avail = store + band_h + farm_food
    give_c = np.minimum(avail, need_child)
    give_r = np.minimum(avail - give_c, need_rest)
    frac_c = np.where(need_child > 0, give_c / np.maximum(need_child, 1e-12), 1.0)
    frac_r = np.where(need_rest > 0, give_r / np.maximum(need_rest, 1e-12), 1.0)
    eaten = give_c + give_r
    left = avail - eaten
    total_need = need_child + need_rest
    if P.STORAGE:
        # farmers store grain (granaries, pits, pots): more room and slower spoilage, in proportion to farming
        fs = w.farm_share[:nb_]
        grain = np.minimum(1.0, 2 * fs)          # a band farming half its work or more stores mostly grain
        cap = (P.STORE_DAYS + grain * P.GRANARY_DAYS) * total_need / P.SEASON_DAYS
        spoil = P.STORE_SPOIL * (1 - grain) + P.GRAIN_SPOIL * grain
    else:
        cap = P.STORE_DAYS * total_need / P.SEASON_DAYS
        spoil = P.STORE_SPOIL
    kept = np.minimum(left, cap) * (1 - spoil)
    spoiled = left - kept
    # food security: farmers must make what they hold last until the next harvest, so their margin is measured
    # against the needs of every season until then (foragers live season to season)
    horizon = ((P.HARVEST_QUARTER - w.quarter - 1) % P.TICKS_PER_YEAR) + 1
    fsh = w.farm_share[:nb_]
    seasons = 1 + fsh * (horizon - 1)
    margin = np.where(total_need > 0, avail / np.maximum(total_need * seasons, 1e-12), 1.6)
    for b in bands:
        b.margin = P.MARGIN_MEMORY * b.margin + (1 - P.MARGIN_MEMORY) * float(min(margin[b.id], 3.0))
        b.store = float(kept[b.id])
        b.last_ratio = float(eaten[b.id] / total_need[b.id]) if total_need[b.id] > 0 else 1.0
    w.ledger["eaten"] += float(eaten[ids].sum())
    w.ledger["spoiled"] += float(spoiled[ids].sum())

    groups.update_condition(w, frac_c, frac_r)
    ratio = np.where(child, frac_c[bid], frac_r[bid])
    c = p.condition[idx].astype(float)
    c = np.where(ratio >= 1 - 1e-9, np.minimum(1.0, c + P.CONDITION_GAIN),
                 np.maximum(0.0, c - P.CONDITION_LOSS * (1 - ratio)))
    p.condition[idx] = c
    w.season_stats = {"ratio": float(eaten[ids].sum() / max(total_need[ids].sum(), 1e-9)),
                      "harvest": float(h.sum()), "need": float(total_need[ids].sum())}
