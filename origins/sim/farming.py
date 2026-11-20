"""Domestication and farming (M2): farming is an option, not a destiny.

Nine wild progenitors are placed unevenly by world generation. A people that
stays long in land with one of them, and is pressed for food, begins to tend it;
tending becomes cultivation, and long cultivation domestication. Skill is held
by each band, inherited when it splits and learned from neighbours. Once a
species is domesticated, its people can grow it wherever it suits, and so can
anyone who learns it from them.

Every year each band divides its work between foraging and farming by comparing
the food each brings per day of work, with inertia. Nothing forces adoption.
Crops are harvested once a year (and must be stored to last); herds give food
every season. Bands that live mainly from farming stop moving and become
villages; the first village to rely mainly on farming for three generations is
recorded as the world's first farming village, which switches the observer's
clock.

reads: planet (biome, rain, temperature, rivers, domesticables), bands, stock, margin
writes: skill, farm_share, crop_store, still_years, bands (village, farm_years), events, counts
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..worldgen import B, DOMESTICABLES

SPECIES = DOMESTICABLES                      # wild_grain ... wild_horse
PLANTS = [i for i, s in enumerate(SPECIES) if s in ("wild_grain", "wild_legume", "wild_tuber", "wild_rice")]
ANIMALS = [i for i, s in enumerate(SPECIES) if i not in PLANTS]
NAMES = {"wild_grain": "grain", "wild_legume": "legumes", "wild_tuber": "tubers", "wild_rice": "rice",
         "wild_goat": "goats", "wild_sheep": "sheep", "wild_cattle": "cattle", "wild_pig": "pigs",
         "wild_horse": "horses"}
SUITED = {
    "wild_grain": ("grassland", "temperate_forest", "savanna"),
    "wild_legume": ("grassland", "temperate_forest", "savanna"),
    "wild_tuber": ("tropical_forest", "savanna", "temperate_forest"),
    "wild_rice": ("tropical_forest", "savanna"),
    "wild_goat": ("alpine", "grassland", "savanna", "temperate_forest"),
    "wild_sheep": ("alpine", "grassland", "temperate_forest", "tundra"),
    "wild_cattle": ("grassland", "savanna", "temperate_forest"),
    "wild_pig": ("temperate_forest", "tropical_forest", "boreal_forest"),
    "wild_horse": ("grassland", "tundra"),
}
STAGES = ["wild", "tending", "cultivation", "domestication", "domesticated"]


def stage_name(x: float) -> str:
    return STAGES[min(int(x) + (1 if x > 0 else 0), 4)] if x < 3 else "domesticated"


# ------------------------------------------------------------------ land
def land_tables(w):
    """Per cell and species: is it wild here, and how well can it be farmed or herded here (0..1)."""
    pl = w.planet
    if getattr(pl, "_farm", None) is not None:
        return pl._farm
    n = pl.n
    wild = np.zeros((n, len(SPECIES)), dtype=bool)
    suit = np.zeros((n, len(SPECIES)))
    rain_ok = np.clip((pl.rain - 250.0) / 700.0, 0, 1)
    warm_ok = np.clip((pl.temp_mean - 2.0) / 10.0, 0, 1)
    water = np.where(pl.river, 1.4, 1.0)
    for k, s in enumerate(SPECIES):
        wild[:, k] = pl.domesticables[s] & pl.land
        biomes = np.isin(pl.biome, [B[x] for x in SUITED[s]]) & pl.land
        if k in PLANTS:
            suit[:, k] = biomes * np.clip(rain_ok * warm_ok * water, 0, 1)
        else:
            suit[:, k] = biomes * np.clip(0.4 + 0.6 * rain_ok, 0, 1)
    pl._farm = (wild, suit)
    return pl._farm


def quality(skill):
    """How productive a species is in a people's hands: little while tended, full once domesticated."""
    s = np.asarray(skill, dtype=float)
    return np.where(s < 1, 0.15 * s, np.where(s < 2, 0.15 + 0.25 * (s - 1),
                                              np.where(s < 3, 0.4 + 0.45 * (s - 2), 1.0)))


