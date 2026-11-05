"""PIE-inspired personal names.

An aesthetic choice for a fictional world: the elements below are commonly
reconstructed Proto-Indo-European roots, used in simplified romanised form.
Reconstructed PIE personal names were often two-part compounds (compare
Greek Sophokles, Perikles with -kles 'fame'; Slavic Vladislav with slava
'glory'). Real PIE belongs to a much later era than this world's start; no
claim is made that these people speak it. From M1, each lineage's names
will change through regular sound changes.

Each element: (reconstructed root, romanised stem, gloss).
"""
from __future__ import annotations

FIRST = [
    ("*h1su-", "Su", "good"),
    ("*meg'h2-", "Mega", "great"),
    ("*deywo-", "Deiwo", "god, of the sky"),
    ("*h1wesu-", "Wesu", "good, goods"),
    ("*h2ner-", "Ner", "man, vigour"),
    ("*h3reg'-", "Reg", "ruler, straight"),
    ("*g'neh3-", "Gno", "know"),
    ("*h2ews-", "Aus", "dawn"),
    ("*h1ek'wo-", "Ekwo", "horse"),
    ("*gwow-", "Gwou", "cow"),
    ("*h2rtk'o-", "Artko", "bear"),
    ("*wlkwo-", "Wolkwo", "wolf"),
    ("*h2ekwa-", "Akwa", "water"),
    ("*bher-", "Bher", "carry"),
    ("*leuk-", "Leuko", "light, bright"),
]

SECOND = [
    ("*-k'lewos", "klewos", "fame"),
    ("*-medes", "medes", "counsel, measure"),
    ("*-h2ner", "ner", "man, vigour"),
    ("*-bhoros", "bhoros", "bearing, carrier"),
    ("*-menes", "menes", "mind, spirit"),
    ("*-wesu", "wesu", "goods"),
    ("*-doros", "doros", "gift"),
    ("*-h3reg's", "reks", "ruler"),
]


def _feminine(stem: str) -> str:
    if stem.endswith("os"):
        return stem[:-2] + "a"
    if stem.endswith("es"):
        return stem[:-2] + "ea"
    if stem.endswith(("r", "s", "u")):
        return stem + "a"
    return stem + "a"


def draw(rng) -> tuple[int, int]:
    """Pick name elements: (first index, second index or -1 for a short name)."""
    a = int(rng.integers(len(FIRST)))
    if rng.random() < 0.18:
        return a, -1
    return a, int(rng.integers(len(SECOND)))


def render(a: int, b: int, female: bool) -> str:
    first = FIRST[a][1]
    if b < 0:
        stem = first + ("os" if not first.endswith(("o", "s", "u")) else "")
        return (_feminine(stem) if female else stem).capitalize()
    second = SECOND[b][1]
    if first[-1] in "aeiou" and second[0] in "aeiou":
        first = first[:-1]
    stem = first + second
    return (_feminine(stem) if female else stem).capitalize()


def etymology(a: int, b: int) -> str:
    if b < 0:
        return f"{FIRST[a][0]} '{FIRST[a][2]}' (short name)"
    return f"{FIRST[a][0]} '{FIRST[a][2]}' + {SECOND[b][0]} '{SECOND[b][2]}'"
