"""Trade (M4a; M4 specification section 4). Stage 1: goods and their ledgers. Stage 2: gift partnerships.

Each good has a source, a stock held by each band, and a ledger, like food: every unit is produced at a source,
worn out or used, lost when a band ends, or moved between bands (trade, migration, merging). sim/observe.py checks
the balance every season. Money waits for M6 (Ben, 15 November 2026): wealth is counted in goods.

Goods (Ben, 15 November 2026): salt and fine stone from deposits; copper, tin, iron and gold from ore by peoples who
practise the right technique; textiles from wool and pottery from potters; shell from coasts. Fine stone (tools),
salt (stores), metals (their techniques) and prestige goods (gold, shell: rulers' wealth) will change something
(stage 5); textiles and pottery are trade goods only, for now. Livestock already moves as herds (surplus.py).

Production is a yearly yield per skilled practitioner (technology.skilled) at a source on the band's own cell, times
the quality of the technique it needs; wear is a yearly share of each stock. Both are starting values in params.py.
Production takes no food time yet (a simplification, recorded in the build notes).

Stage 2, gift partnerships (hxaro; Wiessner 1982, 2007; Ben, 15 November 2026: links between bands): each band keeps
up to PARTNERS_MAX partner bands within two rings (about 120 km; more for larger bands, stage 4a). A link forms with a yearly chance, more readily
between peoples who share words; partners exchange gifts of lasting goods each year (shell, gold); a link lapses
when the two bands are no longer within reach or one ends. In a season when a band cannot meet its needs, partners
with food to spare beyond their own needs give up to PARTNER_SHARE of the spare (food moved, not made). Partners
teach techniques as readily as members of one's own people (technology.keep_and_spread).

Stage 3, down-the-line exchange (Renfrew 1977; Ibáñez et al. 2015; Ben, 15 November 2026): each year, bands on the
same or adjacent cells exchange goods, a share DTL_RATE of the way towards equal holdings per person, so goods flow
from where they are plentiful to where they are scarce and, with wear, thin out with distance from their source.
Bigger bands hold and pass on more (hubs). Pack animals and carts speed exchange over land; canoes along coasts and
rivers; sail adds links between coastal bands across a sea cell. Recorded: a thinned yearly log of each band's
exchanges, and an event when a good first reaches a band (naming where most of it came from).

Stage 4a, partners trade and hubs form (Ibáñez et al. 2015, best fit for the later Neolithic; Ben, 15 November 2026):
partners who are not neighbours also exchange working goods (PARTNER_TRADE_GOODS) as neighbours do, at
PARTNER_TRADE_RATE; a band holds more links the larger it is (PARTNERS_MAX at PARTNER_SIZE_REF people, growing with
the square root of size, at most PARTNERS_CAP); and a settled band with no room left drops, now and then, its
worst-supplied partner for a better-supplied band within reach that has room, so well-supplied villages gather links.

reads: bands (cell), planet minerals and coast, technology (practised quality, skilled practitioners), languages
writes: w.goods (bands x goods), w.goods_ledger, w.partner_of, w.partner_since, band stores (help in need), events
"""
from __future__ import annotations

import numpy as np

GOODS = ("salt", "fine_stone", "copper", "tin", "iron", "gold", "textiles", "pottery", "shell")
G = len(GOODS)
GI = {g: i for i, g in enumerate(GOODS)}
# what each good needs: (deposit on the band's own cell, or "coast"; technique practised, or None)
SOURCES = {
    "salt": ("salt|coast", None),
    "fine_stone": ("flint", None),
    "copper": ("copper", "copper_working"),
    "tin": ("tin", "smelting"),
    "iron": ("iron", "iron"),
    "gold": ("gold", "copper_working"),
    "textiles": (None, "wool"),
    "pottery": (None, "pottery"),
    "shell": ("coast", None),
}
FLOWS = ("produced", "worn", "lost", "moved_out", "moved_in")


