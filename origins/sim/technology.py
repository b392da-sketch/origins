"""The technology network (M4a; M4 specification section 3). Stage 1: techniques as data, held per band.

A technique is a piece of knowledge a people can hold. Each has:
- prerequisites: other techniques, domesticated plants or animals, materials within reach, and enough people
  practising it to keep it alive;
- an effect on a system that already exists (wired in stage 5; listed here so the record says what each is for);
- what kind of need presses towards it (used by invention, stage 2).

Held per band, as a skill level from 0 (unknown) to 1 (the best known): w.tech[band, k]. A daughter band starts
with her mother's techniques (stage 1). Invention, keeping and losing, and spread come in stages 2-4.

There is no timetable: nothing here says when a technique should appear. The real sequences are the starting
point for prerequisites only (for example, kilns before smelting: Roberts, Thornton & Pigott 2009; tallies and
tokens before writing: Schmandt-Besserat 1992).

reads: (stage 1) nothing each season     writes: w.tech (on band creation)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Technique:
    key: str
    name: str
    group: str
    needs: tuple = ()                 # techniques that must be held (at a working level)
    domesticated: tuple = ()          # "plant" and/or "animal": a domesticated species of that kind must be held
    materials: tuple = ()             # any-of groups: each inner tuple needs one of its materials within reach
    keep: int = 10                    # practitioners needed to keep the skill alive (stage 3; starting values)
    need: str = ""                    # the pressure that leads towards it (stage 2)
    effect: str = ""                  # what it changes (stage 5)


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
    # farming
    T("terracing", "terraced fields", "farming", domesticated=("plant",), keep=30, need="crowding",
      effect="farming capacity rises on hilly land"),
    T("irrigation", "irrigation", "farming", domesticated=("plant",), keep=50, need="crowding",
      effect="crop yields rise on river and dry land; salting can follow (section 5)"),
    T("manuring", "manuring and fallow", "farming", domesticated=("plant", "animal"), keep=20, need="crowding",
      effect="soil keeps its fertility (section 5)"),
    T("draft_animals", "draft animals", "farming", domesticated=("animal",), keep=30, need="crowding",
      effect="more land per household (with the plough)"),
    T("plough", "the plough", "farming", needs=("draft_animals",), domesticated=("plant",), keep=40, need="crowding",
      effect="more land per household: advantage compounds (Kohler et al. 2017)"),
    T("milking", "milking", "farming", domesticated=("animal",), keep=20, need="hunger",
      effect="herds yield more food while alive"),
    T("wool", "wool and weaving", "farming", needs=("cordage",), domesticated=("animal",), keep=30, need="trade",
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
    T("pack_animals", "pack animals", "moving", domesticated=("animal",), keep=20, need="trade",
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


def _check():
    for t in TECHNIQUES:
        for n in t.needs:
            assert n in INDEX and INDEX[n] < INDEX[t.key], f"{t.key} needs {n}, which must be listed before it"
        for group in t.materials:
            for m in group:
                assert m in MATERIALS, m


_check()


def init(w):
    w.tech = np.zeros((64, K), dtype=np.float32)


def ensure(w, band_id: int, parent: int):
    if not hasattr(w, "tech"):
        init(w)
    if band_id >= len(w.tech):
        cap = len(w.tech)
        while cap <= band_id:
            cap *= 2
        a = np.zeros((cap, K), dtype=np.float32)
        a[:len(w.tech)] = w.tech
        w.tech = a
    w.tech[band_id] = w.tech[parent] if parent >= 0 else 0.0      # a daughter knows what her mother knew


def materials_near(w, cell: int) -> set:
    """Materials within two rings of a cell (forest from the biomes; the rest from world generation)."""
    from .language import ring2
    pl = w.planet
    cells = [int(c) for c in ring2(w)[cell] if c >= 0]
    found = set()
    from ..worldgen import BIOMES
    forest = {BIOMES.index(b) for b in ("boreal_forest", "temperate_forest", "tropical_forest")}
    for c in cells:
        if int(pl.biome[c]) in forest:
            found.add("forest")
        for m, arr in pl.minerals.items():
            if arr[c]:
                found.add(m)
    return found


def held(w, band_id: int, key: str, level: float = 0.5) -> bool:
    return bool(w.tech[band_id, INDEX[key]] >= level)


def prerequisites_met(w, b, t: Technique, near: set | None = None) -> tuple[bool, list]:
    """Whether a band could hold technique t now, and what is missing (for causes)."""
    missing = []
    for n in t.needs:
        if not held(w, b.id, n):
            missing.append(f"needs {TECHNIQUES[INDEX[n]].name}")
    if t.domesticated:
        from . import farming
        sk = w.skill[b.id]
        if "plant" in t.domesticated and not (sk[farming.PLANTS] >= 3).any():
            missing.append("needs a domesticated crop")
        if "animal" in t.domesticated and not (sk[farming.ANIMALS] >= 3).any():
            missing.append("needs a domesticated animal")
        if float(w.farm_share[b.id]) < P.TECH_FARMING:
            missing.append("needs a people who farm or herd")
    if t.materials:
        near = materials_near(w, b.cell) if near is None else near
        for group in t.materials:
            if not any(m in near for m in group):
                missing.append("needs " + " or ".join(group) + " within reach")
    return (not missing), missing


# --- stage 2: invention ---------------------------------------------------------------------------------------------

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


def _possible(w, ids, cells) -> np.ndarray:
    """live x K: are a technique's prerequisites met (techniques, domesticates, materials)?"""
    from . import farming
    held_ = w.tech[ids] >= P.TECH_WORKING
    sk = w.skill[ids]
    # A farming technique needs a domesticate AND a band that lives partly by farming or herding: terraces and
    # ploughs are worked by farmers, not by foragers who happen to know a domesticate.
    farms = np.clip(w.farm_share[ids], 0, 1) >= P.TECH_FARMING
    plant = (sk[:, farming.PLANTS] >= 3).any(axis=1) & farms
    animal = (sk[:, farming.ANIMALS] >= 3).any(axis=1) & farms
    mats = _cell_materials(w)[cells]
    ok = np.ones((len(ids), K), dtype=bool)
    for k, t in enumerate(TECHNIQUES):
        for n in t.needs:
            ok[:, k] &= held_[:, INDEX[n]]
        if "plant" in t.domesticated:
            ok[:, k] &= plant
        if "animal" in t.domesticated:
            ok[:, k] &= animal
        for group in t.materials:
            ok[:, k] &= mats[:, [MATERIALS.index(x) for x in group]].any(axis=1)
    return ok


