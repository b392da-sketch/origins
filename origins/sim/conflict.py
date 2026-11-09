"""Raids, wars and conquest (M3, behaviour 6).

Who fights: neighbouring sides within reach of each other. A side is a polity
(all its settlements) or a settlement on its own, forager bands included
(M3 decision 1A). Members of one polity do not fight each other.

Why: each year the chance that a side attacks a neighbour rises with its
scarcity (food gathered against need), with closeness, with its strength
against the target's, with cultural difference, with grievance (killings
suffered from that side, remembered for a few generations), with a new leader
and with warriors to feed. Every war is an event naming these causes.

What it costs: fighting kills people on both sides, mostly men of fighting age,
each death recorded with the cause "killed in war" and traced to the war.

What it can win: stores (moved, not created), captives (young women and
children join the winner's people and keep their own speech: M3 decision 2A),
and, for a polity or village attacking a village, the village itself
(annexation), or a whole polity when its seat falls. Conquered settlements
weigh on the conqueror's load for a century.

reads: bands (cell, size, margin, store), polities, customs, languages, people (age, sex), groups
writes: people (deaths, band of captives), groups (deaths, captives), band stores, polity membership,
        grievances, events, logs
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..state import C

OUTCOMES = ["repelled", "raided", "annexed", "polity conquered"]


def init(w):
    w.grievance = {}                       # (side, side) -> remembered killings, decaying
    w.conquered_at = np.full(64, -1, dtype=np.int32)    # tick each band was last conquered
    w.war_log = []                         # [year, attacker, defender, scarcity, cells apart, cultural distance,
                                           #  strength share, outcome, attacker deaths, defender deaths, attacker is polity]
    w.war_stats = {"scarcity": {}, "distance": {}}       # bin -> [side-pair-years considered, wars]


def ensure(w, band_id: int, parent: int):
    if band_id >= len(w.conquered_at):
        cap = len(w.conquered_at)
        while cap <= band_id:
            cap *= 2
        a = np.full(cap, -1, dtype=np.int32)
        a[:len(w.conquered_at)] = w.conquered_at
        w.conquered_at = a
    w.conquered_at[band_id] = w.conquered_at[parent] if parent >= 0 else -1


def cultural_distances(w, a, targets) -> np.ndarray:
    """Cultural distance from band a to each target (as polity.cultural_distance, for many at once)."""
    from . import customs
    from .language import shared_roots
    ids = np.array([t.id for t in targets])
    differ = (w.customs[ids] != w.customs[a.id]).mean(1)
    neutral = np.linalg.norm(w.neutral[ids] - w.neutral[a.id], axis=1) / np.sqrt(customs.N_NEUTRAL)
    d = 0.5 * differ + 0.5 * np.minimum(1.0, neutral / P.NEUTRAL_SCALE)
    out = 0.5 * d
    cache = getattr(w, "_roots_cache", None)
    if cache is None or cache[0] != w.year:
        cache = w._roots_cache = (w.year, {})
    for k, t in enumerate(targets):
        if t.language != a.language:
            key = (min(a.language, t.language), max(a.language, t.language))
            sr = cache[1].get(key)
            if sr is None:
                sr = cache[1][key] = shared_roots(w.languages[a.language], w.languages[t.language])
            out[k] = 0.5 * d[k] + 0.5 * (1 - sr)
    return out


def side_of(w, b) -> tuple:
    pid = int(w.polity_of[b.id])
    if pid >= 0 and w.polities[pid].alive:
        return ("p", pid)
    return ("b", b.id)


def _all_fighters(w) -> dict:
    """Men of fighting age (16-45) in every living band, in one pass."""
    ids, pos = w.live_index()
    p = w.people
    idx = w.alive_idx()
    a = w.ages(idx)
    men = idx[(p.sex[idx] == 1) & (a >= 16) & (a < 46)]
    f = np.bincount(pos[p.band[men]], minlength=len(ids)).astype(float)
    G = w.groups
    rows = G.rows()
    if len(rows):
        k = pos[G.band[rows]]
        ok = k >= 0
        np.add.at(f, k[ok], G.M[rows[ok], 16:46].sum(1))
    return dict(zip(ids.tolist(), f.tolist()))


def _fighters(w, b, sizes) -> float:
    """Men of fighting age (16-45): counted for bands of individuals, from group counts for folded groups."""
    if b.mode == "group":
        G = w.groups
        return float(G.M[b.group, 16:46].sum()) if b.group >= 0 else 0.0
    mem = w.members(b.id)
    if not len(mem):
        return 0.0
    a = w.ages(mem)
    return float(((w.people.sex[mem] == 1) & (a >= 16) & (a < 46)).sum())


def _kill(w, b, n, eid, rng, men_share=0.85) -> int:
    """Kill about n people of band b (mostly men of fighting age); returns deaths."""
    from . import demography
    from .groups import AGE_GROUP
    n = int(n)
    if n <= 0:
        return 0
    if b.mode == "group":
        G = w.groups
        g = b.group
        if g < 0:
            return 0
        done = 0
        for X, ages, k in ((G.M, slice(16, 46), int(round(n * men_share))), (G.F, slice(10, 50), n - int(round(n * men_share)))):
            cnt = np.rint(X[g, ages]).astype(np.int64)
            tot = int(cnt.sum())
            k = min(k, tot)
            if k <= 0:
                continue
            d = rng.multivariate_hypergeometric(cnt, k)
            X[g, ages] -= d
            done += k
            w.accum["deaths"] += np.bincount(AGE_GROUP[ages], weights=d, minlength=18)
        w.counts["deaths"] += done
        w.accum["deaths_by_cause"][C["killed in war"]] += done
        return done
    p = w.people
    mem = w.members(b.id)
    if not len(mem):
        return 0
    a = w.ages(mem)
    men = mem[(p.sex[mem] == 1) & (a >= 16) & (a < 46)]
    rest = mem[~np.isin(mem, men) & (a >= 5)]
    km = min(len(men), int(round(n * men_share)))
    kr = min(len(rest), n - km)
    hit = np.concatenate([rng.choice(men, km, replace=False) if km else men[:0],
                          rng.choice(rest, kr, replace=False) if kr else rest[:0]])
    if len(hit):
        demography.kill(w, hit, np.full(len(hit), C["killed in war"], dtype=np.int8))
        p.death_hazard[hit] = eid
        w.people_changed()
    return int(len(hit))


def _captives(w, loser, winner, share, rng) -> int:
    """Young women and children of the loser join the winner's settlement (they keep their own speech)."""
    if loser.mode == "group" or winner.mode == "group" or share <= 0:
        return 0
    p = w.people
    mem = w.members(loser.id)
    if not len(mem):
        return 0
    a = w.ages(mem)
    pool = mem[((p.sex[mem] == 0) & (a >= 12) & (a < 30)) | (a < 12)]
    k = int(rng.binomial(len(pool), share)) if len(pool) else 0
    if k <= 0:
        return 0
    taken = rng.choice(pool, k, replace=False)
    part = p.partner[taken]
    has = part >= 0
    p.partner[part[has]] = -1
    p.partner[taken] = -1
    p.band[taken] = winner.id
    w.people_changed()
    return k


