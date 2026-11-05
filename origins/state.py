"""World state: plain data plus small helpers. Systems live in origins.sim.

People are stored as arrays (one row per person, ids never reused). Births,
deaths and partnerships are recorded on the person rows themselves; the
event log holds rarer events (bad years, splits, merges, discoveries,
interventions). Both are joined by origins.explain into one causal history.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import names as N
from . import params as P
from .worldgen import Planet, generate

SCHEMA = 1
VERSION = "0.1.0-M0"

CAUSES = ["", "infancy and early childhood", "hunger", "accident or illness",
          "old age", "orphaned infant", "childbirth"]
C = {name: i for i, name in enumerate(CAUSES)}

STREAMS = ["climate", "deaths", "partners", "births", "movement", "fission", "names", "founding"]

FIELDS = {
    "alive": bool, "sex": np.int8, "cause": np.int8, "name_a": np.int16, "name_b": np.int16,
    "condition": np.float32, "death_cond": np.float32, "death_ratio": np.float32,
    "birth": np.int64, "death": np.int64, "mother": np.int64, "father": np.int64,
    "partner": np.int64, "band": np.int64, "preg_due": np.int64, "preg_father": np.int64,
    "youngest": np.int64, "partner_since": np.int64, "death_bad": np.int64,
    "death_cell": np.int64, "birth_cell": np.int64, "folded": np.int64, "unfolded": np.int64, "death_interv": np.int64,
}
_ZERO_DEFAULT = {"alive", "sex", "cause", "condition", "death_cond", "death_ratio"}


class People:
    def __init__(self, capacity: int = 1024):
        self.n = 0
        for f, dt in FIELDS.items():
            setattr(self, f, self._blank(f, dt, capacity))

    @staticmethod
    def _blank(f, dt, cap):
        return np.zeros(cap, dtype=dt) if f in _ZERO_DEFAULT else np.full(cap, -1, dtype=dt)

    def _grow(self, need: int):
        cap = len(self.alive)
        while cap < need:
            cap *= 2
        for f, dt in FIELDS.items():
            old = getattr(self, f)
            new = self._blank(f, dt, cap)
            new[:len(old)] = old
            setattr(self, f, new)

    def add_many(self, k: int) -> np.ndarray:
        if self.n + k > len(self.alive):
            self._grow(self.n + k)
        ids = np.arange(self.n, self.n + k)
        self.n += k
        return ids

    def name(self, i: int) -> str:
        return N.render(int(self.name_a[i]), int(self.name_b[i]), self.sex[i] == 0)

    def arrays(self) -> dict:
        return {f: getattr(self, f)[:self.n].copy() for f in FIELDS}

    @classmethod
    def from_arrays(cls, d: dict) -> "People":
        n = len(d["alive"])
        p = cls(1024)
        if n > len(p.alive):
            p._grow(n)
        for f in FIELDS:
            if f in d:                           # fields added later keep their defaults
                getattr(p, f)[:n] = d[f]
        p.n = n
        return p


@dataclass
class Band:
    id: int
    cell: int
    founded: int
    parent: int = -1
    leader: int = -1            # eldest member at founding, gives the band its name
    store: float = 0.0
    last_ratio: float = 1.0
    margin: float = 1.6         # recent food gathered / food needed (before eating)
    alive: bool = True
    ended: int = -1
    last_move: str = ""
    mode: str = "individual"    # or "group" (counts by age and sex; see sim/groups.py)
    group: int = -1
    fold_tick: int = -1
    group_name: str = ""
    group_deaths: int = 0
    trail: list = field(default_factory=list)   # recent (tick, cell), newest last


class World:
    """All mutable simulation state. Construct with World.new(world_seed, run_seed)."""

    def __init__(self, planet: Planet, run_seed: int):
        self.planet = planet
        self.world_seed = planet.seed
        self.run_seed = run_seed
        self.t = 0
        ss = np.random.SeedSequence([run_seed, 7919])
        self.rng = {name: np.random.default_rng(s) for name, s in zip(STREAMS, ss.spawn(len(STREAMS)))}
        n = planet.n
        self.stock = np.zeros(n)
        self.known = np.zeros(n, dtype=bool)
        self.discovered_by = -np.ones(n, dtype=np.int64)
        self.discovered_at = -np.ones(n, dtype=np.int64)
        self.region_z = np.zeros(planet.n_regions)
        self.region_factor = np.ones(planet.n_regions)
        self.region_bad_event = -np.ones(planet.n_regions, dtype=np.int64)
        self.food_modifier = np.ones(n)            # observer interventions only
        self.intervention_event = -np.ones(n, dtype=np.int64)
        self.pending_restore: list = []
        self.people = People()
        self.bands: dict[int, Band] = {}
        self.next_band = 0
        self.events: list[dict] = []
        self.counts = {"founders": 0, "births": 0, "deaths": 0, "births_ind": 0,
                       "folded": 0, "unfolded": 0}
        from .sim.groups import Groups
        self.groups = Groups()
        self.follow = -1
        self.reveal_pending: set = set()
        self._binfo = None
        self._living = None
        self.ledger = {"regrowth": 0.0, "harvest": 0.0, "eaten": 0.0, "spoiled": 0.0}
        self.invariant_failures: list[str] = []
        self.yearly: list[dict] = []
        self.accum = new_accumulators()
        self.season_stats: dict = {}
        self.intervened = False
        self._live = None

    # ------------------------------------------------------------------ time
    @property
    def year(self) -> int:
        return self.t // P.TICKS_PER_YEAR

    @property
    def quarter(self) -> int:
        return self.t % P.TICKS_PER_YEAR

    @property
    def years_bp(self) -> int:
        return P.START_YEARS_BP - self.year

    def ages(self, idx) -> np.ndarray:
        return (self.t - self.people.birth[idx]) / P.TICKS_PER_YEAR

    def alive_idx(self) -> np.ndarray:
        if self._live is None:
            self._live = np.nonzero(self.people.alive[:self.people.n])[0]
        return self._live

    def people_changed(self):
        self._live = None

    # ---------------------------------------------------------------- events
    def event(self, kind: str, cell: int = -1, band: int = -1, person: int = -1,
              causes: list | None = None, **data) -> int:
        eid = len(self.events)
        self.events.append({"id": eid, "t": self.t, "kind": kind, "cell": int(cell),
                            "band": int(band), "person": int(person),
                            "causes": causes or [], "data": data})
        return eid

    # ----------------------------------------------------------------- bands
    def new_band(self, cell: int, parent: int = -1, leader: int = -1) -> Band:
        b = Band(self.next_band, int(cell), self.t, parent, leader)
        b.trail.append((self.t, int(cell)))
        self.bands[b.id] = b
        self.reveal_pending.add(b.id)
        self._living = None
        self.next_band += 1
        return b

    def band_name(self, b: Band) -> str:
        if b.group_name:
            return b.group_name
        return f"Band of {self.people.name(b.leader)}" if b.leader >= 0 else f"Band {b.id}"

    def living_bands(self):
        if self._living is None:
            self._living = [b for b in self.bands.values() if b.alive]
        return self._living

    def bands_changed(self):
        self._living = None

    def band_sizes(self) -> np.ndarray:
        """People per band id, individuals plus group counts."""
        from .sim import groups
        idx = self.alive_idx()
        out = np.bincount(self.people.band[idx], minlength=self.next_band).astype(float)
        return out + groups.sizes(self)

    def population(self) -> int:
        from .sim import groups
        return int(len(self.alive_idx()) + round(groups.sizes(self).sum()))

    def members(self, band_id: int) -> np.ndarray:
        idx = self.alive_idx()
        return idx[self.people.band[idx] == band_id]

    def add_people(self, sex: np.ndarray, mother: np.ndarray, father: np.ndarray,
                   band: np.ndarray, condition: np.ndarray, cell: np.ndarray) -> np.ndarray:
        p = self.people
        k = len(sex)
        ids = p.add_many(k)
        rng = self.rng["names"]
        p.alive[ids] = True
        p.sex[ids] = sex
        p.birth[ids] = self.t
        p.mother[ids] = mother
        p.father[ids] = father
        p.band[ids] = band
        p.condition[ids] = condition
        p.birth_cell[ids] = cell
        for i in ids:
            a, b = N.draw(rng)
            p.name_a[i], p.name_b[i] = a, b
        self.people_changed()
        return ids

    @classmethod
    def new(cls, world_seed: int, run_seed: int, planet: Planet | None = None) -> "World":
        planet = planet or generate(world_seed)
        w = cls(planet, run_seed)
        from .sim import climate, founding
        climate.init(w)
        founding.found(w)
        return w


def new_accumulators():
    # age groups: 0, 1-4, 5-9, ..., 75-79, 80+ (18 groups); fertility 15-19 .. 45-49 (7 groups)
    return {"person_years": np.zeros(18), "deaths": np.zeros(18),
            "woman_years": np.zeros(7), "births_by_age": np.zeros(7),
            "deaths_by_cause": np.zeros(len(CAUSES)), "band_sizes": []}


def age_group(age: np.ndarray) -> np.ndarray:
    age = np.asarray(age, dtype=float)
    g = np.where(age < 1, 0, np.where(age < 5, 1, np.minimum(2 + ((age - 5) // 5), 17)))
    return g.astype(np.int64)
