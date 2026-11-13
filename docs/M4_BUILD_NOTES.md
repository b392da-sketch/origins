# M4 build notes

All rates are tunable starting values, not measurements.

## 13 November 2026: M3 closed; first M4a steps

- **Merged from branches prepared during the G3 wait:**
  - seats stay individual for 100 years after their polity was last a chiefdom or state (`NOTABLE_MEMORY`);
  - the on-disk event store.

  49 tests pass.

### Circumscription (Carneiro 1970; M4 specification section 2, item 1; Ben's decision 5)

- **The rule:** each year, a member village of a polity (not its seat) takes flight with chance `FLIGHT_RATE` (0.01) × (1 + hunger + overload). It resettles the best open cell within two rings, if there is one. **Open** means:
  - outside every polity;
  - at least `FLIGHT_LAND` (0.7) of home's farming value;
  - farmed below `FLIGHT_OPEN` (0.25) of its capacity.
- **Hemmed in, it cannot leave.** Each flight is a `flight` event with causes. Settlements that answered through a fleeing village now answer to the seat.
- **First trial:** planet 3, from the world saved at year 8,500, to 2,000 years after the first village, with flight off and on.

  | | Flight off | Flight on |
  |---|---|---|
  | First simple chiefdom, years after the first village | −90 | −48 |
  | First complex chiefdom | 51 | 134 |
  | First state | 556 | 775 |
  | Largest polity (settlements) | 26 | 21 |
  | Polity-years as a state | 590 | 210 |
  | Flights | 0 | 1,261 |
  | Flights blocked (hemmed in) | — | 2,827 |
  | Secessions | 4,643 | 4,423 |
  | Conquests | 6,311 | 6,594 |

- **Reading:**
  - Flight works as Carneiro's argument expects: it delays states and shrinks them, and most attempts (69%) are blocked because the land around has filled.
  - But it is a modest brake: about 200 years in this history, against a gap of about 1,500–2,000 years to the historical 2.7–3.1 millennia. One history, so noisy.
  - The specification's other brake is knowledge: writing and administration as techniques to be acquired, not free. It comes with the technology network.
- **Not tuned further:** the literature gives no rate of flight to aim at, and tuning it to hit the historical lag would be tuning to the comparison. The comparison will be made again in G4a, with both brakes in place.

## Seen in passing

`foraging.move` raises a NumPy warning (0/0 in an unused branch of `np.where`, where a neighbour cell has no people and the band no size). It is harmless, because those entries are masked as invalid, but it should be silenced.

### Pastoralism: first GitHub trial (13 November)

Runs 43357881932 (on) and 43357885359 (off): three histories where herding dominated in G3 run 3 (planet 1 seed 5, planet 4 seed 10, planet 5 seed 7), to 1,000 years after the first village. Planet 4 seed 7 was still running. The local test could not be used: planet 4 did not reach farming within a background job's 2-hour limit.

| History | Took up herding (on) | Gini, herding records: on / off | Largest polity: on / off |
|---|---|---|---|
| planet 1 seed 5 | 123 | 0.70 / 0.75 | 16 / 20 |
| planet 4 seed 10 | 476 | 0.45 / 0.73 | 19 / 19 |
| planet 5 seed 7 | 254 | 0.76 / (no herding records: the histories diverged) | 18 / 19 |

- **The mechanism works:** hundreds of peoples took up a herding life.
- **The rules hold:** no accounting failures, every sampled cause chain resolves (including `took_up_herding` and `flight`), and no looping chains of rule.
- **Herding societies are far too unequal:** median Gini 0.45–0.76, against 0.42 for pastoralists (Borgerhoff Mulder et al. 2009). The cause is in the M3 mechanisms carried over: a herd poverty trap below half the village mean, and doubled yearly risk for herds.
- **Calibration against that target,** three variants on GitHub, same three histories:
  - (a) `HERD_RISK` 0.5 (run 43378795580);
  - (b) `HERD_THRESHOLD` 0.25 (run 43378798622);
  - (c) both (run 43378801861).
- **To fix:** the gate record's `herders_alive` counts every living band that ever took up herding, including those that have since gone back to foraging. That is why it can exceed the number of farming bands. It should count current herders.

### Standing crops during seasonal moves (Ben, 13 November 2026)

**Decision: (a) for now, (c) later.** A band's standing crop (`crop_store`) travels with it and is harvested wherever the band is at harvest. This is accepted and documented as an abstraction. It matters little for herders, who by definition get at least 70% of their farming value from animals.

**Later (c):** a band harvests its standing crop only if it is back on the cell where it sowed. Raised by Codex in review 005.

### Herd inequality calibration, round 1 (13 November)

Median Gini of herding records, against a target of 0.42 for pastoralists (Borgerhoff Mulder et al. 2009):

| Variant | Planet 1 seed 5 | Planet 4 seed 10 | Planet 5 seed 7 |
|---|---|---|---|
| base (`HERD_RISK` 1, `HERD_THRESHOLD` 0.5) | 0.70 | 0.45 | 0.76 |
| (a) `HERD_RISK` 0.5 | 0.68 | 0.44 | 0.75 |
| (b) `HERD_THRESHOLD` 0.25 | 0.69 | 0.41 | no herders (the history diverged) |
| (c) both | 0.68 | 0.43 | 0.74 |

**Neither setting is the driver.** Looking inside the records:
- **The high values come where herding land is crowded.** Land counts as scarce in 71% and 86% of herding records on planets 1 and 5, against 6% on planet 4. Pasture carries few people per area, so it fills fast, and the M3 land advantage, meant for heritable fields, then pulls richer households ahead.
- **Even with no crowding, herding records reach 0.60–0.61,** against 0.31 for crop villages (planet 3). The likely driver is the herd poverty trap itself: `HERD_GROWTH` (0.02 a year, gained above the threshold and lost below it) splits households within a generation, whatever the threshold.

**Round 2,** on the code with review 005's fixes, same three histories:
- (d) `HERD_GROWTH` 0.005 (run 43405965189);
- (e) `LAND_HERDS` 0: no land advantage on pasture, as if pasture were held in common (run 43405970426);
- (f) both (run 43405974869).

Whether pasture is held in common is a design assumption, and goes to Ben with the results.
