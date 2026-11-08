# Gate G2 report — 'farming is an option, not a destiny'

Histories: 2 with storage on 2 planets (target 50), 2 with storage turned off (target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 4 of 4 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 28.5–28.5; cause chains complete for 445 of 445 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 4: first farming village in years 15,617–15,617 (spread 0), none in 0 of 1; planet 5: first farming village in years 13,669–13,669 (spread 0), none in 0 of 1. Across all histories: 1,948 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 2 of 2 histories with farming, foragers still hold land at the end (2195–4472 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 2 of 2 histories; crops or herds raised where they never grew wild in 2 of 2 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.18 (1.15–1.22); people per area, farming ÷ foraging: median 3.2 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (1.00–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | PASS | 2 histories with storage turned off: specialists recorded 0; household inequality none recorded (no property) |
| 9. Property and inequality | PASS | rank correlation of household inequality (Gini) with how long a people has farmed: median 0.24; with surplus per person: median 0.27; median Gini in a people's first 100 years of farming 0.37 vs after 500 years 0.46 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (445 of 445 references resolved, including deaths) |
| 11. Speed | — | histories ran 16,431–18,617 years in 11189–27843 s of computing (median 13688 s), one history per GitHub machine |
