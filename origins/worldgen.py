"""Planet generation from a seed.

Everything here is a deterministic function of the world seed, so a world is
never saved: it is regenerated and checked against a stored fingerprint.
Numbers are synthetic starting values, not measurements of Earth.
"""
from __future__ import annotations

import hashlib
import heapq
from dataclasses import dataclass, field

import numpy as np

from .grid import Grid
from .noise import Noise3

EARTH_RADIUS_KM = 6371.0
GRID_LEVEL = 6                         # 40,962 cells
PLANET_RADIUS_KM = EARTH_RADIUS_KM / 2  # a quarter of Earth's surface area
LAND_FRACTION = 0.30

BIOMES = ["ocean", "ice", "tundra", "boreal_forest", "temperate_forest",
          "grassland", "desert", "savanna", "tropical_forest", "alpine", "lake"]
B = {name: i for i, name in enumerate(BIOMES)}

# Sustainable forager population per cell (about 3,100 km2) before water bonuses.
# Starting values to be tuned; they imply roughly 0.004-0.07 people per km2.
FORAGE_CAPACITY = {
    "ocean": 0, "ice": 0, "tundra": 20, "boreal_forest": 55,
    "temperate_forest": 150, "grassland": 130, "desert": 10,
    "savanna": 200, "tropical_forest": 110, "alpine": 18, "lake": 0,
}

MINERALS = ["flint", "clay", "salt", "copper", "tin", "iron", "coal", "gold"]
DOMESTICABLES = ["wild_grain", "wild_legume", "wild_tuber", "wild_rice",
                 "wild_goat", "wild_sheep", "wild_cattle", "wild_pig", "wild_horse"]


@dataclass
class Planet:
    seed: int
    grid: Grid
    elevation: np.ndarray            # metres, negative under the sea
    land: np.ndarray                 # bool
    lake: np.ndarray                 # bool
    downstream: np.ndarray           # cell index or -1
    flow: np.ndarray                 # accumulated runoff (relative units)
    river: np.ndarray                # bool
    coast: np.ndarray                # bool, land next to ocean
    temp_mean: np.ndarray            # degC, annual mean
    temp_season: np.ndarray          # (n, 4) degC; seasons 0=spring..3=winter (northern calendar)
    rain: np.ndarray                 # mm/year
    biome: np.ndarray                # int
    capacity: np.ndarray             # forager people per cell
    season_food: np.ndarray          # (n, 4) relative seasonal productivity, mean 1 over the year
    region: np.ndarray               # climate-variability region per cell
    n_regions: int
    minerals: dict = field(default_factory=dict)       # name -> bool array (unused in M0)
    domesticables: dict = field(default_factory=dict)  # name -> bool array (unused in M0)
    plate: np.ndarray = None         # tectonic plate per cell
    convergence: np.ndarray = None   # >0 plates moving together at this cell's boundary, <0 apart
    volcanic: np.ndarray = None      # bool: volcanic belt (convergent boundaries, rifts, hotspots)
    seismic: np.ndarray = None       # bool: earthquake zone (plate boundaries)
    start_cell: int = -1
    fingerprint: str = ""

    @property
    def n(self):
        return self.grid.n


def _priority_flood(grid: Grid, elev: np.ndarray, land: np.ndarray):
    """Fill depressions; return filled elevation, drainage parent, pop order."""
    n = grid.n
    filled = elev.copy()
    parent = -np.ones(n, dtype=np.int64)
    done = np.zeros(n, dtype=bool)
    heap = []
    nb = grid.neighbours
    ocean = ~land
    done[ocean] = True
    # seed with land cells touching the ocean
    for c in np.nonzero(land)[0]:
        ns = nb[c][nb[c] >= 0]
        oc = ns[ocean[ns]]
        if len(oc):
            parent[c] = int(oc[np.argmin(elev[oc])])
            heapq.heappush(heap, (float(filled[c]), int(c)))
            done[c] = True
    order = []
    eps = 0.01
    while heap:
        h, c = heapq.heappop(heap)
        order.append(c)
        for m in nb[c]:
            if m < 0 or done[m]:
                continue
            done[m] = True
            if filled[m] <= h:
                filled[m] = h + eps
            parent[m] = c
            heapq.heappush(heap, (float(filled[m]), int(m)))
    # land cells never reached (none expected) drain nowhere
    return filled, parent, np.array(order, dtype=np.int64)