def _needs(w, live, ids, cells, sizes, cell_pop) -> dict:
    """The pressures behind invention, each 0..1 per band, measured from what the simulation already computes."""
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


def yearly(w):
    """Invention: each band, for each technique it could hold but does not, invents it with chance
    TECH_INVENT x (TECH_NEED_FLOOR + need) x (connected people / TECH_POP_REF) ** TECH_POP_EXPONENT
    x (TECH_EASY_KEEP / keep) ** TECH_DIFFICULTY: harder techniques (more practitioners needed) are rarer inventions.

    Connected people are everyone within two rings of the band's cell (contact; Henrich 2004; Kline & Boyd 2010).
    TECH_POP_EXPONENT 0 is the knock-out with no population effect (M4 specification section 3.2, check 6)."""
    if not getattr(P, "TECHNOLOGY", False):
        return
    live = w.living_bands()
    if not live:
        return
    from .language import ring2
    ids, _pos = w.live_index()
    ids = np.asarray(ids)
    sizes = np.asarray(w.live_sizes(), dtype=float)
    cells = np.array([b.cell for b in live])
    cell_pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
    r2 = ring2(w)
    connected = np.array([cell_pop[[int(x) for x in r2[c] if x >= 0]].sum() for c in cells])
    possible_all = _possible(w, ids, cells)
    possible = possible_all & (w.tech[ids] < P.TECH_WORKING)
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
        why = (f"{w.band_name(b)} invented {t.name}, under pressure of {t.need} ({top:.0%}), "
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
    keep_and_spread(w, live, ids, cells, sizes, connected, possible_all, need)


from .. import params as P  # noqa: E402  (after the data, which does not depend on parameters)


# --- stages 3 and 4: keeping, losing and spreading knowledge -------------------------------------------------------

def _reach(w, cells, values):
    """For each band's cell, the sum of `values` (cells x K) over the cells within two rings."""
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
    out = np.zeros((len(uc), values.shape[1]))
    for j, c in enumerate(uc.tolist()):
        out[j] = values[idx[off[c]:off[c + 1]]].sum(axis=0)
    return out[inv]


def keep_and_spread(w, live, ids, cells, sizes, connected, possible_all, need=None):
    """Stage 3 (keeping and losing; Henrich 2004): each held technique's skill level drifts each year with
    TECH_LEARN x ln(skilled people within reach / keep). With many skilled people within reach, some learners
    surpass their teachers and the level rises towards 1; with few, imperfect copying wears it down. Below
    TECH_LOST the technique is lost, with its cause recorded. Contact counts: skilled neighbours keep a skill alive.

    Stage 4 (spreading): a band that could hold a technique (prerequisites met) and has skilled people within
    reach adopts it with chance TECH_SPREAD x (skilled people within reach / everyone within reach)
    x (TECH_NEED_FLOOR + need): a technique is taken up faster where it answers a pressing need (relative advantage;
    Rogers 2003; Henrich 2001). It starts at TECH_ADOPT_LEVEL, and the adoption is recorded with where it came from."""
    rng = w.rng["technology"]
    lvl = w.tech[ids].astype(float)
    held_ = lvl >= P.TECH_WORKING
    n_cells = w.planet.n
    skilled_cell = np.zeros((n_cells, K))
    np.add.at(skilled_cell, cells, held_ * sizes[:, None])
    skilled = _reach(w, cells, skilled_cell)                         # skilled people within reach, per technique
    keep = np.array([t.keep for t in TECHNIQUES], dtype=float)
    # stage 3
    known = lvl > 0
    drift = P.TECH_LEARN * np.log(np.maximum(skilled, 1.0) / keep[None, :])
    new = np.where(known, np.clip(lvl + drift, 0.0, 1.0), lvl)
    lost = known & (new < P.TECH_LOST)
    new[lost] = 0.0
    for i, k in np.argwhere(lost).tolist():
        b = live[i]
        t = TECHNIQUES[k]
        why = (f"{w.band_name(b)} lost {t.name}: only {skilled[i, k]:,.0f} people within reach practised it, "
               f"fewer than the {t.keep} it takes to keep it alive, so each generation learned it less well")
        w.event("technique_lost", cell=b.cell, band=b.id, technique=t.key, causes=[{"note": why}],
                skilled=int(skilled[i, k]))
    # stage 4
    can = possible_all & (new < P.TECH_WORKING) & (skilled > 0)
    share = skilled / np.maximum(connected[:, None], 1.0)
    chance = P.TECH_SPREAD * np.clip(share, 0, 1)
    if need is not None:
        chance = chance * (P.TECH_NEED_FLOOR + need)
    draw = rng.random(chance.shape)
    adopt = can & (draw < chance)
    for i, k in np.argwhere(adopt).tolist():
        b = live[i]
        t = TECHNIQUES[k]
        new[i, k] = max(new[i, k], P.TECH_ADOPT_LEVEL)
        src = _source(w, live, cells, held_[:, k], b.cell)
        why = (f"{w.band_name(b)} learned {t.name} from neighbours: {skilled[i, k]:,.0f} of the "
               f"{connected[i]:,.0f} people within reach practised it")
        causes = [{"note": why}]
        if src is not None:
            causes.insert(0, {"band": src})
        w.event("technique_adopted", cell=b.cell, band=b.id, technique=t.key, causes=causes, source=src)
    w.tech[ids] = new.astype(np.float32)


def _source(w, live, cells, held_k, cell):
    """A band within reach that holds the technique (the nearest, lowest id): where it came from."""
    from .language import ring2
    near = set(int(x) for x in ring2(w)[cell] if x >= 0)
    for i in np.nonzero(held_k)[0].tolist():
        if int(cells[i]) in near:
            return live[i].id
    return None
