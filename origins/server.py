"""Local observatory server (standard library only, plus NumPy for the simulation).

Run with:  python run.py   then open http://127.0.0.1:8770

The clock runs at 300 simulated years per real day (a season every 72 s) until the first farming village,
then at the historical rate of 20 years per real day (a season every 18 minutes).
Following a band lets the observer slow the whole world down; stopping
following returns to the normal rate. Fast-forward is separate.
"""
from __future__ import annotations

import json
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from . import engine, explain, persist
from . import params as P
from .names import etymology
from .lang.proto import MEANINGS, NAME_FIRST, NAME_SECOND
from .sim import customs, farming, groups, language, surplus
from .state import CAUSES, World
from .worldgen import BIOMES

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "observatory"
SAVES = ROOT / "saves"
AUTOSAVE = SAVES / "autosave.zip"
NORMAL_RATE = 300 * P.TICKS_PER_YEAR / 86400.0       # seasons per real second (prehistoric clock)
HISTORICAL_YEARS_PER_DAY = 20                         # after the first farming village (M2 specification, decision 2)
HISTORICAL_RATE = HISTORICAL_YEARS_PER_DAY * P.TICKS_PER_YEAR / 86400.0


def years_per_day(w) -> int:
    return HISTORICAL_YEARS_PER_DAY if w is not None and getattr(w, "first_village", None) is not None else 300
AUTOSAVE_SECONDS = 300

lock = threading.RLock()
state = {"world": None, "mode": "paused", "follow_rate": 2.0, "fast_target": None,
         "carry": 0.0, "last": time.time(), "error": "", "geometry": {}, "last_save": time.time()}


# ----------------------------------------------------------------- world control
def new_world(world_seed: int, run_seed: int):
    with lock:
        state["world"] = World.new(world_seed, run_seed)
        state["mode"] = "paused"
        state["fast_target"] = None


def startup():
    SAVES.mkdir(exist_ok=True)
    if AUTOSAVE.exists():
        try:
            state["world"] = persist.load(AUTOSAVE)
            print(f"Restored autosave: {state['world'].years_bp:,} years before present")
            return
        except Exception as exc:  # keep the unreadable file; never overwrite it
            keep = SAVES / f"unreadable-autosave-{int(time.time())}.zip"
            AUTOSAVE.replace(keep)
            print(f"WARNING: autosave could not be read ({exc}); kept as {keep.name}")
    new_world(1, 1)


def autosave():
    w = state["world"]
    if w is not None:
        persist.save(w, AUTOSAVE)
        state["last_save"] = time.time()


def clock_loop(stop: threading.Event):
    while not stop.wait(0.2):
        try:
            with lock:
                w = state["world"]
                now = time.time()
                dt, state["last"] = now - state["last"], now
                mode = state["mode"]
                if w is None or engine.extinct(w):
                    continue
                if mode == "fast":
                    target = state["fast_target"]
                    k = min(8, max(0, target - w.t))
                    if k:
                        engine.step(w, k)
                    if w.t >= target:
                        state["mode"] = "paused"
                        state["fast_target"] = None
                    continue
                normal = HISTORICAL_RATE if years_per_day(w) == HISTORICAL_YEARS_PER_DAY else NORMAL_RATE
                rate = normal if mode == "running" else (
                    state["follow_rate"] / 60.0 if mode == "following" else 0.0)
                state["carry"] += dt * rate
                k = int(state["carry"])
                if k:
                    state["carry"] -= k
                    engine.step(w, min(k, 8))
                if time.time() - state["last_save"] > AUTOSAVE_SECONDS and mode != "paused":
                    autosave()
        except Exception as exc:
            with lock:
                state["mode"] = "paused"
                state["error"] = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()


# ----------------------------------------------------------------- views
def geometry(w) -> dict:
    key = w.world_seed
    if key not in state["geometry"]:
        pl = w.planet
        polys = pl.grid.polygons()
        river_segs = []
        for c in np.nonzero(pl.river)[0]:
            d = pl.downstream[c]
            if d >= 0:
                river_segs.append([round(float(pl.grid.lon[c]), 2), round(float(pl.grid.lat[c]), 2),
                                   round(float(pl.grid.lon[d]), 2), round(float(pl.grid.lat[d]), 2)])
        state["geometry"][key] = {
            "n": pl.n, "biomes": BIOMES, "biome": pl.biome.tolist(),
            "poly": [np.round(pq, 2).ravel().tolist() for pq in polys],
            "lon": np.round(pl.grid.lon, 2).tolist(), "lat": np.round(pl.grid.lat, 2).tolist(),
            "elev": np.round(pl.elevation).astype(int).tolist(), "rivers": river_segs,
            "start": pl.start_cell, "cell_km2": round(pl.grid.cell_area_km2),
        }
    return state["geometry"][key]