def generate(seed: int, level: int = GRID_LEVEL, radius_km: float = PLANET_RADIUS_KM) -> Planet:
    grid = Grid(level, radius_km)
    n = grid.n
    rng = np.random.default_rng([seed, 1])
    xyz = grid.xyz
    nz = Noise3(int(rng.integers(2**31)))

    # --- Elevation: low-frequency continents + detail + ridged mountain belts
    warp = np.stack([nz.fbm(xyz * 1.0 + 3.1 * k, octaves=2, freq=1.2) for k in range(3)], axis=1)
    p = xyz + 0.35 * warp
    continents = nz.fbm(p, octaves=4, freq=1.1)
    detail = nz.fbm(p, octaves=5, freq=4.0)
    ridges = nz.fbm(p + 9.7, octaves=4, freq=2.2, ridged=True)
    raw = continents + 0.35 * detail
    sea = np.quantile(raw, 1 - LAND_FRACTION)
    land = raw > sea
    above = np.clip(raw - sea, 0, None)
    above = above / max(above.max(), 1e-9)
    plates = _plates(grid, seed, nz)
    # mountains rise where plates converge; ridged noise gives them shape
    uplift = plates["uplift"]
    mountain = np.clip(uplift * (0.55 + 0.45 * ridges), 0, 1)
    elevation = np.where(land, 40 + 2000 * above ** 1.3 + 6500 * mountain ** 1.3 * np.clip(above * 6 + 0.35, 0, 1),
                         -4000 * np.clip((sea - raw) / max(sea - raw.min(), 1e-9), 0, 1) ** 0.6)

    # --- Coast, distance to ocean (in cells) by breadth-first search
    nb = grid.neighbours
    ocean = ~land
    dist = np.full(n, 10**6, dtype=np.int64)
    dist[ocean] = 0
    frontier = np.nonzero(ocean)[0]
    d = 0
    while len(frontier):
        d += 1
        cand = nb[frontier].ravel()
        cand = cand[cand >= 0]
        cand = np.unique(cand)
        cand = cand[dist[cand] > d]
        dist[cand] = d
        frontier = cand
    coast = land & (dist == 1)

    # --- Temperature
    alat = np.abs(grid.lat)
    t_sea = 27.0 - 45.0 * (alat / 90.0) ** 1.5
    t_mean = t_sea - 6.5 * np.clip(elevation, 0, None) / 1000.0
    continental = np.clip(dist / 8.0, 0, 1)
    amp = (1.5 + 22.0 * (alat / 90.0)) * (0.45 + 0.55 * continental)
    sign = np.where(grid.lat >= 0, 1.0, -1.0)
    offsets = np.array([0.0, 1.0, 0.0, -1.0])           # spring, summer, autumn, winter (north)
    temp_season = t_mean[:, None] + amp[:, None] * sign[:, None] * offsets[None, :]

    # --- Rainfall: latitude bands carried by prevailing winds, with rain shadows
    lat = grid.lat
    base = (250 + 2000 * np.exp(-(lat / 12.0) ** 2) + 900 * np.exp(-((alat - 50) / 15.0) ** 2))
    base *= 1 - 0.75 * np.exp(-((alat - 27) / 9.0) ** 2)
    east, north = grid.east_north()
    # wind blows FROM upwind; easterlies in tropics and polar, westerlies in mid-latitudes
    wind_from_east = (alat < 30) | (alat > 60)
    upwind_dir = np.where(wind_from_east[:, None], east, -east)
    nbv = np.where(nb[..., None] >= 0, xyz[np.clip(nb, 0, None)] - xyz[:, None, :], 0.0)
    score = (nbv * upwind_dir[:, None, :]).sum(2)
    score[nb < 0] = -np.inf
    upwind = nb[np.arange(n), np.argmax(score, axis=1)]
    moisture = np.where(ocean, 1.0, 0.0)
    for _ in range(40):
        up = moisture[upwind]
        climb = np.clip(elevation - elevation[upwind], 0, None)
        carried = up * 0.96 * np.exp(-climb / 1500.0)
        moisture = np.where(ocean, 1.0, np.maximum(carried, 0.05))
    windward = np.clip((elevation - elevation[upwind]) / 1000.0, 0, 1)
    rain = base * (0.2 + 0.8 * moisture) * (1 + 0.5 * windward)
    rain = np.where(land, rain, base)

    # --- Rivers and lakes
    filled, parent, order = _priority_flood(grid, elevation, land)
    lake = land & (filled - elevation > 25.0)
    runoff = np.where(land, np.clip(rain - 200, 0, None), 0.0)
    flow = runoff.copy()
    for c in order[::-1]:
        p_ = parent[c]
        if p_ >= 0 and land[p_]:
            flow[p_] += flow[c]
    land_flow = flow[land]
    river = land & (flow > np.quantile(land_flow, 0.93)) & ~lake
    downstream = np.where(land, parent, -1)

    # --- Biomes
    biome = np.full(n, B["ocean"], dtype=np.int64)
    T, P = t_mean, rain
    lb = np.full(n, B["temperate_forest"], dtype=np.int64)
    lb[T < -12] = B["ice"]
    lb[(T >= -12) & (T < -2)] = B["tundra"]
    m = (T >= -2) & (T < 4)
    lb[m & (P >= 250)] = B["boreal_forest"]
    lb[m & (P < 250)] = B["tundra"]
    m = (T >= 4) & (T < 18)
    lb[m & (P < 250)] = B["desert"]
    lb[m & (P >= 250) & (P < 600)] = B["grassland"]
    lb[m & (P >= 600)] = B["temperate_forest"]
    m = T >= 18
    lb[m & (P < 250)] = B["desert"]
    lb[m & (P >= 250) & (P < 1000)] = B["savanna"]
    lb[m & (P >= 1000)] = B["tropical_forest"]
    lb[(elevation > 2600) & (T >= -12)] = B["alpine"]
    biome = np.where(land, lb, biome)
    biome = np.where(lake, B["lake"], biome)

    # --- Forager capacity and seasonal productivity
    cap_by_biome = np.array([FORAGE_CAPACITY[b] for b in BIOMES], dtype=float)
    capacity = cap_by_biome[biome]
    capacity *= np.where(river, 1.6, 1.0) * np.where(coast, 1.5, 1.0)
    lake_adj = np.zeros(n, dtype=bool)
    for k in range(6):
        nk = nb[:, k]
        lake_adj |= (nk >= 0) & lake[np.clip(nk, 0, None)]
    capacity *= np.where(land & ~lake & lake_adj, 1.4, 1.0)
    capacity = np.where(land & ~lake, capacity, 0.0)
    growth = np.clip((temp_season + 2.0) / 16.0, 0.08, 1.25)
    season_food = growth / growth.mean(axis=1, keepdims=True)

    # --- Climate-variability regions (nearest of ~160 random sphere points)
    n_regions = 160
    pts = rng.normal(size=(n_regions, 3))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    region = np.argmax(xyz @ pts.T, axis=1)

    # --- Minerals and domesticable species (generated now, unused in M0)
    minerals = {}
    for name in MINERALS:
        f = Noise3(int(rng.integers(2**31))).fbm(xyz, octaves=3, freq=3.0)
        thresh = np.quantile(f[land], 0.85 if name in ("flint", "clay") else 0.95)
        minerals[name] = land & (f > thresh)
    domesticables = {}
    suited = {
        "wild_grain": (B["grassland"], B["temperate_forest"], B["savanna"]),
        "wild_legume": (B["grassland"], B["temperate_forest"]),
        "wild_tuber": (B["tropical_forest"], B["savanna"], B["alpine"]),
        "wild_rice": (B["tropical_forest"], B["savanna"]),
        "wild_goat": (B["alpine"], B["grassland"]),
        "wild_sheep": (B["alpine"], B["grassland"]),
        "wild_cattle": (B["grassland"], B["savanna"], B["temperate_forest"]),
        "wild_pig": (B["temperate_forest"], B["tropical_forest"]),
        "wild_horse": (B["grassland"], B["tundra"]),
    }
    for name, biomes in suited.items():
        f = Noise3(int(rng.integers(2**31))).fbm(xyz, octaves=2, freq=1.6)
        ok = np.isin(biome, biomes)
        thresh = np.quantile(f, 0.80)
        domesticables[name] = ok & (f > thresh)

    planet = Planet(seed, grid, elevation, land & ~lake, lake, downstream, flow, river, coast,
                    t_mean, temp_season, rain, biome, capacity, season_food, region, n_regions,
                    minerals, domesticables)
    planet.plate = plates["plate"]
    planet.convergence = plates["convergence"]
    planet.volcanic = plates["volcanic"]
    planet.seismic = plates["seismic"]
    planet.start_cell = _choose_start(planet, rng)
    planet.fingerprint = fingerprint(planet)
    return planet


