"""Seeded 3D gradient noise (Perlin-style), vectorised with NumPy."""
from __future__ import annotations

import numpy as np

_GRAD = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
                  [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                  [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1]], dtype=float)


class Noise3:
    def __init__(self, seed: int):
        rng = np.random.default_rng(seed)
        p = rng.permutation(256)
        self.perm = np.concatenate([p, p]).astype(np.int64)

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def __call__(self, pts: np.ndarray) -> np.ndarray:
        """Noise in roughly [-1, 1] at points of shape (n, 3)."""
        perm = self.perm
        fl = np.floor(pts)
        i = fl.astype(np.int64) & 255
        f = pts - fl
        u = self._fade(f)
        out = np.zeros(len(pts))
        corners = {}
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    h = perm[perm[perm[i[:, 0] + dx] + i[:, 1] + dy] + i[:, 2] + dz] % 12
                    g = _GRAD[h]
                    d = f - np.array([dx, dy, dz])
                    corners[(dx, dy, dz)] = (g * d).sum(1)
        x0 = corners[(0, 0, 0)] + u[:, 0] * (corners[(1, 0, 0)] - corners[(0, 0, 0)])
        x1 = corners[(0, 1, 0)] + u[:, 0] * (corners[(1, 1, 0)] - corners[(0, 1, 0)])
        x2 = corners[(0, 0, 1)] + u[:, 0] * (corners[(1, 0, 1)] - corners[(0, 0, 1)])
        x3 = corners[(0, 1, 1)] + u[:, 0] * (corners[(1, 1, 1)] - corners[(0, 1, 1)])
        y0 = x0 + u[:, 1] * (x1 - x0)
        y1 = x2 + u[:, 1] * (x3 - x2)
        out = y0 + u[:, 2] * (y1 - y0)
        return out

    def fbm(self, pts: np.ndarray, octaves: int = 5, freq: float = 1.0,
            lacunarity: float = 2.0, gain: float = 0.5, ridged: bool = False) -> np.ndarray:
        total = np.zeros(len(pts))
        amp, norm = 1.0, 0.0
        offset = np.array([17.3, 41.7, 7.9])
        for o in range(octaves):
            v = self(pts * freq + offset * (o + 1))
            if ridged:
                v = 1.0 - np.abs(v)
                v = v * v
            total += amp * v
            norm += amp
            amp *= gain
            freq *= lacunarity
        return total / norm
