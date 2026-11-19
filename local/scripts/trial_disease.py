# Disease trial (20 November 2026): DISEASE=1|0 OVERRIDE="NAME=value,..." python local/scripts/trial_disease.py SAVE.zip YEARS
# Runs YEARS from a save and prints people, the share of deaths from disease, the diseases that appeared (host,
# deaths per case, years circulating, peak cells), and the age of individuals who died of disease, early and late.
import sys, os, time, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from origins import params as P
from origins import persist, engine, explain
from origins.state import C

P.DISEASE = os.environ.get("DISEASE", "1") == "1"
over = {}
for part in filter(None, os.environ.get("OVERRIDE", "").split(",")):
    k, v = part.split("=")
    over[k.strip()] = float(v)
    setattr(P, k.strip(), float(v))
print("save", os.path.basename(sys.argv[1]), "years", sys.argv[2], "DISEASE", P.DISEASE, "overrides", over, flush=True)
w = persist.load(sys.argv[1])
YEARS = int(sys.argv[2])
n0, t0, tt = len(w.events), w.t, time.time()
d0 = w.accum["deaths_by_cause"].copy()
active_years = collections.Counter()
peak = collections.Counter()
for y in range(YEARS):
    engine.step(w, 4)
    if P.DISEASE and getattr(w, "diseases", None):
        for d in range(len(w.diseases)):
            k = int(w.dz_active[:, d].sum())
            if k:
                active_years[d] += 1
                peak[d] = max(peak[d], k)
    if y in (0, 49, 149):
        print("after", y + 1, "years", round(time.time() - tt), "s", flush=True)
live = w.living_bands()
people = int(w.band_sizes()[[b.id for b in live]].sum()) if live else 0
dd = w.accum["deaths_by_cause"] - d0
code = C["disease outbreak"]
print("people at end", people, "secs", round(time.time() - tt), "invariant failures", len(getattr(w, "invariant_failures", [])))
print("deaths", int(dd.sum()), "from disease outbreaks", int(dd[code]), f"({dd[code] / max(dd.sum(), 1):.1%})",
      "from hunger", f"{dd[C['hunger']] / max(dd.sum(), 1):.1%}")
if P.DISEASE:
    print("diseases", len(w.diseases))
    for d, dz in enumerate(w.diseases):
        print(f"  {dz['name']}: host {dz['host']}, year {dz['year']}, attack {dz['attack']}, deaths per adult case "
              f"{dz['cfr']}, k {dz['k']}, lasting {dz['lasting']}, hunger {dz['hunger']}; circulating "
              f"{active_years[d]} years, peak {peak[d]} cells, now {int(w.dz_active[:, d].sum())}")
p = w.people
dead = np.nonzero((p.death[:p.n] >= t0) & (p.cause[:p.n] == code))[0]
if len(dead):
    age = (p.death[dead] - p.birth[dead]) / P.TICKS_PER_YEAR
    half = t0 + (w.t - t0) // 2
    for lab, m in (("first half", p.death[dead] < half), ("second half", p.death[dead] >= half)):
        a = age[m]
        if len(a):
            print(f"  individuals dying of disease, {lab}: {len(a)}, under 15 {np.mean(a < 15):.0%}, median age {np.median(a):.1f}")
    rng = np.random.default_rng(0)
    smp = rng.choice(dead, size=min(20, len(dead)), replace=False)
    print("  sampled death chains resolvable", sum(explain.resolvable(w, {"death": int(i)}) for i in smp), "of", len(smp))
ev = collections.Counter(w.events[i]["kind"] for i in range(n0, len(w.events)))
print("events", {k: ev[k] for k in ("new_disease", "outbreak")})
tag = "dz%d" % int(P.DISEASE) + "".join(f"_{k}{v:g}" for k, v in over.items())
persist.save(w, sys.argv[1].replace(".zip", f"_{tag}_{YEARS}.zip"))
