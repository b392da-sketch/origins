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
    # ... of the crop loss, the parts taken by worn soil and by salt where that condition had a recorded event,
    # booked season by season (Codex review 024): per season from the last harvest, and this year so far; with, per
    # kind, the event of the season with the largest such loss, cited as the example (and that loss)
    w.land_crop_k = np.zeros((0, 2))
    w.land_crop_ev = -np.ones((0, 2), dtype=np.int64)
    w.land_acc_k = np.zeros((0, 2))
    w.land_acc_kev = -np.ones((0, 2), dtype=np.int64)
    w.land_acc_ktop = np.zeros((0, 2))
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
    """Per cell: natural forest cover, from the biome (cached on the planet: the biome does not change; Codex review
    022, a whole-planet scan per call)."""
    pl = w.planet
    c = getattr(pl, "_forest_max", None)
    if c is None or len(c) != pl.n:
        from ..worldgen import B
        c = pl._forest_max = np.isin(pl.biome, [B[b] for b in FOREST_BIOMES]).astype(float)
        c.flags.writeable = False
    return c


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
    fert, salt = crop_parts(w, cells)
    return fert * salt


def crop_parts(w, cells):
    """Per band (by cell): what fertility leaves of crop yields, and what salt leaves of the rest."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return np.ones(len(cells)), np.ones(len(cells))
    fert = P.FERT_FLOOR + (1.0 - P.FERT_FLOOR) * w.fertility[cells]
    over = np.clip((w.salt[cells] - P.SALT_THRESH) / (1.0 - P.SALT_THRESH), 0.0, 1.0)
    return fert, 1.0 - P.SALT_MAX_LOSS * over


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
    """trade: goods made with fire. The wood is gathered from every wooded cell within two rings, in proportion to
    its living cover, not from the cell where the goods are made (Codex review 021, finding 1; Ben, 20 November
    2026: spread it and keep it small, after Iles 2020). Goods smelted with coal within reach take no wood."""
    if getattr(w, "game", None) is None:
        return
    cells = np.asarray(cells)
    units = np.asarray(units, dtype=float)
    if coal_ok:
        from . import technology
        coal = technology._cell_materials(w)[cells, technology.MATERIALS.index("coal")]
        units = np.where(coal, 0.0, units)
    on = units > 0
    if not on.any():
        return
    idx, ok = _ring2_padded(w)
    c, u = cells[on], units[on]
    cover = np.where(ok[c], w.forest[idx[c]], 0.0)
    tot = cover.sum(axis=1)
    has = tot > 0
    share = cover[has] / tot[has, None]
    np.add.at(w.land_fuel, idx[c[has]].ravel(), (share * u[has, None]).ravel())


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
    # forest use starts with fields or with fuel cut there (Codex review 022, finding 7)
    active = {"game": h > 0, "forest": (u > 0) | (w.land_fuel > 0), "soil": u > 0, "salt": u > 0}
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


def _links(w, band_id: int, cell: int):
    """The land events behind each pool of a band's loss this season: (wild events, crop events). Lost game and
    forest are looked up on the band's cell (this season's wild food). Worn and salted soil are the events recorded
    where the crops were grown, when they were grown (Codex review 023, finding 3), so a later move, a sowing
    elsewhere, or the soil's recovery does not change them."""
    wild, crop = [], []
    lw, lc = float(w.land_lost_wild[band_id]), float(w.land_lost_crop[band_id])
    if lw > 0:
        for j, kind in enumerate(KINDS[:2]):
            e = int(w.land_event[cell, j])
            if w.land_flags[cell, j] and e >= 0 and kind_factors(w, cell)[kind] < 1.0:
                wild.append(e)
    ck = getattr(w, "land_crop_k", None)
    if lc > 0 and ck is not None and band_id < len(ck):
        crop = [int(w.land_crop_ev[band_id, j]) for j in range(2)
                if ck[band_id, j] > 0 and w.land_crop_ev[band_id, j] >= 0]
    return wild, crop


def crop_linked(w, band_id: int) -> float:
    """Of a band's crop loss per season, the part taken by soil or salt conditions with a recorded event."""
    ck = getattr(w, "land_crop_k", None)
    if ck is None or band_id >= len(ck):
        return 0.0
    return float(min(ck[band_id].sum(), w.land_lost_crop[band_id]))


def felt(w, band_id: int, cell: int) -> list:
    """The land events behind a band's shortfall this season, as contributing causes (Ben, 20 November 2026, after
    Codex review 022): every recorded loss that took food from a band that went short, ranked by the size of its
    pool's loss. No claim that the land alone caused the shortfall: the amounts are stated in hunger_event."""
    if not getattr(P, "LAND", False) or getattr(w, "land_flags", None) is None:
        return []
    a = getattr(w, "land_short", None)
    if a is None or band_id >= len(a) or float(w.land_short[band_id]) <= 0:
        return []
    wild, crop = _links(w, band_id, cell)
    lw, lc = float(w.land_lost_wild[band_id]), float(w.land_lost_crop[band_id])
    first, second = (wild, crop) if lw >= lc else (crop, wild)
    return first + second


