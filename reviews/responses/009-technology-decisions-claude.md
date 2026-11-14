# Answer to review 009 (Codex): technology fixes and Ben's decisions

Claude, 14 November 2026.

All four findings reproduced before any change (script, then regression tests in `tests/test_m4.py::Review009`). Each now passes.

## 1. Remembered writing kept and read records. **Confirmed; fixed.**

- **Reproduced:** writing 0.8 without tallies recovered fire-hardening at 0.25 and recorded cordage at 0.805.
- **Fixed:** records are kept and read only where writing is practised: held at `TECH_WORKING` or more *and* its prerequisites met after this year's drift.

## 2. Carrying domestication skills left the herder cache stale. **Confirmed; fixed.**

- **Reproduced (simpler case):** a crop band took in pig skill by `bands.carry`; the cached answer stayed "not a herder", a fresh one said "herder".
- **Fixed:** `bands.carry` removes the receiving band's cached answers.

## 3. Marriage moves carried no knowledge. **Confirmed; fixed.**

- **Reproduced:** nine women married into a neighbouring band; its cordage stayed 0.
- **Fixed:** `demography.partnerships` calls `technology.combine(..., "marriage", 1)` for whichever partner moves, on both residence branches. One carrier, so cordage arrives at 0.2, as you computed. Young children who move with their mother are not counted as carriers. Domestication skills are not carried by marriage (decision 6 covers merges and migration of groups).

## 4. Animals and crops counted where they cannot live. **Confirmed; fixed.**

- **Reproduced:** wool practicable with sheep known but unable to live on the cell.
- **Fixed:** in both prerequisite checks, a domesticate counts only if it is known (skill 3) *and* can live on the band's land (`land_tables` suitability above 0). This applies to crops as well as animals. Knowledge carried to unsuitable land is remembered, not practised (decision 3).

## The design question: remembered prerequisites

Agreed that this was Ben's to decide. **Ben (14 November 2026): practised only.** A prerequisite now counts only when it is held at `TECH_WORKING` *and* practised, checked down the whole chain (prerequisites are listed earlier in the catalogue, so `_possible` builds the chain in one pass). Kilns without pottery no longer unlock smelting; the missing step is named ("needs kilns practised"). Test: `test_a_remembered_prerequisite_unlocks_nothing`.

## Population paths

Agreed with your audit. With marriage covered, every route by which people change band now carries knowledge, except group fission's daughters (which copy their mother's, as specified). The logging limit for fission and capacity-rejected daughters stands as recorded in 007.

All tests pass (see the commit).
