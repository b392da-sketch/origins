"""Leaders, polities, institutions and break-up (M3, behaviour 5).

A polity is a set of settlements under one leader: a seat and the villages that
pay it tribute. Villages join through alliance (drawn by a leader's standing,
more readily between close peoples) and through fission (a daughter village
stays in its mother's polity); conquest comes with conflict (M3 step 5). Every
member is attached through another settlement: the seat itself, or a member
that acts as its sub-leader. The depth of that tree is the number of levels of
rule above the village, and from it the tier is measured (never assigned):
simple chiefdom (one level), complex chiefdom (two), state (three or more,
with officials over districts).

Holding settlements costs effort, the polity's load: more members, farther
from the seat, more different in language and customs. Institutions raise the
capacity to bear it; each needs specialists at the seat, who live from its
surplus (tribute included). Members secede with a chance that rises with
overload and stress (a failed harvest at the seat, a contested succession,
hunger at home). Collapse and recovery are measured, not rolled.

reads: bands (store, size, farm share, margin, cell), customs, languages, people (role, alive), specialists
writes: polities, polity_of, polity_via (per band), band stores (tribute moved, not created), events, logs
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import params as P

INSTITUTIONS = ["council of village heads", "tribute collectors", "law and judges",
                "warriors kept by the leader", "officials over districts"]
COUNCIL, COLLECTORS, LAW, WARRIORS, OFFICIALS = range(5)
TIERS = ["autonomous", "simple chiefdom", "complex chiefdom", "state"]


@dataclass(slots=True)
class Polity:
    id: int
    seat: int
    founded: int
    name: str
    alive: bool = True
    ended: int = -1
    leader: int = -1             # the seat's leader (a person), or -1 where the seat is a folded group
    parent: int = -1             # the polity it broke away from
    inst: list = field(default_factory=lambda: [0] * len(INSTITUTIONS))
    tier: int = 0
    load: float = 0.0
    cap: float = 0.0
    contested_until: int = -1    # tick until which a contested succession weakens it
    defeated_until: int = -1     # tick until which a lost war weakens it
    led_since: int = -1          # when the present leader took over
    peak_people: int = 0
    founding_event: int = -1


def init(w):
    w.polities = {}
    w.next_polity = 0
    w.polity_of = np.full(64, -1, dtype=np.int32)
    w.polity_via = np.full(64, -1, dtype=np.int32)
    w.polity_log = []            # every 10 years: [year, polity, settlements, people, depth, load, capacity, institutions, tier, seat cell,
                                 #  languages spoken, settlements once conquered]
    w.sec_stats = {}             # overload bin -> [member-years, secessions]
    w.polity_firsts = {}         # tier name -> event id of the first polity to reach it


def ensure(w, band_id: int, parent: int):
    if band_id >= len(w.polity_of):
        cap = len(w.polity_of)
        while cap <= band_id:
            cap *= 2
        for k in ("polity_of", "polity_via"):
            a = np.full(cap, -1, dtype=np.int32)
            old = getattr(w, k)
            a[:len(old)] = old
            setattr(w, k, a)
    if parent >= 0 and w.polity_of[parent] >= 0:
        w.polity_of[band_id] = w.polity_of[parent]        # a daughter settlement stays in its mother's polity
        w.polity_via[band_id] = parent                    # attached through her
    else:
        w.polity_of[band_id] = -1
        w.polity_via[band_id] = -1


# ------------------------------------------------------------------ helpers
def _cells_apart(w, a: int, b: int) -> float:
    g = w.planet.grid
    cosang = float(np.clip(g.xyz[a] @ g.xyz[b], -1, 1))
    spacing = np.sqrt(g.cell_area_km2) / g.radius_km           # one cell in radians, roughly
    return float(np.arccos(cosang) / spacing)


def cultural_distance(w, a, b) -> float:
    """0 identical, 1 completely different: half customs, half language (shared word roots)."""
    from . import customs, language
    d = customs.distance(w, a.id, b.id)
    if a.language != b.language:
        cache = getattr(w, "_roots_cache", None)
        if cache is None or cache[0] != w.year:
            cache = w._roots_cache = (w.year, {})
        key = (min(a.language, b.language), max(a.language, b.language))
        sr = cache[1].get(key)
        if sr is None:
            sr = cache[1][key] = language.shared_roots(w.languages[a.language], w.languages[b.language])
        d = 0.5 * d + 0.5 * (1 - sr)
    else:
        d = 0.5 * d
    return d


def _surplus(b, size):
    from .surplus import ANNUAL
    return max(0.0, b.store - P.SURPLUS_RESERVE * size * ANNUAL)


def members_of(w, pid) -> list:
    return [b for b in w.living_bands() if w.polity_of[b.id] == pid]


def _depths(w, mem_ids, seat):
    """Levels of rule between each member and the seat (seat 0, direct members 1, ...)."""
    via = {i: int(w.polity_via[i]) for i in mem_ids}
    depth = {seat: 0}
    for i in mem_ids:
        chain, j = [], i
        while j not in depth and len(chain) <= len(mem_ids):
            chain.append(j)
            j = via.get(j, seat)
            if j < 0 or (j not in via and j != seat):
                j = seat
        d = depth.get(j, 0)
        for k in reversed(chain):
            d += 1
            depth[k] = d
    return depth


def levels_of_rule(w, mem_ids, seat) -> int:
    """Levels of rule above the village: the seat is one level if at least two settlements answer to it; each
    settlement through which at least two others answer (a district head) adds a level below it. A chain of
    daughter villages, each attached through its mother, is not a hierarchy and adds nothing."""
    kids: dict[int, list] = {}
    for i in mem_ids:
        if i == seat:
            continue
        v = int(w.polity_via[i])
        kids.setdefault(v if v >= 0 else seat, []).append(i)

    def lv(node, guard=0) -> int:
        ch = kids.get(node, [])
        below = max((lv(c, guard + 1) for c in ch), default=0) if guard < 64 else 0
        return below + (1 if len(ch) >= 2 else 0)
    return lv(seat)


def _neighbour_has(w, p, k, cache):
    """A polity seated within reach (three rings) that has institution k, to learn it from; or None."""
    from .language import ring2
    nb = w.planet.grid.neighbours
    seat_cell = w.bands[p.seat].cell
    near = set(int(c) for c in ring2(w)[seat_cell])
    near |= {int(x) for c in list(near) for x in nb[c] if x >= 0}
    for c in near:
        for q in cache["seats"].get(c, ()):
            if q.id != p.id and q.alive and q.inst[k]:
                return q.id
    return None


def max_depth(p) -> int:
    """How many levels of rule a polity's institutions can support."""
    return 1 + p.inst[COLLECTORS] + 2 * p.inst[OFFICIALS]