# ------------------------------------------------------------------ state
def init(w):
    cap = 64
    w.skill = np.zeros((cap, len(SPECIES)), dtype=np.float32)
    w.farm_share = np.zeros(cap)
    w.crop_store = np.zeros(cap)            # this year's standing crop, harvested in the harvest season
    w.still_years = np.zeros(cap)           # years since the band last moved
    w.forage_rr = np.full(cap, P.FORAGE_RATE)   # recent food per worker-day from foraging
    w.herder_since = np.full(cap, -1.0)     # tick a band first moved with its herds (M4a pastoralism), or -1
    w.farm_rr_real = np.full(cap, np.nan)   # recent food per worker-day actually got from fields and herds (M4a land)
    w.farm_rr_cell = np.full(cap, -1, dtype=np.int64)   # the cell where it was got
    w.farm_rr_lost = np.zeros(cap)          # of which worn or salted soil took, per worker-day, on the same terms
    w.first_village = None                  # event id of the first farming village
    w.farm_firsts = {}                      # species -> {stage: event id} (first anywhere in the world)


def ensure(w, band_id: int, parent: int):
    if band_id >= len(w.farm_share):
        cap = len(w.farm_share)
        while cap <= band_id:
            cap *= 2
        if not hasattr(w, "herder_since"):
            w.herder_since = np.full(len(w.farm_share), -1.0)
        if getattr(w, "farm_rr_real", None) is None:
            w.farm_rr_real = np.full(len(w.farm_share), np.nan)
        if getattr(w, "farm_rr_cell", None) is None or len(w.farm_rr_cell) != len(w.farm_rr_real):
            w.farm_rr_cell = np.full(len(w.farm_rr_real), -1, dtype=np.int64)
        if getattr(w, "farm_rr_lost", None) is None or len(w.farm_rr_lost) != len(w.farm_rr_real):
            w.farm_rr_lost = np.zeros(len(w.farm_rr_real))
        for name in ("skill", "farm_share", "crop_store", "still_years", "forage_rr", "herder_since", "farm_rr_real",
                     "farm_rr_cell", "farm_rr_lost"):
            old = getattr(w, name)
            new = np.zeros((cap,) + old.shape[1:], dtype=old.dtype)
            if name == "forage_rr":
                new[:] = P.FORAGE_RATE
            if name == "herder_since":
                new[:] = -1.0
            if name == "farm_rr_real":
                new[:] = np.nan
            if name == "farm_rr_cell":
                new[:] = -1
            new[:len(old)] = old
            setattr(w, name, new)
    if parent >= 0:
        w.skill[band_id] = w.skill[parent]
        w.farm_share[band_id] = w.farm_share[parent]
        w.forage_rr[band_id] = w.forage_rr[parent]
        if hasattr(w, "herder_since"):
            w.herder_since[band_id] = w.herder_since[parent]


def best(w, b) -> tuple:
    """The band's most productive plant and animal here: (plant k, plant value, animal k, animal value)."""
    wild, suit = land_tables(w)
    c = b.cell
    sk = w.skill[b.id]
    usable = (sk >= 3) | wild[c]                     # before domestication a species must grow wild here
    val = np.where(usable, quality(sk) * suit[c], 0.0)
    kp = PLANTS[int(np.argmax(val[PLANTS]))]
    ka = ANIMALS[int(np.argmax(val[ANIMALS]))]
    return kp, float(val[kp]), ka, float(val[ka])


