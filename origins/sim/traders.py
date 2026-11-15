"""Directed trade (M4a trade stage 4b; M4 specification section 4, item 3; Ben's decisions of 15 November 2026).

Traders are specialists of a polity: a share TRADER_SHARE of the specialists at its seat, fed from surplus as other
specialists are (surplus.py), so they eat but grow no food. Each year a polity's traders carry goods between its seat
and up to ROUTES_MAX other polities' seats, chosen by gravity: trade grows with the two polities' sizes and falls with
the square of the travel cost between them (Barjamovic et al. 2019 found the Old Assyrian records fit such a model).

Travel cost is worked out over the planet's cells: one land cell on foot costs 1 (less with pack animals and carts),
climbing and high ground cost more, rivers and coasts cost less with canoes, and sea cells can be crossed only with
sail. So routes bend through passes and along rivers and coasts, and where land forces them through one polity's
cells, that polity holds a bottleneck (Earle 2011; Hirth 1978).

Each route moves goods (TRADER_GOODS: all of them, textiles and pottery included; Ben, 15 November 2026) from the seat where they are plentiful per person to the
one where they are scarce, a share TRADER_RATE of the gap, within what the traders can carry. On the way:
- goods are lost on the road: 1 - exp(-ROAD_LOSS x cost);
- each polity whose cells the road crosses takes TOLL of the load, unless going round its cells loses less than the
  toll would take (smuggling, recorded);
- the destination's ruler takes FIRST_PICK of what arrives (Kanesh: about a tenth of the textiles);
- the traders keep TRADER_KEEP of what is delivered and take it home; the rest goes to the destination's seat.
Tolls and first picks go to the ruler's store of goods (w.treasury, per polity); when a polity ends, its store
passes to its seat, or is lost if the seat has gone.

Travel costs are pure functions of the planet and the transport qualities (rounded to tenths), so they are cached
without changing any result and need not be saved. All shares and rates are starting values (params.py).

reads: polities (seat, members), specialists (w.spec), technology (practised quality), planet (elevation, land,
       river, coast, lake), goods
writes: w.goods, w.treasury, w.goods_ledger (lost, moved), w.goods_reached, events (trade_route_opened,
        toll_evaded, good_arrived), w.route_log
"""
from __future__ import annotations

import heapq
import math

import numpy as np

from .. import params as P

_COST_CACHE: dict = {}


def _goods():
    from .trade import GOODS, GI
    return GOODS, GI


def init(w):
    GOODS, _ = _goods()
    w.treasury = np.zeros((64, len(GOODS)))
    w.route_log = []
    w.routes_seen = set()        # "a,b": a polity's traders have carried goods from a to b
    w.evaded_seen = set()        # "a,b,k": traders on a's route to b have gone round k's tolls


def grow(w, pid: int):
    GOODS, _ = _goods()
    if getattr(w, "treasury", None) is None:
        init(w)
    if pid >= len(w.treasury):
        cap = len(w.treasury)
        while cap <= pid:
            cap *= 2
        out = np.zeros((cap, len(GOODS)))
        out[:len(w.treasury)] = w.treasury
        w.treasury = out


def totals(w) -> np.ndarray:
    GOODS, _ = _goods()
    t = getattr(w, "treasury", None)
    return t.sum(axis=0) if t is not None else np.zeros(len(GOODS))


def polity_conquered(w, dp, pol):
    """A conquered polity's ruler's store goes to the conqueror's ruler (moved, not made)."""
    t = getattr(w, "treasury", None)
    if t is None or dp.id >= len(t) or not t[dp.id].any():
        return
    grow(w, pol.id)
    w.treasury[pol.id] += w.treasury[dp.id]
    w.treasury[dp.id] = 0.0