def yearly(w):
    if not P.CONFLICT:
        return
    from . import polity
    from .language import ring2
    rng = w.rng["conflict"]
    live = w.living_bands()
    if not live:
        return
    ids, pos = w.live_index()
    sizes = dict(zip(ids.tolist(), w.live_sizes().tolist()))
    for k in list(w.grievance):
        w.grievance[k] *= P.GRIEVANCE_MEMORY
        if w.grievance[k] < 0.5:
            del w.grievance[k]
    r2 = ring2(w)
    nb = w.planet.grid.neighbours
    by_cell: dict[int, list] = {}
    for b in live:
        by_cell.setdefault(b.cell, []).append(b)
    # each side's members, fighters, scarcity
    sides: dict[tuple, list] = {}
    for b in live:
        sides.setdefault(side_of(w, b), []).append(b)
    fighters = _all_fighters(w)
    xyz = w.planet.grid.xyz
    spacing = float(np.sqrt(w.planet.grid.cell_area_km2) / w.planet.grid.radius_km)
    scarcity = {}
    for s, mem in sides.items():
        tot = sum(sizes.get(b.id, 0) for b in mem)
        m = sum(b.margin * sizes.get(b.id, 0) for b in mem) / max(tot, 1)
        scarcity[s] = float(np.clip((P.WAR_SCARCITY_MARGIN - m) / 0.6, 0, 1))
    # who can reach whom: villages and polities two rings, foragers one
    for s, mem in sides.items():
        # a side weighs war in a given year with chance WAR_CONSIDER, and then attacks with chance (its chance
        # of war) / WAR_CONSIDER: the same chance of war (up to WAR_CONSIDER a year), for a quarter of the work
        if rng.random() >= P.WAR_CONSIDER:
            continue
        if not any(fighters[b.id] >= 3 for b in mem):
            continue
        is_pol = s[0] == "p"
        pol = w.polities[s[1]] if is_pol else None
        seen = {}
        for b in mem:
            reach = r2[b.cell] if (is_pol or w.farm_share[b.id] >= 0.5) else [b.cell] + [int(x) for x in nb[b.cell] if x >= 0]
            for c in reach:
                for t in by_cell.get(int(c), ()):
                    ts = side_of(w, t)
                    if ts == s or t.id in seen:
                        continue
                    seen[t.id] = b
        if not seen:
            continue
        # strength of the attacking side near each target, and the chance of attacking it
        sc = scarcity[s]
        lead = w.bands[pol.seat] if is_pol else mem[0]
        new_leader = P.WAR_NEW_LEADER if is_pol and w.t - pol.led_since < 3 * P.TICKS_PER_YEAR else 1.0
        warriors = 1 + P.WARRIOR_STRENGTH * (pol.inst[polity.WARRIORS] if is_pol else 0)
        best, best_p, info = None, 0.0, None
        mcells = np.array([x.cell for x in mem])
        mfight = np.array([fighters[x.id] for x in mem])
        tids = list(seen)
        T = len(tids)
        tb = [w.bands[i] for i in tids]
        tcell = np.array([t.cell for t in tb])
        bcell = np.array([seen[i].cell for i in tids])
        d = np.arccos(np.clip((xyz[bcell] * xyz[tcell]).sum(1), -1, 1)) / spacing
        if len(mem) == 1:
            att = mfight[0] * np.exp(-d / P.LOAD_DISTANCE) * warriors
        else:
            dd = np.arccos(np.clip(xyz[tcell] @ xyz[mcells].T, -1, 1)) / spacing        # targets x members
            att = (np.where(dd <= 2.5, np.exp(-dd / P.LOAD_DISTANCE), 0.0) @ mfight) * warriors
        tside = [side_of(w, t) for t in tb]
        dw = np.array([1 + P.WARRIOR_STRENGTH * w.polities[x[1]].inst[polity.WARRIORS] if x[0] == "p" else 1.0
                       for x in tside])
        dfd = np.array([fighters[i] for i in tids]) * P.DEFENDER_ADVANTAGE * dw
        share = att / np.maximum(att + dfd, 1e-9)
        cd = cultural_distances(w, lead, tb)
        g = np.array([w.grievance.get((s, x), 0.0) for x in tside])
        pr = P.WAR_BASE * (1 + P.WAR_SCARCITY * sc) * (2 * share) * (1 + P.WAR_CULTURE * cd) \
            * (1 + P.WAR_GRIEVANCE * np.minimum(g / 10, 3)) * (1 - 0.3 * np.minimum(d, 2) / 2) * new_leader
        sbin = min(int(sc * 4), 3)
        dbins = np.minimum(np.rint(d).astype(int), 3)
        st = w.war_stats["scarcity"].setdefault(sbin, [0, 0])
        st[0] += T
        for bn, cnt in zip(*np.unique(dbins, return_counts=True)):
            w.war_stats["distance"].setdefault(int(bn), [0, 0])[0] += int(cnt)
        k = int(np.argmax(pr))
        best, best_p = tb[k], float(pr[k])
        info = (seen[tids[k]], float(d[k]), sc, float(cd[k]), float(share[k]), float(g[k]), float(att[k]),
                float(dfd[k]), sbin, int(dbins[k]))
        if best is None or rng.random() >= min(1.0, best_p / P.WAR_CONSIDER):
            continue
        b, d, sc, cd, share, g, att, dfd, sbin, dbin = info
        for key, bn in (("scarcity", sbin), ("distance", dbin)):
            w.war_stats[key][bn][1] += 1
        _fight(w, rng, s, mem, b, best, d, sc, cd, share, g, att, dfd, is_pol, pol, sizes, fighters)
    del w.war_log[:-40000]


