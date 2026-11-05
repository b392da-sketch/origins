"""Band fission, merging, extinction and map discovery.

reads: people (band, mother, partner, age), bands, stock, planet
writes: people.band, bands (new, merged, ended), known, discovered_by/at, events
"""
from __future__ import annotations

import numpy as np

from .. import params as P


def _households(w, members):
    """Group members into households: a woman with her partner and children under 15."""
    p = w.people
    age = w.ages(members)
    mset = set(int(x) for x in members)
    by_mother: dict[int, list] = {}
    for i, a in zip(members, age):
        m = int(p.mother[i])
        if a < 15 and m in mset:
            by_mother.setdefault(m, []).append(int(i))
    assigned, units = set(), []
    for i, a in zip(members, age):
        i = int(i)
        if p.sex[i] == 0 and a >= P.FEMALE_MIN_AGE and i not in assigned:
            u = [i]
            j = int(p.partner[i])
            if j in mset and j not in assigned:
                u.append(j)
            u += [k for k in by_mother.get(i, ()) if k not in assigned]
            assigned.update(u)
            units.append(u)
    where = {i: k for k, u in enumerate(units) for i in u}
    for i, a in zip(members, age):
        i = int(i)
        if i in assigned:
            continue
        f = int(p.father[i])
        if a < 15 and f in where:
            units[where[f]].append(i)
            where[i] = where[f]
        else:
            units.append([i])
            where[i] = len(units) - 1
        assigned.add(i)
    return units


def _best_cell(w, cell, size, occupied):
    nb = w.planet.grid.neighbours
    best, best_val = cell, w.stock[cell] / (occupied.get(cell, 0) + size)
    for m in nb[cell]:
        if m < 0 or not w.planet.land[m]:
            continue
        val = w.stock[m] / (occupied.get(int(m), 0) + size)
        if val > best_val:
            best, best_val = int(m), val
    return best


