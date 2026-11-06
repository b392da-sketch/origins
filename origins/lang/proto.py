"""The proto-language: a PIE-inspired core vocabulary.

Forms follow commonly cited Proto-Indo-European reconstructions, simplified:
accents are dropped, some stems are given in a single citation form, and a few
uncertain details are regularised. This is an aesthetic starting point for a
fictional world (decided in Design Draft v0.3), not a claim that these people
speak PIE or that these forms are authoritative.

Tokens (phonemes) are separated by dots. Notation:
  kw gw gwh = labiovelars (kʷ gʷ gʷʰ); kj gj gjh = palatovelars (ḱ ǵ ǵʰ)
  bh dh gh = voiced aspirates; h1 h2 h3 = laryngeals
  E O A I U = long vowels; R L M N = syllabic resonants (r̥ l̥ m̥ n̥)
"""
from __future__ import annotations

PROTO = {
    # people and kin
    "people": "t.e.w.t.e.h2", "man": "h2.n.E.r", "mother": "m.e.h2.t.E.r", "father": "p.h2.t.E.r",
    "daughter": "dh.u.g.h2.t.E.r", "son": "s.u.n.u.s", "brother": "bh.r.e.h2.t.E.r", "sister": "s.w.e.s.O.r",
    "god": "d.e.y.w.o.s", "sky": "d.y.E.w.s", "ruler": "h3.r.E.gj.s", "name": "h1.n.o.m.N",
    # the world
    "water": "w.o.d.R", "fire": "p.e.h2.w.R", "earth": "dh.e.gjh.O.m", "dawn": "h2.e.w.s.O.s",
    "sun": "s.e.h2.w.L", "moon": "m.e.h1.N.s", "star": "h2.s.t.E.r", "night": "n.o.kw.t.s",
    "snow": "s.n.o.y.gwh.o.s", "wind": "h2.w.e.h1.N.t.o.s", "stone": "h2.e.kj.m.O", "wood": "d.o.r.u",
    "salt": "s.e.h2.l.s", "honey": "m.e.l.i.t", "path": "p.o.n.t.e.h1.s",
    # animals
    "horse": "h1.e.kj.w.o.s", "cow": "gw.O.w.s", "sheep": "h2.o.w.i.s", "dog": "kj.w.O",
    "wolf": "w.L.kw.o.s", "bear": "h2.R.t.kj.o.s", "mouse": "m.U.s", "bird": "h2.e.w.i.s",
    "egg": "h2.O.w.y.o.m",
    # body
    "heart": "kj.E.r", "foot": "p.O.d.s", "tooth": "h1.d.o.n.t.s", "eye": "h3.e.kw.s",
    "ear": "h2.O.w.s", "nose": "n.e.h2.s", "tongue": "d.N.gjh.w.e.h2.s", "knee": "gj.e.n.u",
    "bone": "h3.e.s.t.h1", "blood": "h1.e.s.h2.R",
    # things made
    "house": "d.o.m.h2", "door": "dh.w.O.r", "yoke": "y.u.g.o.m", "wheel": "kw.e.kw.l.o.s",
    # actions
    "eat": "h1.e.d", "drink": "p.e.h3", "give": "d.e.h3", "know": "gj.n.e.h3", "see": "w.e.y.d",
    "die": "m.e.r", "strike": "gwh.e.n", "come": "gw.e.m", "stand": "s.t.e.h2", "sit": "s.e.d",
    "sleep": "s.w.e.p", "carry": "bh.e.r", "lie": "l.e.gh", "float": "p.l.e.w", "fly": "p.e.t",
    "measure": "m.e.d",
    # qualities
    "new": "n.e.w.o.s", "full": "p.L.h1.n.o.s", "old": "s.e.n.o.s", "red": "h1.r.e.w.dh.r.o.s",
    "bright": "h2.e.r.gj", "light": "l.e.w.k", "warm": "gwh.e.r.m.o.s", "cold": "g.e.l",
    "good": "h1.s.u", "great": "m.e.gj.h2",
    # abstract and grammatical
    "fame": "kj.l.e.w.o.s", "mind": "m.e.n.o.s", "gift": "d.e.h3.r.o.m", "goods": "h1.w.e.s.u",
    "one": "h1.o.y.n.o.s", "two": "d.w.o.h1", "three": "t.r.e.y.e.s", "four": "kw.e.t.w.o.r.e.s",
    "five": "p.e.n.kw.e", "ten": "d.e.kj.N.t", "hundred": "kj.M.t.o.m",
    "I": "h1.e.gj.h2", "you": "t.u.h2", "we": "w.e.y", "that": "t.o.d", "who": "kw.i.s", "not": "n.e",
}

MEANINGS = list(PROTO)

# Name elements (M0's PIE-inspired names), now drawn from each language's own words.
NAME_FIRST = ["good", "great", "god", "goods", "man", "ruler", "know", "dawn", "horse", "cow",
              "bear", "wolf", "water", "carry", "light"]
NAME_SECOND = ["fame", "measure", "man", "carry", "mind", "goods", "gift", "ruler"]

VOWELS = {"e", "o", "a", "i", "u", "E", "O", "A", "I", "U"}
FRONT = {"e", "i", "E", "I"}
SYLLABIC = {"R", "L", "M", "N"}
LARYNGEALS = {"h1", "h2", "h3"}
STOPS_VL = {"p", "t", "k", "kw", "kj"}
STOPS_VD = {"b", "d", "g", "gw", "gj"}
ASPIRATES = {"bh", "dh", "gh", "gwh", "gjh"}

DISPLAY = {"kw": "kʷ", "gw": "gʷ", "gwh": "gʷʰ", "kj": "ḱ", "gj": "ǵ", "gjh": "ǵʰ", "bh": "bʰ", "dh": "dʰ",
           "gh": "gʰ", "h1": "h₁", "h2": "h₂", "h3": "h₃", "E": "ē", "O": "ō", "A": "ā", "I": "ī", "U": "ū",
           "R": "r̥", "L": "l̥", "M": "m̥", "N": "n̥", "th": "þ", "dd": "ð", "gg": "ɣ", "x": "χ", "xw": "χʷ",
           "ch": "č", "j": "ǰ", "sh": "š", "zh": "ž"}
ROMAN = {"kw": "qu", "gw": "gu", "gwh": "gu", "kj": "k", "gj": "g", "gjh": "g", "bh": "b", "dh": "d", "gh": "g",
         "h1": "", "h2": "", "h3": "", "E": "e", "O": "o", "A": "a", "I": "i", "U": "u", "R": "er", "L": "el",
         "M": "em", "N": "en", "th": "th", "dd": "dh", "gg": "gh", "x": "kh", "xw": "khw", "ch": "ch", "j": "j",
         "sh": "sh", "zh": "zh", "y": "y", "w": "w"}


def parse(s: str) -> tuple:
    return tuple(s.split("."))


def show(tokens) -> str:
    """Scholarly display, e.g. h₂nḗr -> h₂nēr."""
    return "".join(DISPLAY.get(t, t) for t in tokens)


def roman(tokens) -> str:
    """Readable romanisation for names (laryngeals silent, aspiration and length dropped)."""
    s = "".join(ROMAN.get(t, t) for t in tokens)
    return s
