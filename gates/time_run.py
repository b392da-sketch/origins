"""Time one long history phase by phase (speed pass). Usage: python gates/time_run.py SEED YEARS"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from origins import engine  # noqa: E402
from origins.state import World  # noqa: E402

seed, years = int(sys.argv[1]), int(sys.argv[2])
w = World.new(seed, 1)
tot = {}
t0 = time.time()
for y in range(years):
    for _ in range(4):
        from origins.sim import observe
        observe.begin_tick(w)
        for name, fn in engine.PHASES:
            a = time.perf_counter()
            fn(w)
            tot[name] = tot.get(name, 0.0) + time.perf_counter() - a
        observe.end_tick(w)
        w.t += 1
    if y % 500 == 499:
        print(y + 1, round(time.time() - t0), w.population(), len(w.living_bands()),
              sum(l.alive for l in w.languages.values()), flush=True)
print(json.dumps({k: round(v, 1) for k, v in sorted(tot.items(), key=lambda kv: -kv[1])}))
