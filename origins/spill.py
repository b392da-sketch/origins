"""Large growing arrays kept in files mapped into memory (Ben, 29 November 2026, after G4a pilot 5).

A planet-4 history keeps every person, every compact-log row and every disease record. By year 9,000 these held
several gigabytes, nearly all of it old rows that are rarely read again. An array made here lives in a file in a
temporary folder and is mapped into memory: NumPy reads and writes it exactly as an ordinary array, with the same
bits, but the operating system keeps only the pages in use in memory and writes the rest back to the file.

Small arrays (under SPILL_MIN bytes) stay ordinary arrays. ORIGINS_SPILL=0 turns this off; ORIGINS_SPILL_DIR names
the folder (the system's temporary folder otherwise). The folder is removed when the process ends.
"""
from __future__ import annotations

import atexit
import os
import shutil
import tempfile

import numpy as np

SPILL_MIN = int(os.environ.get("ORIGINS_SPILL_MIN", 32 * 2 ** 20))   # (tests set it small)
_DIR = None
_COUNT = [0]


def on() -> bool:
    return os.environ.get("ORIGINS_SPILL", "1") != "0"


def _dir() -> str:
    global _DIR
    if _DIR is None or not os.path.isdir(_DIR):
        _DIR = tempfile.mkdtemp(prefix="origins-spill-", dir=os.environ.get("ORIGINS_SPILL_DIR") or None)
        atexit.register(shutil.rmtree, _DIR, True)
    return _DIR


def _mapped(path, shape, dtype, mode):
    """A plain ndarray over the mapped file: np.memmap's own methods run in Python on every view and every
    result, which slowed the simulation by about a fifth; the plain array keeps the mapping alive through .base."""
    return np.memmap(path, dtype=dtype, mode=mode, shape=shape).view(np.ndarray)


def _mapping(a):
    b = a
    while b is not None:
        if isinstance(b, np.memmap):
            return b
        b = getattr(b, "base", None)
    return None


def is_spilled(a) -> bool:
    m = _mapping(a) if isinstance(a, np.ndarray) else None
    return m is not None and getattr(m, "filename", None) is not None and \
        os.path.dirname(str(m.filename)) == (_DIR or "")


def filename(a) -> str:
    return str(_mapping(a).filename)


def alloc(shape, dtype, fill=0):
    """An array of this shape filled with `fill`: in a mapped file if it is large, else in memory."""
    shape = tuple(int(s) for s in (shape if isinstance(shape, (tuple, list)) else (shape,)))
    dtype = np.dtype(dtype)
    nbytes = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
    if not on() or nbytes < SPILL_MIN or shape[0] == 0:
        return np.full(shape, fill, dtype=dtype)
    _COUNT[0] += 1
    path = os.path.join(_dir(), f"a{_COUNT[0]}.bin")
    with open(path, "wb") as f:
        f.truncate(nbytes)                       # the new space reads as zeros
    a = _mapped(path, shape, dtype, "r+")
    if fill != 0:
        a[...] = fill
    return a


def regrow(old, cap: int, fill=0):
    """`old` with its first axis grown to `cap` rows, the new rows at `fill`, every old row kept exactly. A mapped
    array grows its own file (nothing is copied); an ordinary one that becomes large moves into a mapped file."""
    cap = int(cap)
    n = len(old)
    if cap <= n:
        return old
    tail = old.shape[1:]
    dtype = old.dtype
    if is_spilled(old):
        path = filename(old)
        _mapping(old).flush()
        row = int(np.prod(tail, dtype=np.int64)) * dtype.itemsize
        with open(path, "r+b") as f:
            f.truncate(cap * row)
        a = _mapped(path, (cap,) + tail, dtype, "r+")
        if fill != 0:
            a[n:] = fill
        return a
    a = alloc((cap,) + tail, dtype, fill)
    a[:n] = old
    return a
