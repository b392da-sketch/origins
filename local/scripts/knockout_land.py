# Land knock-out (19 November 2026, after Codex review 020).
#   LAND=1|0 OVERRIDE="NAME=value,NAME=value" python local/scripts/knockout_land.py SAVE.zip YEARS
# Loads SAVE.zip, applies the switches, runs YEARS years and prints people, land state, land events, moves and
# hunger deaths traced to the land. Every switch used is printed first, so a row can be reproduced exactly.
# The arms reported in docs/M4_BUILD_NOTES.md all start from snap_p3s1_8500_plus1200.zip (planet 3, seed 1,
# year 9,700), kept outside the repository (local saves).
import sys, os, time, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from origins import params as P
from origins import persist, engine, explain

P.LAND = os.environ.get("LAND", "1") == "1"
over = {}
for part in filter(None, os.environ.get("OVERRIDE", "").split(",")):
    k, v = part.split("=")
    over[k.strip()] = float(v)
    setattr(P, k.strip(), float(v))
print("save", os.path.basename(sys.argv[1]), "years", sys.argv[2], "LAND", P.LAND, "overrides", over, flush=True)

w = persist.load(sys.argv[1])
YEARS = int(sys.argv[2])
n0 = len(w.events)
p0 = w.people.n
g0 = w.counts.get("group_hunger_deaths", 0)
w._c0 = dict(w.counts)
t0 = time.time()
for y in range(YEARS):
    engine.step(w, 4)
    if y in (0, 49, 149):
        print("after", y + 1, "years", round(time.time() - t0), "s", flush=True)
fails = getattr(w, "invariant_failures", [])
live = w.living_bands()
people = int(w.band_sizes()[[b.id for b in live]].sum()) if live else 0
print("people at end", people, "secs", round(time.time() - t0), "invariant failures", len(fails), fails[:3])
ev = collections.Counter(w.events[i]["kind"] for i in range(n0, len(w.events)))
print("events", {k: ev[k] for k in sorted(ev) if k.startswith(("land_", "technique_", "group_hunger"))})
nf = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_no_fuel"]
print("no-fuel lapses by technique", dict(collections.Counter(e["data"]["technique"] for e in nf)))
if P.LAND:
    cells = np.unique([b.cell for b in live])          # each lived-in cell once (Codex review 021)
    from origins.sim import land as _land
    fm = _land.forest_max(w)
    fc = cells[fm[cells] > 0]
    print("lived-in cells: game", round(float(w.game[cells].mean()), 3), "fast game", round(float(w.game_fast[cells].mean()), 3),
          "forest (forest cells only)", round(float(w.forest[fc].mean()), 3) if len(fc) else None,
          "wood within reach below FUEL_MIN", round(float((_land.forest_near(w)[cells] < P.FUEL_MIN).mean()), 3),
          "fertility", round(float(w.fertility[cells].mean()), 3), "salt", round(float(w.salt[cells].mean()), 3),
          "fallow", round(float(w.fallow[cells].mean()), 3))
    farms = np.unique([b.cell for b in live if w.farm_share[b.id] > 0.2])
    if len(farms):
        print("farmed cells: fertility", round(float(w.fertility[farms].mean()), 3), "fallow", round(float(w.fallow[farms].mean()), 3))
p = w.people
dead = np.nonzero((p.death[:p.n] >= 0) & (np.arange(p.n) >= 0))[0]
recent = dead[(p.death[dead] >= w.t - YEARS * P.TICKS_PER_YEAR)]
from origins.sim.demography import C
hung = recent[p.cause[recent] == C["hunger"]]
print("hunger deaths (individuals)", len(hung), "(cause hunger) linked to a land_hunger event", int((p.death_land[hung] >= 0).sum()),
      "; grouped hunger deaths in the trial", w.counts.get("group_hunger_deaths", 0) - g0)
c0 = getattr(w, "_c0", {})
cnt = {k: w.counts.get(k, 0) - c0.get(k, 0) for k in ("land_exp_short", "land_exp_linked", "land_exp_wild_only",
                                                       "land_exp_crop_only", "land_exp_both", "land_exp_short_sum",
                                                       "land_exp_linked_sum")}
if cnt["land_exp_short"]:   # every band-season of exposure (Codex review 023, finding 5); exposure, not cause
    print("band-seasons short of food", cnt["land_exp_short"], "with a linked land loss", cnt["land_exp_linked"],
          f"({cnt['land_exp_linked'] / cnt['land_exp_short']:.1%}); wild only", cnt["land_exp_wild_only"],
          "crops only", cnt["land_exp_crop_only"], "both", cnt["land_exp_both"],
          f"; linked loss (capped at the lack) {cnt['land_exp_linked_sum'] / max(cnt['land_exp_short_sum'], 1e-9):.1%}"
          " of all food lacked (crop loss as the harvest's loss spread over the year)")
lh = [w.events[i]["data"] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "land_hunger"]
if lh:   # the events made where deaths were recorded: a selected sample
    print("land_hunger events (at recorded deaths)", len(lh), "; with unlinked losses", sum(d.get("unlinked", 0) > 0 for d in lh))
moves = [i for i in range(n0, len(w.events)) if w.events[i]["kind"] == "land_move"]
rng = np.random.default_rng(0)
sample = rng.choice(moves, size=min(20, len(moves)), replace=False) if moves else []
print("land moves", len(moves), "sampled chains resolvable", sum(explain.resolvable(w, {"event": int(i)}) for i in sample), "of", len(sample))
tag = "land%d" % int(P.LAND) + "".join(f"_{k}{v:g}" for k, v in over.items())
persist.save(w, sys.argv[1].replace(".zip", f"_{tag}_{YEARS}.zip"))
