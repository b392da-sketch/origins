# Gate G2 report — 'farming is an option, not a destiny'

Histories: 7 with storage on 2 planets (target 50), 1 with storage turned off (target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 8 of 8 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 28.2–28.7; cause chains complete for 895 of 895 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 4: first farming village in years 12,385–23,965 (spread 11,580), none in 1 of 6; planet 5: first farming village in years 10,955–10,955 (spread 0), none in 0 of 1. Across all histories: 13,010 years between earliest and latest first village; 1 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 6 of 6 histories with farming, foragers still hold land at the end (1957–4949 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 6 of 6 histories; crops or herds raised where they never grew wild in 6 of 6 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.18–1.23); people per area, farming ÷ foraging: median 3.6 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.96–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | PASS | 1 histories with storage turned off: specialists recorded 0; household inequality none recorded (no property) |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.01; with surplus per person: median 0.15; median Gini in a people's first 100 years of farming 0.41 vs after 500 years 0.45 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (895 of 895 references resolved, including deaths) |
| 11. Speed | — | histories ran 13,955–25,000 years in 7208–38909 s of computing (median 33654 s), one history per GitHub machine |
