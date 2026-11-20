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

### After Codex review 009 (14 November 2026)

- **Decision (Ben): a prerequisite counts only when practised,** not merely remembered at a working level. Checked down the whole chain.
- **Fixes:** only a people that practises writing keeps or reads records; a domesticate counts only where it can live (crops and animals); marriage moves carry knowledge (one carrier); carrying domestication skills refreshes the herder test.

### Trial 7: all decisions and review-009 fixes (planet 3, years 8,500–10,000)

This history differs from trials 1–5 (first village in year 8,963, not 9,172): the new rules draw from the technology stream differently. 33 inventions; 22,829 adoptions; 1,080 losses; cause chains 300 of 300; 2,966 of 3,796 bands farm or herd. 1,619 s, with the test suite running alongside.

- **Routes of adoption:** contact 8,744; migration 8,529; combining populations 4,429; small-band merges 953; captives 140; marriage 34. People moving now carry knowledge about as often as contact spreads it.
- **Spread:**
  - Foraging techniques reached almost every band: the bow 3,639 of 3,796, fish traps 3,586, tallies 3,750. Tally marks are ancient and widespread among foragers, so near-universal tallies are not implausible.
  - Pottery reached 1,595 bands, terracing 1,741, sail 823. Irrigation was known by 59 bands but held well by none (best 0.46). Mud brick was invented once and died with its band.
- **Quality saturates.** Most techniques reach 1.0 within a few centuries: refinement plus catching up with the best practitioner. Only recent or hard techniques stay below (sail median 0.85, irrigation 0.42). Once effects scale with quality, nearly everyone would get the full effect. **Open:** whether `TECH_REFINE` and `TECH_CATCHUP` are too high.
- **Every loss was forgetting, not the Henrich mechanism.** All 1,080 losses were techniques remembered but no longer practised: terracing 792 (after farming was given up, or carried to unsuitable land), canoes 157, pottery 82, sail 48. No technique was lost for want of practitioners: this world is densely connected. **Open, and needed for gate check 5** (isolation causes loss): whether isolated peoples lose techniques on other planets.
- No technique was recovered from records: writing was never invented.

### After the literature check (Ben, 14 November 2026: "go ahead")

