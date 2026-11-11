# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 10 with institutions on 5 planets, 10 with institutions switched off. Each runs until 2,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | FAIL | G2's checks on these histories: failing: 3. Adoption dates vary widely (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | PASS | chiefdoms in 10 of 10 histories with farming (-271–121 years after the first village); states in 9 (448–1,458 years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.006, 0.25+: 0.033, 0.50+: 0.052, 0.75+: 0.070, 1.00+: 0.093, 1.25+: 0.107, 1.50+: 0.139, 1.75+: 0.153; rank correlation per history: median 0.98 (10 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse happens, and recovery follows | PASS | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 10 of 10 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 178 of 178 collapses (pass: collapses in at least 20% of histories; recovery after at least half. The upper mark of 90% was dropped by Ben's decision of 11 November 2026) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 24 with institutions (17–34), 6 without (5–7, 10 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 5b. How long polities stay large (no mark) | — | longest time one polity held 10+ settlements: median 200 years with institutions (110–430), 0 without (0); polity-years at 10+ settlements per history: median 4,735 with, 0 without |
| 6. Conflict rises with scarcity and proximity | FAIL | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.022, 0.25+: 0.054, 0.50+: 0.068, 0.75+: 0.082; by distance (cells): 0: 0.028, 1: 0.028, 2: 0.002 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.057–0.074 (median 0.067); 80,457 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 5195 empires (polities holding conquered settlements of another language) across the histories; for the 4348 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.21 (pass: clearly negative) |
| 9. Inequality compounds | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median 0.04; with surplus per person: median 0.04; median Gini in a people's first 100 years of farming 0.64 vs after 500 years 0.73 (pass: clearly positive with time (above 0.2), positive with surplus) |
| 10. Traceable | PASS | 8,000 of 8,000 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 1: polities 2,922–4,154, largest 21–32 settlements; planet 2: polities 5,540–8,571, largest 17–20 settlements; planet 3: polities 4,814–4,895, largest 17–21 settlements; planet 4: polities 3,319–5,918, largest 28–31 settlements; planet 5: polities 1,630–1,841, largest 26–34 settlements |
| 12. Speed | — | histories ran 10,680–20,961 years in 0.8–6.4 h of computing (median 1.7 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 10 of 10 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.0–27.8; cause chains complete for 1,093 of 1,093 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | FAIL | planet 1: first farming village in years 10,992–12,464 (spread 1,472), none in 0 of 2; planet 2: first farming village in years 12,579–13,889 (spread 1,310), none in 0 of 2; planet 3: first farming village in years 8,680–9,171 (spread 491), none in 0 of 2; planet 4: first farming village in years 17,938–18,961 (spread 1,023), none in 0 of 2; planet 5: first farming village in years 15,558–16,521 (spread 963), none in 0 of 2. Across all histories: 10,281 years between earliest and latest first village; 0 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 10 of 10 histories with farming, foragers still hold land at the end (429–4624 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 10 of 10 histories; crops or herds raised where they never grew wild in 10 of 10 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.22 (1.14–1.23); people per area, farming ÷ foraging: median 3.1 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 1.00 (0.99–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median 0.04; with surplus per person: median 0.04; median Gini in a people's first 100 years of farming 0.64 vs after 500 years 0.73 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (1,093 of 1,093 references resolved, including deaths) |
| 11. Speed | — | histories ran 10,680–20,961 years in 2981–18036 s of computing (median 6198 s), one history per GitHub machine |
