"""Pastoralism (M4a; M4 specification section 2, item 3; Ben's decision 4, 12 November 2026).

A people living mainly from herds, in land where its crops do poorly, does not stay put: it moves its herds to
better pasture, season by season. Here a herding people is a band farming at least half its work, with at least
PASTORAL_SHARE of its farming value in animals at its current cell. Each season it compares pasture per person
here with the neighbouring land cells (herding value x FARM_CAPACITY, shared with everyone farming there) and
moves if a neighbour is at least PASTORAL_MOVE times better. No random numbers are drawn: the order is the order
of living bands, and ties go to the lower cell number.

The year's standing crop (crop_store) travels with a moving band and is harvested wherever it is at harvest: an
accepted abstraction for now (Ben, 13 November 2026); later, harvest only back on the sowing cell.

reads: bands, skill, farm_share, planet tables     writes: bands (cell, trail, last_move), herder_since, events
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from . import farming


def _animal_value(w, b, c, wild, suit):
    sk = w.skill[b.id]
    usable = (sk >= 3) | wild[c]
    val = np.where(usable, farming.quality(sk) * suit[c], 0.0)
    return float(val[farming.ANIMALS].max()), float(val[farming.PLANTS].max())


def is_herder(w, b, wild=None, suit=None) -> bool:
    """A herding people now: farming at least half its work, with at least PASTORAL_SHARE of its farming value in
    animals at its current cell. (herder_since only records that it once took up herding.)"""
    if w.farm_share[b.id] < 0.5:
        return False
    if wild is None:
        wild, suit = farming.land_tables(w)
    va, vp = _animal_value(w, b, b.cell, wild, suit)
    return va > 0 and va >= P.PASTORAL_SHARE * (va + vp)


def move(w):
    if not getattr(P, "PASTORALISM", False):
        return
    bands = w.living_bands()
    if not bands:
        return
    wild, suit = farming.land_tables(w)
    sizes = w.band_sizes()
    nb = w.planet.grid.neighbours
    land = w.planet.land
    farmers: dict = {}
    herders = []
    for b in bands:
        # everyone farming in a cell shares its land, in proportion to their farming work (as in season_food):
        # count people x farming share, not only bands farming at least half their work. (Until 13 November 2026
        # only the latter were counted, so a crowded cell could look empty: found by Codex, review 005)
        if w.farm_share[b.id] > 0:
            farmers[b.cell] = farmers.get(b.cell, 0.0) + float(sizes[b.id]) * float(w.farm_share[b.id])
    for b in bands:
        if w.farm_share[b.id] < 0.5:
            continue
        va, vp = _animal_value(w, b, b.cell, wild, suit)
        if va <= 0 or va < P.PASTORAL_SHARE * (va + vp):
            continue
        herders.append((b, va))
    for b, va in herders:
        n = float(sizes[b.id]) * float(w.farm_share[b.id])          # its farming work, in people
        if n <= 0:
            continue
        here = va * P.FARM_CAPACITY / max(farmers.get(b.cell, 0.0), 1.0)
        best, best_v, best_va = None, here * P.PASTORAL_MOVE, 0.0
        for c in nb[b.cell]:
            c = int(c)
            if c < 0 or not land[c]:
                continue
            vc, _ = _animal_value(w, b, c, wild, suit)
            if vc <= 0:
                continue
            v = vc * P.FARM_CAPACITY / (farmers.get(c, 0.0) + n)
            if v > best_v:
                best, best_v, best_va = c, v, vc
        if best is None:
            continue
        src = b.cell
        farmers[src] = farmers.get(src, 0.0) - n
        farmers[best] = farmers.get(best, 0.0) + n
        b.cell = best
        b.trail = (b.trail + [(w.t, best)])[-40:]
        b.last_move = (f"moved its herds to better pasture: {best_v / here:.1f} times the grazing per person "
                       f"of the area it left")
        w.reveal_pending.add(b.id)
        if w.herder_since[b.id] < 0:
            w.herder_since[b.id] = w.t
            w.event("took_up_herding", cell=best, band=b.id, origin=src,
                    causes=[{"note": f"{w.band_name(b)} lived mainly from its herds ({va / max(va + _animal_value(w, b, src, wild, suit)[1], 1e-9):.0%} "
                                     f"of what its farming could yield where it was), and the pasture of a "
                                     f"neighbouring area offered {best_v / here:.1f} times as much per person"}])
            if getattr(w, "first_herders", None) is None:
                w.first_herders = len(w.events) - 1
