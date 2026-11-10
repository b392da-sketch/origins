# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 1 with institutions on 1 planets, 0 with institutions switched off. Each runs until 6,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | FAIL | chiefdoms in 1 of 1 histories with farming (193 years after the first village); states in 0 (none years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.012, 0.25+: 0.039, 0.50+: 0.056, 0.75+: 0.073, 1.00+: 0.091, 1.25+: 0.109, 1.50+: 0.129, 1.75+: 0.146; rank correlation per history: median 1.00 (1 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse in some histories, recovery after it | FAIL | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 1 of 1 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 0 of 0 collapses (pass: collapses in 20–90% of histories; recovery after at least half) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 20 with institutions (20), 0 without (none, 0 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.019, 0.25+: 0.049, 0.50+: 0.062, 0.75+: 0.061; by distance (cells): 0: 0.028, 1: 0.026, 2: 0.004 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.063 (median 0.063); 5,475 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 566 empires (polities holding conquered settlements of another language) across the histories; for the 519 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.58 (pass: clearly negative) |
| 10. Traceable | PASS | 400 of 400 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 1: polities 45,770, largest 20 settlements |
| 12. Speed | — | histories ran 24,955–24,955 years in 4.3–4.3 h of computing (median 4.3 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 1 of 1 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.9–26.9; cause chains complete for 111 of 111 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 1: first farming village in years 18,955–18,955 (spread 0), none in 0 of 1. Across all histories: 0 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 1 of 1 histories with farming, foragers still hold land at the end (808–808 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 1 of 1 histories; crops or herds raised where they never grew wild in 1 of 1 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.17 (1.17–1.17); people per area, farming ÷ foraging: median 5.6 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.92 (0.92–0.92) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.07; with surplus per person: median 0.25; median Gini in a people's first 100 years of farming 0.28 vs after 500 years 0.25 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (111 of 111 references resolved, including deaths) |
| 11. Speed | — | histories ran 24,955–24,955 years in 15573–15573 s of computing (median 15573 s), one history per GitHub machine |
