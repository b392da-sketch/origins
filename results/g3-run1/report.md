# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 44 with institutions on 5 planets, 18 with institutions switched off. Each runs until 6,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 1. M0 and M1 still hold; 10. Traceable transition (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 42 of 42 histories with farming (-282–-4 years after the first village); states in 34 (219–5,492 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.012, 0.25+: 0.039, 0.50+: 0.057, 0.75+: 0.076, 1.00+: 0.093, 1.25+: 0.111, 1.50+: 0.128, 1.75+: 0.147; rank correlation per history: median 1.00 (42 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse in some histories, recovery after it | FAIL | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 42 of 42 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 309 of 309 collapses (pass: collapses in 20–90% of histories; recovery after at least half) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 20 with institutions (17–34), 18 without (17–20, 17 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.018, 0.25+: 0.052, 0.50+: 0.065, 0.75+: 0.060; by distance (cells): 0: 0.029, 1: 0.026, 2: 0.003 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.052–0.07 (median 0.059); 321,484 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 29542 empires (polities holding conquered settlements of another language) across the histories; for the 26602 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.48 (pass: clearly negative) |
| 10. Traceable | PASS | 24,800 of 24,800 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 1: polities 11,971–42,490, largest 18–22 settlements; planet 2: polities 29,080–50,751, largest 18–22 settlements; planet 3: polities 18,135–28,898, largest 17–28 settlements; planet 4: polities 22,298–40,804, largest 17–23 settlements; planet 5: polities 9,902–37,918, largest 18–34 settlements |
| 12. Speed | — | histories ran 12,079–30,000 years in 1.3–8.4 h of computing (median 3.4 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | FAIL | 44 of 44 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.2–27.8; cause chains complete for 4,832 of 4,833 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 6,440–24,775 (spread 18,335), none in 0 of 9; planet 2: first farming village in years 6,079–15,537 (spread 9,458), none in 0 of 10; planet 3: first farming village in years 7,072–19,688 (spread 12,616), none in 0 of 10; planet 4: first farming village in years 11,118–21,385 (spread 10,267), none in 1 of 5; planet 5: first farming village in years 12,036–23,600 (spread 11,564), none in 1 of 10. Across all histories: 18,696 years between earliest and latest first village; 2 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 42 of 42 histories with farming, foragers still hold land at the end (242–4717 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 42 of 42 histories; crops or herds raised where they never grew wild in 42 of 42 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.12–1.28); people per area, farming ÷ foraging: median 3.9 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.96 (0.76–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.00; with surplus per person: median 0.24; median Gini in a people's first 100 years of farming 0.36 vs after 500 years 0.40 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | FAIL | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (4,832 of 4,833 references resolved, including deaths) |
| 11. Speed | — | histories ran 12,079–30,000 years in 4672–30225 s of computing (median 12093 s), one history per GitHub machine |