def best_all(w, ids, cells):
    """best() for many bands at once: arrays (plant k, plant value, animal k, animal value)."""
    wild, suit = land_tables(w)
    sk = w.skill[ids]
    usable = (sk >= 3) | wild[cells]
    val = np.where(usable, quality(sk) * suit[cells], 0.0)
    pv, av = val[:, PLANTS], val[:, ANIMALS]
    ip, ia = np.argmax(pv, axis=1), np.argmax(av, axis=1)
    rows = np.arange(len(ids))
    return np.array(PLANTS)[ip], pv[rows, ip], np.array(ANIMALS)[ia], av[rows, ia]


def best_farm_cell(w, b, occupied):
    """Where a daughter village can farm best: a neighbouring land cell where the village's crops or herds
    grow, least crowded for its farm capacity (None if there is nowhere)."""
    wild, suit = land_tables(w)
    sk = w.skill[b.id]
    best, best_v = None, 0.0
    from . import land
    plant = np.zeros(len(SPECIES), dtype=bool)
    plant[PLANTS] = True
    for m in w.planet.grid.neighbours[b.cell]:
        m = int(m)
        if m < 0 or not w.planet.land[m]:
            continue
        usable = (sk >= 3) | wild[m]
        # crops judged at their real yields there: worn or salted soil, and land resting in fallow (M4a land)
        real = np.where(plant, float(land.crop_factor(w, np.array([m]))[0] * land.cropped_share(w, np.array([m]))[0]),
                        1.0) if getattr(P, "REAL_YIELDS", True) else 1.0
        v = float(np.max(np.where(usable, quality(sk) * suit[m] * real, 0.0)))
        room = v * P.FARM_CAPACITY / (occupied.get(m, 0.0) + 1.0)
        if v > 0 and room > best_v:
            best, best_v = m, room
    return best


# ------------------------------------------------------------------ each season: food from fields and herds
def season_food(w, ids, cells, effort):
    """Split each band's work; return (forage effort, farm food this season) per band id array.

    Plant food grows over the year and is released at harvest (the third season); herds feed every season.
    Fields in a cell are shared among the bands farming there, in proportion to their work."""
    nb_ = len(effort)
    forage_eff = effort.copy()
    food = np.zeros(nb_)
    share = w.farm_share[:nb_]
    if not share[ids].any():
        return forage_eff, food
    _, suit = land_tables(w)
    farm_eff = np.zeros(nb_)
    farm_eff[ids] = effort[ids] * share[ids]
    forage_eff[ids] = effort[ids] - farm_eff[ids]
    vals = np.zeros(nb_)
    caps = np.zeros(nb_)
    animal_part = np.zeros(nb_)
    on = share[ids] > 0
    fid, fcell = ids[on], cells[on]
    kp, vp, ka, va = best_all(w, fid, fcell)
    vals[fid] = np.maximum(vp, va)
    animal_part[fid] = va / np.maximum(vp + va, 1e-9)
    # land: farmed food a cell can give per season, by its suitability for the species used
    caps[fid] = P.FARM_CAPACITY * np.maximum(suit[fcell, kp] * (vp > 0), suit[fcell, ka] * (va > 0)) * P.SEASON_DAYS
    cell_eff = np.zeros(w.planet.n)
    np.add.at(cell_eff, cells, farm_eff[ids])
    land_share = np.where(cell_eff[cells] > 0, farm_eff[ids] / np.maximum(cell_eff[cells], 1e-12), 0.0)
    # farm_eff is in foraging effort units (worker-days x FORAGE_RATE); FARM_RATE is food per worker-day at full quality
    grown = np.minimum(farm_eff[ids] / P.FORAGE_RATE * P.FARM_RATE * vals[ids], caps[ids] * land_share)
    herd = grown * animal_part[ids]
    crop = grown - herd
    w.crop_store[ids] += crop
    food[ids] = herd
    if w.quarter == P.HARVEST_QUARTER:
        food[ids] += w.crop_store[ids]
        w.crop_store[ids] = 0.0
    w.ledger["farmed"] = w.ledger.get("farmed", 0.0) + float(food[ids].sum())
    return forage_eff, food


