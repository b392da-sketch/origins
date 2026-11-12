# M4 Specification: v1

**Milestone:** M4, "knowledge accumulates, spreads and can be lost" (behaviour 7), with trade and the additions agreed for M4 (Design Draft v0.6, section 16)
**Status:** approved by Ben on 12 November 2026, every proposal accepted (section 13). M4 is split into M4a and M4b. M4b is specified in detail after G4a. Numbers are starting values to be tuned, not established facts; remaining "PROPOSED" labels mark starting values, not open decisions. Building starts when M3 closes.
**Builds on:** M0–M2 (closed) and M3 (G3 run 2 in progress) · Design Draft v0.6
**Note:** written while G3 run 2 runs. Nothing in it changes M3.

---

## 1. What M4 is for

By the end of M3, the world has foragers and farmers, villages, chiefdoms and some states, wars and conquest. What it does not have is **knowledge as a thing of its own**. Farming skill exists (M2), and institutions are discovered and copied (M3), but there are no techniques in general: no pottery, metals, boats, writing or wheels. Peoples do not exchange goods other than by tribute and raiding.

M4 adds:

- **A technology network** (section 3): techniques with prerequisites. They emerge from need, materials and connected population; they spread by contact, trade and migration; and they are **lost** when populations shrink or are cut off.
- **Trade** (section 4): goods that move between peoples, carrying knowledge with them.

These two are what behaviour 7 tests:

- **7. Knowledge accumulates, spreads and can be lost.** Innovation tracks connected population, diffusion follows contact, and isolation causes loss.

Design Draft section 16 also attaches a long list of additions to M4:
- military technology, methods of warfare, logistics, reconnaissance and strategy;
- crime, norms and enforcement;
- lineages, personal ties and reputation;
- people changing the land;
- diseases from domestic animals;
- writing, chronicles and place names.

### 1.1 Proposal: split M4 into two milestones

M4 as listed is about twice the size of M3, and M3 took several gate runs. One very large gate means that when a check fails, it is hard to tell which of a dozen new systems is responsible.

**Proposed:**

