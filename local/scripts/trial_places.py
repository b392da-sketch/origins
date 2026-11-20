# Place-name and writing trial (20 November 2026): OVERRIDE="NAME=value,..." python local/scripts/trial_places.py SAVE.zip YEARS
# Runs YEARS from a save and prints places named by kind, layers (new, kept, replaced), the share of kept names by
# feature size, sample names with their layers, writing (inventions, by stimulus, held, lost) and seat capacity.
import sys, os, time, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from origins import params as P
from origins import persist, engine, explain
from origins.sim import places, technology as T

for part in filter(None, os.environ.get("OVERRIDE", "").split(",")):
    k, v = part.split("=")
    setattr(P, k.strip(), type(getattr(P, k.strip()))(float(v)) if not isinstance(getattr(P, k.strip()), bool) else v == "1")
w = persist.load(sys.argv[1])
YEARS = int(sys.argv[2])
SEED_WRITING = int(os.environ.get("SEED_WRITING", "0"))
if SEED_WRITING:                       # give the seats of the largest polities working writing, to watch it keep or fall
    sz = w.band_sizes()
    tier = int(os.environ.get("SEED_TIER", "0"))      # only seats of polities at this tier or above
    seats = sorted((p.seat for p in w.polities.values() if p.ended < 0 and p.tier >= tier),
                   key=lambda s_: -sz[s_])[:SEED_WRITING]
    for s_ in seats:
        w.tech[s_, T.INDEX["tallies"]] = max(w.tech[s_, T.INDEX["tallies"]], 0.8)
        w.tech[s_, T.WRITING] = 0.6
    print("seeded writing at seats", seats, "specialists", [float(w.spec[s_]) for s_ in seats])
n0, tt = len(w.events), time.time()
for y in range(YEARS):
    engine.step(w, 4)
live = w.living_bands()
print("people", int(w.band_sizes()[[b.id for b in live]].sum()), "secs", round(time.time() - tt),
      "invariant failures", len(getattr(w, "invariant_failures", [])))
pl = getattr(w, "places", [])
print("places", len(pl), collections.Counter(p["kind"] for p in pl))
hows = collections.Counter(l[3] for p in pl for l in p["layers"])
print("layers", hows)
for lo, hi in ((0, .33), (.33, .66), (.66, 1.01)):
    ks = [l[3] for p in pl if lo <= p["size"] < hi for l in p["layers"] if l[3] != "new"]
    if ks:
        print(f"  size {lo}-{hi}: met by newcomers {len(ks)}, kept {ks.count('kept') / len(ks):.0%}")
for kind in places.KINDS:
    ks = [l[3] for p in pl if p["kind"] == kind for l in p["layers"] if l[3] != "new"]
    nl = [len(p["layers"]) for p in pl if p["kind"] == kind]
    if nl:
        print(f"  {kind}: {len(nl)} named, layers per place {np.mean(nl):.2f}, kept {ks.count('kept') / max(len(ks), 1):.0%} of {len(ks)}")
rng = np.random.default_rng(0)
multi = [i for i, p in enumerate(pl) if len(p["layers"]) >= 3]
for i in (rng.choice(multi, size=min(4, len(multi)), replace=False).tolist() if multi else []):
    print(" ", pl[i]["kind"], "size", round(pl[i]["size"], 2))
    for row in places.history(w, i):
        print("     ", row[:5])
ev = [i for i in range(n0, len(w.events)) if w.events[i]["kind"] == "place_named"]
smp = rng.choice(ev, size=min(20, len(ev)), replace=False) if ev else []
print("place events", len(ev), "resolvable", sum(explain.resolvable(w, {"event": int(i)}) for i in smp), "of", len(smp))
ew = collections.Counter((w.events[i]["kind"], "stimulus" in w.events[i]["data"]) for i in range(n0, len(w.events))
                         if w.events[i]["data"].get("technique") == "writing")
print("writing events", dict(ew))
print("writing lost", sum(1 for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_lost" and w.events[i]["data"].get("technique") == "writing"),
      "adopted", sum(1 for i in range(n0, len(w.events)) if w.events[i]["kind"] == "technique_adopted" and w.events[i]["data"].get("technique") == "writing"))
ids = np.array([b.id for b in live])
wr = (w.tech[ids, T.WRITING] > 0).sum(); ta = (w.tech[ids, T.INDEX["tallies"]] > 0).sum()
cells_ = np.array([b.cell for b in live])
prac = int(((w.tech[ids, T.WRITING] > 0) & T._possible(w, ids, cells_)[:, T.WRITING]).sum())
print("bands practising writing", prac, "scribes>=1", int((T._scribes(w)[ids] >= 1).sum()),
      "tier 2+ polities", sum(1 for p in w.polities.values() if p.ended < 0 and p.tier >= 2))
print("bands writing", int(wr), "with tallies", int(ta), "of", len(ids))
caps = [(p.id, T.capacity_multiplier(w, p.seat)) for p in w.polities.values() if p.ended < 0]
print("polities", len(caps), "capacity multipliers", sorted(round(c, 2) for _, c in caps)[-10:])