- **Skilled practitioners, not everyone.** A technique is kept by `TECH_PRACTISE_SHARE` (0.25) of a band's adults (15–59) plus its specialists, not by every member. A band of 40 adults has 10 skilled people, too few for pottery (20). An epidemic that kills adults now weakens skills, as when the Polar Inuit lost kayaks, leisters and bows after the knowledgeable older members died in the 1820s and regained them from Baffin Island migrants around 1862 (Boyd, Richerson & Henrich 2011; the dating is debated: Walls, Knudsen & Larsen 2015).
- **Refinement slows near mastery:** the yearly gain is capped at `TECH_REFINE` x sqrt(5 / keep) x (1 − quality). From crude (0.25), an easy technique takes about 400 years to reach 0.9. This follows Mesoudi (2011): learning what is already known takes more of a lifetime as a technique grows, so improvement levels off. Henrich's (2004) model itself has no ceiling.
- **Forgetting unpractised techniques is kept,** matching Read's (2006) view that peoples drop what no longer suits them.
- **For the gate:** report the population-versus-risk check separately for foragers and farmers. Population predicted toolkit complexity among 40 farming and herding societies (Collard, Ruttle, Buchanan & O'Brien 2013) but not among 20 hunter-gatherer groups, where risk did (Collard, Kemery & Banks 2005).
- **Gate record:** `gates/g3.py` now records technology (inventions, adoptions by route, losses with skilled practitioners and people within reach, what is held, cause chains). `herders_alive` now counts peoples herding now (`ever_herded_alive` keeps the old count).

### Sources (added)

- Boyd, R., Richerson, P. J., & Henrich, J. (2011). The cultural niche: Why social learning is essential for human adaptation. *PNAS*, 108(Suppl 2), 10918–10925.
- Collard, M., Ruttle, A., Buchanan, B., & O'Brien, M. J. (2013). Population size and cultural evolution in nonindustrial food-producing societies. *PLoS ONE*, 8(9), e72628.
- Collard, M., Kemery, M. D., & Banks, S. (2005). Causes of toolkit variation among hunter-gatherers: A test of four competing hypotheses. *Canadian Journal of Archaeology*, 29, 1–19.
- Mesoudi, A. (2011). Variable cultural acquisition costs constrain cumulative cultural evolution. *PLoS ONE*, 6(3), e18239.
- Read, D. (2006). Tasmanian knowledge and skill: Maladaptive imitation or adequate technology? *American Antiquity*, 71(1).
- Roux, V., & Corbetta, D. (1989). *The Potter's Wheel: Craft Specialization and Technical Competence*. Oxford & IBH.
- Walls, M., Knudsen, P., & Larsen, F. (2015). Inughuit open water hunting before the nineteenth century. *American Antiquity*, 80(3), 602–609.

### Stage 5: effects (Ben, 14 November 2026: starting values, open to revision)

Each effect scales with the quality of a technique the band practises now (0 if unknown or only remembered). Full effects are in `params.TECH_EFFECT`. Wired in:

- **Foraging** (`foraging.py`): the work a band spends foraging counts for more (fire-hardened points +5%, cordage +10%, bow +10%, copper tools +5%; fish traps +15% and canoes +10% on cells with coast, lake or river). Food still comes only from the cell's wild stock, so a better-equipped band takes more of the same stock. The recorded return per worker-day uses the real days worked, so better gear also makes foraging more attractive against farming.
- **Farming** (`farming.season_food_live` and the yearly work choice): output per worker rises with irrigation (+50% on river or lake land, crops), the plough with draft animals (+50%, crops), milking (+30%, herds) and copper tools (+5%). Output per field (the land's capacity) rises with irrigation, terracing (+30% on hilly land, crops) and milking.
- **Storage** (`foraging.py`): spoiling of perishable stores x (1 − 0.15 baskets)(1 − 0.30 pottery x (1 + 0.25 kilns))(1 − 0.15 mud brick). Grain spoilage is unchanged: basket granaries already lose little (Golob, Malawi survey 1978: 2–3% in 10 months).
- **Crossings** (`hazards.crossings`): canoes double the chance of putting to sea; with sail, land across two sea cells is within reach. The crossing's cause names the boats.
- **Land advantage** (`surplus.py`): the plough with draft animals raises the yearly advantage of larger households by up to 50% (Kohler et al. 2017).
- **Polity capacity** (`polity.capacity`): tallies (+10%) and writing (+50%) at the seat.
- **Waiting for their systems:** trade (wool, pack animals, carts, sail's trade role), the land answering back (manuring, irrigation's salting), M4b (fortification, bronze and iron weapons, stone building).

Practised quality is judged once per season at first use and refreshed whenever knowledge changes.

### After Codex review 010 (14 November 2026)

- **Fixes:** teachers and the best practitioner within reach are skilled practitioners, as in keeping; crop and herd effects are kept apart in farming and in the work choice; the effects cache is cleared before every phase, when a band is created, and after farming changes skills; a village's founding conquest counts its tallies and writing.
- **Decisions (Ben):** a two-sea-cell crossing succeeds with chance equal to sail quality; skilled practitioners count each person once (a quarter of the non-specialist adults, plus every specialist).

### Trial 8: skilled practitioners and effects (code before the review-010 fixes)

Planet 3, years 8,500–10,000; 1,393 s. First village 9,086; population at the end 440,345 in 3,831 bands; 30 inventions; 23,226 adoptions; 1,356 losses; cause chains 300 of 300.

- **The Henrich mechanism now shows:** 309 losses were for want of skilled practitioners, besides 1,047 forgotten techniques. Gate check 5 still needs isolated peoples on other planets (the GitHub trial).
- **Quality no longer saturates for newer techniques:** terracing median 0.52, sail 0.41, stone building 0.74. Old foraging techniques are at or near 1.
- **Open: building techniques among foragers.** Stone building ended up known by 3,059 bands and mud brick by 2,058, many of them foragers. Neither has a prerequisite beyond clay (mud brick) or none (stone building). Both belong to settled peoples. To put to Ben: require a settled people (farming half its work or more) for building techniques.

### Building techniques need a settled people (Ben, 14 November 2026)

Mud brick, stone building and fortification now need a settled people: one farming half its work or more, or one that has stayed in the same place for `TECH_SETTLED_YEARS` (20) years. The literature ties building to settling down rather than to farming as such:

- **Watson Brake, Louisiana:** an earthen mound complex built around 5,400–5,000 years ago by hunter-gatherers (Saunders et al. 1997).
- **Göbekli Tepe:** monumental stone enclosures from around 9000 BCE, with no domestic grain found. Newer excavations found houses, a cistern and a channel for rainwater, a "full settlement" (Clare, Kinzel; reported in *Archaeology*, 2021). Whether its builders were foragers or early cultivators is debated.
- **The Pre-Pottery Neolithic A (about 10,000–8,800 BCE):** round houses on stone foundations with mud-brick upper walls, and Jericho's stone wall and tower, built by cultivators of not yet domesticated grain.

### Source (added)

- Saunders, J. W., et al. (1997). A mound complex in Louisiana at 5400–5000 years before the present. *Science*, 277(5333), 1796–1799.

### Negative result: technique effects stop farming on planet 3 (14 November 2026)

The preliminary benchmark (Claude Code, cloud container, `local/results/2026-11-14-benchmark-prelim.md`) ran planet 3, history 1, from the first people for 10,000 years with all of M4a: **no farming village formed.** Two diagnostic histories from the same start, on the current code:

| Run | First village | Population at year 6,500 |
|---|---|---|
| technology switched off | year 6,794 | 129,339 |
| technology on, effects switched off (`TECH_EFFECT = {}`) | year 6,794 (identical history) | 129,339 |
| technology and effects on (benchmark) | none by year 10,000 | about 130,000–145,000 |

Knowledge without effects changes nothing, as it should (its own random stream only). **The effects are the cause.** The likely mechanism: foraging gear raises the return per day of foraging (up to +40% with cordage, fire-hardened points, bow and copper, and +25% more by water), and bands choose farming by comparing its return with foraging's. The foraging rate was tuned through gates G0 and G2 on a world without technology, so it already stands for foragers with an ordinary toolkit: the gear bonuses count that toolkit twice.

The literature points the same way. The broad spectrum revolution (Flannery 1969; Stiner 2001) widened foragers' diets to small game, fish and birds under population pressure: more food from the same land, not richer returns per hour. And early cereal farming was probably less productive per hour than foraging (Bowles 2011, about three fifths of the food foraging yielded).

To put to Ben: change how foraging gear works.

### Broad-spectrum food (Ben, 14 November 2026)

**Design chosen:** foraging gear opens a second wild pool in each cell (`w.stock_broad`): small game, birds, fish and marginal plants, sized at the approved gear effects (+30% of ordinary wild food on land, +55% by water). A band reaches it in proportion to the quality of the gear it practises (`technology.forage_access`). It regrows like ordinary wild food and is counted in the food balance. Gear no longer multiplies foraging effort.

**First version failed** (planet 3, fresh): with the pool as good as ordinary food, population rose to about 175,000 by year 7,000 (against about 130,000 without technology), and no band farmed at all. Farming starts from pressure (a band's food margin below `PRESSURE_MARGIN`), and the pool kept margins comfortable.

**Second version:** ordinary food is taken first; broad-spectrum food only with the effort left over, at `TECH_BROAD_RETURN` (0.3) of the return per unit of work. Lower-ranked resources cost more work per calorie: small seeds and other costly plant foods rank low against large animals, and geophyte returns range from about 50 to 4,000 kcal per hour (Louderback 2022, from Simms 1987, Kelly 1995 and others). So as foragers turn to them, returns per day fall, and the pressure that leads to farming remains, as in the broad spectrum revolution. 0.3 is a starting value, not a measured ratio.

### Sources (added)

- Bowles, S. (2011). Cultivation of cereals by the first farmers was not more productive than foraging. *PNAS*, 108(12), 4760–4765.
- Flannery, K. V. (1969). Origins and ecological effects of early domestication in Iran and the Near East. In P. J. Ucko & G. W. Dimbleby (eds.), *The Domestication and Exploitation of Plants and Animals* (pp. 73–100).
- Louderback, L. A. (2022). Climate-driven dietary change on the Colorado Plateau, USA, and implications for gender-specific foraging patterns. *American Antiquity*, 87(1), 1–17.
- Stiner, M. C. (2001). Thirty years on the "Broad Spectrum Revolution" and Paleolithic demography. *PNAS*, 98(13), 6993–6996.

**Second version also failed** (planet 3, fresh, 10,000 years): population about 170,000–180,000 from year 3,000 on; no band tended, sowed or farmed anything. Even at 0.3 of the return, broad-spectrum food keeps food margins above the pressure line. It works like famine food: it buffers the bad years whose pressure starts farming in M2's model. Two attempts have now failed for the same reason: any extra food for foragers removes the pressure that M2's farming needs.

**Decision (Ben, 14 November 2026): foraging gear's food effect is switched off** (`TECH_FORAGE_GEAR = False`) until farming's trigger is recalibrated. Gear is still invented, kept, spread and lost, and still opens later techniques (cordage before the bow, nets, baskets and wool; canoes before sail). Every other effect stays on, canoes' sea crossings included. The broad-spectrum pool and its lower return stay in the code, sized at zero. Carried forward: make farming start from falling returns per day rather than from food margins, so foraging gear can feed people without stopping farming.

### The new farming trigger (Ben, 14 November 2026: "build it as proposed")

Built as in `docs/FARMING_TRIGGER_PROPOSAL.md`. Pressure is the larger of hunger (M2's food margin) and crowding: people on a band's cell and its neighbours per unit of the wild food those cells give unaided (`farming.crowding`), from `CROWD_START` 0.55 to full pressure at 0.85. In the planet-3 forager world at year 8,500 (older code), crowding had a median of 0.64, 90th percentile 0.76 and 99th 0.88; two thirds of bands were below M2's hunger line there. A people settled `ABUNDANCE_YEARS` (20) on land where a wild species grows well (`ABUNDANCE_SUIT` 0.5) tends and sows it at `ABUNDANCE_FLOOR` (0.1) pressure. The first tending of each species names its route. Foraging gear's food effect is back on. Trials on planet 3 (all effects on; technology off) are running; the full test suite runs after them.

**Trials of the new trigger** (planet 3, history 1, from the first people; starting-value parameters):

| Run | First bands farming | First village |
|---|---|---|
| all effects on, foraging gear included | by year 5,000 (76 bands) | year 5,337 |
| technology off | by year 9,000 (527 bands) | year 9,000 |
| (old trigger, technology off, for reference) | by year 6,000 (12 bands) | year 6,794 |

With all effects on, population reaches about 165,000–175,000 before farming (gear feeds more foragers), so crowding builds sooner. The technology-off history farmed later than the old trigger's history although the new pressure is never lower for any band: on the planet-3 forager world at year 8,500, the expected number of first tendings is about 0.0004 a year under the new trigger against 0.0002 under the old. **First tending is so rare under either trigger (one every 2,500–5,000 years across the planet) that its timing in one history is mostly chance.** Only many histories show the average; gate G4a will. Open question for the gate: whether first tending should be less rare, so that farming's timing depends more on conditions than on luck.

### GitHub isolation trial (run 43543673766, code at main `0d554e4`): four of five histories

Code with skilled practitioners and refinement slowing near mastery, but **before** the stage-5 effects changes, the review-010 fixes and the new farming trigger (foraging gear then raised returns per day, which delayed farming). 2,000 years after each first village. Planet 4's history needed five stages: its population reached about 2.6 million after farming, at about 20 seconds per simulated year and 6 GB of memory.

| History | First village | Inventions | Adoptions | Lost for want of skill | Forgotten | People within reach at those losses (10th / median / 90th percentile) | Cause chains |
|---|---|---|---|---|---|---|---|
| planet 1, history 5 | 13,414 | 29 | 63,256 | 990 | 43,667 | 10 / 24 / 1,366 | 400 / 400 |
| planet 2, history 1 | 8,117 | 44 | 81,179 | 2,284 | 38,348 | 11 / 17 / 42 | 400 / 400 |
| planet 5, history 7 | 15,848 | 68 | 140,828 | 12,248 | 60,326 | 15 / 49 / 137 | 400 / 400 |
| planet 6, history 1 | 14,441 | 65 | 120,519 | 1,619 | 64,034 | 11 / 17 / 45 | 400 / 400 |
| planet 4, history 10 | 9,089 | 96 | 223,139 | 11,239 | 121,467 | 14 / 48 / 153 | 400 / 400 |

- **Isolation causes loss (gate check 5, first look):** half of all losses for want of skill happened where 17–49 people were within reach, against hundreds of thousands in the connected parts of each world. The losses are of the right kinds: the bow, fish traps, stone building, pottery, tallies and writing, in small or cut-off peoples.
- **Not yet shown:** the rate of loss per band at each level of contact (this needs the number of bands at each level, not only the losses). The G4a report must measure it.
- **Forgetting is very common** (38,000–64,000 per history), mostly farming techniques carried by migrants and marriages to peoples or land where they cannot be practised. They fade and are recorded as forgotten. Not wrong, but the gate should report the two kinds of loss separately.

## Trade (specification section 4): literature check (15 November 2026)

- **Gift partnerships among foragers (hxaro).** Among the Ju/'hoansi in the early 1970s, a person had on average 16 partners (range 2–42), spread within about 200 km, with partnerships linking into chains of hundreds of kilometres. Gifts were exchanged with a delay and roughly balanced. In need, a family moved to a partner's camp and stayed as long as necessary: on average people spent 3.3 months a year in partners' camps, and 93% of recorded extended visits were to partners (Wiessner, workshop paper 2007, preliminary figures; original study Wiessner 1977, 1982). Such networks are old: ostrich eggshell beads reached Lesotho rock-shelters from more than 100 km and some from more than 300 km away over the last 33,000 years (Stewart et al. 2020).
- **Down-the-line exchange.** Near Eastern obsidian makes up over 80% of chipped stone within about 300 km of its source (the supply zone) and falls off steadily beyond it (the contact zone) (Renfrew, Dixon & Cann 1968; Renfrew 1969). Down-the-line exchange is thought to reflect reciprocity between neighbours (Hodder 1974; Renfrew 1977).
- **Directed trade.** Old Assyrian merchants (19th century BCE) took tin and woollen textiles from Assur to Kanesh in Anatolia by donkey caravan, about 1,200 km in five to six weeks, twice a year. Tin sold at about twice its purchase price, fine textiles at up to 300%. The local ruler took a share of each donkey load and could buy about 10% of the textiles first; merchants lived in their own quarter with its own officials, and some smuggled to avoid the tax. Their records fit a gravity model of trade, in which trade grows with the size of the two places and falls with distance (Barjamovic, Chaney, Coşar & Hortaçsu 2019).
- **Rulers and trade goods.** Chiefs and states finance themselves through staples (food) and through wealth: valuables and prestige goods they produce, trade or control (D'Altroy & Earle 1985). M3 has staple tribute; trade adds wealth.

### Sources (added)

- Barjamovic, G., Chaney, T., Coşar, K., & Hortaçsu, A. (2019). Trade, merchants, and the lost cities of the Bronze Age. *Quarterly Journal of Economics*, 134(3), 1455–1503.
- D'Altroy, T. N., & Earle, T. K. (1985). Staple finance, wealth finance, and storage in the Inka political economy. *Current Anthropology*, 26(2), 187–206.
- Renfrew, C., Dixon, J. E., & Cann, J. R. (1968). Further analysis of Near Eastern obsidians. *Proceedings of the Prehistoric Society*, 34, 319–331.
- Stewart, B. A., et al. (2020). Ostrich eggshell bead strontium isotopes reveal persistent macroscale social networking across late Quaternary southern Africa. *PNAS*, 117(12), 6453–6462.
- Wiessner, P. (1982). Risk, reciprocity and social influences on !Kung San economics. In E. Leacock & R. Lee (eds.), *Politics and History in Band Societies* (pp. 61–84).

### Trade decisions (Ben, 15 November 2026)

1. **Imported materials count for techniques:** a people holding imported tin and copper can practise bronze without the ores nearby; when the trade is cut, the technique stops being practised, with the cause recorded.
2. **Goods that change something:** fine stone (tools), salt (preserves stores), metals (their techniques), prestige goods (rulers' wealth). Textiles and pottery are trade goods only, for now.
3. **Partnerships are links between bands,** not between individuals, sized from the hxaro partner counts.
4. **Sharing in a bad year:** a starting value, tuned so a bad year at one band costs it far less than alone.
5. **No money until M6;** wealth is counted in goods.

Build in stages, each reviewed by Codex: (1) goods and ledgers; (2) gift partnerships; (3) down-the-line exchange; (4) directed trade; (5) effects.

### Trade stage 1: goods and ledgers (15 November 2026)

New module `origins/sim/trade.py`, phase "trade" once a year after technology. Nine goods, each with a source on the band's own cell: salt (salt deposits or coast), fine stone (flint), copper (copper and copper working practised), tin (tin and smelting), iron (iron and iron working), gold (gold and copper working), textiles (wool practised), pottery (pottery practised), shell (coast). Yearly yield per skilled practitioner times the technique's quality; yearly wear per good (`GOOD_YIELD`, `GOOD_WEAR`: starting values). Goods move with people when bands split, migrate, merge or combine (`trade.move_share`), and are lost when a band ends. A ledger per good (produced, worn, lost, moved) is checked every season in `observe.py`. Saves keep goods and ledgers; the replay digest includes them. Livestock already moves as herds (surplus.py); production takes no food time yet (a simplification).

Trial: planet 3 forager world (year 8,500 save), 100 years: no ledger failures. Salt, fine stone and shell produced at their sources; no metals, pottery or textiles (no one practises their techniques). Shell, which lasts, ended up held by 861 of 894 bands, carried by people as bands split and moved; salt, used up quickly, by 256.

### Trade stage 2: gift partnerships (design, before building)

From the literature check (hxaro; Wiessner 1982, 2007) and Ben's decisions 3–4 (band-level links; sharing a starting value):

- **Partnerships are links between bands** within two rings (about 200 km), up to `PARTNERS_MAX` per band (starting value 4: a band of about 30 Ju/'hoansi with 16 partners each, most in a few other camps). A new link forms with a yearly chance, more readily between peoples who share words (as for techniques) and who are already within reach. A gift each year keeps it alive (a small amount of a lasting good, such as shell, when the band has some; otherwise the visit itself); a link lapses after `PARTNER_LAPSE` years without a gift, or when the two bands move out of reach.
- **In a bad year,** a band whose food margin falls below `PRESSURE_MARGIN` draws on partners with food to spare: each gives up to `PARTNER_SHARE` (starting value 0.2) of what it holds above its own season's need. Food moves, it is not made: the transfer is recorded in the food balance as a move between stores. The Ju/'hoansi pattern was visiting, with families staying in a partner's camp for months; moving food is the simpler first version, and moving people can follow if the gate shows it matters.
- **Contact:** a partner counts as a teacher for techniques at the closeness of one people (shared words treated as 1), since partners visit and live together for months.
- **Records:** a partnership's founding is an event (with the gift and the closeness that led to it); help in a bad year is an event per receiving band and season, naming the givers. A new random stream, "trade", appended at the end.
- **Checks:** a band with partners loses far less of its food margin in a bad year than one without (Ben's decision 4); the ledgers still balance; partnerships are dense among foragers in contact and thin among isolated peoples.

### After Codex review 012 (15 November 2026)

- **Fix:** marriage moves carry the movers' share of their band's goods (the spouse and any young children).
- **Decisions (Ben):** a winning raid takes `RAID_TAKE` of the loser's goods as loot, as of its food store, and captives carry none; producing goods costs no food time until the effects stage (stage 5). Until then, goods stocks embody free labour: keep that in mind when judging trade results.

### Trade stage 2: gift partnerships, as built (15 November 2026)

Built as designed above (`trade.partnerships_yearly`, `trade.share_in_need`; new random stream "trade", appended). Partnerships are pairs of bands within two rings, up to `PARTNERS_MAX` (4) each, forming with yearly chance `PARTNER_FORM` (0.05) x closeness of speech, lapsing when out of reach or when a partner ends. Each year partners give each other `GIFT_SHARE` (5%) of their shell and gold. In a season when a band's food in hand falls short of its needs, before eating, each partner gives up to `PARTNER_SHARE` (20%) of what it holds beyond its own needs (for farmers, the needs until the next harvest). Partners teach techniques at closeness 1. A new band starts without partners; Wiessner (2007) describes partnerships being inherited, which can follow if the gate shows it matters. Events: partnership formed, lapsed, and help received (naming the givers). Saves keep the links; replay digest includes them.

Trial: planet 3 forager world (year 8,500 save), 100 years, 39 s (unchanged): no ledger failures; 898 bands averaging 2.8 partners (438 with four, 101 with none); 6,874 partnerships formed and 1,939 lapsed; help in 15,715 band-seasons, median 557 units of food each; 200 of 200 sampled cause chains resolve. Gifts carried shell to every band.

### After Codex review 013 (15 November 2026)

Fixes: loading an older save keeps every goods row (`trade.grow`); help in need comes only from partners within reach at that moment; each yearly gift exchange is an event with its goods and quantities (specification 4.2); consolidation ends the absorbed band's partnerships at once. A lesson taken from a partner is recorded as route "partnership", so the gate can tell it from ordinary contact. The divide-by-zero warning in `foraging.move` (empty bands) is silenced without changing any value.

### Trade stage 3: literature check on down-the-line exchange (15 November 2026)

- **Fall-off.** Within about 240–320 km of an Anatolian source, about 80% of chipped stone at early Neolithic villages was obsidian; beyond it, the share fell as a "nearly perfect exponential function of distance" (Renfrew, Dixon & Cann 1966, 1968; summary in EBSCO Research Starters).
- **Down-the-line alone is not enough.** If each village keeps half and passes half on, after eight exchanges only about 0.39% is left; yet obsidian reached southern Levant sites 700–800 km from its sources at about 0.5% of chipped stone. Simulations fit the data only with dense local links plus a few long-distance links among well-connected hub villages (Ibáñez et al. 2015). Larger sites far from sources held more: obsidian-to-flint ratios of 0.07 (small), 0.40 (medium) and 2.41 (large) at sites over 500 km away.
- **What else shapes it.** The population of the receiving area predicts obsidian nearly as well as distance (Ericson 1977, 1981); routes follow paths and relief rather than straight lines (Findlow & Bolognese 1980, 1982); transport (boats; pack animals) changes effective distance (Hodder & Orton 1976; Renfrew 1977; Ammerman 1978, 1979), and weight mattered before cargo animals (Wright 1970). Summarised in a study guide to exchange at mapaspects.org.

### Source (added)

- Ibáñez, J. J., Ortega, D., Campos, D., Khalidi, L., & Méndez, V. (2015). Testing complex networks of interaction at the onset of the Near Eastern Neolithic using modelling of obsidian exchange. *Journal of the Royal Society Interface*, 12(107), 20150210.

### Trade stage 3: down-the-line exchange, as built (Ben, 15 November 2026: recommendations 1–4 and the recording plan)

`trade.down_the_line`, once a year after gifts and before wear. Bands on the same or adjacent cells exchange each good a share `DTL_RATE` (0.1) of the way towards equal holdings per person, so bigger bands hold and pass on more; no band gives more than half of a good in a year. Pack animals (+50%) and carts (+100%) speed exchange over land, canoes (+50%) between bands by water; with sail, coastal bands across one sea cell exchange at a rate scaled by sail quality. Recorded: a thinned yearly log of each band's units received and given (`exchange_log`, saved), and a `good_arrived` event when a good first reaches a band, naming the neighbour most of it came from. All rates are starting values.

Trial: planet 3 forager world (year 8,500 save), 100 years, 41 s (unchanged); no ledger failures; 3,694 first arrivals, 200 of 200 sampled cause chains resolve. Holdings per person by cells from the nearest source:

| Cells (about 60 km apart) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| fine stone | 0.50 | 0.11 | 0.026 | 0.009 | 0.003 | 0.0014 | 0.0007 | 0.0003 | 0.0002 |
| salt | 0.12 | 0.03 | 0.004 | 0.0007 | 0.0002 | 0.00003 | 0.000004 | 0.000001 | 0.0000003 |

The shape is the expected steady (roughly exponential) decline, steeper for salt, which is used up faster. The tail is too thin: at 8 cells (about 480 km) fine stone is at about 0.04% of its level at the source, whereas Levantine obsidian was still at roughly 0.6% of its near-source share at 700–800 km, about 12–13 cells (0.5% of chipped stone against about 80% near the sources); and there is no plateau near the sources (Renfrew's supply zone, about 300 km or 5 cells). *Correction (15 November 2026): the table first said cells were about 110 km apart; planets are built at grid level 6 on half Earth's radius, so cells are about 60 km apart, which makes the shortfall larger than first written.* This is Ibáñez et al.'s (2015) finding: exchange between neighbours alone falls off too fast. Directed trade (stage 4) is to supply the long links; the trial after stage 4 will check whether it does. (Holdings per person are not the archaeological measure, which is the share of chipped stone, so the comparison is rough.)

### Trade stage 4: literature check on directed trade (15 November 2026)

The specification (section 4, item 3) has directed trade begin "once there are specialists and polities". The literature says long links come in two kinds, and the first is older than polities:

- **Long links before states.** The Near Eastern obsidian data are fitted not by down-the-line exchange but by dense local links (neighbours about 50 km apart) plus at most one distant link per village, up to about 120–180 km. In the best fit for the later Neolithic (PPNB), villages drop weak partners for well-supplied ones, so hubs form; large sites far from sources hold far more obsidian than small ones (Ibáñez et al. 2015). Those are pre-state farming villages. At our grid (cells about 60 km apart), such a link spans two to three cells, which is our partnership reach; but our partners now pass only shell and gold, and only as gifts.
- **Journeys to the source.** Australian ethnography records parties travelling to quarries hundreds of kilometres away: red ochre from Bookartoo (Parachilna) reached Boulia, about 450 km away, by organised expeditions on established routes, men carrying cakes of about 28–35 kg; people came to Ulpunyali ochre from 165–200 km. In 1874, four tons of Moana ochre were taken to Koppermanna to try to stop further Diyari expeditions to Bookartoo (Smith & Fankhauser 2009, citing Jones 1984). At Mount William, the greenstone quarry was held by custodians of two clans; visiting groups sent a messenger to the headman, camped near the quarry and exchanged goods such as possum-skin rugs for axes and blanks; the stone travelled several hundred kilometres (McBryde 1978, 1984, summarised in the encyclopedia article on the quarry). Access to a source was by permission, not open.
- **Prestige goods between elites.** Alpine jadeitite axes travelled up to 2,000 km in the fifth and fourth millennia BCE, largely through direct exchange between elites, and were deposited in hoards and graves (Pétrequin et al. 2012, reviewed by Cooney 2013).
- **Directed trade with merchants and rulers.** Old Assyrian caravans (already in these notes: Barjamovic et al. 2019): a gravity pattern between centres, rulers taking a share of each load and a first choice, merchants in their own quarter, smuggling. Curtin (1984) calls such communities trade diasporas: networks of foreign merchants living, briefly or for generations, in a host society as cross-cultural brokers, which fade once they are no longer needed.
- **A caution.** Similar fall-off curves can come from different exchange systems (equifinality; Hodder 1974; Hodder & Orton 1976). The gate should judge trade by its recorded mechanisms and who carried what, not by the shape of the curve alone.

### Sources (added)

- Cooney, G. (2013). Review of *JADE: Grandes haches alpines du Néolithique européen*. *Antiquity*, 87(336).
- Curtin, P. D. (1984). *Cross-Cultural Trade in World History*. Cambridge University Press.
- McBryde, I. (1984). Kulin greenstone quarries: the social contexts of production and distribution for the Mt William site. *World Archaeology*, 16(2), 267–285.
- Pétrequin, P., Cassen, S., Errera, M., Klassen, L., Sheridan, A., & Pétrequin, A.-M. (eds.) (2012). *JADE: Grandes haches alpines du Néolithique européen, Ve et IVe millénaires av. J.-C.* Presses universitaires de Franche-Comté.
- Smith, M. A., & Fankhauser, B. (2009). *Geochemistry and identification of Australian red ochre deposits*. Palaeoworks Technical Paper 9 (their 1996 report to AIATSIS).

### Trade stage 4 decisions (Ben, 15 November 2026)

1. **Partners trade, and hubs form (a change to specification section 4, item 3, approved by Ben).** Partners pass working goods (fine stone, salt, metals) as well as gifts; settled villages drop weak partners for well-supplied ones, so hubs form, as in Ibáñez et al.'s (2015) best fit. Directed trade by specialist traders comes on top of this, once there are polities. Journeys to distant sources are not built.
2. **Traders are paid in goods:** they keep a share of what they carry; their food comes from surplus, like other specialists.
3. **Rulers take a toll and first pick:** a share of each load crossing their land and the right to buy first, as at Kanesh; smuggling past them is possible and recorded.
4. **Routes follow gravity:** trade between centres grows with both their sizes and falls with distance.

All shares and rates will be starting values. The build waits for Codex's review 014 and Claude's answer.

### After Codex review 014 (15 November 2026)

Three fixes, each reproduced first (`tests/test_trade.py::Review014`):

- **Dense cells:** summed over a band's pairs, the share of the gap closed in a year is held at one half or less, so a well-connected band can no longer be pushed past every donor by many inflows at once.
- **First arrivals:** each band remembers which goods have reached it (`goods_reached`), so wear cannot produce a second "first" arrival.
- **Exchange log:** it records gross flows pair by pair, so bands that pass goods on are counted.

Trial rerun (planet 3, year-8,500 save, 100 years, 51 s): no ledger failures; 1,325 first arrivals (3,694 before, about two thirds of them repeats); 200 of 200 sampled chains resolve. Fine stone per person by cells from the source: 0.50, 0.10, 0.025, 0.0088, 0.0030, 0.0014, 0.00065, 0.00031, 0.0002, essentially unchanged; the thin tail stands. Codex's synthetic timings: exchange on 40,000 bands took 0.44 s (434,242 pairs); an arrival-heavy case took 3.9 s before fix 2. Rates are starting values.

### Trade stage 4a, as built (15 November 2026)

- **Partners trade working goods.** Partners who are not neighbours (up to two rings, about 120 km) exchange salt, fine stone, copper, tin and iron as neighbours do, at `PARTNER_TRADE_RATE` 0.1 of the gap each year. Shell and gold still pass only as gifts. A good that first reaches a band through a partner is recorded with `route="partner"`.
- **Larger bands hold more links** (my choice, flagged for review): `PARTNERS_MAX` 4 at `PARTNER_SIZE_REF` 30 people, growing with the square root of size, at most `PARTNERS_CAP` 16. With a fixed cap of four, a well-supplied village could never gather links, so no hub could form. The cap of 16 follows hxaro's average partners per person (Wiessner 2007); the square root is a guess.
- **Settled bands trade up.** A settled band with no room left, with a yearly chance `PARTNER_SWITCH` 0.1, drops its worst-supplied partner for the best-supplied band within reach that has room, if that band is at least `PARTNER_SWITCH_GAIN` 2 times as well supplied (Ben, 15 November 2026). Supply is holdings per person of the working goods, each relative to its mean, summed.
- **Gift records** (Ben, 15 November 2026). Each partnership keeps running totals of what each side gave (`w.partner_gave`, saved and in the digest). The first exchange is a `gift_exchange` event; a lapse event carries the totals; yearly gifts go into a thinned `gift_log`. In the first 1,200-year trial, yearly gift events were 9.9 million of 11.7 million events, and the full test suite ran out of memory (the 1,500-year event-store test passed 6 GB). With totals, that trial's record holds 2.0 million events and the test peaks at about 1.7 GB.
- Older saves widen to 16 links per band and start their gift totals at zero.

**Trial** (planet 3, year-8,500 save, 1,200 years, 36 min, after both of Ben's decisions):
- no ledger failures; 10,689 first arrivals, none repeated, 2,332 of them through partners; 20 of 20 sampled chains resolve;
- 4,221 bands, about 499,000 people; links per band average 6.9 (settled 7.5, others 3.6), at most 14;
- fine stone per person by cells from the source: 0.40, 0.10, 0.049, 0.017, 0.0066, 0.0037, 0.0013, 0.00049, 0.00021 (8 cells), then 5.3e-5, 1.6e-5, 4.6e-6 at 9–11 cells, and 1.8e-6 at 12 cells (about 720 km), about 0.0005% of the source level against roughly 0.6% for obsidian;
- beyond 5 cells, the largest tenth of bands hold about 5 times as much fine stone per person as the smaller half (Ibáñez et al. 2015: about 33 times beyond 500 km in the PPNB).

**Knock-out** (the same 1,200 years with `PARTNER_TRADE_RATE` and `PARTNER_SWITCH` at zero; link allowance and gifts unchanged): no ledger failures; fine stone per person 0.43, 0.12, 0.045, 0.014, 0.0047, 0.0022, 0.00074, 0.00033, 0.00014 (8 cells), then 3.9e-5, 7.8e-6, 1.2e-6, 2.3e-7 (12 cells); beyond 5 cells the largest tenth hold about 7 times what the smaller half hold. 256,259 partnerships formed, 74,848 lapsed.

**What stage 4a does, then:**
- It thickens the tail: about 1.5 times at 8 cells, 3 times at 10, 8 times at 12; more fine stone leaves the sources (0.40 at the source against 0.43).
- It does **not** make the size difference: large far-off bands already hold about 7 times what small ones do without partner trade or swaps (5 times with them). So the hub pattern in the trial comes from something else, not yet identified (perhaps where large settled bands sit, on rivers and coasts with better transport); "hubs form" is not shown.
- Swaps account for about 153,000 of the 409,196 partnerships formed (37%) and most of the extra lapses (214,808 against 74,848), even with the twice-as-well-supplied rule.

The tail is still far too thin: partner links of two rings shorten chains only a little, and the fall-off is set mainly by wear against exchange (`GOOD_WEAR` 0.2 for fine stone against 0.1 of the gap a year). Directed trade (stage 4b) is meant to add long links between centres; if the tail is still thin after it, the wear and exchange rates go to Ben as a decision, not a quiet tuning. All values are starting values.

Also: partnership formation is now the largest kind of event (409,196 of about 2.0 million, a fifth of the record), over a third of it from swaps.

### Trade stage 4b: literature check on traders, routes and rulers (15 November 2026)

Ben's decisions for 4b (above): traders paid in goods; rulers take a toll and first pick, smuggling recorded; routes by gravity. Further points from the literature:

- **Merchant ventures were financed and shared.** At Kanesh, a long-term partnership of 12 investors put about 15 kg of gold in the hands of one merchant, Amur-Ishtar, for 12 years; a partner who withdrew early got back less than he put in (Kültepe excavation, reported by Arkeonews 2025, citing F. Kulakoğlu; the full archive is described in Larsen 2015). So a trader carries other people's goods and keeps a share, which is how Ben's decision 2 already works. *The exact split between investors and merchant is not stated in the sources I could read; I will not give a figure.*
- **Rulers gain by holding bottlenecks.** Earle (2011) names three sources of rulers' control: land, the taxing or protection of trade, and attached craft specialists. In the Aegean the main bottleneck was probably sea shipping, with palaces charging for safe harbours and protection; in Bronze Age Denmark control moved to the ownership of long-distance boats and warriors guarding trade. Earle sets these against staple finance: wealth finance rests on valuables produced or obtained, and the two can be joined, with staples feeding the specialists who make valuables (also D'Altroy & Earle 1985; Earle 1997). For the build: a ruler's toll should fall where routes are forced through its land (passes, river crossings, harbours), not evenly everywhere.
- **Gateway communities.** Large settlements grow up along natural trade routes, at points where they can control the movement of goods, and can outgrow what their own hinterland would support (Hirth 1978, Chalcatzingo in Formative Mesoamerica). This should emerge from tolls on forced routes rather than being written in; a gate check could look for it.
- **Ports of trade.** Polanyi (1963) describes ports of trade: places, often on the edge of states or between them, set aside for exchange between foreign traders under local control. A later possibility, not for 4b.
- **Caravans had real costs.** A caravan account from Kanesh lists clothing and wages for guides, donkeys, their gear and fodder, and fees; the Assur–Kanesh journey took six to eight weeks (Metropolitan Museum, tablet 66.245.10, merchant Imdi-ilum, active 1888–1876 BCE). Traders' food and the loss of goods on the road should be costs in the build.

Design consequences (to propose before building; Codex review 015 first):
1. Traders are a specialist role of polities, fed from surplus, numbered by the polity's surplus and its trade.
2. Routes link polity centres by gravity (size × size, falling with travel cost), with travel cost from terrain and transport, so routes bend through passes and along rivers and coasts.
3. Goods carried are working and prestige goods, from where they are plentiful to where they are scarce; the trader keeps a share of what arrives.
4. Each polity a route crosses takes a toll; the destination's ruler buys first; a trader may take a costlier way round a toll (smuggling, recorded).
5. Costs: traders' food, and a share of goods lost on the road.

### Sources (added)

- Arkeonews (29 January 2025). Anatolia's first company was founded 4,000 years ago with 15 kilos of gold (reporting F. Kulakoğlu, Kültepe excavations).
- Earle, T. K. (1997). *How Chiefs Come to Power: The Political Economy in Prehistory*. Stanford University Press.
- Earle, T. (2011). Redistribution and the political economy: the evolution of an idea. *American Journal of Archaeology*, 115(2), 237–244.
- Hirth, K. (1978). Interregional trade and the formation of prehistoric gateway communities. *American Antiquity*, 43(1), 35–45.
- Larsen, M. T. (2015). *Ancient Kanesh: A Merchant Colony in Bronze Age Anatolia*. Cambridge University Press.
- Metropolitan Museum of Art. Cuneiform tablet: caravan account, 66.245.10.
- Polanyi, K. (1963). Ports of trade in early societies. *Journal of Economic History*, 23(1), 30–45.

### After Codex review 015 (15 November 2026)

Five fixes, each reproduced first (`tests/test_trade.py::Review015`):
- **Sail pairs:** a sail pair is no longer counted a second time as partners.
- **Dense-cell limit:** worked out separately for goods partners trade and for the rest, so partner links do not slow pottery between neighbours.
- **Gift totals:** ending, merging and consolidation now record the partnership's totals in a lapse event.
- **Goods reached:** what a band holds counts as reached even in a year with no one to exchange with.
- **Swap rule:** "at least twice as well supplied" is now inclusive.

Ben's decisions (15 November 2026):
- the square-root link allowance stays, with a fixed-four comparison before the gate (16 partners per person in hxaro does not establish 16 per band);
- two bands parted by a swap wait `PARTNER_REFORM_WAIT` 10 years before linking again;
- partnership events are not thinned.

**Size difference at matched distance** (stage-4a 1,200-year world; largest tenth of bands against the smaller half at exactly the same distance from a fine-stone source): about 1.0–1.5 times near the sources (0–3 cells), rising to 4–7 times from 6 cells out. So the difference is not an artefact of pooling distances, as Codex suggested it might be. Its cause is not yet separated. Codex shows ordinary size-weighted exchange can produce it, and larger bands' extra links might add to it; the fixed-four comparison will separate them.

### Trade stage 4b, as built (15 November 2026)

`origins/sim/traders.py`, called in the yearly trade phase after neighbours' exchange and before wear.

- **Traders:** `TRADER_SHARE` 0.2 of the specialists at a polity's seat, fed from surplus as specialists are.
- **Routes by gravity:** each polity's traders serve up to `ROUTES_MAX` 3 other seats, chosen among the 12 nearest by polity size × size / cost².
- **Travel cost:** A* over the cells, at most `TRADE_RANGE` 30:
  - a land cell on foot costs 1, divided by 1 + pack animals and carts;
  - climbing costs `MOUNTAIN_COST` 2 per 1,000 m, and high ground (above 2,000 m) adds `HIGH_COST` 0.5 per step;
  - rivers and coasts cost down to `RIVER_COST` 0.5 with canoes;
  - lakes need canoes; sea cells cost `SEA_COST` 2 / sail quality, and none can be crossed without sail.
  Costs are cached as a pure function of the planet and the transport qualities (rounded to tenths).
- **Carried:** all goods (textiles and pottery included: Ben, 15 November 2026, after Kanesh), `TRADER_RATE` 0.5 of the gap in holdings per person between the two seats, within the traders' load (`TRADER_LOAD` 2 units per trader a year, more with pack animals and carts), at most half of what the giver holds.
- **On the way:**
  - road loss is 1 − exp(−`ROAD_LOSS` 0.01 × cost);
  - each polity holding cells on the road takes `TOLL` 0.05, unless going round all its land loses less (recorded once per route and polity as `toll_evaded`);
  - the destination's ruler takes `FIRST_PICK` 0.1;
  - the traders keep `TRADER_KEEP` 0.25 of what is delivered and take it home.
- **Rulers' stores** (`w.treasury`, per polity; saved, in the digest and in the goods ledger): they wear as everyone's goods do; they pass to the seat when a polity ends (lost if the seat has gone), and to the conqueror when it is conquered.
- **Records:** `trade_route_opened` once per pair of polities; `good_arrived` with `route="trader"`; a thinned `route_log` (moved, lost, tolls, first picks, kept, tolls paid and gone round).
- **A bug found by its own test:** going round a polity first avoided only its cells on the road, not its land beside it.

**Trial** (planet 3, year 9,700 world: 1,502 polities, 1,158 seats with traders; 100 years; 439 s, of which traders 108 s, about a quarter):
- no ledger failures;
- 12,060 routes opened (polities come and go); 57 goods first reached a band with traders;
- tolls were paid on 4 sampled route-years and gone round on 146: polities are mostly small, so a way round them is cheap; the bottleneck effect Earle describes does not appear at this scale;
- rulers' stores after 100 years: about 150 units of salt and 21,800 of shell (shell wears 2% a year, so it builds into a hoard);
- fine stone per person by cells from the source: 0.41, 0.12, 0.045, 0.023, 0.0085, 0.0043, 0.0024, 0.00056, 0.00034, 0.00034 (9 cells), then 2.2e-5 at 10 and 3.5e-6 at 11. Against stage 4a's 1,200-year world, about the same out to 8 cells, about 6 times more at 9 cells, and about 1.4 times at 10. These are different starting worlds, so this is only a rough comparison.

**The tail is still far too thin** after stage 4b (at 12 cells about 0.0003% of the source level, against roughly 0.6% for obsidian). As promised, the wear and exchange rates go to Ben as a decision. All values are starting values.

### The thin tail: literature check (15 November 2026; Ben: research, then propose)

- **What sets the tail in the model.** With neighbours exchanging a share r of the gap each year and goods wearing at k a year, holdings fall off by roughly exp(−√(k/r)) per cell. Fine stone has k = 0.2 and r = 0.1, which predicts a fall of about a quarter per cell; we see about 0.4. The obsidian curve falls from about 80% to 0.5% over 12 cells, about 0.65 per cell. Matching it needs k/r about six times smaller than now, or a different mechanism.
- **Discard and movement have the same effect.** In stone-procurement models, how likely a tool is to be thrown away and how far foragers move have similar effects on how far stone ends up from its source, and distance-to-source data alone cannot tell them apart (Lin & Premo 2021). A neutral random-walk model, with no exchange and no choices, already gives distance-decay and reduction-intensity patterns qualitatively like the archaeological ones (Brantingham 2003). So the shape of the curve alone cannot fix our wear rate; a rate has to come from other evidence.
- **Curation.** Binford (1979) distinguishes curated technologies (tools made, carried, maintained and kept) from expedient ones, made and thrown away where used. Ericson (1984, as summarised by Tripcevich) links how far stone was reduced before exchange to the social distance between giver and receiver. What follows for the model: wear need not be one constant; a scarce, valued material can be used more sparingly. *I have not found a source I could read that gives the direction and size of the reduction-intensity-with-distance pattern; that needs checking before it is built on.*
- **Use-life figures.** Ethnographic use-lives of tools exist (Shott 1989, !Kung San and Ingalik; Shott & Sillitoe 2004, Wola of New Guinea), but the figures are behind paywalls I cannot read, so I give none.

Options for Ben:
1. **Curation:** wear of a band's working goods falls as its holdings per person fall (people use scarce stone sparingly). It is mechanism-based and makes the far tail fall more slowly without changing wear near the source. Its form and starting values would be guesses until the reduction-intensity evidence is checked.
2. **Lower wear for fine stone,** once a use-life source can be read.
3. **Journeys to the source:** bands within a few cells of a source fetch stone directly, a supply zone (Renfrew's term), up to about 300 km, about 5 cells. Ben chose not to build this for stage 4a.
4. **Leave it,** and report it as an open item at the gate.

### Sources (added)

- Binford, L. R. (1979). Organization and formation processes: looking at curated technologies. *Journal of Anthropological Research*, 35(3), 255–273.
- Brantingham, P. J. (2003). A neutral model of stone raw material procurement. *American Antiquity*, 68(3). (Page numbers not checked.)
- Lin, S. C., & Premo, L. S. (2021). Forager mobility and lithic discard probability similarly affect the distance of raw material discard from source. *American Antiquity*, 86(4), 845–863.
- Shott, M. J. (1989). On tool-class use lives and the formation of archaeological assemblages. *American Antiquity*, 54(1), 9–30.
- Shott, M. J., & Sillitoe, P. (2004). Modeling use-life distributions in archaeology using New Guinea Wola ethnographic data. *American Antiquity*, 69(2), 339–355.
- Tripcevich, N. (2007). *Quarries, Caravans, and Routes to Complexity: Prehispanic Obsidian in the South-Central Andes* (PhD dissertation, University of California, Santa Barbara), section 2.2.5, online at mapaspects.org (summarising Ericson 1984).

**Ben's decision (15 November 2026): curation.** A band's wear of working goods will fall as its holdings per person fall: scarce goods are used sparingly. Built as a trial with starting values once review 016 is answered, and judged at the gate by its knock-out.

Evidence for the direction: across ethnographic and archaeological cases, poor-quality stone tends to be made into informal tools; good stone in short supply into formal tools; good stone that is plentiful into both, and residential mobility matters less than availability (Andrefsky 1994). Formal tools are the curated ones (Binford 1979). This supports the direction (scarce good stone, used more carefully) but gives no rate; the form and values will be starting values.

- Andrefsky, W., Jr. (1994). Raw-material availability and the organization of technology. *American Antiquity*, 59(1), 21–34.

### After Codex review 016 (16 November 2026)

Three fixes, each reproduced first (`tests/test_trade.py::Review016`):
- **Landing:** a step from the sea onto land climbs from the water's surface, not the seabed.
- **Tolls:** one road is chosen with every toll counted. Entering a third polity's land costs τ = −ln(1 − TOLL) / ROAD_LOSS of travel, so paying and going round are weighed on one road; the independent detours, which could skip a toll that every road must pay, are gone.
- **Route cache:** keyed by the planet's fingerprint, grid and every cost setting.

Ben's decisions (16 November 2026):
- the ruler's take is a levy (`RULER_LEVY`, until money in M6);
- each direction travels its own road, and the traders' share loses goods and pays tolls on the way home;
- the destination shortlist is by gravity on straight-line distance.

Trial rerun (year-9,700 world, 100 years, 435 s, traders 83 s): no ledger failures. Tolls were paid on 2,427 sampled route-years and gone round on 437 (4 and 146 before the fix), totalling 200 units in the sampled rows. 214 goods first reached a band with traders. The fine-stone tail is unchanged. Codex's timings of the shortlist (0.19 s at 500 polities, 0.99 s at 1,500, 3.19 s at 3,000, before the partial sort) go here as measured.

### Curation, as built (16 November 2026)

- **Rule.** In each band, wear of tools (`CURATED_GOODS`: fine stone, copper, tin, iron) is the usual rate × max(`CURATION_MIN` 0.1, h / (h + `CURATION_HALF` 0.01)), where h is the band's holdings per person. Near a source (h about 0.4), wear is about 98% of the usual rate; at h = 0.001 it is a tenth. Salt, textiles, pottery and prestige goods wear as before, and so do rulers' stores. `CURATION` False is the knock-out. The form and values are starting values; only the direction rests on the literature (Andrefsky 1994; Binford 1979).
- **Knock-out** (planet 3, year-9,700 world, 300 years each, run side by side; no ledger failures either way). Fine stone per person by cells from the source:

| Cells | 0 | 4 | 6 | 8 | 10 | 12 | 14 |
|---|---|---|---|---|---|---|---|
| Curation on | 0.41 | 0.013 | 0.0035 | 0.0015 | 0.00045 | 0.00019 | 0.00011 |
| Curation off | 0.44 | 0.0065 | 0.0015 | 0.00035 | 1.9e-5 | 1.8e-6 | 3.4e-7 |

  Near the sources nothing changes; the tail fattens from about 5 cells out, by about 4 times at 8 cells, 100 times at 12 and 300 times at 14. At 12 cells (about 720 km) fine stone is about 0.05% of the source level, against roughly 0.6% for obsidian: still about 13 times short, but the curve now flattens with distance rather than falling at a steady rate. Whether the rest of the gap comes from Renfrew's supply zone (direct access near sources), from values of the curation rule, or from elsewhere is not settled.
- Everything else barely moves: run time 1,266 s against 1,298 s; trader routes and tolls within a few per cent. With curation on there were 4,056 first arrivals against 5,701 off. Fewer bands' stock falls below the threshold and back, so fewer goods arrive "for the first time" through other routes; this is a reading, not checked.

### After Codex review 017 (16 November 2026)

Three fixes, each reproduced first (`tests/test_trade.py::Review017`):
- **Road home:** a destination is served only if there is a road home within range.
- **Range:** the toll-aware search keeps states (cell, tolls paid), so a road needing more of the range for fewer tolls is no longer lost. At most `ROAD_TOLLS_MAX` 8 tolls per leg.
- **Lakes:** the planet records each lake's water surface (`water_level`, not in the fingerprint), and leaving a lake climbs from it.

**Correction to the curation knock-out.** My reading of the fall in first arrivals was wrong. With curation on, more fine stone first reached new bands (2,371 against 1,689); the whole difference is pottery (26 against 2,336). From one practising band in the shared start, pottery spread to 728 bands in the run without curation and died out in the run with it. The histories diverged by chance in their technology. A knock-out from a single history is therefore noisy; at the gate it should run over several histories. Flattening at finite distance is not a permanent plateau (Codex).

### Trade stage 5: literature check on what goods change (16 November 2026)

The specification (section 4.3) asks four things of trade: move goods to where they are scarce, spread techniques, give rulers something to control and fight over, and create dependence ("a people that relies on imported tin loses bronze when the trade is cut, with the cause recorded"). Ben added (15 November) that making goods should cost work, starting at this stage. What the code does now: goods move and wear, but change nothing; a technique's materials count only if they lie within two cells; and only partners and neighbours teach, not traders.

- **Metal tools.** In replicative experiments, metal axes were markedly faster than stone at felling, especially on larger trees, and bronze was about as good as steel. So effectiveness alone cannot explain the move from bronze to iron (Mathieu & Meyer 1997, as described by the Penn Museum; Putz et al. 2023 cite the same review of more than a dozen experiments, "but see" Jørgensen 1985). *I could not read the figures themselves, so I give no ratio.* For the build: copper-working and later metal techniques should help only where the band holds metal, and should help clearing and farm work most.
- **Salt.** A daily intake of salt is needed for human and animal health, and salt preserves food (Harding 2013, p. 11). Diets rich in meat probably supplied enough naturally (p. 43); herbivores, and so herds, need more (p. 16). The first certain salt production in Europe is Neolithic, from about 5900–5600 cal BC (p. 44). For the build: salt held should matter to herders and farmers more than to hunters, and should cut the spoiling of stores. Estimates of need vary tenfold (p. 14), so any rate is a starting value.
- **Prestige goods and rulers.** In Frankenstein & Rowlands's (1978) model, Early Iron Age chiefs in south-western Germany held power through control of imported prestige goods, passed down to dependants to create obligations and a ranked hierarchy. The model is disputed: imports were few (a few hundred objects over centuries), what was sent south in return is hard to trace, and local production may have mattered more (Wells; summarised in the Hallstatt research notes cited below). Earle's wealth finance (1997, 2011; above) is the broader frame. For the build: a ruler's store of prestige goods could help hold a polity together, with a small effect and a knock-out, because the evidence is contested.
- **Craft time.** Specialisation ranges from part-time household production to full-time attached specialists (Costin 1991). For the build: goods made by ordinary members cost them food-getting time, in proportion to what they make; goods made at a seat by specialists come from surplus, as other specialists' work does.
- **Contact through trade.** The specification (4.2) says trade creates contact and so raises the connected population of section 3.2 (Henrich 2004; Powell, Shennan & Thomas 2009). For the build: traders' routes should count as contact between the two seats for learning techniques, recorded as route "trade".
- **Dependence.** At Kanesh, Assyrian merchants carried tin to Anatolia, where bronze-making needed it (Barjamovic et al. 2019; Larsen 2015). For the build: a material held as goods (tin, copper, iron) counts as within reach while the band holds enough of it per person. When imports stop and the stock wears out, the technique stops being practised, and the record says the trade ended.
- **War over trade:** already in the specification ("control of the copper trade"). Earle's bottleneck argument (above) points to routes and sources as targets. To be specified with M4b's war reasons rather than here, unless Ben prefers otherwise.
- **The "trade" need.** Inventions driven by trade (carts, sail, pack animals, wool, copper-working) now use a stand-in built from polities and crowding. With trade in place, they should use the band's actual trade.

### Sources (added)

- Costin, C. L. (1991). Craft specialization: issues in defining, documenting, and explaining the organization of production. In M. B. Schiffer (ed.), *Archaeological Method and Theory*, vol. 3, 1–56. University of Arizona Press.
- Frankenstein, S., & Rowlands, M. (1978). The internal structure and regional context of Early Iron Age society in south-western Germany. *Bulletin of the Institute of Archaeology, London*, 15, 73–112.
- Harding, A. (2013). *Salt in Prehistoric Europe*. Sidestone Press (open access).
- Mathieu, J. R., & Meyer, D. A. (1997). Comparing axe heads of stone, bronze, and steel: studies in experimental archaeology. *Journal of Field Archaeology*, 24, 333–351.
- Penn Museum, *Expedition* magazine: "A tree falls in Philadelphia" (on Mathieu & Meyer's experiments).
- Putz, F. E., Fletcher, T., & Magee, L. (2023). Tree felling with stone axes: pre-bending matters but feller sex does not. *Forests*, 14(2), 202.
- Hallstatt research notes, "Social organisation and hierarchy in the Hallstatt culture" (maptism.github.io), for the criticisms of the prestige-goods model; the primary critique (Wells) is not yet read.

**Ben's decision (16 November 2026): build stage 5 as set out.** Seven effects, with war over trade left for M4b, all as starting values:
1. Materials held as goods count as in reach, so a band can lose a technique when its imports stop.
2. Metal techniques help only bands that hold metal.
3. Salt cuts spoiling and helps herds.
4. Rulers' prestige goods help hold a polity together a little, with a knock-out.
5. Making goods costs ordinary members food time; specialists' goods come from surplus.
6. Traders' routes spread techniques.
7. Trade-driven inventions respond to the band's real trade.

### Trade stage 5, as built (16 November 2026)

All seven of Ben's effects; `GOODS_EFFECTS` False switches all of them off. Values are starting values.

1. **Materials held as goods** (`trade.goods_materials`, in `technology._possible`): a band holding `MATERIAL_HELD` 0.005 per person of fine stone, salt, copper, tin, iron or gold counts as having that material. Each year `technology._cut_off` notes which techniques a band practises only because of goods; when those goods run out and the material is not within reach, a `technique_cut_off` event says the trade's supply ran out. Saved as `w.tech_import`. Inventions name each material as "within reach" or "held, brought by trade".
2. **Metal tools need metal:** copper-working's food effects scale with metal held (copper + tin + iron), full at `METAL_NEED` 0.02 per person.
3. **Salt:** spoiling of stored food × (1 − `SALT_SPOIL` 0.2 × s) and food from herds × (1 + `SALT_HERD` 0.1 × s), where s is salt held over `SALT_NEED` 0.05 per person, at most 1.
4. **Prestige goods:** polity capacity × (1 + `PRESTIGE_HOLD` 0.1 × p), where p is gold and shell in the ruler's store per member over `PRESTIGE_NEED` 0.05, at most 1.
5. **Craft time** (`trade.craft_share`, applied to foraging effort): for each good a band makes, `CRAFT_TIME` 0.05 × the share of ordinary members who practise × the technique's quality, at most half of their work. Specialists' share of the making costs no food time.
6. **Traders' roads teach** (`technology._trade_lessons`): along each route travelled the year before (`w.trade_links`, saved and in the digest), each seat can learn what the other practises, with chance `TECH_SPREAD` × `TRADE_TEACH` 0.5 × (need floor + need) × closeness of speech. Recorded with route "trade".
7. **The trade need** (`trade.trade_need`): imported goods held (goods with a source the band lacks), each relative to the mean, summed, over `TRADE_NEED_REF` 1. With effects off, the old stand-in.

**Knock-out** (planet 3, year-9,700 world, 300 years each, side by side; no ledger failures either way):

| | Effects on | Effects off |
|---|---|---|
| People at the end | 505,630 | 498,501 |
| Techniques learned along traders' roads | 1,205 | 0 |
| Learned by contact / partnership | 2,054 / 134 | 2,565 / 171 |
| Techniques lost | 2,904 | 3,354 |
| Techniques cut off by lost imports | 0 | 0 |
| Fine stone per person at 8 / 12 cells | 0.0014 / 0.00018 | 0.0018 / 0.00017 |

- **What shows:** trade becomes a channel for techniques; fewer techniques are lost; the population is about 1.4% larger after 300 years. This is one history, so these are indications, not results.
- **What cannot show here:** no band in this world practises any metal-working (no copper-working, smelting, bronze or iron in either run), and only 3 inventions happened in 300 years. So dependence on imported metal, and metal tools, are tested only by the unit tests. A world with metal-working is needed before the gate.
- **Speed:** the first version doubled run time (2,633 s against 1,323 s), almost all of it in the prestige check working out every band's size thousands of times a year. Fixed by working out polities' populations once a tick, which changes no result: 10 years now take 52 s with effects against 48 s without.

### After Codex review 018 (16 November 2026)

Five fixes, each reproduced first (`tests/test_trade.py::Review018`):
- **Road teachers:** a band teaches along a road only if it has skilled practitioners.
- **Craft time:** none where there are no ordinary adults.
- **Dependence:** judged against the end of last year's technology pass. `technology._mark` records what each band practises and which materials it holds as goods; a lapse is a cut-off only if those goods would still have made the technique practicable. So a failed prerequisite is not called a supply failure, and techniques acquired during the year are covered.
- **Prerequisite check:** `prerequisites_met` accepts imported materials.
- **Prestige goods:** polity members are looked up fresh each call.

The toll cap (`ROAD_TOLLS_MAX`) bounds the search for a cheaper road, not every toll paid: where no road within eight tolls exists, the original road is used and pays them all.

Ben's decisions (16 November 2026):
- **Trade need:** measured from goods actually received last year per person, by every route and of every good, against `TRADE_NEED_REF` 0.05.
- **Dependence:** a small controlled case now (`local/scripts/dependence_case.py`), with the full experiment across metal-working histories at the gate. In the case, a band given 100 specialists, so knowledge cannot be lost, practises bronze on imported tin. With supply continuing it practises bronze for 40 years. With supply cut, tin is below the threshold after the year-25 wear, and the year-26 technology pass records a `technique_cut_off` naming tin; bronze is still remembered afterwards. *This is a narrow control of the stock threshold, not a viable society or a trade-route experiment: 100 specialists in a 30-person band is outside the population constraint, food and demography do not run, and the tin top-up has no source in the goods ledger (Codex review 019).* Imported tin wears slowly once scarce (curation), about 3% a year at these holdings, which is why the threshold is crossed only after about 25 years.

### The land answers back: literature check (16 November 2026)

The specification (section 5; gate check 9) asks for five things: overhunting lowers game; forest is cleared for fields and fuel, with erosion on slopes; farmed land wears out without fallow or manure; irrigated dry land salts up; recovery is slow or absent, and the chain is recorded wherever it leads to famine or migration. What the code does now: wild food regrows 55% of the gap to its seasonal maximum every season (`REGROWTH`), so hunting leaves no lasting mark; there is no separate large game, and no forest, soil fertility or salt per cell.

- **Large game.** Across Australia, Eurasia, the Americas and Madagascar, the mammal species lost in the late Quaternary were the slow breeders, whatever their size; slow breeders survived mainly in closed habitats, or where they were active at night or in trees, out of people's way. This fits human pressure but not a sudden "blitzkrieg" of hunting (Johnson 2002). A country-level global analysis ties extinctions of mammals of 10 kg and more mainly to how long they had lived alongside humans, few in Africa, most in the Americas and Australia. Humans are linked to about 64% of the losses and climate to about 30%, mostly in Eurasia (Sandom et al. 2014, as reported by Aarhus University). These are associations, and the debate continues. For the build: a large-game pool per cell, recovering slowly (slow breeders), drawn down by hunting. Its loss should depend on hunting pressure against regrowth, so it is not forced; where pressure is low, game persists.
- **Forest clearance.** Europe was already extensively deforested by 1000 BC in a population-driven reconstruction (Kaplan, Krumhardt & Zimmermann 2009). So fields, not fuel, should be the main clearer. Fuel was a modest, local cost: at one iron-smelting site in Tanzania, each kilogram of slag took about 2.74 kg of charcoal, and about 2 hectares of slow woodland could have supported its production for 50 years; sustained yields are put at about 1,000 to 4,000 kg of charcoal per hectare a year (Iles 2020). The same region shows serious erosion linked to forest change. For the build: forest cover per cell, cleared by new fields and, less, by smelting and kilns; regrowing over centuries; clearance on slopes adds erosion, which lowers soil fertility.
- **Soil fertility.** Europe's first farmers manured their crops from about 6000 BC (nitrogen isotopes in charred grain and pulses from 13 sites, about 6000 to 2400 BC). Manure was limited by herd size and the labour of carrying it, so it was used selectively, and well-manured land was a long-term investment passed down in families (Bogaard et al. 2013, as reported by the University of Oxford). For the build: fertility per cell falls under continuous cropping and recovers with fallow; manuring (the technique, plus herds to supply it) slows the fall. Rates are starting values.
- **Salting.** Jacobsen & Adams (1958) linked salting in southern Mesopotamia to a shift from wheat to more salt-tolerant barley and to falling yields. In the figures as later summarised, Lagash yields of about 2,537 litres per hectare around 2400 BC were followed by about 1,460 around 2100 BC, and Larsa yields of about 897 by about 1700 BC; barley rose from about 80% of the crop to about 98% (Altaweel, simulation chapter, summarising Jacobsen and Maekawa). Powell (1985) argued that fallowing and leaching kept salt from being a major problem; Artzy & Hillel (1988) defended the theory. In Altaweel's simulation, basin fields could become unproductive within about 40 years, while long fallow limited salt. So the evidence is contested. For the build: salt per cell on irrigated land in dry climates rises with irrigation and falls only slowly with fallow; it lowers crop yields above a threshold. A salt-tolerant crop, where the planet has one, holds up better.
- **Recovery and feedback.** Forest returns over centuries and salted soil hardly at all (specification). Each of these enters food. The chain should be recorded at the point where it changes something people do (a famine, a move), naming the land's history: for example, the fields of X yielding a third less after 300 years of irrigation without fallow.

### Sources (added)

- Altaweel, M. Simulating the effects of salinization on irrigation agriculture in southern Mesopotamia (book chapter, about 2013; core.ac.uk 18456728).
- Bogaard, A., et al. (2013). Crop manuring and intensive land management by Europe's first farmers. *PNAS*. Read through the University of Oxford's report; the other authors, volume and pages not checked.
- Iles, L. (2020). Exploring the impact of iron production on forest and woodland resources: estimating fuel consumption from slag. *Science and Technology of Archaeological Research*, 5(2), 179–199.
- Jacobsen, T., & Adams, R. M. (1958). Salt and silt in ancient Mesopotamian agriculture. *Science*, 128(3334), 1251–1258.
- Johnson, C. N. (2002). Determinants of loss of mammal species during the late Quaternary "megafauna" extinctions: life history and ecology, but not body size. *Proceedings of the Royal Society B*, 269(1506), 2221–2228.
- Kaplan, J. O., Krumhardt, K. M., & Zimmermann, N. (2009). The prehistoric and preindustrial deforestation of Europe. *Quaternary Science Reviews* (doi 10.1016/j.quascirev.2009.09.028).
- Powell, M. A. (1985). Salt, seed, and yields in Sumerian agriculture: a critique of the theory of progressive salinization. *Zeitschrift für Assyriologie*, 75(1), 7–38.
- Sandom, C., et al. (2014). Global late Quaternary megafauna extinctions linked to humans, not climate change. *Proceedings of the Royal Society B*, doi 10.1098/rspb.2013.3254. Read through Aarhus University's report; the other authors not checked.

### After Codex review 019 (19 November 2026)

Three fixes, each reproduced first (`tests/test_trade.py::Review019`):
- **The cut-off test:** asks whether the technique would be practicable with the imports held now plus those lost, so a newly imported material is not dropped.
- **Joining:** people joining in numbers (migration, merge, consolidation) bring the record of last year's practice and imports to the band they join.
- **The explanation:** a cut-off names the lost import, not within reach, whose return alone would restore the technique, and says whether it is the technique's own material or a prerequisite's.

Ben's decision (19 November 2026): craft time scales with the makers. Ordinary practitioners' craft years are taken from the band's food effort at a full adult's work each, at most half of it.

### The land answers back: Ben's decision (19 November 2026)

Build as set out, after the review-019 fixes:
1. Large game per cell, recovering slowly and hunted down.
2. Forest per cell, cleared mostly by fields and partly by kilns and smelting, regrowing over centuries, with erosion when slopes are cleared.
3. Soil fertility per cell, falling under continuous cropping, recovering with fallow, falling more slowly with manuring where there are herds.
4. Salt building up on irrigated dry land, cutting yields above a threshold.
5. Each recorded where it leads to famine or a move.

All values are starting values.

### The land answers back, as built (19 November 2026)

`origins/sim/land.py`, a yearly phase after trade, at the harvest, drawing no random numbers. Per cell, each 0..1. `LAND` False is the knock-out. All values are starting values.

- **Large game, slow and fast** (Ben, 19 November 2026: split). Slow breeders (`GAME_SHARE` 0.1 of ordinary wild food, regrowth `GAME_GROWTH` 0.05 a year) and faster game (`GAME_FAST_SHARE` 0.2, `GAME_FAST_GROWTH` 0.3), each logistic, drawn down by hunting pressure (the year's take of ordinary wild food against the year's maxima) × `GAME_CATCH`, drifting towards neighbouring cells (`GAME_SPREAD` 0.05).
  - **`GAME_CATCH` 0.18 is calibrated, not measured** (Ben's choice). The median hunting pressure on lived-in cells, planet 3 at year 9,700, is 0.49 (farmed and foraged cells alike; the 10th to 90th percentiles are 0.37 to 0.53). At that pressure faster game settles near 0.7 and slow breeders are lost, the pattern in Johnson (2002).
  - Two corrections on the way: the first single pool lost all large game where people live; and my recommendation to count only the game share of the take would have changed nothing, because the take is proportional, so the game fraction taken equals the overall fraction taken.
- **Forest** (forest biomes only): cleared by fields (`FOREST_CLEAR` 0.3 a year on a fully used cell) and by goods made with fire (`FOREST_FUEL`), regrowing at `FOREST_REGROW` 0.01 of the gap a year where land is unused. In forest biomes, `FOREST_WILD` 0.3 of wild food depends on it.
- **Soil fertility:** falls by `FERT_DRAIN` 0.03 × use × fertility a year, less with manuring and herds (`MANURE_SAVE` 0.7); recovers by `FERT_RECOVER` 0.1 of the gap × unused share; erosion `EROSION` 0.02 × steepness × bare ground × use. Crop yields scale from `FERT_FLOOR` 0.4 to 1.
- **Fallow by crowding** (Ben, 19 November 2026; Boserup 1965): each cell's resting share runs from `FALLOW_MAX` 0.8 with land to spare down to `FALLOW_MIN` 0.1 at crowding `FALLOW_CROWD_FULL` 2. Resting land is taken out of crop capacity, so land-short farmers lose crop and labour-short ones little; use is measured against full capacity, so rested land recovers.
- **Salt:** rises by `SALT_RISE` 0.03 × irrigation × use × dryness (below `DRY_RAIN` 500 mm) and leaches by `SALT_LEACH` 0.02 × salt × unused share. Above `SALT_THRESH` 0.3 it cuts yields, by up to `SALT_MAX_LOSS` 0.9.
- **Records:** a lived-in cell's first crossing (game below 0.3, forest below 0.3, fertility below 0.6, salt above 0.3) is an event (`land_game`, `land_forest`, `land_soil`, `land_salt`) naming the year its use began. It re-arms only after recovery. A band moving off such a cell has the land's events added to the reason for its move.

**Trials** (planet 3, year-9,700 world, 300 years each; no ledger failures in any):

| Run | People at the end | Notes |
|---|---|---|
| Land off | 498,241 | |
| Land on, single game pool | 368,026 | slow game 0.017, faster 0.29 of natural, on lived-in cells |
| Land on, calibrated catch | 376,886 | slow 0.057, fast 0.743 |
| … with the forest effect off | 383,596 | |
| … with the game effect off | 401,499 | |
| … with the soil effect off | 480,367 | |
| Land on, with fallow (as built) | 365,404 | fertility 0.88 on lived-in cells; 954 game, 138 forest and 212 soil crossings; 536 bands' last move cites the land |

**Reading.** Soil causes most of the fall in population; game costs about 6% and forest about 2%. Fallow did not reduce it in this trial: the mean fertility of lived-in cells rose a little (0.874 to 0.881), but resting land takes crops away now. Where crowded farmers have no manure, they settle at roughly half the crop of fresh land. **The size of the soil effect rests on two unmeasured values, `FERT_DRAIN` and `FERT_FLOOR`**: I could not read long-term yields on unmanured land (Rothamsted's figures). Ben's decision (19 November 2026): send it to review as built, and judge the size at the gate across histories. Two cautions:
- each land array starts at its natural level 9,700 years into a peopled world, so part of the fall is a jolt from switching the system on;
- no band in this world irrigates, so salt is tested only by the unit tests.

### Sources (added)

- Boserup, E. (1965). *The Conditions of Agricultural Growth: The Economics of Agrarian Change under Population Pressure*. London: Allen & Unwin; Chicago: Aldine. (Read through G. Federico's review, EH.net.)
- Robinson, J. G., & Redford, K. H. (1991). Sustainable harvest of Neotropical forest animals. In J. G. Robinson & K. H. Redford (eds), *Neotropical Wildlife Use and Conservation*, 415–429. University of Chicago Press. (Citation only; its figures not read.)

### After Codex review 020 (19–20 November 2026)

All seven findings reproduced and fixed (`reviews/responses/020-land-answers-back-claude.md`). In short:

- **Land use** is the share of farmland worked for crops, before fertility and salt (`land_work`, `land_seasons`), so a poor harvest is no longer counted as resting land.
- **Fuel limits output** (Ben, 19 November 2026): tin and iron at a cell scale with the fuel within two rings, from coal or the living cover of the best-wooded cell (`FUEL_FULL` 0.3); below `FUEL_MIN` 0.1 there is no wood for smelting, iron working, canoes or carts. A `technique_no_fuel` event records each such lapse. Pottery and native copper still use forest but are not limited by it (dung, grass and brush can fire them).
- **Broad-spectrum food** is no longer scaled by lost game and forest.
- **Crossings** are flagged only when recorded on a lived-in cell; recovery clears the event.
- **Cause links:** a move decided by the land is a `land_move` event citing the land events; hunger deaths carry `death_land`, group hunger events cite it. The rule (`LAND_FELT` 0.9) is an attribution, not a counterfactual.
- **Cut-offs** name the smallest set of relevant lost imports.
- **Switched off**, the land's yearly accounts are cleared each harvest.
- **Choices see real yields** (Ben, 19 November 2026; switch `REAL_YIELDS`): crops weighed by fertility and salt; the realised return per worker-day caps the expected one; daughter villages judge cells after fertility, salt and fallow. This changes farming behaviour beyond the land; G2 and G3 will show it.
- **Fallow gives way to need** (Ben, 19–20 November 2026, after review 020's design question and a first rule by farmers on cropland): farmers crop as much land as they could work the year before, and the rest rests, between 0.1 and 0.8. **Not modelled:** the extra labour per unit of crop that shorter fallow costs (Boserup 1965).

**Two more errors of mine, found in the trials:** fields cleared nearly all of any farmed cell's forest (now they clear the land they take; the earlier forest knock-out had this error), and wood within reach as a mean over two rings ran out far too soon (now the best-wooded cell).

**Trials** (planet 3, `snap_p3s1_8500_plus1200.zip` at year 9,700, 300 years, `local/scripts/knockout_land.py`; no invariant failures): land off 498,241; land on as built 321,477; with fallow by farmers on cropland 312,138, and with fallow at its shortest 341,774; real yields off 308,430; fuel unlimited 320,452 (an upper bound). The land costs about 35% of the people here. One history: the gate must run the arms over several. **Hunting pressure:** at steady stock `REGROWTH` 0.55 bounds the sustainable take against the year's targets; the median 0.49 is near that ceiling (Codex). The soil values `FERT_DRAIN` and `FERT_FLOOR` remain unmeasured; they are an open question in the Notion research-questions database.

### After Codex review 021 (20 November 2026)

All seven findings reproduced and fixed (`reviews/responses/021-review-020-fixes-claude.md`):
- **Wood** is gathered from the wooded cells within two rings, in proportion to living cover; coal-smelted tin and iron take none.
- **The realised farming return** belongs to the cell where it was earned (`farm_rr_cell`), and is cleared when farming stops.
- **Crop use** is measured against crop capacity.
- **Irrigation and manure** are averages over the crops actually worked.
- **Moves** cite lost game or forest only if the band would have stayed with this season's regrowth at its natural level. Worn soil reaches migration through `land_abandoned`: a village that would have kept farming on fresh soil.
- **Wood and imports lost together** are recorded as one cut-off with `wood: true`.

Ben's decisions (20 November 2026):
- **Resuming wood work** needs `FUEL_RESUME` 0.2 of the best-wooded cell's cover; keeping it going needs `FUEL_MIN` 0.1.
- **Famine evidence: the food account test.** Each band records its seasonal shortfall and what the land's losses took from food it actually got (this season's lost regrowth for wild food; worn or salted soil's loss from its crops, spread over the seasons after the harvest). A hunger death cites the land only if restoring those losses would have covered the shortfall.
- **Farm room** counts only crops and animals a band can use (a bug since M2; it changes harvests).
- **Fuel wood: spread it and keep it small.** `FOREST_FUEL` 0.000005 per unit (it was 0.001, uncalibrated): the first trial of Codex's fix stripped forests region-wide (13% left on lived-in forest cells; 81% of lived-in cells without wood).

**Trial** (planet 3, year-9,700 save, 300 years): land off 505,784 (farm-room fix included); land on 319,551, so the land costs about 37% of the people here. 150 of 3,913 individual hunger deaths pass the food account test. One history.

**Independent literature checks (Ben, 20 November 2026):** for each new idea, Claude does its own check and puts the same question to ChatGPT without Claude's findings, through the Notion research questions; Claude verifies every source before use. ChatGPT's first two rounds (disease origins, first-contact mortality, soil decline, critical community size, causes of death, endemic shift, fallow recovery) are in the Notion sources database with each source's verification status; one figure was corrected (Poulton et al. 2024: 0.90 t/ha, not 1.01).

### Diseases from domestic animals: literature check (Claude, 20 November 2026)

Done alongside ChatGPT's independent check (Ben, 20 November 2026), which is pending for the last question; its earlier rounds on disease origins, first-contact mortality, critical community size, causes of death and the endemic shift are in the Notion sources database with verification status. Sources marked "verified" were read by Claude; the rest are listed as such.

- **Where human pathogens come from.** Of 1,407 human pathogen species, 816 (58%) are zoonotic and 177 are emerging or reemerging; ungulates support the most emerging zoonoses, but emergence is not tied strongly to any one host type (Woolhouse & Gowtage-Sequeria 2005, verified). Domestic mammals share more pathogens with people the longer they have been domesticated, across three datasets (dog 71 and sheep 84 shared parasites against 34 for cattle and pig in one of them), with no strong link to how closely they live with people (Morand, McIntyre & Baylis 2014, verified). Many classic attributions are wrong or unproven: human tuberculosis did not come from cattle (Brites & Gagneux 2015, verified); measles split from a cattle virus about 528 BCE but the jump to people is unproven (Düx et al. 2020, verified); Brucella melitensis was in Neolithic sheep about 8,000 years ago (L'Hôte et al. 2024, verified).
- **Persistence.** Measles needs about 250,000–300,000 people to persist in US cities (Bartlett 1960, verified) and broke off on every island under 500,000 (Black 1966, verified); varicella persists below 1,000 people because it hides and reactivates (Black 1966). Islands lose diseases 1.5 to 10 times more readily than connected countries: linked populations re-seed each other (Metcalf et al. 2013, verified). Mumps needs perhaps 365,000–781,000 (Pomeroy et al. 2023, verified).
- **Outbreaks against endemic disease.** Where smallpox was endemic (York) it caused about 10% of burials every year; in small settlements, when it came, 30–40% of a year's burials (Cambridge Group, verified). A London parish in 1665: 939 deaths, 670 from plague, four times its usual mortality (verified).
- **The shift to a childhood disease** follows survivor immunity: after the Faroes' 1846 measles epidemic (about 6,000 of 7,782 ill, at least 102 deaths), only those born since were susceptible, and those over 65, survivors of 1781, escaped (Panum, verified through a summary).
- **First contact.** No universal death rate: 12.8% on Rotuma in 1911 (Shanks et al. 2011, verified); a median of 18% of the population per epidemic across 117 Amazonian epidemics, falling with time since contact (Walker, Sattenspiel & Hill 2015, verified); Hudson Bay smallpox likely under 20%, not the 50% often claimed (Carlos & Lewis 2012, verified). The genetic "no immunity" account is weakly supported; high mortality is better explained by whole communities lacking acquired immunity at once, and by war, displacement and hunger (Jones 2003, verified; Jones et al. 2021 for California, verified through a press release).
- **Hunger and infection.** In the Irish famine, literal starvation was 3–9% of excess deaths; fevers 28–31%, dysentery and diarrhoea 21–28%, cholera 6–8%. About half of famine mortality came from the famine's effects on behaviour and society: migration, crowding in workhouses and relief works (lice: typhus, relapsing fever), lost hygiene. The synergy is uneven: some diseases depend heavily on food, others barely (Mokyr & Ó Gráda 2002, verified). The classic statement of synergy is Scrimshaw, Taylor & Gordon (1968), not read.
- **Behaviour.** The Acholi epidemic protocol (gemo): the sick housed 100 m apart, no visitors, a survivor as carer, no movement between villages, no sex, burial at the village edge without touching (Hewlett & Amola 2003, verified). People also blame: in 124 towns with Jewish communities, 47% persecuted them during the Black Death, most often where mortality was moderate (about 20%) and least where it was very high, which the authors explain as scapegoating against the value of the minority's services (Jedwab, Johnson & Koyama 2017, verified, working paper).

**What follows for the build (to compare with ChatGPT's check, then to Ben):**
1. Named diseases, each with a host animal or a wild source, a fatality by age, a severity and lasting immunity (or not).
2. Emergence where people live with herds, at a chance rising with the number of people and animals in contact and with how long they have lived together (Morand et al. 2014); a smaller wild-source chance.
3. Persistence emerging, not set: immunity per band by age (children, adults), births adding susceptibles, fade-out where too few are left, and re-introduction along the contacts the world already has (moves, marriage, partners, traders, war). No fixed critical community size and no fixed share of deaths.
4. Deaths: by age; more where hunger is high, for diseases that depend on food; and crisis deaths when many adults are ill at once (care and food production collapse). No genetic weakness at first contact.
5. Behaviour as customs: flight and dispersal; isolation protocols such as gemo; blame of outsiders or minorities, leading to violence (with M4b). Possibly a partial step now.

### Diseases: comparing the two literature checks (20 November 2026)

ChatGPT's independent check (written by ChatGPT into Notion; 19 sources, all Suggested) against Claude's (above). Claude checked two of ChatGPT's sources against their texts: the Kissidougou funeral cluster (Victory et al. 2015: 85 cases, 63 deaths, 18 from handling the body, 67 from contact with mourners) and the Bengal Famine Inquiry (1945: 1,873,749 registered deaths in 1943, 688,846 over the 1938–42 average, the true excess judged nearer one million; malaria and fever diagnoses unreliable).

- **Both found, independently:** no fixed rate of new diseases from animals can be defended; the "no immunity" genetic account of first contact is weak, and whole communities falling ill at once, war, displacement and hunger explain more (both cite Jones 2003); hunger and infection reinforce each other unevenly, by disease (Mokyr & Ó Gráda 2002; Ó Gráda 2007; Scrimshaw); traditional responses to epidemics can help or harm, and should not be assumed to do either (Acholi gemo, both).
- **Only ChatGPT found:**
  - the Americas had their own diseases before contact: tuberculosis in Peru about 1,000 years ago, related to seal lineages (Bos et al. 2014), and treponemes in Brazil about 2,000 years ago (Majander et al. 2024, with an editorial note of concern; Barquera et al. 2025). So the asymmetry at contact is not absolute;
  - spillover as stages: pressure from the animal source (its infection, contact with people, chance per contact), then a separate, chancy step to sustained spread among people (Lloyd-Smith et al. 2009);
  - funerals as a disease-specific hazard (the Kissidougou cluster), communities blocking outsiders and distrust of responders (Fairhead 2016), Cherokee isolation and dispersal (Kelton 2004);
  - iron supplements can raise death and admission where malaria is common (Sazawal et al. 2006): feeding does not protect against every infection.
- **Only Claude found:** shared diseases rise with time since domestication (Morand et al. 2014); 58% of human pathogens are zoonotic and emerging ones are not tied to one host type (Woolhouse & Gowtage-Sequeria 2005); half of Irish famine deaths came from the famine's social effects (Mokyr & Ó Gráda 2002); scapegoating, most likely at moderate mortality (Jedwab, Johnson & Koyama).
- **Disagreements:** none of substance. The two emergence ideas combine: spillover pressure grows with the number of animals and people in contact and with how long they have lived together; sustained spread among people is a separate, chancy step that depends on how many people can catch it.
- **Corrections:** none needed in either check so far; ChatGPT flagged its own uncertainties (Majander's editorial note, the Cochrane version).

### After Codex review 022 (20 November 2026)

All seven findings confirmed and fixed (`reviews/responses/022-review-021-fixes-claude.md`; tests `tests/test_land.py::Review022`, which fail on the code before the fix):
- **Crops grow only on crop land:** a herd's pasture no longer enlarges the fields.
- **The wild loss** is the season's harvest run again at the same effort with natural regrowth (`foraging.wild_gain`), broad-spectrum food included.
- **Crop losses** turn at every harvest and move with the people (`land.move_crop_loss`); soil and salt are cited on the cell where the crops grew (`land_crop_cell`).
- **Abandonment** restores only what the soil took (`farm_rr_lost`).
- **Wood work** is recorded as such (`tech_prev_wood`; coal smelting does not count), and one rule serves practice and explanations.
- **Fuel cutting** starts the forest's record.

**Ben's decision (20 November 2026): the land is a contributing cause of hunger.** After three reviews found flaws in "cite the land only if its loss would have covered the shortfall", that claim is dropped. A band that went short, and from which the land took food, gets one `land_hunger` event per season. The event states what lost game and forest took from its wild food and what worn soil took from its crops, against what it lacked, and cites every land event behind both. Gate checks on land and famine will be stated as exposure, not cause.

**Trial** (planet 3, year-9,700 save, 300 years; parameters are tunable starting values): land off 513,874; land on 324,815, so the land costs about 37% of the people here, as before.
- No invariant failures; 20 of 20 sampled move chains resolve.
- 7,439 `land_hunger` events: the land took a median 43% of what the band lacked (mean 50%).
- 4,900 of those events were wild food only, none crops only.
- 756 of 3,815 individual hunger deaths were in bands the land took food from.
- 67% of lived-in cells have no wood within reach; many are in treeless biomes.
- One history.

### Diseases from animals, as built (20 November 2026)

Ben's decisions (20 November 2026): the full model now; flight and isolation now, blame with M4b; hunger's effect per disease. `origins/sim/disease.py`, yearly at the season of M1's outbreaks, from a new random stream "disease" (appended). `DISEASE` False brings back M1's outbreaks, the knock-out. All values are starting values.

- **Named diseases:** each has its own traits, drawn when it appears:
  - attack (`DZ_ATTACK_RANGE`);
  - deaths per adult case, log-uniform from 0.5% to 30% (`DZ_CFR_RANGE`);
  - children's deaths against adults' (`DZ_CHILD_MULT_RANGE`), and people of 50 and over twice adults';
  - lasting immunity or not (`DZ_LASTING` 0.8; waning 20% a year otherwise);
  - how much hunger raises its deaths (`DZ_HUNGER_RANGE`);
  - k, how many people who can still catch it it needs nearby to keep going.

  Each has a `new_disease` event; each year's epidemic of each disease is an `outbreak` event citing it.
- **Emergence:**
  - **from herds:** each year on each cell, chance `DZ_EMERGE_HERD` 2e-7 × people herding a domesticated species × min(1, years since the species was first domesticated / `DZ_DOM_YEARS` 2,000) (Morand et al. 2014);
  - **from wild animals:** `DZ_EMERGE_WILD` 2e-8 × people.
- **Reservoirs** (Ben, 20 November 2026, after the first trial): a disease that dies out among people lives on in its animals and can pass again:
  - herd diseases where people herd their species (`DZ_RESPILL_HERD` 2e-5 per herder a year);
  - wild ones anywhere in the climate region where they first appeared (`DZ_RESPILL_WILD` 2e-6 per person a year);
  - most such starts are short-lived (Black 1975; Lloyd-Smith et al. 2009).
- **Immunity per band, children and adults:** survivors are immune; each year a fifteenth of children become adults and newborns arrive with none, so a disease that stays shifts to children. Joining bands combine immunity by numbers.
- **Persistence:** a disease circulating on a cell keeps going next year with chance 1 − exp(−people who can still catch it on the cell and its neighbours / k). k is log-uniform from 3,000 to 500,000 (Ben, 20 November 2026, raised from 300–30,000 after the reservoir trial; Bartlett 1957 measured about 250,000 for measles; Black 1975).
- **Spread:** to cells within two rings, partners' cells and traders' seats, with chance `DZ_SPREAD` 0.3 × attack × the share who can catch it there × (1 + `DZ_FAMINE_SPREAD` 2 × hunger at the source) × the response's carry factor.
- **Deaths:** by age, × (1 + the disease's hunger trait × shortfall × `DZ_HUNGER` 2), doubled when half or more of a band's adults are ill at once (`DZ_CRISIS_SHARE`; Jones 2003). No genetic weakness at first contact.
- **Responses:** the custom "response to epidemics" (carry on / flight / isolate the sick). The sizes are guesses: neither literature check found measured effects.
  - **flight:** attack × 0.7, carried × 1.5;
  - **isolating the sick:** attack × 0.6, carried × 0.5, crisis deaths halved (Hewlett & Amola 2003).
- **Records:**
  - saves keep diseases, immunity and circulation, all in the digest;
  - the G3 record lists the diseases and each outbreak (year, disease, cells, deaths), the spillovers, and a cause-chain check;
  - G1's exposure counts carry on.

**Trials** (planet 3, `snap_p3s1_8500_plus1200.zip` at year 9,700, 300 years, `local/scripts/trial_disease.py`; no invariant failures in any; one history):

| Run | People at the end | Deaths from disease | From hunger | Diseases (outbreak events) |
|---|---|---|---|---|
| M1 outbreaks (`DISEASE` False) | 318,095 | 18.8% | 4.7% | (380) |
| Named, first rates (wild 2e-9, no reservoirs, k 300–30,000) | 363,491 | 24 deaths | 10.6% | 1 (1) |
| + reservoirs, wild 2e-8 | 341,441 | 4.1% | 10.1% | 2 (140), both still circulating after 70 years |
| + k 3,000–500,000 (as built) | 360,397 | 0.9% | 10.7% | 2 (79), circulating 34 and 45 years, then gone |

- **No herd diseases on planet 3 here:** no animal is domesticated by year 10,000 (cattle only cultivated), so none can arise. A GitHub trial runs the four herding histories of G3 with diseases on and off.
- **Before herds, epidemics are rare and short-lived,** as Black (1975) found among isolated peoples. Everyday illness stays in the background deaths ("accident or illness", 37% of all deaths in this history). M1's carried-forward item (outbreaks about 9% of deaths) is answered by this design rather than matched.
- **Hunger's share of deaths rises** (about 4.7% to 10.7%). *The reading that this is because epidemics no longer thin crowded regions is withdrawn (Codex review 028): the change in causes also changes both denominators, and the arms follow different population paths.*
- **Diseases kill adults too:** about 28–33% of disease deaths were children under 15. Lasting immunity in adults builds up only where a disease keeps returning.

### After Codex review 023 (20 November 2026)

All five findings confirmed and fixed (`reviews/responses/023-review-022-fixes-claude.md`; tests `tests/test_land.py::Review023`, which fail on the code before the fix):
- **Harvest when nobody farms:** standing crops are still brought in.
- **A small band joining another** brings its standing crop and its crop loss. A band that ends with nobody to take its fields loses both.
- **Crop losses keep the soil and salt events of the fields they came from**, recorded when the crops were grown (`land_crop_ev`, `land_acc_ev`; `land_crop_cell` is gone). A later sowing elsewhere, a move or the fields' recovery no longer changes them.
- **A `land_hunger` event counts as the land's only the pools with a linked event.** Other losses are stated apart (`unlinked`). The note says the crop figure is the harvest's loss spread over the year, and gives no capped percentage.
- **Every band-season of exposure is counted** (`w.counts`, `land_exp_*`). The `land_hunger` events are a sample made where deaths are recorded.

**Trial** (planet 3, year-9,700 save, 300 years; tunable starting values; no invariant failures; one history): land off 503,114; land on 326,460, so the land costs about 35% of the people here.

Every band-season, land on:
- 80,344 band-seasons were short of food;
- 67,259 of them (84%) had a land loss linked to a recorded event: wild food only 43,116, crops only 1, both 24,142;
- the linked losses, capped at what each band lacked, came to 45% of all food lacked.

So in this history lost game and forest touch most shortfalls, and worn soil almost never does so alone. This is exposure, not cause.

Deaths:
- 797 of 3,829 individual deaths from hunger (21%) are linked to a `land_hunger` event;
- 1,057 of the 7,732 events also record losses tied to no event.

### After Codex review 024 (20 November 2026)

All five findings confirmed and fixed (`reviews/responses/024-review-023-fixes-claude.md`; tests `tests/test_land.py::Review024`, which fail on the code before the fix). The "largest season stands for the year" shortcut is gone:
- **Exact linked amounts:** the soil part and the salt part of each season's crop loss are booked as linked (`land_acc_k`, then `land_crop_k`) only where that condition has a recorded event and actually reduced the yield;
- **Events as examples:** an event is kept only as the example a record cites, and moves with its own loss;
- **One factor test:** the exposure count uses the same factor tests as the events;
- **Older saves:** crop amounts from older saves are carried as unlinked, and they load safely with the land off.

**Trial** (planet 3, year-9,700 save, 300 years, land on; tunable starting values; one history):
- The fixes change records only: 326,460 people at the end, as before, with no invariant failures.
- 80,344 band-seasons were short of food. 67,259 of them (84%) had a linked land loss: wild food only 43,044, crops only 1, both 24,214.
- Linked losses came to 45% of all food lacked.
- 1,594 of 7,732 `land_hunger` events also record unlinked losses.

### After Codex review 025 (20 November 2026)

Both findings confirmed and fixed (`reviews/responses/025-review-024-fixes-claude.md`; tests `tests/test_land.py::Review025`):
- an example event's season loss is now shared on a partial move, so a later larger loss can replace it;
- a rounding remainder between the crop loss and its parts no longer counts as unlinked.

Both change records only. Codex found the land and hunger accounts otherwise sound: parts sum to the loss, the exposure count matches the events under every knock-out of the yield shares, and replay is exact.

### After Codex review 026 (20 November 2026)

- **Examples:** an example event's comparison value is the linked loss attributed to it so far. It adds up across seasons and across rejoined parts of a band that cite the same event, so the example is the event behind the most attributed loss among the examples compared. During the year a move compares the two examples' own losses (Codex review 027); once the harvest has passed, no example values are kept, and for last year's loss the larger linked part decides.
- **The rounding tolerance** (1e-9 of a band's losses) can also hide a genuine remainder that small. That is negligible as food; it affects only the note and the tally.

Records only.

### After Codex review 028 (20 November 2026)

All six findings confirmed (`reviews/responses/028-diseases-from-animals-claude.md`; tests `tests/test_disease.py::Review028`):
- **Immunity of joining people** is weighted by their share of the band after the move. It was counted twice before.
- **Deaths and immunity by cohort** (`disease.cohort`): the ill, the dead (never more than the ill), and immunity among survivors.
- **Pregnancies after deaths:** pending pregnancies are kept in proportion to surviving women of 15–49, rounded to whole counts, on every path that removes people from groups: ordinary deaths, hazards, war and diseases. This changes births slightly in every history.
- **G1's contact test** is counted in matched units, disease by disease.
- **A per-cell record of every epidemic** (`w.dz_log`; in the G3 record). It holds how the disease came and from which cell, the people, the share who could catch it, whether the bands there had never met it (`dz_seen`), and the cell's deaths. G1's hazard watch follows named diseases cell by cell from it.
- **The knock-out** (`DISEASE` False) is a switch within the current code, not a replay of pre-disease histories: the epidemic-response custom is still there and changes other draws.

**A further error of mine, caught in trial:** the first version kept fractional pregnancies, which a later group split drove negative (`n < 0` in births). Both local trials and the first GitHub rerun crashed on it. Pregnancies are now whole counts, with a test.

**Ben's decision (20 November 2026): G4a check 10 marks where diseases last.** Diseases that keep circulating for years are found mostly where herds and dense populations meet. Wild and small-group starts happen but fade. Deaths after first contact are heavier among peoples who had never met the disease. The specification is updated.

**Trial** (planet 3, year-9,700 save, 300 years; tunable starting values; no invariant failures; one history; the histories diverge from the trials above):

| Run | People at the end | Deaths from disease | From hunger |
|---|---|---|---|
| Diseases off (M1 outbreaks) | 326,491 | 18.7% | 4.5% |
| Diseases on | 358,896 | 317 deaths | 10.7% |

With diseases on, one wild disease appeared (k about 258,000) and circulated for 3 years on one cell. The GitHub herd pair runs on one commit (`66dea8c`) in three herding histories: runs 44688553058 (on) and 44688555405 (off).

### After Codex review 029 (20 November 2026)

All six findings confirmed and fixed (`reviews/responses/029-review-028-fixes-claude.md`; tests `tests/test_disease.py::Review029`):
- **Pregnancies move with the women** who split off or transfer, and are capped at the number of women of 15–49, also after maternal deaths.
- **Adults' immunity among survivors counts the deaths of people of 50 and over,** at a fixed share of adults (`DZ_OLD_SHARE` 0.15, a starting value).
- **Each epidemic in a year starts from the people left by the earlier ones.** G1's hazard watch follows named epidemics on the cell alone.
- **G1 check 9 counts arrivals by contact only.** Returns from the animals count among the other units; new diseases are counted apart (`dz_new_*`).
- **For check 10:**
  - each band keeps the last year each disease circulated among it (`dz_last`);
  - each row of the per-cell record holds the people and deaths of bands that had and had never met the disease, the years since they last had it, the herders on the cell, and the people on the cell and around it;
  - the G3 record samples whole diseases above 100,000 rows.

**Trial** (planet 3, year-9,700 save, 300 years; tunable starting values; no invariant failures; one history):

| Run | People at the end | Deaths from disease | From hunger |
|---|---|---|---|
| Diseases off (M1 outbreaks) | 329,166 | 19.6% | 4.4% |
| Diseases on | 357,507 | 328 deaths | 10.6% |

With diseases on, one wild disease circulated for 4 years on up to 9 cells. The full suite passes (222 tests).

### After Codex review 030 (20 November 2026)

All seven findings confirmed and fixed (`reviews/responses/030-review-029-fixes-claude.md`; tests `tests/test_disease.py::Review030`):
- **Pregnancies:** moving women are drawn among the women of childbearing age, pregnant or not; conceptions are capped at the women not already pregnant.
- **Older saves:** their epidemic rows are upgraded on loading (`upgrade_log`), and their exposure records keep "met at an unknown time".
- **G1:** it probes every year in its replay check. Named diseases count under their own keys, are reported apart from M1's outbreaks, and pass only with opportunities on both sides.
- **The G3 record** keeps every arrival row plus every unbroken spell of a disease on a cell, so nothing is sampled away.

**Ben's decisions (20 November 2026):**
- **First contact** is a disease arriving by contact from a place where it has circulated unbroken for at least a generation (`DZ_GENERATION` 25 years), into bands that had never met it. `dz_since` records when circulation began on each cell, and each per-cell row splits people and deaths into never met, met within a generation, and met longer ago.
- **The review loop:** one more short review of these fixes; anything further goes into the comprehensive pre-gate review.

**Trial** (planet 3, year-9,700 save, 300 years; tunable starting values; no invariant failures; one history):

| Run | People at the end | Deaths from disease | From hunger |
|---|---|---|---|
| Diseases off (M1 outbreaks) | 326,646 | 18.9% | 4.6% |
| Diseases on | 359,766 | 2,971 deaths (0.1%) | 11.0% |

With diseases on, five wild diseases appeared and circulated for 1–18 years on 1–6 cells each, then died out. The full suite passes (227 tests).

### After Codex review 031 (20 November 2026)

Four findings, fixed without a separate review (Ben's decision: anything after review 031 goes into the comprehensive pre-gate review, which is to verify them):
- **Spells:** a disease's spell on a cell restarts when it comes back after dying out there.
- **G3 spells** keep herders and nearby people year by year.
- **G1:** it dates named epidemics at the first probe after them, so the one-year follow-up is a year later.
- **Older saves:** named-disease counts under M1's keys are set aside as unattributed.

Records and gate code only; the simulation is unchanged.

**Open for the comprehensive review** (Codex's ranking):
- findings 1 and 2 block sign-off on check 10;
- finding 3 blocks G1's named-outbreak recovery results;
- finding 4 blocks mixed-version checkpoints for G1 check 9.

**Codex's reading of the trials:** they give examples of short wild-origin circulation. Neither a comparison of persistence in dense herding areas nor a qualifying first-contact comparison exists yet. Both need the gate's histories with herds.

### Writing and place names: literature check (Claude, 20 November 2026)

Independent check, done before ChatGPT's (the four questions are in the Notion research questions). Writing already exists as a technique in the network (tallies, then writing, with records that let a lost technique come back). This check is for refining it, and for building place names (specification section 7).

**Writing: the scale that comes first.**
- **Seshat** (285 polities): growth in scale comes first. Information processing (writing, texts, money) outpaces scale only once a polity is past a "scale threshold", and that in turn allows further growth: "to make major improvements in information processing, a polity must first surpass a scalar threshold" (Shin et al. 2020).
  - The threshold is on a composite measure, with no single population figure. Upper Egypt about 3600 BC sits near it.
  - Few New World polities in the sample cross it.
  - This fits the network's rule that writing needs tribute administration.
- **What early writing was for** (Postgate, Wang & Wilkinson 1995):
  - The Uruk tablets are "principally utilitarian": commodities, animals and people, with about 15% lexical lists for training scribes.
  - Early Egyptian labels had "primarily … an accounting" purpose.
  - The ceremonial look of early Chinese and Mesoamerican writing is likely survival bias: durable stone and bone for display, perishable media for records.
- **The token theory is contested.** Zimansky's (1993) review finds the categories of tokens loose and many unique. The supposed commodity links are "virtually disprove[d]" by the counts: sheep tokens are rare against "nail" tokens. He reads simple clay shapes as counters made independently.
  - So the build should keep tallies as one route to writing under administrative need, not a fixed token-to-sign sequence.
- **Large states without writing:** Inka khipu recorded census and social categories. Six colonial khipus have been matched to a 1670 census of 132 tributaries, encoding moieties, clans and status (Medrano & Urton, *Ethnohistory*, read through Harvard's report). Records without a script are possible, and the network's tallies can stand for them.

**Writing: who writes, and how it is lost.**
- **Few writers:**
  - Egypt: estimates run from 1–5% of the population, about 1% in the third millennium BC, rising to perhaps 7% by the fourth century BC (Baines 2007, via Zinn 2013).
  - Mycenaean Pylos: about 1,000 tablets by "just over thirty" scribes. Literacy was "monopolized" by the palaces, with no private records. Linear B lasted "no more than c. 300 years" (Palaima 2004).
  - Mesopotamia: functional literacy reached beyond professional scribes in some periods, among Old Assyrian merchants and some officials. A working syllabary could use as few as 68–82 signs (Charpin, via Altman's 2011 review).
- **Loss:** scripts die when their users restrict them to narrow functions and groups (Houston, Baines & Cooper 2003, via report). Linear B ended with the palaces that kept it.
  - For the build: writing kept by a few specialists tied to administration is fragile. When the polity that feeds them falls, the script can be lost. The network's keeping rule already ties loss to the number of skilled practitioners.
- **Spread by idea:** a script can spread by its idea alone, without its signs, as with Sequoyah's Cherokee syllabary (1809–1821; Jordan, after Kroeber's "stimulus diffusion"). For the build: neighbours of a writing people can invent their own script more readily (a contact boost to invention), not only copy one.

**Place names: survival when languages change.**
- **Major places keep their names, minor places do not** (Hall 2012):
  - in Anglo-Saxon England, about 31% of names attested to 731 are lost, against about 8% of Domesday names;
  - eleventh-century Welsh names were lost far more often than English ones (about 55% against 9%, on small samples);
  - Roman-British names survive at only about 17–20% in England;
  - "the names of major places were more stable than those of minor places".
- **Rivers:** pre-English river names such as *Thames* and *Humber* passed from older languages into Brittonic and then into English (Kitson 2011). The general claim that large rivers are the most conservative names is a textbook commonplace (Andresen & Carter 2015, via Wikipedia). I have not yet found a quantified cross-cultural test.
- **Conquest and remoteness** (Guangxi, 1,427 names; Wang et al. 2011):
  - the native Zhuang names survive more in remote, mountainous and less irrigated places, and less in higher administrative units (7% of prefectures, 25% of townships);
  - the Zhuang share of population explains about a third of the variance in Zhuang names by county.
  - For the build: newcomers rename most where they rule and farm, and least in remote uplands; units named by the state are renamed first.

**Place names: how peoples name.**
- **Foragers:**
  - a person knows roughly 500 place names;
  - place-name density rises with population density (r = 0.95 on logs, 12 communities; Hunn 1994);
  - Sahaptin names are very often descriptive of biological and topographic features, and none are named after people (Hunn 1996);
  - binomial names (generic plus specific) are rare in Sahaptin but common elsewhere.
- **A typology for coding names** (Tent & Blair 2011): descriptive, associative, occurrent (events), evaluative, shift (transferred), indigenous (borrowed), eponymous, linguistic innovation. In European naming of the Australian coast, eponymous names were the most common.
- **For the build:**
  - each people names the features it uses most first (water, landform, resources), descriptively, in its own words from the M1 lexicon;
  - names after people (founders, rulers) come with settlements and polities;
  - the number of names grows with population density;
  - newcomers keep or replace names by the kind of contact and by the feature (large rivers and major places kept most; minor places and administrative units replaced most), with the older names kept beneath as layers.

**Not yet found:**
- how long scribal training took (Old Babylonian schooling; Robson's study of House F at Nippur is cited, but I have not read it);
- a quantified cross-cultural rate of adopting versus replacing names by kind of contact.

#### Sources (added)

- Andresen, J. T., & Carter, P. (2015). *Languages in the World*. Wiley. (Through Wikipedia's citation; not read.)
- Altman, R. (2011). Review of D. Charpin, *Writing, Law, and Kingship in Old Babylonian Mesopotamia*. *Bryn Mawr Classical Review* 2011.06.55.
- Baines, J. (1983). Literacy and ancient Egyptian society. *Man* (NS), 18(3), 572–599. (Abstract read.)
- Hall, A. (2012). The instability of place-names in Anglo-Saxon England and early medieval Wales, and the loss of Roman toponymy. In R. Jones & S. Semple (eds), *Sense of Place in Anglo-Saxon England*, 101–129. Tyas.
- Houston, S., Baines, J., & Cooper, J. (2003). Last writing: script obsolescence in Egypt, Mesopotamia, and Mesoamerica. *Comparative Studies in Society and History*, 45(3), 430–479. doi:10.1017/S0010417503000227. (Conclusion through a press report.)
- Hunn, E. (1994). Place-names, population density, and the magic number 500. *Current Anthropology*, 35(1), 81–85.
- Hunn, E. (1996). Columbia Plateau Indian place names: what can they teach us? *Journal of Linguistic Anthropology*, 6(1), from p. 3; doi:10.1525/jlin.1996.6.1.3. (Abstract read; end page not checked.)
- Kitson, P. (2011). Notes on some interfaces between place-name material and linguistic theory. In D. Denison et al. (eds), *Analysing Older English*, 35–56. CUP. doi:10.1017/CBO9781139022170.006. (Summary read.)
- Medrano, M., & Urton, G. (2018). Toward the decipherment of a set of mid-colonial khipus from the Santa Valley, coastal Peru. *Ethnohistory*, 65(1). (Through Harvard Gazette's report.)
- Palaima, T. G. (2004). Mycenaean accounting methods and systems and their place within Mycenaean palatial civilization. In M. Hudson & C. Wunsch (eds), *Creating Economic Order*, 269–301. CDL Press.
- Postgate, N., Wang, T., & Wilkinson, T. (1995). The evidence for early writing: utilitarian or ceremonial? *Antiquity*, 69, 459–480. doi:10.1017/S0003598X00081874.
- Shin, J., Price, M. H., Wolpert, D. H., Shimao, H., Tracey, B., & Kohler, T. A. (2020). Scale and information-processing thresholds in Holocene social evolution. *Nature Communications*, 11, 2394. doi:10.1038/s41467-020-16035-9.
- Tent, J., & Blair, D. (2011). Motivations for naming: the development of a toponymic typology for Australian placenames. *Names*, 59(2), 67–89. doi:10.1179/002777311X12976826704000.
- Wang, F., Wang, G., Hartmann, J. F., & Luo, W. (2011). Sinification of Zhuang place names in Guangxi, China: a GIS-based spatial analysis approach. *Transactions of the Institute of British Geographers*. doi:10.1111/j.1475-5661.2011.00471.x.
- Zimansky, P. (1993). Review of D. Schmandt-Besserat, *Before Writing*. *Journal of Field Archaeology*, 20(4), 513–517.
- Zinn, K. (2013). Literacy, Pharaonic Egypt. In R. S. Bagnall et al. (eds), *The Encyclopedia of Ancient History*, 4100–4104. Wiley-Blackwell.

### Writing and place names: comparing the two literature checks (20 November 2026)

ChatGPT's independent check: 22 sources in Notion, all Suggested; its written summary is not yet in. Claude verified the ones the design would rest on:
- **Tent 2017:** read in full. Indigenous-derived names are 28.2% of Australia's gazetteer, 42.3% of New Zealand's and 96.9% of Fiji's (Table 1, p. 206, not p. 207 as given).
- **Kelley, Cartolano & Ferrara 2025:** read in full.
- **Zair 2023:** chapter 1 read.
- **Blair & Tent 2021:** abstract read.
- **Tent & Blair 2011:** found by both checks.

Several others could not be read here: the DOI links were blocked, or the page showed only a stub. These include Nissen 2016 on Uruk's size, Regulski 2016 on Egyptian literacy, Waal 2024 on the Aegean gap, Strandberg 2016 on river names, Urton 2017 on khipu, the Olmec Cascajal Block papers, and Veldhuis on Mesopotamian schools. They stay Suggested and are not used.

**Both checks found:**
- early writing grew from administration;
- the token theory is contested: Zimansky 1993 (Claude), and Kelley et al. 2025 (ChatGPT), who find seal motifs as precursors of some signs and say "token-to-sign comparisons, numerical notations aside, are rarely demonstrable";
- literacy in early writing societies was a few per cent;
- khipu as records without a script;
- Tent & Blair's typology of names;
- river names as the most persistent layer, though neither check found a quantified cross-cultural test.

**Only ChatGPT found:**
- **Names under colonisation** (Tent 2017): where settlers came in numbers, few native names remain; where they did not, nearly all do. This is the contact-type effect the build needs, though the figures are modern gazetteer shares, not survival rates.
- **Roman literacy:** Harris's estimates of at most 15% in Italy and 5–10% in the western provinces, called "guesstimates" (Zair 2023).
- **Unverified:** Uruk at about 250 ha (perhaps 25,000–50,000 people) when proto-cuneiform appeared (Nissen 2016); the Olmec Cascajal Block, about 900 BC; Meroitic script adapted from Egyptian.

**Only Claude found:**
- the Seshat scale threshold (Shin et al. 2020);
- the utilitarian origins and survival bias of early writing (Postgate et al. 1995);
- about 30 scribes at Pylos, and a palace monopoly on writing (Palaima 2004);
- scripts dying when restricted (Houston et al. 2003);
- major places keeping their names more than minor ones (Hall 2012);
- Zhuang names surviving in remote uplands (Wang et al. 2011);
- the 500-name repertoire and the link between name density and population density (Hunn 1994), and Sahaptin's descriptive names with none after persons (Hunn 1996).

**Disagreements:** none.

**Corrections:**
- Tent 2017's table page (206, not 207);
- Veldhuis's article is dated 2010 on the publisher's page, not 2015;
- ChatGPT itself flagged conflicting page ranges for Woods 2010.

**Still open:**
- how long scribal training took (neither check settled it);
- a measured rate of keeping versus replacing names by kind of contact. The nearest evidence is Hall's major-versus-minor places, Wang's remoteness, and Tent's settler-versus-non-settler gazetteers.

#### Sources (added, verified)

- Kelley, K., Cartolano, M., & Ferrara, S. (2025). Seals and signs: tracing the origins of writing in ancient South-west Asia. *Antiquity*, 99(403), 64–82. doi:10.15184/aqy.2024.165.
- Tent, J. (2017). Indigenous toponyms in the Antipodes: a gazetteer-based study. *Names*, 65(4), 204–214. doi:10.1080/00277738.2017.1369743.
- Zair, N. (2023). Introduction. In *Orthographic Traditions and the Sub-elite in the Roman Empire*, 1–44. Cambridge University Press. doi:10.1017/9781009327633.002.
- Blair, D., & Tent, J. (2021). A revised typology of place-naming. *Names*, 69(4), 30–47. doi:10.5195/names.2021.2260. (Abstract read.)

**ChatGPT's written report** (20 November 2026, after the sources) adds:
- **Emphasis:** the earliest surviving writing also includes royal ritual, divination and display. Postgate et al. (1995) argue this is largely survival bias. This is a difference of weight, not of fact.
- **Writing as several technologies:** tallies, seals, material records, specialist accountants and writing are related but distinct. Growing scale creates pressure to adopt them, with no fixed threshold that guarantees writing. This agrees with Shin et al. (2020), whose thresholds are "elastic and porous".
- **A palace collapse can take its script with it** without everyone losing the ability to write; the Aegean gap is disputed.
- **Names come from people's dealings with places.** There is no secure universal order in which features are named. One place can gather several names, translations and adaptations. Name forms should follow each language: generic plus specific, compounds, possessives, single words, and borrowed names whose parts are no longer understood.

ChatGPT lists Nissen 2016 and Regulski 2016 as read in full; I could not open either here, so their figures stay unverified (Uruk's size and population, and about 1% literacy in Old Kingdom Egypt).

### Writing and place names: Ben's decisions (20 November 2026)

1. **Names for used features.** Each people names the rivers, lakes, coasts, hills and mountains it lives among and uses, plus its own settlements, and later its polities and regions. Bigger rivers and landmarks are named by more peoples and kept longest. The number of names grows with population density (Hunn 1994).
2. **Keep or replace by rule.**
   - The chance that newcomers keep a name rises with the feature's size and fame and with remoteness, and falls with how many newcomers settle and with conquest (Hall 2012; Wang et al. 2011; Tent 2017).
   - A kept name is borrowed and reshaped by the newcomers' sound changes (M1).
   - Old names stay beneath as layers, with their cause recorded.
3. **Writing, all three refinements:**
   - **stimulus diffusion:** neighbours of a writing people invent a script more readily;
   - **the script falls with the state:** scribes are specialists fed by the polity, so its collapse can take writing with it;
   - **records without a script:** tallies and record-keepers give part of writing's boost to administration.

All values will be starting values.

### Writing and place names, as built (20 November 2026)

All numbers are tunable starting values in `params.py`, not facts.

**Writing (`origins/sim/technology.py`).**
- **The script falls with the state** (`TECH_SCRIBES`). Writing's practitioners are the band's scribes only (`skilled_by_technique`), not a quarter of its adults.
  - **Scribes** (`w.tech_scribes`, per band) are the specialists at the seat of a living complex chiefdom or state, averaged over about a generation: each year they move 1/25 of the way to this year's specialists there (`TECH_SCRIBE_YEARS`), or towards 0 for a band that is no seat. A village's leader, ritual specialists and craft workers do not keep a script.
  - **A people writes only where it keeps scribes** (at least one, `TECH_SCRIBE_MIN`): inventing, learning and practising writing all need them, and a cause names the lack ("needs scribes"). A people that loses its scribes stops practising; its writing fades as any unpractised technique does. Specialists are fed from surplus and staff the polity's seat, so when a polity can no longer feed them for years, its scribes dwindle and the script decays and can be lost (Palaima 2004 on Linear B and the palaces). One poor harvest does not erase it.
  - **Writing kept by scribes needs 30** within reach (`TECH_SCRIBES_KEEP`, about Pylos's thirty scribes), not the 60 it needs to be invented.
  - **The array:** grows with the bands, starts at 0 in a daughter (scribes stay with the band that fed them), is added when whole peoples combine or a remnant merges, is saved and in the digest; older saves start from that year's specialists.
  - Keeping, refining, the best practitioner within reach, teaching and lessons along traders' roads all count scribes for writing. Other techniques are unchanged.
  - **Ben's decision (21 November 2026), after the first trial:** with this year's specialists and 60 needed, writing given to the ten largest seats died out everywhere within 100 years (217 losses); seats' specialists often fall to 0 for a year, and with none writing goes in about six years. With the old rule (a quarter of adults) it spread to 2,477 of 3,865 bands. Ben chose steady scribes (a generation's average) and 30.
  - **Second and third trials (same save, 100 years, writing given to the ten largest seats):** with any band's specialists counted, writing spread to 1,969 bands, and with scribes required for practising, to 2,143 of 3,801. Specialists are common (about 12 a band, from M2's surplus), so a scribe has to be a polity's specialist, as Ben's decision says; scribes are now counted at seats only.
  - **Fourth trial:** with scribes at every seat, writing still reached 1,804 of 3,780 bands: there were 1,464 polities, most of them one village whose leader counts as a specialist. **Ben's decision (21 November 2026):** scribes are kept only at seats of complex chiefdoms and states (tier 2 or above, `TECH_SCRIBE_TIER`); writing follows scale (Shin et al. 2020). A polity that falls below that tier loses its scribes over about a generation.
  - **Fifth trial:** with tier-2 seats only, writing churned and died out (1,501 taken up, 1,440 lost, none left). It was being carried without scribes: daughters inherited it, and migrants, captives and spouses carried it into bands that could never practise it, where it faded. **Fix (no new design; follows the decision that scribes keep the script):** a daughter does not inherit writing (the scribes stay), and writing passes in `combine` only when whole peoples join (combined, merge), with their scribes. The trial script now also reports bands *practising* writing.
  - **Sixth and seventh trials (after the fix):**
    - given to the ten largest seats (none a complex chiefdom): 3 taken up, 5 lost, none left;
    - given to all 28 complex-chiefdom seats (20–38 specialists each): 8 taken up, 23 lost, none left after 100 years. Complex chiefdoms fell from 28 to 1 over the century.
  - **Why: complex chiefdoms do not last.** In the save's polity log (years 8,720–9,690), the 317 polities that ever reached tier 2 spent a median of 30 years there (90th percentile 160, longest 480). Scribes averaged over 25 years never build up at seats that fall within a generation. Writing now fails with the state, as decided, but the states here are too brief to carry it. Put to Ben.
  - **Full suite:** 243 tests pass (29.5 minutes), on the code with the fix.
- **Stimulus diffusion** (`TECH_STIMULUS`, writing x10). A people that could practise writing invents it ten times as readily when a people within two rings, or at the other end of a traders' road, writes well (`_stimulus`). The invention's cause names that people and says the idea, not the script, was borrowed. The new script is the inventor's own and starts crude, as any invention does.
- **Records without a script** (`TECH_RECORDS_SHARE` 0.3, `TECH_RECORD_KEEPERS` 10). Tallies kept by record-keepers at the seat give part of writing's capacity effect: writing's effect x 0.3 x tallies' quality x (specialists at the seat / 10, at most 1), as the khipu and its keepers did (Medrano & Urton 2018). Writing and kept tallies are not added; the larger counts.

**Place names (`origins/sim/places.py`, new; stream `places`, appended).**
- **Features** come from the planet, with no random draws:
  - rivers, split at each join (a stream continues up its larger branch, so tributaries are named apart); size from the flow at the stream's mouth (log scale);
  - lakes (joined lake cells, used from the land around them);
  - hills (local peaks of 800 m or more) and mountains (2,000 m or more), used from the peak and the cells around it;
  - coasts (joined coastal cells within one climate region);
  - settlements, made where a settled people or a polity's seat lives, sized by the most people seen there (log scale, full at 5,000); they outlast their people as named places.
- **Naming.** Every 10 years, each language with speakers by a feature, and no name for it in its own lineage, names it with chance 1 − exp(−10 x 0.02 x speakers by it / 100). The larger community by a feature names first. So big features, near more peoples, get more names, and dense land names sooner (Hunn 1994).
- **New names** are made from the people's own words: a descriptor from its lexicon (colours, size, age, animals, materials, by kind of feature) plus a generic word, or the generic word alone (river 25%), or, for settlements, a person's name plus "settlement" (30%). The generic words (river, lake, hill, settlement, sea) are PIE-inspired forms kept apart from the core vocabulary (`lang.proto.PLACE_PROTO`), so the vocabulary and its random draws are unchanged.
- **Keep or replace.** When a people meets a feature that people already by it have a name for, it keeps the name of the largest such community with chance
  (0.2 + 0.5 x size + 0.2 x remoteness) x (1 − 0.6 x the newcomers' share of the people by it), halved when those it hears it from were conquered by a polity of its own language within 100 years. Remoteness is 1 / (1 + people per cell of the feature / 200). Otherwise it gives its own name (Hall 2012; Wang et al. 2011).
- **Layers.** Each place keeps every name as a layer: [tick, language, form then, how (new, kept, replaced), the language it was heard from, cause]. A layer's form now is its form then carried through every later sound change of its language's lineage (`places.current`, as `language.word_history`). Daughter languages inherit their parent's names. A kept name is reshaped by the newcomers' own sound changes from then on.
- **Records.** Each name is an event `place_named` with its cause (resolvable). `w.places` is saved and in the digest; older saves start with none. `places.history(w, i)` lists a place's layers.

**Not built:** names for polities and regions (polities keep their present names), renaming a place a people already names (for example after conquest), and the observatory's display of place names.
