# Gate G2 report — 'farming is an option, not a destiny'

Histories: 42 with storage on 5 planets (target 50), 17 with storage turned off (target 20). Each runs until 3,000 years after its first farming village, or to 25,000 years.

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 59 of 59 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.3–28.9; cause chains complete for 6,453 of 6,453 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 5,524–19,257 (spread 13,733), none in 2 of 10; planet 2: first farming village in years 6,243–12,695 (spread 6,452), none in 0 of 10; planet 3: first farming village in years 5,998–21,212 (spread 15,214), none in 0 of 10; planet 4: first farming village in years 4,385–7,722 (spread 3,337), none in 0 of 3; planet 5: first farming village in years 9,691–18,501 (spread 8,810), none in 0 of 9. Across all histories: 16,827 years between earliest and latest first village; 2 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 40 of 40 histories with farming, foragers still hold land at the end (543–5028 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 40 of 40 histories; crops or herds raised where they never grew wild in 40 of 40 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.23 (1.06–1.26); people per area, farming ÷ foraging: median 3.0 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.88–1.00) (pass: above 0.3) |
| 8. No storage, no specialists | PASS | 17 histories with storage turned off: specialists recorded 0; household inequality none recorded (no property) |
| 9. Property and inequality | FAIL | rank correlation of household inequality with the age of the village: median 0.08; with surplus per person: median 0.18 (pass: clearly positive with age, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (6,453 of 6,453 references resolved, including deaths) |
| 11. Speed | — | histories ran 7,385–25,000 years in 1936–19552 s of computing (median 8858 s), one history per GitHub machine |