def hunger_event(w, band_id: int, cell: int) -> int:
    """One event per band and season linking its hunger to the land, with the amounts (Ben, 20 November 2026:
    contributing cause). Only the pools with a linked land event are counted as the land's; a loss from a pool
    with no recorded event is stated apart (Codex review 023, finding 4). The crop amount is the last harvest's
    loss spread evenly over the year's seasons, a budget convention, not the food missing this season. Made where
    a death is recorded; every band-season of exposure is counted in note_account. -1 if nothing is linked."""
    cache = getattr(w, "_land_hunger", None)
    if cache is None or cache[0] != w.t:
        cache = w._land_hunger = (w.t, {})
    if band_id in cache[1]:
        return cache[1][band_id]
    e = -1
    if felt(w, band_id, cell):
        wild, crop = _links(w, band_id, cell)
        short, lw, lc = float(w.land_short[band_id]), float(w.land_lost_wild[band_id]), float(w.land_lost_crop[band_id])
        lw_l, lc_l = (lw if wild else 0.0), (crop_linked(w, band_id) if crop else 0.0)
        parts = []
        if lw_l > 0:
            parts.append(f"lost game and forest took {lw_l:,.0f} from its wild food this season")
        if lc_l > 0:
            parts.append(f"worn or salted soil took {lc_l:,.0f} a season from its crops (the last harvest's loss, "
                         f"spread over the year)")
        other = (lw - lw_l) + (lc - lc_l)
        note = (f"{w.band_name(w.bands[band_id])} lacked {short:,.0f} of the food it needed this season; "
                + " and ".join(parts)
                + (f"; a further {other:,.0f} lost from its food is not tied to a recorded land event" if other > 0 else ""))
        e = w.event("land_hunger", cell=cell, band=band_id,
                    causes=[{"note": note}] + [{"event": x} for x in felt(w, band_id, cell)],
                    short=round(short, 1), lost_wild=round(lw_l, 1), lost_crop=round(lc_l, 1),
                    unlinked=float(other))
    cache[1][band_id] = e
    return e


def _band_rows(w, n):
    for name in ("land_short", "land_lost_wild", "land_lost_crop", "land_crop_acc", "land_crop_k", "land_crop_ev",
                 "land_acc_k", "land_acc_kev", "land_acc_ktop"):
        a = getattr(w, name, None)
        if a is not None and name in ("land_crop_k", "land_crop_ev", "land_acc_k", "land_acc_kev", "land_acc_ktop") \
                and (a.ndim != 2 or a.shape[1:] != (2,)):
            a = None                                  # an older save's array of another shape: start afresh
        if a is None or len(a) < n:
            size = max(n, 64, 2 * len(a)) if a is not None else max(n, 64)
            if name.endswith("ev"):
                b = -np.ones((size, 2), dtype=np.int64)
            elif name in ("land_crop_k", "land_acc_k", "land_acc_ktop"):
                b = np.zeros((size, 2))
            else:
                b = np.zeros(size)
            if a is not None and len(a):
                b[:len(a)] = a
            setattr(w, name, b)


def move_crop_loss(w, src: int, dst: int, frac: float):
    """The crop loss goes with the share of the standing crop and stores that moves (Codex review 022, finding 3).
    The linked parts move with it, kind by kind; the receiving band takes the moving part's example event (with its
    season's loss) where the moving part of that kind is the larger (Codex review 024, finding 2)."""
    if getattr(w, "land_crop_acc", None) is None or not getattr(P, "LAND", False):
        return
    _band_rows(w, max(src, dst) + 1)
    for name in ("land_crop_acc", "land_lost_crop"):
        a = getattr(w, name)
        x = a[src] * frac
        a[dst] += x
        a[src] -= x
    for amt, ev, top in (("land_acc_k", "land_acc_kev", "land_acc_ktop"), ("land_crop_k", "land_crop_ev", None)):
        a, e = getattr(w, amt), getattr(w, ev)
        for j in range(2):
            x = a[src, j] * frac
            if x > a[dst, j]:
                e[dst, j] = e[src, j]
                if top:
                    getattr(w, top)[dst, j] = getattr(w, top)[src, j]
            a[dst, j] += x
            a[src, j] -= x


def drop_crop_loss(w, band_id: int):
    """A band that ends with nobody to take its fields loses its standing crop and its loss record."""
    if getattr(w, "land_crop_acc", None) is None:
        return
    _band_rows(w, band_id + 1)                    # older saves may hold some of these rows and not others (review 024)
    w.land_crop_acc[band_id] = w.land_lost_crop[band_id] = 0.0
    w.land_crop_k[band_id] = w.land_acc_k[band_id] = w.land_acc_ktop[band_id] = 0.0
    w.land_crop_ev[band_id] = w.land_acc_kev[band_id] = -1


