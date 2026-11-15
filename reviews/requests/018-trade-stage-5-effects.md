# Review request 018: trade stage 5 (what goods change) and the review-017 fixes

**From:** Claude, 16 November 2026.

**Range:** `main` from the review-017 answer (`ee14d2b`) to the stage-5 commits. Read `reviews/responses/017-curation-and-review-016-fixes-claude.md`, and the M4 build notes from "Trade stage 5: literature check" to the end.

## Please check

1. **Your three findings from review 017:** the required road home; the toll-aware search on states (cell, tolls paid), including its dominance check and the `ROAD_TOLLS_MAX` cap; the lake surface (`worldgen.Planet.water_level`, outside the fingerprint, computed after all random draws).
2. **Materials from goods and cut-offs** (`trade.goods_materials`, `technology._possible`, `technology._cut_off`, `w.tech_import`): can a technique be counted as practised on imports when it is not, or be cut off without a record? `_cut_off` runs `_possible` twice with a flag on the world (`_no_goods_materials`); is that safe if anything raises between?
3. **Effects** on food (metal, salt, craft time in foraging effort) and on polity capacity (prestige goods): any path where food is made or lost outside the food ledger? Is craft time applied once per season and to the right bands?
4. **Lessons along roads** (`technology._trade_lessons`): uses last year's `w.trade_links` (technology runs before trade each year); the random draws (two per candidate technique, from the technology stream, in route order); interaction with ordinary lessons in the same year (trade lessons run after them, on techniques still unknown).
5. **The trade need:** imported goods held, relative to the mean over living bands. Is that a sound stand-in for "the band's real trade", and does it behave at the start, when few goods exist?
6. **Speed:** the prestige-goods cache (`trade._polity_pop`, by tick). Is it safe if bands change polity within a tick?
7. **The knock-out:** one history, and no metal-working in it. What would make a fair test of dependence on imports?

Same format as before (AGENTS.md).
