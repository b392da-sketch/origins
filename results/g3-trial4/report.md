# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 4 with institutions on 2 planets, 3 with institutions switched off. Each runs until 1,500 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 4 of 4 histories with farming (-228–-26 years after the first village); states in 3 (616–876 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.006, 0.25+: 0.034, 0.50+: 0.051, 0.75+: 0.071, 1.00+: 0.090, 1.25+: 0.112, 1.50+: 0.145, 1.75+: 0.172; rank correlation per history: median 0.98 (4 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse happens, and recovery follows | PASS | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 4 of 4 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 25 of 25 collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 20 with institutions (17–28), 6 without (6–7, 3 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 5b. How long polities stay large (no mark) | — | longest time one polity held 10+ settlements: median 120 years with institutions (80–160), 0 without (0); polity-years at 10+ settlements per history: median 3,280 with, 0 without |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.018, 0.25+: 0.050, 0.50+: 0.064, 0.75+: 0.074; by distance (cells): 0: 0.032, 1: 0.025, 2: 0.002 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.055–0.069 (median 0.061); 28,231 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 2071 empires (polities holding conquered settlements of another language) across the histories; for the 1651 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.20 (pass: clearly negative) |
| 9. Inequality rises with scarce land and herds | FAIL | rank correlation of household inequality (Gini) with land scarcity: median 0.23 (4 histories); with the share of farming in herds: median 0.01 (4); median Gini of farming villages 0.65 (0.62–0.74); with years farmed (no mark): -0.03 (pass: both correlations clearly positive (median above 0.2), and median Gini 0.25-0.55) |
| 10. Traceable | PASS | 2,800 of 2,800 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 2: polities 4,208, largest 22 settlements; planet 3: polities 2,571–3,624, largest 17–28 settlements |
| 12. Speed | — | histories ran 9,437–18,503 years in 0.6–0.8 h of computing (median 0.8 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 4 of 4 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.3–27.6; cause chains complete for 429 of 429 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 2: first farming village in years 7,937–7,937 (spread 0), none in 0 of 1; planet 3: first farming village in years 8,680–17,003 (spread 8,323), none in 0 of 3. Across all histories: 9,066 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 4 of 4 histories with farming, foragers still hold land at the end (478–1355 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 4 of 4 histories; crops or herds raised where they never grew wild in 4 of 4 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.23 (1.22–1.23); people per area, farming ÷ foraging: median 2.7 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (0.99–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.03; with surplus per person: median 0.04; median Gini in a people's first 100 years of farming 0.48 vs after 500 years 0.63 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (429 of 429 references resolved, including deaths) |
| 11. Speed | — | histories ran 9,437–18,503 years in 2180–3036 s of computing (median 2755 s), one history per GitHub machine |