def polity_ended(w, p):
    """A ruler's store passes to the seat, or is lost with it."""
    t = getattr(w, "treasury", None)
    if t is None or p.id >= len(t) or not t[p.id].any():
        return
    GOODS, _ = _goods()
    seat = w.bands[p.seat] if p.seat < len(w.bands) else None
    for i, g in enumerate(GOODS):
        x = float(t[p.id, i])
        if x <= 0:
            continue
        if seat is not None and seat.alive:
            w.goods[p.seat, i] += x                     # moved within the world: from the ruler's store to the seat
        else:
            w.goods_ledger[g]["lost"] += x
    t[p.id] = 0.0


# ---------------------------------------------------------------- travel cost

def _tq(q_row) -> tuple:
    from . import technology
    I = technology.INDEX
    return tuple(round(float(q_row[I[k]]), 1) for k in ("pack_animals", "carts", "canoes", "sail"))


def _step_costs(pl, tq):
    pack, cart, canoe, sail = tq
    E = P.TECH_EFFECT
    foot = 1.0 / (1.0 + E.get("pack_animals", 0) * pack + E.get("carts", 0) * cart)
    water = 1.0 - (1.0 - P.RIVER_COST) * canoe if canoe > 0 else None
    sea = P.SEA_COST / sail if sail > 0 else None
    return foot, water, sea


def _cost(u, v, pl, foot, water, sea):
    if pl.land[v]:
        c = foot + P.MOUNTAIN_COST * max(0.0, float(pl.elevation[v] - pl.elevation[u])) / 1000.0
        if pl.elevation[v] > 2000:
            c += P.HIGH_COST
        if water is not None and ((pl.river[u] and pl.river[v]) or (pl.coast[u] and pl.coast[v])):
            c = min(c, water)
        return c
    if pl.lake[v]:
        return water
    return sea


def path(pl, a: int, b: int, tq: tuple, blocked: frozenset = frozenset()):
    """Cheapest route from cell a to cell b (A*), within TRADE_RANGE. Returns (cost, cells) or (inf, ())."""
    key = (pl.seed, a, b, tq, blocked)
    hit = _COST_CACHE.get(key)
    if hit is not None:
        return hit
    if a == b:
        out = (0.0, (a,))
        _COST_CACHE[key] = out
        return out
    foot, water, sea = _step_costs(pl, tq)
    hmin = min(x for x in (foot, water, sea) if x is not None)
    xyz = pl.grid.xyz
    R = pl.grid.radius_km / pl.grid.spacing_km
    target = xyz[b]

    def h(c):
        d = float(np.clip(np.dot(xyz[c], target), -1.0, 1.0))
        return 0.8 * R * math.acos(d) * hmin               # 0.8: neighbouring centres can be a little closer

    nb = pl.grid.neighbours
    best = {a: 0.0}
    prev = {}
    heap = [(h(a), 0.0, a)]
    found = None
    while heap:
        f, g, u = heapq.heappop(heap)
        if u == b:
            found = g
            break
        if g > best.get(u, math.inf) or f > P.TRADE_RANGE:
            continue
        for v in nb[u]:
            v = int(v)
            if v < 0 or v in blocked:
                continue
            c = _cost(u, v, pl, foot, water, sea)
            if c is None:
                continue
            gv = g + c
            if gv < best.get(v, math.inf) and gv <= P.TRADE_RANGE:
                best[v] = gv
                prev[v] = u
                heapq.heappush(heap, (gv + h(v), gv, v))
    if found is None:
        out = (math.inf, ())
    else:
        cells = [b]
        while cells[-1] != a:
            cells.append(prev[cells[-1]])
        out = (found, tuple(reversed(cells)))
    if len(_COST_CACHE) > 200_000:
        _COST_CACHE.clear()
    _COST_CACHE[key] = out
    return out


# ---------------------------------------------------------------- yearly

