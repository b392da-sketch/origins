"""Trade (M4a; M4 specification section 4). Stage 1: goods and their ledgers.

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

reads: bands (cell), planet minerals and coast, technology (practised quality, skilled practitioners)
writes: w.goods (bands x goods), w.goods_ledger
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


def ensure(w, band_id: int, parent: int):
    """A new band starts with no goods; whoever creates it moves a share across with move_share."""
    if getattr(w, "goods", None) is None:
        init(w)
    if band_id >= len(w.goods):
        cap = len(w.goods)
        while cap <= band_id:
            cap *= 2
        out = np.zeros((cap, G), dtype=np.float64)
        out[:len(w.goods)] = w.goods
        w.goods = out
    w.goods[band_id] = 0.0


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
    """An ended band's goods are lost (scattered, buried, taken up by no one we follow)."""
    if getattr(w, "goods", None) is None or band_id >= len(w.goods):
        return
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
    worn = w.goods[ids] * np.array([P.GOOD_WEAR[g] for g in GOODS])[None, :]
    w.goods[ids] -= worn
    for i, g in enumerate(GOODS):
        w.goods_ledger[g]["worn"] += float(worn[:, i].sum())


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
