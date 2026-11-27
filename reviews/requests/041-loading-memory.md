# Review request 041: loading large saves

**From:** Claude, 26 November 2026. **Branch:** `wip-restore` (on main `9264a97`). **Not yet merged.** Ben's decision (26 November 2026): steps 1–4 below.

## Background

G4a pilot 2 (gate run 44973846305, planet 4 seed 1, code from main `9264a97`) ran out of memory loading its stage-4 checkpoint:

| Stage | Loaded from year | Checkpoint | Load time | Memory peak |
|---|---|---|---|---|
| 2 | 6,398 | 1,099 MiB | 78 s | 13.0 GB |
| 3 | 7,191 | 1,522 MiB | 126 s | 15.45 GB |
| 4 | 7,681 | 1,794 MiB | 186 s | 15.54 GB |
| 5 | 8,120 | 2,038 MiB | — | killed (the runner's 16 GB) |

While stepping, a stage stayed far lower: 3.9 GB in stage 1 at year 5,500. The history must reach about year 11,250.

## What changed

1. **`persist.from_file(path_or_file, planet)`.** It reads a save from disk as it parses. It unpacks `arrays.npz` to a temporary file and reads the arrays one by one, instead of holding the save's bytes and the npz's bytes beside the arrays. `from_bytes` now calls it. Every gate worker (g0 slice, g1–g4) loads checkpoints through it.
2. **No second copies while building the world.** Arrays taken from the save are used as read (`np.asarray`), not copied again with `np.array`. Nothing else holds them.
3. **Memory traced at each part of loading and saving,** when `ORIGINS_MEM_TRACE` is set; the gate workflow now sets it:
   - on loading: memory in use and peak after meta.json, the arrays, the events, the bands, the per-band arrays, technology, trade, disease and places, and the finished world;
   - on saving: the largest parts of `meta.json` and the largest arrays.

   This is a measuring aid; it changes nothing else.
4. **Checkpoints are kept 14 days,** not 2, so a pilot that fails can be continued.

## Evidence

- **Same world:** on the planet-3 save at year 9,910, `from_file` and `from_bytes` give the same digest (`d6db1c86f6441e307834`). A world loaded either way steps on identically (`tests/test_rows.py::LoadFromFile`).
- **Local peak while loading that save:** 2.75 GB before, 2.41 GB now, measured with the trace:

  | After | Memory in use |
  |---|---|
  | meta.json | 0.37 GB |
  | arrays | 1.58 GB |
  | events | 1.83 GB |
  | finished world | 2.41 GB |

- **Pilot 3** (gate run 45794080188, the same history on this branch) reports the same breakdown at planet-4 scale, from its stage-2 load onwards. Its figures go to the build notes.

## Please check

1. **`from_file`:** is it the same world as `from_bytes` for every older schema and save? Can `np.asarray` in place of `np.array` leave two attributes sharing one array that either changes?
2. **Memory at planet-4 scale:** from the code, what is likely to fill memory while a 2 GB checkpoint at year 8,000 loads? At that point there are 6.8 million events, 4.2 million band ids allocated, 1.7 million disease-log rows, and the polity log up to 3 million rows. What would you change first, keeping the history exact?
3. **The workflow:** is anything wrong with the 14-day checkpoints (storage) or the trace (log size)?

Same format as before (AGENTS.md).
