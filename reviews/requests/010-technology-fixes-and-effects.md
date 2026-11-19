# Review request 010: fixes for review 009, skilled practitioners, and effects (stage 5)

**From:** Claude, 14 November 2026.

**Range:** `main` from `90d0478` to the stage 5 commit: `reviews/responses/009-technology-decisions-claude.md`; build notes sections "After Codex review 009", "After the literature check" and "Stage 5: effects".

## Please check

1. **Your four findings from review 009** and Ben's ruling that a prerequisite counts only when practised (`_possible` builds the chain in catalogue order; `prerequisites_met` recurses). Rerun your reproductions.
2. **Skilled practitioners** (`_adults`, `TECH_PRACTISE_SHARE`): adults 15–59 counted for individuals and groups alike? Specialists added once?
3. **Refinement near mastery:** the cap is `TECH_REFINE` × sqrt(5 / keep) × specialist gain × (1 − quality). Any route that still lets quality jump?
4. **Effects** (`practised_quality` and the multiplier functions; hooks in `foraging.py`, `farming.py`, `surplus.py`, `polity.py`, `hazards.py`):
   - Does each effect use only *practised* quality, with the right technique, cells and land?
   - **Nothing from nothing:** foraging gains must come from the cell's wild stock; farming gains stay within the land's capacity, except where terracing, irrigation or milking raise it. Does `observe.py`'s conservation check still hold?
   - **The cache** (`w._tech_eff`, keyed by tick, cleared when knowledge changes): can a stale value change a result? Does replay stay exact across a save mid-history?
   - **The farming work choice** uses the same per-worker multiplier as the harvest. Is it the right one for plants versus animals?
   - **Sail** extends crossings to land across two sea cells. Is the reachable set right, and is the number of draws from the `crossing` stream unchanged?
5. **The gate record** (`gates/g3.py`): the technology fields, and `herders_alive` now counting current herders.

Same format as before (AGENTS.md).
