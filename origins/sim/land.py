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
- fallow: the share of farmland resting each year. It gives way to need: farmers crop as much of the land as they
  could work last year, and the rest rests, between FALLOW_MIN and FALLOW_MAX (Boserup 1965; Ben, 19 November 2026,
  after Codex review 020). Resting land is taken from crop capacity; it lets fertility recover. The extra labour per
  unit of crop that shorter fallow costs (Boserup) is not modelled.
- salt: salt on irrigated dry land. It rises with irrigation in dry climates and falls only slowly in fallow;
  above SALT_THRESH it cuts crop yields (Jacobsen & Adams 1958; contested by Powell 1985).

Use is measured over each year: hunting as the year's take of ordinary wild food against the year's seasonal
maxima; farming as the share of the cell's farmland worked for crops, averaged over the seasons it was farmed. The
worked share is judged before fertility and salt losses, so a poor harvest from the same fields does not count as
resting land (Codex review 020, finding 1). The yearly update runs after trade, at the harvest, and draws no random
numbers.

Fuel: smelting and iron working need living forest (or coal) within two rings; their output scales with the forest
left on the best-wooded cell there (Ben, 19 November 2026: fuel limits output; Codex review 020, finding 2).

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
    w.fallow = np.full(n, P.FALLOW_MAX)        # share of farmland resting, set each year by need (Boserup 1965)
    w.land_short = np.zeros(0)                 # per band, this season: shortfall of food against needs
    w.land_lost_wild = np.zeros(0)             # ... wild food lost game and forest took from its harvest
    w.land_lost_crop = np.zeros(0)             # ... crops worn or salted soil took, per season, from the last harvest
    w.land_crop_acc = np.zeros(0)              # ... crops lost so far this year, before the harvest
    w.land_flags = np.zeros((n, len(KINDS)), dtype=bool)   # crossed and not yet recovered
    w.land_event = -np.ones((n, len(KINDS)), dtype=np.int64)
    w.land_since = -np.ones((n, len(KINDS)), dtype=np.int64)   # year the use began that led to the crossing
    _clear_year(w)


def _clear_year(w):
    n = w.planet.n
    w.land_take = np.zeros(n)       # this year's take of ordinary wild food
    w.land_wild = np.zeros(n)       # this year's seasonal maxima of ordinary wild food
    w.land_work = np.zeros(n)       # this year's share of farmland worked for crops, summed over farmed seasons
    w.land_seasons = np.zeros(n)    # seasons this year in which the cell was farmed
    w.land_need = np.zeros(n)       # share of farmland the farmers would have worked for crops with no fallow
    w.land_manure = np.zeros(n)     # sum over bands of worked share x manuring x herds share
    w.land_irr = np.zeros(n)        # sum over bands of worked share x irrigation quality
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


def cropped_share(w, cells) -> np.ndarray:
    """Per band (by cell): the share of farmland under crops this year; the rest rests in fallow."""
    if not getattr(P, "LAND", False) or getattr(w, "fallow", None) is None:
        return np.ones(len(cells))
    return 1.0 - w.fallow[cells]


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


def note_crops(w, ids, cells, worked, animal_part, need=None):
    """farming, each season: the share of each farmed cell's land worked for crops (each band's crops before
    fertility and salt, against the cell's whole farmland; summed over the bands there, at most 1), and the
    manuring and irrigation of its farmers. Independent of the order of the bands (Codex review 020, finding 1)."""
    if getattr(w, "game", None) is None:
        return
    season = np.zeros(w.planet.n)
    np.add.at(season, cells, worked)
    farmed = np.zeros(w.planet.n, dtype=bool)
    farmed[cells] = True
    w.land_work += np.clip(season, 0.0, 1.0)
    w.land_seasons += farmed
    if need is not None:
        wanted = np.zeros(w.planet.n)
        np.add.at(wanted, cells, need)
        w.land_need += np.clip(wanted, 0.0, 1.0)
    from . import technology
    # irrigation and manuring count for the crops each band actually works (Codex review 021, finding 4): sums of
    # worked share x quality, divided by the worked share in the yearly update
    man = technology._q(w, ids, "manuring") * animal_part
    irr = technology._q(w, ids, "irrigation")
    np.add.at(w.land_manure, cells, worked * man)
    np.add.at(w.land_irr, cells, worked * irr)


def note_fuel(w, cells, units, coal_ok=False):
    """trade: goods made with fire. The wood is taken from the best-wooded cell within two rings, the one that
    supplies it, not the cell where the goods are made; goods smelted with coal within reach take no wood (Codex
    review 021, finding 1)."""
    if getattr(w, "game", None) is None:
        return
    cells = np.asarray(cells)
    units = np.asarray(units, dtype=float)
    src = wood_source(w, cells)
    take = units * (src >= 0)
    if coal_ok:
        from . import technology
        coal = technology._cell_materials(w)[cells, technology.MATERIALS.index("coal")]
        take = np.where(coal, 0.0, take)
    ok = take > 0
    np.add.at(w.land_fuel, src[ok], take[ok])