def staff_needed(p, n_members) -> float:
    return sum(P.INSTITUTION_STAFF[k] * np.sqrt(max(n_members, 1)) for k in range(len(INSTITUTIONS)) if p.inst[k])


def capacity(p) -> float:
    c = P.POLITY_CAPACITY * (1 + sum(P.INSTITUTION_GAIN[k] for k in range(len(INSTITUTIONS)) if p.inst[k] and k != OFFICIALS))
    return c * (P.OFFICIALS_MULTIPLIER if p.inst[OFFICIALS] else 1.0)


def tier_of(p, depth, n_settlements) -> int:
    if n_settlements < 3:
        return 0
    if depth >= 3 and p.inst[OFFICIALS]:
        return 3
    return 2 if depth >= 2 else 1


def _name(w, seat) -> str:
    """Named after its first leader, or after the local people where the seat is a folded group."""
    if seat.mode == "individual" and seat.leader >= 0:
        return f"the polity of {w.people.name(seat.leader)}"
    base = w.band_name(seat).removesuffix(" (daughter group)")
    if base.lower().startswith("band of "):
        base = base[8:]
    return f"the polity of the {base[:1].upper() + base[1:]} people"


def _new_polity(w, seat, causes, parent=-1, why="") -> Polity:
    pid = w.next_polity
    w.next_polity += 1
    p = Polity(pid, seat.id, w.t, _name(w, seat), parent=parent)
    p.led_since = w.t
    p.leader = seat.leader if seat.mode == "individual" and seat.leader >= 0 and w.people.alive[seat.leader] \
        and int(w.people.band[seat.leader]) == seat.id else _successor(w, seat, -1, 2)[0]
    w.polities[pid] = p
    w.polity_of[seat.id] = pid
    w.polity_via[seat.id] = -1
    p.founding_event = w.event("polity_founded", cell=seat.cell, band=seat.id, causes=causes, polity=pid,
                               why=why, parent=parent)
    return p


