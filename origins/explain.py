"""Turn any recorded happening into a readable cause chain.

References are small dicts:
  {"event": id}           a logged event (bad year, split, merge, ...)
  {"death": person}       a person's death, from their record
  {"birth": person}       a person's birth
  {"partnership": person} the partnership in force when that woman conceived
  {"note": "..."}         a plain recorded fact (a leaf)
"""
from __future__ import annotations

from . import params as P
from .state import C, CAUSES


def when(w, t: int) -> str:
    year = t // P.TICKS_PER_YEAR
    season = ["spring", "summer", "autumn", "winter"][t % P.TICKS_PER_YEAR]
    return f"{P.START_YEARS_BP - year:,} years before present, {season} (northern calendar)"


def _war_reasons(w, e) -> str:
    sc, share, cd, g = e["data"]["why"]
    a = w.bands.get(e["band"])
    t = w.bands.get(e["data"].get("target"))
    reasons = []
    if sc > 0:
        reasons.append(f"hunger at home (scarcity {sc:.2f})")
    reasons.append(f"strength {share:.0%} of the fighters on both sides")
    if cd > 0.3:
        reasons.append(f"a different people (cultural distance {cd:.2f})")
    if g >= 1:
        reasons.append(f"revenge for {g:.0f} remembered killings")
    an = w.band_name(a) if a else "a band"
    tn = w.band_name(t) if t else "a neighbour"
    return f"{an} attacked {tn}: " + "; ".join(reasons)


def describe(w, ref: dict) -> dict:
    p = w.people
    if "note" in ref:
        return {"title": ref["note"], "causes": []}
    if "event" in ref:
        e = w.events[int(ref["event"])]
        title = _event_title(w, e)
        causes = e["causes"]
        if e["kind"] == "war" and "why" in e["data"]:
            causes = [{"note": _war_reasons(w, e)}] + causes
        return {"title": title, "t": e["t"], "when": when(w, e["t"]), "cell": e["cell"], "causes": causes,
                "ref": ref}
    if "death" in ref:
        i = int(ref["death"])
        age = (p.death[i] - p.birth[i]) / P.TICKS_PER_YEAR
        cause = CAUSES[int(p.cause[i])]
        causes = [{"note": f"age {age:.1f}"}]
        if p.cause[i] == C["hunger"] or p.death_cond[i] < 0.5:
            causes.append({"note": f"body condition {p.death_cond[i]:.2f}; their band received "
                                   f"{p.death_ratio[i]:.0%} of its food needs that season"})
            if p.death_bad[i] >= 0:
                causes.append({"event": int(p.death_bad[i])})
            if p.death_interv[i] >= 0:
                causes.append({"event": int(p.death_interv[i])})
        if p.death_hazard[i] >= 0:
            causes.append({"event": int(p.death_hazard[i])})
        if p.cause[i] == C["orphaned infant"] and p.mother[i] >= 0:
            m = int(p.mother[i])
            if p.death[m] >= 0:
                causes.append({"death": m})
            else:
                causes.append({"note": f"separated from their mother {p.name(m)}, whose people were later "
                                       f"counted only as a group (her record ends there)"})
        if p.cause[i] == C["childbirth"]:
            kids = [k for k in range(p.n) if p.mother[k] == i and p.birth[k] == p.death[i]] if p.n < 200000 else []
            causes += [{"birth": int(k)} for k in kids[:1]]
        if p.cause[i] == C["infancy and early childhood"]:
            causes.append({"note": "high background risk of illness in early childhood"})
        if p.cause[i] == C["old age"]:
            causes.append({"note": "risk rising with age"})
        if p.cause[i] == C["accident or illness"]:
            causes.append({"note": "background risk of accident or illness at any age"})
        return {"title": f"Death of {p.name(i)} ({cause})", "t": int(p.death[i]), "when": when(w, int(p.death[i])),
                "cell": int(p.death_cell[i]), "person": i, "causes": causes, "ref": ref}
    if "birth" in ref:
        i = int(ref["birth"])
        m, f = int(p.mother[i]), int(p.father[i])
        if m < 0:
            how = ("a founder of the world" if p.unfolded[i] < 0 else
                   f"ancestry unrecorded: brought out of a folded group in "
                   f"{P.START_YEARS_BP - int(p.unfolded[i]) // P.TICKS_PER_YEAR:,} BP, with age and sex from the group's "
                   f"counts; parents and earlier life were not followed")
            return {"title": f"{p.name(i)}: {how}", "t": int(p.birth[i]), "causes": [], "ref": ref, "person": i}
        parents = p.name(m) + (f" and {p.name(f)}" if f >= 0 else "")
        causes = [{"note": f"conceived about {P.PREGNANCY_TICKS} seasons earlier"}]
        if f >= 0:
            causes.append({"partnership": m})
        return {"title": f"Birth of {p.name(i)} to {parents}", "t": int(p.birth[i]),
                "when": when(w, int(p.birth[i])), "cell": int(p.birth_cell[i]), "person": i, "causes": causes, "ref": ref}
    if "partnership" in ref:
        i = int(ref["partnership"])
        j = int(p.partner[i]) if p.partner[i] >= 0 else -1
        who = p.name(i) + (f" and {p.name(j)}" if j >= 0 else "")
        return {"title": f"Partnership of {who}", "causes": [
            {"note": "both unpartnered adults living in the same or neighbouring land; not close kin"}], "ref": ref}
    if "band" in ref:
        b = w.bands[int(ref["band"])]
        origin = next((e for e in w.events if e["kind"] == "fission" and e["data"].get("new_band") == b.id), None)
        causes = [{"event": origin["id"]}] if origin else [{"event": 0}]
        return {"title": f"Origin of {w.band_name(b)}", "t": b.founded, "causes": causes, "ref": ref}
    return {"title": "unknown reference", "causes": []}


