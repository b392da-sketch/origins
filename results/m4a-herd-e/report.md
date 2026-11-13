# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 3 with institutions on 3 planets, 0 with institutions switched off. Each runs until 1,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 3 of 3 histories with farming (-248–-83 years after the first village); states in 1 (688 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.007, 0.25+: 0.049, 0.50+: 0.073, 0.75+: 0.101, 1.00+: 0.124, 1.25+: 0.134, 1.50+: 0.198, 1.75+: 0.199; rank correlation per history: median 0.98 (3 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse happens, and recovery follows | FAIL | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 3 of 3 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 0 of 0 collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 20 with institutions (18–25), 0 without (none, 0 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | FAIL | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.023, 0.25+: 0.054, 0.50+: 0.067, 0.75+: 0.071; by distance (cells): 0: 0.026, 1: 0.029, 2: 0.001 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.059–0.073 (median 0.060); 11,958 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 1118 empires (polities holding conquered settlements of another language) across the histories; for the 786 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.29 (pass: clearly negative) |
| 9. Inequality rises with scarce land and herds | FAIL | rank correlation of household inequality (Gini) with land scarcity: median 0.37 (3 histories); with the share of farming in herds: median -0.01 (3); median Gini of farming villages 0.59 (0.57–0.60); with years farmed (no mark): 0.39 (pass: both correlations clearly positive (median above 0.2), and median Gini 0.25-0.55) |
| 10. Traceable | PASS | 1,200 of 1,200 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains; chains of rule that loop at the end of a history: 0 in 3 histories |
| 11. Same rules, different histories | — | planet 1: polities 1,495, largest 18 settlements; planet 4: polities 1,236, largest 20 settlements; planet 5: polities 1,301, largest 25 settlements |
| 12. Speed | — | histories ran 11,356–20,612 years in 1.7–3.0 h of computing (median 2.7 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 3 of 3 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.7–27.9; cause chains complete for 325 of 325 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 1: first farming village in years 12,273–12,273 (spread 0), none in 0 of 1; planet 4: first farming village in years 10,356–10,356 (spread 0), none in 0 of 1; planet 5: first farming village in years 19,612–19,612 (spread 0), none in 0 of 1. Across all histories: 9,256 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 3 of 3 histories with farming, foragers still hold land at the end (1837–5042 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 3 of 3 histories; crops or herds raised where they never grew wild in 3 of 3 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.21 (1.10–1.21); people per area, farming ÷ foraging: median 5.6 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (0.99–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | PASS | rank correlation of household inequality (Gini) with how long a people has farmed: median 0.39; with surplus per person: median 0.05; median Gini in a people's first 100 years of farming 0.29 vs after 500 years 0.61 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (325 of 325 references resolved, including deaths) |
| 11. Speed | — | histories ran 11,356–20,612 years in 5953–10972 s of computing (median 9846 s), one history per GitHub machine |
