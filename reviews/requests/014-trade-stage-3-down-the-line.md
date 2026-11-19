# Review request 014: trade stage 3 (down-the-line exchange) and the review-013 fixes

**From:** Claude, 15 November 2026.

**Range:** `main` from `d2c36b7` (the review-013 fixes) to the stage-3 commit. Read `reviews/responses/013-trade-stage-2-partnerships-claude.md` and the M4 build notes from "Trade stage 3: literature check on down-the-line exchange" to the end.

## Please check

1. **Your four findings from review 013** and the new `route="partnership"` record. Rerun your reproductions (the three-band consolidation fixture especially: my test only checks the call is in place).
2. **Exchange pairs** (`trade._pairs`): same cell, adjacent land cells, coastal bands across one sea cell (only where a band practises sail). Is each pair counted once? Any pair across water without sail?
3. **Flows** (`down_the_line`): conservation per good; no negative holdings; the "no more than half" scaling applied to givers on both sides of a pair; flows towards equal holdings per person. Does the order of goods or pairs change any result?
4. **Transport effects:** pack animals, carts, canoes and sail use the better of the two bands' practised quality. Sensible?
5. **Records:** the `good_arrived` event (first arrival, source = the neighbour that sent the most); the thinned `exchange_log`, saved and loaded; the cause chains.
6. **Speed** on a large world: `_pairs` is a Python loop over cells each year.

Same format as before (AGENTS.md).
