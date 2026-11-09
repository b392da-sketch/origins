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
}
NAMES = list(CUSTOMS)
RESIDENCE = NAMES.index("marriage residence")
SUCCESSION = NAMES.index("succession")
HOUSEHOLD_VOICE = NAMES.index("household voice")
RESIDENCE_WITH_HUSBAND = [0.85, 0.15, 0.5]       # chance she moves to his band, by variant
N_NEUTRAL = 12


def init(w):
    cap = 64
    w.customs = np.zeros((cap, len(NAMES)), dtype=np.int8)
    w.customs[:, RESIDENCE] = 2                   # founders: either (M0's 50/50 rule)
    w.neutral = np.zeros((cap, N_NEUTRAL), dtype=np.float32)
    w.custom_log = {}


def ensure(w, band_id: int, parent: int):
    if band_id >= len(w.customs):
        cap = len(w.customs)
        while cap <= band_id:
            cap *= 2
        c = np.zeros((cap, len(NAMES)), dtype=np.int8)
        c[:len(w.customs)] = w.customs
        n = np.zeros((cap, N_NEUTRAL), dtype=np.float32)
        n[:len(w.neutral)] = w.neutral
        w.customs, w.neutral = c, n
    src = parent if parent >= 0 else 0
    w.customs[band_id] = w.customs[src]
    w.neutral[band_id] = w.neutral[src]


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