# ------------------------------------------------------------------ each year: skills, choices, villages
def yearly(w):
    if not P.FARMING:
        return
    rng = w.rng["farming"]
    bands = w.living_bands()
    if not bands:
        return
    from .language import ring2
    r2 = ring2(w)
    wild, suit = land_tables(w)
    years = 1.0
    crowd = crowding(w, bands)
    w._press_why = {}
    by_cell: dict[int, list] = {}
    for b in bands:
        by_cell.setdefault(b.cell, []).append(b)
    old = {b.id: w.skill[b.id].copy() for b in bands}
    for b in bands:
        c = b.cell
        moved = bool(b.trail) and b.trail[-1][0] > w.t - P.TICKS_PER_YEAR
        w.still_years[b.id] = 0 if moved else w.still_years[b.id] + years
        sk = w.skill[b.id]
        # pressure (Ben, 14 November 2026; docs/FARMING_TRIGGER_PROPOSAL.md): the larger of hunger (food margin, as in
        # M2) and crowding against the wild food the land gives unaided (Weitzel & Codding 2016), so gear and stores
        # feed people without hiding the crowding beneath
        hunger = float(np.clip((P.PRESSURE_MARGIN - b.margin) / 0.6, 0, 1))
        cr = float(crowd[b.cell])
        crowded = float(np.clip((cr - P.CROWD_START) / P.CROWD_RANGE, 0, 1))
        pressure = max(hunger, crowded)
        w._press_why[b.id] = (hunger, cr, crowded)
        settled = w.still_years[b.id] >= P.ABUNDANCE_YEARS
        share = w.farm_share[b.id]
        for k in range(len(SPECIES)):
            here = wild[c, k] or (sk[k] >= 3 and suit[c, k] > 0)
            if not here:
                continue
            # abundance (niche construction; Zeder 2012): a people settled on land rich in this wild species may tend
            # and sow it without pressure, at a small floor of pressure
            rich = settled and wild[c, k] and suit[c, k] >= P.ABUNDANCE_SUIT
            press_k = max(pressure, P.ABUNDANCE_FLOOR if rich else 0.0)
            if sk[k] < 1:
                if wild[c, k] and w.still_years[b.id] >= P.TEND_STILL_YEARS and press_k > 0:
                    if sk[k] > 0:
                        sk[k] = min(1.0, sk[k] + P.TEND_RATE * press_k * suit[c, k])
                    elif rng.random() < P.TEND_START * press_k * suit[c, k]:
                        # beginning to tend a wild plant or herd is a rare idea, not a certainty
                        sk[k] = P.TEND_RATE * press_k * suit[c, k]
            elif sk[k] < 2:
                if sk[k] == 1.0:
                    # the step from tending to deliberate sowing is another rare idea
                    if rng.random() < P.CULTIVATE_START * max(share, press_k) * max(suit[c, k], 0.1):
                        sk[k] = 1.0 + 1e-3
                else:
                    # deliberate sowing grows with how much a people farms, or how pressed it is for food
                    sk[k] = min(2.0, sk[k] + P.CULTIVATE_RATE * max(share, press_k))
            elif sk[k] < 3:
                sk[k] = min(3.0, sk[k] + P.DOMESTICATE_RATE * max(share, press_k))
        # learning from neighbours who know more about something that can live here
        if rng.random() < P.LEARN_CHANCE:
            near = [o for cc in r2[c] for o in by_cell.get(int(cc), ()) if o.id != b.id]
            if near:
                o = near[int(rng.integers(len(near)))]
                ok = wild[c] | ((old[o.id] >= 3) & (suit[c] > 0))
                gain = np.where(ok & (old[o.id] > sk), old[o.id] - sk, 0.0)
                if gain.any():
                    sk += (P.LEARN_SHARE * gain).astype(sk.dtype)
                    sk[(old[o.id] >= 3) & ok & (sk >= 2.9)] = 3.0
    # firsts in the world, with their causes
    for b in bands:
        for k in np.nonzero(w.skill[b.id] != old[b.id])[0]:
            for stage, thr in (("tending", 1e-9), ("cultivation", 1.0 + 1e-4), ("domestication", 3.0)):
                if old[b.id][k] < thr <= w.skill[b.id][k] or (thr < 1e-6 and old[b.id][k] == 0 < w.skill[b.id][k]):
                    _first(w, b, k, stage)
    # work choice: compare food per day of work
    bid = np.array([b.id for b in bands])
    KP, VP, KA, VA = best_all(w, bid, np.array([b.cell for b in bands]))
    from . import technology
    technology.refresh(w)                            # domestication skills changed above (Codex review 010, finding 4)
    _cw, _cf, _hw, _hf = technology.farm_multipliers(w, bid, np.array([b.cell for b in bands]))
    _ap = VA / np.maximum(VP + VA, 1e-9)             # the same mixture as the harvest (review 010, finding 3)
    from . import land
    _bc = np.array([b.cell for b in bands])
    _cfac = land.crop_factor(w, _bc) if getattr(P, "REAL_YIELDS", True) else 1.0
    TPW = _cw * (1 - _ap) * _cfac + _hw * _ap         # worn or salted soil pays less (M4a land)
    real = _real_rr(w, bid, _bc)
    real_lost = _real_rr(w, bid, _bc, lost=True)
    for n, b in enumerate(bands):
        kp, vp, ka, va = int(KP[n]), float(VP[n]), int(KA[n]), float(VA[n])
        v = max(vp, va)
        if v <= 0:
            target = 0.0
            w.farm_share[b.id] = 0.0                 # nothing here can be farmed: back to foraging at once
        else:
            farm_rr = P.FARM_RATE * v * P.FARM_RISK * float(TPW[n])
            if np.isfinite(real[n]):
                # farmers judge by what their fields and herds actually gave, when that is less: fallow and full
                # fields cap it (Ben, 19 November 2026: choices see real yields; Codex review 020)
                farm_rr = min(farm_rr, P.FARM_RISK * float(real[n]))
            ratio = farm_rr / max(w.forage_rr[b.id], 1e-6)
            target = float(np.clip((ratio - 0.8) / 0.6, 0, 1))
        s = w.farm_share[b.id]
        w.farm_share[b.id] = s + P.FARM_INERTIA * (target - s)
        if w.farm_share[b.id] < 0.01:
            w.farm_share[b.id] = 0.0
            if getattr(w, "farm_rr_real", None) is not None:
                w.farm_rr_real[b.id] = np.nan          # no longer observed (Codex review 021, finding 2)
        if b.village and w.farm_share[b.id] < 0.5 and v > 0:
            _land_abandoned(w, b, n, v, float(TPW[n]), float(_cw[n] * (1 - _ap[n]) + _hw[n] * _ap[n]), real[n],
                            real_lost[n], s)
        # villages: living mainly from farming, staying put
        if w.farm_share[b.id] >= 0.5:
            b.farm_years += 1
            if not b.village:
                b.village = True
                b.village_since = w.t
                if b.farming_since < 0:
                    b.farming_since = w.t
        else:
            b.farm_years = 0
            b.village = False
        if w.first_village is None and b.farm_years >= P.FIRST_VILLAGE_YEARS:
            _first_village(w, b, kp if vp >= va else ka)


