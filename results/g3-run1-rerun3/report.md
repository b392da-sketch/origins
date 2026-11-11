# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 4 with institutions on 1 planets, 2 with institutions switched off. Each runs until 6,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 4 of 4 histories with farming (-203–-66 years after the first village); states in 2 (933–5,185 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.011, 0.25+: 0.039, 0.50+: 0.058, 0.75+: 0.077, 1.00+: 0.096, 1.25+: 0.112, 1.50+: 0.129, 1.75+: 0.153; rank correlation per history: median 1.00 (4 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse in some histories, recovery after it | FAIL | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 4 of 4 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 13 of 13 collapses (pass: collapses in 20–90% of histories; recovery after at least half) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 19 with institutions (18–20), 20 without (19–20, 2 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | FAIL | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.023, 0.25+: 0.054, 0.50+: 0.066, 0.75+: 0.049; by distance (cells): 0: 0.025, 1: 0.029, 2: 0.003 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.064–0.07 (median 0.070); 27,344 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 2682 empires (polities holding conquered settlements of another language) across the histories; for the 2402 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.53 (pass: clearly negative) |
| 10. Traceable | PASS | 2,400 of 2,400 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 4: polities 21,078–50,471, largest 18–20 settlements |
| 12. Speed | — | histories ran 17,868–30,000 years in 5.0–11.0 h of computing (median 8.8 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 4 of 4 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.8–27.6; cause chains complete for 450 of 450 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 4: first farming village in years 11,868–21,385 (spread 9,517), none in 0 of 4. Across all histories: 9,517 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 4 of 4 histories with farming, foragers still hold land at the end (3823–4736 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 4 of 4 histories; crops or herds raised where they never grew wild in 4 of 4 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.16 (1.15–1.18); people per area, farming ÷ foraging: median 3.9 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.98–0.99) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.04; with surplus per person: median 0.37; median Gini in a people's first 100 years of farming 0.41 vs after 500 years 0.35 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (450 of 450 references resolved, including deaths) |
| 11. Speed | — | histories ran 17,868–27,385 years in 17975–39559 s of computing (median 32343 s), one history per GitHub machine |
