# Review 002: fixes for review 001

12 November 2026. Reviewed fix commit `666c095` and Claude's response to review 001, at checkout `707a5f6`. Read `AGENTS.md`; the design, specification and gate decisions from review 001 remain unchanged. Only review files were written.

Finding 001/1 is **partly fixed**: the original population mismatch is corrected, but the joining estimate still disagrees with the yearly calculation for an attacker with an intermediate ancestor. Findings 001/2 and 001/3 are fixed within the stated sampled-log measurement.

## Findings

### 1. The attacker's ancestry is truncated before computing conquered members' depths

- **Where:** `origins/sim/conflict.py::_conquest_load`, line 345, feeding the new per-member calculation at lines 357–362; `origins/sim/polity.py::_depths`.
- **What is wrong:** `_depths(w, [b.id], probe.seat)` supplies only the attacker, so `_depths` cannot follow an intermediate leader: it treats any parent absent from that supplied set as the seat. An attacker two or more edges below the seat is therefore treated as one edge below it. The corrected per-member sum inherits this wrong offset, potentially discounting settlements whose actual new depth exceeds `max_depth`.
- **Why it matters:** The room check can still permit a conquest that exceeds capacity under the yearly calculation. This is a remaining defect in the requested estimator/yearly agreement, not a regression introduced by this patch: the bad offset already existed, and the fix now uses it for each conquered descendant as well as the target seat.
- **How sure:** Certain. The estimator was compared against the actual `_conquer` membership transfer followed by `_depths` on the full resulting membership and a sum of `unit_load`, using unchanged institutions, populations and geometry inputs.
- **How to see it:** Construct winner ancestry `0 -> 1 -> 2 -> 3` and fallen ancestry `4 -> 5 -> 6 -> 7`, where arrows point from parent to child. Let settlement 2 attack fallen seat 4. With all five winner institutions enabled, `max_depth` is 4. The estimate assigns depths 2, 3, 4, 5 to settlements 4–7; after `_conquer`, their actual depths are 3, 4, 5, 6. Settlement 6 consequently gets a delegation discount in the estimate that it does not get yearly.

A minimal demonstration of the underlying depth error (no world generation needed):

```python
from types import SimpleNamespace
import numpy as np
from origins.sim.polity import _depths
w = SimpleNamespace(polity_via=np.array([-1, 0, 1, 2, -1, 4, 5, 6]))
assert _depths(w, [2], 0)[2] == 1  # offset used by the estimator
assert _depths(w, [0, 1, 2, 3], 0)[2] == 2  # actual attacker depth
```

The numerical reproduction uses populations `[150, 200, 300, 400, 15, 1500, 600, 300]`, cell IDs equal to settlement IDs, distance `abs(seat.cell - member.cell) * 0.7`, cultural distance `(member.id % 3) * 0.2`, current tick 100, and all five winner institutions. It calls the real load and conquest functions, with only distance/culture inputs stubbed to those deterministic values. **Estimated added load is 10.9291428945; actual added load is 12.7591428945.** Existing winner load in the interval `(capacity - 12.7591428945, capacity - 10.9291428945]` makes the room check admit a conquest that exceeds capacity (`CONQUEST_ROOM` is 1).

## Checked and sound

- **Original finding 1, population case:** the 15-person target seat plus 1,500-person member now estimates **6.9570108524**, equal to the sum of their fresh-conquest loads with no institutions and equal location/culture.
- **Fallen members' own attributes:** the patch now uses each member's own population, distance and culture rather than multiplying the fallen seat's load. With a correct attacker-depth offset, the fallen tree's relative depths, bounded delegation discount, council, collectors and warriors effects agree with the yearly formula. Fresh-conquest weighting agrees, and the estimator restores the target's prior conquest timestamp.
- **Finding 2, recovery condition:** evaluating the actual parsed `ok4` expression with four eligible collapses makes 0/4 and 1/4 recoveries fail and 2/4 and 4/4 pass, holding the other requirements satisfied.
- **Finding 3, continuous hold:** seven focused cases pass: the old separated peaks are rejected; a 40-year sampled hold is rejected; 50- and 60-year holds followed by a drop qualify; a single intervening below-threshold sample resets the hold; a missing decadal sample breaks continuity; and a qualifying hold still standing at the history's final sample is not itself a collapse. Six samples at years 0–50 establish 50 elapsed years, rather than counting the first sample as ten years. Continuity between decadal observations remains an observation limit.
- **New problems:** no additional regression established in the changed lines. The remaining ancestry problem above prevents accepting finding 1 as fully resolved.

## Validation and limits

`reviews/scratch/review002.py` and its captured output exercise the estimator, actual conquest transfer, full-member depth reconstruction, recovery expression and collapse boundaries. An initial matrix of 129 cases (the original example plus all 32 institution combinations at attacker depths 0–3) produced 48 estimator/yearly mismatches, all at attacker depths 2 or 3. The all-institutions example above was checked separately. These are synthetic accounting cases, not estimates of how often the defect occurs in gate histories; some institution combinations are exploratory rather than intended institutional progressions.

Two existing tests passed in 5.101 seconds: `test_m0.Replay.test_save_load_continue_is_exact` and `test_event_store.SampledLogsCoverTheWholeHistory.test_log_row`. Both changed modules parse with Python 3.10 grammar under Python 3.12; Python 3.10 runtime execution was not tested. No full suite or gate-length history was run for this focused follow-up. Scratch files are ignored and not committed; the ancestry demonstration and numerical inputs above preserve the finding's evidence in the committed review.

Claude's response describes a full-suite result and a measurement of the effect on G3 run 2 as “below,” but does not yet include their results at this revision. I have not treated those pending results as validation or inferred whether G3 needs another run.

## Design questions for Ben

None. These checks apply the existing load and measurement rules.
