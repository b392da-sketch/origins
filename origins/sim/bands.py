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
    live = w.living_bands()
    ids, _pos = w.live_index()
    sz = np.rint(w.live_sizes()).astype(np.int64).tolist()     # aligned with live
    fsv = (w.farm_share[ids] >= 0.5).tolist()
    occupied: dict[int, float] = {}
    for k, b in enumerate(live):
        occupied[b.cell] = occupied.get(b.cell, 0) + float(sz[k])
    group_at = {}
    for k, b in enumerate(live):
        key = (b.cell, fsv[k])
        if b.mode == "group" and key not in group_at:
            group_at[key] = b
    for k, b in enumerate(live):
        s = sz[k]
        limit = P.GROUP_FISSION_SIZE if b.mode == "group" else P.FISSION_SIZE
        if b.village:
            limit = max(limit, P.VILLAGE_FISSION_SIZE)
        if 0 < s <= limit and (s < P.STRESS_FISSION_MIN or b.last_ratio >= P.STRESS_FISSION_RATIO):
            continue
        if s == 0:
            end_band(w, b, "no surviving members")
            continue
        stressed = s >= P.STRESS_FISSION_MIN and b.last_ratio < P.STRESS_FISSION_RATIO
        if not (s > limit or stressed):
            continue
        target = _best_cell(w, b.cell, s // 2, occupied)
        if b.village:
            from .farming import best_farm_cell
            target = best_farm_cell(w, b, occupied)
            if target is None:
                continue
        if s <= limit:
            here = w.stock[b.cell] / max(occupied.get(b.cell, s), 1)
            there = w.stock[target] / (occupied.get(target, 0) + s // 2)
            if target == b.cell or there < 1.3 * here:
                continue
        if b.mode == "group" and target == b.cell:
            continue          # a local population splitting within its own land would only be recombined at once
        if b.mode == "group":
            now = w.groups.total(b.group)          # current size: this group may already have taken people in this season
            dst = group_at.get((target, fsv[k]))
            if dst is not None and dst.alive and dst.id != b.id:
                # people moving into a neighbouring local population join it directly (the same result as
                # splitting off a new group that then combines with it, without creating a band record)
                count = groups.transfer(w, b, dst, rng)
                if count == 0:
                    continue
                frac = min(1.0, count / max(now, 1e-9))
                share = b.store * frac
                dst.store, b.store = dst.store + share, b.store - share
                crop = w.crop_store[b.id] * frac
                w.crop_store[dst.id] += crop
                w.crop_store[b.id] -= crop
                occupied[b.cell] -= count
                occupied[target] = occupied.get(target, 0) + count
                w.counts["group_splits"] = w.counts.get("group_splits", 0) + 1
                continue
            res = groups.split(w, b, target, rng)
            if res is None:
                continue
            nb_, count = res
            group_at[(target, fsv[k])] = nb_
        else:
            mem = w.members(b.id)
            units = _households(w, mem)
            moving, count = [], 0
            for k in rng.permutation(len(units)):
                if count >= s / 2:
                    break
                moving += units[int(k)]
                count += len(units[int(k)])
            now = len(mem)
            if count == 0 or count == now:
                continue
            moving = np.array(moving)
            leader = int(moving[np.argmin(p.birth[moving])])
            nb_ = w.new_band(target, parent=b.id, leader=leader)
            p.band[moving] = nb_.id
            w.people_changed()
        frac = min(1.0, count / max(now, 1e-9))
        share = b.store * frac
        nb_.store, b.store = share, b.store - share
        crop = w.crop_store[b.id] * frac               # the standing crop is shared with the people
        w.crop_store[nb_.id] += crop
        w.crop_store[b.id] -= crop
        nb_.last_ratio = b.last_ratio
        occupied[b.cell] -= count
        occupied[target] = occupied.get(target, 0) + count
        if s > limit:
            why = f"{w.band_name(b)} grew to {s} people ({'groups' if b.mode == 'group' else 'bands'} split above {limit})"
        else:
            why = (f"{w.band_name(b)} ({s} people) received only {b.last_ratio:.0%} of its food needs; "
                   f"better land nearby")
        if b.mode == "group":
            # a group splitting is people spreading within a local population: counted, not logged
            w.counts["group_splits"] = w.counts.get("group_splits", 0) + 1
            continue
        w.event("fission", cell=target, band=b.id, causes=[{"note": why}],
                new_band=nb_.id, moved=int(count), stayed=int(s - count))
    nbr = w.planet.grid.neighbours
    live = w.living_bands()
    ids, _pos = w.live_index()
    sizes = dict(zip(ids.tolist(), np.rint(w.live_sizes()).astype(np.int64).tolist()))
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
        if not others:
            continue
        o = max(others, key=lambda o: (float(sizes[o.id]), -o.id))
        if b.mode == "individual" and o.mode == "individual":
            mem = w.members(b.id)
            p.band[mem] = o.id
            if b.language != o.language:          # joining another people: they take up its speech
                p.lang[mem] = o.language
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
    first: dict[tuple, object] = {}
    for b in w.living_bands():
        if b.mode != "group":
            continue
        # villages and foragers sharing land stay separate peoples (different ways of life, different stores)
        key = (b.cell, bool(w.farm_share[b.id] >= 0.5))
        o = first.get(key)
        if o is None:
            first[key] = b
            continue
        groups.merge_into(w, b, o)
        o.store += b.store
        b.store = 0.0
        w.crop_store[o.id] += w.crop_store[b.id]     # the standing crop goes with the people
        w.crop_store[b.id] = 0.0
        b.alive = False
        b.ended = w.t
        del b.trail[:-3]
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
    # Who is followed person by person depends only on the world, never on what the observer is watching:
    # bands farthest from the centres of rule (the seats of chiefdoms and states) fold first; before there are
    # any, those farthest from the people's first home.
    sizes = np.bincount(w.people.band[w.alive_idx()], minlength=w.next_band)
    seats = {p.seat for p in getattr(w, "polities", {}).values() if p.alive and p.tier >= 1}
    focus_cells = sorted({w.bands[s].cell for s in seats}) or [int(w.planet.start_cell)]
    fx = xyz[np.array(focus_cells)]
    focus = focus_cells[0]
    cands = [b for b in w.living_bands() if b.mode == "individual" and b.id not in seats]
    near = {b.id: float((fx @ xyz[b.cell]).max()) for b in cands}
    cands.sort(key=lambda b: (near[b.id], b.id))   # farthest from every centre first
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
    del b.trail[:-3]                  # ended bands keep only their last steps (memory)
    w.bands_changed()
    b.ended = w.t
    if b.store:
        w.ledger["spoiled"] += b.store
        b.store = 0.0
    if log:
        p = w.people
        # members who died (not those who were folded into a group, who are no longer followed one by one)
        dead = np.nonzero((p.band[:p.n] == b.id) & ~p.alive[:p.n] & (p.death[:p.n] >= 0))[0]
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
