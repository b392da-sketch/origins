# M0 build notes: decisions, calibration and negative results

5 November 2026. These notes record what was tried while building M0, including what did not work, so later sessions do not repeat it. All numbers are tunable starting values in `origins/params.py`, not measurements.

## Change of sequence: individual-to-group folding moved into M0

The M0 specification put the "about 20,000 individuals" threshold in M1 or later, and estimated that after 2,000 years the population would be "a few hundred to a few thousand". **That estimate was wrong.** With forager demography in plausible ranges (life expectancy at birth around 30, about 4–5 births per woman), a well-fed population with empty land around it grows at roughly 0.5–0.8% a year. In test worlds it passed 20,000 people around year 1,000–1,100 and reached 150,000–240,000 by year 2,000. This is broadly consistent with how quickly real people appear to have spread into new continents, though no historical fit was attempted.

Without folding, 2,000-year runs needed millions of person records and many minutes each, so gate G0 could not run. Folding (approved in Design Draft v0.3) was therefore built now: above 20,000 individuals, the bands farthest from the observer's focus become groups, counts by sex and single year of age that follow the same food, mortality and fertility rules. Followed bands stay individual; following a group recreates named individuals ("unfolding"). Groups are local populations: they split above 200 people (bands split above 50) and groups that share land are combined.

## Calibration history

| Step | Setting | Result | Decision |
|---|---|---|---|
| 1 | First values (conception 0.22/season, lower mortality) | about 3% growth a year; 59,000 people in 270 years; births per woman about 7 | too fast |
| 2 | Siler mortality a1 0.33, b1 1.0, a2 0.012, a3 0.00015, b3 0.085 | life expectancy 32.5, infant mortality 20%, 58% reach 15 | kept |
| 3 | Conception 0.10 → 0.12 → 0.085 per season | births per woman 5.6 → 6.3 → 5.1 | 0.085 kept |
| 4 | Wild food 2.5× seasonal need, regrowth 0.6 | population reached the capacity figure while fully fed: capacity was not a ceiling | rejected |
| 5 | Wild food 1.6×, regrowth 0.55 (break-even at about 0.87 of capacity) | population settles at 70–80% of capacity | kept |
| 6 | Hunger mortality 3.0 × (1 − condition)^2.5 | at the food limit, survival from 15 to 60 only 25–28%; hunger about a quarter of deaths | rejected |
| 7 | Hunger mortality only below condition 0.6; fertility zero below condition 0.5 | no material change (survival 15–60: 29%; hunger 24% of deaths) | **negative result**, kept as part of step 9 |
| 8 | Larger food stores (45 days, 30% spoilage instead of 21 days, 50%) | no material change | **negative result**; kept the larger store as more plausible for foragers but it is not what fixed step 6 |
| 9 | Fertility responds to the band's recent food margin (gathered ÷ needed): full above 1.5, falling to 15% at 1.0 | life expectancy 30.7, births per woman 4.3, survival 15–60 at 38%, hunger 10% of deaths | **kept** |

Diagnosis behind step 9: at the food limit, 90% of groups were well fed; hunger deaths came from a minority stuck in crowded or poor land, where local populations grew at full fertility until food ran out and then crashed. Fertility needed to respond to tightening food before people went hungry, as forager fertility does.

## Event-log volume

Early 2,000-year runs logged about 290,000 group splits, 190,000 group hunger-death records and 105,000 separations. These now go into counters: group splits are people spreading within a local population; separations are counted; group hunger deaths are logged as events only when they exceed 3% of a group in one season. Individual births, deaths and partnerships are stored on the person records and are always explainable.

## Exact replay across machines

Histories are identical when re-run on the same Python and NumPy versions (tested, including different Python hash seeds and save-reload-continue). Across versions they are not guaranteed: Python 3.13/NumPy 2.5 and Python 3.10/NumPy 2.2 gave identical people after 200 years but wild-food totals that differed in the last decimal places, because maths functions such as exponentials differ very slightly between NumPy builds. Over long runs such differences can grow until histories diverge. Saves now record their Python and NumPy versions and show a warning (not an error) when opened under different ones.

## Known limitations of M0

- Groups use one body condition for adults and one for children, a fixed partnered share of women (0.85), and nursing estimated from infant counts. A test checks that birth and death rates match individuals within 15% during growth; agreement at the food limit has not been tested separately.
- Individual bands find partners only among individuals; groups exchange people only by merging.
- The individual threshold folds the bands farthest from the focus (the followed band, or the starting land). After that, much of the world is groups.
- Discovery of land is recorded on the map (who reached it and when) rather than as events.
- No natural hazards other than good and bad years; no technology, culture or language change yet.
- Speed: about 100–135 seconds per 2,000-year history in the build environment. The observatory's fast-forward reaches about 10 simulated years per second while the world is small and slows as it grows.