def _end_polity(w, p, why, causes):
    p.alive = False
    p.ended = w.t
    for b in members_of(w, p.id):
        w.polity_of[b.id] = -1
        w.polity_via[b.id] = -1
    w.event("polity_ended", cell=w.bands[p.seat].cell, band=p.seat, causes=causes, polity=p.id, why=why)


def _successor(w, seat, old, rule):
    """(new leader, number of rival claimants) by the succession custom: the eldest son, the eldest son of a
    sister, or the council's choice (the head of the richest household); any adult man of the seat if none."""
    if seat.mode != "individual":
        return -1, 0
    p = w.people
    mem = w.members(seat.id)
    if not len(mem):
        return -1, 0
    ages = w.ages(mem)
    adult = mem[(ages >= 20) & (ages < 60)]          # an heir in the prime of life where there is one
    if not len(adult):
        adult = mem[ages >= 18]
    if not len(adult):
        return -1, 0
    cands = np.zeros(0, dtype=np.int64)
    if old >= 0 and rule == 0:
        cands = adult[(p.father[adult] == old) & (p.sex[adult] == 1)]
    elif old >= 0 and rule == 1:
        m = int(p.mother[old])
        if m >= 0:
            sisters = np.nonzero((p.mother[:p.n] == m) & (p.sex[:p.n] == 0))[0] if p.n < 3_000_000 else []
            cands = adult[np.isin(p.mother[adult], sisters) & (p.sex[adult] == 1)]
    if len(cands) == 0:
        heads = adult[p.wealth[adult] > 0]
        if len(heads):
            best = heads[np.argsort(-p.wealth[heads])]
            rich = float(p.wealth[best[0]])
            rivals = int((p.wealth[best[1:]] >= 0.7 * rich).sum())
            new = int(best[0])
            if p.sex[new] == 0 and p.partner[new] >= 0 and p.alive[p.partner[new]]:
                new = int(p.partner[new])          # a household is led by its man where there is one (PROPOSED)
            return new, rivals
        men = adult[p.sex[adult] == 1]
        pool = men if len(men) else adult
        return int(pool[np.argmin(p.birth[pool])]), 0      # the eldest man in the prime of life
    order = cands[np.argsort(p.birth[cands])]
    return int(order[0]), len(order) - 1


def _leader(w, seat) -> int:
    if seat.mode != "individual":
        return -1
    mem = w.members(seat.id)
    lead = mem[w.people.role[mem] == 1] if len(mem) else mem
    return int(lead[0]) if len(lead) else -1


