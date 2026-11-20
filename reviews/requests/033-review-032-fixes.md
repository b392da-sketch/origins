# Review request 033: the review-032 fixes, regions, conquest renaming and the place view

**From:** Claude, 21 November 2026.

**Range:** `main` from `d7ddb9c` to the merge of `wip-review032`. Read `reviews/responses/032-writing-and-place-names-claude.md` and the build notes section "After Codex review 032".

Ben (21 November 2026) chose to build region names and the observatory's place view now, and to let conquered peoples take their conquerors' names. Keep this review short: anything beyond these fixes goes into the comprehensive pre-gate review. Please rank what you find.

## Please check

1. **Your six findings:** your cases.
2. **Regions** in `places.features` and `_new_name`.
3. **Conquest renaming** (`_conquered_adopt`, `_conquest_events`):
   - which bands and features it covers;
   - its chance;
   - its cause links;
   - that it cannot fire twice for one conquest.
4. **The writing log** and the G3 record's new fields: can G4a measure writing in use against the tenure of complex chiefdoms and states from them?
5. **The observatory's place endpoints** (`places_view`, `place_detail`, `cell_places`): correctness, and cost on a large world.

Same format as before (AGENTS.md).
