"""Languages: change, contact, splitting, and names built from each language's words.

Every band or group speaks one language. Languages change as wholes:
regular sound changes (lang/changes.py), replacement of words, and borrowing
from languages in contact. When a language's speakers become separated (no
contact within two rings of land, the partner network) for three checks in a
row, or spread over too much land to stay one speech community, it splits
into daughter languages. Each language keeps its own history, so any word at
any time can be rebuilt from the proto-language.

reads: bands, people (names), planet grid
writes: languages, bands.language, people.lang, events (language_split, language_extinct)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import params as P
from ..lang import changes as CH
from ..lang.proto import MEANINGS, NAME_FIRST, NAME_SECOND, PROTO, parse, roman, show

MEANING_INDEX = {m: i for i, m in enumerate(MEANINGS)}


@dataclass
class Language:
    id: int
    parent: int
    born: int
    ended: int = -1
    lexicon: dict = field(default_factory=dict)     # meaning -> [tokens(list), root, origin]
    history: list = field(default_factory=list)     # [t, kind, payload...]
    applied: list = field(default_factory=list)     # sound-change ids in this lineage
    sep: int = 0                                    # consecutive checks with separated speakers

    @property
    def alive(self):
        return self.ended < 0


def name_of(lang: Language) -> str:
    s = roman(tuple(lang.lexicon["people"][0])) or "?"
    return s[:1].upper() + s[1:]


def init(w):
    lex = {m: [list(parse(f)), i, "inherited"] for i, (m, f) in enumerate(PROTO.items())}
    lang = Language(0, -1, 0, lexicon=lex)
    w.languages = {0: lang}
    w.next_lang = 1
    w.next_root = 10_000


def ring2(w):
    """Cells within two rings of each cell (cached on the planet)."""
    pl = w.planet
    if getattr(pl, "_ring2", None) is None:
        nb = pl.grid.neighbours
        out = []
        for c in range(pl.n):
            s = {c}
            f1 = [int(x) for x in nb[c] if x >= 0]
            s.update(f1)
            for x in f1:
                s.update(int(y) for y in nb[x] if y >= 0)
            out.append(np.array(sorted(s)))
        pl._ring2 = out
    return pl._ring2


# ------------------------------------------------------------------ names
def compose_name(lang: Language, a: int, b: int, female: bool) -> str:
    first = list(lang.lexicon[NAME_FIRST[a]][0])
    if b < 0:
        toks = first
    else:
        if len(first) > 2 and first[-1] == "s":
            first = first[:-1]
        toks = first + list(lang.lexicon[NAME_SECOND[b]][0])
    if female:
        if len(toks) > 2 and toks[-1] == "s":
            toks = toks[:-1]
        if toks and toks[-1] in CH.V:
            toks = toks[:-1] + ["a"]
        else:
            toks = toks + ["a"]
    s = roman(tuple(toks)) or "?"
    return s[:1].upper() + s[1:]


# ------------------------------------------------------------------ history
def lineage(w, lang_id: int) -> list:
    out = []
    while lang_id >= 0:
        out.append(w.languages[lang_id])
        lang_id = w.languages[lang_id].parent
    return out[::-1]


def word_history(w, lang_id: int, meaning: str, until_t: int | None = None) -> list:
    """Every change to one word from the proto-language to `until_t`: [(t, form, what changed)]."""
    form = parse(PROTO[meaning])
    steps = [(0, show(form), "proto-language form")]
    chain = lineage(w, lang_id)
    for k, lang in enumerate(chain):
        end = chain[k + 1].born if k + 1 < len(chain) else (until_t if until_t is not None else 10 ** 12)
        for ev in lang.history:
            t = ev[0]
            if t >= end:
                break
            if ev[1] == "rule":
                new = CH.apply(ev[2], form)
                if new != form:
                    form = new
                    steps.append((t, show(form), CH.describe(ev[2])))
            elif ev[2] == meaning:
                form = tuple(ev[3])
                what = "new word" if ev[1] == "replace" else f"borrowed from {ev[5]}"
                steps.append((t, show(form), what))
    return steps


# ------------------------------------------------------------------ change
def _apply_rule(lang: Language, rid: str, t: int):
    for m, entry in lang.lexicon.items():
        entry[0] = list(CH.apply(rid, tuple(entry[0])))
    lang.applied.append(rid)
    lang.history.append([t, "rule", rid])


def _new_word(rng, lang: Language) -> list:
    inv = sorted({p for e in lang.lexicon.values() for p in e[0]})
    vow = [p for p in inv if p in CH.V] or ["a"]
    con = [p for p in inv if p not in CH.V and p not in ("R", "L", "M", "N")] or ["t"]
    syl = int(rng.integers(1, 3))
    out = []
    for _ in range(syl):
        out.append(con[int(rng.integers(len(con)))])
        out.append(vow[int(rng.integers(len(vow)))])
    if rng.random() < 0.5:
        out.append(con[int(rng.integers(len(con)))])
    return out


def _speakers(w):
    by = {}
    for b in w.living_bands():
        by.setdefault(b.language, []).append(b)
    return by


def _components(cells: set, r2) -> list:
    cells = set(cells)
    comps = []
    while cells:
        start = cells.pop()
        comp = {start}
        stack = [start]
        while stack:
            c = stack.pop()
            for m in r2[c]:
                m = int(m)
                if m in cells:
                    cells.remove(m)
                    comp.add(m)
                    stack.append(m)
        comps.append(comp)
    return comps


def _bisect(w, bands) -> list:
    """Split a sprawling speech area into two halves along its longest axis."""
    xyz = w.planet.grid.xyz[[b.cell for b in bands]]
    c = xyz - xyz.mean(0)
    axis = np.linalg.svd(c, full_matrices=False)[2][0]
    side = c @ axis >= 0
    return [{b.cell for b, s in zip(bands, side) if s}, {b.cell for b, s in zip(bands, side) if not s}]


def split(w, lang: Language, groups: list, why: str):
    t = w.t
    lang.ended = t
    kids = []
    for cells in groups:
        k = Language(w.next_lang, lang.id, t,
                     lexicon={m: [list(e[0]), e[1], e[2]] for m, e in lang.lexicon.items()},
                     applied=list(lang.applied))
        w.languages[k.id] = k
        w.next_lang += 1
        for b in w.living_bands():
            if b.language == lang.id and b.cell in cells:
                b.language = k.id
                mem = w.members(b.id)
                if len(mem):
                    w.people.lang[mem[w.people.lang[mem] == lang.id]] = k.id
        kids.append(k)
    w.event("language_split", cause_note=why, causes=[{"note": why}], language=lang.id,
            daughters=[k.id for k in kids], name=name_of(lang))
    return kids


def check(w):
    """Every LANGUAGE_CHECK_YEARS: extinctions, splits, sound change, replacement, borrowing."""
    rng = w.rng["language"]
    t = w.t
    years = P.LANGUAGE_CHECK_YEARS
    r2 = ring2(w)
    speakers = _speakers(w)
    for lang in list(w.languages.values()):
        if lang.alive and lang.id not in speakers:
            lang.ended = t
            w.event("language_extinct", causes=[{"note": "no remaining speakers"}], language=lang.id,
                    name=name_of(lang))
    # splitting: only separations between sizeable communities count; small outlying
    # fragments keep the speech of the largest community (they are too few to drift alone)
    sizes = w.band_sizes()
    for lid in sorted(speakers):
        lang = w.languages[lid]
        bands = speakers[lid]
        cells = {b.cell for b in bands}
        comps = _components(cells, r2)
        pop = {}
        for b in bands:
            pop[b.cell] = pop.get(b.cell, 0.0) + float(sizes[b.id])
        major = [c for c in comps if sum(pop[x] for x in c) >= P.LANGUAGE_SPLIT_PEOPLE]
        if len(major) > 1:
            lang.sep += 1
            if lang.sep >= P.LANGUAGE_SPLIT_CHECKS:
                major.sort(key=lambda c: -sum(pop[x] for x in c))
                for c in comps:
                    if c not in major:
                        major[0] |= c
                split(w, lang, major, f"speakers of {name_of(lang)} separated into {len(major)} communities "
                                      f"with no contact for about {lang.sep * years} years")
                continue
        else:
            lang.sep = 0
        if len(cells) > P.LANGUAGE_MAX_CELLS:
            split(w, lang, _bisect(w, bands), f"{name_of(lang)} spread over {len(cells)} areas of land, too wide "
                                               f"to remain one speech community")
    speakers = _speakers(w)
    # contact: which languages are spoken within two rings of each language's land
    cell_langs: dict[int, set] = {}
    for lid, bands in speakers.items():
        for b in bands:
            cell_langs.setdefault(b.cell, set()).add(lid)
    for lid in sorted(speakers):
        lang = w.languages[lid]
        # sound change
        if rng.random() < 1 - np.exp(-years / P.SOUND_CHANGE_YEARS):
            opts = CH.eligible(set(lang.applied), [tuple(e[0]) for e in lang.lexicon.values()])
            if opts:
                wts = np.array([CH.RULES[r][1] for r in opts])
                rid = opts[int(rng.choice(len(opts), p=wts / wts.sum()))]
                _apply_rule(lang, rid, t)
        # replacement
        k = rng.poisson(years * len(MEANINGS) * P.WORD_REPLACEMENT_RATE)
        for _ in range(int(k)):
            m = MEANINGS[int(rng.integers(len(MEANINGS)))]
            form = _new_word(rng, lang)
            lang.lexicon[m] = [form, w.next_root, "new word"]
            lang.history.append([t, "replace", m, form, w.next_root])
            w.next_root += 1
        # borrowing
        contact = {}
        for b in speakers[lid]:
            for c in r2[b.cell]:
                for other in cell_langs.get(int(c), ()):
                    if other != lid:
                        contact[other] = contact.get(other, 0) + 1
        if contact:
            k = rng.poisson(years * P.BORROWING_RATE)
            donors = sorted(contact)
            wts = np.array([contact[d] for d in donors], dtype=float)
            for _ in range(int(k)):
                d = w.languages[donors[int(rng.choice(len(donors), p=wts / wts.sum()))]]
                m = MEANINGS[int(rng.integers(len(MEANINGS)))]
                form, root = list(d.lexicon[m][0]), d.lexicon[m][1]
                lang.lexicon[m] = [form, root, f"borrowed from {name_of(d)}"]
                lang.history.append([t, "borrow", m, form, root, name_of(d)])


# ------------------------------------------------------------------ measures
def shared_roots(a: Language, b: Language) -> float:
    return sum(a.lexicon[m][1] == b.lexicon[m][1] for m in MEANINGS) / len(MEANINGS)


def common_ancestor_time(w, a: int, b: int) -> int:
    la, lb = lineage(w, a), lineage(w, b)
    k = 0
    while k < min(len(la), len(lb)) and la[k].id == lb[k].id:
        k += 1
    # the split happened when the first differing descendants were born
    return min(la[k].born if k < len(la) else w.t, lb[k].born if k < len(lb) else w.t)


def to_json(w):
    return {"next_lang": w.next_lang, "next_root": w.next_root,
            "languages": [[l.id, l.parent, l.born, l.ended, l.lexicon, l.history, l.applied, l.sep]
                          for l in w.languages.values()]}


def from_json(w, d):
    w.next_lang, w.next_root = d["next_lang"], d["next_root"]
    w.languages = {}
    for i, par, born, ended, lex, hist, applied, sep in d["languages"]:
        w.languages[i] = Language(i, par, born, ended, lex, hist, applied, sep)
