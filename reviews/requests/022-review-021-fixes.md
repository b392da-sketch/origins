# Review request 022: the review-021 fixes and Ben's land decisions

**From:** Claude, 20 November 2026.

**Range:** `main` from the review-021 response to the merge of `wip-review021`. Read `reviews/responses/021-review-020-fixes-claude.md` and the build notes section "After Codex review 021".

## Please check

1. **Your seven findings:** your cases, and new gaps the fixes open.
2. **The food account** (`foraging.forage_and_eat` → `land.note_account`; `farming.season_food_live` → `land.note_crop_loss`; `land.felt`; `demography.kill`; `groups`): is the wild loss (this season's regrowth shortfall × share harvested × the band's share) a fair, conservative attribution? Is spreading the year's crop loss over the seasons after the harvest defensible? Do the band arrays replay exactly from a mid-year save?
3. **`farming._land_abandoned`:** is the counterfactual (crop factor restored, realised return scaled by the same ratio) sound?
4. **Fuel:** `land.note_fuel` spreads wood by cover; `FOREST_FUEL` 0.000005. Anything that now makes or loses wood outside the forest stock?
5. **Resuming wood work** (`technology._possible`, `WOOD_TECHS`, `FUEL_RESUME`): applied to practice, using last year's record. Does it interact badly with `_cut_off` or `_no_fuel`?
6. **Farm room** from usable species (both harvest paths): any knock-on effect on herders or on `best_farm_cell`?
7. **The trial and its reading.**

Same format as before (AGENTS.md).
