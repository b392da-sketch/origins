"""The land answers back (M4 specification section 5; Ben's decision of 19 November 2026; build notes "The land
answers back: literature check").

Four kinds of lasting change, per cell, each 0..1 and each a starting value to be tuned:

- game: slow-breeding large game against its natural level, and game_fast for faster breeders (Ben, 19 November
  2026: the slow breeders were lost, the faster ones survived; Johnson 2002). Hunting draws both down; each regrows
  at its own rate and drifts in from neighbouring cells. Their parts of wild food (GAME_SHARE, GAME_FAST_SHARE)
  scale with them.
- forest: tree cover against the cell's natural cover (forest biomes only). Fields clear it fast; fuel for kilns
  and smelting clears a little (Iles 2020: a modest, local cost); it regrows over centuries where land is left. In
  forest biomes part of the wild food (FOREST_WILD) scales with it.
- fertility: the soil's fertility under crops. It falls under continuous cropping, less with manuring where there
  are herds (Bogaard et al. 2013), recovers in fallow, and is lost to erosion where cleared slopes are farmed. Crop
  yields scale between FERT_FLOOR and 1 with it.
- salt: salt on irrigated dry land. It rises with irrigation in dry climates and falls only slowly in fallow;
  above SALT_THRESH it cuts crop yields (Jacobsen & Adams 1958; contested by Powell 1985).

Use is measured over each year: hunting as the year's take of ordinary wild food against the year's seasonal
maxima; farming as the year's crops against the cell's crop capacity. The yearly update runs after trade, at the
harvest, and draws no random numbers.

A cell's first crossing of a threshold is an event (game hunted out, forest cleared, soil worn, land salted) naming
the land's history; it can recur only after the cell recovers. A band that moves off such a cell has the event added
to the reason for its move, so the chain from land to movement is recorded.

reads: planet (biome, rain, elevation), stock take (foraging), crops and herds (farming), goods made (trade),
       technology (manuring, irrigation)
writes: w.game, w.forest, w.fertility, w.salt, w.land_flags, w.land_event, yearly accumulators, events
"""
from __future__ import annotations

import numpy as np

from .. import params as P

KINDS = ("game", "forest", "soil", "salt")
FOREST_BIOMES = ("boreal_forest", "temperate_forest", "tropical_forest")


def init(w):
    n = w.planet.n
    w.game = np.ones(n)
    w.game_fast = np.ones(n)
    w.forest = forest_max(w).copy()
    w.fertility = np.ones(n)
    w.salt = np.zeros(n)
    w.land_flags = np.zeros((n, len(KINDS)), dtype=bool)   # crossed and not yet recovered
    w.land_event = -np.ones((n, len(KINDS)), dtype=np.int64)
    w.land_since = -np.ones((n, len(KINDS)), dtype=np.int64)   # year the use began that led to the crossing
    _clear_year(w)


def _clear_year(w):
    n = w.planet.n
    w.land_take = np.zeros(n)       # this year's take of ordinary wild food
    w.land_wild = np.zeros(n)       # this year's seasonal maxima of ordinary wild food
    w.land_crop = np.zeros(n)       # this year's crops
    w.land_cap = np.zeros(n)        # this year's crop capacity
    w.land_manure = np.zeros(n)     # best manuring x herds share among farmers on the cell
    w.land_irr = np.zeros(n)        # best irrigation quality among farmers on the cell
    w.land_fuel = np.zeros(n)       # goods made with fire (pottery, copper, tin, iron) this year


def ensure(w):
    if getattr(w, "game", None) is None:
        init(w)


def forest_max(w) -> np.ndarray:
    from ..worldgen import B
    return np.isin(w.planet.biome, [B[b] for b in FOREST_BIOMES]).astype(float)


def _slope(w) -> np.ndarray:
    c = getattr(w, "_land_slope", None)
    if c is None or len(c) != w.planet.n:
        pl = w.planet
        nb = pl.grid.neighbours
        ok = nb >= 0
        e = pl.elevation
        diff = np.where(ok, np.abs(e[np.clip(nb, 0, None)] - e[:, None]), 0.0)
        c = np.clip(diff.max(axis=1) / P.LAND_STEEP, 0.0, 1.0)
        w._land_slope = c
    return c


