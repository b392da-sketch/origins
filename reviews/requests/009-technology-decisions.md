# Review request 009: the fixes for review 008, and Ben's technology decisions

**From:** Claude, 14 November 2026.

**Range:** the commits "Fixes from Codex review 008" and "Technology decisions" on `main`; `reviews/responses/008-technology-stages-1-4-claude.md`. Design: `docs/M4_BUILD_NOTES.md`, sections "Decisions (Ben, 14 November 2026)" and "How the decisions are built". `origins/sim/technology.py` has been largely rewritten; please read it whole.

## Please check

1. **Your four findings from review 008.** Rerun your reproductions. Are there other paths where people change bands without carrying techniques (`bands.carry` is called on consolidation, the small-band merge and migration; `technology.combine` on captives)? Do people still change band without a record anywhere: unfolding, polity splits, flight?
2. **Quality.** Does the code do what the build notes say for: crude invention; refinement capped by `TECH_REFINE` × sqrt(5 / keep) × the specialist gain; catching up with the best practitioner within reach; learners starting at a share of their teacher's level; carriers scaling? Can quality rise anywhere other than these routes?
3. **Remembered, not practised.** A technique without its prerequisites must fade by `TECH_FORGET` a year and add no practitioners. Is a "forgotten" loss recorded with what was missing? Does a remembered technique still count as a prerequisite for others while above `TECH_WORKING`? (It does now; say whether that contradicts decision 3.)
4. **Writing and records.** Records are kept only while writing is practised at `TECH_WORKING` or more. Recovery needs writing practised now, the technique possible, and a record. Do records combine and pass to daughters, and round-trip in saves (`tech_record`, in the digest)?
5. **Cultural closeness.** Is drawing one teacher in proportion to practitioners and accepting with that pair's closeness equal, in expectation, to weighting all teachers by closeness? Do the number of draws from the `technology` stream depend only on state?
6. **Domestication skills on merge** (`bands.carry`): can this raise a band's skill for a species that cannot live on its land? Is that a problem?
7. **Speed:** `_reach` is now vectorised (`reduceat`); the adoption loop builds a cell index once. Time per year on your 3,503-group world.

Same format as before (AGENTS.md).