def init(w):
    w.goods = np.zeros((64, G), dtype=np.float64)
    w.goods_ledger = {g: {f: 0.0 for f in FLOWS} for g in GOODS}
    k = int(getattr(P, "PARTNERS_CAP", 16))
    w.partner_of = -np.ones((64, k), dtype=np.int64)
    w.partner_gave = np.zeros((64, k, len(P.GIFT_GOODS)))    # running totals of gifts given to each partner (Ben, 15 Nov 2026)
    w.gift_log = []              # thinned: [year, band, partner, {good: given}, {good: received}]
    w.partner_since = -np.ones((64, k), dtype=np.int64)
    w.exchange_log = []          # [year, band, units received, units given, goods that first arrived]
    w.goods_reached = np.zeros((64, G), dtype=bool)   # a good has reached this band (Codex review 014)


def ensure(w, band_id: int, parent: int):
    """A new band starts with no goods and no partners; whoever creates it moves a share across with move_share."""
    grow(w, band_id)
    w.goods[band_id] = 0.0
    w.partner_of[band_id] = -1                 # a new band starts without partners of its own
    w.partner_since[band_id] = -1
    w.partner_gave[band_id] = 0.0
    w.goods_reached[band_id] = False


def grow(w, band_id: int):
    """Make room for rows up to band_id, keeping every existing row (Codex review 013: loading an older save used to
    clear its last goods row)."""
    if getattr(w, "goods", None) is None:
        init(w)
    if band_id >= len(w.goods):
        cap = len(w.goods)
        while cap <= band_id:
            cap *= 2
        out = np.zeros((cap, G), dtype=np.float64)
        out[:len(w.goods)] = w.goods
        w.goods = out
    if getattr(w, "goods_reached", None) is None:
        w.goods_reached = w.goods > P.ARRIVE_MIN        # older saves: whatever a band holds has reached it
    if len(w.goods_reached) < len(w.goods):
        out = np.zeros((len(w.goods), G), dtype=bool)
        out[:len(w.goods_reached)] = w.goods_reached
        w.goods_reached = out
    if getattr(w, "partner_of", None) is None:
        k = int(P.PARTNERS_CAP)
        w.partner_of = -np.ones((len(w.goods), k), dtype=np.int64)
        w.partner_since = -np.ones((len(w.goods), k), dtype=np.int64)
    if getattr(w, "partner_gave", None) is None:                # saves from before running totals: start at zero
        w.partner_gave = np.zeros(w.partner_of.shape + (len(P.GIFT_GOODS),))
    if not hasattr(w, "gift_log"):
        w.gift_log = []
    if w.partner_of.shape[1] < int(P.PARTNERS_CAP):            # saves from before stage 4a held four links per band
        for name in ("partner_of", "partner_since"):
            a = getattr(w, name)
            out = -np.ones((len(a), int(P.PARTNERS_CAP)), dtype=np.int64)
            out[:, :a.shape[1]] = a
            setattr(w, name, out)
        out = np.zeros((len(w.partner_of), int(P.PARTNERS_CAP), len(P.GIFT_GOODS)))
        out[:, :w.partner_gave.shape[1]] = w.partner_gave
        w.partner_gave = out
    if band_id >= len(w.partner_of):
        cap = len(w.goods)
        for name in ("partner_of", "partner_since"):
            a = getattr(w, name)
            out = -np.ones((cap, a.shape[1]), dtype=np.int64)
            out[:len(a)] = a
            setattr(w, name, out)
    if len(w.partner_gave) < len(w.partner_of):
        out = np.zeros((len(w.partner_of),) + w.partner_gave.shape[1:])
        out[:len(w.partner_gave)] = w.partner_gave
        w.partner_gave = out


def move_share(w, src_id: int, dst_id: int, frac: float):
    """Move a share of one band's goods to another (people leaving with their share, or joining another band).
    A transfer, not a flow in or out of the world: recorded as moved out and moved in."""
    if getattr(w, "goods", None) is None or frac <= 0:
        return
    frac = min(1.0, float(frac))
    amt = w.goods[src_id] * frac
    w.goods[src_id] -= amt
    w.goods[dst_id] += amt
    for i, g in enumerate(GOODS):
        if amt[i]:
            w.goods_ledger[g]["moved_out"] += float(amt[i])
            w.goods_ledger[g]["moved_in"] += float(amt[i])