def _land_abandoned(w, b, n, v, tpw, tpw_natural, real, real_lost, s):
    """A village that stops living mainly from farming because its soil is worn or salted (Codex review 021,
    finding 5: soil reaches migration through the farming choice, not through wild food). Recorded only if, with
    the soil's yield restored, the same choice would have kept it a village."""
    from . import land
    if not getattr(P, "LAND", False) or getattr(w, "land_flags", None) is None:
        return
    j = [land.KINDS.index("soil"), land.KINDS.index("salt")]
    events = [int(w.land_event[b.cell, k]) for k in j if w.land_flags[b.cell, k] and w.land_event[b.cell, k] >= 0]
    if not events or tpw >= tpw_natural:
        return
    farm_rr = P.FARM_RATE * v * P.FARM_RISK * tpw_natural
    if np.isfinite(real):
        # the realised return with what the soil took from the crops given back, on the same terms (the same effort,
        # room and seasons): the herds' part is not scaled (Codex review 022, finding 4)
        farm_rr = min(farm_rr, P.FARM_RISK * (float(real) + (float(real_lost) if np.isfinite(real_lost) else 0.0)))
    ratio = farm_rr / max(w.forage_rr[b.id], 1e-6)
    target = float(np.clip((ratio - 0.8) / 0.6, 0, 1))
    if s + P.FARM_INERTIA * (target - s) < 0.5:
        return
    cf = float(land.crop_factor(w, np.array([b.cell]))[0])
    note = (f"{w.band_name(b)} turned from its fields: they gave {cf:.0%} of what fresh soil gives; with fresh soil it "
            f"would have kept farming")
    w.event("land_abandoned", cell=b.cell, band=b.id, causes=[{"note": note}] + [{"event": e} for e in events])


