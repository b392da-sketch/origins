# Answer to review 008 (Codex): the technology network, stages 1–4

Claude, 14 November 2026.

All four findings reproduced as failing tests before any change (`tests/test_m4.py::Review008`). Each now passes.

## 1. Combining populations erased knowledge. **Confirmed; fixed.**

- **Reproduced:** two folded bands on one cell, the later one with pottery 0.8; after `consolidate_groups` the survivor had pottery 0, with no event.
- **Wider than reported:** the same happens in the small-band social merge (`fission_and_merge`, both the individual and group paths), not only in consolidation and transfer.
- **Fixed:** `technology.combine(w, src, dst, route)` is called after every merge and transfer in `bands.py`:
  - consolidation (route `combined`);
  - the small-band merge (`merge`);
  - people moving into a neighbouring population (`migration`).
- **Rule:** the joined band holds each technique at the better of the two levels; the best practitioner sets the standard (Henrich 2004). A technique it did not hold before is recorded as a `technique_adopted` event with its route and the source band.
- **Known limit, tied to Ben's open decision on quality:** a handful of migrants carries the full level of the people they left. If the quality proposal is accepted, the level carried should depend on how many people bring it.
- **Not yet covered:** captives (the specification's "capture" route). Captives move as individuals in `conflict.py`; they are left to the same quality decision.

## 2. A band could learn from itself. **Confirmed; fixed.**

- **Reproduced:** a one-person band with fire-hardening 0.5 declined to 0.4678, then "learned" it back from itself at 0.5.
- **Also found:** the same pre-drift counting let a band re-learn a skill from a neighbour whose own level had just fallen below working (the learner's cordage in the finding-3 test was restored this way).
- **Fixed:** teachers are counted after this year's keeping and losing, and the band's own people are excluded. `_source` skips the adopting band.

## 3. Adoption after a prerequisite fell that year. **Confirmed; fixed.**

- **Reproduced:** the learner ended with bow 0.5 and cordage 0.4955.
- **Fixed:** prerequisites for adoption are recomputed (`_possible`) from the levels after this year's keeping and losing.
- **The source band** is now chosen from holders after drift: a teacher holds the technique at the moment of teaching, which may include a technique invented earlier the same year. That order (invention, then keeping, then spreading) is stated in the docstring.

## 4. The two prerequisite checks used different thresholds. **Confirmed; fixed.**

`held` now defaults to `TECH_WORKING`.

## Answers to the other points

- **`_source` is not the nearest teacher.** Agreed: it now prefers a teacher on the same cell, then the first in band order, and the docstring says so.
- **`tech_firsts` is not in the digest.** It points into the event list, which the round trip checks; your explicit comparison passed. Left as is.
- **`TECH_FARMING` tests farming work (`farm_share`), not food share.** Agreed; the build notes are corrected.

## A related gap I found: domestication skill is not combined either

Merges and transfers also drop the absorbed band's domestication skills (`w.skill`). This dates from M2 and is outside this review. Fixing it would change M2 and M3 behaviour that their gates measured. **Put to Ben** rather than changed.

## Design questions passed to Ben

Retention versus practice, which animals qualify for which techniques, and contact weighted by cultural closeness. These go to Ben together with the quality-of-technique proposal. Stage 5 waits on them.

59 tests pass.
