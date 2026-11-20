# Review request 032: writing refinements and place names

**From:** Claude, 21 November 2026.

**Range:** `main` from `cbcedad` (the merge of `wip-review031`) to the merge of `wip-writing`. Read the build notes sections from "Writing and place names: literature check (Claude)" to "Writing and place names, as built", including Ben's decisions of 20 and 21 November.

This is the last M4a build step. After it comes the comprehensive pre-gate review (CLAUDE.md). Please rank what you find and say which items should block the G4a gate.

## Please check

1. **Writing (`origins/sim/technology.py`):**
   - **scribes** (`w.tech_scribes`, `_scribes`, `skilled_by_technique`, `keep_needed`): only at seats of living complex chiefdoms and states, averaged over a generation. Check how the array grows, starts in a daughter, combines, is saved, enters the digest, and is derived for older saves;
   - **writing needs scribes** in `_possible` and `prerequisites_met`; it is not inherited by daughters and passes in `combine` only for whole peoples;
   - **stimulus diffusion** (`_stimulus`, the invention multiplier and its cause);
   - **records without a script** in `capacity_multiplier`.
2. **Place names (`origins/sim/places.py`, stream `places`):**
   - **features from the planet:** rivers split at joins, lakes, hills and mountains, coasts, settlements;
   - **naming chance, keep or replace, and conquest;**
   - **layers and their forms now** (`evolve`, `current`, `name_in`): rules applied after the naming tick only, through the right lineage, for dead languages up to their end, and daughters inheriting;
   - **saves, digest, events and cause chains;**
   - **cost at gate scale.**
3. **Older saves:** they load and replay (no places, scribes from today's specialists at qualifying seats).
4. **Trials** in the build notes: do the numbers say what the notes say they say?

Same format as before (AGENTS.md).
