"""Diseases from animals (M4 specification section 6; Ben's decisions of 20 November 2026; build notes "Diseases from
domestic animals: literature check" and "comparing the two literature checks").

Named diseases replace M1's anonymous outbreaks (DISEASE False keeps the old ones, the knock-out).

- **Emergence in two steps** (Lloyd-Smith et al. 2009): pressure from an animal source, then a chancy start of spread
  among people. Pressure from herds grows with the people herding a species on a cell and with how long that species
  has been domesticated anywhere (Morand, McIntyre & Baylis 2014: shared diseases rise with time since
  domestication). A smaller pressure from wild animals exists everywhere people live (the Americas had tuberculosis
  and treponemes before contact: Bos et al. 2014; Barquera et al. 2025). No fixed rate is claimed by the literature;
  the rates here are starting values.
- **Each disease is named and has its own traits**, drawn when it appears: the share of those who can catch it who do
  in an epidemic; deaths per case by age; how many people who can still catch it a region needs to keep it going
  (so the critical community size emerges: Bartlett 1960; Black 1966); whether immunity lasts; how much hunger raises
  its deaths (Ben: per disease; Mokyr & O Grada 2002: uneven by disease).
- **Immunity per band by age** (children under 15, adults): survivors are immune; each year the oldest children
  become adults and newborns arrive with no immunity, so a disease that stays shifts to children (Panum's Faroes).
- **Persistence and spread**: a disease circulating on a cell this year keeps going next year with a chance that
  rises with the people who can still catch it on the cell and its neighbours; otherwise it dies out there. It
  spreads along the contacts the world has: neighbouring cells within two rings, gift partners, traders' roads;
  more where hunger sets people moving (Mokyr & O Grada 2002). Linked places re-seed each other (Metcalf et al.
  2013).
- **Deaths**: by age, raised by hunger for diseases that depend on food, and raised again when so many adults are
  ill at once that care and food production fail (crisis deaths; Jones 2003; Shanks et al. 2011). No genetic
  weakness at first contact: heavy deaths come from everyone being able to catch it at once.
- **Responses** (Ben: flight and isolation now, blame with M4b): the custom "response to epidemics": "flight"
  (fewer caught here, more carried away), "isolate the sick" (as in the Acholi gemo, Hewlett & Amola 2003: fewer
  caught, less carried, a survivor to care). Their sizes are guesses: neither literature check found measured
  effects.

Each year, at the season of M1's outbreaks. Random draws from the "disease" stream only.

reads: bands, people and groups (ages), farm_share, skill, best crops and herds (farming), food ratio, customs,
       partners, trade links, first domestications
writes: w.diseases, w.dz_imm, w.dz_active, people/groups (deaths), events (new_disease, outbreak), counts
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..state import C

ND_CAP = 64                     # at most this many named diseases in one world
CHILD = 0                       # immunity columns: children (under 15), adults
ADULT = 1


def init(w):
    w.diseases = []                                                   # list of dicts (traits, origin, events)
    w.dz_imm = np.zeros((64, ND_CAP, 2), dtype=np.float32)           # band x disease x (child, adult): immune share
    w.dz_active = np.zeros((w.planet.n, ND_CAP), dtype=bool)         # circulating on the cell this year


def ensure(w, band_id: int, parent: int):
    if getattr(w, "dz_imm", None) is None:
        init(w)
    if band_id >= len(w.dz_imm):
        cap = len(w.dz_imm)
        while cap <= band_id:
            cap *= 2
        a = np.zeros((cap, ND_CAP, 2), dtype=np.float32)
        a[:len(w.dz_imm)] = w.dz_imm
        w.dz_imm = a
    if parent >= 0:
        w.dz_imm[band_id] = w.dz_imm[parent]                         # a daughter band shares its mother's history


def combine(w, src, dst, carriers: float):
    """People joining another band bring their immunity (shares weighted by numbers)."""
    if getattr(w, "dz_imm", None) is None or not w.diseases:
        return
    n_dst = float(w.band_sizes()[dst.id]) if dst.id < len(w.band_sizes()) else 0.0
    c = max(float(carriers), 0.0)
    if c <= 0:
        return
    wt = c / max(n_dst + c, 1.0)
    w.dz_imm[dst.id] = (1 - wt) * w.dz_imm[dst.id] + wt * w.dz_imm[src.id]


# ------------------------------------------------------------------ the year

def yearly(w):
    if not getattr(P, "DISEASE", False):
        return
    if getattr(w, "dz_imm", None) is None:
        init(w)
    rng = w.rng["disease"]
    bands = w.living_bands()
    if not bands:
        return
    if len(w.dz_imm) <= max(b.id for b in bands):
        ensure(w, max(b.id for b in bands), -1)
    nd = len(w.diseases)
    ids = np.array([b.id for b in bands])
    cells = np.array([b.cell for b in bands])
    sizes = w.band_sizes()[ids].astype(float)
    _age_and_wane(w, ids)
    n = w.planet.n
    # people who can still catch each disease, per cell
    sus = np.zeros((n, max(nd, 1)))
    if nd:
        s_band = sizes[:, None] * (P.DZ_CHILD_SHARE * (1 - w.dz_imm[ids, :nd, CHILD])
                                   + (1 - P.DZ_CHILD_SHARE) * (1 - w.dz_imm[ids, :nd, ADULT]))
        np.add.at(sus, cells, s_band)
    pop = np.bincount(cells, weights=sizes, minlength=n)
    nb = w.planet.grid.neighbours
    valid = nb >= 0
    nbi = np.where(valid, nb, 0)
    hunger = np.zeros(n)
    np.add.at(hunger, cells, sizes * np.array([max(0.0, 1.0 - b.last_ratio) for b in bands]))
    hunger = np.where(pop > 0, hunger / np.maximum(pop, 1.0), 0.0)
    active = np.zeros((n, ND_CAP), dtype=bool)
    source = {}                                                     # (cell, d) -> how it came
    # 1. persistence: last year's circulation keeps going where enough people can still catch it nearby
    for d in range(nd):
        prev = np.nonzero(w.dz_active[:, d])[0]
        if not len(prev):
            continue
        near = sus[prev, d] + np.where(valid[prev], sus[nbi[prev], d], 0.0).sum(axis=1)
        keep = rng.random(len(prev)) < 1.0 - np.exp(-near / w.diseases[d]["k"])
        for c in prev[keep].tolist():
            if pop[c] > 0:
                active[c, d] = True
                source[(c, d)] = "kept"
    # 2. spread along contacts
    contacts = _contacts(w, bands, cells)
    resp = _responses(w, ids)
    resp_cell = {}
    for i, c in enumerate(cells.tolist()):
        resp_cell.setdefault(c, []).append(resp[i])
    for d in range(nd):
        src = np.nonzero(active[:, d])[0]
        if not len(src):
            continue
        dz = w.diseases[d]
        for c in src.tolist():
            out = np.mean([P.DZ_FLIGHT_OUT if r == 1 else P.DZ_ISOLATE_OUT if r == 2 else 1.0
                           for r in resp_cell.get(c, [0])])
            chance = P.DZ_SPREAD * dz["attack"] * out * (1.0 + P.DZ_FAMINE_SPREAD * hunger[c])
            for m in contacts.get(c, ()):
                if active[m, d] or pop[m] <= 0:
                    continue
                share = sus[m, d] / max(pop[m], 1.0)
                if rng.random() < chance * share:
                    active[m, d] = True
                    source[(m, d)] = "contact"
                    w.counts["ob_contact_infections"] = w.counts.get("ob_contact_infections", 0) + 1
    # 3. spillover again from the animals that carry each disease (Ben, 20 November 2026: reservoirs)
    herders = _herders(w, ids, cells, sizes)
    _respill(w, rng, pop, herders, active, source)
    # 4. emergence: new diseases from herds and from wild animals
    _emerge(w, rng, bands, ids, cells, sizes, pop, active, source, herders)
    nd = len(w.diseases)
    # exposure accounting for gate G1 check 9 (as M1): peopled cells in contact with circulation vs not
    any_active = active[:, :nd].any(axis=1) if nd else np.zeros(n, dtype=bool)
    exposed = set()
    for c in np.nonzero(any_active)[0].tolist():
        exposed.update(m for m in contacts.get(c, ()) if pop[m] > 0 and not any_active[m])
    peopled = int((pop > 0).sum())
    w.counts["ob_contact_cell_years"] = w.counts.get("ob_contact_cell_years", 0) + len(exposed)
    w.counts["ob_other_cell_years"] = w.counts.get("ob_other_cell_years", 0) + peopled - len(exposed)
    # 5. epidemics where it circulates: deaths and immunity
    w.dz_active[:] = active
    if nd:
        _epidemics(w, rng, bands, ids, cells, sizes, active, resp, source)


def _age_and_wane(w, ids):
    """A year passes: the oldest children become adults and newborns arrive with no immunity; immunity that does not
    last wanes."""
    nd = len(w.diseases)
    if not nd:
        return
    a = w.dz_imm[ids, :nd]
    out = 1.0 / P.DZ_CHILD_YEARS
    turn = out * P.DZ_CHILD_SHARE / (1 - P.DZ_CHILD_SHARE)          # share of adults who were children last year
    adults = a[:, :, ADULT] * (1 - turn) + a[:, :, CHILD] * turn
    child = a[:, :, CHILD] * (1 - out)
    wane = np.array([0.0 if dz["lasting"] else P.DZ_WANE for dz in w.diseases])
    w.dz_imm[ids, :nd, ADULT] = adults * (1 - wane)
    w.dz_imm[ids, :nd, CHILD] = child * (1 - wane)


def _responses(w, ids) -> np.ndarray:
    from . import customs
    k = customs.NAMES.index("response to epidemics")
    if w.customs.shape[1] <= k:
        return np.zeros(len(ids), dtype=int)
    return w.customs[ids, k].astype(int)


def _contacts(w, bands, cells) -> dict:
    """Cell -> cells in contact: within two rings, gift partners' cells, traders' roads (seat to seat)."""
    from .language import ring2
    r2 = ring2(w)
    out = {}
    for c in set(cells.tolist()):
        out[c] = set(int(m) for m in r2[c] if int(m) != c)
    cell_of = {b.id: b.cell for b in bands}
    po = getattr(w, "partner_of", None)
    if po is not None:
        for b in bands:
            if b.id < len(po):
                for o in po[b.id]:
                    o = int(o)
                    if o >= 0 and o in cell_of and cell_of[o] != b.cell:
                        out[b.cell].add(cell_of[o])
    for link in getattr(w, "trade_links", []) or []:
        a, bb = int(link[0]), int(link[1])
        if a in cell_of and bb in cell_of and cell_of[a] != cell_of[bb]:
            out.setdefault(cell_of[a], set()).add(cell_of[bb])
            out.setdefault(cell_of[bb], set()).add(cell_of[a])
    return out


def _herders(w, ids, cells, sizes) -> dict:
    """(cell, species) -> people herding that domesticated species there (the band's farm share x its herd part)."""
    from . import farming
    share = np.clip(w.farm_share[ids], 0, 1)
    on = share > 0
    pressure = {}
    if on.any():
        _kp, vp, ka, va = farming.best_all(w, ids[on], cells[on])
        herd = sizes[on] * share[on] * np.where(vp + va > 0, va / np.maximum(vp + va, 1e-9), 0.0)
        dom = w.skill[ids[on], ka] >= 3
        for c, s, h, ok in zip(cells[on].tolist(), ka.tolist(), herd.tolist(), dom.tolist()):
            if ok and h > 0:
                pressure[(c, s)] = pressure.get((c, s), 0.0) + h
    return pressure


def _respill(w, rng, pop, herders, active, source):
    """A disease that has died out among people lives on in its animals and can pass to people again (Ben,
    20 November 2026, after the first trial: a disease that died out never came back). Herd diseases pass again
    where people herd their species; wild ones where people live in the region where they first appeared (their
    reservoir's range). Most such starts are short: in small groups an acute disease soon runs out of people who
    can catch it (Black 1975)."""
    from . import farming
    region = w.planet.region
    for d, dz in enumerate(w.diseases):
        if dz["host"] == "wild":
            cand = np.nonzero((region == region[dz["cell"]]) & (pop > 0) & ~active[:, d])[0]
            if not len(cand):
                continue
            hit = cand[rng.random(len(cand)) < P.DZ_RESPILL_WILD * pop[cand]]
        else:
            k = farming.SPECIES.index(dz["host"])
            cand = [(c, h) for (c, s), h in sorted(herders.items()) if s == k and not active[c, d]]
            if not cand:
                continue
            draw = rng.random(len(cand))
            hit = [c for (c, h), r in zip(cand, draw) if r < P.DZ_RESPILL_HERD * h]
        for c in np.asarray(hit, dtype=np.int64).tolist():
            active[c, d] = True
            source[(c, d)] = "spillover"
            w.counts["dz_spillovers"] = w.counts.get("dz_spillovers", 0) + 1


def _emerge(w, rng, bands, ids, cells, sizes, pop, active, source, herders=None):
    if len(w.diseases) >= ND_CAP:
        return
    from . import farming
    pressure = _herders(w, ids, cells, sizes) if herders is None else herders
    for (c, s), h in sorted(pressure.items()):
        name = farming.SPECIES[s]
        first = w.farm_firsts.get(name, {}).get("domestication")
        since = (w.t - w.events[first]["t"]) / P.TICKS_PER_YEAR if first is not None else 0.0
        together = min(1.0, since / P.DZ_DOM_YEARS)
        chance = P.DZ_EMERGE_HERD * h * together
        if rng.random() < chance and len(w.diseases) < ND_CAP:
            _new(w, rng, c, name, active, source,
                 f"{int(h)} people herding {farming.NAMES[name]} here, which people have kept for "
                 f"{int(since)} years", first)
    # wild animals, everywhere people live
    peopled = np.nonzero(pop > 0)[0]
    draw = rng.random(len(peopled))
    hit = peopled[draw < P.DZ_EMERGE_WILD * pop[peopled]]
    for c in hit.tolist():
        if len(w.diseases) >= ND_CAP:
            break
        _new(w, rng, int(c), "wild", active, source,
             f"a sickness passed from wild animals to {int(pop[c])} people here", None)


def _new(w, rng, cell, host, active, source, note, first_event):
    d = len(w.diseases)
    lo, hi = np.log(P.DZ_CFR_RANGE[0]), np.log(P.DZ_CFR_RANGE[1])
    cfr = float(np.exp(rng.uniform(lo, hi)))
    k_lo, k_hi = np.log(P.DZ_K_RANGE[0]), np.log(P.DZ_K_RANGE[1])
    traits = {
        "id": d, "host": host, "attack": round(float(rng.uniform(*P.DZ_ATTACK_RANGE)), 3),
        "cfr": round(cfr, 4), "child": round(float(rng.uniform(*P.DZ_CHILD_MULT_RANGE)), 2),
        "k": round(float(np.exp(rng.uniform(k_lo, k_hi))), 1), "lasting": bool(rng.random() < P.DZ_LASTING),
        "hunger": round(float(rng.uniform(*P.DZ_HUNGER_RANGE)), 2), "year": int(w.year), "cell": int(cell),
    }
    traits["name"] = _name(w, cell, host, d)
    causes = [{"note": note}]
    if first_event is not None:
        causes.append({"event": int(first_event)})
    traits["event"] = w.event("new_disease", cell=cell, causes=causes, disease=traits["name"], host=host,
                              deaths_per_case=traits["cfr"], lasting=traits["lasting"])
    w.diseases.append(traits)
    active[cell, d] = True
    source[(cell, d)] = "new"
    w.counts["ob_new_starts"] = w.counts.get("ob_new_starts", 0) + 1


def _name(w, cell, host, d) -> str:
    from . import farming
    what = farming.NAMES.get(host, "wild") if host != "wild" else "wild"
    return f"the {what} sickness ({d + 1})"


def _epidemics(w, rng, bands, ids, cells, sizes, active, resp, source):
    """Each band on a cell where a disease circulates: those who can catch it do, at the disease's attack share
    (less with flight or isolation); deaths by age; survivors immune."""
    nd = len(w.diseases)
    hunger = np.array([max(0.0, 1.0 - b.last_ratio) for b in bands])
    flight, isolate = resp == 1, resp == 2
    for d in range(nd):
        here = active[cells, d]
        if not here.any():
            continue
        dz = w.diseases[d]
        first = [s for (c, dd), s in source.items() if dd == d]
        eid = w.event("outbreak", cell=int(cells[np.nonzero(here)[0][0]]),
                      causes=[{"event": int(dz["event"])},
                              {"note": f"{dz['name']} circulating in {int(here.sum())} bands ({first.count('new')} "
                                       f"new, {first.count('spillover')} passed again from its animals, "
                                       f"{first.count('contact')} reached by contact, {first.count('kept')} "
                                       f"kept from last year)"}],
                      disease=dz["name"], cells=int(len(set(cells[here].tolist()))), deaths=0, severity=dz["cfr"])
        sel = np.nonzero(here)[0]
        bid = ids[sel]
        att = dz["attack"] * np.where(flight[sel], P.DZ_FLIGHT_ATTACK, np.where(isolate[sel], P.DZ_ISOLATE_ATTACK, 1.0))
        ci = w.dz_imm[bid, d, CHILD].astype(float)
        ai = w.dz_imm[bid, d, ADULT].astype(float)
        crisis = 1.0 + np.where(att * (1 - ai) >= P.DZ_CRISIS_SHARE,      # too many adults ill to care and feed
                                P.DZ_CRISIS_EXTRA * np.where(isolate[sel], P.DZ_ISOLATE_CRISIS, 1.0), 0.0)
        base = dz["cfr"] * (1.0 + dz["hunger"] * hunger[sel] * P.DZ_HUNGER) * crisis
        pc = np.minimum(1.0, att * (1 - ci) * base * dz["child"])
        pa = np.minimum(1.0, att * (1 - ai) * base)
        po = np.minimum(1.0, pa * P.DZ_OLD_MULT)
        deaths = _kill(w, rng, [bands[i] for i in sel.tolist()], bid, pc, pa, po, eid)
        w.events[eid]["data"]["deaths"] = int(deaths)
        w.dz_imm[bid, d, CHILD] = (ci + att * (1 - ci)).astype(np.float32)
        w.dz_imm[bid, d, ADULT] = (ai + att * (1 - ai)).astype(np.float32)


def _kill(w, rng, blist, bid, pc, pa, po, event_id) -> int:
    """Deaths by age in the given bands: individuals at once, groups row by row."""
    from . import demography
    from .groups import AGES, AGE_GROUP
    code = C["disease outbreak"]
    n = 0
    p = w.people
    idx = w.alive_idx()
    if len(idx):
        m = int(max(bid.max(), p.band[idx].max())) + 1
        tc, ta, to = np.zeros(m), np.zeros(m), np.zeros(m)
        tc[bid], ta[bid], to[bid] = pc, pa, po
        pb = p.band[idx]
        hot = (tc[pb] > 0) | (ta[pb] > 0)
        if hot.any():
            cand = idx[hot]
            age = w.ages(cand)
            b_ = p.band[cand]
            pr = np.where(age < 15, tc[b_], np.where(age < 50, ta[b_], to[b_]))
            hit = cand[rng.random(len(cand)) < pr]
            if len(hit):
                demography.kill(w, hit, np.full(len(hit), code, dtype=np.int8))
                p.death_hazard[hit] = event_id
                n += len(hit)
    G = w.groups
    age = np.arange(AGES)
    for j, b in enumerate(blist):
        if b.mode != "group" or not b.alive:
            continue
        pr = np.where(age < 15, pc[j], np.where(age < 50, pa[j], po[j]))
        for X in (G.F, G.M):
            cnt = np.rint(X[b.group]).astype(np.int64)
            dd = rng.binomial(cnt, pr)
            if dd.any():
                X[b.group] -= dd
                k = int(dd.sum())
                n += k
                w.counts["deaths"] += k
                w.accum["deaths_by_cause"][code] += k
                w.accum["deaths"] += np.bincount(AGE_GROUP, weights=dd, minlength=18)
    return n


# ------------------------------------------------------------------ saves

def to_json(w):
    return {"diseases": getattr(w, "diseases", [])}


def from_json(w, d):
    init(w)
    w.diseases = d.get("diseases", [])


ARRAYS = ("dz_imm", "dz_active")
