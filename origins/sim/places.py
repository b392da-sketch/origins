"""Place names (M4a, writing and place names; Ben, 20 November 2026).

Peoples name the features they use: rivers, lakes, hills and mountains, stretches of coast, and their settlements.
Bigger features are near more peoples and so are named by more of them; how soon a people names a feature grows with
how many of its speakers live by it. Names are layered: when newcomers meet a feature that people already living
there have a name for, they keep that name (borrowed, then reshaped by their own sound changes) or give their own.
Keeping is likelier for larger and more remote features and less likely the more the newcomers outnumber the people
they hear it from, and after conquest (major places keep names, minor ones do not: Hall 2012; native names survive
in remote uplands and least in units the state names: Wang et al. 2011; river names passed between languages: Kitson
2011; names grow with population density: Hunn 1994; kinds of naming: Tent & Blair 2011; build notes, "writing and
place names"). Every layer keeps its year, language, how it came (new, kept, replaced) and its cause.

A layer's form is the form at the year it was given; its form now is that form carried through every sound change
of its language's lineage since (as language.word_history does for words). Generic words (river, lake, hill,
settlement, sea) are PIE-inspired forms kept apart from the lexicon (lang.proto.PLACE_PROTO), so the core vocabulary
and its random draws are unchanged; they too change through each lineage's rules.

Features are derived from the planet (no random draws): rivers are split into a trunk and its tributaries at each
join (a stream continues up its larger branch); lakes are joined lake cells, used from the land around them; hills
and mountains are local peaks of elevation; coasts are joined coastal cells within one climate region. Settlements
are made where a settled people (technology._settled) or a polity's seat lives, and outlast it as named places.

reads: bands (cell, language, size), languages, planet, farm share and still years (settled), polity_of,
conquered_at; writes: w.places (saved, in the digest), events "place_named"; stream "places".
All numbers are tunable starting values in params.py.
"""
from __future__ import annotations

import numpy as np

from .. import params as P
from ..lang import changes as CH
from ..lang.proto import PLACE_PROTO, parse, roman

KINDS = ("river", "lake", "hill", "mountain", "coast", "settlement")
GENERIC = {"river": "river", "lake": "lake", "hill": "hill", "mountain": "hill", "coast": "sea",
           "settlement": "settlement"}
# descriptors a people may give a feature of each kind, from its own words (meanings of the core vocabulary)
DESCRIBE = {
    "river": ["great", "bright", "cold", "red", "old", "water", "wolf", "bear", "horse", "bird", "stone", "wood"],
    "lake": ["bright", "cold", "great", "salt", "bird", "stone", "moon", "sky"],
    "hill": ["red", "stone", "wood", "bright", "wolf", "bear", "old", "sun"],
    "mountain": ["great", "snow", "stone", "bright", "god", "sky", "cold", "old"],
    "coast": ["great", "bright", "cold", "salt", "wind", "bird", "dawn", "stone"],
    "settlement": ["new", "old", "great", "stone", "wood", "house", "salt", "cow", "sheep", "water"],
}


def init(w):
    w.places = []                       # [{kind, cell, key, size, layers: [[t, lang, tokens, how, src_lang, note]]}]
    w._place_key = {}


def _index(w):
    if getattr(w, "_place_key", None) is None or len(w._place_key) != len(w.places):
        w._place_key = {(p["kind"], int(p["key"])): i for i, p in enumerate(w.places)}
    return w._place_key


# --------------------------------------------------------------------------------------------- features (planet)