def yearly(w, live):
    """Traders carry goods between polity seats (called by trade.yearly after neighbours' exchange, before wear)."""
    if not getattr(P, "TRADE", False) or not getattr(w, "polities", None):
        return
    from . import technology
    from .trade import GI, GOODS, partners  # noqa: F401
    from ..state import log_row
    grow(w, max(w.polities) if w.polities else 0)
    pl = w.planet
    sizes_all = w.band_sizes()
    alive = [p for p in sorted(w.polities.values(), key=lambda x: x.id)
             if p.alive and p.seat < len(w.bands) and w.bands[p.seat].alive]
    if len(alive) < 2:
        return
    ids = np.array([b.id for b in live])
    pol = w.polity_of[ids]
    pop = {}
    for pid, n in zip(pol.tolist(), sizes_all[ids].tolist()):
        if pid >= 0:
            pop[pid] = pop.get(pid, 0) + n
    # who holds each cell: the polity of the largest band on it
    holder, held_by = {}, {}
    for b, pid, n in zip(live, pol.tolist(), sizes_all[ids].tolist()):
        if pid >= 0 and n > held_by.get(b.cell, -1):
            holder[b.cell], held_by[b.cell] = pid, n
    land_of: dict = {}
    for c_, k_ in holder.items():
        land_of.setdefault(k_, set()).add(c_)
    land_of = {k_: frozenset(v) for k_, v in land_of.items()}
    q = technology.practised_quality(w)
    E = P.TECH_EFFECT
    cols = [GI[g] for g in P.TRADER_GOODS]
    seats = np.array([p.seat for p in alive])
    sx = pl.grid.xyz[[w.bands[s].cell for s in seats]]
    R = pl.grid.radius_km / pl.grid.spacing_km
    for ia, A in enumerate(alive):
        traders = math.floor(P.TRADER_SHARE * float(w.spec[A.seat]))
        if traders <= 0:
            continue
        seatA = w.bands[A.seat]
        tq = _tq(q[A.seat])
        foot, water, sea = _step_costs(pl, tq)
        hmin = min(x for x in (foot, water, sea) if x is not None)
        # candidates: other seats close enough in a straight line to be within range at the cheapest step cost
        ang = np.arccos(np.clip(sx @ sx[ia], -1.0, 1.0)) * R
        order = [int(j) for j in np.argsort(ang, kind="stable") if j != ia and ang[j] * hmin * 0.8 <= P.TRADE_RANGE][:12]
        opts = []
        for j in order:
            B = alive[j]
            cost, cells = path(pl, seatA.cell, w.bands[B.seat].cell, tq)
            if not cells or cost <= 0:
                continue
            opts.append((pop.get(A.id, 0) * pop.get(B.id, 0) / cost ** 2, B.id, B, cost, cells))
        if not opts:
            continue
        opts.sort(key=lambda o: (-o[0], o[1]))
        opts = opts[:P.ROUTES_MAX]
        gsum = sum(o[0] for o in opts)
        load = traders * P.TRADER_LOAD * (1 + E.get("pack_animals", 0) * tq[0] + E.get("carts", 0) * tq[1])
        for grav, _, B, cost, cells in opts:
            cap = load * grav / gsum if gsum > 0 else 0.0
            _carry(w, A, B, cost, cells, cap, tq, holder, land_of, cols, sizes_all, log_row)


