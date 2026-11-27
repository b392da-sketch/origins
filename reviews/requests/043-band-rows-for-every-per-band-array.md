# Review request 043: band rows for every per-band array

**From:** Claude, 27 November 2026. **Branch:** `wip-bandrows` (on main `7093fe8`). **Not yet merged.** This carries through the third planet-4 step Ben approved on 22 November ("per-band rows only for bands holding people") to every remaining per-band array. Details and figures are in `docs/M4_BUILD_NOTES.md`, "Band rows for every per-band array".

## What pilot 3 showed

At year 6,348 the band ids passed 2,097,152. Every per-band array that still held a row for every id then doubled to 4,194,304 rows, with about 26,000 bands alive. The figures:
- **Loading peak:** 6.41 GB at stage 2, then 11.27 GB at stage 3.
- **Saves:** 1,212 MiB, then 1,527 MiB.
- **What the rows were:** 2.7 GiB of the year-6,348 arrays, almost all for bands that had ended.

## What changed

- **One slot map.** `w.band_rows` (`origins/rows.py`: `band_rows`, `new_rows`, `rows_from_dense`) holds 31 arrays as `SparseRows`:
  - customs and neutral traits;
  - skill, farming and the per-band land accounts;
  - specialists;
  - technology, its record, scribes and last year's practice;
  - goods, goods reached and trade receipts.

  A band gets its slot in `World.new_band`. It gives it up in `bands.release_rows`, called at the end of `end_band` and of each merge in `consolidate_groups`, after the existing folding and clearing.
- **A fast path for one band id** in `SparseRows._key`.
- **Whole-array uses rewritten to work by band id:**
  - `technology.practised_quality` now reuses one set of band rows (it allocated a dense bands × K float32 array each phase);
  - `trade.totals` and `check_end`;
  - `per_person`;
  - the farm share in `season_food`, `observe.end_tick`, and births and conception (`groups._farm_share_of_rows`);
  - `np.add.at` in the land accounts;
  - G4's census snapshot of `trade_in`.
- **Ended seats keep their rows.** The seat of a living polity that ends keeps its rows until the polity has a new seat or ends (`w.rows_kept`, swept at the end of each tick by `bands.sweep_rows`), because cultural distance and record-keeping read them until then.
- **Saves are schema 6.** They hold `band_rows_*`, plus `br_<name>` and `brfill_<name>` for each array. Older saves convert in `persist._load_band_rows`: living bands and kept seats keep their rows, and every other issued id is marked ended.
- **The digest** hashes each array by band id (`_band_rows_digest`).

## Evidence

- **Planet 3, year 9,910 save, 20 years in shadow mode:** the all-event hash is `f9eb76a6d77265d1`, as on main.
- **Planet 4, year 5,765 save, 10 years:** `fbc73ea0f432818d` on main and here. The peak is 3.60 GB on main and 2.68 GB here.
- **Planet 4, pilot 3's year-6,348 checkpoint:**
  - loading peak 4.10 GB (11.27 GB on the runner with the old code);
  - 39.9 s a year;
  - save 874 MiB, 4.6 GB peak.

  The old code cannot load it within this container's 8 GB, so there is no same-machine event-hash comparison at this year.
- **Tests:** `tests/test_rows.py::BandRows` covers:
  - every array is band rows on the shared map;
  - an ended band's rows raise;
  - a freed slot is refilled at each array's fill;
  - kept seats, through a save;
  - exact replay after a round trip;
  - a dense save gives the same rows by id and the same history.

  Five older tests were adapted to rows; the changes are in the diff.
- **The full suite:** 327 passed.

## Please check

1. **Reads of ended bands I have not found.** Every other read now raises, and only the two runs above and the suite exercise them. Look for paths these runs may not reach:
   - interventions;
   - the observatory and `explain`;
   - capture and conquest that ends a band;
   - the polity pass when a seat's `polity_of` is not its own polity (`_seat_of_living_polity` assumes it is);
   - gates G1 to G4 reading rows of ended bands.
2. **Exactness of the conversions:**
   - **customs:** the founders' row in place of band 0's;
   - **fills:** `forage_rr` at `P.FORAGE_RATE`, `farm_rr_real` at NaN, `-1` for cells and events;
   - **land accounts:** these were empty-length until first noted;
   - **goods totals:** summed by id without the ended rows (the conservation tolerance is 1e-6);
   - **dense saves:** ended seats taken from the polity JSON.
3. **Slot lifecycle and replay:**
   - free-list order across save and load;
   - `rows_kept` and `sweep_rows` timing within a tick;
   - arrays created mid-history (`trade_in`, `tech_scribes`, `tech_prev_*`, `_tech_eff_rows`) on the shared map;
   - registration left behind by `_set_rows` and `widen`.
4. **What remains at gate scale.** At year 6,353 the compact log is about 1.4 GB unpacked and the events 1.1 GB, both growing with history. Speed falls from 22 to 40–45 s a year between years 5,765 and 6,350, on main as well. A profile puts the time in partnerships, fission and merging, polities, conflict, traders and consolidation. Please rank what scales worse than living bands.

Same format as before (AGENTS.md).