# ------------------------------------------------------------------ yearly
def yearly(w):
    if not P.POLITIES:
        return
    from . import customs
    rng = w.rng["polity"]
    live = w.living_bands()
    if not live:
        return
    ids, pos = w.live_index()
    sizes = w.live_sizes()
    size_of = dict(zip(ids.tolist(), sizes.tolist()))
    village = (w.farm_share[ids] >= 0.5).tolist()
    is_village = dict(zip(ids.tolist(), village))

    # --- seats that ended: the largest member takes over, or the polity dissolves
    by_polity: dict[int, list] = {}
    for b in live:
        pid = int(w.polity_of[b.id])
        if pid >= 0:
            by_polity.setdefault(pid, []).append(b)
    for pid, p in list(w.polities.items()):
        if not p.alive:
            continue
        mem = by_polity.get(pid, [])
        seat = w.bands[p.seat]
        if not seat.alive:
            others = [b for b in mem if b.id != p.seat]
            if not others:
                _end_polity(w, p, "its seat is gone and no settlement remains", [{"note": f"{w.band_name(seat)} ended"}])
                continue
            new = max(others, key=lambda b: (size_of.get(b.id, 0), -b.id))
            old_seat = p.seat
            p.seat = new.id
            w.polity_via[new.id] = -1
            for b in others:
                if int(w.polity_via[b.id]) == old_seat:
                    w.polity_via[b.id] = new.id
            w.event("seat_moved", cell=new.cell, band=new.id, polity=pid,
                    causes=[{"note": f"{w.band_name(seat)}, the seat, ended; {w.band_name(new)} is the largest settlement"}])
        # members attached through a settlement that left or ended are attached to the seat
        member_ids = {b.id for b in mem}
        for b in mem:
            v = int(w.polity_via[b.id])
            if b.id != p.seat and (v < 0 or v not in member_ids):
                w.polity_via[b.id] = p.seat

    # --- succession: a leader holds the place until death; then it passes by the seat's custom
    p_ = w.people
    for p in w.polities.values():
        if not p.alive:
            continue
        seat = w.bands[p.seat]
        if p.leader >= 0 and p_.alive[p.leader] and int(p_.band[p.leader]) == seat.id:
            continue
        old = p.leader
        died = old >= 0 and not p_.alive[old] and p_.death[old] >= 0
        rule = int(w.customs[seat.id, customs.SUCCESSION])
        new, rivals = _successor(w, seat, old, rule)
        p.leader = new
        p.led_since = w.t
        if died and new >= 0:
            contested = rivals > 0 and rng.random() < P.CONTESTED_SUCCESSION[rule]
            if contested:
                p.contested_until = w.t + P.CONTEST_YEARS * P.TICKS_PER_YEAR
            w.event("succession", cell=seat.cell, band=seat.id, person=new, polity=p.id,
                    causes=[{"death": int(old)}, {"note": f"succession {customs.CUSTOMS['succession'][rule]}"
                                                          + (f"; {rivals} rival claimants" if rivals else "")}],
                    contested=bool(contested))

    # --- tribute: members send a share of their surplus to the seat (sub-leaders keep part of what passes)
    by_polity = {}
    for b in live:
        pid = int(w.polity_of[b.id])
        if pid >= 0 and w.polities[pid].alive:
            by_polity.setdefault(pid, []).append(b)
    for pid, mem in by_polity.items():
        p = w.polities[pid]
        seat = w.bands[p.seat]
        for b in mem:
            if b.id == p.seat:
                continue
            give = P.TRIBUTE_SHARE * _surplus(b, size_of.get(b.id, 0))
            if give <= 0:
                continue
            b.store -= give
            via = int(w.polity_via[b.id])
            if via != p.seat and via >= 0 and w.bands[via].alive and int(w.polity_of[via]) == pid:
                keep = P.SUB_LEADER_KEEP * give
                w.bands[via].store += keep
                give -= keep
            seat.store += give

    # --- load, capacity, institutions, tier; secessions
    r2_cache = {"seats": {}}
    for q in w.polities.values():
        if q.alive:
            r2_cache["seats"].setdefault(w.bands[q.seat].cell, []).append(q)
    for pid, mem in by_polity.items():
        p = w.polities[pid]
        seat = w.bands[p.seat]
        mem_ids = [b.id for b in mem]
        depth = _depths(w, mem_ids, p.seat)
        load = 0.0
        unit = {}
        for b in mem:
            if b.id == p.seat:
                continue
            d = _cells_apart(w, seat.cell, b.cell)
            cd = cultural_distance(w, seat, b)
            u = np.sqrt(max(size_of.get(b.id, 0), 1) / 150.0) * (1 + d / P.LOAD_DISTANCE) * (1 + P.LOAD_CULTURE * cd)
            ca = int(w.conquered_at[b.id]) if hasattr(w, "conquered_at") else -1
            if ca >= 0 and w.t - ca < P.CONQUEST_MEMORY * P.TICKS_PER_YEAR:
                u *= 1 + P.CONQUEST_LOAD * (1 - (w.t - ca) / (P.CONQUEST_MEMORY * P.TICKS_PER_YEAR))
            unit[b.id] = (u, d, cd)
            load += u
        p.load = load
        p.cap = capacity(p)
        n = len(mem)
        staff = float(w.spec[p.seat])
        # institutions: add one when the load presses on capacity and the seat's specialists can staff it;
        # drop the last when they no longer can
        if staff < staff_needed(p, n) and any(p.inst):
            k = max(i for i in range(len(INSTITUTIONS)) if p.inst[i])
            p.inst[k] = 0
            w.event("institution_lost", cell=seat.cell, band=seat.id, polity=pid, institution=INSTITUTIONS[k],
                    causes=[{"note": f"{p.name} could keep {staff:.0f} specialists; its institutions needed "
                                     f"{staff_needed(p, n) + 0:.0f}"}])
            p.cap = capacity(p)
        elif P.INSTITUTIONS and load > P.INSTITUTION_PRESSURE * p.cap:
            # an institution is a new way of doing things: under pressure, a polity finds one only now and then,
            # much sooner where a neighbouring polity already has it to copy
            order = [COUNCIL, COLLECTORS, LAW, WARRIORS, OFFICIALS]
            for k in order:
                if p.inst[k] or (k == OFFICIALS and not (p.inst[COLLECTORS] and p.inst[LAW])):
                    continue
                example = _neighbour_has(w, p, k, r2_cache)
                if rng.random() >= P.INSTITUTION_INVENT * (P.INSTITUTION_COPY if example is not None else 1.0):
                    break
                p.inst[k] = 1
                if staff >= staff_needed(p, n):
                    w.event("institution_founded", cell=seat.cell, band=seat.id, polity=pid,
                            institution=INSTITUTIONS[k],
                            causes=[{"event": p.founding_event}] + ([{"note": f"copied from {w.polities[example].name}"}, {"event": w.polities[example].founding_event}]
                                                                     if example is not None else []) + [
                                    {"note": f"{p.name} held {n} settlements: load {load:.1f} against capacity "
                                             f"{p.cap:.1f}; {staff:.0f} specialists at the seat could staff it"}])
                    p.cap = capacity(p)
                else:
                    p.inst[k] = 0
                break
        dmax = levels_of_rule(w, mem_ids, p.seat)
        p.tier = tier_of(p, dmax, n)
        people = int(sum(size_of.get(i, 0) for i in mem_ids))
        p.peak_people = max(p.peak_people, people)
        if p.tier >= 1:
            name = TIERS[p.tier]
            if name not in w.polity_firsts:
                w.polity_firsts[name] = w.event("first_" + name.replace(" ", "_"), cell=seat.cell, band=seat.id,
                                                polity=pid, causes=[{"event": p.founding_event},
                                                                    {"note": f"{p.name}: {n} settlements, "
                                                                             f"{dmax} levels of rule"}])
        if w.year % 10 == 0:
            langs = len({b.language for b in mem})
            conq = sum(1 for b in mem if hasattr(w, "conquered_at") and w.conquered_at[b.id] >= 0)
            w.polity_log.append([w.year, pid, n, people, dmax, round(load, 2), round(p.cap, 2),
                                 int(sum(1 << k for k in range(len(INSTITUTIONS)) if p.inst[k])), p.tier, int(seat.cell),
                                 langs, conq])
        # secessions
        over = max(0.0, load / max(p.cap, 1e-9) - 1)
        stress = 0.0
        notes = []
        if seat.margin < 1.0:
            stress += 1.0
            notes.append(f"a poor harvest at the seat (food {seat.margin:.0%} of needs)")
        if p.contested_until > w.t:
            stress += 1.0
            notes.append("a contested succession")
        if p.defeated_until > w.t:
            stress += 1.0
            notes.append("a lost war")
        law = 1 - P.LAW_CALM * p.inst[LAW]
        bin_ = min(int(over * 4), 12)
        st = w.sec_stats.setdefault(bin_, [0, 0])
        gone = set()
        for b in mem:
            if b.id == p.seat or b.id in gone:
                continue
            u, d, cd = unit[b.id]
            st[0] += 1
            own = 0.5 if b.last_ratio < 0.9 else 0.0
            h = (P.SECESSION_BASE + P.SECESSION_OVERLOAD * over + P.SECESSION_STRESS * (stress + own)) * law
            h *= (1 + d / P.LOAD_DISTANCE) * (1 + cd)
            if rng.random() < min(h, 0.9):
                st[1] += 1
                sub = [x for x in mem_ids if x not in gone and _under(w, x, b.id, p.seat)]
                gone.update(sub)
                causes = [{"event": p.founding_event},
                          {"note": f"{w.band_name(b)} left {p.name}: load {load:.1f} against capacity "
                                   f"{p.cap:.1f}" + (f"; {', '.join(notes)}" if notes else "")
                                   + ("; hunger at home" if own else "")}]
                for x in sub:
                    w.polity_of[x] = -1
                    w.polity_via[x] = -1
                eid = w.event("secession", cell=b.cell, band=b.id, polity=pid, causes=causes, took=len(sub),
                              overload=round(over, 3), stress=round(stress + own, 2))
                if len(sub) >= 2:
                    np_ = _new_polity(w, b, [{"event": eid}], parent=pid, why="secession")
                    for x in sub:
                        if x != b.id:
                            w.polity_of[x] = np_.id
        if len(gone) and len(mem) - len(gone) < 2:
            rest = [b for b in mem if b.id not in gone]
            _end_polity(w, p, "too few settlements remain", [{"note": f"{len(gone)} settlements left {p.name}"}])
            for b in rest:
                w.polity_of[b.id] = -1

    # --- alliance: autonomous villages join a leader of greater standing nearby
    from .language import ring2
    r2 = ring2(w)
    by_cell: dict[int, list] = {}
    for b in live:
        if is_village.get(b.id):
            by_cell.setdefault(b.cell, []).append(b)
    standing = {}
    for b in live:
        if is_village.get(b.id):
            standing[b.id] = _surplus(b, size_of.get(b.id, 0)) / 365.0 + float(w.spec[b.id])
    for b in live:
        if not is_village.get(b.id) or w.polity_of[b.id] >= 0:
            continue
        if rng.random() >= P.ALLIANCE_RATE:
            continue
        own = standing.get(b.id, 0.0)
        best, best_a = None, 0.0
        for c in r2[b.cell]:
            for t in by_cell.get(int(c), ()):
                if t.id == b.id or not t.alive:
                    continue
                pid = int(w.polity_of[t.id])
                if pid >= 0:
                    p = w.polities[pid]
                    if not p.alive:
                        continue
                    head = w.bands[p.seat]
                    s = standing.get(head.id, 0.0) + 0.25 * p.load
                    depth_here = 1 if t.id == p.seat else _depths(w, [t.id], p.seat).get(t.id, 1) + 1
                    if depth_here > max_depth(p):
                        continue
                    if p.load > P.INSTITUTION_PRESSURE * 1.5 * p.cap:
                        continue
                else:
                    head = t
                    s = standing.get(t.id, 0.0)
                a = np.clip((s - own) / max(own + 1.0, 1.0), 0, 3) / 3 * (1 - cultural_distance(w, head, b))
                if a > best_a:
                    best, best_a = t, a
        if best is None or rng.random() >= best_a:
            continue
        pid = int(w.polity_of[best.id])
        why = (f"{w.band_name(b)} (surplus {own:.1f} person-years) accepted the leadership of "
               f"{w.band_name(best if pid < 0 else w.bands[w.polities[pid].seat])}")
        if pid < 0:
            p = _new_polity(w, best, [{"note": why}], why="alliance")
            pid = p.id
        w.polity_of[b.id] = pid
        w.polity_via[b.id] = best.id
        w.event("polity_joined", cell=b.cell, band=b.id, polity=pid, causes=[{"note": why}],
                through=best.id)

    # --- notables stay individual: the seats of chiefdoms and states are followed person by person (their
    # leaders, heirs and households), even where the world has folded its people into groups
    if P.NOTABLE_SEATS:
        from . import groups
        seats = sorted((p for p in w.polities.values() if p.alive and p.tier >= 1), key=lambda p: -p.load)
        for p in seats[:P.NOTABLE_SEATS]:
            seat = w.bands[p.seat]
            if seat.alive and seat.mode == "group" and seat.group >= 0:
                groups.unfold(w, seat)
                p.leader, _ = _successor(w, seat, -1, 2)
                p.led_since = w.t
    del w.polity_log[:-40000]


def _under(w, x, top, seat) -> bool:
    """True if settlement x is top or attached (directly or through others) under top."""
    j, steps = x, 0
    while j >= 0 and j != seat and steps < 64:
        if j == top:
            return True
        j = int(w.polity_via[j])
        steps += 1
    return False


# ------------------------------------------------------------------ saving
def to_json(w):
    from dataclasses import asdict
    return {"next_polity": w.next_polity, "polities": [asdict(p) for p in w.polities.values()],
            "polity_log": w.polity_log[-20000:], "sec_stats": {str(k): v for k, v in w.sec_stats.items()},
            "polity_firsts": w.polity_firsts}


def from_json(w, d):
    w.next_polity = d.get("next_polity", 0)
    w.polities = {}
    for x in d.get("polities", []):
        p = Polity(**x)
        w.polities[p.id] = p
    w.polity_log = d.get("polity_log", [])
    w.sec_stats = {int(k): v for k, v in d.get("sec_stats", {}).items()}
    w.polity_firsts = d.get("polity_firsts", {})