N_PLATES = 14


def _plates(grid: Grid, seed: int, nz) -> dict:
    """A simple plate model: irregular plates, each rotating about its own axis.

    Boundary cells where plates converge get uplift (mountains) and, where
    convergence is strong, volcanoes (as at subduction zones); diverging
    boundaries (rifts) get weaker volcanism; a few hotspots sit inside plates.
    Every boundary is an earthquake zone. A cartoon of plate tectonics, not a
    geophysical model.
    """
    rng = np.random.default_rng([seed, 2])
    xyz = grid.xyz
    nb = grid.neighbours
    n = grid.n
    centres = rng.normal(size=(N_PLATES, 3))
    centres /= np.linalg.norm(centres, axis=1, keepdims=True)
    wobble = np.stack([Noise3(int(rng.integers(2**31))).fbm(xyz, octaves=3, freq=2.5) for _ in range(N_PLATES)], axis=1)
    plate = np.argmax(xyz @ centres.T + 0.25 * wobble, axis=1)
    axes = rng.normal(size=(N_PLATES, 3))
    axes /= np.linalg.norm(axes, axis=1, keepdims=True)
    speed = rng.uniform(0.3, 1.0, size=N_PLATES)
    vel = np.cross(axes[plate] * speed[plate, None], xyz)            # velocity of each cell's plate there
    conv = np.zeros(n)
    boundary = np.zeros(n, dtype=bool)
    for k in range(6):
        m = nb[:, k]
        ok = (m >= 0)
        mm = np.clip(m, 0, None)
        diff = ok & (plate[mm] != plate)
        boundary |= diff
        normal = xyz[mm] - xyz
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        rel = ((vel - vel[mm]) * normal).sum(1)                     # >0: this cell moves toward the neighbour
        c = np.where(diff, rel, 0.0)
        conv = np.where(np.abs(c) > np.abs(conv), c, conv)
    # spread uplift a few cells into the overriding side
    up = np.clip(conv, 0, None)
    up = up / max(up.max(), 1e-9)
    field = up.copy()
    for _ in range(3):
        nbmax = np.max(np.where(nb >= 0, field[np.clip(nb, 0, None)], 0.0), axis=1)
        field = np.maximum(field, 0.7 * nbmax)
    volcanic = boundary & (conv > np.quantile(conv[boundary], 0.55)) if boundary.any() else boundary
    rift = boundary & (conv < np.quantile(conv[boundary], 0.15)) if boundary.any() else boundary
    hotspots = rng.choice(n, size=4, replace=False)
    volcanic = volcanic | rift
    volcanic[hotspots] = True
    seismic = boundary.copy()
    for k in range(6):
        m = nb[:, k]
        seismic |= (m >= 0) & boundary[np.clip(m, 0, None)]
    return {"plate": plate, "convergence": conv, "uplift": field, "volcanic": volcanic, "seismic": seismic}


