# Curation knock-out (16 November 2026): CURATION=1|0 python local/scripts/knockout_curation.py SAVE.zip YEARS
# Runs YEARS from a save with curation on or off and prints routes, arrivals, rulers' stores and fine stone by distance.
import sys, time, collections
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
import numpy as np
from origins import persist, engine
from origins.sim import trade, traders
import os
from origins import params as _P
_P.CURATION = os.environ.get("CURATION", "1") == "1"
w = persist.load(sys.argv[1]); YEARS = int(sys.argv[2])
T = [0.0]; orig = traders.yearly
def timed(w_, live):
    t = time.time(); orig(w_, live); T[0] += time.time() - t
traders.yearly = timed
from origins.sim import trade as _t
n0 = len(w.events); t0 = time.time()
for y in range(YEARS):
    engine.step(w, 4)
    if y in (0, 9, 49):
        print("after", y + 1, "years: total", round(time.time() - t0), "s, traders", round(T[0]), "s", flush=True)
fails = getattr(w, "invariant_failures", [])
print("years", YEARS, "secs", round(time.time() - t0), "traders secs", round(T[0]), "fails", len(fails), fails[:3])
ev = collections.Counter(w.events[i]["kind"] for i in range(n0, len(w.events)))
print({k: ev[k] for k in ("trade_route_opened", "toll_evaded", "good_arrived")})
arr = [w.events[i] for i in range(n0, len(w.events)) if w.events[i]["kind"] == "good_arrived"]
print("arrivals by trader", sum(1 for e in arr if e["data"].get("route") == "trader"))
rl = w.route_log
if rl:
    a = np.array([r[3:] for r in rl], float)
    print("route rows", len(rl), "moved", a[:, 0].sum().round(1), "lost", a[:, 1].sum().round(2), "tolls", a[:, 2].sum().round(2),
          "levies", a[:, 3].sum().round(2), "kept", a[:, 4].sum().round(2), "paid", int(a[:, 5].sum()), "evaded", int(a[:, 6].sum()))
print("treasury total", traders.totals(w).round(2).tolist())
persist.save(w, sys.argv[1].replace(".zip", f"_cur{os.environ.get('CURATION','1')}_{YEARS}.zip"))
pl = w.planet; nb = pl.grid.neighbours
live = w.living_bands()
ids = np.array([b.id for b in live]); cells = np.array([b.cell for b in live])
sizes = np.maximum(w.band_sizes()[ids].astype(float), 1)
gi = trade.GI["fine_stone"]
src = np.nonzero(trade._deposit(w, np.arange(pl.grid.n), trade.SOURCES["fine_stone"][0]))[0]
dist = -np.ones(pl.grid.n, int); dist[src] = 0; front = list(src); d = 0
while front and d < 14:
    d += 1; nxt = []
    for c in front:
        for x in nb[c]:
            if x >= 0 and dist[x] < 0:
                dist[x] = d; nxt.append(x)
    front = nxt
dd = dist[cells]; per = w.goods[ids, gi] / sizes
print("fine stone to 14 cells", [float(f"{per[dd == k].mean():.2g}") if (dd == k).any() else None for k in range(15)])
