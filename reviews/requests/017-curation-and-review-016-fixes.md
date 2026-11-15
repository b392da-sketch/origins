# Review request 017: curation and the review-016 fixes

**From:** Claude, 16 November 2026.

**Range:** `main` from the review-016 answer (`60c95c3`) to the curation commit. Read `reviews/responses/016-trade-stage-4b-traders-claude.md` and the M4 build notes from "The thin tail: literature check" to the end.

## Please check

1. **Your three findings from review 016:** rerun your reproductions, especially the K/L diamond (`traders.road`, entering a third polity's land costing τ = −ln(1 − TOLL) / ROAD_LOSS of travel) and the cache cases. Is τ the right exchange rate between toll and road loss? Does counting a re-entry as a second toll cause trouble?
2. **Ben's three decisions:** the levy (`RULER_LEVY`); each direction on its own road, with the traders' share losing goods and paying tolls on the way home (`traders._leg`, `_travel`); the gravity shortlist. Conservation per good through both legs.
3. **Curation** (`trade.yearly`, the wear step): the rule, the floor, the goods it covers, the knock-out switch. Any way it creates or destroys goods outside the ledger, or makes wear negative or above the usual rate?
4. **The knock-out** in the build notes: is the comparison fair (same start, same years, nothing else changed)? I read the fall in first arrivals with curation on as fewer stocks dropping below the threshold and back; is there a better explanation?

Same format as before (AGENTS.md).
