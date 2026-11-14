# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 5 with institutions on 5 planets, 0 with institutions switched off. Each runs until 2,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | FAIL | chiefdoms in 5 of 5 histories with farming (-209–-49 years after the first village); states in 5 (422–1,953 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.006, 0.25+: 0.045, 0.50+: 0.071, 0.75+: 0.097, 1.00+: 0.122, 1.25+: 0.153, 1.50+: 0.190, 1.75+: 0.224; rank correlation per history: median 0.99 (5 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse happens, and recovery follows | PASS | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 5 of 5 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 114 of 119 collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 24 with institutions (22–30), 0 without (none, 0 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.006, 0.25+: 0.027, 0.50+: 0.036, 0.75+: 0.026; by distance (cells): 0: 0.018, 1: 0.014, 2: 0.001 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | FAIL | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.04–0.049 (median 0.041); 25,872 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 14242 empires (polities holding conquered settlements of another language) across the histories; for the 11760 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.36 (pass: clearly negative) |
| 9. Inequality rises with scarce land and herds | FAIL | rank correlation of household inequality (Gini) with land scarcity: median 0.10 (5 histories); with the share of farming in herds: median -0.11 (5); median Gini of farming villages 0.50 (0.49–0.76); with years farmed (no mark): 0.05 (pass: both correlations clearly positive (median above 0.2), and median Gini 0.25-0.55) |
| 10. Traceable | PASS | 2,000 of 2,000 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains; chains of rule that loop at the end of a history: 0 in 5 histories |
| 11. Same rules, different histories | — | planet 1: polities 13,439, largest 24 settlements; planet 2: polities 13,249, largest 30 settlements; planet 4: polities 63,449, largest 22 settlements; planet 5: polities 24,119, largest 22 settlements; planet 6: polities 22,572, largest 30 settlements |
| 12. Speed | — | histories ran 10,117–17,848 years in 1.7–9.6 h of computing (median 4.0 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 5 of 5 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.8–27.5; cause chains complete for 565 of 565 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 1: first farming village in years 13,414–13,414 (spread 0), none in 0 of 1; planet 2: first farming village in years 8,117–8,117 (spread 0), none in 0 of 1; planet 4: first farming village in years 9,089–9,089 (spread 0), none in 0 of 1; planet 5: first farming village in years 15,848–15,848 (spread 0), none in 0 of 1; planet 6: first farming village in years 14,441–14,441 (spread 0), none in 0 of 1. Across all histories: 7,731 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 5 of 5 histories with farming, foragers still hold land at the end (580–3395 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 5 of 5 histories; crops or herds raised where they never grew wild in 5 of 5 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.15 (1.11–1.19); people per area, farming ÷ foraging: median 6.4 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (0.99–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median 0.05; with surplus per person: median 0.06; median Gini in a people's first 100 years of farming 0.35 vs after 500 years 0.50 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (565 of 565 references resolved, including deaths) |
| 11. Speed | — | histories ran 10,117–17,848 years in 6053–34472 s of computing (median 14413 s), one history per GitHub machine |
