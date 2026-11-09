"""One tick (one season) in a fixed order of phases. See M0 specification section 9."""
from __future__ import annotations

from . import interventions
from . import params as P
from .sim import bands, climate, customs, demography, farming, foraging, groups, conflict, hazards, language, observe, polity, surplus

PHASES = [
    ("interventions", interventions.restore_due),
    ("climate", lambda w: climate.yearly(w) if w.quarter == 0 and w.t > 0 else None),
    ("regrowth", climate.regrow),
    ("movement", foraging.move),
    ("foraging_and_eating", foraging.forage_and_eat),
    ("ageing", lambda w: groups.age_one_year(w) if w.quarter == 0 and w.t > 0 else None),
    ("deaths", demography.deaths),
    ("group_deaths", groups.deaths),
    ("partnerships", demography.partnerships),
    ("births", demography.births),
    ("group_births", groups.births),
    ("fission_merge", bands.fission_and_merge),
    ("discovery", bands.reveal),
    ("fold", lambda w: bands.fold_distant(w) if w.quarter == 3 else None),
    ("compact", lambda w: groups.compact(w) if w.quarter == 3 and w.year % 50 == 0 else None),
    ("hazards", lambda w: hazards.yearly(w) if w.quarter == 1 else None),
    ("farming", lambda w: farming.yearly(w) if w.quarter == 3 else None),
    ("surplus", lambda w: surplus.yearly(w) if w.quarter == P.HARVEST_QUARTER else None),
    ("polity", lambda w: polity.yearly(w) if w.quarter == P.HARVEST_QUARTER else None),
    ("conflict", lambda w: conflict.yearly(w) if w.quarter == P.HARVEST_QUARTER else None),
    ("customs", lambda w: customs.yearly(w) if w.quarter == 1 else None),
    ("language", lambda w: language.check(w)
     if w.quarter == 2 and w.year % P.LANGUAGE_CHECK_YEARS == 0 and w.t > 0 else None),
]


def step(w, ticks: int = 1):
    for _ in range(ticks):
        observe.begin_tick(w)
        for _name, fn in PHASES:
            fn(w)
        observe.end_tick(w)
        w.t += 1
        if not w.living_bands():
            if not w.events or w.events[-1]["kind"] != "extinction":
                w.event("extinction", causes=[{"note": "no living bands remain"}])
            break


def extinct(w) -> bool:
    return not w.living_bands()