def note_crop_loss(w, ids, lost, cells=None, parts=None):
    """farming, each season: crops worn or salted soil took from each band. At the harvest the year's loss becomes
    the band's crop loss per season until the next harvest (the crops feed it through the year). parts: the soil
    and salt parts of the loss; each is booked as linked where that condition has a recorded event on the cell
    (Codex review 024, findings 3 and 4: so a salt flag below the yield threshold links nothing, and each season's
    linked amount is kept, not one season's events for the whole year)."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return
    ids = np.asarray(ids)
    _band_rows(w, int(np.max(ids, initial=-1)) + 1)
    lost = np.asarray(lost, dtype=float)
    np.add.at(w.land_crop_acc, ids, lost)
    if cells is not None and parts is not None:
        cells = np.asarray(cells)
        for j, kind in enumerate(("soil", "salt")):
            k = KINDS.index(kind)
            part = np.asarray(parts[j], dtype=float)
            ev = np.where(w.land_flags[cells, k], w.land_event[cells, k], -1)
            on = (part > 0) & (ev >= 0)
            if not on.any():
                continue
            oi, op, oe = ids[on], part[on], ev[on]
            np.add.at(w.land_acc_k[:, j], oi, op)
            top = op > w.land_acc_ktop[oi, j]
            w.land_acc_kev[oi[top], j] = oe[top]
            w.land_acc_ktop[oi[top], j] = op[top]
    if w.quarter == P.HARVEST_QUARTER:
        w.land_lost_crop[ids] = w.land_crop_acc[ids] / P.TICKS_PER_YEAR
        w.land_crop_k[ids] = w.land_acc_k[ids] / P.TICKS_PER_YEAR
        w.land_crop_ev[ids] = w.land_acc_kev[ids]
        w.land_crop_acc[ids] = 0.0
        w.land_acc_k[ids] = 0.0
        w.land_acc_kev[ids] = -1
        w.land_acc_ktop[ids] = 0.0


def note_account(w, ids, short, lost_wild, cells=None):
    """foraging, each season: each band's shortfall, and the wild food lost game and forest took from it. With the
    cells, every band-season of exposure is counted (Codex review 023, finding 5: the events are made only where a
    death is recorded): band-seasons short of food; of those, with a land loss linked to a recorded event, by pool;
    and the food lacked and the linked loss, summed."""
    if not getattr(P, "LAND", False) or getattr(w, "game", None) is None:
        return
    ids = np.asarray(ids)
    _band_rows(w, int(np.max(ids, initial=-1)) + 1)
    w.land_short[ids] = short
    w.land_lost_wild[ids] = lost_wild
    if cells is None:
        return
    cells = np.asarray(cells)
    short = np.asarray(short, dtype=float)
    lw = np.asarray(lost_wild, dtype=float)
    lc = w.land_lost_crop[ids]
    fm = forest_max(w)[cells]
    jg, jf = KINDS.index("game"), KINDS.index("forest")
    # the same factor tests as kind_factors, for all bands at once (Codex review 024, finding 5)
    game_f = 1.0 - P.GAME_SHARE * (1.0 - w.game[cells]) - P.GAME_FAST_SHARE * (1.0 - w.game_fast[cells])
    forest_f = np.where(fm > 0, 1.0 - P.FOREST_WILD * fm * (1.0 - w.forest[cells] / np.maximum(fm, 1e-9)), 1.0)
    game_ok = w.land_flags[cells, jg] & (w.land_event[cells, jg] >= 0) & (game_f < 1.0)
    forest_ok = w.land_flags[cells, jf] & (w.land_event[cells, jf] >= 0) & (forest_f < 1.0)
    wl = (short > 0) & (lw > 0) & (game_ok | forest_ok)
    ck = np.where(w.land_crop_ev[ids] >= 0, w.land_crop_k[ids], 0.0).sum(axis=1)
    lc = np.minimum(ck, lc)                       # the linked part only (Codex review 024, finding 4)
    cl = (short > 0) & (lc > 0)
    c = w.counts
    for k, v in (("land_exp_short", int((short > 0).sum())), ("land_exp_linked", int((wl | cl).sum())),
                 ("land_exp_wild_only", int((wl & ~cl).sum())), ("land_exp_crop_only", int((cl & ~wl).sum())),
                 ("land_exp_both", int((wl & cl).sum()))):
        c[k] = c.get(k, 0) + v
    c["land_exp_short_sum"] = c.get("land_exp_short_sum", 0.0) + float(short[short > 0].sum())
    c["land_exp_linked_sum"] = c.get("land_exp_linked_sum", 0.0) + float(
        np.minimum(np.where(wl, lw, 0.0) + np.where(cl, lc, 0.0), short)[wl | cl].sum())


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
          "land_lost_crop", "land_crop_acc", "land_crop_k", "land_crop_ev", "land_acc_k", "land_acc_kev", "land_acc_ktop")
