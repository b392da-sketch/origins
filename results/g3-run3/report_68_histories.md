# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 50 with institutions on 5 planets, 18 with institutions switched off. Each runs until 6,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | PASS | G2's checks on these histories: all pass (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 47 of 47 histories with farming (-451–711 years after the first village); states in 40 (305–5,571 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.006, 0.25+: 0.033, 0.50+: 0.052, 0.75+: 0.070, 1.00+: 0.089, 1.25+: 0.111, 1.50+: 0.137, 1.75+: 0.162; rank correlation per history: median 0.99 (47 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse happens, and recovery follows | PASS | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 47 of 47 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 705 of 712 collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 24 with institutions (18–38), 6 without (6–8, 17 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 5b. How long polities stay large (no mark) | — | longest time one polity held 10+ settlements: median 230 years with institutions (90–920), 0 without (0); polity-years at 10+ settlements per history: median 12,190 with, 0 without |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.019, 0.25+: 0.053, 0.50+: 0.066, 0.75+: 0.063; by distance (cells): 0: 0.028, 1: 0.027, 2: 0.003 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.057–0.085 (median 0.069); 288,849 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 58289 empires (polities holding conquered settlements of another language) across the histories; for the 53962 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.35 (pass: clearly negative) |
| 9. Inequality rises with scarce land and herds | FAIL | rank correlation of household inequality (Gini) with land scarcity: median 0.32 (47 histories); with the share of farming in herds: median 0.01 (43); median Gini of farming villages 0.40 (0.23–0.84); with years farmed (no mark): -0.10 (pass: both correlations clearly positive (median above 0.2), and median Gini 0.25-0.55) |
| 10. Traceable | FAIL | 27,200 of 27,200 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains; chains of rule that loop at the end of a history: 1 in 68 histories |
| 11. Same rules, different histories | — | planet 1: polities 9,599–22,867, largest 18–38 settlements; planet 2: polities 19,514–33,242, largest 18–36 settlements; planet 3: polities 3,871–16,953, largest 18–28 settlements; planet 4: polities 4,811–29,969, largest 19–32 settlements; planet 5: polities 1,945–18,458, largest 20–31 settlements |
| 12. Speed | — | histories ran 9,983–30,000 years in 1.0–9.9 h of computing (median 3.0 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 50 of 50 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 25.8–28.0; cause chains complete for 5,517 of 5,517 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 9,640–20,034 (spread 10,394), none in 2 of 10; planet 2: first farming village in years 7,484–22,382 (spread 14,898), none in 0 of 10; planet 3: first farming village in years 3,983–28,512 (spread 24,529), none in 0 of 10; planet 4: first farming village in years 8,922–27,577 (spread 18,655), none in 1 of 10; planet 5: first farming village in years 13,202–28,003 (spread 14,801), none in 0 of 10. Across all histories: 24,529 years between earliest and latest first village; 3 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 47 of 47 histories with farming, foragers still hold land at the end (222–4812 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 47 of 47 histories; crops or herds raised where they never grew wild in 47 of 47 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.08–1.28); people per area, farming ÷ foraging: median 3.9 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (0.98–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.10; with surplus per person: median 0.08; median Gini in a people's first 100 years of farming 0.31 vs after 500 years 0.40 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (5,517 of 5,517 references resolved, including deaths) |
| 11. Speed | — | histories ran 9,983–30,000 years in 3647–35715 s of computing (median 12084 s), one history per GitHub machine |
