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

SCHEMA = 3
READABLE_SCHEMAS = (1, 2, 3)
VERSION = "0.2.0-M1"

CAUSES = ["", "infancy and early childhood", "hunger", "accident or illness",
          "old age", "orphaned infant", "childbirth",
          "flood", "wildfire", "volcanic eruption", "earthquake", "disease outbreak"]   # appended in M1
C = {name: i for i, name in enumerate(CAUSES)}

STREAMS = ["climate", "deaths", "partners", "births", "movement", "fission", "names", "founding",
           "language", "customs", "hazards", "crossing",
           "farming", "surplus"]   # new streams are appended, never inserted

# ids, ticks and cells all fit in 32 bits; people are never removed, so their rows are kept compact
FIELDS = {
    "alive": bool, "sex": np.int8, "cause": np.int8, "name_a": np.int16, "name_b": np.int16,
    "condition": np.float32, "death_cond": np.float32, "death_ratio": np.float32,
    "birth": np.int32, "death": np.int32, "mother": np.int32, "father": np.int32,
    "partner": np.int32, "band": np.int32, "preg_due": np.int32, "preg_father": np.int32,
    "youngest": np.int32, "partner_since": np.int32, "death_bad": np.int32,
    "death_cell": np.int32, "lang": np.int32, "role": np.int8, "wealth": np.float32, "birth_cell": np.int32, "folded": np.int32, "unfolded": np.int32, "death_interv": np.int32, "death_hazard": np.int32,
}
_ZERO_DEFAULT = {"alive", "sex", "cause", "condition", "death_cond", "death_ratio", "role", "wealth"}


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

    languages = None            # set by World: names are spoken in each person's language

    def name(self, i: int) -> str:
        lg = int(self.lang[i])
        if self.languages is not None and lg >= 0 and lg in self.languages:
            from .sim.language import compose_name
            return compose_name(self.languages[lg], int(self.name_a[i]), int(self.name_b[i]), self.sex[i] == 0)
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


@dataclass(slots=True)          # many thousands of bands are kept for history: keep each record small
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
    language: int = 0           # the language this band speaks (sim/language.py)
    village: bool = False       # lives mainly from farming and stays put (sim/farming.py)
    village_since: int = -1
    farming_since: int = -1     # when this people (or the people it split from) first lived mainly by farming
    farm_years: int = 0


_NUM = [("cell", np.int32), ("founded", np.int32), ("parent", np.int32), ("leader", np.int64),
        ("store", np.float64), ("last_ratio", np.float64), ("margin", np.float64), ("ended", np.int32),
        ("group", np.int32), ("fold_tick", np.int32), ("group_deaths", np.int64), ("language", np.int32),
        ("village", np.bool_), ("village_since", np.int32), ("farming_since", np.int32), ("farm_years", np.int32)]
_STR = ["last_move", "mode", "group_name"]
TRAIL_KEEP = 3


