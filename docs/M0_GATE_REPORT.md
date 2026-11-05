# M0 gate G0 report — "the first people survive"

**Date:** 6 November 2026 · **Founding people:** three neighbouring bands of 30 (Ben's decision, 6 November 2026) · **Result: PASS — M0 closed with Ben's approval, 6 November 2026**

## 1. Result

**All nine checks with a pass mark pass.** The tenth (speed) had no target in the specification and is reported for information.

- **Survival: 100 of 100** histories lived 2,000 years (with one founding band of 30, the earlier gate gave 63 of 100; that report is kept as `M0_GATE_REPORT_single_band.md`).
- **No runaway growth:** population never exceeded 81% of what its occupied land supports.
- **Ups and downs:** every history had populations fall by 5% or more and recover (median 7 times).
- **Plausible demography in every history:** life expectancy at birth 29.8–30.6, births per woman 4.06–4.17, median band size 24–27; 37% of 15-year-olds reach 60; hunger causes 11–14% of deaths.
- **Famine response, 5 of 5:** a three-year 40% cut in wild food (year 1,500, once land had filled) raised hunger deaths in the shocked land (26–980 against 0–25 without the shock) and roughly halved births there; every area was back within 10% of its unshocked twin after 60 years.
- **Spread:** from 2–3 cells to 861–2,612 cells of land; final populations 115,000–330,000.
- **Nothing from nothing:** 0 accounting failures in 100 histories, checked every season.
- **Exact replay:** 4 of 4 save-reload-continue checks identical, plus automated tests.
- **Explainability:** 25,000 of 25,000 sampled deaths and band events have complete cause chains.
- **Speed (no target):** a 2,000-year history takes about 3–11 minutes of computing; median 7.6.

## 2. How it was measured

5 generated planets × 20 histories × 2,000 years on the final code. 78 histories ran in the build environment (Python 3.13, NumPy 2.5) and 22 on Ben's computer (Python 3.10, NumPy 2.2) in checkpointed slices; slicing reproduces an uninterrupted history exactly (tested). Each history is internally consistent within one environment; histories are not claimed to be identical across the two environments (see `M0_BUILD_NOTES.md`). All numbers in `origins/params.py` are tunable starting values, not measurements.

The shock test applies the cut to the most populated land (the cell and two rings around it) in an identical copy of the world and compares the two. Earlier versions of this test, with the shock in year 800 while food was not scarce, and with hunger deaths counted over the whole world, were replaced; both are recorded in the single-band report and the build notes.

## 3. What M0 does not establish

Historical realism or calibration; behaviour beyond 2,000 years (the world has about 48,000 more years of prehistory); agreement between groups and individuals at the food limit (tested only during growth); any hazards other than good and bad years. These belong to later milestones.

## 4. Generated gate table

| Check | Result | Evidence |
|---|---|---|
| 1. Survival | PASS | 100 of 100 runs survived 2,000 years (pass mark 90 of 100). Extinctions: none |
| 2. No explosion | PASS | highest population ÷ capacity of occupied land in any year of any run: 0.811 (must stay ≤ 1.0); median of run maxima 0.757 |
| 3. Fluctuation and recovery | PASS | 100 of 100 surviving runs show at least one population fall of 5% or more (after year 300) that recovers to its earlier peak within 150 years (pass mark 80%); median number of such recoveries per run 7 |
| 4. Plausible demography | PASS | life expectancy at birth 29.8–30.6 (median 30.3; range 25–40); births per woman 4.06–4.17 (median 4.10; range 4–7); median band size 24–27 (range 15–60); survival from 15 to 60: median 0.37. 100 of 100 runs inside all three ranges. |
| 5. Shock response | PASS | shock in year 1500: 5 of 5 paired tests pass. planet 1: hunger deaths in 3 years 26 vs 0 without the shock; births 157 vs 326; area population after 60 years 3257 vs 3180 (recovered within 10%); planet 2: hunger deaths in 3 years 478 vs 13 without the shock; births 184 vs 383; area population after 60 years 2957 vs 3048 (recovered within 10%); planet 3: hunger deaths in 3 years 658 vs 25 without the shock; births 60 vs 144; area population after 60 years 2556 vs 2647 (recovered within 10%); planet 4: hunger deaths in 3 years 321 vs 0 without the shock; births 68 vs 130; area population after 60 years 1463 vs 1444 (recovered within 10%); planet 5: hunger deaths in 3 years 980 vs 8 without the shock; births 126 vs 221; area population after 60 years 3425 vs 3636 (recovered within 10%) |
| 6. Spread begins | PASS | occupied land cells at year 2,000: 861–2612 (median 1490), from 2–3 after the first year |
| 7. Nothing from nothing | PASS | 0 accounting failures in 100 runs (people checked every season against births and deaths; food against regrowth, eating and spoilage) |
| 8. Exact replay | PASS | save, reload and continue identical to uninterrupted run in 4 of 4 checks at year 1,000; also covered by automated tests (reload, and different Python hash seeds) |
| 9. Explainability | PASS | 25000 of 25000 sampled deaths and band events have complete cause chains |
| 10. Speed | — | 2,000 years took 160–654 s (median 456 s) of computing, two histories in parallel (22 histories ran on Ben's computer in checkpointed slices); no target was fixed in the specification |

Final populations at year 2,000: 115,412–329,896 (median 215,382).
Share of all deaths from hunger: 11%–14% (median 12%).