def wild_factor(w) -> np.ndarray:
    """Per cell: the share of natural wild food the land still offers (game and forest)."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return 1.0
    f = 1.0 - P.GAME_SHARE * (1.0 - w.game) - P.GAME_FAST_SHARE * (1.0 - w.game_fast)
    f = f * (1.0 - P.FOREST_WILD * forest_max(w) * (1.0 - w.forest / np.maximum(forest_max(w), 1e-9)))
    return f


def crop_factor(w, cells) -> np.ndarray:
    """Per band (by cell): what fertility and salt leave of crop yields."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return np.ones(len(cells))
    fert = P.FERT_FLOOR + (1.0 - P.FERT_FLOOR) * w.fertility[cells]
    over = np.clip((w.salt[cells] - P.SALT_THRESH) / (1.0 - P.SALT_THRESH), 0.0, 1.0)
    return fert * (1.0 - P.SALT_MAX_LOSS * over)


# ------------------------------------------------------------------ yearly accounts, kept by other systems

def note_wild(w, cells, take, target):
    """foraging and regrowth: ordinary wild food taken and the seasonal maximum."""
    if getattr(w, "game", None) is None:
        return
    if take is not None:
        np.add.at(w.land_take, cells, take)
    if target is not None:
        w.land_wild += target


def note_crops(w, ids, cells, crop, cap, animal_part):
    """farming: crops grown, crop capacity of each farmed cell, manuring and irrigation of its farmers."""
    if getattr(w, "game", None) is None:
        return
    np.add.at(w.land_crop, cells, crop)
    seen = np.zeros(w.planet.n, dtype=bool)
    for c, k in zip(cells.tolist(), cap.tolist()):
        if not seen[c] and k > 0:
            w.land_cap[c] += k
            seen[c] = True
    from . import technology
    man = technology._q(w, ids, "manuring") * animal_part
    irr = technology._q(w, ids, "irrigation")
    np.maximum.at(w.land_manure, cells, man)
    np.maximum.at(w.land_irr, cells, irr)


def note_fuel(w, cells, units):
    if getattr(w, "game", None) is None:
        return
    np.add.at(w.land_fuel, cells, units)


# ------------------------------------------------------------------ the yearly update

def yearly(w):
    if not getattr(P, "LAND", False):
        return
    ensure(w)
    pl = w.planet
    land = pl.land
    # game: logistic regrowth, hunting, drift from neighbours
    h = np.where(w.land_wild > 0, w.land_take / np.maximum(w.land_wild, 1e-12), 0.0)
    nb = pl.grid.neighbours
    ok = (nb >= 0) & land[np.clip(nb, 0, None)]

    def step(g, growth):
        nmean = np.where(ok.any(1), (np.where(ok, g[np.clip(nb, 0, None)], 0.0).sum(1) / np.maximum(ok.sum(1), 1)), g)
        g = g + growth * g * (1 - g) - P.GAME_CATCH * h * g + P.GAME_SPREAD * (nmean - g)
        return np.where(land, np.clip(g, 0.0, 1.0), 1.0)
    w.game = step(w.game, P.GAME_GROWTH)
    w.game_fast = step(w.game_fast, P.GAME_FAST_GROWTH)
    # crops: use of the cell's capacity
    u = np.where(w.land_cap > 0, np.clip(w.land_crop / np.maximum(w.land_cap, 1e-12), 0.0, 1.0), 0.0)
    fm = forest_max(w)
    # forest: fields clear, fuel clears a little, regrowth where unused
    f = w.forest
    f = f - P.FOREST_CLEAR * u * f - P.FOREST_FUEL * w.land_fuel * fm + P.FOREST_REGROW * (1 - u) * (fm - f)
    w.forest = np.clip(f, 0.0, fm)
    # fertility: drawn down by cropping (less with manure), recovering in fallow, lost to erosion on cleared slopes
    bare = np.where(fm > 0, 1.0 - w.forest / np.maximum(fm, 1e-9), 1.0)
    F = w.fertility
    drain = P.FERT_DRAIN * u * F * (1.0 - P.MANURE_SAVE * np.clip(w.land_manure, 0, 1))
    erode = P.EROSION * _slope(w) * bare * u
    F = F - drain - erode + P.FERT_RECOVER * (1.0 - u) * (1.0 - F)
    w.fertility = np.clip(F, 0.0, 1.0)
    # salt: irrigation on dry land, slow leaching in fallow
    dry = np.clip((P.DRY_RAIN - pl.rain) / P.DRY_RAIN, 0.0, 1.0)
    S = w.salt + P.SALT_RISE * np.clip(w.land_irr, 0, 1) * u * dry - P.SALT_LEACH * w.salt * (1.0 - u)
    w.salt = np.clip(S, 0.0, 1.0)
    _crossings(w, u, h)
    _clear_year(w)


