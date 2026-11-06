# M2 Specification — draft

**Milestone:** M2, "farming is an option, not a destiny" (behaviours 3 and 4)
**Status:** DRAFT for Ben's review. Items marked **DECISION** need Ben's answer; numbers are starting values to be tuned, not established facts.
**Builds on:** M0 (closed 6 November 2026), M1 (closed 7 November 2026) · Design Draft v0.5
**Date:** 7 November 2026

---

## 1. What M2 is for

M1 ends with a world of foragers who have spread across their land and drifted into hundreds of peoples. M2 lets some of them, in some places, **start to farm**. Farming should not be a scripted stage everyone reaches: it appears where useful wild species, a suitable climate and the pressure of numbers come together, spreads by people and by example, and leaves some regions foraging for good. Where farming takes hold, stored harvests make room for people who do not produce food, for leaders and for property, and so for inequality.

Behaviours tested (Design Draft section 11):

- **3. Farming is an option, not a destiny.** Adoption dates vary widely across histories; some regions stay foraging.
- **4. Surplus creates specialists, hierarchy and property. No surplus, no specialists.** The share of specialists follows surplus; turning food storage off prevents them.

M2 also brings the **switch from the prehistoric to the historical clock** (300 years per real day to 10–25), triggered by the first lasting farming village.

Out of scope for M2 (later milestones): chiefdoms and states, war and conquest (M3); the general technology network, metals, trade (M4); religion (M5).

---

## 2. From wild plants to crops

The world already places nine wild progenitors unevenly (grains, legumes, tubers, rice; goats, sheep, cattle, pigs, horses). In M2 they matter.

| Stage | What happens | How it is reached |
|---|---|---|
| **Wild use** | Bands in land with a wild progenitor gather or hunt it like any other wild food. | Living there |
| **Tending** | A band that stays long in one area and leans on a wild plant begins to tend it: weeding, sowing, protecting stands. A little more food, more work, less moving. | Low mobility + reliance on the species (both measured) |
| **Cultivation** | Tended stands are sown deliberately each year. Knowledge of the species is now a skill the band holds; it passes to daughters and can be learned from neighbours who hold it. | Years of tending |
| **Domestication** | Long cultivation changes the plant or animal (larger seeds, non-shattering heads, tamer herds): higher yields, but dependent on people. Domesticated forms can be **carried** to other suitable land. | Several centuries to a couple of thousand years of cultivation (PROPOSED: a progress counter per species and people) |

Animals follow the same path (wild hunting → managing herds → herding → domestic animals that give meat, milk, hides, later traction).

Real-world note, used as a plausibility guide, not a target: the transition was slow, plants were cultivated for a long time before visibly domestic forms appear, and it happened independently in only a few regions.

---

## 3. Farming as a way of life

**Food.** Each land cell gets a **farming capacity** for each domesticate it can grow (from climate, rainfall, rivers and soil fertility), much higher per area than foraging (PROPOSED: 5–20 times, set by land quality and the crop) but needing more work per unit of food, especially at first.

**Choice, not destiny.** Every year each band or village splits its work between foraging, herding and farming by comparing **food per hour of work** and **reliability** for each, with some inertia from custom. Foraging stays the better choice where wild food is plentiful; farming wins where people are many and wild food per person is low. Nothing forces adoption: bands with plentiful wild food can keep foraging indefinitely, even next to farmers.

**Risk.** Harvests concentrate risk: a bad year (climate, flood, pests) hits a field harder than a wide foraging range. Storage is the answer (section 4), and also one source of the famines the design wants to emerge on their own.

**DECISION 1 — When can farming begin?** The world has no ice ages by default (glacial cycles are an option, off). In the real world farming appears only after the end of the last ice age; one well-known argument is that the late Pleistocene climate was too variable for farming to be worth it (Richerson, Boyd & Bettinger 2001). Options:

- **A. Whenever conditions allow (PROPOSED).** No date and no ice-age rule: farming can appear tens of thousands of years earlier than on Earth if a people meets the conditions. Most faithful to "no fixed timetable".
- **B. A variable early climate.** Year-to-year climate swings are larger for the first part of every history and settle down over time (an Earth-like pattern without full ice ages), which makes early farming risky without forbidding it.
- **C. Tie it to the ice-age option.** Farming is possible at any time when glacial cycles are off; when they are on, it follows the climate.

---

## 4. Storage, settlement and the first villages

