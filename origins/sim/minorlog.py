"""The compact log (Ben, 22 November 2026; docs/COMPACT_LOG_PROPOSAL.md): five kinds of happening that end no chain
but their own, recorded as rows of numbers instead of full events. They were 15 of the planet-4 pilot's 16.9 million
events by year 5,765:

- helped_by_partners: a band short of food helped by its gift partners;
- partnership_formed and partnership_lapsed: gift partnerships begun and ended;
- gift_exchange: a partnership's first gifts;
- land_move: a move that worn land decided.

Every row is kept (nothing is thinned). A row is read back as the event it replaces (as_event): the same kind, data
and causes, its note written from the numbers and from the band names as they were when it was recorded (kept in a
shared table of names; Codex review 039, finding 2). No other record cites these happenings as a cause; they cite
bands, and land moves cite land events. References to a row are {"log": [kind, row]}.

Each row also keeps where it falls among events: "after" is the number of events recorded before it, "order" a
count over all rows, so rows and events read back in the order they happened (review 039, finding 4). Saved in
arrays.npz and included in the digest (persist)."""
from __future__ import annotations

import numpy as np

from .. import params as P

# columns per kind; every value is held as float64 (ids, ticks and counts are whole numbers well inside its exact
# range). A gift good a record did not mention is -1, so a gift that rounded to 0.0 keeps its key (review 039, 3).
COLUMNS = {
    "helped_by_partners": ["t", "band", "cell", "amount", "givers_from", "givers_n", "name_band"],
    "partnership_formed": ["t", "band", "partner", "cell", "reason", "closeness", "dropped",
                           "name_band", "name_partner", "name_dropped"],
    "partnership_lapsed": ["t", "band", "partner", "cell", "reason", "other", "years",
                           "band_gave_shell", "band_gave_gold", "partner_gave_shell", "partner_gave_gold",
                           "name_band", "name_partner", "name_other"],
    "gift_exchange": ["t", "band", "partner", "cell",
                      "band_gave_shell", "band_gave_gold", "partner_gave_shell", "partner_gave_gold",
                      "name_band", "name_partner"],
    "land_move": ["t", "band", "cell", "here", "there", "here_natural", "land_event_1", "land_event_2", "name_band"],
}
for _c in COLUMNS.values():
    _c += ["after", "order"]
KINDS = tuple(COLUMNS)
COL = {k: {c: i for i, c in enumerate(cs)} for k, cs in COLUMNS.items()}
FORMED_NEAR, FORMED_SWAP = 0, 1
LAPSED_REACH, LAPSED_ENDED, LAPSED_JOINED, LAPSED_SWAP = 0, 1, 2, 3
GIFT = ("shell", "gold")        # P.GIFT_GOODS when the log was made; checked in init
NONE = -1.0                     # a gift good not mentioned
# For checking only (tests): also write each row as the full event the old code wrote, from as_event, so that a
# history can be compared bit for bit with the code before the compact log (events, digest and band texts alike).
SHADOW = False


FLOATS = {"amount", "closeness", "here", "there", "here_natural", "band_gave_shell", "band_gave_gold",
          "partner_gave_shell", "partner_gave_gold"}


I32 = (-2 ** 31, 2 ** 31 - 1)


def _whole(a, kind: str) -> np.ndarray:
    """Whole numbers as int32, checked before narrowing: finite, integral and inside int32 (review 042, finding 4)."""
    a = np.asarray(a)
    if a.size == 0:
        return a.astype(np.int32)
    if np.issubdtype(a.dtype, np.integer):
        if a.min() < I32[0] or a.max() > I32[1]:
            raise OverflowError(f"compact log {kind}: a whole number beyond int32")
        return a.astype(np.int32)
    f = np.asarray(a, dtype=np.float64)
    if not np.isfinite(f).all():
        raise ValueError(f"compact log {kind}: a whole-number column holds a non-finite value")
    if (f != np.floor(f)).any():
        raise ValueError(f"compact log {kind}: a whole-number column holds a fraction")
    if f.min() < I32[0] or f.max() > I32[1]:
        raise OverflowError(f"compact log {kind}: a whole number beyond int32")
    return f.astype(np.int32)


