"""The technology network (M4a; M4 specification section 3).

A technique is a piece of knowledge a people can hold. Each has:
- prerequisites: other techniques held well, domesticated crops or particular animals, a people that farms,
  materials within reach, the right land, and enough people practising it to keep it alive;
- an effect on a system that already exists (wired in stage 5; listed here so the record says what each is for);
- what kind of need presses towards it.

Held per band as a quality from 0 (unknown) to 1 (the best known): w.tech[band, k]. A daughter band starts with her
mother's techniques and records.

- Invention (stage 2) is rare and gives a crude technique (TECH_INVENT_LEVEL).
- Keeping (stage 3; Henrich 2004): a technique is PRACTISED when its prerequisites are met. Practised, its quality
  drifts with ln(skilled practitioners within reach / people it needs): practitioners are TECH_PRACTISE_SHARE of
  the adults plus the specialists. Above the line it improves, but only slowly (at most TECH_REFINE a year, less for
  harder techniques, and less the nearer it is to mastery: Mesoudi 2011), and a people also closes part of the gap to the best
  practitioner within reach (TECH_CATCHUP). Below the line, imperfect copying wears it down. A technique that is
  REMEMBERED but not practised (its prerequisites gone) fades by TECH_FORGET a year. Below TECH_LOST it is lost.
- Teaching (Ben, 14 November 2026): specialists make copying more faithful (fewer people needed, faster
  refinement); writing slows decline and keeps records, from which a lost technique can rarely be recovered, crude.
- Spreading (stage 4): learners start at a share of their teacher's quality (TECH_ADOPT_SHARE), more readily from
  culturally close peoples (shared words, M1), and where the technique answers a need.
- Combining: people who join another band bring what they know, at a quality that depends on how many bring it.

There is no timetable: nothing here says when a technique should appear. The real sequences are the starting
point for prerequisites only (for example, kilns before smelting: Roberts, Thornton & Pigott 2009; tallies and
tokens before writing: Schmandt-Besserat 1992). All numbers are tunable starting values in params.py.

reads: bands (cell, size, language, store, last_ratio), farm_share, skill, spec, polity_of, planet tables
writes: w.tech, w.tech_record, w.tech_firsts, events (invention, technique_lost, technique_adopted,
        technique_recovered)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Technique:
    key: str
    name: str
    group: str
    needs: tuple = ()                 # techniques that must be held well (at TECH_WORKING) and practised
    crop: bool = False                # a domesticated crop must be held, by a people that farms
    animals: tuple = ()               # one of these domesticated animals must be held, by a people that farms or herds
    materials: tuple = ()             # any-of groups: each inner tuple needs one of its materials within reach
    terrain: str = ""                 # land the band's own cell must have: "hills" or "water" (river or lake)
    keep: int = 10                    # practitioners needed to keep the skill alive (starting values)
    need: str = ""                    # the pressure that leads towards it
    effect: str = ""                  # what it changes (stage 5)


ANY_ANIMAL = ("wild_goat", "wild_sheep", "wild_cattle", "wild_pig", "wild_horse")
T = Technique
TECHNIQUES: list[Technique] = [
    # foraging
    T("fire_hardening", "fire-hardened points", "foraging", keep=5, need="hunting",
      effect="hunting returns rise a little"),
    T("cordage", "cordage and nets", "foraging", keep=5, need="hunting",
      effect="small game, birds and fish yield more"),
    T("fish_traps", "fish traps and weirs", "foraging", needs=("cordage",), keep=10, need="hunger",
      effect="fishing yields rise where there is water"),
    T("bow", "the bow and arrow", "foraging", needs=("cordage",), keep=15, need="hunting",
      effect="hunting returns rise; later, war strength (M4b)"),
    T("canoes", "dugout canoes", "moving", materials=(("forest",),), keep=15, need="water",
      effect="sea crossings become more likely; fishing yields rise"),
    # containers
    T("baskets", "baskets", "containers", needs=("cordage",), keep=5, need="stores",
      effect="gathering and storage losses improve a little"),
    T("pottery", "pottery", "containers", materials=(("clay",),), keep=20, need="stores",
      effect="storage losses fall; cooked grain and pulses go further"),
    T("kilns", "kilns", "containers", needs=("pottery",), materials=(("clay",),), keep=30, need="stores",
      effect="better pottery; the heat that smelting needs"),
    # farming (animals per technique: Ben, 14 November 2026)
    T("terracing", "terraced fields", "farming", crop=True, terrain="hills", keep=30, need="crowding",
      effect="farming capacity rises on hilly land"),
    T("irrigation", "irrigation", "farming", crop=True, terrain="water", keep=50, need="crowding",
      effect="crop yields rise on river and dry land; salting can follow (section 5)"),
    T("manuring", "manuring and fallow", "farming", crop=True, animals=ANY_ANIMAL, keep=20, need="crowding",
      effect="soil keeps its fertility (section 5)"),
    T("draft_animals", "draft animals", "farming", animals=("wild_cattle", "wild_horse"), keep=30, need="crowding",
      effect="more land per household (with the plough)"),
    T("plough", "the plough", "farming", needs=("draft_animals",), crop=True, keep=40, need="crowding",
      effect="more land per household: advantage compounds (Kohler et al. 2017)"),
    T("milking", "milking", "farming", animals=("wild_goat", "wild_sheep", "wild_cattle", "wild_horse"), keep=20,
      need="hunger", effect="herds yield more food while alive"),
    T("wool", "wool and weaving", "farming", needs=("cordage",), animals=("wild_sheep",), keep=30, need="trade",
      effect="a good to trade (section 4)"),
    # building
    T("mud_brick", "mud-brick building", "building", materials=(("clay",),), keep=20, need="crowding",
      effect="lasting villages; storage improves"),
    T("stone_building", "stone building", "building", keep=40, need="power",
      effect="monuments and lasting seats"),
    T("fortification", "fortification", "building", needs=("mud_brick",), keep=40, need="war",
      effect="defence in war (M4b)"),
    # metals
    T("copper_working", "copper working", "metals", materials=(("copper",),), keep=30, need="trade",
      effect="tools and prestige goods"),
    T("smelting", "smelting", "metals", needs=("kilns", "copper_working"), materials=(("copper",), ("forest", "coal")),
      keep=50, need="trade", effect="metal from ore"),
    T("bronze", "bronze", "metals", needs=("smelting",), materials=(("copper",), ("tin",)), keep=80, need="war",
      effect="better tools and weapons; needs tin, often from far away (section 4)"),
    T("iron", "iron working", "metals", needs=("smelting",), materials=(("iron",), ("forest", "coal")), keep=80,
      need="war", effect="cheap tools and weapons (M4b)"),
    # moving
    T("sail", "sail", "moving", needs=("canoes", "cordage"), keep=40, need="trade",
      effect="longer sea crossings; sea trade"),
    T("pack_animals", "pack animals", "moving", animals=("wild_horse", "wild_cattle"), keep=20, need="trade",
      effect="trade over land carries more"),
    T("carts", "wheeled carts", "moving", needs=("draft_animals",), materials=(("forest",),), keep=40, need="trade",
      effect="trade over land carries much more"),
    # recording
    T("tallies", "tallies and tokens", "recording", keep=10, need="tribute",
      effect="accounts of stores and tribute"),
    T("writing", "writing", "recording", needs=("tallies",), keep=60, need="tribute",
      effect="officials' capacity rises; records outlast the people who made them (section 7)"),
]
KEYS = [t.key for t in TECHNIQUES]
INDEX = {k: i for i, k in enumerate(KEYS)}
K = len(TECHNIQUES)
MATERIALS = ("forest", "flint", "clay", "salt", "copper", "tin", "iron", "coal", "gold")
TERRAIN = ("hills", "water")
WRITING = INDEX["writing"]


def _check():
    from ..worldgen import DOMESTICABLES
    for t in TECHNIQUES:
        for n in t.needs:
            assert n in INDEX and INDEX[n] < INDEX[t.key], f"{t.key} needs {n}, which must be listed before it"
        for group in t.materials:
            for m in group:
                assert m in MATERIALS, m
        for a in t.animals:
            assert a in DOMESTICABLES, a
        assert not t.terrain or t.terrain in TERRAIN, t.terrain


_check()


def init(w):
    w.tech = np.zeros((64, K), dtype=np.float32)
    w.tech_record = np.zeros((64, K), dtype=np.float32)


def _grow(a, n):
    cap = len(a)
    while cap <= n:
        cap *= 2
    out = np.zeros((cap, K), dtype=np.float32)
    out[:len(a)] = a
    return out


def ensure(w, band_id: int, parent: int):
    if not hasattr(w, "tech"):
        init(w)
    if getattr(w, "tech_record", None) is None or w.tech_record.shape != w.tech.shape:
        rec = np.zeros_like(w.tech)
        old = getattr(w, "tech_record", None)
        if old is not None:
            n = min(len(old), len(rec))
            rec[:n] = old[:n]
        w.tech_record = rec
    if band_id >= len(w.tech):
        w.tech = _grow(w.tech, band_id)
        w.tech_record = _grow(w.tech_record, band_id)
    w.tech[band_id] = w.tech[parent] if parent >= 0 else 0.0            # a daughter knows what her mother knew
    w.tech_record[band_id] = w.tech_record[parent] if parent >= 0 else 0.0   # and keeps her records


def held(w, band_id: int, key: str, level: float | None = None) -> bool:
    """Held well enough to build on (TECH_WORKING unless another level is asked for; the same test as _possible:
    Codex review 008, finding 4)."""
    return bool(w.tech[band_id, INDEX[key]] >= (P.TECH_WORKING if level is None else level))


def materials_near(w, cell: int) -> set:
    """Materials within two rings of a cell (forest from the biomes; the rest from world generation)."""
    m = _cell_materials(w)[cell]
    return {MATERIALS[i] for i in np.nonzero(m)[0]}


def _species(names):
    from .farming import SPECIES
    return [SPECIES.index(n) for n in names]


def prerequisites_met(w, b, t: Technique, near: set | None = None) -> tuple[bool, list]:
    """Whether a band could practise technique t now, and what is missing (for causes)."""
    from . import farming
    missing = []
    for n in t.needs:      # a prerequisite counts only if held well AND practised (Ben, 14 November 2026)
        if not held(w, b.id, n):
            missing.append(f"needs {TECHNIQUES[INDEX[n]].name} held well")
        elif not prerequisites_met(w, b, TECHNIQUES[INDEX[n]], near)[0]:
            missing.append(f"needs {TECHNIQUES[INDEX[n]].name} practised")
    sk = w.skill[b.id]
    here = farming.land_tables(w)[1][b.cell] > 0                    # species that can live on this land
    farms = float(w.farm_share[b.id]) >= P.TECH_FARMING
    if t.crop and not ((sk[farming.PLANTS] >= 3) & here[farming.PLANTS]).any():
        missing.append("needs a domesticated crop that grows here")
    if t.animals and not ((sk[_species(t.animals)] >= 3) & here[_species(t.animals)]).any():
        missing.append("needs " + " or ".join(a.removeprefix("wild_") for a in t.animals)
                       + " domesticated, on land where they can live")
    if (t.crop or t.animals) and not farms:
        missing.append("needs a people who farm or herd")
    if t.materials:
        near = materials_near(w, b.cell) if near is None else near
        for group in t.materials:
            if not any(m in near for m in group):
                missing.append("needs " + " or ".join(group) + " within reach")
    if t.terrain and not _cell_terrain(w)[b.cell, TERRAIN.index(t.terrain)]:
        missing.append("needs hilly land" if t.terrain == "hills" else "needs a river or lake")
    return (not missing), missing


def _cell_materials(w) -> np.ndarray:
    """cells x materials: is each material within two rings? (cached on the planet; the planet does not change)"""
    pl = w.planet
    m = getattr(pl, "_tech_materials", None)
    if m is not None:
        return m
    from ..worldgen import BIOMES
    from .language import ring2
    here = np.zeros((pl.n, len(MATERIALS)), dtype=bool)
    forest = np.isin(pl.biome, [BIOMES.index(b) for b in ("boreal_forest", "temperate_forest", "tropical_forest")])
    here[:, MATERIALS.index("forest")] = forest
    for name, arr in pl.minerals.items():
        if name in MATERIALS:
            here[:, MATERIALS.index(name)] = arr
    r2 = ring2(w)
    m = np.zeros_like(here)
    for c in range(pl.n):
        idx = [int(x) for x in r2[c] if x >= 0]
        m[c] = here[idx].any(axis=0)
    pl._tech_materials = m
    return m


def _cell_terrain(w) -> np.ndarray:
    """cells x TERRAIN, judged on the cell itself (cached): hills = relief to a neighbour of at least
    TECH_HILL_RELIEF metres; water = a river or lake in the cell."""
    pl = w.planet
    m = getattr(pl, "_tech_terrain", None)
    if m is not None:
        return m
    e = pl.elevation
    nb = pl.grid.neighbours
    relief = np.where(nb >= 0, np.abs(e[np.maximum(nb, 0)] - e[:, None]), 0.0).max(axis=1)
    m = np.stack([relief >= P.TECH_HILL_RELIEF, pl.river | pl.lake], axis=1)
    pl._tech_terrain = m
    return m


def _possible(w, ids, cells, lvl=None) -> np.ndarray:
    """live x K: could each band practise each technique now (prerequisites held well, domesticates, farming,
    materials, land)? lvl: technique levels to judge prerequisites by (default the current ones)."""
    from . import farming
    lvl = w.tech[ids] if lvl is None else lvl
    held_ = lvl >= P.TECH_WORKING
    here = farming.land_tables(w)[1][cells] > 0                     # species that can live on each band's land
    sk = (w.skill[ids] >= 3) & here                                   # domesticated AND able to live here (review 009)
    farms = np.clip(w.farm_share[ids], 0, 1) >= P.TECH_FARMING
    crop = sk[:, farming.PLANTS].any(axis=1)
    mats = _cell_materials(w)[cells]
    land = _cell_terrain(w)[cells]
    ok = np.ones((len(ids), K), dtype=bool)
    for k, t in enumerate(TECHNIQUES):
        for n in t.needs:                    # held well AND practised (prerequisites come earlier in the list)
            ok[:, k] &= held_[:, INDEX[n]] & ok[:, INDEX[n]]
        if t.crop:
            ok[:, k] &= crop
        if t.animals:
            ok[:, k] &= sk[:, _species(t.animals)].any(axis=1)
        if t.crop or t.animals:
            ok[:, k] &= farms
        for group in t.materials:
            ok[:, k] &= mats[:, [MATERIALS.index(x) for x in group]].any(axis=1)
        if t.terrain:
            ok[:, k] &= land[:, TERRAIN.index(t.terrain)]
    return ok


def _needs(w, live, ids, cells, sizes, cell_pop) -> dict:
    """The pressures behind invention and adoption, each 0..1 per band, from what the simulation already computes."""
    ratio = np.array([b.last_ratio for b in live], dtype=float)
    store = np.array([b.store for b in live], dtype=float)
    hunger = np.clip(1.0 - ratio, 0, 1)
    per_head = store / np.maximum(sizes, 1.0)
    stores = np.clip(1.0 - per_head / max(P.TECH_STORE_REF, 1e-9), 0, 1)
    cap = np.maximum(w.planet.capacity[cells], 1.0)
    crowding = np.clip(cell_pop[cells] / cap - 0.5, 0, 1)
    forager = 1.0 - np.clip(w.farm_share[ids], 0, 1)
    pl = w.planet
    water = (pl.coast[cells] | pl.lake[cells]).astype(float) if hasattr(pl, "coast") else np.zeros(len(ids))
    pol = w.polity_of[ids] >= 0 if hasattr(w, "polity_of") else np.zeros(len(ids), bool)
    tier = np.zeros(len(ids))
    for i, b in enumerate(live):
        if pol[i]:
            p = w.polities.get(int(w.polity_of[b.id]))
            tier[i] = (p.tier if p is not None else 0) / 3.0
    return {"hunting": forager * (0.5 + 0.5 * hunger), "hunger": hunger, "stores": np.maximum(stores, hunger),
            "crowding": crowding, "water": water, "trade": np.clip(pol * 0.5 + crowding, 0, 1),
            "power": tier, "tribute": tier, "war": np.clip(tier + crowding * 0.5, 0, 1)}


# --- stage 2: invention ---------------------------------------------------------------------------------------------

def yearly(w):
    """Invention: each band, for each technique it could practise but does not know, invents it with chance
    TECH_INVENT x (TECH_NEED_FLOOR + need) x (connected people / TECH_POP_REF) ** TECH_POP_EXPONENT
    x (TECH_EASY_KEEP / keep) ** TECH_DIFFICULTY: harder techniques (more practitioners needed) are rarer inventions.
    A new invention is crude (TECH_INVENT_LEVEL) and improves only with practice (keep_and_spread).

    Connected people are everyone within two rings of the band's cell (contact; Henrich 2004; Kline & Boyd 2010).
    TECH_POP_EXPONENT 0 is the knock-out with no population effect (M4 specification section 3.2, check 6)."""
    if not getattr(P, "TECHNOLOGY", False):
        return
    live = w.living_bands()
    if not live:
        return
    ids, _pos = w.live_index()
    ids = np.asarray(ids)
    sizes = np.asarray(w.live_sizes(), dtype=float)
    cells = np.array([b.cell for b in live])
    cell_pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
    connected = _reach(w, cells, cell_pop[:, None])[:, 0]
    possible = _possible(w, ids, cells) & (w.tech[ids] <= 0)
    needs = _needs(w, live, ids, cells, sizes, cell_pop)
    need = np.stack([needs[t.need] for t in TECHNIQUES], axis=1)
    pop = (connected / P.TECH_POP_REF) ** P.TECH_POP_EXPONENT
    hard = (P.TECH_EASY_KEEP / np.array([t.keep for t in TECHNIQUES], dtype=float)) ** P.TECH_DIFFICULTY
    chance = P.TECH_INVENT * (P.TECH_NEED_FLOOR + need) * pop[:, None] * hard[None, :]
    rng = w.rng["technology"]
    draw = rng.random(chance.shape)
    hits = np.argwhere(possible & (draw < chance))
    for i, k in hits.tolist():
        b = live[i]
        t = TECHNIQUES[k]
        w.tech[b.id, k] = P.TECH_INVENT_LEVEL
        top = needs[t.need][i]
        why = (f"{w.band_name(b)} invented {t.name}, crude at first, under pressure of {t.need} ({top:.0%}), "
               f"with {connected[i]:,.0f} people within reach")
        if t.materials:
            why += "; materials within reach: " + ", ".join(
                next(m for m in group if _cell_materials(w)[b.cell, MATERIALS.index(m)]) for group in t.materials)
        w.event("invention", cell=b.cell, band=b.id, technique=t.key, causes=[{"note": why}],
                need=t.need, pressure=round(float(top), 3), connected=int(connected[i]))
        firsts = w.tech_firsts if hasattr(w, "tech_firsts") else {}
        if t.key not in firsts:
            firsts[t.key] = len(w.events) - 1
            w.tech_firsts = firsts
    keep_and_spread(w, live, ids, cells, sizes, connected, need)


from .. import params as P  # noqa: E402  (after the data, which does not depend on parameters)


# --- stages 3 and 4: keeping, losing and spreading knowledge -------------------------------------------------------

def _ring_index(w, cells):
    """For the distinct cells in `cells`: the flattened cells within two rings of each, and the offsets."""
    from .language import ring2
    pl = w.planet
    flat = getattr(pl, "_ring2_flat", None)
    if flat is None:
        r2 = ring2(w)
        lens = np.array([sum(1 for x in r2[c] if x >= 0) for c in range(pl.n)])
        flat = (np.concatenate([[int(x) for x in r2[c] if x >= 0] for c in range(pl.n)]),
                np.concatenate([[0], np.cumsum(lens)]))
        pl._ring2_flat = flat
    idx, off = flat
    uc, inv = np.unique(cells, return_inverse=True)
    starts, ends = off[uc], off[uc + 1]
    take = np.concatenate([idx[s:e] for s, e in zip(starts.tolist(), ends.tolist())])
    seg = np.concatenate([[0], np.cumsum(ends - starts)[:-1]])
    return take, seg, inv


def _reach(w, cells, values, how="sum"):
    """For each band's cell, the sum (or maximum) of `values` (cells x columns) over the cells within two rings."""
    take, seg, inv = _ring_index(w, cells)
    v = values[take]
    out = np.maximum.reduceat(v, seg, axis=0) if how == "max" else np.add.reduceat(v, seg, axis=0)
    return out[inv]


