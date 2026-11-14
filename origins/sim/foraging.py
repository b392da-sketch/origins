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
    for k in cand[w.rng["movement"].permutation(len(cand))]:
        b = bands[int(k)]
        sz = s[k]
        here = w.stock[b.cell] / max(occ[b.cell], 1)
        ns = nbs[k][valid[k]]
        v = w.stock[ns] / (occ[ns] + sz)
        j = int(np.argmax(v))
        if v[j] > here * P.MOVE_THRESHOLD:
            best = int(ns[j])
            occ[b.cell] -= sz
            occ[best] += sz
            b.last_move = (f"moved for food: {v[j] / P.SEASON_DAYS:.2f} vs "
                           f"{here / P.SEASON_DAYS:.2f} food units per person-day available")
            b.cell = best
            b.trail = (b.trail + [(w.t, best)])[-40:]
            w.reveal_pending.add(b.id)


def forage_and_eat(w):
    """Per-band arrays here are compact: one entry per living band, in living_bands() order."""
    from . import groups
    p = w.people
    bands = w.living_bands()
    idx = w.alive_idx()
    if not bands:
        w.season_stats = {"ratio": 1.0, "harvest": 0.0, "need": 0.0}
        return
    ids, pos = w.live_index()
    L = len(ids)
    age = w.ages(idx)
    nurse = nursing(w, idx)
    need = P.need(age, p.sex[idx], p.preg_due[idx] >= 0, nurse) * P.SEASON_DAYS
    work = P.work(age, nurse) * P.SEASON_DAYS * P.FORAGE_RATE
    bpos = pos[p.band[idx]]
    effort = np.bincount(bpos, weights=work, minlength=L)
    child = age < 5
    need_child = np.bincount(bpos, weights=np.where(child, need, 0.0), minlength=L)
    need_rest = np.bincount(bpos, weights=np.where(child, 0.0, need), minlength=L)
    g_nc, g_nr, g_ef = groups.needs_and_work(w, pos, L)
    effort, need_child, need_rest = effort + g_ef, need_child + g_nc, need_rest + g_nr

    cells = np.fromiter((b.cell for b in bands), dtype=np.int64, count=L)
    from . import farming, surplus
    effort *= surplus.work_share(w, ids, w.live_sizes())   # specialists eat but do not produce food
    effort, farm_food = farming.season_food_live(w, ids, cells, effort)
    # Wild food: the ordinary stock, plus broad-spectrum food (small game, birds, fish, marginal plants) that only
    # foragers with the right gear can take (M4a; Ben, 14 November 2026: gear lets the land yield more to foragers,
    # not a richer return per day; the broad spectrum revolution, Flannery 1969, Stiner 2001). Each band's share of
    # the broad pool follows the quality of the gear it practises (technology.forage_access, 0..1).
    from . import technology
    raw_effort = effort
    access = technology.forage_access(w, ids, cells)
    cell_effort = np.zeros(w.planet.n)
    np.add.at(cell_effort, cells, effort)
    cell_reach = np.zeros(w.planet.n)
    np.add.at(cell_reach, cells, effort * access)
    used = np.nonzero(cell_effort)[0]
    e = cell_effort[used]
    am = w.stock[used]
    broad = getattr(w, "stock_broad", None)
    ab_all = broad[used] if broad is not None else np.zeros(len(used))
    ab = ab_all * np.clip(cell_reach[used] / np.maximum(e, 1e-12), 0, 1)     # the part this cell's foragers can reach
    A = am + ab
    H = np.where(A > 1e-9, A * (1 - np.exp(-e / np.maximum(A, 1e-9))), 0.0)
    hm = np.where(A > 1e-9, H * am / np.maximum(A, 1e-9), 0.0)
    hb = H - hm
    w.stock[used] = am - hm
    if broad is not None:
        broad[used] = ab_all - hb
    cell_hm = np.zeros(w.planet.n)
    cell_hb = np.zeros(w.planet.n)
    cell_hm[used] = hm
    cell_hb[used] = hb
    band_h = (np.where(cell_effort[cells] > 0, cell_hm[cells] * effort / np.maximum(cell_effort[cells], 1e-12), 0.0)
              + np.where(cell_reach[cells] > 0, cell_hb[cells] * effort * access / np.maximum(cell_reach[cells], 1e-12), 0.0))
    w.ledger["harvest"] += float(H.sum())

    store = np.fromiter((b.store for b in bands), dtype=float, count=L)
    farming.record_forage_return_live(w, ids, raw_effort, band_h)
    avail = store + band_h + farm_food
    give_c = np.minimum(avail, need_child)
    give_r = np.minimum(avail - give_c, need_rest)
    frac_c = np.where(need_child > 0, give_c / np.maximum(need_child, 1e-12), 1.0)
    frac_r = np.where(need_rest > 0, give_r / np.maximum(need_rest, 1e-12), 1.0)
    eaten = give_c + give_r
    left = avail - eaten
    total_need = need_child + need_rest
    fs = w.farm_share[ids]
    if P.STORAGE:
        # farmers store grain (granaries, pits, pots): more room and slower spoilage, in proportion to farming
        grain = np.minimum(1.0, 2 * fs)          # a band farming half its work or more stores mostly grain
        cap = (P.STORE_DAYS + grain * P.GRANARY_DAYS) * total_need / P.SEASON_DAYS
        spoil = P.STORE_SPOIL * technology.spoil_multiplier(w, ids) * (1 - grain) + P.GRAIN_SPOIL * grain
    else:
        cap = P.STORE_DAYS * total_need / P.SEASON_DAYS
        spoil = P.STORE_SPOIL * technology.spoil_multiplier(w, ids)
    kept = np.minimum(left, cap) * (1 - spoil)
    spoiled = left - kept
    # food security: farmers must make what they hold last until the next harvest, so their margin is measured
    # against the needs of every season until then (foragers live season to season)
    horizon = ((P.HARVEST_QUARTER - w.quarter - 1) % P.TICKS_PER_YEAR) + 1
    seasons = 1 + fs * (horizon - 1)
    margin = np.where(total_need > 0, avail / np.maximum(total_need * seasons, 1e-12), 1.6)
    ratio_b = np.where(total_need > 0, eaten / np.where(total_need > 0, total_need, 1.0), 1.0)
    mg = np.minimum(margin, 3.0).tolist()
    kp = kept.tolist()
    rb = ratio_b.tolist()
    for k, b in enumerate(bands):
        b.margin = P.MARGIN_MEMORY * b.margin + (1 - P.MARGIN_MEMORY) * mg[k]
        b.store = kp[k]
        b.last_ratio = rb[k]
    w.ledger["eaten"] += float(eaten.sum())
    w.ledger["spoiled"] += float(spoiled.sum())

    groups.update_condition(w, frac_c, frac_r, pos)
    ratio = np.where(child, frac_c[bpos], frac_r[bpos])
    c = p.condition[idx].astype(float)
    c = np.where(ratio >= 1 - 1e-9, np.minimum(1.0, c + P.CONDITION_GAIN),
                 np.maximum(0.0, c - P.CONDITION_LOSS * (1 - ratio)))
    p.condition[idx] = c
    w.season_stats = {"ratio": float(eaten.sum() / max(total_need.sum(), 1e-9)),
                      "harvest": float(H.sum()), "need": float(total_need.sum())}
