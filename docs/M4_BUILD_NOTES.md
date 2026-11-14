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

Code with skilled practitioners and refinement slowing near mastery, but **before** the stage-5 effects changes, the review-010 fixes and the new farming trigger (foraging gear then raised returns per day, which delayed farming). 2,000 years after each first village. Planet 4's history was still running.

| History | First village | Inventions | Adoptions | Lost for want of skill | Forgotten | People within reach at those losses (10th / median / 90th percentile) | Cause chains |
|---|---|---|---|---|---|---|---|
| planet 1, history 5 | 13,414 | 29 | 63,256 | 990 | 43,667 | 10 / 24 / 1,366 | 400 / 400 |
| planet 2, history 1 | 8,117 | 44 | 81,179 | 2,284 | 38,348 | 11 / 17 / 42 | 400 / 400 |
| planet 5, history 7 | 15,848 | 68 | 140,828 | 12,248 | 60,326 | 15 / 49 / 137 | 400 / 400 |
| planet 6, history 1 | 14,441 | 65 | 120,519 | 1,619 | 64,034 | 11 / 17 / 45 | 400 / 400 |

- **Isolation causes loss (gate check 5, first look):** half of all losses for want of skill happened where 17–49 people were within reach, against hundreds of thousands in the connected parts of each world. The losses are of the right kinds: the bow, fish traps, stone building, pottery, tallies and writing, in small or cut-off peoples.
- **Not yet shown:** the rate of loss per band at each level of contact (this needs the number of bands at each level, not only the losses). The G4a report must measure it.
- **Forgetting is very common** (38,000–64,000 per history), mostly farming techniques carried by migrants and marriages to peoples or land where they cannot be practised. They fade and are recorded as forgotten. Not wrong, but the gate should report the two kinds of loss separately.
