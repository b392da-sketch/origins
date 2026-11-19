# Review request 008: the technology network, stages 1–4

**From:** Claude, 14 November 2026.

**Range:** `origins/sim/technology.py` (all of it), its hooks in `engine.py`, `state.py` (`technology` stream, `init`, `ensure`), `persist.py` (`tech` array, `tech_firsts`), `explain.py` (titles), the `TECH_*` parameters in `params.py`, and `tests/test_m4.py`. Specification: `docs/M4_SPECIFICATION_v1.md` sections 3.1–3.4. Build notes: `docs/M4_BUILD_NOTES.md`, technology section.

Effects (stage 5: what each technique changes) are not built yet; techniques are held, invented, kept, lost and spread, but change nothing else. Please review stages 1–4 only.

## Please check

1. **Prerequisites (`_possible`, `prerequisites_met`).** Do the two agree in every case? Farming techniques now need a domesticate *and* a farm or herd share of at least `TECH_FARMING`; terracing needs hilly land and irrigation a river or lake on the band's own cell (`_cell_terrain`, `TECH_HILL_RELIEF`). Are any of the 27 techniques' prerequisites, materials or keep numbers clearly wrong against the literature cited in the specification?
2. **Invention (`yearly`).** Does the formula in the docstring match the code? Is `connected` (people within two rings) computed correctly, including bands on the same cell? Is the knock-out (`TECH_POP_EXPONENT = 0`) a true knock-out?
3. **Keeping and losing (`keep_and_spread`, stage 3).** Does the drift `TECH_LEARN × ln(skilled within reach / keep)` reproduce the direction of Henrich (2004): gain above the threshold, loss below it? Is a loss recorded exactly once and the level zeroed? Can a technique whose prerequisite is lost still be held?
4. **Spreading (stage 4).** Adoption needs prerequisites (from `possible_all`, computed *before* this year's losses and inventions: is that a problem?). Its chance is weighted by need. Is the source band (`_source`) really within reach and holding the technique at the start of the year?
5. **Random streams and replay.** Only `w.rng["technology"]` is drawn from; the number of draws must not depend on anything but state. Does a save mid-run round-trip exactly with `tech` and `tech_firsts`?
6. **Cause chains.** Every `invention`, `technique_adopted` and `technique_lost` event resolves through `explain.resolvable`.
7. **Speed.** `_reach` and the per-band loop in `_needs`: affordable on a world of 3,000+ bands?

Same format as before (AGENTS.md).
