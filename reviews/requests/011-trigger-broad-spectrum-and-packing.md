# Review request 011: review-010 fixes, settled builders, broad-spectrum food, the farming trigger, and gate packing

**From:** Claude, 14 November 2026.

**Range:** `main` from `7649b88` (the review-010 fixes) to the current head. Read `reviews/responses/010-technology-fixes-and-effects-claude.md`, `docs/FARMING_TRIGGER_PROPOSAL.md`, and the M4 build notes from "Building techniques need a settled people" to the end.

## Please check

1. **Your five findings from review 010** and the two decisions (sail reach scales with quality; specialists counted once). Rerun your reproductions.
2. **Settled builders** (`technology._settled`, the `settled` field): `_possible` and `prerequisites_met` agree?
3. **Broad-spectrum food** (`climate.broad_share`, `broad_max`, `regrow`; `foraging.forage_and_eat`; `technology.forage_access`; `w.stock_broad` in `persist` and `observe`):
   - Conservation: every unit taken from either pool is recorded, and the food balance holds each season.
   - Ordinary food is taken first; broad food only with the effort left over, at `TECH_BROAD_RETURN`, and only by bands with gear, in proportion to their reach. Is the split of the harvest between bands on one cell right?
   - Saves from before the pool load with it at its seasonal level; replay stays exact.
4. **The farming trigger** (`farming.yearly`, `farming.crowding`, `_first`):
   - Is crowding computed as described (the cell and its neighbours; people against unaided wild-food capacity)?
   - The abundance route: settled `ABUNDANCE_YEARS`, rich land (`ABUNDANCE_SUIT`), pressure floor `ABUNDANCE_FLOOR`. Does it apply per species, and only where the species grows wild?
   - The random draws from the `farming` stream now happen in more cases. Is their number still a function of state only?
   - Each first tending names its route. Correct in all three cases?
   - Our finding that first tending is very rare (expected 0.0002–0.0004 a year on a forager world): please check the arithmetic.
5. **Three histories per GitHub job** (`gates/plan.py`, `gates/run_job.sh`, the workflow): parallel processes share one checkpoint folder and one results folder. Can they collide? A later stage continues only histories with a checkpoint; a finished history's checkpoint is removed. Any case where a history is lost, run twice, or restarted from scratch?

Same format as before (AGENTS.md).
