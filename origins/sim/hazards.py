"""Natural hazards and disease outbreaks, and rare sea crossings.

Hazards are drawn each year for every land cell from where they can happen
(rivers flood, dry vegetation burns, volcanic belts erupt, plate boundaries
shake). Their effects on wild food recover over the following years
(hazard_food); deaths they cause are recorded with the hazard's event so
every death can be explained. Hazards in unpeopled land change the land but
are not logged as events.

Outbreaks start more often where people are crowded together, spread only
through contact (bands within the two-ring partner network), and leave
survivors immune for a while.

Sea crossings: a crowded coastal band whose land offers no relief may cross
one stretch of sea (one ocean cell, about 50 km) to empty land that is
visible on the far side.

reads: planet (biome, river, volcanic, seismic, coast), bands, region_factor, stock
writes: hazard_food, hazard_event, immune, hazards, region_z, people/groups (deaths), bands (cell), events
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..state import C
from ..worldgen import B

FIRE_BIOMES = [B["grassland"], B["savanna"], B["boreal_forest"], B["temperate_forest"], B["tropical_forest"]]


def _ring(nb, cells, k):
    s = set(int(c) for c in cells)
    front = set(s)
    for _ in range(k):
        nxt = set()
        for c in front:
            nxt.update(int(x) for x in nb[c] if x >= 0)
        nxt -= s
        s |= nxt
        front = nxt
    return s


def _occupancy(w):
    occ = {}
    for b in w.living_bands():
        occ.setdefault(b.cell, []).append(b)
    return occ


def kill_share(w, cell_probs: dict, cause: str, event_id: int, rng, occ=None) -> int:
    """Each person in each cell dies with the given probability; returns deaths."""
    from . import demography
    from .groups import AGE_GROUP
    if not cell_probs:
        return 0
    p = w.people
    G = w.groups
    code = C[cause]
    n = 0
    cells = np.fromiter(cell_probs.keys(), dtype=np.int64, count=len(cell_probs))
    probs = np.fromiter(cell_probs.values(), dtype=float, count=len(cell_probs))
    idx = w.alive_idx()
    if len(idx):
        cell, _ = demography._band_info(w)
        pc = cell[p.band[idx]]
        sel = np.isin(pc, cells)
        if sel.any():
            cand = idx[sel]
            pr = np.zeros(w.planet.n)
            pr[cells] = probs
            hit = cand[rng.random(len(cand)) < pr[pc[sel]]]
            if len(hit):
                demography.kill(w, hit, np.full(len(hit), code, dtype=np.int8))
                p.death_hazard[hit] = event_id
                n += len(hit)
    if occ is None:
        occ = _occupancy(w)
    in_cells = [b for c in sorted(cell_probs) for b in occ.get(c, ())]
    for b in in_cells:
        if b.mode != "group" or not b.alive:
            continue
        g = b.group
        for X in (G.F, G.M):
            cnt = np.rint(X[g]).astype(np.int64)
            d = rng.binomial(cnt, cell_probs[b.cell])
            if d.any():
                X[g] -= d
                k = int(d.sum())
                n += k
                w.counts["deaths"] += k
                w.accum["deaths_by_cause"][code] += k
                w.accum["deaths"] += np.bincount(AGE_GROUP, weights=d, minlength=18)
    return n


def _log(w, kind, cell, note, deaths, **data):
    return w.event(kind, cell=cell, causes=[{"note": note}], deaths=int(deaths), **data)


def yearly(w):
    rng = w.rng["hazards"]
    pl = w.planet
    nb = pl.grid.neighbours
    land = pl.land
    # recovery of land struck in earlier years
    w.hazard_food += P.HAZARD_RECOVERY * (1.0 - w.hazard_food)
    w.hazard_food[np.abs(w.hazard_food - 1.0) < 1e-3] = 1.0
    w.immune *= (1 - P.IMMUNITY_LOSS)
    occ = _occupancy(w)
    wet = w.region_factor[pl.region]
    u = rng.random((5, pl.n))
    year_deaths = 0

    def count(kind):
        w.counts["hz_" + kind] = w.counts.get("hz_" + kind, 0) + 1

    def struck(cells, food, note, kind, death_p, ring_p=0.0, **data):
        nonlocal year_deaths
        count(kind)
        cells = sorted(cells)
        w.hazard_food[cells] = np.minimum(w.hazard_food[cells], food)
        peopled = [c for c in cells if c in occ]
        if not peopled:
            return
        eid = w.event(kind, cell=peopled[0], causes=[{"note": note}], cells=len(cells), **data)
        w.hazard_event[cells] = eid
        probs = {c: death_p for c in peopled}
        if ring_p:
            for c in _ring(nb, peopled, 1):
                if c in occ and c not in probs:
                    probs[c] = ring_p
        d = kill_share(w, probs, kind_cause[kind], eid, rng, occ)
        w.events[eid]["data"]["deaths"] = d
        year_deaths += d

    kind_cause = {"flood": "flood", "wildfire": "wildfire", "eruption": "volcanic eruption",
                  "earthquake": "earthquake"}
    # floods: rivers, more likely in wet years
    p_flood = np.where(pl.river & land, P.FLOOD_RATE * np.clip(wet, 0.5, 1.5) ** 3, 0.0)
    for c in np.nonzero(u[0] < p_flood)[0]:
        struck([int(c)], P.FLOOD_FOOD, f"the river flooded in a {'wet' if wet[c] > 1.1 else 'normal'} year",
               "flood", P.FLOOD_DEATHS)
    # wildfire: dry vegetation, far more likely in dry years; spreads to some neighbours
    fire_ok = np.isin(pl.biome, FIRE_BIOMES) & land
    dryness = np.clip(1.0 / np.maximum(wet, 0.3), 0.5, 2.5) ** 3 * np.clip(1500.0 / np.maximum(pl.rain, 100), 0.3, 3)
    p_fire = np.where(fire_ok, P.FIRE_RATE * dryness, 0.0)
    for c in np.nonzero(u[1] < p_fire)[0]:
        burn = {int(c)} | {int(x) for x in nb[c] if x >= 0 and fire_ok[x] and rng.random() < 0.4}
        struck(burn, P.FIRE_FOOD, f"wildfire in {'a dry year' if wet[c] < 0.9 else 'dry season'}",
               "wildfire", P.FIRE_DEATHS)
    # volcanic eruptions
    if pl.volcanic is not None:
        p_erupt = np.where(pl.volcanic & land, P.ERUPTION_RATE, 0.0)
        for c in np.nonzero(u[2] < p_erupt)[0]:
            c = int(c)
            count("eruption")
            large = rng.random() < P.LARGE_ERUPTION
            ash = sorted(_ring(nb, [c], 4 if large else 2) - {c})
            w.hazard_food[c] = min(w.hazard_food[c], P.ERUPTION_FOOD)
            w.hazard_food[ash] = np.minimum(w.hazard_food[ash], P.ASH_FOOD)
            probs = {x: P.ERUPTION_DEATHS / 10 for x in ash if x in occ}
            if c in occ:
                probs[c] = P.ERUPTION_DEATHS
            if probs:
                eid = w.event("eruption", cell=c, causes=[{"note": ("a large" if large else "a") +
                                                                   " volcanic eruption; ash fell over the land around"}],
                              cells=len(ash) + 1, large=bool(large))
                w.hazard_event[[c] + ash] = eid
                d = kill_share(w, probs, "volcanic eruption", eid, rng, occ)
                w.events[eid]["data"]["deaths"] = d
            if large:
                regions = sorted({int(pl.region[x]) for x in _ring(nb, [c], 8)})
                w.region_z[regions] -= P.ERUPTION_COOLING
    # earthquakes
    if pl.seismic is not None:
        p_quake = np.where(pl.seismic & land, P.QUAKE_RATE, 0.0)
        for c in np.nonzero(u[3] < p_quake)[0]:
            struck([int(c)], 1.0, "an earthquake on a plate boundary", "earthquake", P.QUAKE_DEATHS,
                   ring_p=P.QUAKE_DEATHS / 4)
    outbreaks(w, rng, occ)
    crossings(w)


def outbreaks(w, rng, occ):
    nb = w.planet.grid.neighbours
    from .language import ring2
    r2 = ring2(w)
    sizes = w.band_sizes()
    pop = {c: float(sum(sizes[b.id] for b in bs)) for c, bs in occ.items()}
    # spread or end existing outbreaks
    still = []
    for ob in w.hazards:
        if ob["kind"] != "outbreak":
            continue
        new = set()
        for c in ob["front"]:
            for m in r2[c]:
                m = int(m)
                if m in pop and m not in ob["seen"] and rng.random() < P.OUTBREAK_SPREAD * (1 - w.immune[m]):
                    new.add(m)
        if new:
            w.counts["ob_contact_infections"] = w.counts.get("ob_contact_infections", 0) + len(new)
            _strike_outbreak(w, rng, ob, sorted(new), occ)
            still.append(ob)
        else:
            w.events[ob["event"]]["data"]["ended"] = w.t
    w.hazards = still
    # exposure accounting for gate G1 check 9: peopled cells in contact with an outbreak vs not
    exposed = set()
    for ob in still:
        for c in ob["front"]:
            exposed.update(int(m) for m in r2[c] if int(m) in pop and int(m) not in ob["seen"])
    w.counts["ob_contact_cell_years"] = w.counts.get("ob_contact_cell_years", 0) + len(exposed)
    w.counts["ob_other_cell_years"] = w.counts.get("ob_other_cell_years", 0) + len(set(pop) - exposed)
    # new outbreaks, more likely where people are crowded
    for c in sorted(pop):
        dens = pop[c] / max(w.planet.capacity[c], 1.0)
        village = any(w.farm_share[b.id] >= 0.5 for b in occ[c])
        mult = P.VILLAGE_OUTBREAK if village else P.FORAGER_OUTBREAK
        if rng.random() < P.OUTBREAK_RATE * mult * pop[c] / 100.0 * max(dens, 0.2) * (1 - w.immune[c]):
            eid = w.event("outbreak", cell=c, causes=[{"note": f"a new illness appeared among {int(pop[c])} people "
                                                               f"living at {dens:.0%} of the land's food supply"}],
                          cells=0, deaths=0, severity=round(float(rng.uniform(0.3, 1.0)), 2))
            w.counts["ob_new_starts"] = w.counts.get("ob_new_starts", 0) + 1
            ob = {"kind": "outbreak", "event": eid, "front": [], "seen": [], "severity": w.events[eid]["data"]["severity"]}
            _strike_outbreak(w, rng, ob, [c], occ)
            w.hazards.append(ob)


def _strike_outbreak(w, rng, ob, cells, occ):
    sev = ob["severity"]
    probs = {c: P.OUTBREAK_DEATHS * sev * (1 - w.immune[c]) for c in cells}
    d = kill_share(w, probs, "disease outbreak", ob["event"], rng, occ)
    for c in cells:
        w.immune[c] = max(w.immune[c], P.OUTBREAK_IMMUNITY)
        w.hazard_event[c] = ob["event"]
    ob["front"] = list(cells)
    ob["seen"] = sorted(set(ob["seen"]) | set(cells))
    e = w.events[ob["event"]]["data"]
    e["cells"] = len(ob["seen"])
    e["deaths"] += d


def crossings(w):
    """A crowded coastal band with no better land nearby may cross one ocean cell to visible empty land."""
    rng = w.rng["crossing"]
    pl = w.planet
    nb = pl.grid.neighbours
    occ = _occupancy(w)
    sizes = w.band_sizes()
    for b in list(w.living_bands()):
        if not pl.coast[b.cell] or b.last_ratio >= P.CROSSING_HUNGER:
            continue
        here = w.stock[b.cell] / max(sum(sizes[o.id] for o in occ.get(b.cell, [])), 1)
        land_nb = [int(x) for x in nb[b.cell] if x >= 0 and pl.land[x]]
        if any(w.stock[x] / (sum(sizes[o.id] for o in occ.get(x, [])) + sizes[b.id]) > here * P.MOVE_THRESHOLD
               for x in land_nb):
            continue                                  # relief on foot: no need to put to sea
        far = set()
        for x in nb[b.cell]:
            if x >= 0 and not pl.land[x]:
                far.update(int(y) for y in nb[x] if y >= 0 and pl.land[y] and y not in occ and y != b.cell)
        far -= set(land_nb)
        # reachable but only by sea: not connected on foot within two steps
        far = [c for c in sorted(far) if c not in _ring(nb, [b.cell], 2) or not _walkable(pl, nb, b.cell, c)]
        if not far or rng.random() >= P.CROSSING_RATE:
            continue
        target = max(far, key=lambda c: (w.stock[c], -c))
        src = b.cell
        b.cell = target
        b.trail = (b.trail + [(w.t, target)])[-40:]
        b.last_move = "crossed the sea to land seen on the far side"
        w.reveal_pending.add(b.id)
        w.event("sea_crossing", cell=target, band=b.id,
                causes=[{"note": f"{w.band_name(b)} received only {b.last_ratio:.0%} of its food needs on a crowded "
                                 f"coast with no better land within reach on foot; land was visible across about "
                                 f"50 km of sea"}], origin=src, size=int(sizes[b.id]))
        occ.setdefault(target, []).append(b)


def _walkable(pl, nb, a, c):
    """True if c can be reached from a over land within two steps."""
    for x in nb[a]:
        if x >= 0 and pl.land[x] and (x == c or c in nb[x]):
            return True
    return False
