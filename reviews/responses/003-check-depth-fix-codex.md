# Review 003: the depth fix

12 November 2026. Reviewed `f090cbb` and Claude's response to review 002 at checkout `51583aa`, following `AGENTS.md`. The previously read M3 rules and gate decisions remain the review basis; the new M4 approval does not change this request's M3 accounting scope. No application files were changed.

The original conquest-depth defect is fixed for valid trees: the 129-case matrix now has **zero mismatches**. Two remaining issues prevent an unqualified claim that all four joining calculations agree with the yearly calculation.

## Findings

### 1. A daughter of the seat is still priced as a delegated member

- **Where:** `origins/sim/polity.py::ensure`, lines 83–89.
- **What is wrong:** The special case for `parent == p.seat` starts at 1 and then adds another 1, giving daughter depth 2. Once registered with `polity_via[daughter] = seat`, its actual depth is 1. With collectors, the estimate therefore applies `DELEGATED_LOAD = 0.5` to a settlement that the yearly calculation treats as a direct member.
- **Why it matters:** Daughter settlements can be admitted beyond capacity and their immediate load is undercounted. This offset predates the patch but remains in the explicitly requested daughter-joining path. The example below isolates depth: daughter size and place exactly match the estimator's assumptions, and neither settlement has a conquest penalty.
- **How sure:** Certain.
- **How to see it:** With collectors alone, capacity is 9. For 75 people at the seat's location and culture, true direct load is `sqrt(75 / 150) = 0.7071067812`; `ensure` adds **0.3535533906**. Starting at load **8.4696699141**, it admits the daughter, although the true total is **9.1767766953**. Reproduce using the real admission function:

```python
from types import SimpleNamespace as S
from unittest.mock import patch
import numpy as np
from origins.sim import polity
p = polity.Polity(0, 0, 0, 'p')
p.inst[polity.COLLECTORS] = 1
p.cap = polity.capacity(p)
u = np.sqrt(75 / 150)
p.load = p.cap - .75 * u
before = p.load
w = S(t=0, polity_of=np.array([0, -1, -1, -1]),
      polity_via=np.full(4, -1), polities={0: p},
      bands={0: S(id=0, cell=0)}, conquered_at=np.full(4, -1))
with patch.object(polity, '_cells_apart', return_value=0), \
     patch.object(polity, 'cultural_distance', return_value=0):
    polity.ensure(w, 1, 0)
assert w.polity_of[1] == 0
assert polity._depths(w, [0, 1], 0)[1] == 1
assert np.isclose(p.load - before, u / 2)
assert before + u > p.cap
```

### 2. Cycle handling does not agree between the two depth helpers

- **Where:** `origins/sim/polity.py::depth_of`, lines 137–141, compared with `_depths`, lines 146–161.
- **What is wrong:** `depth_of` terminates a self-link as one edge, whereas `_depths` walks it until its membership-based guard expires. For longer cycles, `depth_of` uses allocated array length as its guard, while `_depths` uses supplied membership length and memoizes results. They therefore produce different depths on the cyclic inputs explicitly named in this request.
- **Why it matters:** On such inputs, admission depth checks and delegation discounts can disagree with yearly loads. This is a confirmed edge-case inconsistency, not evidence that normal simulation histories contain cycles. `_depths` is not a mathematically correct reference for a cyclic hierarchy either; reproducing its arbitrary number alone would not establish a meaningful tree depth.
- **How sure:** Certain about the disagreement; occurrence and impact in real histories are unmeasured.
- **How to see it:** Set `w = S(polity_of=np.zeros(4, dtype=int), polity_via=np.array([-1, 1, 1, 2]))`. Then `depth_of(w, 1, 0)` is **1**, but `_depths(w, [0, 1, 2, 3], 0)[1]` is **5**. For `polity_via=[-1, 2, 1, 2]`, the single helper returns depths **5, 5, 5** for members 1–3, while the full helper returns **5, 4, 5**. Both examples terminate; the defect is inconsistent interpretation, not an infinite loop.

## Checked and sound

- **Ordinary depth lookup:** all 14,400 comparisons passed across 120 acyclic five-settlement parent configurations and every ordering of the full membership. This includes the seat (depth 0), ordinary chains and non-seat members whose parent is −1. A separate stale link through another polity stops at the same boundary as the full-membership helper.
- **Conquest estimate:** the requested 129-case matrix now has zero mismatches, including all 32 institution combinations at attacker depths 0–3. It calls actual `_conquer`, then compares against full-member depths and fresh-conquest `unit_load` sums. The original example agrees at **6.9570108524**; the all-institutions/deep-attacker example from review 002 now agrees at **12.7591428945**.
- **Alliance depth check and added load:** both use the same parent-depth-plus-one rule, with a direct seat child explicitly at depth 1. On valid trees, their use of `depth_of` agrees with the full-member calculation. This statement concerns the inspected expressions and the helper comparisons, not a newly executed full alliance simulation.
- **Non-seat daughter depth:** on valid trees the new `depth_of(parent) + 1` offset is correct. The seat special case is finding 1.
- **Recovery and collapse checks:** the seven boundary cases and recovery-threshold checks from review 002 still pass.

## Other joining estimates and validation limits

`ensure` intentionally estimates a daughter before registration using the parent's cell/culture, a fixed `VILLAGE_FISSION_SIZE / 2` population, and `conquest=False`. Actual fission can choose another cell and move a different number of people; `World.new_band` also calls `conflict.ensure`, which copies the parent's conquest timestamp to the daughter. These proxy inputs can differ from yearly load independently of depth. I have not classified those documented approximations as new regressions, nor claimed that correcting finding 1 would make all daughter admission estimates exact.

The focused scripts and output are under ignored `reviews/scratch/` (`review003.py`, `review003.log`, `review003-matrix.log`); the committed examples above preserve the two findings. The matrix contains exploratory institution combinations as well as plausible ones and measures accounting agreement, not frequency in gate histories. Both changed modules parse with Python 3.10 grammar under Python 3.12; no Python 3.10 runtime was available for this check. The two existing replay and sampled-log tests passed in 5.064 seconds (`review003-existing-tests.log`). No full suite or gate-length history was run.

## Design questions for Ben

None required to establish these discrepancies. No changes to the institutional rules are proposed.