def _real_rr(w, ids, cells=None, lost=False) -> np.ndarray:
    """The realised farming return per worker-day, where it was earned on the band's present cell; unobserved (NaN)
    elsewhere, so a band that moved, or gave up farming, judges new land by expectation (Codex review 021,
    finding 2)."""
    if not getattr(P, "LAND", False) or not getattr(P, "REAL_YIELDS", True) or getattr(w, "farm_rr_real", None) is None:
        return np.full(len(ids), np.nan)
    if len(w.farm_rr_real) <= int(np.max(ids, initial=0)):
        ensure(w, int(np.max(ids)), -1)
    if lost and (getattr(w, "farm_rr_lost", None) is None or len(w.farm_rr_lost) != len(w.farm_rr_real)):
        w.farm_rr_lost = np.zeros(len(w.farm_rr_real))
    r = (w.farm_rr_lost if lost else w.farm_rr_real)[ids].copy()
    if lost:
        r[~np.isfinite(w.farm_rr_real[ids])] = np.nan
    if cells is not None:
        r[w.farm_rr_cell[ids] != np.asarray(cells)] = np.nan
    return r


def crowding(w, bands=None) -> np.ndarray:
    """Per cell: people on it and its neighbours over the wild food capacity of those cells (the people the land
    feeds unaided, before gear or stores)."""
    pl = w.planet
    bands = w.living_bands() if bands is None else bands
    sizes = w.band_sizes()
    pop = np.zeros(pl.n)
    if bands:
        np.add.at(pop, np.array([b.cell for b in bands]), np.array([sizes[b.id] for b in bands]))
    nb = pl.grid.neighbours
    valid = nb >= 0
    idx = np.where(valid, nb, 0)
    around_pop = pop + np.where(valid, pop[idx], 0.0).sum(axis=1)
    cap = pl.capacity
    around_cap = cap + np.where(valid, cap[idx], 0.0).sum(axis=1)
    return around_pop / np.maximum(around_cap, 1e-9)


