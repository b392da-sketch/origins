"""Group-mode bands: people as counts by sex and single year of age.

Above the individual threshold (about 20,000 people), bands far from the
observer's focus are folded into groups. A group uses the same food,
mortality and fertility rules as individuals, applied to counts, so the
world's demography is continuous across the switch. A followed group can be
unfolded back into named individuals.

Approximations relative to individuals (documented, tested statistically):
partnership is a share of women rather than named couples; nursing is
estimated from the number of infants; orphaned-infant risk is folded into
early-childhood risk; groups exchange partners only through merging.
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..state import C, age_group

AGES = 90
_age = np.arange(AGES) + 0.5
PARTNERED_SHARE = 0.85      # share of women 15-49 with a partner (measured from individual runs)


def _tables():
    need_f = P.need(_age, np.zeros(AGES, int), np.zeros(AGES, bool), np.zeros(AGES, bool))
    need_m = P.need(_age, np.ones(AGES, int), np.zeros(AGES, bool), np.zeros(AGES, bool))
    work = P.work(_age, np.zeros(AGES, bool))
    return need_f, need_m, work


NEED_F, NEED_M, WORK = _tables()
AGE_GROUP = age_group(_age)


class Groups:
    """Arrays indexed by group row; band.group gives the row. Rows are never reused."""

    KEYS = ("F", "M", "preg", "cond_child", "cond_rest", "band", "active")

    def __init__(self):
        self.n = 0
        self._alloc(64)

    def _alloc(self, cap):
        old = {k: getattr(self, "_" + k, None) for k in self.KEYS}
        self._F = np.zeros((cap, AGES))
        self._M = np.zeros((cap, AGES))
        self._preg = np.zeros((cap, P.PREGNANCY_TICKS))
        self._cond_child = np.zeros(cap)
        self._cond_rest = np.zeros(cap)
        self._band = np.full(cap, -1, dtype=np.int64)
        self._active = np.zeros(cap, dtype=bool)
        for k, v in old.items():
            if v is not None:
                getattr(self, "_" + k)[:len(v)] = v

    # views onto the used part
    F = property(lambda s: s._F[:s.n])
    M = property(lambda s: s._M[:s.n])
    preg = property(lambda s: s._preg[:s.n])
    cond_child = property(lambda s: s._cond_child[:s.n])
    cond_rest = property(lambda s: s._cond_rest[:s.n])
    band = property(lambda s: s._band[:s.n])
    active = property(lambda s: s._active[:s.n])

    def add(self, band_id, F, M, preg, cc, cr) -> int:
        if self.n == len(self._active):
            self._alloc(2 * len(self._active))
        g = self.n
        self.n += 1
        self._F[g], self._M[g], self._preg[g] = F, M, preg
        self._cond_child[g], self._cond_rest[g] = cc, cr
        self._band[g], self._active[g] = band_id, True
        return g

    def total(self, g) -> float:
        return float(self.F[g].sum() + self.M[g].sum())

    def rows(self):
        return np.nonzero(self.active)[0]

    def arrays(self):
        return {k: getattr(self, k).copy() for k in self.KEYS}

    def compact(self) -> dict:
        """Drop inactive rows (memory only: active rows keep their order). Returns old row -> new row."""
        rows = self.rows()
        old = {k: getattr(self, k)[rows].copy() for k in self.KEYS}
        self.n = 0
        self._F = None
        for k in self.KEYS:
            setattr(self, "_" + k, None)
        self._alloc(max(64, 2 * len(rows)))
        for k in self.KEYS:
            getattr(self, "_" + k)[:len(rows)] = old[k]
        self.n = len(rows)
        return {int(r): i for i, r in enumerate(rows)}

    @classmethod
    def from_arrays(cls, d):
        g = cls()
        n = len(d["active"])
        g._alloc(max(64, n))
        g.n = n
        for k in cls.KEYS:
            getattr(g, "_" + k)[:n] = d[k]
        return g


def compact(w):
    """Every so often, drop the rows of groups that have ended, and pack the records of bands that ended more than
    ten years ago into compact columns (results are unchanged)."""
    for b in w.bands.live.values():
        if not b.alive and 0 <= b.ended < w.t - 40:
            b.group = -1                  # an ended band has no group rows
    w.bands.pack(w.t - 40)
    G = w.groups
    live = int(G.active.sum())
    if G.n - live < max(2000, live):
        return
    remap = G.compact()
    for b in w.bands.live.values():
        if b.group >= 0:
            b.group = remap.get(b.group, -1)


def sizes(w) -> np.ndarray:
    out = np.zeros(w.next_band)
    G = w.groups
    rows = G.rows()
    if len(rows):
        np.add.at(out, G.band[rows], G.F[rows].sum(1) + G.M[rows].sum(1))
    return out


# ------------------------------------------------------------ food
def needs_and_work(w):
    """Per band: need of children (<5), need of others, foraging effort (all per season)."""
    G = w.groups
    nb = w.next_band
    nc, nr, ef = np.zeros(nb), np.zeros(nb), np.zeros(nb)
    rows = G.rows()
    if len(rows) == 0:
        return nc, nr, ef
    F, M = G.F[rows], G.M[rows]
    child = _age < 5
    infants = F[:, :2].sum(1) + M[:, :2].sum(1)
    preg = G.preg[rows].sum(1)
    extra = 0.15 * preg + 0.25 * infants
    need_c = (F[:, child] @ NEED_F[child] + M[:, child] @ NEED_M[child]) * P.SEASON_DAYS
    need_r = (F[:, ~child] @ NEED_F[~child] + M[:, ~child] @ NEED_M[~child] + extra) * P.SEASON_DAYS
    work = (F @ WORK + M @ WORK - 0.3 * infants) * P.SEASON_DAYS * P.FORAGE_RATE
    b = G.band[rows]
    nc[b] += need_c
    nr[b] += need_r
    ef[b] += np.maximum(work, 0)
    return nc, nr, ef


def update_condition(w, frac_child, frac_rest):
    G = w.groups
    rows = G.rows()
    if len(rows) == 0:
        return
    b = G.band[rows]
    for arr, frac in ((G.cond_child, frac_child[b]), (G.cond_rest, frac_rest[b])):
        c = arr[rows]
        arr[rows] = np.where(frac >= 1 - 1e-9, np.minimum(1.0, c + P.CONDITION_GAIN),
                             np.maximum(0.0, c - P.CONDITION_LOSS * (1 - frac)))


# ------------------------------------------------------------ demography
def _hazards(cond_child, cond_rest):
    a = _age
    base = P.SILER_A1 * np.exp(-P.SILER_B1 * a), np.full(AGES, P.SILER_A2), P.SILER_A3 * np.exp(P.SILER_B3 * a)
    vuln = np.where((a < 5) | (a >= 60), P.HUNGER_VULNERABLE, 1.0)
    cond = np.where(a < 5, cond_child[:, None], cond_rest[:, None])
    hun = P.HUNGER_HAZARD * np.clip((P.HUNGER_ONSET - cond) / P.HUNGER_ONSET, 0, 1) ** P.HUNGER_POWER * vuln
    inf = base[0][None] + 0.004 * (a < 1)          # orphaned-infant risk folded in
    return np.stack(np.broadcast_arrays(inf, base[1][None], base[2][None], hun), axis=0)


def deaths(w):
    G = w.groups
    rows = G.rows()
    if len(rows) == 0:
        return
    rng = w.rng["deaths"]
    comps = _hazards(G.cond_child[rows], G.cond_rest[rows])       # (4, n, AGES): infancy, accident, old age, hunger
    total = comps.sum(0)
    prob = 1 - np.exp(-total / P.TICKS_PER_YEAR)
    acc = w.accum
    cause_codes = [C["infancy and early childhood"], C["accident or illness"], C["old age"], C["hunger"]]
    hunger_rows = np.zeros(len(rows), dtype=np.int64)
    for X in (G.F, G.M):
        counts = np.rint(X[rows]).astype(np.int64)
        acc["person_years"] += np.bincount(AGE_GROUP, weights=counts.sum(0), minlength=18) / P.TICKS_PER_YEAR
        nz = np.nonzero(counts)
        d = rng.binomial(counts[nz], prob[nz])
        hit = d > 0
        if not hit.any():
            continue
        r_i, a_i, d = nz[0][hit], nz[1][hit], d[hit]
        n = int(d.sum())
        X[rows[r_i], a_i] -= d
        rem = d
        for k in range(3):
            ck = comps[k][r_i, a_i]
            frac = np.clip(ck / np.maximum(comps[k:, r_i, a_i].sum(0), 1e-12), 0, 1)
            byk = rng.binomial(rem, frac)
            acc["deaths_by_cause"][cause_codes[k]] += byk.sum()
            rem = rem - byk
        acc["deaths_by_cause"][cause_codes[3]] += rem.sum()
        np.add.at(hunger_rows, r_i, rem)
        w.counts["deaths"] += n
        acc["deaths"] += np.bincount(AGE_GROUP[a_i], weights=d, minlength=18)
    row_cells = np.array([w.bands[int(b)].cell for b in G.band[rows]], dtype=np.int64)
    np.add.at(w.cell_hunger, row_cells, hunger_rows)
    size = G.F[rows].sum(1) + G.M[rows].sum(1) + hunger_rows
    w.counts["group_hunger_deaths"] = w.counts.get("group_hunger_deaths", 0) + int(hunger_rows.sum())
    for k in np.nonzero(hunger_rows > P.GROUP_HUNGER_EVENT * np.maximum(size, 1))[0]:
        r = rows[k]
        b = w.bands[int(G.band[r])]
        causes_ = [{"note": f"{w.band_name(b)} received {b.last_ratio:.0%} of its food needs; "
                            f"body condition {G.cond_rest[r]:.2f} (adults), {G.cond_child[r]:.2f} (children)"}]
        bad = w.region_bad_event[w.planet.region[b.cell]]
        if bad >= 0:
            causes_.append({"event": int(bad)})
        if w.intervention_event[b.cell] >= 0:
            causes_.append({"event": int(w.intervention_event[b.cell])})
        w.event("group_hunger_deaths", cell=b.cell, band=b.id, causes=causes_, deaths=int(hunger_rows[k]))


def births(w):
    G = w.groups
    rows = G.rows()
    if len(rows) == 0:
        return
    rng = w.rng["births"]
    # deliveries
    due = G.preg[rows, 0].copy()
    G.preg[rows, :-1] = G.preg[rows, 1:]
    G.preg[rows, -1] = 0
    n_due = np.rint(due).astype(np.int64)
    if n_due.sum():
        girls = rng.binomial(n_due, 0.5)
        G.F[rows, 0] += girls
        G.M[rows, 0] += n_due - girls
        w.counts["births"] += int(n_due.sum())
        vill = w.farm_share[G.band[rows]] >= 0.5
        w.counts["births_village"] = w.counts.get("births_village", 0) + int(n_due[vill].sum())
        w.counts["births_forager"] = w.counts.get("births_forager", 0) + int(n_due[w.farm_share[G.band[rows]] < 0.1].sum())
        np.add.at(w.cell_births, np.array([w.bands[int(b)].cell for b in G.band[rows]], dtype=np.int64), n_due)
        maternal = rng.binomial(n_due, P.MATERNAL_DEATH)
        for r, k in zip(rows, maternal):
            for _ in range(int(k)):
                ages = np.nonzero(G.F[r, 15:50] >= 1)[0]
                if len(ages) == 0:
                    break
                a = 15 + int(rng.choice(ages))
                G.F[r, a] -= 1
                w.counts["deaths"] += 1
                w.accum["deaths_by_cause"][C["childbirth"]] += 1
                w.accum["deaths"][int(age_group(np.array([a + 0.5]))[0])] += 1
    # conceptions
    F = G.F[rows]
    women = F[:, 15:50]
    wtot = women.sum(1)
    w.accum["woman_years"] += np.bincount(np.clip((np.arange(15, 50) - 15) // 5, 0, 6),
                                          weights=women.sum(0), minlength=7) / P.TICKS_PER_YEAR
    infants01 = G.F[rows, :2].sum(1) + G.M[rows, :2].sum(1)
    age2 = G.F[rows, 2] + G.M[rows, 2]
    pregnant = G.preg[rows].sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.clip(np.where(wtot > 0, infants01 / wtot, 0), 0, 1)
        f2 = np.clip(np.where(wtot > 0, age2 / wtot, 0), 0, 1 - f1)
        fp = np.clip(np.where(wtot > 0, pregnant / wtot, 0), 0, 1)
    settled = w.farm_share[G.band[rows]] >= 0.5
    sup1 = np.where(settled, P.FARMER_NURSING_1, P.NURSING_SUPPRESS_1)
    nurse = (1 - f1 - f2) + f1 * sup1 + f2 * P.NURSING_SUPPRESS_2
    from .demography import _fecundity
    fec = _fecundity(np.arange(15, 50) + 0.5)
    cond = np.clip((G.cond_rest[rows] - P.FERTILE_CONDITION[0]) / P.FERTILE_CONDITION[1], 0, 1)
    from .demography import margin_factor
    cond = cond * margin_factor(np.array([w.bands[int(b)].margin for b in G.band[rows]]))
    rate = PARTNERED_SHARE * P.CONCEPTION * cond * nurse * (1 - fp)
    expected = women * fec[None] * rate[:, None]
    conc = rng.poisson(expected)
    G.preg[rows, -1] += conc.sum(1)
    w.accum["births_by_age"] += np.bincount(np.clip((np.arange(15, 50) - 15) // 5, 0, 6),
                                            weights=conc.sum(0), minlength=7)


def age_one_year(w):
    G = w.groups
    rows = G.rows()
    if len(rows) == 0:
        return
    for X in (G.F, G.M):
        last = X[rows, -1] + X[rows, -2]
        X[rows, 1:] = X[rows, :-1]
        X[rows, 0] = 0
        X[rows, -1] = last


# ------------------------------------------------------------ fold / unfold / split
def fold(w, b):
    """Turn an individual band into a group. Individuals keep their records (folded, not dead)."""
    p = w.people
    mem = w.members(b.id)
    age = np.clip(w.ages(mem).astype(np.int64), 0, AGES - 1)
    F = np.bincount(age[p.sex[mem] == 0], minlength=AGES).astype(float)
    M = np.bincount(age[p.sex[mem] == 1], minlength=AGES).astype(float)
    preg = np.zeros(P.PREGNANCY_TICKS)
    due = p.preg_due[mem]
    for d in due[due >= 0]:
        k = int(min(max(d - w.t - 1, 0), P.PREGNANCY_TICKS - 1))
        preg[k] += 1
    cond = p.condition[mem]
    child = w.ages(mem) < 5
    cc = float(cond[child].mean()) if child.any() else 1.0
    cr = float(cond[~child].mean()) if (~child).any() else 1.0
    b.group = w.groups.add(b.id, F, M, preg, cc, cr)
    b.mode = "group"
    b.fold_tick = w.t
    p.alive[mem] = False
    p.folded[mem] = w.t
    w.counts["folded"] = w.counts.get("folded", 0) + len(mem)
    w.people_changed()


def split(w, b, target_cell, rng):
    """Split a group band in two by drawing half of each age-sex count."""
    G = w.groups
    g = b.group
    hF = rng.binomial(np.rint(G.F[g]).astype(np.int64), 0.5)
    hM = rng.binomial(np.rint(G.M[g]).astype(np.int64), 0.5)
    hP = rng.binomial(np.rint(G.preg[g]).astype(np.int64), 0.5)
    moved = int(hF.sum() + hM.sum())
    if moved == 0 or moved == G.total(g):
        return None
    G.F[g] -= hF
    G.M[g] -= hM
    G.preg[g] -= hP
    nb = w.new_band(target_cell, parent=b.id, leader=-1)
    nb.mode = "group"
    nb.group = G.add(nb.id, hF.astype(float), hM.astype(float), hP.astype(float),
                     G.cond_child[g], G.cond_rest[g])
    base = (b.group_name or w.band_name(b)).removesuffix(" (daughter group)")   # not repeated down the generations
    nb.group_name = f"{base} (daughter group)"
    return nb, moved


def transfer(w, b, dst, rng) -> int:
    """Move half of group b's people (drawn by age and sex) into neighbouring group dst."""
    G = w.groups
    g, d = b.group, dst.group
    hF = rng.binomial(np.rint(G.F[g]).astype(np.int64), 0.5)
    hM = rng.binomial(np.rint(G.M[g]).astype(np.int64), 0.5)
    hP = rng.binomial(np.rint(G.preg[g]).astype(np.int64), 0.5)
    moved = int(hF.sum() + hM.sum())
    if moved == 0 or moved == G.total(g):
        return 0
    td = G.total(d)
    G.F[g] -= hF
    G.M[g] -= hM
    G.preg[g] -= hP
    G.F[d] += hF
    G.M[d] += hM
    G.preg[d] += hP
    tot = max(td + moved, 1e-9)
    G.cond_child[d] = (G.cond_child[d] * td + G.cond_child[g] * moved) / tot
    G.cond_rest[d] = (G.cond_rest[d] * td + G.cond_rest[g] * moved) / tot
    return moved


