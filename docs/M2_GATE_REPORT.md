# M2 gate report: "farming is an option, not a destiny"

9 November 2026. For Ben's decision. All rates are tunable starting values (`origins/params.py`), not measurements.

## In short

- **Gate G2** (50 histories with storage on 5 planets and 20 with storage turned off): **9 of the 10 checks with a pass mark pass. Check 9 (property and inequality) fails.**
- **Gate G1 rerun with the final code** (farming off, 75 histories): all 11 checks pass, with check 2 measured against the reachable land as the M1 specification words it. On the old measure check 2 fails (66 of 75; 68 were needed). See `M1_GATE_RERUN3_REPORT.md`.
- **Decisions for you:**
  1. what to do about check 9;
  2. whether the change to check 2's measure stands;
  3. whether M2 closes.

## G2 results

**Runs:** GitHub Actions run 42394703083 (`results/g2-run5`). 10 histories could not continue on a second machine and were rerun in runs 42431949840 (`g2-run5-rerun`) and 42455383342 (`g2-run5-rerun2`).

**How the results were combined** (rule fixed before looking at results): the second rerun is used for every history it covers (planet 4 seeds 1, 2, 5, 6, 9 and 10, planet 5 seed 10, and planet 4 seed 1 without storage), the first rerun for the rest it completed, and the main run for everything else. That gives 70 histories: 50 with storage and 20 without.

**Code:** the gate branch at `46e36b1` (main run), `8c1f944` (first rerun) and `37ee310` (second rerun). Between them only the planet fingerprint, the observatory and event titles changed, so the simulation code is the same in all three. Python 3.13.18 and NumPy 2.5.4 on GitHub; the tests also run on Python 3.10.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 70 of 70 histories survived; 0 accounting failures (people, and food including harvests); life expectancy 27.1–28.7; cause chains complete for 7,678 of 7,678 sampled deaths and farming events |
| 2. Farming needs its conditions | PASS | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 0 |
| 3. Adoption dates vary widely | PASS | first farming village, by planet: 1: years 8,315–19,584; 2: 7,392–15,573; 3: 4,919–22,295; 4: 7,380–23,965; 5: 9,189–24,855. Across all histories 19,936 years between the earliest and latest first village; 2 histories with no farming village by their end |
| 4. Some regions stay foraging | PASS | in 48 of 48 histories with farming, foragers still hold land at the end (344–4,949 areas) |
| 5. Farming spreads | PASS | the number of villages grows after the first in 47 of 48 histories; crops or herds raised where they never grew wild in 48 of 48 |
| 6. Demographic transition | PASS | births per person-year, villages ÷ foragers (second half of each history): median 1.22 (1.05–1.28); people per area, farming ÷ foraging: median 3.3 |
| 7. Specialists follow surplus | PASS | rank correlation of surplus per person with the share of specialists: median 0.99 (0.23–1.00). **This passes by construction**: specialists are set from surplus by rule, so it checks the bookkeeping; check 8 is the real test |
| 8. No storage, no specialists | PASS | 20 histories with storage turned off: no specialists, no household property, so no inequality |
| 9. Property and inequality | **FAIL** | rank correlation of household inequality (Gini) with how long a people has farmed: median −0.05; with surplus per person: median 0.14. Median Gini 0.39 in a people's first 100 years of farming, 0.46 after 500 years |
| 10. Traceable transition | PASS | every sampled first tending, first cultivation, first domestication and first village has a complete cause chain (7,678 of 7,678 references resolved) |
| 11. Speed | (no mark) | histories ran 7,919–25,000 years in 0.6–10.8 hours of computing (median 2.4 h), one history per GitHub machine; the longest are on planet 4 |

## Check 9: what fails, and the options

**Specification (M2 v1, check 9):** "Inequality between households rises with time and surplus where property is inherited."

**What happens:** pooling all 141,463 samples from the first 42 histories (full figures in `M2_BUILD_NOTES.md`), the median Gini is:
- 0.34 in a people's first 50 years of farming;
- 0.45–0.47 from 50 to 500 years;
- falling slowly to 0.40 after 2,000 years, as surplus per person falls (from 89 to 70 days).

So inequality rises over the first century or two, then settles. Within one history it does not keep rising, which is why the correlation with time is near zero. The link with surplus is positive but weak (0.14).

**Why:** yearly luck in the harvest pulls households apart; equal shares to all children and dowries to daughters pull them together; the two balance within a few generations. This is the pattern Borgerhoff Mulder et al. (2009) describe for small-scale societies: inequality settles at a level set by how strongly wealth passes between generations. The long-run rise in house-size inequality across Eurasia after farming began is linked by Kohler et al. (2017) to draft animals and plough farming, which M2 does not model.