def features(planet):
    """Static features of a planet, cached on it: (kind, key, anchor, size 0..1, near cells) per feature and, for each
    cell, the features used from it. Deterministic, no random draws."""
    f = getattr(planet, "_place_features", None)
    if f is not None:
        return f
    nb = planet.grid.neighbours
    n = planet.n
    out = []                                            # (kind, key, anchor, size, cells)
    # rivers: a stream continues up its larger branch; each other branch starts a stream of its own
    riv = np.nonzero(planet.river)[0]
    if len(riv):
        order = riv[np.argsort(-planet.flow[riv], kind="stable")]
        main = {}
        for c in order.tolist():                        # the larger upstream river branch of each river cell
            d = int(planet.downstream[c])
            if d >= 0 and planet.river[d]:
                if d not in main or planet.flow[c] > planet.flow[main[d]]:
                    main[d] = c
        stream = {}
        cells_of: dict = {}
        def head(c):                                    # walk down the larger branches to where the stream starts
            path = []
            while c not in stream:
                d = int(planet.downstream[c])
                if d >= 0 and planet.river[d] and main.get(d) == c and d not in path:
                    path.append(c)
                    c = d
                else:
                    stream[c] = c
            for x in path:
                stream[x] = stream[c]
            return stream[c]
        for c in order.tolist():
            cells_of.setdefault(head(c), []).append(c)
        flows = np.array([planet.flow[s] for s in cells_of], dtype=float)
        lo, hi = np.log(flows.min()), np.log(flows.max())
        for s, cs in cells_of.items():
            size = float((np.log(planet.flow[s]) - lo) / max(hi - lo, 1e-9))
            out.append(("river", int(s), int(s), size, sorted(cs)))
    # lakes: joined lake cells, used from the land around them
    lake = planet.lake
    seen = np.zeros(n, dtype=bool)
    comps = []
    for c in np.nonzero(lake)[0].tolist():
        if seen[c]:
            continue
        comp, stack = [], [c]
        seen[c] = True
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in nb[x]:
                if y >= 0 and lake[y] and not seen[y]:
                    seen[y] = True
                    stack.append(int(y))
        comps.append(sorted(comp))
    if comps:
        big = np.log1p(max(len(c) for c in comps))
        for comp in comps:
            shore = sorted({int(y) for x in comp for y in nb[x] if y >= 0 and planet.land[y]})
            if shore:
                out.append(("lake", comp[0], comp[0], float(np.log1p(len(comp)) / max(big, 1e-9)), shore))
    # hills and mountains: local peaks, used from the peak and the cells around it
    el = planet.elevation
    top = float(el[planet.land].max()) if planet.land.any() else 1.0
    for c in np.nonzero(planet.land & (el >= P.PLACE_HILL_M))[0].tolist():
        ns = [int(y) for y in nb[c] if y >= 0]
        if all(el[c] > el[y] or (el[c] == el[y] and c < y) for y in ns):
            kind = "mountain" if el[c] >= P.PLACE_MOUNTAIN_M else "hill"
            size = float(np.clip((el[c] - P.PLACE_HILL_M) / max(top - P.PLACE_HILL_M, 1.0), 0, 1))
            out.append((kind, c, c, size, sorted([c] + [y for y in ns if planet.land[y]])))
    # coasts: joined coastal cells within one climate region
    coast = planet.coast
    seen = np.zeros(n, dtype=bool)
    comps = []
    for c in np.nonzero(coast)[0].tolist():
        if seen[c]:
            continue
        comp, stack = [], [c]
        seen[c] = True
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in nb[x]:
                if y >= 0 and coast[y] and not seen[y] and planet.region[y] == planet.region[c]:
                    seen[y] = True
                    stack.append(int(y))
        comps.append(sorted(comp))
    if comps:
        big = np.log1p(max(len(c) for c in comps))
        for comp in comps:
            out.append(("coast", comp[0], comp[0], float(np.log1p(len(comp)) / max(big, 1e-9)), comp))
    near: dict = {}
    for i, (_k, _key, _a, _s, cs) in enumerate(out):
        for c in cs:
            near.setdefault(int(c), []).append(i)
    planet._place_features = (out, near)
    return planet._place_features


# --------------------------------------------------------------------------------------------- forms

