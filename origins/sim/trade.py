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
up to PARTNERS_MAX partner bands within two rings (about 200 km). A link forms with a yearly chance, more readily
between peoples who share words; partners exchange gifts of lasting goods each year (shell, gold); a link lapses
when the two bands are no longer within reach or one ends. In a season when a band cannot meet its needs, partners
with food to spare beyond their own needs give up to PARTNER_SHARE of the spare (food moved, not made). Partners
teach techniques as readily as members of one's own people (technology.keep_and_spread).

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
    k = int(getattr(P, "PARTNERS_MAX", 4))
    w.partner_of = -np.ones((64, k), dtype=np.int64)
    w.partner_since = -np.ones((64, k), dtype=np.int64)


def ensure(w, band_id: int, parent: int):
    """A new band starts with no goods and no partners; whoever creates it moves a share across with move_share."""
    grow(w, band_id)
    w.goods[band_id] = 0.0
    w.partner_of[band_id] = -1                 # a new band starts without partners of its own
    w.partner_since[band_id] = -1


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
    if getattr(w, "partner_of", None) is None:
        k = int(P.PARTNERS_MAX)
        w.partner_of = -np.ones((len(w.goods), k), dtype=np.int64)
        w.partner_since = -np.ones((len(w.goods), k), dtype=np.int64)
    if band_id >= len(w.partner_of):
        cap = len(w.goods)
        for name in ("partner_of", "partner_since"):
            a = getattr(w, name)
            out = -np.ones((cap, a.shape[1]), dtype=np.int64)
            out[:len(a)] = a
            setattr(w, name, out)


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


def _unlink(w, a: int, b: int):
    for x, y in ((a, b), (b, a)):
        hit = w.partner_of[x] == y
        w.partner_of[x, hit] = -1
        w.partner_since[x, hit] = -1


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
                _unlink(w, b.id, o)
                w.event("partnership_lapsed", cell=b.cell, band=b.id, partner=o,
                        causes=[{"band": o}, {"note": f"{w.band_name(b)} and {w.band_name(alive[o])} were no longer "
                                                          f"within reach of each other"}])
    # gifts: lasting goods pass both ways each year, keeping the link alive and carrying goods along chains
    for b in live:
        for o in partners(w, b.id):
            if o > b.id:
                given = {str(b.id): {}, str(o): {}}
                for g in P.GIFT_GOODS:
                    i = GI[g]
                    x, y = P.GIFT_SHARE * w.goods[b.id, i], P.GIFT_SHARE * w.goods[o, i]
                    gx, gy = move_good(w, b.id, o, i, x), move_good(w, o, b.id, i, y)
                    if gx > 0:
                        given[str(b.id)][g] = round(gx, 6)
                    if gy > 0:
                        given[str(o)][g] = round(gy, 6)
                if given[str(b.id)] or given[str(o)]:
                    # each exchange recorded with its partners, goods and quantities (M4 spec 4.2; Codex review 013)
                    w.event("gift_exchange", cell=b.cell, band=b.id, partner=o, goods=given,
                            causes=[{"band": o}, {"note": f"{w.band_name(b)} and {w.band_name(alive[o])} exchanged "
                                                          f"their yearly gifts as partners"}])
    # new links: pairs within reach with room, drawn in band order, likelier between peoples who share words
    by_cell: dict = {}
    for b in live:
        by_cell.setdefault(b.cell, []).append(b)
    free = {b.id: int((w.partner_of[b.id] < 0).sum()) for b in live}
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
