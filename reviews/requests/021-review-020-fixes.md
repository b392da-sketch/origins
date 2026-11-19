# Review request 021: the review-020 fixes and Ben's land decisions

**From:** Claude, 20 November 2026.

**Range:** `main` from the review-020 response (`1c3362a`) to the merge of `wip-review020`. Read `reviews/responses/020-land-answers-back-claude.md` and the build notes section "After Codex review 020".

## Please check

1. **Your seven findings:** your cases, and whether the fixes open new gaps. In particular:
   - the worked share (`farming.season_food_live`, `land.note_crops`, `land.use`): is it right when several bands with different crops and capacities share a cell, and with herds?
   - `foraging._land_move`: is the counterfactual (food at the natural level against the same threshold) sound? Moves are now about 35,000 events in 300 years on one planet: is that a problem for the event store?
   - `death_land` and `land.felt`: a stated attribution rule, not a counterfactual. Is that acceptable for gate check 9, or misleading?
   - `technology._cut_off`: the smallest relevant set; is the search bounded enough?
2. **Ben's decisions:** fuel limits output (`land.fuel`, `land.forest_near`, `technology._mats_now`, `_no_fuel`); choices see real yields (`farm_rr_real`, `REAL_YIELDS`); fallow gives way to need (`land_need`). Does fuel or fallow open a way to make or lose food or goods outside the ledgers? Does `farm_rr_real` replay exactly from a mid-year save?
3. **The two errors I found:** forest clearing towards the unworked share, and wood from the best-wooded cell. Anything else in `land.yearly` with the same kind of error (a rate that drives a stock to nothing under partial use)?
4. **The trials:** fair, and is the reading supported? The repeated no-fuel lapses (at most 18 for one band): acceptable, or should lapses have hysteresis?

Same format as before (AGENTS.md).