def lineage_ids(w, lang_id: int) -> list:
    out = []
    while lang_id is not None and lang_id >= 0 and lang_id in w.languages:
        out.append(lang_id)
        lang_id = w.languages[lang_id].parent
    return out[::-1]


def evolve(w, lang_id: int, tokens, after: int, until: int | None = None) -> tuple:
    """A form given at tick `after` in language `lang_id` (or one of its ancestors), carried through every sound
    change of the lineage after that tick and up to `until` (now, if None), as language.word_history does."""
    form = tuple(tokens)
    chain = [w.languages[i] for i in lineage_ids(w, lang_id)]
    for k, lang in enumerate(chain):
        end = chain[k + 1].born if k + 1 < len(chain) else (until if until is not None else 10 ** 12)
        if until is not None:
            end = min(end, until + 1)
        for ev in lang.history:
            t = ev[0]
            if t >= end:
                break
            if t > after and ev[1] == "rule":
                form = CH.apply(ev[2], form)
    return form


def generic(w, lang_id: int, kind: str, t: int) -> tuple:
    """A language's generic word for a kind of feature at tick t: the proto form through its lineage's rules."""
    return evolve(w, lang_id, parse(PLACE_PROTO[GENERIC[kind]]), -1, t)


def show(tokens) -> str:
    s = roman(tuple(tokens)) or "?"
    return s[:1].upper() + s[1:]


def current(w, layer, lang_id: int | None = None) -> tuple:
    """A layer's form now, in its own language (or in `lang_id`, a descendant that inherited it)."""
    t, lid, toks = layer[0], layer[1], layer[2]
    use = lid if lang_id is None else lang_id
    lang = w.languages.get(use)
    until = lang.ended if (lang is not None and not lang.alive) else None
    return evolve(w, use, toks, t, until)


def name_in(w, place: dict, lang_id: int):
    """The layer a language uses for a place: the latest given in its own lineage, or None."""
    lin = set(lineage_ids(w, lang_id))
    best = None
    for layer in place["layers"]:
        if layer[1] in lin and (best is None or layer[0] >= best[0]):
            best = layer
    return best


def display(w, i: int, lang_id: int | None = None) -> str:
    """A place's name now: in `lang_id` if it has one, otherwise its latest layer."""
    p = w.places[i]
    if not p["layers"]:
        return "?"
    layer = name_in(w, p, lang_id) if lang_id is not None else None
    if layer is not None:
        return show(current(w, layer, lang_id))
    return show(current(w, p["layers"][-1]))


def history(w, i: int) -> list:
    """Every layer of a place: [year, language, form then, form now, how, cause]."""
    from .language import label
    out = []
    for layer in w.places[i]["layers"]:
        lang = w.languages.get(layer[1])
        out.append([layer[0] // P.TICKS_PER_YEAR, label(w, lang) if lang else "?", show(layer[2]),
                    show(current(w, layer)), layer[3], layer[5]])
    return out


# --------------------------------------------------------------------------------------------- naming

def _compound(first, second) -> list:
    first = list(first)
    if len(first) > 2 and first[-1] == "s":
        first = first[:-1]
    return first + list(second)


def _new_name(w, rng, lang, kind: str, t: int) -> tuple[list, str]:
    gen = list(generic(w, lang.id, kind, t))
    bare = P.PLACE_BARE.get(kind, 0.0)
    if kind == "settlement" and rng.random() < P.PLACE_EPONYM:
        from ..lang.proto import NAME_FIRST, NAME_SECOND
        a = NAME_FIRST[int(rng.integers(len(NAME_FIRST)))]
        b = NAME_SECOND[int(rng.integers(len(NAME_SECOND)))]
        person = _compound(lang.lexicon[a][0], lang.lexicon[b][0])
        return _compound(person, gen), f"named after a person, {show(person)} ('{a}-{b}')"
    if rng.random() < bare:
        return gen, f"called simply '{GENERIC[kind]}' in their speech"
    m = DESCRIBE[kind][int(rng.integers(len(DESCRIBE[kind])))]
    return _compound(lang.lexicon[m][0], gen), f"'{m} {GENERIC[kind]}' in their speech"


