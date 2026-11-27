"""Customs: eight observable practices with named variants, plus neutral drift.

Inherited when a band splits, copied a little from bands in contact (within
the partner network), and occasionally changed at random. In M1 only marriage
residence has an effect (where a new couple lives); the rest make separation
visible and measurable. Belief (M5) may later give some of them weight.

reads: bands, planet ring-2 contact
writes: customs, neutral, custom_log, events (none: changes are logged per band)
"""
from __future__ import annotations

import numpy as np

from ..rows import new_rows

from .. import params as P

CUSTOMS = {
    "treatment of the dead": ["burial", "cremation", "exposure", "cave deposit", "burial with goods"],
    "body ornament": ["shell beads", "ochre paint", "tooth pendants", "tattooing", "feather work"],
    "hair": ["long and loose", "braided", "shaved", "bound up", "cut short"],
    "gathering festival": ["spring", "midsummer", "autumn", "midwinter", "first rains"],
    "tool style": ["leaf-shaped points", "long blades", "small bladelets", "heavy choppers", "bone points"],
    "shelter": ["brush huts", "hide tents", "pit houses", "rock shelters", "pole-and-mat"],
    "marriage residence": ["with his people", "with her people", "either"],
    "naming of children": ["after a grandparent", "after an animal", "after the season of birth",
                           "from a dream", "after a deed"],
    # M3: how a leader's place passes on (matters only where there is a leader to succeed)
    "succession": ["to a son", "to a sister's son", "chosen by the council", "to a daughter"],
    # M3: who speaks for a household (and so may lead, when a council chooses among household heads)
    "household voice": ["the man", "the woman", "the elder of the two"],
    # M4a: what people do when an epidemic comes (Ben, 20 November 2026; Hewlett & Amola 2003; Kelton 2004)
    "response to epidemics": ["carry on", "flight", "isolate the sick"],
}
NAMES = list(CUSTOMS)
RESIDENCE = NAMES.index("marriage residence")
SUCCESSION = NAMES.index("succession")
HOUSEHOLD_VOICE = NAMES.index("household voice")
RESIDENCE_WITH_HUSBAND = [0.85, 0.15, 0.5]       # chance she moves to his band, by variant
N_NEUTRAL = 12


def init(w):
    w.customs = new_rows(w, (len(NAMES),), np.int8, 0)
    w.neutral = new_rows(w, (N_NEUTRAL,), np.float32, 0.0)
    w.custom_log = {}


def _founders_row():
    c = np.zeros(len(NAMES), dtype=np.int8)
    c[RESIDENCE] = 2                              # founders: either (M0's 50/50 rule)
    return c


def widen(w):
    """Older saves have fewer customs: new ones start at their first variant."""
    if w.customs.shape[1] < len(NAMES):
        c = new_rows(w, (len(NAMES),), np.int8, 0)
        ids, rows = w.customs.by_id()
        wide = np.zeros((len(ids), len(NAMES)), dtype=np.int8)
        wide[:, :rows.shape[1]] = rows
        c.load_rows(ids, wide)
        w.customs.slots.arrays.remove(w.customs)
        w.customs = c


def ensure(w, band_id: int, parent: int):
    widen(w)
    if parent >= 0:
        w.customs[band_id] = w.customs[parent]
        w.neutral[band_id] = w.neutral[parent]
    else:                                         # the founders (the only bands made without a mother)
        w.customs[band_id] = _founders_row()
        w.neutral[band_id] = 0.0


def residence_share(w, band_id: int) -> float:
    return RESIDENCE_WITH_HUSBAND[int(w.customs[band_id, RESIDENCE])]


def _log(w, bid, t, k, old, new, how):
    log = w.custom_log.setdefault(int(bid), [])
    log.append([t, NAMES[k], CUSTOMS[NAMES[k]][old], CUSTOMS[NAMES[k]][new], how])
    del log[:-12]


def yearly(w):
    from .language import ring2
    rng = w.rng["customs"]
    bands = w.living_bands()
    if not bands:
        return
    widen(w)
    r2 = ring2(w)
    by_cell: dict[int, list] = {}
    for b in bands:
        by_cell.setdefault(b.cell, []).append(b.id)
    ids = np.array([b.id for b in bands])
    t = w.t
    # neutral drift
    w.neutral[ids] += rng.normal(0, P.NEUTRAL_DRIFT, size=(len(ids), N_NEUTRAL)).astype(np.float32)
    # invention
    inv = rng.random((len(ids), len(NAMES))) < P.CUSTOM_INVENTION
    for r, k in zip(*np.nonzero(inv)):
        bid = int(ids[r])
        old = int(w.customs[bid, k])
        new = int(rng.integers(len(CUSTOMS[NAMES[k]]) - 1))
        new = new + (new >= old)
        w.customs[bid, k] = new
        _log(w, bid, t, k, old, new, "new practice")
    # copying from a band in contact
    copy = rng.random(len(ids)) < P.CUSTOM_COPYING
    for r in np.nonzero(copy)[0]:
        b = bands[int(r)]
        near = [o for c in r2[b.cell] for o in by_cell.get(int(c), ()) if o != b.id]
        if not near:
            continue
        o = near[int(rng.integers(len(near)))]
        k = int(rng.integers(len(NAMES)))
        old, new = int(w.customs[b.id, k]), int(w.customs[o, k])
        w.neutral[b.id] += P.NEUTRAL_COPY * (w.neutral[o] - w.neutral[b.id])
        if old != new:
            w.customs[b.id, k] = new
            _log(w, b.id, t, k, old, new, f"copied from {w.band_name(w.bands[o])}")


def distance(w, a: int, b: int) -> float:
    """0 = identical, 1 = completely different (half customs, half neutral drift)."""
    differ = float((w.customs[a] != w.customs[b]).mean())
    neutral = float(np.linalg.norm(w.neutral[a] - w.neutral[b]) / np.sqrt(N_NEUTRAL))
    return 0.5 * differ + 0.5 * min(1.0, neutral / P.NEUTRAL_SCALE)
