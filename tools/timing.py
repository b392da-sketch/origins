"""Restore a checkpoint, step 40 years, print speed and memory every 5 years, then the digest and a hash of every
new event. With the compact log present, its shadow mode is on, so events compare with older code."""
import sys, time, resource, json, hashlib


def rss_now():
    for line in open("/proc/self/status"):
        if line.startswith("VmRSS"):
            return int(line.split()[1]) / 1e6
    return 0.0
from pathlib import Path
try:
    from origins.sim import minorlog
    minorlog.SHADOW = "--shadow" in sys.argv
except ImportError:
    pass
from origins import engine, persist
from gates import g2
from gates.g4 import install_observers
install_observers()
cp, ws = Path(sys.argv[1]), int(sys.argv[2])
w = persist.from_bytes(cp.read_bytes(), g2.resume_planet(cp, ws))
print("restored", w.year, f"peak {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
n0 = len(w.events)
for k in range(8):
    t0 = time.time()
    engine.step(w, 20)
    print(f"years {w.year - 5}-{w.year}: {(time.time() - t0) / 5:.2f} s per year, living {len(w.living_bands()):,}, "
          f"peak {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB, now {rss_now():.2f} GB", flush=True)
import gc
gc.collect()
print(f"in use after stepping: {rss_now():.2f} GB", flush=True)
h = hashlib.sha1()
for i in range(n0, len(w.events)):
    h.update(json.dumps(w.events[i], sort_keys=True, default=str).encode())
print("events", len(w.events) - n0, "hash", h.hexdigest()[:16], "population", w.population(),
      "rng", hashlib.sha1(json.dumps({k: g.bit_generator.state for k, g in w.rng.items()}, sort_keys=True,
                                     default=str).encode()).hexdigest()[:16], flush=True)
