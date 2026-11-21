"""The compact log (Ben, 22 November 2026; docs/COMPACT_LOG_PROPOSAL.md): five kinds of happening that ended no
chain but one, recorded as rows of numbers instead of full events. They were 15 of the planet-4 pilot's 16.9 million
events by year 5,765:

- helped_by_partners: a band short of food helped by its gift partners;
- partnership_formed and partnership_lapsed: gift partnerships begun and ended;
- gift_exchange: a partnership's first gifts;
- land_move: a move that worn land decided.

Every row is kept (nothing is thinned). A row is read back as an event-like dict (as_event), with the same kind,
data and causes the event had, and its note written from the numbers when it is read. No other record cites these
happenings as a cause; they cite bands, and land moves cite land events. References to a row are
{"log": [kind, row]}. Saved in arrays.npz and included in the digest (persist)."""
from __future__ import annotations

import numpy as np

from .. import params as P

# columns per kind; every value is held as float64 (ids and ticks are whole numbers well inside its exact range)
COLUMNS = {
    "helped_by_partners": ["t", "band", "cell", "amount", "givers_from", "givers_n"],
    "partnership_formed": ["t", "band", "partner", "cell", "reason", "closeness", "dropped"],
    "partnership_lapsed": ["t", "band", "partner", "cell", "reason", "other", "years",
                           "band_gave_shell", "band_gave_gold", "partner_gave_shell", "partner_gave_gold"],
    "gift_exchange": ["t", "band", "partner", "cell",
                      "band_gave_shell", "band_gave_gold", "partner_gave_shell", "partner_gave_gold"],
    "land_move": ["t", "band", "cell", "here", "there", "here_natural", "land_event_1", "land_event_2"],
}
KINDS = tuple(COLUMNS)
FORMED_NEAR, FORMED_SWAP = 0, 1
LAPSED_REACH, LAPSED_ENDED, LAPSED_JOINED, LAPSED_SWAP = 0, 1, 2, 3
GIFT = ("shell", "gold")        # P.GIFT_GOODS when the log was made; checked in init
# For checking only (tests): also write each row as the full event the old code wrote, from as_event, so that a
# history can be compared bit for bit with the code before the compact log (events, digest and band texts alike).
SHADOW = False


class Table:
    """A growing float64 array of rows."""

    def __init__(self, ncol: int, a=None):
        a = np.zeros((0, ncol)) if a is None else np.asarray(a, dtype=np.float64).reshape(-1, ncol)
        self._a = np.zeros((max(1024, 2 * len(a)), ncol))
        self._a[:len(a)] = a
        self.n = len(a)

    def append(self, row) -> int:
        if self.n == len(self._a):
            b = np.zeros((2 * len(self._a), self._a.shape[1]))
            b[:self.n] = self._a
            self._a = b
        self._a[self.n] = row
        self.n += 1
        return self.n - 1

    def array(self):
        return self._a[:self.n]

    def __len__(self):
        return self.n


class Ints:
    """A growing int64 list (the givers of help)."""

    def __init__(self, a=None):
        a = np.zeros(0, dtype=np.int64) if a is None else np.asarray(a, dtype=np.int64).ravel()
        self._a = np.zeros(max(1024, 2 * len(a)), dtype=np.int64)
        self._a[:len(a)] = a
        self.n = len(a)

    def extend(self, xs):
        xs = np.asarray(xs, dtype=np.int64)
        if self.n + len(xs) > len(self._a):
            b = np.zeros(max(2 * len(self._a), self.n + len(xs)), dtype=np.int64)
            b[:self.n] = self._a[:self.n]
            self._a = b
        self._a[self.n:self.n + len(xs)] = xs
        self.n += len(xs)

    def array(self):
        return self._a[:self.n]


def init(w):
    assert tuple(P.GIFT_GOODS) == GIFT, "the compact log's gift columns follow GIFT_GOODS"
    w.minor = {k: Table(len(c)) for k, c in COLUMNS.items()}
    w.minor_givers = Ints()