def wood_source(w, cells) -> np.ndarray:
    """Per given cell: the best-wooded cell within two rings (-1 where there is no living forest)."""
    idx, ok = _ring2_padded(w)
    cells = np.asarray(cells)
    f = np.where(ok[cells], w.forest[idx[cells]], -1.0)
    j = f.argmax(axis=1)
    best = idx[cells, j]
    return np.where(f[np.arange(len(cells)), j] > 0, best, -1)


# ------------------------------------------------------------------ the yearly update

def use(w) -> np.ndarray:
    """Per cell: the share of its farmland worked for crops this year (0 where it was not farmed)."""
    return np.where(w.land_seasons > 0, np.clip(w.land_work / np.maximum(w.land_seasons, 1), 0.0, 1.0), 0.0)


def fuel(w, cells=None) -> np.ndarray:
    """Per cell (or for the given cells): the fuel within two rings for smelting, 0..1. Coal within reach gives
    full fuel; otherwise the best-wooded cell within two rings, its living cover against FUEL_FULL (Ben, 19 November
    2026). The best cell, not the mean: one well-wooded cell of some 3,000 km2 within reach is enough wood, as the
    biome rule before it said."""
    n = w.planet.n
    cells = np.arange(n) if cells is None else np.asarray(cells)
    if not getattr(P, "LAND", False) or getattr(w, "forest", None) is None:
        from . import technology
        m = technology._cell_materials(w)[cells]
        have = m[:, technology.MATERIALS.index("forest")] | m[:, technology.MATERIALS.index("coal")]
        return have.astype(float)
    from . import technology
    coal = technology._cell_materials(w)[cells, technology.MATERIALS.index("coal")]
    wood = np.clip(forest_near(w)[cells] / P.FUEL_FULL, 0.0, 1.0)
    return np.where(coal, 1.0, wood)


def forest_near(w) -> np.ndarray:
    """Per cell: the living forest cover of the best-wooded cell within two rings (cached until the forest
    changes)."""
    key = (w.year, id(w.forest))
    c = getattr(w, "_forest_near", None)
    if c is not None and c[0] == key:
        return c[1]
    idx, ok = _ring2_padded(w)
    f = np.where(ok, w.forest[idx], 0.0).max(1)
    w._forest_near = (key, f)
    return f


def _ring2_padded(w):
    pl = w.planet
    r = getattr(pl, "_ring2_pad", None)
    if r is None:
        from .language import ring2
        rr = ring2(w)
        k = max(len(x) for x in rr)
        idx = np.zeros((pl.n, k), dtype=np.int64)
        ok = np.zeros((pl.n, k), dtype=bool)
        for c, x in enumerate(rr):
            idx[c, :len(x)] = x
            ok[c, :len(x)] = True
        r = pl._ring2_pad = (idx, ok)
    return r


def yearly(w):
    if not getattr(P, "LAND", False):
        if getattr(w, "game", None) is not None:
            _clear_year(w)                  # switched off: the accounts do not pile up (Codex review 020, finding 7)
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
    u = use(w)
    fm = forest_max(w)
    # forest: fields clear the land they take, fast; fuel clears a little; the rest regrows over centuries. The
    # forest left under fields tends to the unworked share of the cell, not to nothing (corrected 19 November 2026:
    # a cell worked at 30% lost about 93% of its forest before)
    f = w.forest
    room = fm * (1.0 - u)
    f = (f - P.FOREST_CLEAR * np.maximum(f - room, 0.0) - P.FOREST_FUEL * w.land_fuel * fm
         + P.FOREST_REGROW * np.maximum(room - f, 0.0))
    w.forest = np.clip(f, 0.0, fm)
    w._forest_near = None
    # fertility: drawn down by cropping (less with manure), recovering in fallow, lost to erosion on cleared slopes
    bare = np.where(fm > 0, 1.0 - w.forest / np.maximum(fm, 1e-9), 1.0)
    F = w.fertility
    worked = np.maximum(w.land_work, 1e-12)
    manure = np.clip(w.land_manure / worked, 0, 1)      # mean over the crops worked (Codex review 021, finding 4)
    irrig = np.clip(w.land_irr / worked, 0, 1)
    drain = P.FERT_DRAIN * u * F * (1.0 - P.MANURE_SAVE * manure)
    erode = P.EROSION * _slope(w) * bare * u
    F = F - drain - erode + P.FERT_RECOVER * (1.0 - u) * (1.0 - F)
    w.fertility = np.clip(F, 0.0, 1.0)
    # salt: irrigation on dry land, slow leaching in fallow
    dry = np.clip((P.DRY_RAIN - pl.rain) / P.DRY_RAIN, 0.0, 1.0)
    S = w.salt + P.SALT_RISE * irrig * u * dry - P.SALT_LEACH * w.salt * (1.0 - u)
    w.salt = np.clip(S, 0.0, 1.0)
    _crossings(w, u, h)
    # fallow for the coming year gives way to need (Ben, 19 November 2026, after review 020; Boserup 1965): farmers
    # crop as much of the land as they can work, and the rest rests, between FALLOW_MIN and FALLOW_MAX
    need = np.where(w.land_seasons > 0, w.land_need / np.maximum(w.land_seasons, 1), 0.0)
    w.fallow = np.clip(1.0 - need, P.FALLOW_MIN, P.FALLOW_MAX)
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
    occupied = np.zeros(w.planet.n, dtype=bool)
    for b in w.living_bands():
        occupied[b.cell] = True
    for j, kind in enumerate(KINDS):
        low, back = state[kind]
        w.land_flags[back, j] = False
        w.land_event[back, j] = -1                      # recovered: no stale event (Codex review 020, finding 4)
        w.land_since[back & ~active[kind], j] = -1
        # recorded only where people live to feel it; an empty cell stays un-flagged, so people arriving while the
        # land is still poor record the crossing then (Codex review 020, finding 4)
        new = np.nonzero(low & ~w.land_flags[:, j] & occupied)[0]
        for c in new.tolist():
            w.land_flags[c, j] = True
            note = text[kind].format(v=float(value[kind][c]), s=int(w.land_since[c, j]))
            w.land_event[c, j] = w.event(f"land_{kind}", cell=c, causes=[{"note": note}],
                                         value=round(float(value[kind][c]), 3), since=int(w.land_since[c, j]))


