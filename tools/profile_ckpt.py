"""Profile a gate checkpoint: restore it, step some years, and report time by phase and by function, and the size of
the per-band state. A measuring tool (G4a pilot, 21 November 2026); it changes nothing in the simulation."""
import cProfile
import io
import pstats
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path


def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def main(cp: Path, ws: int, years: int):
    from gates import g2
    from origins import engine
    from origins import persist
    from gates.g4 import install_observers
    install_observers()
    t0 = time.time()
    w = persist.from_bytes(cp.read_bytes(), g2.resume_planet(cp, ws))
    print(f"restored year {w.year} in {time.time() - t0:.0f} s, peak {rss():.2f} GB; next_band {w.next_band:,}, "
          f"living {len(w.living_bands()):,}, events {len(w.events):,}", flush=True)
    t0 = time.time()
    engine.step(w, 40)                       # ten years without the profiler, for the true speed
    print(f"10 years without the profiler: {(time.time() - t0) / 10:.2f} s per year", flush=True)
    phase = defaultdict(float)
    pr = cProfile.Profile()
    from origins.sim import observe
    t0 = time.time()
    pr.enable()
    for _ in range(years * 4):
        observe.begin_tick(w)
        for name, fn in engine.PHASES:
            w._tech_eff = None
            s = time.perf_counter()
            fn(w)
            phase[name] += time.perf_counter() - s
        s = time.perf_counter()
        observe.end_tick(w)
        phase["observe.end_tick"] += time.perf_counter() - s
        w.t += 1
    pr.disable()
    el = time.time() - t0
    print(f"\n{years} years in {el:.0f} s ({el / years:.1f} s per year), peak {rss():.2f} GB\n")
    print("time by phase (s per year):")
    for k, v in sorted(phase.items(), key=lambda kv: -kv[1]):
        print(f"  {k:30s}{v / years:8.2f}")
    for key in ("cumulative", "tottime"):
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats(key).print_stats(45)
        print(f"\n--- by {key} ---\n" + s.getvalue()[-9000:])


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
