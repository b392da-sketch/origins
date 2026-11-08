# Gate G2 report (merged: main run plus reruns) — 'farming is an option, not a destiny'

Histories: 50 with storage on 5 planets (target 50), 20 with storage turned off (target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 70 of 70 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.1–28.7; cause chains complete for 7,678 of 7,678 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 8,315–19,584 (spread 11,269), none in 0 of 10; planet 2: first farming village in years 7,392–15,573 (spread 8,181), none in 0 of 10; planet 3: first farming village in years 4,919–22,295 (spread 17,376), none in 0 of 10; planet 4: first farming village in years 7,380–23,965 (spread 16,585), none in 1 of 10; planet 5: first farming village in years 9,189–24,855 (spread 15,666), none in 1 of 10. Across all histories: 19,936 years between earliest and latest first village; 2 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 48 of 48 histories with farming, foragers still hold land at the end (344–4949 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 47 of 48 histories; crops or herds raised where they never grew wild in 48 of 48 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.05–1.28); people per area, farming ÷ foraging: median 3.3 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.23–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | PASS | 20 histories with storage turned off: specialists recorded 0; household inequality none recorded (no property) |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.05; with surplus per person: median 0.14; median Gini in a people's first 100 years of farming 0.39 vs after 500 years 0.46 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (7,678 of 7,678 references resolved, including deaths) |
| 11. Speed | — | histories ran 7,919–25,000 years in 2126–38909 s of computing (median 8636 s), one history per GitHub machine |
