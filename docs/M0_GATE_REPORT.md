# M0 gate G0 report — "the first people survive"

**Date:** 6 November 2026 · **Code:** this folder's latest commit · **Decision needed from Ben:** yes (section 3)

## 1. Result

**G0 does not pass as written: 7 of the 10 checks pass, 2 fail, and 1 (speed) had no fixed target.**

- **Passes:** no runaway growth; populations rise and fall and recover; demography inside every plausible range; spread from one band to 864–2,483 cells of land; zero accounting failures in 100 runs; exact replay; every sampled death and band event has a complete cause chain.
- **Fails, check 1 (survival): 63 of 100 histories survived 2,000 years against a pass mark of 90.** Every one of the 37 extinctions has the same signature: the founding band never grew beyond one band (peak 29–49 people), with no hunger and food fully available. An isolated band of 30 runs out of partners who are not siblings or half-siblings within a generation or two, and there is nobody else in the world to marry. Every history that reached two bands survived to year 2,000.
- **Fails narrowly, check 5 (shock): 4 of 5 paired tests pass.** In the fifth (planet 1), the shocked land's births fell by a third and bands moved away, but there were no hunger deaths there; the spec's test asks for both more hunger deaths and fewer births. Every shocked area recovered to within 10% of its unshocked twin after 60 years.
- **Speed:** a 2,000-year history took 87–568 seconds (median 311) in the build environment, two at a time. Histories that die out early finish in seconds.

## 2. What the gate measured

5 generated planets × 20 histories × 2,000 years, run on the final code (Python 3.13, NumPy 2.5), with planet and history seeds producing independent random streams. The shock test cut wild food by 40% for three years in the most populated land (the cell and two rings around it) in year 1,500, once land had filled, and compared it with an identical copy of the world left alone. All numbers in `origins/params.py` are tunable starting values, not measurements.

An earlier attempt at this gate was stopped and discarded because its histories were not independent between planets (see `M0_BUILD_NOTES.md`). An earlier version of the shock test, in year 800, could not test anything because food was not yet scarce, and its first rerun counted hunger deaths and births over the whole world instead of the shocked land; both are recorded below rather than hidden.

## 3. Decision for Ben

The failure of check 1 comes from the founding scenario, which is your design decision, not from food, climate or a bug. Options:

| Option | What changes | Evidence |
|---|---|---|
| **A. Several founding bands (recommended)** | The world begins with, say, three bands of 30 in neighbouring land: one people rather than one family group | With three bands, **0 of 40** histories died out in 600 years on the two planets where single bands fared worst (15 of 40 died out with one band). Already built as the setting `FOUNDING_BANDS`; default still 1. |
| B. One larger band | e.g. one band of 60–90 | Not yet tested; it would split into two bands quickly, which is what protects survival. |
| C. Keep one band of 30, lower the pass mark | Accept that roughly a third of worlds end early, as a small isolated founding group might; the observer starts another | Honest, but a third of worlds ending in the first few centuries may be frustrating to watch. |
| D. New social mechanisms | e.g. more than one partner, adoption of orphans, bands visiting and fusing | Each is a design choice about these societies; none tested. |

For check 5: accept that moving away and having fewer children is a valid response to famine (planet 1), or keep the strict wording and treat it as a fail.

If you choose A, the gate would be rerun with that founding setting before M0 is closed.

## 4. Generated gate table

| Check | Result | Evidence |
|---|---|---|
| 1. Survival | FAIL | 63 of 100 runs survived 2,000 years (pass mark 90 of 100). Extinctions: planet 1 history 10 in year 431, planet 1 history 11 in year 389, planet 1 history 14 in year 293, planet 1 history 3 in year 217, planet 1 history 9 in year 166, planet 2 history 10 in year 309, planet 2 history 11 in year 383, planet 2 history 15 in year 251, planet 2 history 20 in year 432, planet 2 history 2 in year 407, planet 2 history 4 in year 145, planet 2 history 5 in year 120, planet 2 history 6 in year 565, planet 2 history 8 in year 209, planet 2 history 9 in year 393, planet 3 history 10 in year 189, planet 3 history 15 in year 581, planet 3 history 1 in year 196, planet 3 history 3 in year 254, planet 3 history 5 in year 185, planet 4 history 15 in year 196, planet 4 history 16 in year 209, planet 4 history 17 in year 214, planet 4 history 1 in year 158, planet 4 history 20 in year 330, planet 4 history 6 in year 317, planet 4 history 7 in year 218, planet 5 history 16 in year 97, planet 5 history 18 in year 269, planet 5 history 1 in year 240, planet 5 history 20 in year 222, planet 5 history 3 in year 230, planet 5 history 4 in year 192, planet 5 history 8 in year 123, planet 5 history 9 in year 218 |
| 2. No explosion | PASS | highest population ÷ capacity of occupied land in any year of any run: 0.796 (must stay ≤ 1.0); median of run maxima 0.757 |
| 3. Fluctuation and recovery | PASS | 63 of 63 surviving runs show at least one population fall of 5% or more (after year 300) that recovers to its earlier peak within 150 years (pass mark 80%); median number of such recoveries per run 8 |
| 4. Plausible demography | PASS | life expectancy at birth 29.9–30.9 (median 30.4; range 25–40); births per woman 4.09–4.33 (median 4.13; range 4–7); median band size 25–28 (range 15–60); survival from 15 to 60: median 0.37. 63 of 63 runs inside all three ranges. |
| 5. Shock response | FAIL | shock in year 1500: 4 of 5 paired tests pass. planet 1: hunger deaths in 3 years 0 vs 0 without the shock; births 225 vs 334; area population after 60 years 1560 vs 1556 (recovered within 10%); planet 2: hunger deaths in 3 years 192 vs 6 without the shock; births 164 vs 335; area population after 60 years 2922 vs 2738 (recovered within 10%); planet 3: hunger deaths in 3 years 333 vs 0 without the shock; births 88 vs 182; area population after 60 years 1544 vs 1583 (recovered within 10%); planet 4: hunger deaths in 3 years 474 vs 221 without the shock; births 80 vs 170; area population after 60 years 2592 vs 2555 (recovered within 10%); planet 5: hunger deaths in 3 years 190 vs 0 without the shock; births 192 vs 337; area population after 60 years 3102 vs 3353 (recovered within 10%) (An earlier version of this test, with the shock in year 800 while land was still mostly empty, produced 0 hunger deaths in 5 pairs: food was not scarce, so it could not test the response and was replaced by this one.) |
| 6. Spread begins | PASS | occupied land cells at year 2,000: 864–2483 (median 1332), from 1 at the start |
| 7. Nothing from nothing | PASS | 0 accounting failures in 100 runs (people checked every season against births and deaths; food against regrowth, eating and spoilage) |
| 8. Exact replay | PASS | save, reload and continue identical to uninterrupted run in 2 of 2 checks at year 1,000; also covered by automated tests (reload, and different Python hash seeds) |
| 9. Explainability | PASS | 19437 of 19437 sampled deaths and band events have complete cause chains |
| 10. Speed | — | 2,000 years took 87–568 s (median 311 s) in this test environment, two runs in parallel; the target was to be fixed once the first version existed |

Final populations at year 2,000: 120,492–321,501 (median 173,851).
Share of all deaths from hunger: 10%–14% (median 12%).