def _first(w, b, k, stage):
    f = w.farm_firsts.setdefault(SPECIES[k], {})
    if stage in f:
        return
    causes = []
    if stage == "tending":
        hunger, cr, crowded = getattr(w, "_press_why", {}).get(b.id, (0.0, 0.0, 0.0))
        wild, suit = land_tables(w)
        rich = (w.still_years[b.id] >= P.ABUNDANCE_YEARS and wild[b.cell, k] and suit[b.cell, k] >= P.ABUNDANCE_SUIT)
        if rich and P.ABUNDANCE_FLOOR > max(hunger, crowded):     # the floor, not the pressure, set the chance (review 011)
            why = (f"settled {int(w.still_years[b.id])} years on land rich in wild {NAMES[SPECIES[k]]}, it began to "
                   f"tend it without being pressed for food")
        elif crowded >= hunger:
            why = (f"{cr:.2f} people per unit of the wild food the land gives unaided were living within reach "
                   f"(crowded against wild food)")
        else:
            why = f"it gathered {b.margin:.2f} times its food needs (pressed for food)"
        causes.append({"note": f"{w.band_name(b)} had stayed in one area for {int(w.still_years[b.id])} years where "
                               f"wild {NAMES[SPECIES[k]]} grew; " + why})
    else:
        prev = {"cultivation": "tending", "domestication": "cultivation"}[stage]
        if prev in f:
            causes.append({"event": f[prev]})
        causes.append({"note": f"years of {prev} by {w.band_name(b)} and the peoples it learned from"})
    f[stage] = w.event(f"first_{stage}", cell=b.cell, band=b.id, causes=causes, species=NAMES[SPECIES[k]])
    w.counts[f"first_{stage}"] = w.counts.get(f"first_{stage}", 0) + 1


def _first_village(w, b, k):
    f = w.farm_firsts.get(SPECIES[k], {})
    causes = [{"event": f[s]} for s in ("domestication", "cultivation") if s in f][:1]
    causes.append({"note": f"{w.band_name(b)} had lived mainly from {NAMES[SPECIES[k]]} for "
                           f"{b.farm_years} years without moving"})
    w.first_village = w.event("first_farming_village", cell=b.cell, band=b.id, causes=causes,
                              species=NAMES[SPECIES[k]], year=w.year)


