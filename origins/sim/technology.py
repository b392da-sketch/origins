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
    if t.materials:
        near = materials_near(w, b.cell) if near is None else near
        for group in t.materials:
            if not any(m in near for m in group):
                missing.append("needs " + " or ".join(group) + " within reach")
    return (not missing), missing