def _ensure(w):
    if getattr(w, "minor", None) is None:
        init(w)


def _count(w, kind):
    if not SHADOW:
        w.counts[kind] = w.counts.get(kind, 0) + 1


def _add(w, kind, row) -> int:
    i = w.minor[kind].append(row)
    if SHADOW:
        e = as_event(w, kind, i)
        return w.event(kind, cell=e["cell"], band=e["band"], causes=e["causes"], **e["data"])
    return i


def _sides(d: dict, a: int, b: int):
    da, db = d.get(str(a), {}), d.get(str(b), {})
    return [float(da.get(g, 0.0)) for g in GIFT] + [float(db.get(g, 0.0)) for g in GIFT]


# ------------------------------------------------------------------ recording
def helped(w, band, cell, amount: float, givers) -> int:
    _ensure(w)
    _count(w, "helped_by_partners")
    start = w.minor_givers.n
    w.minor_givers.extend([int(g) for g in givers])
    return _add(w, "helped_by_partners", [w.t, band, cell, amount, start, len(givers)])


def formed(w, band, partner, cell, reason: int, closeness: float = 0.0, dropped: int = -1) -> int:
    _ensure(w)
    _count(w, "partnership_formed")
    return _add(w, "partnership_formed", [w.t, band, partner, cell, reason, closeness, dropped])


def lapsed(w, band, partner, cell, reason: int, gifts: dict, other: int = -1) -> int:
    _ensure(w)
    _count(w, "partnership_lapsed")
    return _add(w, "partnership_lapsed", [w.t, band, partner, cell, reason, other, gifts.get("years", 0)]
                                                + _sides(gifts, band, partner))


def first_gifts(w, band, partner, cell, given: dict) -> int:
    _ensure(w)
    _count(w, "gift_exchange")
    return _add(w, "gift_exchange", [w.t, band, partner, cell] + _sides(given, band, partner))


def land_move(w, band, cell, here: float, there: float, here_nat: float, events) -> int:
    _ensure(w)
    _count(w, "land_move")
    ev = list(events) + [-1, -1]
    return _add(w, "land_move", [w.t, band, cell, here, there, here_nat, ev[0], ev[1]])


# ------------------------------------------------------------------ reading
def size(w, kind) -> int:
    m = getattr(w, "minor", None)
    return len(m[kind]) if m is not None and kind in m else 0


def _name(w, i: int) -> str:
    b = w.bands.get(int(i))
    return w.band_name(b) if b is not None else f"band {int(i)}"


def _gifts(band, partner, v):
    return {str(band): {g: x for g, x in zip(GIFT, v[:2]) if x > 0},
            str(partner): {g: x for g, x in zip(GIFT, v[2:]) if x > 0}}