def keep_chance(size: float, remote: float, newcomers: float, conquest: bool) -> float:
    """Chance newcomers keep the name they hear rather than give their own (Ben, 20 November 2026): larger and more
    remote features keep names; the more the newcomers outnumber those they hear it from, and after conquest, the
    less likely. Starting values in params.py."""
    p = (P.PLACE_KEEP_BASE + P.PLACE_KEEP_SIZE * size + P.PLACE_KEEP_REMOTE * remote) \
        * (1.0 - P.PLACE_KEEP_NEWCOMERS * newcomers)
    if conquest:
        p *= P.PLACE_KEEP_CONQUEST
    return float(np.clip(p, 0.0, 1.0))


def _settlements(w, live, cells, sizes):
    """Settlements: a place on the cell of each settled people or polity seat; its size follows the most people seen
    living there."""
    from . import technology
    ids = np.array([b.id for b in live])
    settled = technology._settled(w, ids) if hasattr(w, "farm_share") and len(w.farm_share) > ids.max() \
        else np.zeros(len(ids), dtype=bool)
    seats = set()
    for p in getattr(w, "polities", {}).values():
        if getattr(p, "ended", -1) < 0 and getattr(p, "seat", -1) >= 0:
            seats.add(int(p.seat))
    cell_pop = np.bincount(cells, weights=sizes, minlength=w.planet.n)
    idx = _index(w)
    for i, b in enumerate(live):
        if not (settled[i] or b.id in seats):
            continue
        key = ("settlement", int(b.cell))
        if key not in idx:
            w.places.append({"kind": "settlement", "key": int(b.cell), "cell": int(b.cell), "size": 0.0,
                             "most": 0.0, "layers": []})
            idx[key] = len(w.places) - 1
    for (kind, key), j in idx.items():
        if kind == "settlement":
            p = w.places[j]
            p["most"] = max(float(p.get("most", 0.0)), float(cell_pop[key]))
            p["size"] = float(min(1.0, np.log1p(p["most"]) / np.log1p(P.PLACE_TOWN_REF)))


