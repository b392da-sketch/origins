"""Preliminary benchmark (Ben, 14 November 2026): time one history phase by phase, by era.

Usage: python local/scripts/bench.py PLANET SEED YEARS OUT_JSON [SAVE_AT_YEAR SAVE_PATH]

Runs a fresh world for YEARS simulated years. Every 500 years it records the seconds spent in each phase, the
population, living bands and peak memory, and prints a progress line. Optionally saves the world at a given year
(to reuse as a benchmark start; keep saves out of git). Writes the timings to OUT_JSON.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from origins import engine, persist  # noqa: E402
from origins.sim import observe  # noqa: E402
from origins.state import World  # noqa: E402
from gates.g0 import _planet  # noqa: E402


def peak_mb():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:                       # Windows
        try:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            c = PMC()
            c.cb = ctypes.sizeof(PMC)
            h = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb)
            return c.PeakWorkingSetSize / 1e6
        except Exception:
            return -1.0


def main():
    planet, seed, years, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
    save_at = int(sys.argv[5]) if len(sys.argv) > 5 else None
    save_path = Path(sys.argv[6]) if len(sys.argv) > 6 else None
    out.parent.mkdir(parents=True, exist_ok=True)
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
    w = World.new(planet, seed, _planet(planet))
    rows, block, t_block = [], {}, time.time()
    start = time.time()
    for y in range(1, years + 1):
        for _ in range(4):
            observe.begin_tick(w)
            for name, fn in engine.PHASES:
                w._tech_eff = None
                a = time.perf_counter()
                fn(w)
                block[name] = block.get(name, 0.0) + time.perf_counter() - a
            observe.end_tick(w)
            w.t += 1
        if save_at is not None and y == save_at and save_path is not None:
            persist.save(w, save_path)
            print(f"saved world at year {y} to {save_path}", flush=True)
        if y % 500 == 0 or y == years:
            secs = time.time() - t_block
            fv = w.first_village
            row = {"to_year": y, "seconds": round(secs, 1), "seconds_per_year": round(secs / 500, 3),
                   "population": w.population(), "bands": len(w.living_bands()),
                   "polities": sum(1 for p in getattr(w, "polities", {}).values() if p.alive),
                   "first_village_year": w.events[fv]["data"]["year"] if fv is not None else None,
                   "peak_memory_mb": round(peak_mb(), 1),
                   "phases": {k: round(v, 1) for k, v in sorted(block.items(), key=lambda kv: -kv[1])}}
            rows.append(row)
            print(json.dumps({k: row[k] for k in row if k != "phases"}), flush=True)
            block, t_block = {}, time.time()
            out.write_text(json.dumps({"planet": planet, "seed": seed, "total_seconds": round(time.time() - start, 1),
                                       "rows": rows}, indent=1))
            if engine.extinct(w):
                break


if __name__ == "__main__":
    main()