def _fight(w, rng, s, mem, b, t, d, sc, cd, share, g, att, dfd, is_pol, pol, sizes, fighters):
    from . import polity
    ts = side_of(w, t)
    an = w.band_name(w.bands[pol.seat]) if is_pol else w.band_name(b)
    tn = w.band_name(t)
    reasons = []
    if sc > 0:
        reasons.append(f"hunger at home (scarcity {sc:.2f})")
    reasons.append(f"strength {share:.0%} of the fighters on both sides")
    if cd > 0.3:
        reasons.append(f"a different people (cultural distance {cd:.2f})")
    if g >= 1:
        reasons.append(f"revenge for {g:.0f} remembered killings")
    causes = [{"note": f"{an} attacked {tn}: " + "; ".join(reasons)}]
    if is_pol:
        causes.append({"event": pol.founding_event})
    win = rng.random() < share ** P.WAR_DECISIVENESS / (share ** P.WAR_DECISIVENESS + (1 - share) ** P.WAR_DECISIVENESS)
    eid = w.event("war", cell=t.cell, band=b.id, causes=causes, target=t.id, attacker_polity=s[1] if is_pol else -1,
                  defender_polity=ts[1] if ts[0] == "p" else -1, won=bool(win))
    fa = att / max(1.0, 1 + P.WARRIOR_STRENGTH * (pol.inst[polity.WARRIORS] if is_pol else 0))
    loss_a = P.WAR_LOSS * fa * (1 - share) * (0.5 if win else 1.0)
    loss_d = P.WAR_LOSS * fighters.get(t.id, 0.0) * share * (1.5 if win else 0.7)
    da = _kill(w, b, rng.poisson(loss_a), eid, rng)
    dd = _kill(w, t, rng.poisson(loss_d * (1 + 0.15)), eid, rng, men_share=0.8)
    w.grievance[(ts, s)] = w.grievance.get((ts, s), 0.0) + dd
    w.grievance[(s, ts)] = w.grievance.get((s, ts), 0.0) + da
    outcome = 0
    took = 0.0
    caps = 0
    if win:
        outcome = 1
        took = P.RAID_TAKE * max(t.store, 0.0)
        t.store -= took
        b.store += took
        caps = _captives(w, t, b, P.CAPTIVE_SHARE, rng)
        # conquest: a polity or village of farmers may take a farming village (and with its seat, a polity)
        if (is_pol or w.farm_share[b.id] >= 0.5) and w.farm_share[t.id] >= 0.5:
            want = P.CONQUEST_CHANCE * (1.5 if is_pol and pol.inst[polity.WARRIORS] else 1.0)
            if rng.random() < want:
                outcome = _conquer(w, b, t, s, ts, is_pol, pol, eid)
    w.war_log.append([w.year, b.id, t.id, round(sc, 3), round(d, 2), round(cd, 3), round(share, 3), outcome,
                      da, dd, int(is_pol)])
    w.events[eid]["data"].update(outcome=OUTCOMES[outcome], attacker_deaths=da, defender_deaths=dd,
                                 food_taken=round(took, 1), captives=caps)
    if win and ts[0] == "p" and w.polities[ts[1]].alive:
        dp = w.polities[ts[1]]
        dp.defeated_until = max(dp.defeated_until, w.t + P.DEFEAT_YEARS * P.TICKS_PER_YEAR)


