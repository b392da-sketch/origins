"""Observer interventions (god powers arrive later; M0 has only the food shock used by the gate).

Every intervention is logged as an event, marks the world as intervened, and
is cited as a cause by any death it contributes to.
"""
from __future__ import annotations

import numpy as np


def cells_within(w, centre: int, rings: int) -> np.ndarray:
    nb = w.planet.grid.neighbours
    cells = {int(centre)}
    frontier = {int(centre)}
    for _ in range(rings):
        nxt = set()
        for c in frontier:
            nxt.update(int(x) for x in nb[c] if x >= 0)
        nxt -= cells
        cells |= nxt
        frontier = nxt
    return np.array(sorted(cells))


def food_shock(w, cells: np.ndarray, factor: float, seasons: int, why: str) -> int:
    eid = w.event("intervention", cell=int(cells[0]), causes=[{"note": why}],
                  what=f"wild food reduced to {factor:.0%} for {seasons} seasons in {len(cells)} cells",
                  factor=factor, seasons=seasons, cells=[int(c) for c in cells])
    w.food_modifier[cells] *= factor
    w.intervention_event[cells] = eid
    w.intervened = True
    w.pending_restore = getattr(w, "pending_restore", []) + [(w.t + seasons, [int(c) for c in cells], factor)]
    return eid


def restore_due(w):
    keep = []
    for t_end, cells, factor in getattr(w, "pending_restore", []):
        if w.t >= t_end:
            c = np.array(cells)
            w.food_modifier[c] /= factor
            w.intervention_event[c] = -1
        else:
            keep.append((t_end, cells, factor))
    w.pending_restore = keep