class Bands:
    """Every band that ever existed, by id. Living and recently ended bands are Band objects; bands that ended
    long ago are packed into columns (one row per band id) so that millions of past bands take little memory.
    Packed bands are read back as fresh Band objects; they never change again."""

    def __init__(self):
        self.live: dict[int, Band] = {}
        self.cap = 0
        self.packed = np.zeros(0, dtype=np.bool_)
        self.col = {k: np.zeros(0, dtype=t) for k, t in _NUM}
        self.code = {k: np.zeros(0, dtype=np.int32) for k in _STR}
        self.trail = np.zeros((0, TRAIL_KEEP, 2), dtype=np.int64)
        self.trail_n = np.zeros(0, dtype=np.int8)
        self.strings: list[str] = [""]
        self._sid = {"": 0}

    # mapping interface
    def __getitem__(self, i):
        i = int(i)
        b = self.live.get(i)
        if b is not None:
            return b
        if 0 <= i < self.cap and self.packed[i]:
            return self._unpack(i)
        raise KeyError(i)

    def get(self, i, default=None):
        if i is None:
            return default
        try:
            return self[i]
        except (KeyError, TypeError, ValueError):
            return default

    def __setitem__(self, i, b):
        self.live[int(i)] = b

    def __contains__(self, i):
        i = int(i)
        return i in self.live or (0 <= i < self.cap and bool(self.packed[i]))

    def __len__(self):
        return len(self.live) + int(self.packed.sum())

    def values(self):
        """All bands in id order (packed ones rebuilt: slow for very large worlds)."""
        ids = sorted(set(self.live) | set(np.nonzero(self.packed)[0].tolist()))
        return [self[i] for i in ids]

    def _grow(self, n):
        if n <= self.cap:
            return
        cap = max(n, 2 * self.cap, 1024)
        def g(a, shape=None):
            out = np.zeros((cap,) + a.shape[1:], dtype=a.dtype)
            out[:len(a)] = a
            return out
        self.packed = g(self.packed)
        self.col = {k: g(v) for k, v in self.col.items()}
        self.code = {k: g(v) for k, v in self.code.items()}
        self.trail = g(self.trail)
        self.trail_n = g(self.trail_n)
        self.cap = cap

    def _s(self, x: str) -> int:
        k = self._sid.get(x)
        if k is None:
            k = self._sid[x] = len(self.strings)
            self.strings.append(x)
        return k

    def pack(self, before: int):
        """Pack bands that ended before tick `before`."""
        done = [i for i, b in self.live.items() if not b.alive and 0 <= b.ended < before]
        if not done:
            return 0
        self._grow(max(done) + 1)
        for i in done:
            b = self.live.pop(i)
            for k, _ in _NUM:
                self.col[k][i] = getattr(b, k)
            for k in _STR:
                self.code[k][i] = self._s(getattr(b, k))
            tr = b.trail[-TRAIL_KEEP:]
            self.trail_n[i] = len(tr)
            for j, (t, c) in enumerate(tr):
                self.trail[i, j] = (t, c)
            self.packed[i] = True
        return len(done)

    def _unpack(self, i) -> Band:
        b = Band(i, int(self.col["cell"][i]), int(self.col["founded"][i]))
        for k, t in _NUM:
            v = self.col[k][i]
            setattr(b, k, bool(v) if t is np.bool_ else float(v) if t is np.float64 else int(v))
        for k in _STR:
            setattr(b, k, self.strings[int(self.code[k][i])])
        b.alive = False
        b.trail = [(int(t), int(c)) for t, c in self.trail[i, :int(self.trail_n[i])]]
        return b

    # saving
    def arrays(self) -> dict:
        n = int(np.nonzero(self.packed)[0].max()) + 1 if self.packed.any() else 0
        out = {"packed": self.packed[:n], "trail": self.trail[:n], "trail_n": self.trail_n[:n]}
        out.update({"c_" + k: v[:n] for k, v in self.col.items()})
        out.update({"s_" + k: v[:n] for k, v in self.code.items()})
        return out

    def load_arrays(self, d: dict, strings: list):
        n = len(d.get("packed", []))
        self._grow(n)
        if n:
            self.packed[:n] = d["packed"]
            self.trail[:n] = d["trail"]
            self.trail_n[:n] = d["trail_n"]
            for k in self.col:
                self.col[k][:n] = d["c_" + k]
            for k in self.code:
                self.code[k][:n] = d["s_" + k]
        self.strings = list(strings) or [""]
        self._sid = {x: k for k, x in enumerate(self.strings)}


class World:
    """All mutable simulation state. Construct with World.new(world_seed, run_seed)."""

    def __init__(self, planet: Planet, run_seed: int):
        self.planet = planet
        self.world_seed = planet.seed
        self.run_seed = run_seed
        self.t = 0
        ss = np.random.SeedSequence([run_seed, planet.seed, 7919])   # independent histories per planet
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
        self.cell_hunger = np.zeros(n)             # diagnostics: hunger deaths and births recorded per land cell
        self.cell_births = np.zeros(n)
        self.people = People()
        self.bands = Bands()
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
        self._pool = None            # candidate living bands (speed only)
        self.ledger = {"regrowth": 0.0, "harvest": 0.0, "eaten": 0.0, "spoiled": 0.0, "farmed": 0.0}
        self.invariant_failures: list[str] = []
        self.yearly: list[dict] = []
        self.accum = new_accumulators()
        self.season_stats: dict = {}
        self.intervened = False
        self._live = None
        from .sim import customs, farming, language, surplus
        language.init(self)
        customs.init(self)
        farming.init(self)
        surplus.init(self)
        self.people.languages = self.languages
        self.hazards: list = []                    # active hazards (sim/hazards.py)
        self.hazard_food = np.ones(n)              # hazard effect on wild food, recovering over years
        self.hazard_event = -np.ones(n, dtype=np.int64)
        self.immune = np.zeros(n)                  # share of a cell's people immune to the last outbreak
        self.timing: dict = {}

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
        if parent >= 0:
            b.language = self.bands[parent].language
            b.farming_since = self.bands[parent].farming_since
        from .sim import customs, farming, surplus
        customs.ensure(self, b.id, parent)
        farming.ensure(self, b.id, parent)
        surplus.ensure(self, b.id, parent)
        self.bands[b.id] = b
        if self._pool is not None:
            self._pool[b.id] = b
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
            # bands never come back to life, so only bands alive at the last rebuild (plus new ones) need checking
            if self._pool is None:
                self._pool = dict(self.bands.live)
            self._living = [b for b in self._pool.values() if b.alive]
            self._pool = {b.id: b for b in self._living}
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
        p.lang[ids] = [self.bands[int(x)].language for x in band]
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