class Table:
    """A growing table of rows: whole-number columns as int32, amounts as float64 (G4a pilot 3, 26 November 2026:
    every column was float64, 1.4 GB by year 5,733 on planet 4). Every value reads back exactly as recorded: ids,
    ticks, cells, counts and indexes are whole numbers well inside int32, and amounts keep their float64 bits."""

    def __init__(self, kind: str, ints=None, floats=None):
        cols = COLUMNS[kind]
        self.kind = kind
        self.icol = [c for c in cols if c not in FLOATS]
        self.fcol = [c for c in cols if c in FLOATS]
        self.where = {c: ("i", self.icol.index(c)) if c in self.icol else ("f", self.fcol.index(c)) for c in cols}
        ints = np.zeros((0, len(self.icol)), dtype=np.int32) if ints is None else np.asarray(ints).reshape(-1, len(self.icol))
        floats = np.zeros((0, len(self.fcol))) if floats is None else np.asarray(floats, dtype=np.float64).reshape(-1, len(self.fcol))
        n = len(ints)
        if len(floats) != n:
            raise ValueError(f"compact log {kind}: {n} rows of whole numbers, {len(floats)} of amounts")
        cap = max(1024, n + n // 4)
        self._i = np.zeros((cap, len(self.icol)), dtype=np.int32)
        self._f = np.zeros((cap, len(self.fcol)))
        self._i[:n] = _whole(ints, kind)
        self._f[:n] = floats
        self.n = n

    @classmethod
    def from_wide(cls, kind: str, a):
        """From one float64 array holding every column (saves of 22-26 November 2026)."""
        cols = COLUMNS[kind]
        a = np.asarray(a, dtype=np.float64).reshape(-1, len(cols))
        t = cls(kind)
        ii = [cols.index(c) for c in t.icol]
        fi = [cols.index(c) for c in t.fcol]
        return cls(kind, _whole(a[:, ii], kind), a[:, fi])

    def append(self, row) -> int:
        if self.n == len(self._i):
            cap = 2 * len(self._i)
            i, f = np.zeros((cap, self._i.shape[1]), dtype=np.int32), np.zeros((cap, self._f.shape[1]))
            i[:self.n], f[:self.n] = self._i[:self.n], self._f[:self.n]
            self._i, self._f = i, f
        cols = COLUMNS[self.kind]
        vals = dict(zip(cols, row))
        self._i[self.n] = _whole(np.array([vals[c] for c in self.icol]), self.kind)
        self._f[self.n] = [float(vals[c]) for c in self.fcol]
        self.n += 1
        return self.n - 1

    def col(self, name: str) -> np.ndarray:
        """One column over all rows (whole numbers as int32, amounts as float64)."""
        part, j = self.where[name]
        return (self._i if part == "i" else self._f)[:self.n, j]

    def row(self, i: int) -> np.ndarray:
        """Row i with every column, in COLUMNS order, as float64 (whole numbers are exact in float64)."""
        out = np.empty(len(COLUMNS[self.kind]))
        for c, (part, j) in self.where.items():
            out[COL[self.kind][c]] = self._i[i, j] if part == "i" else self._f[i, j]
        return out

    def ints(self):
        return self._i[:self.n]

    def floats(self):
        return self._f[:self.n]

    def __len__(self):
        return self.n


class Ints:
    """A growing int64 list (the givers of help)."""

    def __init__(self, a=None):
        a = np.zeros(0, dtype=np.int64) if a is None else np.asarray(a, dtype=np.int64).ravel()
        self._a = np.zeros(max(1024, len(a) + len(a) // 4), dtype=np.int64)
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
    w.minor = {k: Table(k) for k in COLUMNS}
    w.minor_givers = Ints()
    w.minor_names = []           # band names as recorded, shared by all rows
    w._minor_name_ix = {}
    w.minor_order = 0


def _ensure(w):
    if getattr(w, "minor", None) is None:
        init(w)


def _count(w, kind):
    if not SHADOW:
        w.counts[kind] = w.counts.get(kind, 0) + 1


def _name_ix(w, band_id: int) -> int:
    """The index of this band's name as it is now, in the shared table of names."""
    if band_id < 0:
        return -1
    b = w.bands.get(int(band_id))
    nm = w.band_name(b) if b is not None else f"band {int(band_id)}"
    ix = w._minor_name_ix.get(nm)
    if ix is None:
        ix = w._minor_name_ix[nm] = len(w.minor_names)
        w.minor_names.append(nm)
    return ix


def _add(w, kind, row) -> int:
    row = list(row) + [len(w.events), w.minor_order]
    w.minor_order += 1
    i = w.minor[kind].append(row)
    if SHADOW:
        e = as_event(w, kind, i)
        return w.event(kind, cell=e["cell"], band=e["band"], causes=e["causes"], **e["data"])
    return i


def _sides(d: dict, a: int, b: int):
    da, db = d.get(str(a), {}), d.get(str(b), {})
    return [float(da[g]) if g in da else NONE for g in GIFT] + [float(db[g]) if g in db else NONE for g in GIFT]


# ------------------------------------------------------------------ recording
def helped(w, band, cell, amount: float, givers) -> int:
    _ensure(w)
    _count(w, "helped_by_partners")
    start = w.minor_givers.n
    w.minor_givers.extend([int(g) for g in givers])
    return _add(w, "helped_by_partners", [w.t, band, cell, amount, start, len(givers), _name_ix(w, band)])


def formed(w, band, partner, cell, reason: int, closeness: float = 0.0, dropped: int = -1) -> int:
    _ensure(w)
    _count(w, "partnership_formed")
    return _add(w, "partnership_formed", [w.t, band, partner, cell, reason, closeness, dropped, _name_ix(w, band),
                                          _name_ix(w, partner), _name_ix(w, dropped)])


def lapsed(w, band, partner, cell, reason: int, gifts: dict, other: int = -1) -> int:
    _ensure(w)
    _count(w, "partnership_lapsed")
    return _add(w, "partnership_lapsed", [w.t, band, partner, cell, reason, other, gifts.get("years", 0)]
                + _sides(gifts, band, partner) + [_name_ix(w, band), _name_ix(w, partner), _name_ix(w, other)])


def first_gifts(w, band, partner, cell, given: dict) -> int:
    _ensure(w)
    _count(w, "gift_exchange")
    return _add(w, "gift_exchange", [w.t, band, partner, cell] + _sides(given, band, partner)
                + [_name_ix(w, band), _name_ix(w, partner)])


def land_move(w, band, cell, here: float, there: float, here_nat: float, events) -> int:
    _ensure(w)
    _count(w, "land_move")
    ev = list(events) + [-1, -1]
    return _add(w, "land_move", [w.t, band, cell, here, there, here_nat, ev[0], ev[1], _name_ix(w, band)])


# ------------------------------------------------------------------ reading
def size(w, kind) -> int:
    m = getattr(w, "minor", None)
    return len(m[kind]) if m is not None and kind in m else 0


def count_all(w, counts: dict | None = None) -> dict:
    """Events by kind with the compact log's rows added (older records of these kinds stay events; review 039,
    finding 1). Pass a dict of event counts already made to add the rows to it."""
    if counts is None:
        counts = {}
        for e in w.events:
            counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    for k in KINDS:
        n = size(w, k)
        if n:
            counts[k] = counts.get(k, 0) + n
    return counts


def _gifts(band, partner, v):
    return {str(band): {g: float(x) for g, x in zip(GIFT, v[:2]) if x >= 0},
            str(partner): {g: float(x) for g, x in zip(GIFT, v[2:]) if x >= 0}}


def as_event(w, kind: str, i: int) -> dict:
    """Row i of a table as the event it replaces: id, t, kind, cell, band, person, causes and data, the note
    written from the numbers and the names recorded with them (the same words the event carried)."""
    if kind not in COLUMNS:
        raise KeyError(f"no compact log of {kind!r}")
    i = int(i)
    if not 0 <= i < size(w, kind):
        raise IndexError(f"no row {i} in the compact log of {kind}")      # (review 039, finding 5)
    r = w.minor[kind].row(i)
    c = COL[kind]
    names = w.minor_names

    def nm(col):
        return names[int(r[c[col]])]
    t, band = int(r[0]), int(r[1])
    ref = {"log": [kind, i]}
    if kind == "helped_by_partners":
        cell, amount, s, n = int(r[2]), float(r[3]), int(r[4]), int(r[5])
        givers = w.minor_givers.array()[s:s + n].tolist()
        causes = [{"band": g} for g in givers] + [{"note": f"{nm('name_band')} could not meet its needs this "
                                                           f"season; its gift partners gave food they could spare"}]
        data = {"amount": amount, "givers": givers}
    elif kind == "partnership_formed":
        partner, cell, reason = int(r[2]), int(r[3]), int(r[4])
        if reason == FORMED_NEAR:
            causes = [{"band": partner}, {"note": f"{nm('name_band')} and {nm('name_partner')} lived within reach of "
                                                  f"each other ({float(r[5]):.0%} closeness of speech) and began to "
                                                  f"exchange gifts"}]
        else:
            causes = [{"band": partner}, {"note": f"{nm('name_band')}, settled and with no room for more partners, "
                                                  f"took up {nm('name_partner')}, better supplied with tools, salt "
                                                  f"and metal than {nm('name_dropped')}"}]
        data = {"partner": partner}
    elif kind == "partnership_lapsed":
        partner, cell, reason = int(r[2]), int(r[3]), int(r[4])
        gifts = {"years": int(r[6]), **_gifts(band, partner, r[7:11])}
        if reason == LAPSED_REACH:
            causes = [{"band": partner}, {"note": f"{nm('name_band')} and {nm('name_partner')} were no longer "
                                                  f"within reach of each other"}]
        elif reason in (LAPSED_ENDED, LAPSED_JOINED):
            why = "ended" if reason == LAPSED_ENDED else f"joined {nm('name_other')}"
            causes = [{"band": band}, {"note": f"the partnership ended when {nm('name_band')} {why}"}]
        else:
            causes = [{"band": partner}, {"note": f"{nm('name_band')} gave up its partnership with "
                                                  f"{nm('name_partner')}, its worst-supplied partner, for a "
                                                  f"better-supplied one"}]
        data = {"partner": partner, "gifts": gifts}
    elif kind == "gift_exchange":
        partner, cell = int(r[2]), int(r[3])
        causes = [{"band": partner}, {"note": f"{nm('name_band')} and {nm('name_partner')} exchanged their first "
                                              f"gifts as partners"}]
        data = {"partner": partner, "goods": _gifts(band, partner, r[4:8])}
    else:                                                                   # land_move
        cell, here, there, nat = int(r[2]), float(r[3]), float(r[4]), float(r[5])
        note = (f"{nm('name_band')} left: {here / P.SEASON_DAYS:.2f} food units per person-day where it was, against "
                f"{there / P.SEASON_DAYS:.2f} next door; with this season's regrowth at the land's natural level it "
                f"would have had {nat / P.SEASON_DAYS:.2f}, and stayed")
        causes = [{"note": note}] + [{"event": int(e)} for e in r[6:8] if e >= 0]
        data = {}
    return {"id": ref, "t": t, "kind": kind, "cell": cell, "band": band, "person": -1, "causes": causes,
            "data": data}


def key_of_row(w, kind: str, i: int) -> tuple:
    """Where a row falls among events and rows: (events recorded before it, its order among rows)."""
    t = w.minor[kind]
    return (int(t.col("after")[int(i)]), int(t.col("order")[int(i)]))


def key_of_event(event_id: int) -> tuple:
    """An event's place in the same order: after every row recorded before it (rows recorded when it was the
    next event to come have after == its id)."""
    return (int(event_id), 1 << 62)


def move_text(ref: int) -> str:
    """How a band's last move names the land move that decided it."""
    return f"event {ref}" if SHADOW else f"land move {ref}"


def since(w, kind: str, n0: int) -> list:
    """Rows n0 onwards of a kind, as events."""
    return [as_event(w, kind, i) for i in range(n0, size(w, kind))]


def latest(w, limit: int, band_id: int | None = None) -> list:
    """The last `limit` rows over all kinds (those naming a band as its band or partner, if given), oldest first,
    as (key, kind, row): only those are read back (review 039, finding 4)."""
    m = getattr(w, "minor", None)
    if m is None:
        return []
    out = []
    for kind, tab in m.items():
        if not len(tab):
            continue
        if band_id is None:
            idx = np.arange(max(0, len(tab) - limit), len(tab))
        else:
            hit = tab.col("band") == band_id
            if COLUMNS[kind][2] == "partner":
                hit |= tab.col("partner") == band_id
            idx = np.nonzero(hit)[0][-limit:]
        after, order = tab.col("after"), tab.col("order")
        out += [((int(after[i]), int(order[i])), kind, int(i)) for i in idx]
    out.sort()
    return out[-limit:]


def band_rows(w, band_id: int, limit: int | None = None):
    """The rows naming this band as its band or partner, as events, oldest first (the last `limit` if given)."""
    return [as_event(w, k, i) for _, k, i in latest(w, limit if limit is not None else 1 << 62, band_id)]


# ------------------------------------------------------------------ saving
def _names_blob(w) -> np.ndarray:
    return np.frombuffer("\x1f".join(w.minor_names).encode("utf-8"), dtype=np.uint8).copy()


def arrays(w) -> dict:
    """The same keys whether or not anything has been recorded (a fresh world and a reloaded one digest alike)."""
    _ensure(w)
    if SHADOW:
        return {}
    out = {}
    for k, t in w.minor.items():
        out[f"minor_{k}_i"] = t.ints()
        out[f"minor_{k}_f"] = t.floats()
    out["minor_givers"] = w.minor_givers.array()
    out["minor_names"] = _names_blob(w)
    out["minor_order"] = np.array([w.minor_order], dtype=np.int64)
    return out


def load(w, arrs: dict):
    w.minor = {}
    for k, c in COLUMNS.items():
        if f"minor_{k}_i" in arrs:
            w.minor[k] = Table(k, arrs[f"minor_{k}_i"], arrs[f"minor_{k}_f"])
        elif f"minor_{k}" in arrs:                       # one float64 array per kind (saves of 22-26 November)
            a = np.asarray(arrs[f"minor_{k}"])
            if a.ndim == 2 and a.shape[1] != len(c):
                raise ValueError(f"compact log {k}: {a.shape[1]} columns saved, {len(c)} expected")
            w.minor[k] = Table.from_wide(k, a)
            a = None                                     # released before the next table is read (review 042)
        else:
            w.minor[k] = Table(k)
    w.minor_givers = Ints(arrs.get("minor_givers"))
    blob = arrs.get("minor_names")
    w.minor_names = (bytes(np.asarray(blob, dtype=np.uint8)).decode("utf-8").split("\x1f")
                     if blob is not None and len(blob) else [])
    w._minor_name_ix = {n: i for i, n in enumerate(w.minor_names)}
    o = arrs.get("minor_order")
    w.minor_order = int(np.asarray(o)[0]) if o is not None and len(o) else sum(len(t) for t in w.minor.values())
