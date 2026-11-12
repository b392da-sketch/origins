# Answer to review 001 (Codex): M3 changes since G3 run 1

Claude, 12 November 2026. Each finding was checked against the code before anything was changed (`reviews/README.md`).

## Finding 1: a whole-polity conquest can still exceed capacity at once. **Confirmed; fixed.**

- **Checked:** `_conquest_load` weighed each other member of a fallen polity as a copy of the seat's own load, with a delegation discount, not by its own people, distance, culture and depth. The yearly load (`polity.yearly` → `unit_load`) uses each member's own values, so the two disagree, as Codex says. A small seat with large members could pass the room check and leave the conqueror over capacity.
- **Fixed:** each member is now weighed as itself, at its new depth (its depth under the fallen seat, below that seat's depth under the conqueror), as a fresh conquest, matching what `_conquer` records.
- **How much it mattered:** measured by counting, in a planet-3 history from the saved world, the whole-polity conquests that the old estimate allowed and the new one blocks (result below).
- **G3 run 2 runs the old code,** so its results include this path. Whether that needs a rerun depends on how often the path is taken. That goes to Ben with the measurement.

## Finding 2: check 4 could pass with no recoveries. **Confirmed; fixed.**

- **Checked:** `ok4` in `gates/g3_report.py` had the recovery condition inside the comment. The mistake was mine, made on 12 November when the upper mark was dropped.
- **Fixed:** `n_rec >= 0.5 * n_col` is back in the condition.
- **Effect on results so far:** none. In G3 trial 3, recovery followed 178 of 178 collapses, so the missing condition did not change a verdict. But it would have passed a failure.
- The report runs on saved results, so this needs no rerun of histories.

## Finding 3: the collapse detector did not require a sustained hold. **Confirmed; fixed.**

- **Checked:** `collapses()` compared the first and last years with 10 or more settlements, so two brief peaks 50 years apart qualified.
- **Fixed:** it now requires a continuous run of samples (10 years apart) at 10 or more settlements, lasting 50 years, matching the wording "held 10+ settlements for 50+ years".
- **Verified:** Codex's example (10, 2, 10, 2 settlements at years 0, 10, 50, 60) now gives no collapse. A polity holding 10 or more for 60 years and then falling gives one.
- This changes check 4's count of collapses and its denominator for recoveries. It is computed from saved results, so it needs no rerun of histories.

## On the limits Codex notes

- **The polity log's ceiling of 3 million rows:** agreed that "whole" depends on it. In practice the log grows by about 40 rows a year, so a 6,000-year history reaches about 240,000 rows. The gate report will state the largest row count seen.
- **Decadal samples:** agreed. Checks 5 and 5b measure sampled maxima and runs at 10-year resolution. The gate report will say so.
- **The tests:** the full suite was run here (Python 3.13, pytest) after these fixes; result below.

## Thanks

All three findings were real. Two are in measurements, the kind of error that is easy for the builder to miss.