def as_event(w, kind: str, i: int) -> dict:
    """Row i of a table as the event it replaces: id, t, kind, cell, band, person, causes and data, the note
    written from the numbers (the same words the event carried)."""
    r = w.minor[kind].array()[int(i)]
    t, band = int(r[0]), int(r[1])
    ref = {"log": [kind, int(i)]}
    if kind == "helped_by_partners":
        cell, amount, s, n = int(r[2]), float(r[3]), int(r[4]), int(r[5])
        givers = w.minor_givers.array()[s:s + n].tolist()
        causes = [{"band": g} for g in givers] + [{"note": f"{_name(w, band)} could not meet its needs this season; "
                                                           f"its gift partners gave food they could spare"}]
        data = {"amount": amount, "givers": givers}
    elif kind == "partnership_formed":
        partner, cell, reason = int(r[2]), int(r[3]), int(r[4])
        if reason == FORMED_NEAR:
            causes = [{"band": partner}, {"note": f"{_name(w, band)} and {_name(w, partner)} lived within reach of "
                                                  f"each other ({float(r[5]):.0%} closeness of speech) and began to "
                                                  f"exchange gifts"}]
        else:
            causes = [{"band": partner}, {"note": f"{_name(w, band)}, settled and with no room for more partners, "
                                                  f"took up {_name(w, partner)}, better supplied with tools, salt and "
                                                  f"metal than {_name(w, int(r[6]))}"}]
        data = {"partner": partner}
    elif kind == "partnership_lapsed":
        partner, cell, reason, other = int(r[2]), int(r[3]), int(r[4]), int(r[5])
        gifts = {"years": int(r[6]), **_gifts(band, partner, r[7:11])}
        if reason == LAPSED_REACH:
            causes = [{"band": partner}, {"note": f"{_name(w, band)} and {_name(w, partner)} were no longer within "
                                                  f"reach of each other"}]
        elif reason in (LAPSED_ENDED, LAPSED_JOINED):
            why = "ended" if reason == LAPSED_ENDED else f"joined {_name(w, other)}"
            causes = [{"band": band}, {"note": f"the partnership ended when {_name(w, band)} {why}"}]
        else:
            causes = [{"band": partner}, {"note": f"{_name(w, band)} gave up its partnership with "
                                                  f"{_name(w, partner)}, its worst-supplied partner, for a "
                                                  f"better-supplied one"}]
        data = {"partner": partner, "gifts": gifts}
    elif kind == "gift_exchange":
        partner, cell = int(r[2]), int(r[3])
        causes = [{"band": partner}, {"note": f"{_name(w, band)} and {_name(w, partner)} exchanged their first "
                                              f"gifts as partners"}]
        data = {"partner": partner, "goods": _gifts(band, partner, r[4:8])}
    elif kind == "land_move":
        cell, here, there, nat = int(r[2]), float(r[3]), float(r[4]), float(r[5])
        note = (f"{_name(w, band)} left: {here / P.SEASON_DAYS:.2f} food units per person-day where it was, against "
                f"{there / P.SEASON_DAYS:.2f} next door; with this season's regrowth at the land's natural level it "
                f"would have had {nat / P.SEASON_DAYS:.2f}, and stayed")
        causes = [{"note": note}] + [{"event": int(e)} for e in r[6:8] if e >= 0]
        data = {}
    else:
        raise KeyError(kind)
    return {"id": ref, "t": t, "kind": kind, "cell": cell, "band": band, "person": -1, "causes": causes,
            "data": data}


def rows(w, kind: str):
    """All rows of a kind as events, in order (slow for millions: for samples and small worlds)."""
    for i in range(size(w, kind)):
        yield as_event(w, kind, i)


def move_text(ref: int) -> str:
    """How a band's last move names the land move that decided it."""
    return f"event {ref}" if SHADOW else f"land move {ref}"


def since(w, kind: str, n0: int) -> list:
    """Rows n0 onwards of a kind, as events."""
    return [as_event(w, kind, i) for i in range(n0, size(w, kind))]


def band_rows(w, band_id: int):
    """Every row naming this band as its band or partner, as events, in time order."""
    out = []
    m = getattr(w, "minor", None)
    if m is None:
        return out
    for kind, tab in m.items():
        a = tab.array()
        if not len(a):
            continue
        hit = a[:, 1] == band_id
        if COLUMNS[kind][2] == "partner":
            hit |= a[:, 2] == band_id
        out += [as_event(w, kind, int(i)) for i in np.nonzero(hit)[0]]
    return sorted(out, key=lambda e: e["t"])


# ------------------------------------------------------------------ saving
def arrays(w) -> dict:
    """The same keys whether or not anything has been recorded (a fresh world and a reloaded one digest alike)."""
    _ensure(w)
    if SHADOW:
        return {}
    m = w.minor
    out = {f"minor_{k}": t.array() for k, t in m.items()}
    out["minor_givers"] = w.minor_givers.array()
    return out


def load(w, arrs: dict):
    w.minor = {k: Table(len(c), arrs.get(f"minor_{k}")) for k, c in COLUMNS.items()}
    w.minor_givers = Ints(arrs.get("minor_givers"))