def _event_title(w, e) -> str:
    k, d = e["kind"], e["data"]
    b = w.bands.get(e["band"])
    bn = w.band_name(b) if b else ""
    if k == "founding":
        return f"The world begins: {bn} ({d.get('size')} people)"
    if k == "bad_year":
        return f"Bad year in climate region {d.get('region')} (wild food at {d.get('factor', 0):.0%} of normal)"
    if k == "fission":
        nb = w.bands.get(d.get("new_band"))
        return f"{bn} split: {d.get('moved')} people left to form {w.band_name(nb) if nb else 'a new band'}"
    if k == "merge":
        o = w.bands.get(d.get("into"))
        return f"{bn} ({d.get('size')} people) joined {w.band_name(o) if o else 'another band'}"
    if k == "band_extinct":
        return f"{bn} died out"
    if k == "group_hunger_deaths":
        return f"{d.get('deaths')} hunger deaths in {bn}"
    if k == "fold":
        return f"{d.get('folded'):,} people in distant bands are now followed as groups"
    if k == "unfold":
        return f"{bn} is followed person by person: {d.get('people')} people brought out of a folded group (ancestry unrecorded)"
    if k == "separation":
        return "A partnership ended"
    if k == "intervention":
        return f"Observer intervention: {d.get('what', '')}"
    if k == "extinction":
        return "Humanity died out"
    if k == "language_split":
        return f"{d.get('name')} divided into {', '.join(d.get('names', [])) or 'daughter languages'}"
    if k == "language_extinct":
        return f"The last speakers of {d.get('name')} are gone"
    if k == "sea_crossing":
        return f"{bn} ({d.get('size')} people) crossed the sea to new land"
    if k == "outbreak":
        return f"Outbreak of illness: {d.get('deaths', 0)} deaths across {d.get('cells', 0)} areas"
    if k in ("polity_founded", "polity_joined", "secession", "flight", "polity_ended", "seat_moved", "succession",
             "institution_founded", "institution_lost") or k.startswith("first_") and k.endswith(("chiefdom", "state")):
        pol = w.polities.get(d.get("polity")) if hasattr(w, "polities") else None
        pn = pol.name if pol else "a polity"
        if k == "polity_founded":
            return f"{pn.capitalize()} founded at {bn}" + (" (breaking away)" if d.get("why") == "secession" else "")
        if k == "polity_joined":
            return f"{bn} joined {pn}"
        if k == "flight":
            return f"{bn} left the rule of {pn} for open land"
        if k == "secession":
            return f"{bn} broke away from {pn}" + (f", taking {d.get('took') - 1} other settlements" if d.get("took", 1) > 1 else "")
        if k == "polity_ended":
            return f"{pn.capitalize()} came apart: {d.get('why')}"
        if k == "seat_moved":
            return f"The seat of {pn} moved to {bn}"
        if k == "succession":
            who = w.people.name(e["person"]) if e.get("person", -1) >= 0 else "a new leader"
            return f"{who} succeeded as leader of {pn}" + (" (contested)" if d.get("contested") else "")
        if k == "institution_founded":
            return f"{pn.capitalize()} established {d.get('institution')}"
        if k == "institution_lost":
            return f"{pn.capitalize()} could no longer keep {d.get('institution')}"
        return f"{pn.capitalize()}: the world's first {k[6:].replace('_', ' ')}"
    if k == "war":
        tb = w.bands.get(d.get("target"))
        tn = w.band_name(tb) if tb else "a neighbour"
        res = d.get("outcome", "")
        dead = d.get("attacker_deaths", 0) + d.get("defender_deaths", 0)
        return f"{bn} attacked {tn}: {res}" + (f", {dead} killed" if dead else "")
    if k == "conquest":
        pol = w.polities.get(d.get("polity"))
        return f"{bn} conquered by {pol.name if pol else 'a polity'}" + (" (its whole polity)" if d.get("whole_polity") else "")
    if k == "first_tending":
        return f"{bn} began tending wild {d.get('species')}: the first people anywhere to do so"
    if k == "first_cultivation":
        return f"{bn} began sowing and harvesting {d.get('species')}: the first cultivation anywhere"
    if k == "first_domestication":
        return f"{d.get('species', '').capitalize()} domesticated by {bn}: the first anywhere"
    if k == "first_farming_village":
        return (f"{bn} became the world's first farming village (living mainly from {d.get('species')}); "
                f"the observer's clock changes to historical time")
    if k in ("flood", "wildfire", "earthquake", "eruption"):
        what = {"flood": "Flood", "wildfire": "Wildfire", "earthquake": "Earthquake",
                "eruption": "Large volcanic eruption" if d.get("large") else "Volcanic eruption"}[k]
        return f"{what} ({d.get('deaths', 0)} deaths)"
    return k.replace("_", " ")


def chain(w, ref: dict, depth: int = 5) -> dict:
    node = describe(w, ref)
    node["causes"] = [chain(w, c, depth - 1) if depth > 0 and "note" not in c else describe(w, c)
                      for c in node.get("causes", [])]
    return node


def resolvable(w, ref: dict, depth: int = 6) -> bool:
    """True if every reference in the chain points at something that exists."""
    p = w.people
    try:
        if "event" in ref and not (0 <= int(ref["event"]) < len(w.events)):
            return False
        for key in ("death", "birth", "partnership"):
            if key in ref and not (0 <= int(ref[key]) < p.n):
                return False
        if "death" in ref and p.death[int(ref["death"])] < 0:
            return False
        node = describe(w, ref)
        if depth > 0:
            return all(resolvable(w, c, depth - 1) for c in node.get("causes", []))
        return True
    except (KeyError, IndexError, ValueError):
        return False