def season_food_live(w, ids, cells, effort):
    """As season_food, on compact arrays (one entry per living band, aligned with ids)."""
    forage_eff = effort.copy()
    L = len(ids)
    food = np.zeros(L)
    share = w.farm_share[ids]
    if not share.any():
        from . import land
        land.note_crop_loss(w, ids, np.zeros(L))       # the harvest still turns the year (Codex review 022, finding 3)
        if w.quarter == P.HARVEST_QUARTER:             # ... and crops already grown are still brought in (review 023)
            food = w.crop_store[ids].copy()
            w.crop_store[ids] = 0.0
            w.ledger["farmed"] = w.ledger.get("farmed", 0.0) + float(food.sum())
        return forage_eff, food
    _, suit = land_tables(w)
    farm_eff = effort * share
    forage_eff = effort - farm_eff
    vals = np.zeros(L)
    caps = np.zeros(L)
    animal_part = np.zeros(L)
    on = share > 0
    fid, fcell = ids[on], cells[on]
    kp, vp, ka, va = best_all(w, fid, fcell)
    vals[on] = np.maximum(vp, va)
    animal_part[on] = va / np.maximum(vp + va, 1e-9)
    # the room a band's farming has is sized by the crops and animals it can actually use there, not by one it has
    # never domesticated (Ben, 20 November 2026, after Codex review 021, finding 3)
    caps[on] = P.FARM_CAPACITY * np.maximum(suit[fcell, kp] * (vp > 0), suit[fcell, ka] * (va > 0)) * P.SEASON_DAYS
    crop_caps = np.zeros(L)
    crop_caps[on] = P.FARM_CAPACITY * suit[fcell, kp] * (vp > 0) * P.SEASON_DAYS
    cell_eff = np.zeros(w.planet.n)
    np.add.at(cell_eff, cells, farm_eff)
    land_share = np.where(cell_eff[cells] > 0, farm_eff / np.maximum(cell_eff[cells], 1e-12), 0.0)
    from . import technology
    cw, cf, hw_, hf = technology.farm_multipliers(w, ids, cells)       # M4a: crops and herds separately (review 010)
    base = farm_eff / P.FORAGE_RATE * P.FARM_RATE * vals
    room = caps * land_share
    from . import land
    herd = np.minimum(base * animal_part * hw_, room * animal_part * hf)
    rest = land.cropped_share(w, cells)                 # land resting in fallow grows nothing this year (M4a land)
    # crops grow only on crop land: a herd's larger pasture does not enlarge the fields (Codex review 022, finding 1)
    crop_room = crop_caps * land_share
    crop = np.minimum(base * (1 - animal_part) * cw, crop_room * (1 - animal_part) * cf * rest)
    # the share of the cell's farmland each band works for crops, before fertility and salt (Codex review 020), and
    # the share it would have worked with no land resting (fallow gives way to need; Ben, 19 November 2026)
    # measured against the cell's crop capacity, not a pasture capacity (Codex review 021, finding 3)
    worked = np.where(crop_caps * cf > 0, crop / np.maximum(crop_caps * cf, 1e-12), 0.0)
    wanted = np.minimum(base * (1 - animal_part) * cw, crop_room * (1 - animal_part) * cf)
    need = np.where(crop_caps * cf > 0, wanted / np.maximum(crop_caps * cf, 1e-12), 0.0)
    _cfac = land.crop_factor(w, cells)
    lost_crop = crop * (1.0 - _cfac)                    # what worn or salted soil took (the food account)
    crop = crop * _cfac                                 # worn or salted soil yields less (M4a land)
    if on.any():
        land.note_crops(w, ids[on], cells[on], worked[on], animal_part[on], need[on])
    land.note_crop_loss(w, ids, lost_crop, cells)
    grown = herd + crop
    if getattr(w, "farm_rr_real", None) is not None and on.any():
        # what fields and herds actually gave per worker-day this season (M4a land: choices see real yields)
        days = farm_eff[on] / P.FORAGE_RATE
        ok = days > 0
        if len(w.farm_rr_real) <= int(ids.max()):
            ensure(w, int(ids.max()), -1)
        oi = ids[on][ok]
        rr = grown[on][ok] / days[ok]
        prev = w.farm_rr_real[oi]
        here = cells[on][ok]
        same = np.isfinite(prev) & (w.farm_rr_cell[oi] == here)
        w.farm_rr_real[oi] = np.where(same, 0.9 * prev + 0.1 * rr, rr)
        if getattr(w, "farm_rr_lost", None) is None or len(w.farm_rr_lost) != len(w.farm_rr_real):
            w.farm_rr_lost = np.zeros(len(w.farm_rr_real))
        lr = lost_crop[on][ok] / days[ok]
        w.farm_rr_lost[oi] = np.where(same, 0.9 * w.farm_rr_lost[oi] + 0.1 * lr, lr)
        w.farm_rr_cell[oi] = here
    w.crop_store[ids] += crop
    food = herd
    if w.quarter == P.HARVEST_QUARTER:
        food = food + w.crop_store[ids]
        w.crop_store[ids] = 0.0
    w.ledger["farmed"] = w.ledger.get("farmed", 0.0) + float(food.sum())
    return forage_eff, food


def record_forage_return_live(w, ids, days, forage_food):
    rr = np.where(days > 0, forage_food / np.maximum(days, 1e-9) * P.FORAGE_RATE, w.forage_rr[ids])
    w.forage_rr[ids] = 0.9 * w.forage_rr[ids] + 0.1 * rr


def record_forage_return(w, ids, forage_eff, forage_food):
    """Remember food per worker-day from foraging (slowly), for next year's choice."""
    days = forage_eff[ids]
    # effort is worker-days x FORAGE_RATE, so food / effort x FORAGE_RATE is food per worker-day
    rr = np.where(days > 0, forage_food[ids] / np.maximum(days, 1e-9) * P.FORAGE_RATE, w.forage_rr[ids])
    w.forage_rr[ids] = 0.9 * w.forage_rr[ids] + 0.1 * rr


def to_json(w):
    return {"first_village": w.first_village, "farm_firsts": w.farm_firsts}


def from_json(w, d):
    w.first_village = d.get("first_village")
    w.farm_firsts = d.get("farm_firsts", {})