def _conquer(w, b, t, s, ts, is_pol, pol, eid) -> int:
    from . import polity
    if not is_pol:
        pol = polity._new_polity(w, b, [{"event": eid}], why="conquest")
        s = ("p", pol.id)
    seat_fell = ts[0] == "p" and w.polities[ts[1]].alive and w.polities[ts[1]].seat == t.id
    moved = [t]
    if seat_fell:
        dp = w.polities[ts[1]]
        moved = polity.members_of(w, dp.id)
        dp.alive = False
        dp.ended = w.t
        w.event("polity_ended", cell=t.cell, band=t.id, polity=dp.id, why="conquered",
                causes=[{"event": eid}])
    for x in moved:
        w.polity_of[x.id] = pol.id
        if x.id == t.id or not seat_fell:
            w.polity_via[x.id] = b.id
        w.conquered_at[x.id] = w.t
    w.event("conquest", cell=t.cell, band=t.id, causes=[{"event": eid}], polity=pol.id, settlements=len(moved),
            whole_polity=bool(seat_fell))
    return 3 if seat_fell else 2


def to_json(w):
    return {"grievance": [[list(a), list(b), v] for (a, b), v in w.grievance.items()],
            "war_log": w.war_log[-20000:],
            "war_stats": {k: {str(b): v for b, v in d.items()} for k, d in w.war_stats.items()}}


def from_json(w, d):
    w.grievance = {(tuple(a), tuple(b)): v for a, b, v in d.get("grievance", [])}
    w.war_log = d.get("war_log", [])
    ws = d.get("war_stats", {})
    w.war_stats = {k: {int(b): v for b, v in ws.get(k, {}).items()} for k in ("scarcity", "distance")}
