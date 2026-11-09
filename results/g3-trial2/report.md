# Gate G3 report — 'scale needs institutions; conflict has causes and costs'

Histories: 20 with institutions on 5 planets, 10 with institutions switched off. Each runs until 3,000 years after its first farming village, or to 30,000 years.

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0-M2 still hold | PASS | G2's checks on these histories: all pass (G2 check 8 needs no-storage histories, not run in G3; G2 check 9 is G3 check 9) |
| 2. Polities form; states in some histories | FAIL | chiefdoms in 15 of 15 histories with farming (-334–-7 years after the first village); states in 0 (none years after) (pass: chiefdoms in at least 80%; states in some but not all) |
| 3. Oversized polities break up | PASS | yearly secession rate per member by overload (load ÷ capacity − 1, in quarters): 0.00+: 0.012, 0.25+: 0.037, 0.50+: 0.057, 0.75+: 0.076, 1.00+: 0.096, 1.25+: 0.115, 1.50+: 0.137, 1.75+: 0.154; rank correlation per history: median 1.00 (15 histories) (pass: clearly positive, and overloaded polities lose members at least twice as often) |
| 4. Collapse in some histories, recovery after it | PASS | at least one collapse (a polity that held 10+ settlements for 50+ years losing half its people within a century) in 13 of 15 histories with chiefdoms; recovery (a polity of at least half that size seated within 4 cells within 1,000 years) after 20 of 20 collapses (pass: collapses in 20–90% of histories; recovery after at least half) |
| 5. No institutions, no large polities | FAIL | largest polity (settlements): median 17 with institutions (14–19), 17 without (14–19, 7 histories with farming); states without institutions: 0 (pass: median under a quarter, no states) |
| 6. Conflict rises with scarcity and proximity | PASS | chance of war per side and neighbour weighed, by scarcity (quarters): 0.00+: 0.022, 0.25+: 0.054, 0.50+: 0.068, 0.75+: 0.076; by distance (cells): 0: 0.029, 1: 0.028, 2: 0.002 (pass: pressed sides at least 1.5 times as warlike as unpressed ones; war falling with each cell of distance). Note: both enter the chance of war by rule, so this checks the bookkeeping; check 8 and the collapse checks test what follows from war |
| 7. Conflict has costs | PASS | deaths in war after the first farming village, as a share of deaths at 15 and over: 0.056–0.072 (median 0.067); 139,426 sampled wars the attacker won, each taking stores, captives or settlements (pass: 2–30%, median 5–25%; plausibility guide 12–16% of adult deaths among foragers, Bowles 2009) |
| 8. Conquest builds empires that are hard to hold | PASS | 6797 empires (polities holding conquered settlements of another language) across the histories; for the 6377 that ended, rank correlation of duration with mean overextension (load ÷ capacity): -0.63 (pass: clearly negative) |
| 10. Traceable | PASS | 12,000 of 12,000 sampled polity events (founding, joining, secession, succession, institutions, tiers) have complete cause chains |
| 11. Same rules, different histories | — | planet 1: polities 11,255–15,279, largest 17–18 settlements; planet 2: polities 11,451–16,801, largest 14–17 settlements; planet 3: polities 8,743–12,156, largest 16–18 settlements; planet 4: polities 8,384–11,616, largest 16–19 settlements; planet 5: polities 5,101, largest 19 settlements |
| 12. Speed | — | histories ran 8,367–30,000 years in 0.6–6.3 h of computing (median 2.4 h) |

## G2 checks on these histories

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 20 of 20 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 26.7–28.0; cause chains complete for 2,175 of 2,175 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | planet 1: first farming village in years 5,367–17,486 (spread 12,119), none in 1 of 4; planet 2: first farming village in years 6,287–14,808 (spread 8,521), none in 0 of 4; planet 3: first farming village in years 9,779–18,986 (spread 9,207), none in 1 of 4; planet 4: first farming village in years 11,173–15,992 (spread 4,819), none in 0 of 4; planet 5: first farming village in years 17,900–17,900 (spread 0), none in 3 of 4. Across all histories: 13,619 years between earliest and latest first village; 5 histories with no farming village by their end (pass: spread of several thousand years and at least one history without farming) |
| 4. Some regions stay foraging | PASS | in 15 of 15 histories with farming, foragers still hold land at the end (278–4628 areas; pass mark 80%) |
| 5. Farming spreads | PASS | number of villages grows after the first in 15 of 15 histories; crops or herds raised where they never grew wild in 15 of 15 |
| 6. Demographic transition | PASS | births per person-year in villages ÷ among foragers (second half of each history): median 1.21 (1.17–1.24); people per area, farming ÷ foraging: median 2.9 (both must exceed 1) |
| 7. Specialists follow surplus | PASS | rank correlation between surplus per person and the share of specialists, across bands and years: median 0.99 (0.96–1.00) (pass: above 0.3). Note: specialists are set from surplus by rule, so this checks the bookkeeping more than it tests a behaviour; check 8 (no storage, no specialists) is the meaningful test |
| 8. No storage, no specialists | FAIL | knock-out histories not run |
| 9. Property and inequality | FAIL | rank correlation of household inequality (Gini) with how long a people has farmed: median -0.16; with surplus per person: median 0.17; median Gini in a people's first 100 years of farming 0.36 vs after 500 years 0.45 (pass: clearly positive with time, positive with surplus) |
| 10. Traceable transition | PASS | every sampled first-tending, first-cultivation, first-domestication and first-village event has a complete cause chain (2,175 of 2,175 references resolved, including deaths) |
| 11. Speed | — | histories ran 8,367–30,000 years in 2275–21156 s of computing (median 8490 s), one history per GitHub machine |
