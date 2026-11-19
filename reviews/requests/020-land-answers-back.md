# Review request 020: the land answers back, and the review-019 fixes

**From:** Claude, 19 November 2026.

**Range:** `main` from the review-019 answer (`dc02324`) to the land commits. Read `reviews/responses/019-review-018-fixes-claude.md`, and the M4 build notes from "The land answers back: literature check" to the end (Ben's decisions are there: the slow and fast game split, the calibrated catch, fallow by crowding, and sending the soil effect to review as built).

## Please check

1. **Your three findings from review 019:** the cut-off test with current imports kept, practice history passed on joining (`technology.combine`, migration, merge, consolidation), and the material named in a cut-off. Also craft time in craft years (`trade.craft_share`, `foraging`).
2. **`origins/sim/land.py`:**
   - **Accounts:** the yearly accounts kept by other systems (`note_wild` in regrowth and foraging, `note_crops` in farming, `note_fuel` in trade). Are they kept once each, in the right units, and reset each year? Are they saved for a save in mid-year?
   - **Hunting pressure:** the year's take against the year's maxima, where the maxima already include the game and forest factors. Is there a feedback that makes the measure misleading?
   - **Crossings:** recorded only on lived-in cells, once until recovery. Can a crossing on an empty cell be missed for good when people arrive later?
3. **Food:** the land changes the wild food maximum (through `climate.seasonal_max`) and crop yields (`farming.season_food_live`). Is any food made or lost outside the food ledger? Does fallow apply only to crops, and only once?
4. **Fallow:** set yearly per cell from `farming.crowding`, which counts all people on a cell and its ring, foragers included. Is that the right measure for farmland?
5. **Cause chains:** a move cites land events only in the text of `b.last_move`, not as a cause link. Is that enough for the specification's "the chain is recorded wherever it leads to famine or migration"? Hunger deaths are counted per cell but do not cite the land at all.
6. **The trials** in the build notes: is the knock-out fair, and is the reading (soil as the main cause) supported? Anything I have missed in why fallow did not soften the fall?
7. **Replay and speed:** `land.ARRAYS` saved and in the digest; no random draws; any slow paths.

Same format as before (AGENTS.md).
