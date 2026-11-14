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

### Herd inequality calibration, round 2 (14 November)

On the code with review 005's fixes; median Gini of herding records, with the value where land is not crowded in brackets. Target 0.42 (pastoralists, Borgerhoff Mulder et al. 2009).

| Variant | Planet 1 seed 5 | Planet 4 seed 10 | Planet 5 seed 7 |
|---|---|---|---|
| (d) `HERD_GROWTH` 0.005 | 0.74 (0.50) | 0.55 (0.46) | 0.76 (0.49) |
| (e) `LAND_HERDS` 0 | 0.60 (0.56) | 0.57 (0.50) | no herders (the history diverged; crop villages 0.59) |
| **(f) both** | **0.49 (0.49)** | **0.49 (0.45)** | **0.50 (0.48)** |

- **Only (f) brings all three to the same level,** 0.49–0.50. That is still above 0.42, but near the 0.48 for agriculturalists in the same study. Every sampled cause chain resolves in all variants.
- **Planet 4 seed 7** never reached a farming village in either run (pastoralism on and off), so it adds nothing.

**The design question, for Ben.** (f) includes `LAND_HERDS` 0: pasture held in common, so crowding gives the richer households no extra land, while herds stay private property.
- **Literature:** Fratkin and Mearns (2003) describe exactly that combination:
  - in Mongolia, "pastureland is constitutionally excluded from private ownership" and herders "continue to herd their animals on common pastures", with "public ownership of pastureland, combined with private ownership of livestock";
  - in traditional Maasai society, "no individual 'owned' grazing or water resources". Privatisation came later.

  These are two cases, not a survey of all pastoral societies.
- **Recommended:** (f), recorded as Ben's decision if he agrees. It is not set in `params.py` until then.

### Source (added)

- Fratkin, E., & Mearns, R. (2003). Sustainability and pastoral livelihoods: Lessons from East African Maasai and Mongolia. *Human Organization*, 62(2), 112–122.

**Decision (Ben, 14 November 2026): (f) is set.** Pasture is held in common and herds privately (`LAND_HERDS` 0), with herds growing and shrinking by 0.5% a year around the poverty-trap line (`HERD_GROWTH` 0.005).

### The cause-chain validator follows whole chains (carried forward from M3; 14 November)

`explain.resolvable` now follows every reference in a chain once each, iteratively, with no depth limit. A chain larger than 200,000 references counts as unresolved, so a gate cannot pass on a chain it did not finish.

- **Measured** on the planet-3 farming world: polity and war chains have a median of 2 references and a maximum of 11, so the old limit of 6 did cut some of them.
- **Speed:** 400 sampled deaths and 400 sampled polity and farming events are checked in about 0.1 s.
- **Still sampled:** the check samples events; it does not cover every event in a history.

## The technology network, stages 1–4 (14 November 2026)

Built in `origins/sim/technology.py`: 27 techniques with prerequisites (stage 1), invention from need, materials and connected population (stage 2), keeping and losing skills after Henrich (2004) (stage 3), and spreading by contact (stage 4). Techniques do not yet change anything else; effects are stage 5. Every number below comes from starting values in `params.py`, which are tunable, not facts.

All trials start from the planet-3 snapshot at year 8,500 and run 1,500 years.

### Trial 1: invention only

1,840 inventions: far too many. Hard techniques were invented as readily as easy ones.

**Change:** a difficulty factor, `(TECH_EASY_KEEP / keep) ** TECH_DIFFICULTY`, so techniques that need more practitioners are rarer inventions; base rate cut to 5e-6; tribute pressure set by polity tier only.

### Trial 2: invention only, after the change

97 inventions. Simple techniques were invented many times (cordage 46, fire-hardened points 32), harder ones rarely (canoes 3, terracing 3, irrigation 1, stone building 1). No writing, metals or plough. Cause chains 97 of 97.

### Trial 3: all four stages

29 inventions, 16,174 adoptions, 11 losses. Spreading did most of the work, as the specification intends. But it spread too freely:

- Terraced fields reached 2,923 of 3,312 bands within about 360 years of first appearing, and stone building 2,762, including foragers. The prerequisite asked only whether a band knew a domesticated crop, not whether it farmed.
- Adoption ignored whether a technique was any use to the adopter.
- With everything held everywhere, no band was short of practitioners nearby, so losses could not show.

The cause-chain check in the trial script was cut off at the time limit: it checked all 16,000 events before sampling. It now samples 300 events spread through the run.

**Changes (design choices for Ben to confirm; the specification does not spell them out):**

1. **Farming techniques need farmers.** A domesticate is not enough; the band must put at least `TECH_FARMING` (0.2) of its work into farming or herding (`farm_share`, the share of work, not of food: Codex review 008).
2. **Adoption is weighted by need,** as invention is: chance x (`TECH_NEED_FLOOR` + need). A technique spreads faster where it answers a pressing problem (relative advantage: Rogers 2003; adoption curves shaped by biased transmission: Henrich 2001).

### Trial 4: after changes 1 and 2

46 inventions, 6,588 adoptions, 3 losses; cause chains 300 of 300.

