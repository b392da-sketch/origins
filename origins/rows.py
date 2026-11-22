"""Per-band arrays that keep rows only for bands that hold one (Ben, 22 November 2026, after the G4a planet-4 pilot:
1.7 million band ids issued by year 5,765, about 14,000 bands alive, and every per-band array sized by the ids).

A SlotMap gives each band holding a row its slot; when a band ends its slot is released and reused. A SparseRows
array indexes by band id like the dense array it replaces: an int, a list or array of ids, or ':' for every slot,
followed by the usual trailing indices. Reading or writing a released (or never assigned) id raises, so no code can
silently read an ended band's row: nothing in the simulation reads one (an ended band's values are folded into
whatever aggregate still needs them, by the system that owns the array, before release)."""
from __future__ import annotations

import numpy as np


class SlotMap:
    def __init__(self, cap_ids: int = 64):
        self.slot = np.full(cap_ids, -1, dtype=np.int64)     # band id -> slot; -1 none yet; -2 released
        self._owner = np.zeros(64, dtype=np.int64)            # slot -> band id, -1 if free (capacity)
        self.n = 0                                            # slots made so far (review 040: grown by doubling)
        self.free: list[int] = []
        self.arrays: list["SparseRows"] = []

    @property
    def owner(self) -> np.ndarray:
        return self._owner[:self.n]

    def __len__(self):                                          # ids covered (as the dense array's length)
        return len(self.slot)

    def grow_ids(self, band_id: int):
        if band_id >= len(self.slot):
            cap = max(band_id + 1, 2 * len(self.slot), 64)
            s = np.full(cap, -1, dtype=np.int64)
            s[:len(self.slot)] = self.slot
            self.slot = s

    def assign(self, band_id: int) -> int:
        """A slot for this band (its own if it has one), its rows set to each array's fill."""
        self.grow_ids(band_id)
        s = int(self.slot[band_id])
        if s >= 0:
            return s
        if s == -2:
            raise KeyError(f"band {band_id} has ended: its row was released")
        if self.free:
            s = self.free.pop()
        else:
            s = self.n
            if s == len(self._owner):
                o = np.full(2 * len(self._owner), -1, dtype=np.int64)
                o[:s] = self._owner[:s]
                self._owner = o
            self.n += 1
            for a in self.arrays:
                a._grow_rows(s + 1)
        self.slot[band_id] = s
        self._owner[s] = band_id
        for a in self.arrays:
            a.data[s] = a.fill
        return s

    def release(self, band_id: int):
        """The band has ended: its slot (if any) is freed, and the id can never hold a row again (review 040,
        finding 3: an ended band without a row is marked too)."""
        self.grow_ids(band_id)
        if self.slot[band_id] >= 0:
            s = int(self.slot[band_id])
            self._owner[s] = -1
            for a in self.arrays:
                a.data[s] = a.fill
            self.free.append(s)
        self.slot[band_id] = -2

    def mark_ended(self, ids):
        """Ids of bands that have ended, with or without rows (loading older saves)."""
        ids = np.asarray(ids, dtype=np.int64)
        if ids.size:
            self.grow_ids(int(ids.max()))
            for i in ids[self.slot[ids] >= 0].tolist():
                self.release(int(i))
            self.slot[ids] = -2

    def slots_of(self, ids) -> np.ndarray | int:
        if isinstance(ids, (int, np.integer)):
            i = int(ids)
            if i < 0 or i >= len(self.slot) or self.slot[i] < 0:
                raise KeyError(f"band {i} holds no row")
            return int(self.slot[i])
        a = np.asarray(ids)
        if a.dtype == bool:
            raise TypeError("index sparse rows by band ids, not a mask")
        a = a.astype(np.int64, copy=False)
        if a.size and (a.min() < 0 or a.max() >= len(self.slot)):
            raise KeyError("band id out of range")
        s = self.slot[a]
        if s.size and (s < 0).any():
            raise KeyError(f"band {int(a[np.argmax(s < 0)])} holds no row")
        return s

    def held(self) -> np.ndarray:
        """Band ids holding a row, ascending."""
        return np.nonzero(self.slot >= 0)[0]

    # saving
    def state(self, prefix: str) -> dict:
        return {f"{prefix}_slot": self.slot, f"{prefix}_owner": self.owner,
                f"{prefix}_free": np.asarray(self.free, dtype=np.int64)}

    def load(self, prefix: str, arrs: dict):
        self.slot = np.array(arrs[f"{prefix}_slot"], dtype=np.int64)
        o = np.array(arrs[f"{prefix}_owner"], dtype=np.int64)
        self.n = len(o)
        self._owner = np.full(max(64, 2 * len(o)), -1, dtype=np.int64)
        self._owner[:len(o)] = o
        self.free = [int(x) for x in arrs[f"{prefix}_free"]]


class SparseRows:
    def __init__(self, slots: SlotMap, tail: tuple, dtype, fill):
        self.slots = slots
        self.tail = tuple(tail)
        self.fill = fill
        self.data = np.full((max(len(slots.owner), 1),) + self.tail, fill, dtype=dtype)
        slots.arrays.append(self)

    def _grow_rows(self, n):
        if n > len(self.data):
            d = np.full((max(n, 2 * len(self.data)),) + self.tail, self.fill, dtype=self.data.dtype)
            d[:len(self.data)] = self.data
            self.data = d

    def __len__(self):
        return len(self.slots)

    @property
    def shape(self):
        return (len(self.slots),) + self.tail

    @property
    def dtype(self):
        return self.data.dtype

    def _key(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        first, rest = key[0], key[1:]
        if isinstance(first, slice):
            if first != slice(None):
                raise IndexError("only ':' slices sparse rows")
            return (slice(0, len(self.slots.owner)),) + rest
        return (self.slots.slots_of(first),) + rest

    def __getitem__(self, key):
        return self.data[self._key(key)]

    def __setitem__(self, key, value):
        self.data[self._key(key)] = value

    def rows(self):
        """The rows in use, by slot (free slots hold the fill value)."""
        return self.data[:len(self.slots.owner)]

    def dense(self) -> np.ndarray:
        """Every id's row as a dense array, released and unassigned ids at the fill value (for tests and small
        worlds only)."""
        out = np.full(self.shape, self.fill, dtype=self.dtype)
        ids = self.slots.held()
        out[ids] = self.data[self.slots.slot[ids]]
        return out

    def by_id(self) -> tuple[np.ndarray, np.ndarray]:
        """(band ids holding a row, ascending; their rows in that order)."""
        ids = self.slots.held()
        return ids, self.data[self.slots.slot[ids]] if len(ids) else self.data[:0]
