# Review request 001: M3 changes since G3 run 1

> **Status (12 November 2026, 12:11):** active again (Ben). G3 run 2 (GitHub run 43126485621) is running on this code: findings that would change its results matter most.

**From:** Claude, 12 November 2026. **For:** Ben's decision on G3 run 2 and the M3 gate.

**Range:** commits from `804cf20` ("Captive infants go with their mothers…") to the head of `main` (`git log 804cf20^..main`). The background is in `docs/M3_BUILD_NOTES.md` (sections from 11 November onward) and in `docs/M3_GATE_REPORT.md` (corrections and Ben's decisions at the end).

## Please check, most important first

1. **Do the gate checks measure what their wording says?** In `gates/g3_report.py`, look at checks 4, 5, 5b and 9 (check 9 was reworded by Ben on 12 November: "inequality rises with scarce land and herds"), and at what the gate worker records in `gates/g3.py` `finish()`.
   - Are the logs they read complete over each history? `state.log_row`, `polity_log` in `sim/polity.py`, `war_log` in `sim/conflict.py`, `gini_log` in `sim/surplus.py`, and their saving and loading at checkpoints in `persist.py`.
   - G3 run 1's logs covered only the end of each history. Is anything else still cut short?
2. **Wealth and inequality** (`sim/surplus.py`): the property households (founded at partnership), new households, land scarcity per cell, herds, and `inherit()` by custom of succession.
   - Can holdings be created or lost where they should not be?
   - Does anything still level households artificially, or inflate the Gini?
3. **Polity load and capacity** (`sim/polity.py`, `sim/conflict.py`): `unit_load`, load counted at once when settlements join, `_room_for` / `_conquest_load`, and delegated load limited by `max_depth`.
   - Can a polity still grow far beyond its capacity in one year?
   - Is there an inconsistency between how load is estimated at joining and how it is computed yearly?
4. **The project's rules:** random streams (no system drawing from another's stream), exact replay (`EventStore`, `to_file`, and checkpoints round-tripping exactly), and cause chains (the orphaned-infant fix in `explain.py`).
5. **Python 3.10 compatibility** of everything changed.

## Not in scope

The design choices Ben has already made (in the gate report's decision sections). Comment on them only under "Design questions for Ben".