def kind_factors(w, cell: int) -> dict:
    """What each kind of loss leaves of its own part of the food on a cell (1 = no loss)."""
    fm = forest_max(w)[cell]
    fert = P.FERT_FLOOR + (1.0 - P.FERT_FLOOR) * w.fertility[cell]
    over = min(max((w.salt[cell] - P.SALT_THRESH) / (1.0 - P.SALT_THRESH), 0.0), 1.0)
    return {"game": 1.0 - P.GAME_SHARE * (1.0 - w.game[cell]) - P.GAME_FAST_SHARE * (1.0 - w.game_fast[cell]),
            "forest": 1.0 - P.FOREST_WILD * fm * (1.0 - w.forest[cell] / max(fm, 1e-9)) if fm > 0 else 1.0,
            "soil": float(fert), "salt": 1.0 - P.SALT_MAX_LOSS * over}


def felt(w, band_id: int, cell: int) -> list:
    """The land events to cite for a band's shortfall this season (Ben, 19 November 2026, after Codex review 021:
    the food account test). The band's food account records what lost game and forest took from the wild food it
    actually harvested, and what worn or salted soil took from the crops it actually grew; the land is cited only if
    restoring that would have covered its shortfall. Within each pool, the events are ranked by their own loss."""
    if not getattr(P, "LAND", False) or getattr(w, "land_flags", None) is None:
        return []
    a = getattr(w, "land_short", None)
    if a is None or band_id >= len(a):
        return []
    short, lw, lc = float(w.land_short[band_id]), float(w.land_lost_wild[band_id]), float(w.land_lost_crop[band_id])
    if short <= 0 or lw + lc < short:
        return []
    fac = kind_factors(w, cell)
    out = []
    for j, kind in enumerate(KINDS):
        e = int(w.land_event[cell, j])
        if not w.land_flags[cell, j] or e < 0:
            continue
        lost = lw if kind in ("game", "forest") else lc
        if lost > 0 and fac[kind] < 1.0:
            out.append((-lost, fac[kind], e))
    return [e for _l, _f, e in sorted(out)]


def _band_rows(w, n):
    for name in ("land_short", "land_lost_wild", "land_lost_crop", "land_crop_acc"):
        a = getattr(w, name, None)
        if a is None or len(a) < n:
            b = np.zeros(max(n, 64) if a is None else max(n, 2 * len(a)))
            if a is not None:
                b[:len(a)] = a
            setattr(w, name, b)


def note_crop_loss(w, ids, lost):
    """farming, each season: crops worn or salted soil took from each band. At the harvest the year's loss becomes
    the band's crop loss per season until the next harvest (the crops feed it through the year)."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return
    ids = np.asarray(ids)
    _band_rows(w, int(np.max(ids, initial=-1)) + 1)
    np.add.at(w.land_crop_acc, ids, lost)
    if w.quarter == P.HARVEST_QUARTER:
        w.land_lost_crop[ids] = w.land_crop_acc[ids] / P.TICKS_PER_YEAR
        w.land_crop_acc[ids] = 0.0


def note_account(w, ids, short, lost_wild):
    """foraging, each season: each band's shortfall, and the wild food lost game and forest took from it."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return
    ids = np.asarray(ids)
    _band_rows(w, int(np.max(ids, initial=-1)) + 1)
    w.land_short[ids] = short
    w.land_lost_wild[ids] = lost_wild


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


ARRAYS = ("game", "game_fast", "forest", "fertility", "salt", "fallow", "land_flags", "land_event", "land_since", "land_take", "land_wild",
          "land_work", "land_seasons", "land_need", "land_manure", "land_irr", "land_fuel", "land_short", "land_lost_wild",
          "land_lost_crop", "land_crop_acc")