- Foraging techniques now spread selectively: fish traps held by 57 bands, the bow by 105, canoes by 647, baskets by 391. Cordage and fire-hardened points are held by every band, which is plausible after 1,500 years of contact.
- **Terracing was still held by 2,775 bands.** Either most bands farm by year 10,000, or the prerequisite is still too loose. Terraces are built on slopes, and irrigation needs water, but neither prerequisite checked the land.

**Change 3:** terrain prerequisites, judged on the band's own cell. Terracing needs hilly land (relief of at least `TECH_HILL_RELIEF`, 300 m, to a neighbouring cell: 41% of land cells on planet 3). Irrigation needs a river or lake in the cell (6.7% of land cells). The trial script now also counts the bands that farm or herd.

### Sources (added)

- Henrich, J. (2001). Cultural transmission and the diffusion of innovations: Adoption dynamics indicate that biased cultural transmission is the predominate force in behavioral change. *American Anthropologist*, 103(4), 992–1013.
- Rogers, E. M. (2003). *Diffusion of Innovations* (5th ed.). Free Press.

### Trial 5: after change 3 (terrain)

44 inventions, 4,264 adoptions, 2 losses; cause chains 300 of 300. 2,532 of 3,312 bands farm or herd (at least 0.2 of their work) by year 10,000.

- Foraging, container and building techniques as in trial 4.
- **No terracing or irrigation was invented in this history.** Villages began in year 9,172, so farmers had about 800 years. One history cannot tell whether that is too rare. Terraces and canals came long after the first farming in the archaeological record, so their absence here is not implausible, but the gate's many histories must show them appearing somewhere.
- **Trial 4 showed 2,775 bands holding terracing when only about 2,500 farmed:** a band keeps a technique after it stops farming, because keeping does not check prerequisites. Asked of Codex in request 008, question 3.

## Decisions (Ben, 14 November 2026), after Codex review 008

1. **Quality of techniques: agreed.** Inventions start crude and improve slowly with practice, harder techniques more slowly. Learners start at a share of their teacher's level. Effects (stage 5) grow with quality. Prerequisites need a technique held well (for example, smelting needs good kilns). Migrants and captives carry a level that depends on how many of them bring it.
2. **Teaching and writing: agreed.** Craft specialists and writing make copying more faithful. A technique lost by a people with writing can, rarely, be recovered from records, coming back crude.
3. **A technique whose prerequisite has gone: remembered, not deleted.** It is not practised, gives no benefit, does not count its holders as practitioners, and fades over generations unless the conditions return.
4. **Animals per technique: agreed.** Milking: goat, sheep, cattle, horse. Wool: sheep. Draft animals: cattle, horse. Pack animals: horse, cattle. Manuring: any domesticated animal.
5. **Spreading weighted by cultural closeness: agreed** (M4 specification section 3.4), using language distance from M1.
6. **Domestication skills combined on merge: agreed**, with the M2 and M3 checks confirmed in the G4a gate run.
7. **Confirmed:** farming techniques need a people that farms or herds; adoption is weighted by need; terracing needs hills and irrigation a river or lake.

### How the decisions are built (14 November 2026)

All numbers are tunable starting values in `params.py`.

- **Quality (1).** A new invention starts at `TECH_INVENT_LEVEL` 0.25. A technique practised by more people than it needs improves by at most `TECH_REFINE` (0.005) a year, times sqrt(5 / keep), so an easy technique can go from crude to mastered in about 150 years and the hardest (keep 80) in about 600. A people also closes `TECH_CATCHUP` (5%) a year of the gap to the best practitioner within reach. Learners start at `TECH_ADOPT_SHARE` (0.6) of their teacher's level; a lesson below `TECH_LOST` does not take. Prerequisites need a technique held at `TECH_WORKING` (0.5), so a crude technique is not yet a foundation. People who join or are taken carry a level scaled by (carriers / people the technique needs), capped at 1.
- **Teaching (2).** Specialists (M2's surplus-fed specialists, all kinds counted, as a proxy for craft specialists) make copying more faithful: at a specialist share of `TECH_CRAFT_REF` (5%) or more, the people a technique needs are halved and refinement doubles (`TECH_CRAFT_GAIN` 1). A people practising writing loses `TECH_WRITING_HOLD` x writing's quality (up to half) less in copying, and keeps a record (`w.tech_record`) of each technique it practises. A lost technique still on record can come back, crude, with yearly chance `TECH_RECOVER` (0.002) x writing's quality.
- **Remembered, not practised (3).** A known technique whose prerequisites are gone is not practised: its holders are not counted as practitioners and it fades by `TECH_FORGET` (0.005) a year, from 0.5 to the loss line in about 70 years (some three generations), unless its conditions return. Its loss is recorded as forgotten, naming what was missing.
- **Animals (4)** as decided, in each technique's `animals`.
- **Cultural closeness (5).** For each adoption, a teacher is drawn in proportion to the practitioners each band within reach has, and the lesson takes with chance `TECH_FOREIGN` + (1 - `TECH_FOREIGN`) x (share of words the two languages share, from M1). This gives the closeness-weighted chance in expectation, without comparing every pair of peoples.
- **Domestication skills (6)** are combined as the better of the two in every merge and migration (`bands.carry`). Like farming's learning from neighbours, this records no event per band.
- **Captives** carry techniques (route `capture`), scaled by their number.