def _adults(w, live, ids) -> np.ndarray:
    """Adults (15 to 59) per living band, people followed one by one plus group counts."""
    out = np.zeros(len(ids))
    idx = w.alive_idx()
    if len(idx):
        a = w.ages(idx)
        ad = idx[(a >= 15) & (a < 60)]
        out += np.bincount(w.people.band[ad], minlength=int(max(ids.max() + 1, 1)))[ids]
    G = getattr(w, "groups", None)
    if G is not None:
        for i, b in enumerate(live):
            if b.mode == "group" and b.group is not None and b.group >= 0:
                out[i] += float(G.F[b.group][15:60].sum() + G.M[b.group][15:60].sum())
    return out


def keep_and_spread(w, live, ids, cells, sizes, connected, need=None):
    """Stage 3: keeping, refining and losing (Henrich 2004), teaching (specialists and writing), recovery from
    records. Stage 4: spreading by contact. See the module docstring; each change of state is recorded."""
    rng = w.rng["technology"]
    n_cells = w.planet.n
    lvl = w.tech[ids].astype(float)
    keep = np.array([t.keep for t in TECHNIQUES], dtype=float)
    known = lvl > 0
    practised = known & _possible(w, ids, cells, lvl)
    # skilled practitioners, not everyone: a share of the adults, plus the specialists (Ben, 14 November 2026;
    # the Polar Inuit lost kayaks and bows when an epidemic carried off the knowledgeable adults: Boyd, Richerson
    # & Henrich 2011)
    spec = np.asarray(w.spec[ids], dtype=float) if hasattr(w, "spec") else np.zeros(len(ids))
    skilled_people = P.TECH_PRACTISE_SHARE * _adults(w, live, ids) + spec
    pract_cell = np.zeros((n_cells, K))
    np.add.at(pract_cell, cells, practised * skilled_people[:, None])
    practitioners = _reach(w, cells, pract_cell)                     # skilled practitioners within reach
    best_cell = np.zeros((n_cells, K))
    np.maximum.at(best_cell, cells, np.where(practised, lvl, 0.0))
    best = _reach(w, cells, best_cell, how="max")                      # the best practitioner within reach
    # teaching: specialists make copying more faithful (Ben, decision 2; craft specialists from M2's surplus)
    craft = np.clip(spec / np.maximum(sizes, 1.0) / P.TECH_CRAFT_REF, 0, 1)
    gain = 1.0 + P.TECH_CRAFT_GAIN * craft[:, None]
    drift = P.TECH_LEARN * np.log(np.maximum(practitioners, 1.0) * gain / keep[None, :])
    # refinement slows as a technique nears mastery: learning what is already known takes more of a life (Mesoudi
    # 2011), so the yearly gain shrinks with the distance still to go (Ben, 14 November 2026)
    cap = P.TECH_REFINE * np.sqrt(P.TECH_EASY_KEEP / keep)[None, :] * gain * np.clip(1.0 - lvl, 0.0, 1.0)
    # writing: records hold part of what is lost in copying, in proportion to writing's own quality
    wq = np.where(practised[:, WRITING], lvl[:, WRITING], 0.0)
    hold = 1.0 - P.TECH_WRITING_HOLD * wq[:, None]
    step = np.where(drift > 0, np.minimum(drift, cap), drift * hold)
    catch = P.TECH_CATCHUP * np.maximum(best - lvl, 0.0)
    new = np.where(practised, np.clip(lvl + step + catch, 0.0, 1.0), lvl)
    new = np.where(known & ~practised, lvl - P.TECH_FORGET, new)       # remembered, not practised: fades
    lost = known & (new < P.TECH_LOST)
    new[lost] = 0.0
    for i, k in np.argwhere(lost).tolist():
        b = live[i]
        t = TECHNIQUES[k]
        if practised[i, k]:
            why = (f"{w.band_name(b)} lost {t.name}: only {practitioners[i, k]:,.0f} skilled people within reach practised "
                   f"it, fewer than the {t.keep} it takes to keep it alive, so each generation learned it less well")
        else:
            _ok, missing = prerequisites_met(w, b, t)
            why = (f"{w.band_name(b)} forgot {t.name}: it was no longer practised ("
                   + "; ".join(missing or ["its conditions were gone"]) + ")")
        w.event("technique_lost", cell=b.cell, band=b.id, technique=t.key, causes=[{"note": why}],
                skilled=int(practitioners[i, k]), practised=bool(practised[i, k]), connected=int(connected[i]))
    # records: a people that writes keeps a record of what it practises; a lost technique can come back from it
    possible_now = _possible(w, ids, cells, new)
    # only a people that PRACTISES writing keeps records or reads them (Codex review 009, finding 1: remembered
    # writing still kept and used records)
    writes = (new[:, WRITING] >= P.TECH_WORKING) & possible_now[:, WRITING]
    rec = w.tech_record[ids].astype(float)
    rec = np.where(writes[:, None] & practised & (new > 0), np.maximum(rec, new), rec)
    w.tech[ids] = new.astype(np.float32)
    back = (new <= 0) & (rec > 0) & writes[:, None] & possible_now
    chance = P.TECH_RECOVER * new[:, WRITING][:, None]
    draw = rng.random(back.shape)
    for i, k in np.argwhere(back & (draw < chance)).tolist():
        b = live[i]
        t = TECHNIQUES[k]
        new[i, k] = P.TECH_INVENT_LEVEL
        why = f"{w.band_name(b)} recovered {t.name} from its records, crude at first, after it had been lost"
        w.event("technique_recovered", cell=b.cell, band=b.id, technique=t.key, causes=[{"note": why}])
    w.tech_record[ids] = rec.astype(np.float32)
    w.tech[ids] = new.astype(np.float32)
    # stage 4: teachers and prerequisites are judged after this year's keeping and losing, and a people never
    # learns from itself (Codex review 008, findings 2 and 3)
    practising_now = (new > 0) & possible_now
    teach_cell = np.zeros((n_cells, K))
    np.add.at(teach_cell, cells, practising_now * sizes[:, None])
    teachers = _reach(w, cells, teach_cell) - practising_now * sizes[:, None]
    can = possible_now & (new <= 0) & (teachers > 0.5)
    share = teachers / np.maximum(connected[:, None], 1.0)
    chance = P.TECH_SPREAD * np.clip(share, 0, 1)
    if need is not None:
        chance = chance * (P.TECH_NEED_FLOOR + need)
    draw = rng.random(chance.shape)
    hits = np.argwhere(can & (draw < chance)).tolist()
    if not hits:
        return
    from .language import ring2, shared_roots
    by_cell: dict[int, list] = {}
    for i, c in enumerate(cells.tolist()):
        by_cell.setdefault(c, []).append(i)
    r2 = ring2(w)
    for i, k in hits:
        b = live[i]
        t = TECHNIQUES[k]
        # a teacher, drawn in proportion to the practitioners each band has (so the expected closeness is the
        # practitioners' average); the lesson takes with chance = cultural closeness (M4 spec 3.4; Ben, decision 5)
        cand = [j for c in r2[b.cell] if c >= 0 for j in by_cell.get(int(c), ())
                if j != i and practising_now[j, k]]
        if not cand:
            continue
        wts = sizes[cand] / sizes[cand].sum()
        j = cand[int(rng.choice(len(cand), p=wts))]
        src = live[j]
        la, lb = w.languages.get(b.language), w.languages.get(src.language)
        same = shared_roots(la, lb) if (la is not None and lb is not None) else 1.0
        close = P.TECH_FOREIGN + (1.0 - P.TECH_FOREIGN) * same
        if rng.random() >= close:
            continue
        level = P.TECH_ADOPT_SHARE * float(new[j, k])                # learners fall short of their teacher
        if level < P.TECH_LOST:
            continue                                                  # too crude a lesson to take hold
        new[i, k] = level
        why = (f"{w.band_name(b)} learned {t.name} from {w.band_name(src)} ({same:.0%} of words shared); "
               f"{teachers[i, k]:,.0f} of the {connected[i]:,.0f} people within reach practised it")
        w.event("technique_adopted", cell=b.cell, band=b.id, technique=t.key,
                causes=[{"band": src.id}, {"note": why}], source=src.id, route="contact",
                level=round(level, 3), closeness=round(close, 3))
    w.tech[ids] = new.astype(np.float32)