def merge_into(w, src, dst):
    """Merge band src into dst; both groups, or an individual band into a group."""
    G = w.groups
    if src.mode == "individual":
        fold(w, src)
    if dst.mode == "individual":
        fold(w, dst)
    gs, gd = src.group, dst.group
    ts, td = G.total(gs), G.total(gd)
    G.F[gd] += G.F[gs]
    G.M[gd] += G.M[gs]
    G.preg[gd] += G.preg[gs]
    tot = max(ts + td, 1e-9)
    G.cond_child[gd] = (G.cond_child[gd] * td + G.cond_child[gs] * ts) / tot
    G.cond_rest[gd] = (G.cond_rest[gd] * td + G.cond_rest[gs] * ts) / tot
    G.F[gs] = 0
    G.M[gs] = 0
    G.preg[gs] = 0
    G.active[gs] = False


def unfold(w, b):
    """Recreate named individuals from a group's counts (when the observer follows it)."""
    G = w.groups
    g = b.group
    rng = w.rng["founding"]
    sexes, ages = [], []
    for sex, X in ((0, G.F[g]), (1, G.M[g])):
        for a in np.nonzero(X > 0)[0]:
            k = int(round(X[a]))
            sexes += [sex] * k
            ages += [a] * k
    k = len(sexes)
    if k == 0:
        return np.zeros(0, dtype=np.int64)
    order = np.argsort(-np.array(ages), kind="stable")
    sexes = np.array(sexes, dtype=np.int8)[order]
    ages = np.array(ages)[order]
    cond = np.where(ages < 5, G.cond_child[g], G.cond_rest[g])
    ids = w.add_people(sexes, np.full(k, -1), np.full(k, -1), np.full(k, b.id), cond, np.full(k, b.cell))
    p = w.people
    p.birth[ids] = w.t - ages * P.TICKS_PER_YEAR - rng.integers(0, 4, size=k)
    p.unfolded[ids] = w.t
    _pair_and_parent(w, ids, rng)
    # pregnancies
    women = [i for i in ids if p.sex[i] == 0 and 15 <= w.ages(i) < 45 and p.partner[i] >= 0]
    rng.shuffle(women)
    for d, n in enumerate(np.rint(G.preg[g]).astype(int)):
        for _ in range(n):
            if not women:
                break
            m = women.pop()
            p.preg_due[m] = w.t + d + 1
            p.preg_father[m] = p.partner[m]
    G.active[g] = False
    G.F[g] = 0
    G.M[g] = 0
    G.preg[g] = 0
    b.mode = "individual"
    b.group = -1
    b.leader = int(ids[0])
    w.counts["unfolded"] = w.counts.get("unfolded", 0) + k
    w.people_changed()
    return ids


