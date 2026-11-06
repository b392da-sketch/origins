"""Climate variability and wild-food regrowth.

reads: planet (capacity, season_food, region), t, region_z, food_modifier, hazard_food
writes: region_z, region_factor, region_bad_event, stock, ledger['regrowth'], events (bad_year)
"""
from __future__ import annotations

import numpy as np

from .. import params as P


def init(w):
    """Opening state: draw initial climate anomalies; fill wild food to its seasonal level."""
    rng = w.rng["climate"]
    w.region_z = rng.normal(size=w.planet.n_regions)
    w.region_factor = _factor(w.region_z)
    w.stock = seasonal_max(w).copy()


def _factor(z):
    return np.clip(np.exp(P.CLIMATE_SIGMA * z), P.CLIMATE_MIN, P.CLIMATE_MAX)


def seasonal_max(w, quarter=None):
    p = w.planet
    q = w.quarter if quarter is None else quarter
    return (p.capacity * P.SEASON_DAYS * P.STOCK_MULTIPLIER * p.season_food[:, q]
            * w.region_factor[p.region] * w.food_modifier * w.hazard_food)


def yearly(w):
    """At the start of each year: new regional good/bad-year factors (correlated over time)."""
    rng = w.rng["climate"]
    eps = rng.normal(size=w.planet.n_regions)
    w.region_z = P.CLIMATE_AR * w.region_z + np.sqrt(1 - P.CLIMATE_AR ** 2) * eps
    w.region_factor = _factor(w.region_z)
    w.region_bad_event[:] = -1
    occupied = {w.planet.region[b.cell] for b in w.living_bands()}
    for r in sorted(occupied):
        if w.region_factor[r] < P.BAD_YEAR:
            w.region_bad_event[r] = w.event(
                "bad_year", causes=[{"note": f"climate factor {w.region_factor[r]:.2f} in this region "
                                             f"(below {P.BAD_YEAR})"}],
                region=int(r), factor=round(float(w.region_factor[r]), 3))


def regrow(w):
    target = seasonal_max(w)
    before = w.stock.sum()
    w.stock += P.REGROWTH * (target - w.stock)
    np.maximum(w.stock, 0.0, out=w.stock)
    w.ledger["regrowth"] += float(w.stock.sum() - before)
