"""Time a checkpoint: restore, then step 40 years, printing seconds per year for each 5 years. No profiler."""
import sys, time, resource
from pathlib import Path
from origins import engine, persist
from gates import g2
from gates.g4 import install_observers
install_observers()
cp, ws = Path(sys.argv[1]), int(sys.argv[2])
w = persist.from_bytes(cp.read_bytes(), g2.resume_planet(cp, ws))
print("restored", w.year, flush=True)
for k in range(8):
    t0 = time.time()
    engine.step(w, 20)
    print(f"years {w.year - 5}-{w.year}: {(time.time() - t0) / 5:.2f} s per year, living {len(w.living_bands()):,}, "
          f"peak {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
from origins import persist as p2
print("digest", p2.digest(w), flush=True)