def yearly(w):
    """Every PLACE_CHECK_YEARS: peoples living by features without a name of their own may name them."""
    if not getattr(P, "PLACES", False):
        return
    if not hasattr(w, "places"):
        init(w)
    live = w.living_bands()
    if not live:
        return
    rng = w.rng["places"]
    t = w.t
    years = P.PLACE_CHECK_YEARS
    sizes = np.asarray(w.live_sizes(), dtype=float)
    cells = np.array([b.cell for b in live])
    _settlements(w, live, cells, sizes)
    feats, near = features(w.planet)
    idx = _index(w)
    # people per feature and language, from the cells each feature is used from
    use: dict = {}                                      # (kind, key) -> {lang: people}
    band_at: dict = {}                                  # (kind, key) -> {lang: a band of that language}
    for i, b in enumerate(live):
        if sizes[i] <= 0 or b.language < 0:
            continue
        keys = [(feats[f][0], feats[f][1]) for f in near.get(int(b.cell), ())]
        if ("settlement", int(b.cell)) in idx:
            keys.append(("settlement", int(b.cell)))
        for k in keys:
            d = use.setdefault(k, {})
            d[b.language] = d.get(b.language, 0.0) + float(sizes[i])
            band_at.setdefault(k, {}).setdefault(b.language, b)
    info = {(feats[f][0], feats[f][1]): (feats[f][2], feats[f][3], len(feats[f][4])) for f in range(len(feats))}
    conquest_ticks = P.PLACE_CONQUEST_YEARS * P.TICKS_PER_YEAR
    for k in sorted(use):
        langs = use[k]
        place = w.places[idx[k]] if k in idx else None
        if k in info:
            anchor, size, n_cells = info[k]
        else:                                           # a settlement: one cell, its size from the most people seen
            anchor, size, n_cells = place["cell"], place["size"], 1
        total = sum(langs.values())
        remote = 1.0 / (1.0 + total / max(n_cells, 1) / P.PLACE_DENSITY_REF)
        for lid in sorted(langs, key=lambda x: (-langs[x], x)):    # the larger community by it names first
            lang = w.languages.get(lid)
            if lang is None or not lang.alive:
                continue
            if place is not None and name_in(w, place, lid) is not None:
                continue
            chance = 1.0 - np.exp(-years * P.PLACE_NAME_RATE * langs[lid] / P.PLACE_POP_REF)
            if rng.random() >= chance:
                continue
            if place is None:
                w.places.append({"kind": k[0], "key": int(k[1]), "cell": int(anchor), "size": float(size),
                                 "layers": []})
                idx[k] = len(w.places) - 1
                place = w.places[-1]
            # holders: peoples here who already have a name for it
            holders = {h: langs[h] for h in langs if h != lid and name_in(w, place, h) is not None}
            b = band_at[k][lid]
            from .language import label
            kind_word = k[0]
            if holders:
                src = max(sorted(holders), key=lambda h: holders[h])
                newcomers = langs[lid] / (langs[lid] + sum(holders.values()))
                conquest = False
                ca = getattr(w, "conquered_at", None)
                if ca is not None:
                    for h in holders:
                        hb = band_at[k][h]
                        if hb.id < len(ca) and ca[hb.id] >= 0 and t - int(ca[hb.id]) <= conquest_ticks:
                            pol = int(w.polity_of[hb.id]) if hb.id < len(w.polity_of) else -1
                            pp = w.polities.get(pol) if pol >= 0 else None
                            if pp is not None and pp.seat >= 0 and pp.seat in w.bands.live \
                                    and w.bands[pp.seat].language in lineage_ids(w, lid) + [lid]:
                                conquest = True
                pk = keep_chance(size, remote, newcomers, conquest)
                src_layer = name_in(w, place, src)
                heard = current(w, src_layer, src)
                if rng.random() < pk:
                    toks, how = list(heard), "kept"
                    note = (f"{label(w, lang)} speakers came to the {kind_word} and kept the name {show(heard)} they heard "
                            f"from {label(w, w.languages[src])} speakers ({pk:.0%} chance: size {size:.2f}, remoteness "
                            f"{remote:.2f}, newcomers {newcomers:.0%} of the people by it"
                            + (", after conquest" if conquest else "") + "); their own sound changes reshape it")
                else:
                    toks, what = _new_name(w, rng, lang, k[0], t)
                    how = "replaced"
                    note = (f"{label(w, lang)} speakers gave the {kind_word} their own name, {show(toks)} ({what}), not "
                            f"{show(heard)} used by {label(w, w.languages[src])} speakers (kept with chance {pk:.0%}: "
                            f"size {size:.2f}, remoteness {remote:.2f}, newcomers {newcomers:.0%}"
                            + (", after conquest" if conquest else "") + ")")
                place["layers"].append([int(t), int(lid), [str(x) for x in toks], how, int(src), note])
            else:
                toks, what = _new_name(w, rng, lang, k[0], t)
                note = (f"{label(w, lang)} speakers, {langs[lid]:,.0f} of them living by it, named the {kind_word} "
                        f"{show(toks)} ({what})")
                place["layers"].append([int(t), int(lid), [str(x) for x in toks], "new", -1, note])
            w.event("place_named", cell=int(place["cell"]), band=b.id, causes=[{"band": b.id}, {"note": note}],
                    place=idx[k], feature=k[0], language=int(lid), how=place["layers"][-1][3], name=show(toks))


def to_json(w):
    return {"places": getattr(w, "places", [])}


def from_json(w, d):
    init(w)
    w.places = (d or {}).get("places", [])
    w._place_key = None
