# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 20 with institutions on 5 planets, 10 with institutions switched off. Each runs until 3,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | PASS | G2's checks on these histories: all pass (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | FAIL | chiefdoms in 19 of 19 histories with farming (-332–60 years after the first village); states in 19 (-152–225 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.004, 0.25+: 0.026, 0.50+: 0.045, 0.75+: 0.067, 1.00+: 0.087, 1.25+: 0.109, 1.50+: 0.132, 1.75+: 0.152; rank correlation per history: median 0.99 (19 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse in some histories, recovery after it | FAIL | at least one collapse (a polity of 5+ settlements and 1,000+ people losing half its people within a century) in 19 of 19 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 2685 of 2686 collapses (pass: collapses in 20–90% of histories; recovery after at least half) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 21 with institutions (18–27), 12 without (10–14, 10 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 10. Traceable | PASS | 11,600 of 11,600 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 1: polities 357–2,412, largest 19–23 settlements; planet 2: polities 2,466–4,778, largest 21–24 settlements; planet 3: polities 1,261–2,699, largest 19–27 settlements; planet 4: polities 2,189–3,260, largest 18–22 settlements; planet 5: polities 1,914–2,828, largest 20–22 settlements |
| 12. Speed | — | histories ran 8,466–30,000 years in 0.4–5.3 h of computing (median 1.8 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 20 of 20 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.1–28.8; cause chains complete for 2,184 of 2,184 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 13,849–17,513 (spread 3,664), none in 0 of 4; planet 2: first farming village in years 6,811–11,548 (spread 4,737), none in 0 of 4; planet 3: first farming village in years 5,466–12,551 (spread 7,085), none in 0 of 4; planet 4: first farming village in years 9,267–15,456 (spread 6,189), none in 0 of 4; planet 5: first farming village in years 8,677–10,914 (spread 2,237), none in 1 of 4. Across all histories: 12,047 years between earliest and latest first village; 1 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 19 of 19 histories with farming, foragers still hold land at the end (289–4909 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 19 of 19 histories; crops or herds raised where they never grew wild in 19 of 19 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.14–1.28); people per area, farming ÷ foraging: median 2.8 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.98 (0.83–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.02; with surplus per person: median 0.22; median Gini in a people's first 100 years of farming 0.40 vs after 500 years 0.45 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (2,184 of 2,184 references resolved, including deaths) |
| 11. Speed | — | histories ran 8,466–30,000 years in 1329–19020 s of computing (median 6341 s), one history per GitHub machine |
