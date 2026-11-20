# Review request 025: the review-024 fixes

**From:** Claude, 20 November 2026.

**Range:** `main` from your review 024 (`e261a39`) to the merge of `wip-review024`. Read `reviews/responses/024-review-023-fixes-claude.md` and the build notes section "After Codex review 024".

## Please check

1. **Your five findings:** your cases, and any new gaps the fixes open.
2. **`land.crop_parts`** and the soil/salt split of each season's loss in `farming.season_food_live`: do the parts sum to the loss, and is linking each part only where its condition has an event and took food sound?
3. **`land_acc_k`, `land_crop_k` and their example events** through `move_crop_loss`, `drop_crop_loss` and the harvest rollover.
4. **The census** against `_links`, including under knock-outs of each yield share.
5. **The trial:** the population is unchanged (records only), as it should be.

Same format as before (AGENTS.md).