def fission_and_merge(w):
    from . import groups
    p = w.people
    rng = w.rng["fission"]
    sizes = np.rint(w.band_sizes()).astype(np.int64)
    live = w.living_bands()
    occupied: dict[int, float] = {}
    for b in live:
        occupied[b.cell] = occupied.get(b.cell, 0) + float(sizes[b.id])
    for b in live:
        s = int(sizes[b.id])
        limit = P.GROUP_FISSION_SIZE if b.mode == "group" else P.FISSION_SIZE
        if 0 < s <= limit and (s < P.STRESS_FISSION_MIN or b.last_ratio >= P.STRESS_FISSION_RATIO):
            continue
        if s == 0:
            end_band(w, b, "no surviving members")
            continue
        stressed = s >= P.STRESS_FISSION_MIN and b.last_ratio < P.STRESS_FISSION_RATIO
        if not (s > limit or stressed):
            continue
        target = _best_cell(w, b.cell, s // 2, occupied)
        if s <= limit:
            here = w.stock[b.cell] / max(occupied.get(b.cell, s), 1)
            there = w.stock[target] / (occupied.get(target, 0) + s // 2)
            if target == b.cell or there < 1.3 * here:
                continue
        if b.mode == "group":
            res = groups.split(w, b, target, rng)
            if res is None:
                continue
            nb_, count = res
        else:
            mem = w.members(b.id)
            units = _households(w, mem)
            moving, count = [], 0
            for k in rng.permutation(len(units)):
                if count >= s / 2:
                    break
                moving += units[int(k)]
                count += len(units[int(k)])
            if count == 0 or count == s:
                continue
            moving = np.array(moving)
            leader = int(moving[np.argmin(p.birth[moving])])
            nb_ = w.new_band(target, parent=b.id, leader=leader)
            p.band[moving] = nb_.id
            w.people_changed()
        share = b.store * count / s
        nb_.store, b.store = share, b.store - share
        nb_.last_ratio = b.last_ratio
        occupied[b.cell] -= count
        occupied[target] = occupied.get(target, 0) + count
        if s > limit:
            why = f"{w.band_name(b)} grew to {s} people ({'groups' if b.mode == 'group' else 'bands'} split above {limit})"
        else:
            why = (f"{w.band_name(b)} ({s} people) received only {b.last_ratio:.0%} of its food needs; "
                   f"better land nearby")
        w.event("fission", cell=target, band=b.id, causes=[{"note": why}],
                new_band=nb_.id, moved=int(count), stayed=int(s - count))
    sizes = np.rint(w.band_sizes()).astype(np.int64)
    nbr = w.planet.grid.neighbours
    live = w.living_bands()
    by_cell: dict[int, list] = {}
    for o in live:
        by_cell.setdefault(o.cell, []).append(o)
    for b in [b for b in live if sizes[b.id] < P.MERGE_SIZE]:
        if not b.alive:
            continue
        s = int(sizes[b.id])
        if s == 0:
            end_band(w, b, "no surviving members")
            continue
        if s >= P.MERGE_SIZE:
            continue
        near = {b.cell} | {int(x) for x in nbr[b.cell] if x >= 0}
        others = [o for c in near for o in by_cell.get(c, ()) if o.alive and o.id != b.id and sizes[o.id] > 0]
        # never fold the followed band through a merge
        others = [o for o in others if (o.mode == b.mode) or w.follow not in (o.id, b.id)]
        if not others:
            continue
        o = max(others, key=lambda o: (float(sizes[o.id]), -o.id))
        if b.mode == "individual" and o.mode == "individual":
            mem = w.members(b.id)
            p.band[mem] = o.id
            w.people_changed()
        else:
            groups.merge_into(w, b, o)
        sizes[o.id] += s
        sizes[b.id] = 0
        o.store += b.store
        b.store = 0.0
        w.event("merge", cell=o.cell, band=b.id,
                causes=[{"note": f"{w.band_name(b)} shrank to {s} people (below {P.MERGE_SIZE}) "
                                 f"and joined {w.band_name(o)}"}], into=o.id, size=int(s))
        end_band(w, b, "merged", log=False)
    consolidate_groups(w)
    w.people_changed()


def consolidate_groups(w):
    """Groups sharing a cell become one local population (a change of representation, not a social event)."""
    from . import groups
    first: dict[int, object] = {}
    for b in w.living_bands():
        if b.mode != "group":
            continue
        o = first.get(b.cell)
        if o is None:
            first[b.cell] = b
            continue
        groups.merge_into(w, b, o)
        o.store += b.store
        b.store = 0.0
        b.alive = False
        b.ended = w.t
        b.last_move = f"combined with {w.band_name(o)} (same land)"
        w.counts["consolidated"] = w.counts.get("consolidated", 0) + 1
        w.bands_changed()


def fold_distant(w):
    """Keep individuals under the threshold by folding the bands farthest from the focus."""
    from . import groups
    n_ind = len(w.alive_idx())
    if n_ind <= P.INDIVIDUAL_THRESHOLD:
        return
    xyz = w.planet.grid.xyz
    focus = w.bands[w.follow].cell if w.follow >= 0 and w.bands[w.follow].alive else w.planet.start_cell
    sizes = np.bincount(w.people.band[w.alive_idx()], minlength=w.next_band)
    cands = [b for b in w.living_bands() if b.mode == "individual" and b.id != w.follow]
    cands.sort(key=lambda b: (float(xyz[b.cell] @ xyz[focus]), b.id))   # farthest first
    target = P.FOLD_TARGET * P.INDIVIDUAL_THRESHOLD
    folded = 0
    for b in cands:
        if n_ind <= target:
            break
        n_ind -= int(sizes[b.id])
        folded += int(sizes[b.id])
        groups.fold(w, b)
    if folded:
        w.event("fold", cell=focus, causes=[{"note": f"more than {P.INDIVIDUAL_THRESHOLD:,} individuals; "
                                                     f"{folded:,} people in distant bands now followed as groups"}],
                folded=folded)


def end_band(w, b, why, log=True):
    b.alive = False
    w.bands_changed()
    b.ended = w.t
    if b.store:
        w.ledger["spoiled"] += b.store
        b.store = 0.0
    if log:
        p = w.people
        dead = np.nonzero((p.band[:p.n] == b.id) & ~p.alive[:p.n])[0]
        causes = [{"note": why}]
        if len(dead):
            last = int(dead[np.argmax(p.death[dead])])
            causes.append({"death": last})
        w.event("band_extinct", cell=b.cell, band=b.id, causes=causes)


def reveal(w):
    nb = w.planet.grid.neighbours
    pending = [w.bands[i] for i in sorted(w.reveal_pending) if w.bands[i].alive]
    w.reveal_pending.clear()
    for b in pending:
        cells = [b.cell] + [int(x) for x in nb[b.cell] if x >= 0]
        for c in cells:
            if not w.known[c]:
                w.known[c] = True
                w.discovered_by[c] = b.id
                w.discovered_at[c] = w.t
