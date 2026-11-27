# Review request 044: speed before the gate

**From:** Claude, 28 November 2026. **Branch:** `wip-speed`. **Not yet merged.** Ben chose speed work before G4a on 28 November 2026 (`docs/G4A_GATE_PLAN.md`). Details are in `docs/M4_BUILD_NOTES.md`, "Speed before the gate".

## What changed

Every change is meant to compute the same values in the same order. The exception is where a different order cannot change the result: sums of whole-number band sizes, and first-match lookups.

- **`trade.prestige_factor`:** polity members' sizes come from the tick's snapshot of bands holding anyone, selected by a fresh `polity_of` read, in place of an `np.nonzero` over every issued id.
- **`polity.members_of`:** the living bands' ids, cached with the list.
- **`rows.SparseRows`:** a fast path for an `int` or `np.int64` key, for both reading and writing.
- **The gift loop in `trade.partnerships_yearly`:** rows by slot, with `move_good` written out. Partner slots are found with `list.index`.
- **`traders._carry`:** the seats' rows by slot.
- **`farming.quality`:** a cache keyed by the row's bytes. The results are read-only; `_quality` is the computation.
- **Herding and group keys:**
  - `pastoral.herders_now` and `bands.group_keys` compute herding and group keys for many bands at once and fill the same per-tick cache;
  - `pastoral.move` uses `sizes_of` in place of `band_sizes`, and computes each herder's own-cell and neighbouring-cell values in batches.
- **`conflict.yearly`:**
  - sides are cached until a war is fought;
  - a cell already scanned for targets is skipped by later members of the same side.
- **Smaller changes:**
  - `trade.goods_materials` reads sizes once for all goods;
  - `down_the_line`'s first-arrival loop runs only over the pairs flowing into a new arrival;
  - `technology._settled` and `band_quality` use direct lookups.

## Evidence

The all-event hash in shadow mode, against main (`dbbb14c`):

| Save | Run | Hash | Speed |
|---|---|---|---|
| Planet 3, year 9,910 | 20 years | `f9eb76a6d77265d1` | 84 → 60 s for the run |
| Planet 4, year 5,765 | 10 years | `fbc73ea0f432818d` | 22.0 → 12.0 s a year |
| Planet 4, year 6,631 (pilot 4's stage-3 checkpoint) | 5 years | `c3e0b565819d60f0` | 59.7 → 34.1 s a year |

The event counts and populations are unchanged in each run. The full suite result is in the commit message.

## Please check

1. **Exactness**, especially:
   - **the gift loop:** the order of reads and writes per good, the cases of a zero or negative amount, and the ledger additions;
   - **the herder and group-key batches:** that each answer and cache entry equals `is_herder` and `group_key`, including bands below half farming;
   - **conflict:** that nothing but `_fight` changes a side inside the pass, and that skipping an already-scanned cell cannot change `seen` or its insertion order;
   - **prestige:** whether a member holding nobody, or a size that is not a whole number, could make the sum differ.
2. **Caches that could go stale:**
   - `_living_ids`, keyed on the list's identity and length;
   - the quality cache, module-wide and shared between worlds in one process;
   - the slot views held across loops: `gdata`, `rb` and `ro`, and partner rows, if anything inside could grow or replace the arrays.
3. **What else is worth doing exactly at gate scale,** ranked. The phase timings are in the build notes.