def band_ended(w, band_id: int):
    """An ended band's goods are lost (scattered, buried, taken up by no one we follow); its partnerships end."""
    if getattr(w, "goods", None) is None or band_id >= len(w.goods):
        return
    _unlink_all(w, band_id)
    for i, g in enumerate(GOODS):
        if w.goods[band_id, i]:
            w.goods_ledger[g]["lost"] += float(w.goods[band_id, i])
    w.goods[band_id] = 0.0


def totals(w) -> np.ndarray:
    return w.goods.sum(axis=0) if getattr(w, "goods", None) is not None else np.zeros(G)


def _deposit(w, cells, what) -> np.ndarray:
    pl = w.planet
    out = np.zeros(len(cells), dtype=bool)
    for part in what.split("|"):
        if part == "coast":
            out |= pl.coast[cells]
        else:
            out |= pl.minerals[part][cells]
    return out


def yearly(w):
    """Production at sources, then wear. Called once a year."""
    if not getattr(P, "TRADE", False):
        return
    if getattr(w, "goods", None) is None:
        init(w)
    from . import technology
    live = w.living_bands()
    if not live:
        return
    ids = np.asarray(w.live_index()[0])
    if len(w.goods) <= ids.max():
        ensure(w, int(ids.max()), -1)
    cells = np.array([b.cell for b in live])
    skilled = technology.skilled(w, live, ids)
    q = technology.practised_quality(w)
    for i, g in enumerate(GOODS):
        where, tech = SOURCES[g]
        ok = _deposit(w, cells, where) if where else np.ones(len(ids), dtype=bool)
        level = q[ids, technology.INDEX[tech]].astype(float) if tech else np.ones(len(ids))
        made = P.GOOD_YIELD[g] * skilled * level * ok
        w.goods[ids, i] += made
        w.goods_ledger[g]["produced"] += float(made.sum())
    partnerships_yearly(w, live)
    down_the_line(w, live, ids, cells)
    worn = w.goods[ids] * np.array([P.GOOD_WEAR[g] for g in GOODS])[None, :]
    w.goods[ids] -= worn
    for i, g in enumerate(GOODS):
        w.goods_ledger[g]["worn"] += float(worn[:, i].sum())


# --- stage 2: gift partnerships -------------------------------------------------------------------------------------

def partners(w, band_id: int) -> list:
    if getattr(w, "partner_of", None) is None or band_id >= len(w.partner_of):
        return []
    return [int(x) for x in w.partner_of[band_id] if x >= 0]


def _link(w, a: int, b: int):
    ia = int(np.nonzero(w.partner_of[a] < 0)[0][0])
    ib = int(np.nonzero(w.partner_of[b] < 0)[0][0])
    w.partner_of[a, ia], w.partner_since[a, ia] = b, w.t
    w.partner_of[b, ib], w.partner_since[b, ib] = a, w.t
    w.partner_gave[a, ia] = 0.0
    w.partner_gave[b, ib] = 0.0


def _unlink(w, a: int, b: int):
    for x, y in ((a, b), (b, a)):
        hit = w.partner_of[x] == y
        w.partner_of[x, hit] = -1
        w.partner_since[x, hit] = -1
        w.partner_gave[x, hit] = 0.0


