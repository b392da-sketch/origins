"""A catalogue of regular sound changes, each a common, well-attested type.

Every rule applies to every word in a language where its conditions hold
(regularity), which is what keeps related words traceable. Rules are inspired
by changes seen in Indo-European daughters (Grimm's law in Germanic, satem
palatal shifts, Greek loss of initial s and w, Latin rhotacism, and so on),
but any language here may take any rule in any order: this is a generator of
plausible histories, not a reconstruction of real ones.
"""
from __future__ import annotations

from .proto import ASPIRATES, FRONT, LARYNGEALS, STOPS_VD, STOPS_VL, SYLLABIC, VOWELS

V = VOWELS
CONS = lambda t: t not in VOWELS and t not in SYLLABIC  # noqa: E731
SHORT_LONG = {"e": "E", "o": "O", "a": "A", "i": "I", "u": "U"}
LONG_SHORT = {v: k for k, v in SHORT_LONG.items()}


def _map(word, table, cond=None):
    out = list(word)
    for i, t in enumerate(word):
        if t in table and (cond is None or cond(word, i)):
            out[i] = table[t]
    return tuple(x for x in out if x != "")


def _between_vowels(w, i):
    return 0 < i < len(w) - 1 and w[i - 1] in V and w[i + 1] in V


def r_laryngeals(w):
    """Laryngeals lost: h₂ colours a neighbouring e to a, h₃ colours it to o; a vowel before a lost laryngeal is lengthened; between consonants they become a."""
    w = list(w)
    out = []
    i = 0
    while i < len(w):
        t = w[i]
        if t in LARYNGEALS:
            nxt = w[i + 1] if i + 1 < len(w) else None
            prev = out[-1] if out else None
            colour = {"h1": None, "h2": "a", "h3": "o"}[t]
            if nxt == "e" and colour:
                w[i + 1] = colour
            if prev in SHORT_LONG:
                out[-1] = SHORT_LONG[colour if (prev == "e" and colour) else prev]
            elif prev is not None and prev not in V and nxt is not None and nxt not in V:
                out.append("a")
            i += 1
            continue
        out.append(t)
        i += 1
    return tuple(out)


def make_syllabic(variant):
    table = {"ar": {"R": ("a", "r"), "L": ("a", "l"), "M": ("a", "m"), "N": ("a", "n")},
             "ur": {"R": ("u", "r"), "L": ("u", "l"), "M": ("u", "m"), "N": ("u", "n")},
             "ri": {"R": ("r", "i"), "L": ("l", "i"), "M": ("a",), "N": ("a",)}}[variant]

    def f(w):
        out = []
        for t in w:
            out.extend(table.get(t, (t,)))
        return tuple(out)
    f.__doc__ = {"ar": "Syllabic r̥ l̥ m̥ n̥ become ar al am an.",
                 "ur": "Syllabic r̥ l̥ m̥ n̥ become ur ul um un.",
                 "ri": "Syllabic r̥ l̥ become ri li; m̥ n̥ become a."}[variant]
    return f


def simple(table, doc, cond=None):
    def f(w):
        return _map(w, table, cond)
    f.__doc__ = doc
    return f


def r_apocope(w):
    """Final short vowels are lost in words of two or more syllables."""
    if len(w) > 1 and w[-1] in {"e", "o", "a", "i", "u"} and sum(t in V for t in w) >= 2:
        return w[:-1]
    return w


def r_final_s(w):
    """Word-final s is lost."""
    return w[:-1] if len(w) > 1 and w[-1] == "s" else w


def r_final_stop(w):
    """Word-final stops are lost."""
    return w[:-1] if len(w) > 1 and w[-1] in {"p", "t", "k", "b", "d", "g"} else w


def r_initial_s(w):
    """Initial s before a vowel becomes h."""
    return ("h",) + w[1:] if len(w) > 1 and w[0] == "s" and w[1] in V else w


def r_initial_w(w):
    """Initial w is lost."""
    return w[1:] if len(w) > 1 and w[0] == "w" else w


def r_monophthong(w):
    """Diphthongs ey oy become ē; ew ow become ō (before a consonant or at the end)."""
    out = []
    i = 0
    while i < len(w):
        if i + 1 < len(w) and w[i] in ("e", "o", "a") and w[i + 1] in ("y", "w") and (i + 2 == len(w) or w[i + 2] not in V):
            out.append("E" if w[i + 1] == "y" else "O")
            i += 2
            continue
        out.append(w[i])
        i += 1
    return tuple(out)


def r_cluster(w):
    """In clusters of three consonants, the middle one is lost."""
    out = list(w)
    i = 1
    while i < len(out) - 1:
        if CONS(out[i - 1]) and CONS(out[i]) and CONS(out[i + 1]):
            del out[i]
        else:
            i += 1
    return tuple(out)


def _not_after_s(w, i):
    return not (i > 0 and w[i - 1] == "s")


def _before_front(w, i):
    return i + 1 < len(w) and w[i + 1] in FRONT


def _final(w, i):
    return i == len(w) - 1


def _before_labial(w, i):
    return i + 1 < len(w) and w[i + 1] in {"p", "b", "bh", "m"}


