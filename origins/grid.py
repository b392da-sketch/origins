"""Geodesic grid on a sphere: subdivided icosahedron, cells are its vertices.

Level n gives 10*4**n + 2 cells (12 pentagons, the rest hexagons).
Each cell has up to six neighbours (-1 pads pentagons) and a polygon made
from the centroids of the triangles around it, used only for drawing.
"""
from __future__ import annotations

import math
import numpy as np


def _icosahedron():
    t = (1.0 + 5 ** 0.5) / 2.0
    v = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], dtype=float)
    f = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
         [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
         [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
         [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v, np.array(f, dtype=np.int64)


def _subdivide(verts: list, faces: np.ndarray):
    cache: dict[tuple[int, int], int] = {}

    def mid(a: int, b: int) -> int:
        key = (a, b) if a < b else (b, a)
        i = cache.get(key)
        if i is None:
            p = verts[a] + verts[b]
            p = p / math.sqrt(float(p @ p))
            verts.append(p)
            i = len(verts) - 1
            cache[key] = i
        return i

    out = np.empty((len(faces) * 4, 3), dtype=np.int64)
    for k, (a, b, c) in enumerate(faces.tolist()):
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        out[4 * k:4 * k + 4] = ((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca))
    return verts, out


class Grid:
    """Immutable geometry for one planet."""

    def __init__(self, level: int, radius_km: float):
        v, f = _icosahedron()
        verts = list(v)
        for _ in range(level):
            verts, f = _subdivide(verts, f)
        self.level = level
        self.radius_km = radius_km
        self.xyz = np.array(verts)
        self.faces = f
        self.n = len(self.xyz)
        x, y, z = self.xyz.T
        # rounded so that every machine gets the same values: several cells sit exactly on latitudes 27 and 30,
        # where the last digit of arcsin (which differs between processors) would otherwise decide comparisons
        self.lat = np.round(np.degrees(np.arcsin(np.clip(z, -1, 1))), 9)
        self.lon = np.round(np.degrees(np.arctan2(y, x)), 9)
        self.cell_area_km2 = 4 * math.pi * radius_km ** 2 / self.n
        self._build_neighbours()

    def _build_neighbours(self):
        f = self.faces
        edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
        edges = np.concatenate([edges, edges[:, ::-1]])
        edges = np.unique(edges, axis=0)
        counts = np.bincount(edges[:, 0], minlength=self.n)
        nb = -np.ones((self.n, 6), dtype=np.int64)
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
        pos = np.arange(len(edges)) - starts[edges[:, 0]]
        nb[edges[:, 0], pos] = edges[:, 1]
        self.neighbours = nb
        self.n_neighbours = counts
        # mean centre-to-centre spacing in km
        a = self.xyz[edges[:, 0]]
        b = self.xyz[edges[:, 1]]
        ang = np.arccos(np.clip((a * b).sum(1), -1, 1))
        self.spacing_km = float(ang.mean() * self.radius_km)

    def east_north(self):
        """Local east and north unit vectors at each cell."""
        up = self.xyz
        zaxis = np.array([0.0, 0.0, 1.0])
        east = np.cross(zaxis, up)
        norm = np.linalg.norm(east, axis=1, keepdims=True)
        east = np.where(norm > 1e-9, east / np.maximum(norm, 1e-12), np.array([1.0, 0, 0]))
        north = np.cross(up, east)
        return east, north

    def polygons(self):
        """Per cell, the lon/lat corners of its drawing polygon (ordered)."""
        f = self.faces
        cent = self.xyz[f].mean(axis=1)
        cent /= np.linalg.norm(cent, axis=1, keepdims=True)
        inc = [[] for _ in range(self.n)]
        for k, (a, b, c) in enumerate(f.tolist()):
            inc[a].append(k)
            inc[b].append(k)
            inc[c].append(k)
        east, north = self.east_north()
        out = []
        for i in range(self.n):
            ks = np.array(inc[i])
            p = cent[ks] - self.xyz[i]
            ang = np.arctan2(p @ north[i], p @ east[i])
            ks = ks[np.argsort(ang)]
            c = cent[ks]
            lat = np.degrees(np.arcsin(np.clip(c[:, 2], -1, 1)))
            lon = np.degrees(np.arctan2(c[:, 1], c[:, 0]))
            out.append(np.stack([lon, lat], axis=1))
        return out