def combine(w, src, dst, route: str, carriers: float | None = None):
    """People who join another band bring what they know (M4 specification section 3.4: migration and capture).
    The joined band holds each technique at the better of its own level and the level the newcomers carry; the
    newcomers carry their people's level in full only if they number at least the people the technique needs
    (Ben, decision 1; Henrich 2004). Records come with them. A technique the band did not know before is recorded
    as learned from src. (Codex review 008, finding 1: knowledge was erased when populations combined.)

    route: "combined" (two local populations of one land become one), "merge" (a remnant joins a neighbour),
    "migration" (people move into a neighbouring population), "capture" (captives taken in war)."""
    if not getattr(P, "TECHNOLOGY", False) or not hasattr(w, "tech"):
        return
    keep = np.array([t.keep for t in TECHNIQUES], dtype=float)
    a = w.tech[src.id].astype(float)
    if carriers is not None:
        a = a * np.clip(carriers / keep, 0.0, 1.0)
    a = np.where(a >= P.TECH_LOST, a, 0.0)                              # a fragment too small to take hold
    d = w.tech[dst.id].astype(float)
    gained = (a > 0) & (d <= 0)
    w.tech[dst.id] = np.maximum(a, d).astype(np.float32)
    if getattr(w, "tech_record", None) is not None:
        w.tech_record[dst.id] = np.maximum(w.tech_record[dst.id], w.tech_record[src.id])
    for k in np.nonzero(gained)[0].tolist():
        t = TECHNIQUES[k]
        how = {"combined": "combined with", "merge": "took in the remnant of", "marriage": "took in by marriage someone from",
               "capture": f"took {carriers:,.0f} captives from" if carriers else "took captives from"}.get(
            route, f"took in {carriers:,.0f} people from" if carriers else "took in people from")
        why = f"{w.band_name(dst)} {how} {w.band_name(src)}, who knew {t.name}"
        w.event("technique_adopted", cell=dst.cell, band=dst.id, technique=t.key,
                causes=[{"band": src.id}, {"note": why}], source=src.id, route=route, level=round(float(a[k]), 3))
