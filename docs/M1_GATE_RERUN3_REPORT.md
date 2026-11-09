# Gate G1, third rerun (final M2 code, farming off) — 8 November 2026

**Why:** to confirm that M1 still holds with the code M2 will close on: group movement as approved in M1 (the restriction tried on 7 November is withdrawn), long-ended band records packed into columns, a group never splitting into its own land, and the standing crop travelling with people when groups combine (farming is off here, so that last change has no effect).

**Run:** GitHub Actions run 42394742466, 75 histories (5 planets × 15) of 5,000 years plus the five crowded-world experiments. Results are on the `gate-results` branch under `results/g1-after-band-packing/`. All rates are tunable starting values (`origins/params.py`), not measurements.

## Result

As published by the workflow, 10 of the 11 checks pass and check 2 (spread) fails: 66 of 75 histories hold at least 80% of the starting land mass's food capacity, and 68 were needed. Check 3 (drift with distance), the check the movement restriction had weakened, passes again: 69 of 75 are clearly positive, with a median of 0.46 (0.41 in the earlier passing rerun and 0.38 with the restriction).

## Check 2: what the failure was

All nine histories below 80% are on planet 1. Planet 1's peoples stop spreading at 77–81% of the land mass's food capacity from about year 2,500 onward, and both runs show this plateau: 4 of 15 were below 80% in the earlier passing rerun and 9 of 15 here.

The reason is the planet, not the people. 16.9% of the land mass's food capacity (1,442 cells) lies beyond at least eight cells of ice, about 900 km, and in the model bands never walk into land with no food. That land is also not within one sea cell of the occupied coast, so it cannot be reached by sea either. Only 82.8% of planet 1's capacity can be walked to at all. On the other four planets 99.8–100% can be.

The specification (M1 v1, section 7, check 2) asks that "occupied land keeps growing until the **reachable** land is full". The report had measured against the whole land mass, which does not match that wording. The report now measures against the reachable land: land of the starting land mass that can be walked to through land with food, with land reached by sea counted as before. It prints both measures:

| | Reachable land (as specified) | Whole land mass (as before) |
|---|---|---|
| This rerun | 85–105%, median 97%; ≥80% in **75 of 75** | 78–105%, median 89%; ≥80% in 66 of 75 |
| Earlier passing rerun (store fix) | 85–104%, median 97%; ≥80% in 75 of 75 | 79–104%, median 89%; ≥80% in 70 of 75 |

On the specified measure, check 2 passes and all 11 checks pass. Values above 100% come from occupied islands and other land masses, which count in the numerator as before.

**For Ben:** the change brings the measure into line with the approved wording. Whether that settles check 2 is your call.

Not changed, and an open question for later milestones: bands cannot cross barren land (ice, desert) on foot at all, while real foragers did sometimes cross such country. Allowing rare crossings, like the one-cell sea crossings, would be a design change. It is not proposed here.

## Decision (9 November 2026)

Ben accepted the recommendation: check 2 is measured against the reachable land, as the specification words it. G1 passes all 11 checks with the final M2 code.