def _choose_start(p: Planet, rng) -> int:
    """A habitable, moderately rich cell with fresh water: not best, not worst."""
    cap = p.capacity
    nb = p.grid.neighbours
    nbcap = np.where(nb >= 0, cap[np.clip(nb, 0, None)], 0.0).sum(1)
    water = p.river | p.lake.any() & np.zeros(p.n, bool)
    water = p.river.copy()
    for k in range(6):
        nk = nb[:, k]
        water |= (nk >= 0) & p.lake[np.clip(nk, 0, None)]
    ok = p.land & (cap > 0) & water & (np.abs(p.grid.lat) < 50) & (nbcap > 0)
    if not ok.any():
        ok = p.land & (cap > 0)
    idx = np.nonzero(ok)[0]
    score = cap[idx] + 0.3 * nbcap[idx] / 6
    lo, hi = np.quantile(score, [0.45, 0.8])
    mid = idx[(score >= lo) & (score <= hi)]
    if len(mid) == 0:
        mid = idx
    return int(rng.choice(mid))


def fingerprint(p: Planet) -> str:
    """Identifies the planet a save belongs to. Elevation and capacity are rounded first: different processors
    (GitHub's machines are of more than one kind) compute the same planet with differences in the last few
    digits (about 1e-12 m of elevation), which change nothing else on the planet."""
    h = hashlib.sha256()
    for arr in (np.round(p.elevation, 3), p.biome, np.round(p.capacity, 6), p.river, p.region, p.plate, p.volcanic):
        h.update(np.ascontiguousarray(arr).tobytes())
    h.update(str(p.start_cell).encode())
    return h.hexdigest()[:16]


def legacy_fingerprint(p: Planet) -> str:
    """The fingerprint used before November 2026 (exact to the last digit), so older saves still load."""
    h = hashlib.sha256()
    for arr in (p.elevation, p.biome, p.capacity, p.river, p.region, p.plate, p.volcanic):
        h.update(np.ascontiguousarray(arr).tobytes())
    h.update(str(p.start_cell).encode())
    return h.hexdigest()[:16]