def _carry(w, A, B, cost, cells, cap, tq, holder, land_of, cols, sizes_all, log_row):
    from .trade import GOODS
    pl = w.planet
    a, b = A.seat, B.seat
    sa, sb = max(float(sizes_all[a]), 1.0), max(float(sizes_all[b]), 1.0)
    ga, gb = w.goods[a, cols], w.goods[b, cols]
    f = P.TRADER_RATE * (ga * sb - gb * sa) / (sa + sb)         # positive: from A's seat to B's
    f = np.where(f > 0, np.minimum(f, 0.5 * ga), np.maximum(f, -0.5 * gb))
    tot = float(np.abs(f).sum())
    if tot <= 0 or cap <= 0:
        return
    if tot > cap:
        f *= cap / tot
    # tolls: polities whose cells the road crosses, other than the two ends; go round one if that loses less
    ends = {A.id, B.id}
    crossed = []
    for c in cells[1:-1]:
        k = holder.get(c, -1)
        if k >= 0 and k not in ends and k not in crossed:
            crossed.append(k)
    total_cost, paid, evaded = cost, [], []
    for k in crossed:
        blocked = land_of[k]                              # going round means off all of k's land
        dcost, dcells = path(pl, cells[0], cells[-1], tq, blocked)
        extra = (math.exp(-P.ROAD_LOSS * total_cost) - math.exp(-P.ROAD_LOSS * (total_cost + dcost - cost))
                 if dcells else math.inf)
        if extra < P.TOLL * math.exp(-P.ROAD_LOSS * total_cost):
            evaded.append(k)
            total_cost += dcost - cost
        else:
            paid.append(k)
    keep_frac = math.exp(-P.ROAD_LOSS * total_cost)
    moved = lost = tolls = picks = kept = 0.0
    for col, x in zip(cols, f.tolist()):
        if x == 0:
            continue
        src, dst, dst_pid = (a, b, B.id) if x > 0 else (b, a, A.id)
        m = abs(x)
        g = GOODS[col]
        led = w.goods_ledger[g]
        w.goods[src, col] -= m
        arrive = m * keep_frac
        led["lost"] += m - arrive
        lost += m - arrive
        for k in paid:
            t = P.TOLL * arrive
            arrive -= t
            grow(w, k)
            w.treasury[k, col] += t
            tolls += t
        fp = P.FIRST_PICK * arrive
        grow(w, dst_pid)
        w.treasury[dst_pid, col] += fp
        arrive -= fp
        kp = P.TRADER_KEEP * arrive                          # the traders are A's: they take their share home
        w.goods[a, col] += kp
        arrive -= kp
        reached_before = bool(w.goods_reached[dst, col])
        w.goods[dst, col] += arrive
        led["moved_out"] += m
        led["moved_in"] += m - (m - m * keep_frac)
        moved += m
        picks += fp
        kept += kp
        if not reached_before and w.goods[dst, col] > P.ARRIVE_MIN:
            w.goods_reached[dst, col] = True
            db = w.bands[dst]
            w.event("good_arrived", cell=db.cell, band=dst, good=g, source=src, route="trader",
                    causes=[{"band": a}, {"note": f"{g.replace('_', ' ')} first reached {w.band_name(db)} with the "
                                                   f"traders of {A.name}"}])
    key = f"{A.id},{B.id}"
    if key not in w.routes_seen:
        w.routes_seen.add(key)
        ba, bb = w.bands[a], w.bands[b]
        w.event("trade_route_opened", cell=ba.cell, band=a, partner=b, polity=A.id, to_polity=B.id,
                cost=round(cost, 2), cells=len(cells),
                causes=[{"band": a}, {"band": b},
                        {"note": f"traders of {A.name} began to carry goods to {B.name}, {len(cells) - 1} cells away "
                                 f"(travel cost {cost:.1f}), drawn by the size of both and the nearness of the road"}])
    for k in evaded:
        ek = f"{A.id},{B.id},{k}"
        if ek not in w.evaded_seen:
            w.evaded_seen.add(ek)
            kp_ = w.polities[k]
            w.event("toll_evaded", cell=w.bands[a].cell, band=a, polity=A.id, to_polity=B.id, around=k,
                    causes=[{"band": a}, {"band": kp_.seat},
                            {"note": f"traders of {A.name} bound for {B.name} went round the lands of {kp_.name} "
                                     f"rather than pay its toll"}])
    log_row(w, "route_log", [w.year, A.id, B.id, round(moved, 4), round(lost, 4), round(tolls, 4), round(picks, 4),
                             round(kept, 4), len(paid), len(evaded)], P.TRADE_LOG_CAP)


def to_json(w) -> dict:
    return {"route_log": getattr(w, "route_log", []), "routes_seen": sorted(getattr(w, "routes_seen", set())),
            "evaded_seen": sorted(getattr(w, "evaded_seen", set()))}


def from_json(w, d: dict):
    d = d or {}
    w.route_log = d.get("route_log", [])
    w.routes_seen = set(d.get("routes_seen", []))
    w.evaded_seen = set(d.get("evaded_seen", []))