- **Storage.** Grain and legumes keep for a year or more in pits, baskets and later pots; tubers and meat keep less (PROPOSED spoilage rates by food type). Foragers already carry a small store (M0); farmers can store much more, and stores belong to households.
- **Settling down.** A band whose food comes mostly from fields and stores stops moving and becomes a **village**: a fixed place with houses, fields around it and a name (from its people's language). Villages grow, split (daughter villages on new land), and can be abandoned.
- **First farming village.** When a village has relied on crops for most of its food for three generations (PROPOSED: about 75 years), the world records **"the first farming village"** with its full cause chain, and the clock switches (section 7).

---

## 5. People in farming villages

These follow the evidence for a **Neolithic demographic transition**: births rose with farming and settled life (Bocquet-Appel 2011), so populations grew, but so did crowd illness.

- **Births:** settled life and weaning foods (gruel, milk) shorten the gap between births (PROPOSED: lower nursing suppression for farmers).
- **Health:** dense, settled villages living near animals and their waste have more illness (PROPOSED: outbreak rate rises with settlement size and herds). This also answers M1's open item: outbreaks among scattered foragers will be made rarer, and most epidemic deaths will come where people are crowded.
- **Food limit still holds:** the population ceiling rises with farming but does not disappear (behaviour 8 belongs to M6).

---

## 6. Surplus, specialists, hierarchy and property

Testart (1982) argued that **storage**, more than farming as such, goes with settled life, high density and inequality among hunter-gatherers. M2 follows that: everything below hangs on stored surplus, so that foragers who store heavily (rich fishing coasts, for instance) can show some of it too.

- **Surplus** = stored food beyond what a household needs to reach next harvest.
- **Specialists:** when a village's surplus can feed people who do not produce food, some people become specialists (PROPOSED for M2: craft workers, ritual specialists, and leaders). Their share is set by the surplus available, not by a rule; when surplus fails, they go back to the fields. Specialists are named individuals where individuals are followed.
- **Property:** fields and stores belong to households and pass to heirs. Bowles & Choi (2013) argue that farming and private property arose together, because farming made property easier to define and defend. Households that do well accumulate; inheritance carries advantage forward.
- **Hierarchy (minimal in M2):** the household with the largest store or the most kin often leads the village (its head is a **notable**: stays individual, can be prayed through later, M5). Chiefdoms and states are M3.
- **Measures:** share of specialists, inequality of stores and land between households (Gini coefficient), and how these follow surplus.

**Knock-out test:** a world option that turns storage off. Behaviour 4 requires that without storage no specialists appear and inequality stays low.

---

## 7. The clock switch

When the first farming village is recorded, the observatory clock changes from 300 simulated years per real day to the historical rate (the simulation's own steps do not change; only how fast the observer's clock runs).

**DECISION 2 — Historical clock rate.** Design Draft range: 10–25 simulated years per real day. PROPOSED: **20 years per day** (about 600 years from first farming to the end of a real year), adjustable later.

---

## 8. Carried from M1

- **Outbreaks** are made density-dependent (section 5).
- **Island divergence:** M1 showed that isolation alone does not make island languages diverge faster. **DECISION 3:** add a founder effect (a small group that splits off by sea takes a shifted share of the language's words and changes faster for a few generations; PROPOSED), or leave it as an honest negative result. Whether small populations change language faster is debated among linguists, so this would be a modelling choice, not an established fact.

---

## 9. What the observer sees

- Map layers: **farming** (fields by crop, herds, villages, foragers), **spread of farming** over time (first dates by region), **surplus and specialists**.
- Village pages: houses, households, fields, stores, specialists, leading household; the village's history.
- The world's first farming village and the switch of the clock, with its full cause chain.
- Each crop's and animal's story: where it was first tended, cultivated and domesticated, and how it spread.

---

## 10. Performance

Farming multiplies population (perhaps to millions), and gate histories must run until farming appears, which may take tens of thousands of years. Gate G1 histories took 13–53 minutes for 5,000 years. M2 needs:

- a **second speed pass** (the largest costs are band movement, splitting and merging, and partnerships), and
- villages represented compactly (households as rows, not individuals, beyond the followed area), extending M0's groups.

**DECISION 4 — Gate size.** PROPOSED: 50 histories (5 planets × 10), each run until 3,000 years after its first farming village or to 25,000 years, whichever comes first; plus 20 short knock-out histories with storage turned off. At M1's speed this would take days of computing on two cores, so the speed pass decides whether 50 is reachable; running histories in parallel elsewhere is one option (see the separate note on GitHub).

---

## 11. Gate G2 (PROPOSED pass marks)

| # | Check | Pass mark |
|---|---|---|
| 1 | **M0 and M1 still hold** | G0 and G1 checks still pass where they apply |
| 2 | **Farming needs its conditions** | Domestication starts only where a wild progenitor lives; no farming village without a domesticate |
| 3 | **Adoption dates vary widely** | First farming dates spread over at least several thousand years across histories on the same planet; in some histories no farming appears by the end |
| 4 | **Some regions stay foraging** | In at least 80% of histories with farming, foragers still hold land with wild food at the end |
| 5 | **Farming spreads by people and example** | Farming spreads outward from its centres over time; crops reach land where they were never wild |
| 6 | **Demographic transition** | Farmers' birth rates and densities exceed foragers' in the same histories |
| 7 | **Specialists follow surplus** | Across villages and years, the share of specialists rises with surplus per person (clear positive correlation) |
| 8 | **No storage, no specialists** | In the knock-out histories, no specialists and low inequality |
| 9 | **Property and inequality** | Inequality between households rises with time and surplus where property is inherited |
| 10 | **Traceable transition** | Every first-cultivation, domestication, first-village and clock-switch event has a complete cause chain |
| 11 | **Speed** | Reported; target set after the speed pass |

---

## Sources

- Bocquet-Appel, J.-P. (2011). When the world's population took off: the springboard of the Neolithic demographic transition. *Science*, 333(6042), 560–561.
- Bowles, S., & Choi, J.-K. (2013). Coevolution of farming and private property during the early Holocene. *Proceedings of the National Academy of Sciences*, 110(22), 8830–8835.
- Richerson, P. J., Boyd, R., & Bettinger, R. L. (2001). Was agriculture impossible during the Pleistocene but mandatory during the Holocene? A climate change hypothesis. *American Antiquity*, 66(3), 387–411.
- Testart, A. (1982). The significance of food storage among hunter-gatherers: residence patterns, population densities, and social inequalities. *Current Anthropology*, 23(5), 523–537.

(Bibliographic details checked against Crossref records, 7 November 2026.)