def _crossings(w, u, h):
    fm = forest_max(w)
    used_since = getattr(w, "land_since")
    year = w.year
    active = {"game": h > 0, "forest": u > 0, "soil": u > 0, "salt": u > 0}
    for j, kind in enumerate(KINDS):
        col = used_since[:, j]
        start = active[kind] & (col < 0)
        col[start] = year
    state = {
        "game": (w.game < P.LAND_GAME_LOW, w.game > P.LAND_GAME_BACK),
        "forest": ((fm > 0) & (w.forest < P.LAND_FOREST_LOW), (fm > 0) & (w.forest > P.LAND_FOREST_BACK)),
        "soil": (w.fertility < P.LAND_SOIL_LOW, w.fertility > P.LAND_SOIL_BACK),
        "salt": (w.salt > P.LAND_SALT_HIGH, w.salt < P.LAND_SALT_BACK),
    }
    text = {
        "game": "large game hunted out: {v:.0%} of its natural number, after hunting here since year {s}",
        "forest": "forest cleared: {v:.0%} of its natural cover left, after fields and fires since year {s}",
        "soil": "soil worn: fertility {v:.0%} of its natural level, after cropping since year {s}",
        "salt": "land salted: salt {v:.0%}, after irrigation since year {s} on dry land",
    }
    value = {"game": w.game, "forest": np.where(fm > 0, w.forest / np.maximum(fm, 1e-9), 1.0),
             "soil": w.fertility, "salt": w.salt}
    occupied = {b.cell for b in w.living_bands()}
    for j, kind in enumerate(KINDS):
        low, back = state[kind]
        w.land_flags[back, j] = False
        w.land_since[back & ~active[kind], j] = -1
        new = np.nonzero(low & ~w.land_flags[:, j])[0]
        for c in new.tolist():
            w.land_flags[c, j] = True
            if c not in occupied:
                continue                                    # recorded only where people live to feel it
            note = text[kind].format(v=float(value[kind][c]), s=int(w.land_since[c, j]))
            w.land_event[c, j] = w.event(f"land_{kind}", cell=c, causes=[{"note": note}],
                                         value=round(float(value[kind][c]), 3), since=int(w.land_since[c, j]))


def history(w, cell) -> str:
    """The land's recorded state on a cell, for a band's reason for moving (empty if nothing is recorded)."""
    if not getattr(P, "LAND", False) or getattr(w, "land_flags", None) is None:
        return ""
    parts = []
    names = {"game": "game hunted out", "forest": "forest cleared", "soil": "soil worn", "salt": "land salted"}
    for j, kind in enumerate(KINDS):
        if w.land_flags[cell, j] and w.land_event[cell, j] >= 0:
            parts.append(f"{names[kind]} (event {int(w.land_event[cell, j])})")
    return "; the land: " + ", ".join(parts) if parts else ""


ARRAYS = ("game", "game_fast", "forest", "fertility", "salt", "land_flags", "land_event", "land_since", "land_take", "land_wild",
          "land_crop", "land_cap", "land_manure", "land_irr", "land_fuel")