| | Builds | Gate |
|---|---|---|
| **M4a** "knowledge and exchange" | the technology network; trade; people changing the land; diseases from domestic animals; writing (as a technique) and place names | G4a: behaviour 7, plus land and disease checks |
| **M4b** "how wars are fought, and who people are to each other" | military technology (as nodes in M4a's network); methods of warfare and logistics; reconnaissance and strategy; crime, norms and enforcement; lineages, personal ties and reputation; chronicles | G4b: warfare, crime and personal-ties checks, including the knock-out of personal ties (section 16, item 19) |

The order follows dependence. Military technology needs the network, chronicles need writing, and lineages and ties need the M3 notables.

**Decision 1 for Ben:** split, or keep M4 whole.

---

## 2. Before anything else: carried forward

1. **States arrive too early** (from M3, Ben's decision of 12 November). In G3 trials they come 363–1,458 years after the first village, against 2.7–3.1 millennia historically (Borcan, Olsson & Putterman 2021). M4 adds two brakes that the literature names:
   - knowledge has to accumulate first: writing, metals and administration as techniques, not free;
   - Carneiro's (1970) circumscription: villages leave a heavy ruler while there is open land to leave to.

   **PROPOSED:** add the second as a small M3-level rule at the start of M4: a member settlement under heavy tribute may move to open land within reach. Then measure the lag again.
2. **Seat-unfolding churn** (M3 build notes, 12 November): seats fold and unfold as their polities cross the chiefdom line, which costs about 15% of the farming era's time and cuts family lines at seats. Protect a seat for a while (for example 100 years) after it unfolds. **This comes first, because M4b's lineages depend on unbroken lines at seats.**
3. **Herding economies barely exist.** On planet 3, herds are under 13% of farming in 90% of village-years, and all five planets have similar wild animals. Mobile pastoralism, as among the herders of the steppe and East Africa, is missing: villages farm where crops grow, and nobody lives mainly from herds in dry land. This matters for check 9 of M3 (inequality rises with herds) and for M4b's cavalry. **PROPOSED:** in M4a, a pastoral way of life on dry grassland, moving seasonally with herds. Decided with G3 run 2's results.
4. **The on-disk event store** (agreed for M4): G3 histories reach 4 million events. The compact store added on 11 November is enough for M3, but M4 adds goods, techniques and trade, so the record moves to disk.
5. **Island peoples do not diverge faster; outbreaks cause about 9% of deaths** (from M1). Section 9 takes up outbreaks.
6. **Working arrangements:**
   - the local runner in Claude Code (section 16, item 22; handover note written);
   - Codex as independent reviewer from M4 (Ben, 12 November), starting with a review of the M3 gate.

---

## 3. The technology network

### 3.1 Techniques as nodes

A **technique** is a piece of knowledge a people can hold.

**Each technique has:**
- **Prerequisites**:
  - other techniques (bronze needs copper-working and a hot-enough kiln);
  - **materials** in reach (copper ore, tin, clay, suitable wood or stone; from world generation, which already places some minerals);
  - **people enough to keep the skill**.
- **What it does**: a change to something that already exists, never a free bonus. For example:
  - pottery: storage losses fall, and cooked cereals and pulses go further;
  - boats: some sea crossings open, and fishing yields rise;
  - irrigation: crop yields on river land rise, and salting can follow (section 8);
  - metals: tools first, then weapons in M4b;
  - the plough with draft animals: more land per household, and compounding inequality (Kohler et al. 2017);
  - writing: officials' capacity rises (section 10).
- **How hard it is to keep**: how many skilled people it needs, and how much practice. Simple techniques survive in small groups; complex ones need many people and specialists.

**About 25–35 techniques for M4a, PROPOSED**, chosen because each has a clear effect on systems that already exist:

| Group | Techniques |
|---|---|
| Foraging | fire-hardening, cordage and nets, fish traps, bow and arrow, canoes |
| Containers | baskets, pottery, kilns |
| Farming | terracing, irrigation, manuring, the plough, draft animals, milking, wool |
| Building | mud-brick, stone building, fortification (its war effect comes in M4b) |
| Metals | copper-working, smelting, bronze (needs tin), iron |
| Moving | sail, wheeled carts, pack animals |
| Recording | tallies and tokens, writing |

The real sequences are the starting point. Metallurgy in Eurasia grew out of high-temperature kilns, smelting came after the working of native copper, and bronze needed tin brought from far away (Roberts et al. 2009). Writing in Mesopotamia grew out of accounting tokens (Schmandt-Besserat 1992).

**There is no timetable.** Nothing in the code says when a technique should appear.

### 3.2 Emergence: why a people invents something

Each year, for each people (a culture, as in M1) and each technique whose prerequisites it meets:

> chance = base rate × need × connected skilled population × materials in reach

- **Need** is pressure the people actually face, measured from what is already computed: hunger and stores for containers and farming techniques, crowded land for irrigation and the plough, war for fortification, the burden of tribute accounting for tallies and writing.
- **Connected skilled population** is the people's own skilled members, plus those of peoples it is in regular contact with, weighted by how much contact there is. This is the "effective population" of the demography hypothesis (Henrich 2004; Powell, Shennan & Thomas 2009).

Every invention records its causes, for example "invented by the X, under pressure of hunger (stores below half a year's need for 6 of 10 years), with 1,400 skilled people in contact; copper ore within 2 cells".

**The debate about population size is real, and the design must not bake one side in:**
- **For:** Henrich (2004) on Tasmania; Kline and Boyd (2010) found that population size and contact predict toolkit complexity across ten Oceanic island societies; Derex et al. (2013) found the same in laboratory experiments.
- **Against:**
  - Collard, Kemery and Banks (2005) found that risk (temperature, plant productivity) predicted hunter-gatherer toolkits, and population size did not.
  - Vaesen et al. (2016) argue that the demographic models hold only under implausible conditions, and that the archaeological and ethnographic evidence does not support them.

**PROPOSED:** both population and risk enter the chance of invention (risk through need). The gate then measures which matters in the simulation, so the result is an outcome, not an assumption. A knock-out run with the population term switched off shows how much rests on it (section 11).

### 3.3 Keeping and losing knowledge

Each technique a people holds has a number of skilled practitioners. Each year, practitioners teach the next generation, imperfectly. The best teacher sets the standard, and learners fall a little short on average, with chance variation (Henrich's 2004 model).

- With many learners, a few exceed the teacher and the skill holds or improves.
- With few, the skill degrades. Below a minimum, the technique is **lost**, with its cause recorded: "lost when the X fell below 40 people who practised it, after the famine of year Y and the loss of contact with the Z."
- **Contact restores.** A people in contact with others who hold the technique can relearn it, more easily than inventing it.

### 3.4 Diffusion: how knowledge spreads

A technique spreads to a neighbouring people by three routes, each recorded:

- **contact:** neighbours who meet, in proportion to shared borders and cultural closeness;
- **trade:** partners exchange knowledge with goods (section 4);
- **migration and capture:** people moving or taken as captives carry their skills (M3's captives already exist).

Adopting needs the prerequisites and materials, as inventing does. Diffusion is far more likely than independent invention, so most peoples get most techniques from others. The record shows the path: "learned pottery from the Y through trade, year Z."

---

## 4. Trade

### 4.1 Goods

- **A small set of goods, PROPOSED:** food (from stores), salt, fine stone (flint, obsidian), metals and ore, textiles, pottery, livestock, and prestige goods (shell, amber, gold).
- **Nothing from nothing:** each good has a source (a deposit, a herd, a craft specialist's work) and a ledger, like food. `sim/observe.py` checks it every season, as it does food and people.
- **Money waits for M6.**

### 4.2 How exchange works, by scale

1. **Gift and risk-sharing exchange among foragers and small villages.** Partners in other bands exchange gifts and can call on each other in bad years, as in the !Kung San *hxaro* system (Wiessner 1982). This is mostly an insurance tie, and it carries knowledge.
2. **Down-the-line exchange:** goods pass from neighbour to neighbour, so their abundance falls steadily with distance from the source (Renfrew 1977). Obsidian in the prehistoric Near East is the classic case. Fall-off curves are a measurable prediction.
3. **Directed trade** once there are specialists and polities: traders (a specialist role from surplus, like M2's) carry goods along routes between centres, and rulers tax or control the trade.

Each trade is recorded with its partners, goods and quantities. Trade creates contact, so it raises the "connected population" of section 3.2.

### 4.3 What trade changes

- It moves goods to where they are scarce: food in bad years, metal to places without ore.
- It spreads techniques (section 3.4).
- It gives rulers something to control and fight over. Trade routes and their goods enter M3's war reasons as "control of the copper trade".
- It creates dependence, so a people that relies on imported tin loses bronze when the trade is cut, with the cause recorded.

---

## 5. People change the land (section 16, item 1)

- **Overhunting:** large game recovers slowly. Hunting pressure above what a population can replace reduces it, and foraging returns fall. Whether people drove the extinctions of large mammals at the end of the Ice Age is debated; the simulation lets it happen where pressure is high, and does not force it.
- **Forest clearance:** farming and fuel (kilns, smelting) clear forest. Clearance has a fuel cost for metal-working and brings erosion on slopes.
- **Soil exhaustion and salting:** farmed land loses fertility without fallow or manure, and irrigated land in dry climates salts up. In southern Mesopotamia, Jacobsen and Adams (1958) linked salting to a shift from wheat to more salt-tolerant barley and to falling yields.
- **Recovery is slow or absent:** forest returns over centuries, salted soil hardly at all.
- **Feedback:** all of these enter food, so famine, migration and collapse can follow, with the chain recorded: "the fields of X yielded a third less after 300 years of irrigation without drainage".

---

## 6. Diseases from domestic animals (section 16, item 2)

Many major human infectious diseases arose from animals: some from domestic animals, many from wild ones, especially in the Old World. Their spread also needed dense populations, which came with farming and towns (Wolfe, Dunavan & Diamond 2007).

**PROPOSED:**
- **New diseases are rare and need two conditions:** people living closely with a particular herd animal, and enough people for the disease to persist.
- **Each disease is a named entity**, with an origin, a host animal and a severity.
- **Peoples who live with a disease for generations build up resistance** (as a share of the population, not by genetics; the genetics are item 3, in M5–M6).
- **Contact between long-separated peoples** brings a disease to people without resistance, with heavy deaths in one direction.
- **This builds on M1's outbreaks**, which take a cause from these diseases. That should also explain outbreaks' share of deaths, carried forward from M1, rather than tuning it.

---

## 7. Writing and place names

- **Writing** (section 16, item 4) is a technique in the network. It grows from tallies and tokens under the burden of administration: many tribute payers, many officials (Schmandt-Besserat 1992).
  - **Effect:** officials' capacity rises (M3's capacity), and records outlast the people who made them. Lost knowledge can then be recovered from records, a rare and recorded event.
  - **Chronicles written by the peoples themselves** are M4b.
- **Place names** (section 16, item 6): rivers, mountains, regions and settlements get names in the language of whoever lives there. Newcomers and conquerors rename them, and older names survive beneath, as layers. This uses the M1 language system.

---

## 8. M4b in outline (specified in detail after G4a)

1. **Military technology** as nodes of the network: bows, bronze and iron weapons, horses and cavalry, chariots, fortification and siege, ships. Each enters M3's war strength.
   - Seshat supports this as a driver of scale. Turchin et al. (2022) tested 17 candidate predictors of social complexity. The best-supported model combines rising agricultural productivity with military technology, notably iron weapons and cavalry in the first millennium BCE.
2. **Methods of war and logistics:**
   - raids, battles, sieges, ambush;
   - armies eat from real stores, the season matters, and distance limits reach.
3. **Reconnaissance and strategy:**
   - polities act on estimates of their neighbours' strength, not the truth;
   - the estimates come from traders, scouts and spies, and they can be wrong.
   - This follows the rationalist account of war: wars that both sides would rather avoid happen because of private information and incentives to misrepresent it (Fearon 1995).
   - Leaders choose between attack, defence, alliance, tribute and waiting by understandable rules.
4. **Crime, norms and enforcement:**
   - norms belong to each culture;
   - responses run from gossip, exile and feud (Boehm 1984) to compensation, courts and graduated sanctions;
   - long-lasting common-pool institutions use graduated sanctions (Ostrom 1990).
   - The limit set in section 16 holds: sexual violence and the abuse of children appear only as counts at the level of a society.
5. **Lineages, personal ties, reputation:**
   - lineages as compact records under each people's descent rule, able to split, migrate and expand. Segmentary lineages can organise expansion against neighbours (Sahlins 1961).
   - two kinds of tie: obligation and enmity;
   - reputation earned by deeds;
   - the knock-out of personal ties in G4b.
6. **Chronicles:** selective and partisan records in the people's own language, set beside the true record.

---

## 9. Gate G4a: PROPOSED checks

Run across many histories on five planets, plus knock-out histories.

| # | Check | Pass mark (PROPOSED) |
|---|---|---|
| 1 | M0–M3 still hold | all earlier gates' checks, as in G3 check 1 |
| 2 | **Innovation tracks connected population** | rank correlation of inventions per century with connected skilled population: clearly positive (median above 0.3) |
| 3 | **Risk matters too, or doesn't** (measured, no mark) | correlation of inventions with need, beside check 2: reported so the debate in section 3.2 is answered by the simulation, not assumed |
| 4 | **Diffusion follows contact** | of techniques a people holds, most come from others (median share learned above 0.6); the time a technique takes to reach a people rises with distance in contact steps |
| 5 | **Isolation causes loss** | losses occur in some histories; the chance of loss rises as connected population falls; knowledge falls in peoples cut off (islands, after collapse) |
| 6 | **Knock-out: no population effect** | with the population term off (section 3.2), check 2's correlation falls clearly, showing how much rests on it |
| 7 | **Trade follows supply and distance** | goods' abundance falls with distance from their sources (a fall-off curve); trade rises in bad years where partners exist |
| 8 | **Goods are conserved** | no accounting failures in any history (goods, food, people) |
| 9 | **The land answers back** | yields fall under long irrigation without drainage and under exhausted soil; large game falls under heavy hunting; at least some famines and migrations trace to them |
| 10 | **Diseases from animals** | new diseases arise only where herds and dense populations meet; deaths after first contact between long-separated peoples are heavier among those without resistance |
| 11 | **Traceable** | every sampled invention, loss, adoption, trade and new disease has a complete cause chain |
| 12 | **Same rules, different histories** (no mark) | which techniques appear, where and when, varies widely across histories |
| 13 | **Speed** (no mark) | computing time per history |

**Historical comparisons**, reported beside the checks, not as pass marks:
- the order and spacing of techniques against archaeological sequences (pottery, copper, bronze, iron, writing);
- the time from first villages to states, against Borcan, Olsson and Putterman (2021), with the brakes from section 2;
- Seshat's measures of technology against polity scale (Turchin et al. 2022).

---

## 10. What the observer sees

- **A technology map:** which peoples hold which techniques, and where each was invented and lost.
- **A technique's page:** its invention, its spread across the map over time, and its losses, each with causes.
- **Trade:** routes and the volume of goods; the fall-off of a good from its source.
- **The land:** cleared forest, exhausted and salted soil, and game.
- **Diseases:** origin, spread, and deaths by people.
- **Place names** on the map, in the local language, with the older layers on the place's page.

---

## 11. Engineering

- **New random streams appended at the end:** "technology", "trade", "land", "disease" (never inserted).
- **Data plus systems:** techniques per people in arrays, goods in a ledger, with new systems in `origins/sim/`.
- **The on-disk event store** (section 2).
- **Exact replay and saves:** as before.
- **Speed:** M4 adds per-people work, not per-person work, so the cost should stay modest. Measure early.

---

## 12. Out of scope

- M5: religion, rituals, myths, and religious sanction for norms.
- M6: money, markets, the long-run economy, inherited traits.

---

## 13. Decisions (Ben, 12 November 2026)

1. **M4 is split into M4a and M4b** (section 1.1): agreed.
2. **The technique list:** about 25–35 techniques, as proposed (section 3.1).
3. **Population and risk both enter the chance of invention**, with a knock-out to measure which matters (section 3.2): agreed.
4. **Pastoralism**, a way of life on dry grassland, in M4a (section 2, item 3): agreed.
5. **Circumscription**, villages leaving heavy rulers while there is open land, as an early-M4 brake on early states (section 2, item 1): agreed.
6. **The G4a checks and marks** (section 9): agreed.

## Sources

- Boehm, C. (1984). *Blood Revenge: The Anthropology of Feuding in Montenegro and Other Tribal Societies*. Lawrence: University Press of Kansas.
- Borcan, O., Olsson, O., & Putterman, L. (2021). Transition to agriculture and first state presence: A global analysis. *Explorations in Economic History*, 82, 101404.
- Carneiro, R. L. (1970). A theory of the origin of the state. *Science*, 169(3947), 733–738.
- Collard, M., Kemery, M., & Banks, S. (2005). Causes of toolkit variation among hunter-gatherers: A test of four competing hypotheses. *Canadian Journal of Archaeology*, 29.
- Derex, M., Beugin, M.-P., Godelle, B., & Raymond, M. (2013). Experimental evidence for the influence of group size on cultural complexity. *Nature*, 503, 389–391.
- Fearon, J. D. (1995). Rationalist explanations for war. *International Organization*, 49(3), 379–414.
- Henrich, J. (2004). Demography and cultural evolution: How adaptive cultural processes can produce maladaptive losses: The Tasmanian case. *American Antiquity*, 69(2), 197–214.
- Jacobsen, T., & Adams, R. M. (1958). Salt and silt in ancient Mesopotamian agriculture. *Science*, 128(3334), 1251–1258.
- Kline, M. A., & Boyd, R. (2010). Population size predicts technological complexity in Oceania. *Proceedings of the Royal Society B*, 277, 2559–2564.
- Kohler, T. A., Smith, M. E., Bogaard, A., et al. (2017). Greater post-Neolithic wealth disparities in Eurasia than in North America and Mesoamerica. *Nature*, 551, 619–622.
- Ostrom, E. (1990). *Governing the Commons: The Evolution of Institutions for Collective Action*. Cambridge: Cambridge University Press.
- Powell, A., Shennan, S., & Thomas, M. G. (2009). Late Pleistocene demography and the appearance of modern human behavior. *Science*, 324, 1298–1301.
- Renfrew, C. (1977). Alternative models for exchange and spatial distribution. In T. K. Earle & J. E. Ericson (Eds.), *Exchange Systems in Prehistory* (pp. 71–90). New York: Academic Press.
- Roberts, B. W., Thornton, C. P., & Pigott, V. C. (2009). Development of metallurgy in Eurasia. *Antiquity*, 83(322), 1012–1022.
- Sahlins, M. D. (1961). The segmentary lineage: An organization of predatory expansion. *American Anthropologist*, 63(2), 322–345.
- Schmandt-Besserat, D. (1992). *Before Writing* (2 vols). Austin: University of Texas Press.
- Turchin, P., Whitehouse, H., Gavrilets, S., et al. (2022). Disentangling the evolutionary drivers of social complexity: A comprehensive test of hypotheses. *Science Advances*, 8(25), eabn3517.
- Vaesen, K., Collard, M., Cosgrove, R., & Roebroeks, W. (2016). Population size does not explain past changes in cultural complexity. *PNAS*, 113, E2241–E2247.
- Wiessner, P. (1982). Risk, reciprocity and social influences on !Kung San economics. In E. Leacock & R. Lee (Eds.), *Politics and History in Band Societies* (pp. 61–84). Cambridge: Cambridge University Press.
- Wolfe, N. D., Dunavan, C. P., & Diamond, J. (2007). Origins of major human infectious diseases. *Nature*, 447, 279–283.