def _pair_and_parent(w, ids, rng):
    p = w.people
    age = w.ages(ids)
    women = [int(i) for i, a in zip(ids, age) if p.sex[i] == 0 and a >= P.FEMALE_MIN_AGE]
    men = [int(i) for i, a in zip(ids, age) if p.sex[i] == 1 and a >= P.MALE_MIN_AGE]
    for wmn in sorted(women, key=lambda i: p.birth[i]):
        if not men or w.ages(wmn) > 60 or rng.random() > PARTNERED_SHARE:
            continue
        j = min(men, key=lambda m: abs(p.birth[m] - p.birth[wmn] + 3 * P.TICKS_PER_YEAR))
        if abs(p.birth[j] - p.birth[wmn]) > 20 * P.TICKS_PER_YEAR:
            continue
        men.remove(j)
        p.partner[wmn], p.partner[j] = j, wmn
        p.partner_since[wmn] = p.partner_since[j] = w.t
    for i, a in zip(ids, age):
        if a >= 15:
            continue
        cands = [m for m in women if 16 <= (w.ages(m) - a) <= 42]
        if not cands:
            continue
        m = cands[int(rng.integers(len(cands)))]
        p.mother[i] = m
        p.father[i] = p.partner[m]
        y = p.youngest[m]
        if y < 0 or p.birth[i] > p.birth[y]:
            p.youngest[m] = i