**Options:**
- **(a) Close M2 with check 9 recorded as failed** and carried forward. Inequality appears with farming and storage, and is absent without them (check 8); what it does not do is keep growing.
- **(b) Revise check 9** to what the model is meant to show: inequality appears where property is inherited and storage exists, rises over the first generations of farming, and is higher where surplus is higher. On that wording it passes, though the surplus link is weak. This is a change to the approved specification.
- **(c) Add a mechanism that lets advantage compound**, for example households with draft animals farming more land, or land becoming scarce and heritable. Kohler et al. point to exactly this. It is a design change and could be an M2 addition or part of a later milestone; either way G2 would be rerun.

**My view:** (c) is the substantive answer, but it belongs with draft animals and land, which fit a later milestone better than M2. For now I lean to (a), because it keeps the specification as approved and records the gap honestly. (b) would also be defensible, provided the change to the wording is recorded as yours.

## Things found during the gate that you should know

1. **Group movement as approved in M1.** A restriction on group movement tried on 7 November (to save memory) weakened M1's drift of cultures with distance, so it was withdrawn. The memory problem was solved in the records instead: bands that ended long ago are packed into columns, and saves store them that way. Results with packing on and off are identical.

2. **GitHub's machines compute planets slightly differently.** GitHub runs on more than one processor type, and NumPy uses different instructions on each. For planet 4, the continuation logs show:
   - elevation and temperature differ only in the last digits;
   - rainfall differs by up to 188 mm a year in some cells;
   - biome and food capacity differ in 2 of 40,962 cells.

   The likely cause is one step in world generation. Each cell takes its rain from the neighbour most nearly upwind, and when two neighbours are almost exactly as upwind as each other, the last digits decide which one it picks. That choice then carries on downwind. So histories of "planet 4" ran on one of two very slightly different planets, depending on the machine that started them.

   Gate claims are made across histories and do not depend on this, but exact replay holds only on one kind of machine. Since the second rerun, each history saves its planet with its checkpoints and continues on that same planet.

   **Proposed for the next milestone:** make that upwind choice robust (break near-ties by rounding first). It changes every planet, so it should come with the next round of gate runs rather than now.

3. **G1 check 2** was measured against the whole starting land mass; the specification says "reachable" land. Planet 1 has 17% of its food capacity beyond about 900 km of ice that bands cannot walk across. See `M1_GATE_RERUN3_REPORT.md`.

4. **Barren land:** bands never walk into land with no food, so ice and desert are complete barriers on foot. Rare crossings, like the one-cell sea crossings, would be a design change. Not proposed now.

## Open items carried forward

- Island peoples do not diverge faster (from M1).
- Planet 3's drift of cultures with distance is weaker than other planets' (still within the pass mark).
- **Outbreaks:** across whole G2 histories they cause a median 8.4% of deaths (6.1% without storage), against 11.3% for hunger. The earlier figure of 18–20% referred to the farming period alone and was not measured again in this run.
- **Speed:** the longest planet-4 histories need nearly 11 hours of computing, spread over three machines in a row. Big worlds need to be faster before M3.
- Check 7 passes by construction (see above).

## Also built for M2

- **The observatory:**
  - the historical clock (20 years per real day after the first farming village);
  - farming, spread-of-farming and surplus map layers;
  - village pages with crops, stores, specialists and households, and the crops-and-herds panel.

  See `M2_BUILD_NOTES.md`.

- 40 tests pass.

## Sources

- Borgerhoff Mulder, M., Bowles, S., Hertz, T., et al. (2009). Intergenerational wealth transmission and the dynamics of inequality in small-scale societies. *Science*, 326(5953), 682–688. https://doi.org/10.1126/science.1178336
- Kohler, T. A., Smith, M. E., Bogaard, A., et al. (2017). Greater post-Neolithic wealth disparities in Eurasia than in North America and Mesoamerica. *Nature*, 551(7682), 619–622.

## Decision (Ben, 9 November 2026)

- **Check 9: option (a).** M2 closes with check 9 recorded as failed and carried forward. Inequality appears with farming and inherited property, rises over the first generations, then settles; it does not keep growing. Option (c), a mechanism that lets advantage compound (draft animals, scarce heritable land), is planned for a later milestone.
- **G1 check 2:** the measure against reachable land, as the M1 specification words it, stands (Ben accepted Claude's recommendation). On it, G1 passes all 11 checks with the final M2 code.
- **M2 is closed** (Ben's approval, given on Claude's recommendation to close).

Carried forward to the next milestone:
1. Check 9: inequality does not keep growing with time (to be addressed with option (c)).
2. Make world generation's upwind choice robust, so that every machine builds the same planet. This changes every planet, so it comes first, before that milestone's gate runs.
3. Speed of big worlds (planet-4 histories need up to 11 hours of computing).
4. From M1: island peoples do not diverge faster; outbreaks cause about 8% of deaths over whole histories.
5. Bands cannot cross barren land on foot (a possible design change; not proposed).
6. Planet 3's drift with distance is weaker than other planets'.