def gift_totals(w, a: int, b: int) -> dict:
    """What a and b have given each other since their partnership began: {"years": n, "<a>": {good: total},
    "<b>": {...}} (running totals; Ben, 15 November 2026)."""
    out = {"years": 0, str(a): {}, str(b): {}}
    for x, y in ((a, b), (b, a)):
        hit = np.nonzero(w.partner_of[x] == y)[0]
        if not len(hit):
            continue
        k = int(hit[0])
        out["years"] = int((w.t - int(w.partner_since[x, k])) // 4)
        out[str(x)] = {g: round(float(v), 6) for g, v in zip(P.GIFT_GOODS, w.partner_gave[x, k]) if v > 0}
    return out


def _unlink_all(w, a: int):
    if getattr(w, "partner_of", None) is None or a >= len(w.partner_of):
        return
    for b in partners(w, a):
        _unlink(w, a, b)


def move_good(w, src_id: int, dst_id: int, i: int, amount: float):
    """Move an amount of one good between bands (a gift); recorded as moved out and in."""
    amount = float(min(max(amount, 0.0), w.goods[src_id, i]))
    if amount <= 0:
        return 0.0
    w.goods[src_id, i] -= amount
    w.goods[dst_id, i] += amount
    w.goods_ledger[GOODS[i]]["moved_out"] += amount
    w.goods_ledger[GOODS[i]]["moved_in"] += amount
    return amount


def allowance(w, ids) -> np.ndarray:
    """How many partner links each band can hold: PARTNERS_MAX at PARTNER_SIZE_REF people, growing with the square
    root of size, at most PARTNERS_CAP (stage 4a; starting values)."""
    n = np.maximum(w.band_sizes()[np.asarray(ids)].astype(float), 1.0)
    k = np.floor(P.PARTNERS_MAX * np.sqrt(np.maximum(n / P.PARTNER_SIZE_REF, 1.0)))
    return np.minimum(k, P.PARTNERS_CAP).astype(int)


def supply(w, ids) -> np.ndarray:
    """How well supplied each band is with working goods: holdings per person of each, relative to the mean over
    the bands given, summed."""
    ids = np.asarray(ids)
    cols = [GI[g] for g in P.PARTNER_TRADE_GOODS]
    n = np.maximum(w.band_sizes()[ids].astype(float), 1.0)
    per = w.goods[ids][:, cols] / n[:, None]
    mean = per.mean(axis=0)
    return (per / np.where(mean > 0, mean, 1.0)).sum(axis=1)


def _closeness(w, a, b) -> float:
    from .language import shared_roots
    la, lb = w.languages.get(a.language), w.languages.get(b.language)
    same = shared_roots(la, lb) if (la is not None and lb is not None) else 1.0
    return P.TECH_FOREIGN + (1.0 - P.TECH_FOREIGN) * same


def partnerships_yearly(w, live):
    """Lapse, gifts, then new links. Draws from the 'trade' stream only."""
    from .language import ring2
    rng = w.rng["trade"]
    r2 = ring2(w)
    reach = {b.id: {int(c) for c in r2[b.cell] if c >= 0} for b in live}
    alive = {b.id: b for b in live}
    # lapse: a partner that has ended or is no longer within reach
    for b in live:
        for o in partners(w, b.id):
            if o not in alive:
                _unlink(w, b.id, o)                      # the partner's end is its own record
            elif alive[o].cell not in reach[b.id] and o > b.id:
                tot = gift_totals(w, b.id, o)
                _unlink(w, b.id, o)
                w.event("partnership_lapsed", cell=b.cell, band=b.id, partner=o, gifts=tot,
                        causes=[{"band": o}, {"note": f"{w.band_name(b)} and {w.band_name(alive[o])} were no longer "
                                                          f"within reach of each other"}])
    # gifts: lasting goods pass both ways each year, keeping the link alive and carrying goods along chains
    for b in live:
        for o in partners(w, b.id):
            if o > b.id:
                given = {str(b.id): {}, str(o): {}}
                kb = int(np.nonzero(w.partner_of[b.id] == o)[0][0])
                ko = int(np.nonzero(w.partner_of[o] == b.id)[0][0])
                first = not (w.partner_gave[b.id, kb].any() or w.partner_gave[o, ko].any())
                for j, g in enumerate(P.GIFT_GOODS):
                    i = GI[g]
                    x, y = P.GIFT_SHARE * w.goods[b.id, i], P.GIFT_SHARE * w.goods[o, i]
                    gx, gy = move_good(w, b.id, o, i, x), move_good(w, o, b.id, i, y)
                    w.partner_gave[b.id, kb, j] += gx
                    w.partner_gave[o, ko, j] += gy
                    if gx > 0:
                        given[str(b.id)][g] = round(gx, 6)
                    if gy > 0:
                        given[str(o)][g] = round(gy, 6)
                if given[str(b.id)] or given[str(o)]:
                    # Each exchange is recorded with its partners, goods and quantities (M4 spec 4.2) as running
                    # totals per partnership, carried by the lapse event; the first exchange is an event; yearly
                    # exchanges go into a thinned log (Ben, 15 November 2026: 9.9 million yearly events in 1,200
                    # years were 85% of the record).
                    from ..state import log_row
                    log_row(w, "gift_log", [w.t, b.id, o, given[str(b.id)], given[str(o)]], P.EXCHANGE_LOG_CAP)
                    if first:
                        w.event("gift_exchange", cell=b.cell, band=b.id, partner=o, goods=given,
                                causes=[{"band": o}, {"note": f"{w.band_name(b)} and {w.band_name(alive[o])} "
                                                              f"exchanged their first gifts as partners"}])
    # new links: pairs within reach with room, drawn in band order, likelier between peoples who share words
    by_cell: dict = {}
    for b in live:
        by_cell.setdefault(b.cell, []).append(b)
    allow = dict(zip([b.id for b in live], allowance(w, [b.id for b in live]).tolist()))
    free = {b.id: allow[b.id] - len(partners(w, b.id)) for b in live}
    _switch(w, live, reach, by_cell, free, rng)
    for b in sorted(live, key=lambda x: x.id):
        if free[b.id] <= 0:
            continue
        mine = set(partners(w, b.id))
        cands = sorted((o for c in sorted(reach[b.id]) for o in by_cell.get(c, ())
                        if o.id > b.id and o.id not in mine and free[o.id] > 0), key=lambda x: x.id)
        if not cands:
            continue
        draws = rng.random(len(cands))
        for o, u in zip(cands, draws.tolist()):
            if free[b.id] <= 0:
                break
            if free[o.id] <= 0:
                continue
            close = _closeness(w, b, o)
            if u < P.PARTNER_FORM * close:
                _link(w, b.id, o.id)
                free[b.id] -= 1
                free[o.id] -= 1
                w.event("partnership_formed", cell=b.cell, band=b.id, partner=o.id,
                        causes=[{"band": o.id}, {"note": f"{w.band_name(b)} and {w.band_name(o)} lived within reach "
                                                          f"of each other ({close:.0%} closeness of speech) and began "
                                                          f"to exchange gifts"}])


def _switch(w, live, reach, by_cell, free, rng):
    """Settled bands with no room left drop, with a yearly chance PARTNER_SWITCH, their worst-supplied partner for
    the best-supplied band within reach that has room and is better supplied (Ibáñez et al. 2015's optimised links).
    Draws from the 'trade' stream, one draw per settled band with no room, in band order."""
    from . import technology
    full = sorted((b for b in live if free[b.id] <= 0 and partners(w, b.id)), key=lambda x: x.id)
    if not full:
        return
    settled = technology._settled(w, [b.id for b in full])
    full = [b for b, s_ in zip(full, settled.tolist()) if s_]
    if not full:
        return
    draws = rng.random(len(full))
    ids = np.array([b.id for b in live])
    sup = dict(zip(ids.tolist(), supply(w, ids).tolist()))
    for b, u in zip(full, draws.tolist()):
        if u >= P.PARTNER_SWITCH or free[b.id] > 0:
            continue
        mine = partners(w, b.id)
        worst = min(mine, key=lambda o: (sup.get(o, 0.0), o))
        mine_set = set(mine)
        cands = [o for c in sorted(reach[b.id]) for o in by_cell.get(c, ())
                 if o.id != b.id and o.id not in mine_set and free[o.id] > 0
                 and sup[o.id] > P.PARTNER_SWITCH_GAIN * sup.get(worst, 0.0) and sup[o.id] > 0]
        if not cands:
            continue
        best = max(cands, key=lambda o: (sup[o.id], -o.id))
        tot = gift_totals(w, b.id, worst)
        _unlink(w, b.id, worst)
        free[worst] = free.get(worst, 0) + 1
        _link(w, b.id, best.id)
        free[best.id] -= 1
        ow = w.bands[worst]
        w.event("partnership_lapsed", cell=b.cell, band=b.id, partner=worst, gifts=tot,
                causes=[{"band": worst}, {"note": f"{w.band_name(b)} gave up its partnership with {w.band_name(ow)}, "
                                                  f"its worst-supplied partner, for a better-supplied one"}])
        w.event("partnership_formed", cell=b.cell, band=b.id, partner=best.id,
                causes=[{"band": best.id}, {"note": f"{w.band_name(b)}, settled and with no room for more partners, "
                                                    f"took up {w.band_name(best)}, better supplied with tools, salt "
                                                    f"and metal than {w.band_name(ow)}"}])


def share_in_need(w, bands, ids, avail, need_now, keep_need):
    """Within a season, before eating: a band that cannot meet this season's needs draws on partners with food to
    spare beyond their own needs (keep_need), each giving up to PARTNER_SHARE of its spare. Food moves between
    bands' food in hand; nothing is made. Returns the new food in hand."""
    if not getattr(P, "TRADE", False) or getattr(w, "partner_of", None) is None or not len(ids):
        return avail
    pos = {int(b): k for k, b in enumerate(ids.tolist())}
    short = np.maximum(need_now - avail, 0.0)
    if not (short > 0).any():
        return avail
    avail = avail.copy()
    spare = np.maximum(avail - keep_need, 0.0) * P.PARTNER_SHARE
    from .language import ring2
    r2 = ring2(w)
    for k in np.nonzero(short > 0)[0].tolist():
        bid = int(ids[k])
        if bid >= len(w.partner_of):
            continue
        near = {int(c) for c in r2[bands[k].cell] if c >= 0}
        givers, got = [], 0.0
        for o in partners(w, bid):
            j = pos.get(o)
            if j is None or spare[j] <= 0 or short[k] - got <= 1e-9:
                continue
            if bands[j].cell not in near:
                continue                     # a partner who has moved out of reach cannot help (Codex review 013)
            give = min(spare[j], short[k] - got)
            spare[j] -= give
            avail[j] -= give
            got += give
            givers.append(o)
        if got > 0:
            avail[k] += got
            b = bands[k]
            w.event("helped_by_partners", cell=b.cell, band=bid, amount=round(got, 3), givers=givers,
                    causes=[{"band": g} for g in givers] + [{"note": f"{w.band_name(b)} could not meet its needs this "
                                                                    f"season; its gift partners gave food they could "
                                                                    f"spare"}])
    return avail


# --- stage 3: down-the-line exchange ---------------------------------------------------------------------------------

def _pairs(w, live, cells):
    """Pairs of bands (positions in live) that exchange: same cell or adjacent cells; with sail, coastal bands across
    one sea cell. Returns (i, j, kind) arrays, kind 0 land, 1 by water, 2 across the sea."""
    pl = w.planet
    nb = pl.grid.neighbours
    by_cell: dict = {}
    for k, c in enumerate(cells.tolist()):
        by_cell.setdefault(c, []).append(k)
    from . import technology
    sail = technology.practised_quality(w)[np.asarray([b.id for b in live]), technology.INDEX["sail"]] > 0
    wet = pl.coast | pl.lake | pl.river
    I, J, KIND = [], [], []
    for c, ks in by_cell.items():
        for a in range(len(ks)):
            for b in range(a + 1, len(ks)):
                I.append(ks[a]); J.append(ks[b]); KIND.append(1 if wet[c] else 0)
        near = [int(x) for x in nb[c] if x > c and pl.land[x]]
        for d in near:
            for ka in ks:
                for kb in by_cell.get(d, ()):
                    I.append(ka); J.append(kb); KIND.append(1 if (wet[c] and wet[d]) else 0)
        if pl.coast[c]:
            across = {int(z) for x in nb[c] if x >= 0 and not pl.land[x] for z in nb[x]
                      if z > c and z >= 0 and pl.land[z] and pl.coast[z]} - set(int(x) for x in nb[c])
            for d in sorted(across):
                for ka in ks:
                    for kb in by_cell.get(d, ()):
                        if sail[ka] or sail[kb]:
                            I.append(ka); J.append(kb); KIND.append(2)
    return np.array(I, dtype=np.int64), np.array(J, dtype=np.int64), np.array(KIND, dtype=np.int64)


def _partner_pairs(w, live, ids, cells, I, J, KIND):
    """Add partners who are not already neighbours (same or adjacent cell) as pairs of kind 3 (stage 4a)."""
    if getattr(w, "partner_of", None) is None:
        return I, J, KIND
    pos = {int(b): k for k, b in enumerate(np.asarray(ids).tolist())}
    nb = w.planet.grid.neighbours
    PI, PJ = [], []
    for k, bid in enumerate(np.asarray(ids).tolist()):
        if bid >= len(w.partner_of):
            continue
        c = int(cells[k])
        near = set(int(x) for x in nb[c] if x >= 0)
        for o in partners(w, bid):
            j = pos.get(o)
            if j is None or o <= bid:
                continue
            d = int(cells[j])
            if d == c or d in near:
                continue                      # already exchanging as neighbours
            PI.append(k); PJ.append(j)
    if not PI:
        return I, J, KIND
    return (np.concatenate([I, np.array(PI, dtype=np.int64)]), np.concatenate([J, np.array(PJ, dtype=np.int64)]),
            np.concatenate([KIND, np.full(len(PI), 3, dtype=np.int64)]))


def down_the_line(w, live, ids, cells):
    """Exchange between neighbouring bands, a share of the way towards equal holdings per person (conserving)."""
    if not getattr(P, "TRADE", False) or len(ids) < 2:
        return
    from . import technology
    I, J, KIND = _pairs(w, live, cells)
    I, J, KIND = _partner_pairs(w, live, ids, cells, I, J, KIND)
    if not len(I):
        return
    sizes = np.maximum(w.band_sizes()[ids].astype(float), 1.0)
    q = technology.practised_quality(w)
    def best(key):
        v = q[ids, technology.INDEX[key]].astype(float)
        return np.maximum(v[I], v[J])
    E = P.TECH_EFFECT
    land = 1 + E.get("pack_animals", 0) * best("pack_animals") + E.get("carts", 0) * best("carts")
    water = 1 + E.get("canoes_trade", 0) * best("canoes")
    rate = P.DTL_RATE * np.where(KIND == 0, land, np.where(KIND == 1, np.maximum(land, water), best("sail")))
    rate = np.where(KIND == 3, P.PARTNER_TRADE_RATE * land, rate)       # partners who are not neighbours (stage 4a)
    # (across the sea, exchange scales with the better sail's quality, as crossings do: Ben, 14 Nov 2026)
    rate = np.clip(rate, 0, 0.5)
    sa, sb = sizes[I], sizes[J]
    # Each pair closes a share of the gap in holdings per person; summed over all of a band's pairs, that share must
    # stay at or below one half, or many simultaneous inflows push a well-connected band past every donor (Codex
    # review 014). Pairs touching a band over the limit are scaled down together, so each band's new holding per
    # person stays between its own and its neighbours'.
    cond = np.zeros(len(ids))
    np.add.at(cond, I, rate * sb / (sa + sb))
    np.add.at(cond, J, rate * sa / (sa + sb))
    lim = np.where(cond > 0.5, 0.5 / np.maximum(cond, 1e-300), 1.0)
    rate = rate * np.minimum(lim[I], lim[J])
    before = w.goods[ids].copy()
    received = np.zeros(len(ids))
    given = np.zeros(len(ids))
    top_src = {}
    reached = w.goods_reached[ids] | (before > P.ARRIVE_MIN)    # by any route: production, gifts, people moving
    for gi in range(G):
        g = before[:, gi]
        if not g.any():
            continue
        # towards equal holdings per person: m* = (ga sb - gb sa) / (sa + sb); positive flows a -> b
        r = rate if GOODS[gi] in P.PARTNER_TRADE_GOODS else np.where(KIND == 3, 0.0, rate)
        f = r * (g[I] * sb - g[J] * sa) / (sa + sb)
        out = np.zeros(len(ids))
        np.add.at(out, I, np.maximum(f, 0))
        np.add.at(out, J, np.maximum(-f, 0))
        scale = np.where(out > 0, np.minimum(1.0, 0.5 * g / np.maximum(out, 1e-300)), 1.0)
        f = np.where(f > 0, f * scale[I], f * scale[J])          # no band gives more than half of what it holds
        delta = np.zeros(len(ids))
        np.add.at(delta, I, -f)
        np.add.at(delta, J, f)
        w.goods[ids, gi] = g + delta
        moved = float(np.abs(f).sum())
        if moved:
            w.goods_ledger[GOODS[gi]]["moved_out"] += moved
            w.goods_ledger[GOODS[gi]]["moved_in"] += moved
        # gross flows, pair by pair, so a band that passes goods on is counted (Codex review 014)
        np.add.at(received, J, np.maximum(f, 0))
        np.add.at(received, I, np.maximum(-f, 0))
        np.add.at(given, I, np.maximum(f, 0))
        np.add.at(given, J, np.maximum(-f, 0))
        # first arrivals: a band this good has never reached now holds some (wear can take it below the line again
        # without a second "first" arrival)
        new = np.nonzero(~reached[:, gi] & (g + delta > P.ARRIVE_MIN))[0]
        reached[:, gi] |= (g + delta > P.ARRIVE_MIN)
        if len(new):
            inflow = {}
            for a, b_, x, kd in zip(I.tolist(), J.tolist(), f.tolist(), KIND.tolist()):
                if x > 0:
                    inflow.setdefault(b_, []).append((x, a, kd))
                elif x < 0:
                    inflow.setdefault(a, []).append((-x, b_, kd))
            for k in new.tolist():
                _, src, kd = max(inflow.get(k, [(0.0, -1, 0)]))
                top_src.setdefault(k, []).append((GOODS[gi], src, kd))
    for k, arrivals in top_src.items():
        b = live[k]
        for good, src, kd in arrivals:
            if src < 0:
                continue
            o = live[src]
            how = "its trading partner" if kd == 3 else "its neighbour"
            w.event("good_arrived", cell=b.cell, band=b.id, good=good, source=o.id, route="partner" if kd == 3 else "neighbour",
                    causes=[{"band": o.id}, {"note": f"{good.replace('_', ' ')} first reached {w.band_name(b)} "
                                                      f"from {w.band_name(o)}, {how}, by exchange"}])
    w.goods_reached[ids] = reached
    from ..state import log_row
    for k in np.nonzero((received > 0) | (given > 0))[0].tolist():
        log_row(w, "exchange_log", [w.year, int(ids[k]), round(float(received[k]), 4), round(float(given[k]), 4),
                                    [g for g, _, _ in top_src.get(k, [])]], P.EXCHANGE_LOG_CAP)


def to_json(w) -> dict:
    return {"exchange_log": getattr(w, "exchange_log", []), "gift_log": getattr(w, "gift_log", [])}


def from_json(w, d: dict):
    w.exchange_log = (d or {}).get("exchange_log", [])
    w.gift_log = (d or {}).get("gift_log", [])


def check_begin(w):
    if getattr(w, "goods", None) is None:
        return
    w._goods_check = (totals(w).copy(), {g: dict(v) for g, v in w.goods_ledger.items()})


def check_end(w):
    """Every unit of every good has a recorded source and fate (nothing from nothing)."""
    c = getattr(w, "_goods_check", None)
    if c is None or getattr(w, "goods", None) is None:
        return
    before, led = c
    now = totals(w)
    for i, g in enumerate(GOODS):
        L, L0 = w.goods_ledger[g], led[g]
        flows = (L["produced"] - L0["produced"]) - (L["worn"] - L0["worn"]) - (L["lost"] - L0["lost"])
        if abs((now[i] - before[i]) - flows) > 1e-6 * max(1.0, abs(before[i])):
            w.invariant_failures.append(f"t={w.t}: {g} change {now[i] - before[i]:.4f} vs flows {flows:.4f}")
    if (w.goods < -1e-9).any():
        w.invariant_failures.append(f"t={w.t}: negative goods")


from .. import params as P  # noqa: E402
