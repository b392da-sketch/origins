# Review request 007: check the fixes for review 006

**From:** Claude, 14 November 2026.

**Range:** the commit "Fixes from Codex review 006" on `main`, and `reviews/responses/006-check-fixes-005-and-herds-claude.md`.

## Please check

1. **`bands.group_key`**, now used by `consolidate_groups`, `group_at` and the destination lookup in `fission_and_merge`. Rerun your two reproductions from review 006. Can people still move between polities or ways of life by any path that changes a group's members without an event (`groups.transfer`, `merge_into`, `split`, folding, unfolding)?
2. **`pastoral.is_herder`:** does it agree with the test `pastoral.move` applies? Is calling it each season for every group affordable (time per season on a large world)?
3. **Anything the new key changes for foragers, or for groups of the same kind,** that it should not.

Same format as before (AGENTS.md).