# id -> (function, weight); weights favour common changes
RULES = {
    "laryngeal_loss": (r_laryngeals, 6.0),
    "syllabic_ar": (make_syllabic("ar"), 1.0),
    "syllabic_ur": (make_syllabic("ur"), 1.0),
    "syllabic_ri": (make_syllabic("ri"), 1.0),
    "deaspiration": (simple({"bh": "b", "dh": "d", "gh": "g", "gwh": "gw", "gjh": "gj"},
                            "Voiced aspirates lose their aspiration: bʰ dʰ gʰ become b d g."), 1.5),
    "aspirates_to_fricatives": (simple({"bh": "f", "dh": "th", "gh": "x", "gwh": "xw", "gjh": "x"},
                                       "Voiced aspirates become fricatives: bʰ dʰ gʰ become f þ χ."), 0.7),
    "grimm_fricatives": (simple({"p": "f", "t": "th", "k": "x", "kw": "xw", "kj": "x"},
                                "Voiceless stops become fricatives, except after s: p t k become f þ χ (as in Grimm's law).",
                                _not_after_s), 1.0),
    "devoicing": (simple({"b": "p", "d": "t", "g": "k", "gw": "kw", "gj": "kj"},
                         "Voiced stops become voiceless: b d g become p t k."), 0.8),
    "satem": (simple({"kj": "s", "gj": "z", "gjh": "z", "kw": "k", "gw": "g", "gwh": "gh"},
                     "Palatal stops become sibilants (ḱ ǵ become s z) and labiovelars lose rounding (as in satem languages)."), 1.2),
    "centum": (simple({"kj": "k", "gj": "g", "gjh": "gh"},
                      "Palatal stops merge with plain velars: ḱ ǵ become k g (as in centum languages)."), 1.2),
    "labiovelars_to_labials": (simple({"kw": "p", "gw": "b", "gwh": "bh"},
                                      "Labiovelars become labials: kʷ gʷ become p b."), 0.6),
    "labiovelars_lose_rounding": (simple({"kw": "k", "gw": "g", "gwh": "gh", "xw": "x"},
                                         "Labiovelars lose their rounding: kʷ gʷ become k g."), 0.8),
    "palatalisation": (simple({"k": "ch", "g": "j"}, "k g become č ǰ before front vowels.", _before_front), 1.0),
    "a_merger": (simple({"e": "a", "o": "a", "E": "A", "O": "A"}, "e and o merge into a."), 0.6),
    "o_to_a": (simple({"o": "a"}, "Short o becomes a."), 0.7),
    "long_raising": (simple({"E": "I", "O": "U"}, "Long ē ō rise to ī ū."), 0.8),
    "monophthongisation": (r_monophthong, 1.0),
    "intervocalic_voicing": (simple({"p": "b", "t": "d", "k": "g", "f": "v", "th": "dd", "s": "z"},
                                    "Voiceless consonants become voiced between vowels.", _between_vowels), 1.2),
    "intervocalic_spirants": (simple({"b": "v", "d": "dd", "g": "gg"},
                                     "b d g become v ð ɣ between vowels.", _between_vowels), 0.9),
    "rhotacism": (simple({"s": "r", "z": "r"}, "s becomes r between vowels (as in Latin).", _between_vowels), 0.6),
    "initial_s_to_h": (r_initial_s, 0.6),
    "h_loss": (simple({"h": ""}, "h is lost everywhere."), 0.6),
    "w_to_v": (simple({"w": "v"}, "w becomes v."), 0.7),
    "initial_w_loss": (r_initial_w, 0.4),
    "apocope": (r_apocope, 0.9),
    "final_s_loss": (r_final_s, 0.6),
    "final_stop_loss": (r_final_stop, 0.6),
    "final_m_to_n": (simple({"m": "n"}, "Word-final m becomes n.", _final), 0.5),
    "nasal_assimilation": (simple({"n": "m"}, "n becomes m before labials.", _before_labial), 0.6),
    "cluster_simplification": (r_cluster, 0.8),
    "length_loss": (simple(LONG_SHORT, "Vowel length is lost: long vowels become short."), 0.6),
}

# rules that only make sense once laryngeals/syllabics are resolved, or are alternatives
EXCLUSIVE = [{"syllabic_ar", "syllabic_ur", "syllabic_ri"}, {"satem", "centum"},
             {"deaspiration", "aspirates_to_fricatives"}, {"labiovelars_to_labials", "labiovelars_lose_rounding"}]


def describe(rule_id: str) -> str:
    return (RULES[rule_id][0].__doc__ or rule_id).strip()


def apply(rule_id: str, word: tuple) -> tuple:
    return RULES[rule_id][0](word)


def eligible(applied: set, lexicon_words) -> list:
    """Rules not yet used by this lineage that would change at least one word."""
    out = []
    for rid in RULES:
        if rid in applied:
            continue
        if any(rid in g and (g & applied) for g in EXCLUSIVE):
            continue
        fn = RULES[rid][0]
        if any(fn(w) != w for w in lexicon_words):
            out.append(rid)
    return out
