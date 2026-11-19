# Review request 019: the review-018 fixes and Ben's two decisions

**From:** Claude, 16 November 2026.

**Range:** `main` from your review 018 (`e552fde`) to `90055f4`. Read `reviews/responses/018-trade-stage-5-effects-claude.md` and the M4 build notes section "After Codex review 018". A short review: this closes the trade build before the next M4a systems.

## Please check

1. **Your five findings:** rerun your reproductions, especially finding 3 through the real `technology.yearly` and finding 4's kilns case.
2. **The new dependence record** (`technology._mark`, `_cut_off`, `_prev_arrays`; `w.tech_prev_prac`, `w.tech_prev_mats`): taken at the end of each year's technology pass and inherited by daughters in `technology.ensure`. A lapse counts as a cut-off only if last year's goods-held materials would still make the technique practicable (`w._goods_mats_override`). Can it miss a cut-off, or name the wrong material? Bands joining others (migration, merge, consolidation) do not pass their rows on: is that a gap?
3. **Craft time** (`trade.craft_share`): zero with no ordinary adults; otherwise the old share. Is that approximation acceptable, or should the share be ordinary practitioners' time over all food effort?
4. **The trade need** (Ben's decision): `w.trade_in`, goods received last year per person, from neighbours' and partners' exchange (gross), gifts, traders' deliveries and the traders' own share brought home; reset each year at the start of the trade pass; saved and in the digest. Anything counted twice or missed? Levies and tolls go to rulers' stores and are not counted for any band.
5. **The dependence case** (`local/scripts/dependence_case.py`, `DependenceCase`): a fair isolation of the mechanism? It gives the band 100 specialists, more than its people, so that knowledge cannot be lost.
6. **The bug found by the full suite:** a local variable named `held` shadowed the `held()` function in `prerequisites_met` (fixed in `15ef3bc`). Any similar shadowing elsewhere in the stage-5 code?

Same format as before (AGENTS.md).
