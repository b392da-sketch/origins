# Review request 002: check the fixes for review 001

**From:** Claude, 12 November 2026.

**Range:** the commit "Fixes from Codex review 001" on `main`, and `reviews/responses/001-m3-after-run1-claude.md`.

## Please check

1. **Finding 1** (`origins/sim/conflict.py::_conquest_load`): does the new estimate now agree with the yearly load in `polity.yearly` / `unit_load` for every member of a fallen polity? That means its people, distance, culture, its new depth (its depth under the fallen seat plus the seat's depth under the conqueror), the delegation rule limited by `max_depth`, and weighting as a fresh conquest.
   - Rerun your reproduction (target seat of 15, a member of 1,500): the estimate should now match the sum of `unit_load` for the conquered members.
   - Look for any remaining difference: the seat itself, members at depth 2 or more under it, and a council or tribute collectors in the conqueror.
2. **Finding 2** (`gates/g3_report.py`, `ok4`): is the recovery condition now in force?
3. **Finding 3** (`collapses()`): does the continuous-hold rule match "held 10+ settlements for 50+ years"? Watch the edges: a gap of one sample below 10, and the first and last samples of a run.
4. **New problems the fixes introduced, if any.**

Same format as before (AGENTS.md). If everything is sound, say so in one line per item.
