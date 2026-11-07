# Gate G2 report — 'farming is an option, not a destiny'

Histories: 38 with storage on 4 planets (target 50), 10 with storage turned off (target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 48 of 48 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.7–28.7; cause chains complete for 5,284 of 5,284 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 4,901–15,151 (spread 10,250), none in 1 of 10; planet 2: first farming village in years 6,294–17,318 (spread 11,024), none in 0 of 10; planet 3: first farming village in years 4,884–17,400 (spread 12,516), none in 0 of 10; planet 5: first farming village in years 7,303–14,338 (spread 7,035), none in 0 of 8. Across all histories: 12,516 years between earliest and latest first village; 1 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 37 of 37 histories with farming, foragers still hold land at the end (397–3096 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 37 of 37 histories; crops or herds raised where they never grew wild in 37 of 37 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.23 (1.07–1.27); people per area, farming ÷ foraging: median 3.6 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.53–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | PASS | 10 histories with storage turned off: specialists recorded 0; household inequality none recorded (no property) |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.10; with surplus per person: median 0.23; median Gini in a people's first 100 years of farming 0.41 vs after 500 years 0.45 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (5,284 of 5,284 references resolved, including deaths) |
| 11. Speed | — | histories ran 7,884–25,000 years in 1041–10020 s of computing (median 4089 s), one history per GitHub machine |
