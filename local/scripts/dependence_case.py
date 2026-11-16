"""Dependence on imports, a small controlled case (Ben, 16 November 2026; Codex review 018).

A real founding band is moved to a cell with copper, clay and forest within reach but no tin, given enough
specialists to keep every technique (so loss of knowledge cannot confound the result), and given the bronze
chain (pottery, kilns, copper-working, smelting, bronze) and imported tin. Two arms from the same start: in one the
tin is topped up every year (supply continues), in the other it is not (supply cut). Each year runs the real
technology and trade passes. Prints, per year, tin held per person, whether bronze is practised, its remembered
quality, and any cut-off or loss events with their causes.

    python local/scripts/dependence_case.py [YEARS]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np

from origins import params as P
from origins.state import World
from origins.worldgen import generate
from origins.sim import technology as T, trade

CHAIN = ("pottery", "kilns", "copper_working", "smelting", "bronze")
START_TIN = 0.008                      # per person: 1.6 times MATERIAL_HELD
SPECIALISTS = 100.0                    # enough skilled practitioners to keep the whole chain (bronze keeps at 80)


def setup():
    w = World.new(1, 1, generate(1))
    mats = T._cell_materials(w)
    M = T.MATERIALS
    cell = next(c for c in range(w.planet.n) if w.planet.land[c] and mats[c, M.index("copper")]
                and mats[c, M.index("clay")] and mats[c, M.index("forest")] and not mats[c, M.index("tin")])
    b = w.living_bands()[0]
    b.cell = cell
    w.bands_changed()
    for k in CHAIN:
        w.tech[b.id, T.INDEX[k]] = 0.9
    w.spec[b.id] = SPECIALISTS            # so that losing knowledge cannot confound the supply (Codex review 018)
    return w, b


def run(years, supply):
    w, b = setup()
    n0 = len(w.events)
    rows = []
    for y in range(years):
        n = float(w.band_sizes()[b.id])
        if supply:
            w.goods[b.id, trade.GI["tin"]] = max(w.goods[b.id, trade.GI["tin"]], START_TIN * n)
        elif y == 0:
            w.goods[b.id, trade.GI["tin"]] = START_TIN * n
        w.spec[b.id] = SPECIALISTS
        T.yearly(w)
        trade.yearly(w)
        T.refresh(w)
        q = T.practised_quality(w)[b.id, T.INDEX["bronze"]]
        rows.append((y + 1, w.goods[b.id, trade.GI["tin"]] / max(n, 1.0), bool(q > 0), float(w.tech[b.id, T.INDEX["bronze"]])))
        w.t += P.TICKS_PER_YEAR
    ev = [w.events[i] for i in range(n0, len(w.events))
          if w.events[i]["kind"] in ("technique_cut_off", "technique_lost") and w.events[i]["band"] == b.id]
    return rows, ev


if __name__ == "__main__":
    years = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    for supply in (True, False):
        rows, ev = run(years, supply)
        print("supply continues" if supply else "supply cut", "(MATERIAL_HELD", P.MATERIAL_HELD, "per person)")
        for y, tin, prac, lvl in rows:
            print(f"  year {y:3d}: tin per person {tin:.4f}  bronze practised {prac!s:5}  remembered {lvl:.3f}")
        for e in ev:
            print("  ", e["kind"], e["data"].get("technique"), "-", e["causes"][-1].get("note", ""))