def season_name(w, cell=None) -> str:
    q = w.quarter
    if cell is not None and w.planet.grid.lat[cell] < 0:
        q = (q + 2) % 4
    return ["spring", "summer", "autumn", "winter"][q]


def summary(w) -> dict:
    y = w.yearly
    step = max(1, len(y) // 600)
    series = [[r["years_bp"], r["population"], r["individuals"], round(r["food_ratio"], 3)] for r in y[::step]]
    if y and (not series or series[-1][0] != y[-1]["years_bp"]):
        r = y[-1]
        series.append([r["years_bp"], r["population"], r["individuals"], round(r["food_ratio"], 3)])
    return {
        "t": w.t, "years_bp": w.years_bp, "season": season_name(w), "world_seed": w.world_seed, "run_seed": w.run_seed,
        "population": w.population(), "individuals": int(len(w.alive_idx())),
        "bands": len(w.living_bands()), "groups": sum(b.mode == "group" for b in w.living_bands()),
        "known_cells": int(w.known.sum()), "mode": state["mode"], "follow": w.follow,
        "follow_rate": state["follow_rate"], "fast_target": state["fast_target"], "error": state["error"],
        "extinct": engine.extinct(w), "series": series, "invariant_failures": len(w.invariant_failures),
        "intervened": w.intervened, "years_per_day_normal": years_per_day(w), "threshold": P.INDIVIDUAL_THRESHOLD,
        "first_village": first_village(w), "farming": farming_counts(w), "polities": polity_counts(w),
        "food_ratio": w.season_stats.get("ratio", 1.0), "load_warning": getattr(w, "load_warning", ""),
    }


def known_since(w, t: int) -> list:
    return np.nonzero(w.known & (w.discovered_at >= t))[0].tolist() if t > 0 else np.nonzero(w.known)[0].tolist()


def bands_view(w) -> list:
    sizes = w.band_sizes()
    g = w.planet.grid
    bands = w.living_bands()
    if not bands:
        return []
    ids = np.array([b.id for b in bands])
    KP, VP, KA, VA = farming.best_all(w, ids, np.array([b.cell for b in bands]))
    out = []
    for n, b in enumerate(bands):
        size = float(sizes[b.id])
        fs = float(w.farm_share[b.id])
        main = None
        if fs > 0.02:
            main = farming.NAMES[farming.SPECIES[int(KP[n]) if VP[n] >= VA[n] else int(KA[n])]]
        surplus_pp = max(0.0, b.store - P.SURPLUS_RESERVE * size * surplus.ANNUAL) / max(size, 1.0)
        out.append({"id": b.id, "cell": b.cell, "parent": b.parent,
                    "lon": round(float(g.lon[b.cell]), 3), "lat": round(float(g.lat[b.cell]), 3),
                    "size": int(round(size)), "mode": b.mode, "name": w.band_name(b), "ratio": round(b.last_ratio, 3),
                    "lang": b.language, "hue": lang_hue(w, b.language), "custom": custom_key(w, b.id),
                    "farm": round(fs, 2), "village": bool(b.village), "crop": main,
                    "fsince": _bp(b.farming_since) if b.farming_since >= 0 else
                    (_bp(b.village_since) if b.village and b.village_since >= 0 else None),   # saves before farming_since
                    "spec": round(float(w.spec[b.id]) / max(size, 1.0), 3), "surplus": round(surplus_pp / 0.95),
                    "pol": _pol_of(w, b.id), "seat": _is_seat(w, b.id),
                    "tier": w.polities[_pol_of(w, b.id)].tier if _pol_of(w, b.id) >= 0 else 0})
    return out


def _pol_of(w, bid) -> int:
    pid = int(w.polity_of[bid]) if hasattr(w, "polity_of") and bid < len(w.polity_of) else -1
    return pid if pid >= 0 and pid in w.polities and w.polities[pid].alive else -1


def _is_seat(w, bid) -> bool:
    pid = _pol_of(w, bid)
    return pid >= 0 and w.polities[pid].seat == bid


def polities_view(w) -> list:
    from .sim import polity as PL
    sizes = w.band_sizes()
    g = w.planet.grid
    out = []
    by = {}
    for b in w.living_bands():
        pid = _pol_of(w, b.id)
        if pid >= 0:
            by.setdefault(pid, []).append(b)
    for pid, mem in by.items():
        p = w.polities[pid]
        seat = w.bands[p.seat]
        out.append({"id": pid, "name": p.name, "tier": PL.TIERS[p.tier], "tier_n": p.tier, "settlements": len(mem),
                    "people": int(round(sum(sizes[b.id] for b in mem))),
                    "lon": round(float(g.lon[seat.cell]), 3), "lat": round(float(g.lat[seat.cell]), 3),
                    "leader": w.people.name(p.leader) if p.leader >= 0 else "",
                    "institutions": [PL.INSTITUTIONS[k] for k in range(len(PL.INSTITUTIONS)) if p.inst[k]],
                    "load": round(p.load, 1), "capacity": round(p.cap, 1)})
    out.sort(key=lambda r: -r["people"])
    return out


def polity_detail(w, pid: int) -> dict:
    from .sim import polity as PL
    p = w.polities[pid]
    sizes = w.band_sizes()
    seat = w.bands[p.seat]
    mem = PL.members_of(w, pid) if p.alive else []
    depth = PL._depths(w, [b.id for b in mem], p.seat) if mem else {}
    ev = [e for e in w.events if e["data"].get("polity") == pid or e["data"].get("attacker_polity") == pid
          or e["data"].get("defender_polity") == pid]
    leaders = [{"name": w.people.name(e["person"]), "id": e["person"], "bp": _bp(e["t"]),
                "contested": bool(e["data"].get("contested"))} for e in ev if e["kind"] == "succession" and e["person"] >= 0]
    return {"id": pid, "name": p.name, "alive": p.alive, "tier": PL.TIERS[p.tier], "founded_bp": _bp(p.founded),
            "ended_bp": _bp(p.ended) if p.ended >= 0 else None, "founding_event": p.founding_event,
            "seat": {"id": seat.id, "name": w.band_name(seat)},
            "leader": person_brief(w, p.leader) if p.leader >= 0 else None, "leaders": leaders[-12:],
            "institutions": [{"name": PL.INSTITUTIONS[k], "held": bool(p.inst[k])} for k in range(len(PL.INSTITUTIONS))],
            "load": round(p.load, 2), "capacity": round(p.cap, 2),
            "levels": PL.levels_of_rule(w, [b.id for b in mem], p.seat) if mem else 0,
            "members": [{"id": b.id, "name": w.band_name(b), "people": int(round(sizes[b.id])),
                         "level": depth.get(b.id, 0), "language": language.display(w, b.language),
                         "conquered": bool(w.conquered_at[b.id] >= 0)} for b in sorted(mem, key=lambda b: depth.get(b.id, 0))],
            "events": [{"id": e["id"], "title": explain.describe(w, {"event": e["id"]})["title"], "bp": _bp(e["t"])}
                       for e in ev[-60:]][::-1]}


def wars_view(w, years: int = 30) -> list:
    g = w.planet.grid
    since = w.t - years * P.TICKS_PER_YEAR
    out = []
    for e in reversed(w.events[-20000:]):
        if e["t"] < since:
            break
        if e["kind"] != "war":
            continue
        a = w.bands.get(e["band"])
        t = w.bands.get(e["data"].get("target"))
        if a is None or t is None:
            continue
        out.append({"id": e["id"], "from": [round(float(g.lon[a.cell]), 3), round(float(g.lat[a.cell]), 3)],
                    "to": [round(float(g.lon[e["cell"]]), 3), round(float(g.lat[e["cell"]]), 3)],
                    "outcome": e["data"].get("outcome", ""), "deaths": e["data"].get("attacker_deaths", 0)
                    + e["data"].get("defender_deaths", 0), "age": (w.t - e["t"]) // P.TICKS_PER_YEAR})
    return out


def _bp(t: int) -> int:
    return P.START_YEARS_BP - int(t) // P.TICKS_PER_YEAR


def first_village(w):
    e = getattr(w, "first_village", None)
    if e is None:
        return None
    ev = w.events[e]
    return {"event": e, "bp": _bp(ev["t"]), "title": explain.describe(w, {"event": e})["title"], "band": ev["band"]}


def farming_counts(w) -> dict:
    bands = w.living_bands()
    sizes = w.band_sizes()
    fs = w.farm_share
    v = sum(1 for b in bands if fs[b.id] >= 0.5)
    people = {"villages": 0.0, "mixed": 0.0, "foragers": 0.0}
    for b in bands:
        k = "villages" if fs[b.id] >= 0.5 else "mixed" if fs[b.id] > 0.02 else "foragers"
        people[k] += float(sizes[b.id])
    return {"villages": v, "people": {k: int(round(x)) for k, x in people.items()},
            "specialists": int(sum(w.spec[b.id] for b in bands))}


def polity_counts(w) -> dict:
    ps = [p for p in getattr(w, "polities", {}).values() if p.alive]
    return {"chiefdoms": sum(1 for p in ps if p.tier in (1, 2)), "states": sum(1 for p in ps if p.tier == 3),
            "all": len(ps)}


def farming_story(w) -> list:
    """Each crop's and animal's story: firsts, and how many peoples now keep it domesticated."""
    bands = w.living_bands()
    ids = np.array([b.id for b in bands]) if bands else np.zeros(0, dtype=int)
    out = []
    for k, sp in enumerate(farming.SPECIES):
        f = w.farm_firsts.get(sp, {})
        firsts = []
        for stage in ("tending", "cultivation", "domestication"):
            if stage in f:
                e = w.events[f[stage]]
                firsts.append({"stage": stage, "event": f[stage], "bp": _bp(e["t"]),
                               "by": w.band_name(w.bands[e["band"]]) if e["band"] in w.bands else ""})
        sk = w.skill[ids, k] if len(ids) else np.zeros(0)
        out.append({"species": farming.NAMES[sp], "kind": "crop" if k in farming.PLANTS else "animal",
                    "firsts": firsts, "peoples_domesticated": int((sk >= 3).sum()),
                    "peoples_tending": int(((sk > 0) & (sk < 3)).sum())})
    return out


def lang_hue(w, lid: int) -> int:
    """Related languages get related colours: each daughter's hue is near its parent's."""
    cache = state.setdefault("hues", {})
    key = (w.world_seed, w.run_seed, lid)
    if key in cache:
        return cache[key]
    lang = w.languages[lid]
    if lang.parent < 0:
        h = 35.0
    else:
        par = w.languages[lang.parent]
        sibs = sorted(k.id for k in w.languages.values() if k.parent == par.id)
        depth = len(language.lineage(w, lid)) - 1
        spread = 300.0 / (1.8 ** (depth - 1))
        k = sibs.index(lid)
        h = lang_hue(w, par.id) + (k - (len(sibs) - 1) / 2) * spread / max(len(sibs), 1)
    cache[key] = int(h % 360)
    return cache[key]


def custom_key(w, bid: int) -> int:
    """A number standing for a band's set of customs (for colouring the customs layer)."""
    v = w.customs[bid].astype(np.int64)
    return int(sum(int(x) * 7 ** k for k, x in enumerate(v)) % 360)


def language_detail(w, lid: int) -> dict:
    lang = w.languages[lid]
    chain = language.lineage(w, lid)
    speakers = [b for b in w.living_bands() if b.language == lid]
    sizes = w.band_sizes()
    rel = []
    for k in w.languages.values():
        if k.alive and k.id != lid:
            sr = language.shared_roots(lang, k)
            if sr > 0.3:
                rel.append({"id": k.id, "name": language.display(w, k.id), "shared": round(sr, 2),
                            "split_bp": P.START_YEARS_BP - language.common_ancestor_time(w, lid, k.id) // P.TICKS_PER_YEAR})
    rel.sort(key=lambda r: -r["shared"])
    changes = []
    for anc in chain:
        for ev in anc.history:
            if ev[1] == "rule":
                changes.append({"bp": P.START_YEARS_BP - ev[0] // P.TICKS_PER_YEAR, "rule": language.CH.describe(ev[2]),
                                "in": language.display(w, anc.id)})
    words = [{"meaning": m, "proto": language.show(language.parse(language.PROTO[m])),
              "now": language.show(tuple(lang.lexicon[m][0])), "origin": lang.lexicon[m][2]} for m in MEANINGS]
    return {"id": lid, "name": language.display(w, lang.id), "self_name": language.name_of(lang), "alive": lang.alive,
            "born_bp": P.START_YEARS_BP - lang.born // P.TICKS_PER_YEAR,
            "ended_bp": P.START_YEARS_BP - lang.ended // P.TICKS_PER_YEAR if lang.ended >= 0 else None,
            "lineage": [{"id": a.id, "name": language.display(w, a.id)} for a in chain],
            "daughters": [{"id": k.id, "name": language.display(w, k.id)} for k in w.languages.values() if k.parent == lid],
            "speakers": int(sum(sizes[b.id] for b in speakers)), "bands": len(speakers),
            "sound_changes": changes, "relatives": rel[:12], "words": words}


def language_tree(w) -> list:
    sizes = w.band_sizes()
    spk = {}
    for b in w.living_bands():
        spk[b.language] = spk.get(b.language, 0) + float(sizes[b.id])
    return [{"id": l.id, "parent": l.parent, "name": language.display(w, l.id), "born_bp": P.START_YEARS_BP - l.born // 4,
             "ended_bp": P.START_YEARS_BP - l.ended // 4 if l.ended >= 0 else None, "speakers": int(spk.get(l.id, 0)),
             "hue": lang_hue(w, l.id)} for l in w.languages.values()]


def name_story(w, i: int) -> dict:
    """How a person's name came from the proto-language's words into their own language."""
    p = w.people
    lid = int(p.lang[i])
    if lid < 0:
        return {"text": etymology(int(p.name_a[i]), int(p.name_b[i])), "parts": []}
    a, b = int(p.name_a[i]), int(p.name_b[i])
    until = int(p.death[i]) if p.death[i] >= 0 else None
    parts = []
    for meaning in [NAME_FIRST[a]] + ([NAME_SECOND[b]] if b >= 0 else []):
        hist = language.word_history(w, lid, meaning, until)
        parts.append({"meaning": meaning, "steps": [{"bp": P.START_YEARS_BP - t // 4, "form": f, "why": why}
                                                    for t, f, why in hist]})
    lang = w.languages[lid]
    text = (f"in {language.display(w, lang.id)}: " + " + ".join(f"'{q['meaning']}' ({q['steps'][-1]['form']})" for q in parts))
    return {"text": text, "parts": parts, "language": lid}


def hazard_view(w, years: int = 60) -> list:
    t0 = w.t - years * P.TICKS_PER_YEAR
    g = w.planet.grid
    out = []
    for e in reversed(w.events):
        if e["t"] < t0:
            break
        if e["kind"] in ("flood", "wildfire", "eruption", "earthquake", "outbreak", "sea_crossing") and e["cell"] >= 0:
            out.append({"ref": f"event:{e['id']}", "kind": e["kind"], "lon": round(float(g.lon[e["cell"]]), 2),
                        "lat": round(float(g.lat[e["cell"]]), 2), "bp": P.START_YEARS_BP - e["t"] // 4,
                        "title": explain.describe(w, {"event": e["id"]})["title"]})
    return out[:300]


def person_brief(w, i) -> dict:
    p = w.people
    i = int(i)
    alive = bool(p.alive[i])
    end = w.t if alive else (p.death[i] if p.death[i] >= 0 else p.folded[i])
    return {"id": i, "name": p.name(i), "sex": "female" if p.sex[i] == 0 else "male",
            "age": round((end - p.birth[i]) / P.TICKS_PER_YEAR, 1), "alive": alive,
            "condition": round(float(p.condition[i]), 2), "band": int(p.band[i]),
            "died": int(p.death[i]) >= 0, "folded": int(p.folded[i]) >= 0,
            "cause": CAUSES[int(p.cause[i])] if p.death[i] >= 0 else "",
            "role": surplus.ROLES[int(p.role[i])] if alive else ""}


def band_detail(w, bid: int) -> dict:
    b = w.bands[bid]
    out = {"id": b.id, "name": w.band_name(b), "mode": b.mode, "alive": b.alive, "cell": b.cell,
           "founded_bp": P.START_YEARS_BP - b.founded // P.TICKS_PER_YEAR, "store_days": 0.0,
           "ratio": round(b.last_ratio, 3), "last_move": b.last_move, "season": season_name(w, b.cell),
           "biome": BIOMES[w.planet.biome[b.cell]], "capacity": float(w.planet.capacity[b.cell]),
           "trail": [[P.START_YEARS_BP - t // P.TICKS_PER_YEAR, c] for t, c in b.trail[-20:]],
           "parent": b.parent, "followed": w.follow == b.id,
           "language": {"id": b.language, "name": language.display(w, b.language)},
           "customs": [{"custom": k, "practice": customs.CUSTOMS[k][int(w.customs[b.id, j])]}
                       for j, k in enumerate(customs.NAMES)],
           "custom_changes": [{"bp": P.START_YEARS_BP - t // 4, "custom": c, "from": a, "to": z, "how": how}
                              for t, c, a, z, how in w.custom_log.get(b.id, [])][::-1]}
    if b.mode == "group" and b.group >= 0:
        G = w.groups
        out["pyramid"] = {"female": G.F[b.group].astype(int).tolist(), "male": G.M[b.group].astype(int).tolist()}
        out["size"] = int(G.total(b.group))
        out["condition"] = {"children": round(float(G.cond_child[b.group]), 2),
                            "adults": round(float(G.cond_rest[b.group]), 2)}
    else:
        mem = w.members(bid)
        order = mem[np.argsort(w.people.birth[mem])]
        out["members"] = [person_brief(w, i) for i in order]
        out["size"] = len(mem)
    out["farming"] = band_farming(w, b, out["size"])
    pid = _pol_of(w, b.id)
    out["polity"] = {"id": pid, "name": w.polities[pid].name, "seat": w.polities[pid].seat == b.id} if pid >= 0 else None
    out["events"] = [{"id": e["id"], "title": explain.describe(w, {"event": e["id"]})["title"],
                      "bp": P.START_YEARS_BP - e["t"] // P.TICKS_PER_YEAR}
                     for e in w.events if e["band"] == bid or e["data"].get("new_band") == bid
                     or e["data"].get("into") == bid][-30:]
    return out


def band_farming(w, b, size) -> dict:
    """Fields, herds, stores, specialists and households of a band (the village page)."""
    sk = w.skill[b.id]
    crops = [{"species": farming.NAMES[sp], "kind": "crop" if k in farming.PLANTS else "animal",
              "stage": farming.stage_name(float(sk[k])), "skill": round(float(sk[k]), 2)}
             for k, sp in enumerate(farming.SPECIES) if sk[k] > 0]
    crops.sort(key=lambda c: -c["skill"])
    need_day = max(size, 1) * 0.95
    out = {"share": round(float(w.farm_share[b.id]), 2), "village": bool(b.village),
           "village_since_bp": _bp(b.village_since) if b.village and b.village_since >= 0 else None,
           "farming_since_bp": _bp(b.farming_since) if b.farming_since >= 0 else None,
           "years_in_place": int(w.still_years[b.id]), "crops": crops,
           "store_days": round(b.store / need_day), "standing_crop_days": round(float(w.crop_store[b.id]) / need_day),
           "granary_days": P.GRANARY_DAYS if P.STORAGE else 0,
           "surplus_per_person_days": round(max(0.0, b.store - P.SURPLUS_RESERVE * size * surplus.ANNUAL) / need_day),
           "specialists": int(w.spec[b.id]), "households": [], "gini": None}
    if b.mode != "group":
        from .sim.bands import _households
        mem = w.members(b.id)
        p = w.people
        roles = {}
        for i in mem:
            if p.role[i]:
                roles.setdefault(surplus.ROLES[int(p.role[i])], []).append(person_brief(w, int(i)))
        out["roles"] = roles
        if len(mem) and w.farm_share[b.id] >= P.PROPERTY_SHARE and P.STORAGE:
            units = _households(w, mem)
            heads = [u[0] for u in units]
            wealth = np.array([float(p.wealth[h]) for h in heads])
            tot = wealth.sum()
            hh = [{"head": person_brief(w, int(h)), "people": len(u), "share": round(float(x / tot), 3) if tot > 0 else 0.0}
                  for h, u, x in zip(heads, units, wealth)]
            hh.sort(key=lambda r: -r["share"])
            out["households"] = hh
            out["gini"] = round(surplus.gini(wealth), 3) if len(wealth) >= 2 else None
    return out


def person_detail(w, i: int) -> dict:
    p = w.people
    out = person_brief(w, i)
    story = name_story(w, i)
    out["etymology"] = story["text"]
    out["name_story"] = story["parts"]
    out["born_bp"] = P.START_YEARS_BP - int(p.birth[i]) // P.TICKS_PER_YEAR
    rel = {}
    for key, j in (("mother", p.mother[i]), ("father", p.father[i]), ("partner", p.partner[i])):
        rel[key] = person_brief(w, j) if j >= 0 else None
    n = p.n
    kids = np.nonzero((p.mother[:n] == i) | (p.father[:n] == i))[0]
    rel["children"] = [person_brief(w, k) for k in kids]
    sib = np.zeros(0, dtype=np.int64)
    if p.mother[i] >= 0:
        sib = np.nonzero(p.mother[:n] == p.mother[i])[0]
        sib = sib[sib != i]
    rel["siblings"] = [person_brief(w, k) for k in sib]
    out["family"] = rel
    out["life"] = []
    if p.mother[i] >= 0 or p.unfolded[i] < 0:
        out["life"].append({"ref": f"birth:{i}", "title": explain.describe(w, {"birth": i})["title"]})
    if p.death[i] >= 0:
        out["life"].append({"ref": f"death:{i}", "title": explain.describe(w, {"death": i})["title"]})
    if p.folded[i] >= 0:
        out["life"].append({"ref": "", "title": f"Followed as part of a group from "
                                                f"{P.START_YEARS_BP - int(p.folded[i]) // P.TICKS_PER_YEAR:,} BP"})
    return out


def recent_events(w, limit=60) -> list:
    p = w.people
    out = []
    for e in w.events[-limit:]:
        out.append({"ref": f"event:{e['id']}", "t": e["t"], "kind": e["kind"], "cell": e["cell"],
                    "title": explain.describe(w, {"event": e["id"]})["title"]})
    n = p.n
    dead = np.nonzero(p.death[:n] >= max(0, w.t - 8))[0]
    for i in dead[np.argsort(-p.death[dead])][:limit]:
        out.append({"ref": f"death:{i}", "t": int(p.death[i]), "kind": "death", "cell": int(p.death_cell[i]),
                    "title": explain.describe(w, {"death": int(i)})["title"]})
    born = np.nonzero(p.birth[:n] >= max(0, w.t - 4))[0]
    born = born[p.mother[born] >= 0]
    for i in born[np.argsort(-p.birth[born])][:20]:
        out.append({"ref": f"birth:{i}", "t": int(p.birth[i]), "kind": "birth", "cell": int(p.birth_cell[i]),
                    "title": explain.describe(w, {"birth": int(i)})["title"]})
    out.sort(key=lambda r: -r["t"])
    for r in out:
        r["bp"] = P.START_YEARS_BP - r["t"] // P.TICKS_PER_YEAR
    return out[:limit]


def parse_ref(s: str) -> dict:
    kind, _, val = s.partition(":")
    return {kind: int(val)}


# ----------------------------------------------------------------- control
def control(body: dict) -> dict:
    a = body.get("action")
    with lock:
        w = state["world"]
        state["error"] = ""
        if a == "play":
            state["mode"] = "following" if w.follow >= 0 else "running"
        elif a == "pause":
            state["mode"] = "paused"
        elif a == "fast":
            years = int(body.get("years", 10))
            if not 1 <= years <= 5000:
                raise ValueError("fast-forward between 1 and 5,000 years")
            state["fast_target"] = w.t + years * P.TICKS_PER_YEAR
            state["mode"] = "fast"
        elif a == "follow":
            bid = int(body["band"])
            b = w.bands[bid]
            if not b.alive:
                raise ValueError("that band no longer exists")
            if b.mode == "group":
                ids = groups.unfold(w, b)
                w.event("unfold", cell=b.cell, band=b.id,
                        causes=[{"note": "the observer chose to follow this band"}], people=int(len(ids)))
            w.follow = bid
            if "rate" in body:
                state["follow_rate"] = float(body["rate"])
            if state["mode"] in ("running", "following"):
                state["mode"] = "following"
        elif a == "rate":
            r = float(body["rate"])
            if not 0.05 <= r <= 120:
                raise ValueError("follow speed between 0.05 and 120 seasons per minute")
            state["follow_rate"] = r
        elif a == "unfollow":
            w.follow = -1
            if state["mode"] == "following":
                state["mode"] = "running"
        elif a == "save":
            name = "".join(ch for ch in str(body.get("name", "manual")) if ch.isalnum() or ch in "-_") or "manual"
            persist.save(w, SAVES / f"{name}.zip")
        elif a == "load":
            name = "".join(ch for ch in str(body.get("name", "")) if ch.isalnum() or ch in "-_.")
            path = SAVES / (name if name.endswith(".zip") else name + ".zip")
            state["world"] = persist.load(path)          # nothing changes if loading fails
            state["mode"] = "paused"
        elif a == "new":
            new_world(int(body.get("world_seed", 1)), int(body.get("run_seed", 1)))
        else:
            raise ValueError(f"unknown action {a!r}")
    return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, payload, ctype="application/json"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            if u.path.startswith("/static/"):
                f = (STATIC / u.path[len("/static/"):]).resolve()
                if STATIC in f.parents and f.exists():
                    ctype = "text/javascript" if f.suffix == ".js" else "text/css" if f.suffix == ".css" else "application/octet-stream"
                    return self._send(200, f.read_bytes(), ctype)
                return self._send(404, {"error": "not found"})
            with lock:
                w = state["world"]
                if u.path == "/api/geometry":
                    return self._send(200, geometry(w))
                if u.path == "/api/state":
                    return self._send(200, {**summary(w), "known": known_since(w, int(q.get("since", 0)))})
                if u.path == "/api/bands":
                    return self._send(200, bands_view(w))
                if u.path == "/api/band":
                    return self._send(200, band_detail(w, int(q["id"])))
                if u.path == "/api/person":
                    return self._send(200, person_detail(w, int(q["id"])))
                if u.path == "/api/events":
                    return self._send(200, recent_events(w))
                if u.path == "/api/explain":
                    return self._send(200, explain.chain(w, parse_ref(q["ref"]), depth=int(q.get("depth", 5))))
                if u.path == "/api/cell":
                    c = int(q["id"])
                    pl = w.planet
                    return self._send(200, {"cell": c, "biome": BIOMES[pl.biome[c]], "known": bool(w.known[c]),
                                            "elevation_m": int(pl.elevation[c]), "rain_mm": int(pl.rain[c]),
                                            "temp_c": round(float(pl.temp_mean[c]), 1), "river": bool(pl.river[c]),
                                            "coast": bool(pl.coast[c]), "capacity": float(pl.capacity[c]),
                                            "wild_food_days": round(float(w.stock[c]) / max(1.0, pl.capacity[c] * 0.8), 1),
                                            "discovered_bp": (P.START_YEARS_BP - int(w.discovered_at[c]) // P.TICKS_PER_YEAR)
                                            if w.discovered_at[c] >= 0 else None})
                if u.path == "/api/language":
                    return self._send(200, language_detail(w, int(q["id"])))
                if u.path == "/api/languages":
                    return self._send(200, language_tree(w))
                if u.path == "/api/hazards":
                    return self._send(200, hazard_view(w, int(q.get("years", 60))))
                if u.path == "/api/polities":
                    return self._send(200, polities_view(w))
                if u.path == "/api/polity":
                    return self._send(200, polity_detail(w, int(q["id"])))
                if u.path == "/api/wars":
                    return self._send(200, wars_view(w))
                if u.path == "/api/farming":
                    return self._send(200, {"species": farming_story(w), "first_village": first_village(w)})
                if u.path == "/api/saves":
                    return self._send(200, sorted(f.name for f in SAVES.glob("*.zip")))
            return self._send(404, {"error": "not found"})
        except Exception as exc:
            traceback.print_exc()
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 1_000_000:
                raise ValueError("request too large")
            body = json.loads(self.rfile.read(n) or b"{}")
            if urlparse(self.path).path != "/api/control":
                return self._send(404, {"error": "not found"})
            return self._send(200, control(body))
        except Exception as exc:
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})


def main(port: int = 8770, open_browser: bool = True):
    import webbrowser
    startup()
    stop = threading.Event()
    th = threading.Thread(target=clock_loop, args=(stop,), daemon=True)
    th.start()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"Origins observatory at {url}  (Ctrl+C to stop; the world is saved on exit)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        stop.set()
        th.join(timeout=3)
        server.server_close()
        with lock:
            try:
                autosave()
                print("World saved.")
            except Exception as exc:
                print("Final save failed:", exc)
