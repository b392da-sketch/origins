# Review 001: M3 changes since G3 run 1

Reviewed 12 November 2026 at `acc55a3`, range `804cf20^..acc55a3`. Ben explicitly requested this review in this session, superseding the request file's deferral. No application code, tests, specifications or gate inputs were changed.

## Findings

### 1. Whole-polity conquest can still exceed capacity immediately

- **Where:** `origins/sim/conflict.py::_conquest_load`, lines 351–354; `_room_for`; `origins/sim/polity.py::unit_load` and `yearly`.
- **What is wrong:** The conquest estimate treats every subordinate settlement as a copy of the defeated seat's load (with a possible delegation discount). The yearly calculation instead uses each settlement's own population, distance, culture and actual depth. A small defeated seat can therefore hide expensive members and let the winner conquer beyond its capacity despite the new room check.
- **Why it matters:** This preserves the conquest-overshoot mechanism that the post-run-1 changes were meant to remove, distorting polity size, overload, secession and the institutions comparison.
- **How sure:** Certain about the estimator mismatch and capacity bypass; frequency in gate histories is unmeasured.
- **How to see it:** Run `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python reviews/scratch/reproduce.py`. With no institutions, equal location and culture, a target seat of 15 people and one member of 1,500, the real estimator returns **1.2649** against capacity **3**. Summing `unit_load` for those same newly conquered members returns **6.9570**. The reproduction stubs distance and culture to zero to isolate the population error; it uses the actual load functions and parameters. `_conquer` transfers both settlements and marks both as fresh conquests.

### 2. Check 4 can pass with no recoveries

- **Where:** `gates/g3_report.py:158` (`ok4`).
- **What is wrong:** The recovery requirement `and n_rec >= 0.5 * n_col` is inside the comment. The executable condition checks collapse prevalence and an eligible collapse, but never the number of recoveries.
- **Why it matters:** A history set with zero recoveries can receive PASS for “Collapse happens, and recovery follows.” Ben's 11 November decision explicitly retained recovery after at least half of collapses; only the upper prevalence limit was dropped.
- **How sure:** Certain.
- **How to see it:** The reproduction evaluates the actual parsed `ok4` expression with `share=1`, `n_col=1`, and `n_rec=0`; it returns `True`. This is independent of the content of any particular G3 result files.

### 3. The collapse detector does not establish a sustained large polity

- **Where:** `gates/g3_report.py::collapses`, lines 44–46.
- **What is wrong:** The qualification for having held 10+ settlements for 50+ years is `max(big) - min(big) >= 50`. That includes time below ten settlements between isolated large samples. Even a polity recorded as large only twice can qualify.
- **Why it matters:** Check 4 can count repeated short-lived expansions as the collapse of an established large polity. Its collapse prevalence and recovery denominator therefore do not measure the stated qualification. This detector predates the requested changes but is in the explicitly requested measurement scope.
- **How sure:** Certain.
- **How to see it:** The reproduction supplies rows with settlement counts 10, 2, 10, 2 at years 0, 10, 50, 60 and populations 100, 20, 101, 20. `collapses` returns a collapse at year 50 despite no recorded continuous 50-year hold of ten settlements.

## Checked and sound

- The changed surplus, polity and conflict systems draw from their respective named random streams; `log_row` itself draws no random numbers.
- Checkpoint serialization now includes the complete retained surplus, war and polity logs and persists `log_strides`; the earlier save-time tail slices are removed.
- G3 finish samples whole polity identities and retains every identity ever logged with five or more settlements, preserving their retained time series.
- Check 9 uses the two correlations and Gini bounds chosen by Ben on 12 November; it reports the time trend without grading it.
- All 42 Python files under `origins/` and directly under `gates/` parse with Python 3.10 grammar. This is not a Python 3.10 runtime test.

## Limits and validation

Focused reproductions pass; their source and output are under `reviews/scratch/` and are not intended for commit. These are isolated accounting/measurement checks, not a gate run. The land-only calculation printed by that script is exploratory and is not submitted as a finding about physical wealth conservation.

The polity log still has a runtime ceiling of 3,000,000 rows (`polity.py:608` approximately); “whole histories” is conditional on not crossing that ceiling. No gate data demonstrating that ceiling was crossed was available here. The other logs retain samples across history, rather than every observation. Polity observations are decadal, so checks 5 and 5b measure sampled maxima and sampled runs, not exact annual extrema or durations.

Python 3.12.14 and NumPy 2.3.5 were already installed. Pytest is absent; the repository-supported unittest runner was used instead. The full discovery run was interrupted after about three minutes in its first, 1,500-year event-store test; it has no pass/fail verdict. The two selected existing tests (`test_m0.Replay.test_save_load_continue_is_exact` and `test_event_store.SampledLogsCoverTheWholeHistory.test_log_row`) both passed in 4.9 seconds. No gate-length histories were launched. No claim is made that current G3 run 2 passes or that every possible replay/cause-chain defect is excluded.

An additional short simulation check also passed (`reviews/scratch/short-event-replay.py`): 150-year histories with early event freezing enabled and disabled have equal digests and complete event records; a streamed checkpoint preserves full events, the sampled war log and thinning counters, and an eight-tick continuation matches exactly. This verifies the exercised path, not long-history coverage.

## Design questions for Ben

None required for these findings. The documented decisions on inequality, institutional tuning and early state formation were treated as requirements, not challenged as defects.
