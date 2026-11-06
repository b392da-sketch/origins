# Gate G2, first run (7 November 2026): kept for the record

The first run of gate G2 on GitHub (50 histories + 20 with storage off). Four checks failed; the fixes are in `docs/M2_BUILD_NOTES.md`. Check 6's births measure in this run was faulty (births were counted in whichever land was farmed at each moment, so the numbers are meaningless) and is superseded by the second run.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 and M1 still hold | PASS | 70 of 70 histories survived; 0 accounting failures; life expectancy 26.3–27.4; cause chains complete for 8,806 of 8,806 sampled deaths and farming events |
| 2. Farming needs its conditions | FAIL | tending begun where the species does not grow wild: 0; village-years with nothing to farm: 35,883 (daughter villages founded where their crops could not grow, and unable to move) |
| 3. Adoption dates vary widely | FAIL | first farming village in years 3,014–3,779 across all 50 histories (spread 765 years); every history farmed (the steps to farming were near-certain once land filled) |
| 4. Some regions stay foraging | PASS | in 50 of 50 histories, foragers still hold land at the end (225–2,843 areas) |
| 5. Farming spreads | PASS | villages multiply in 50 of 50; crops raised beyond their wild range in 50 of 50 |
| 6. Demographic transition | not usable | births measure faulty (see above); people per area, farming ÷ foraging: median 3.7 |
| 7. Specialists follow surplus | PASS | rank correlation median 0.99 (true by construction: specialists are set from surplus) |
| 8. No storage, no specialists | PASS | 20 histories with storage off: 0 specialists, no property |
| 9. Property and inequality | FAIL | correlation of household inequality with village age: median 0.11; with surplus: 0.23 (new households started with equal shares, so advantage did not pass down) |
| 10. Traceable transition | PASS | 8,806 of 8,806 references resolved |
| 11. Speed | — | histories of 6,014–6,857 years took 1,365–8,443 s (median 3,532 s) |
