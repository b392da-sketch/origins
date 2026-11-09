# M3 Specification — draft

**Milestone:** M3, "scale needs institutions; conflict has causes and costs" (behaviours 5 and 6)
**Status:** draft for Ben's review. Sections marked **DECISION** need your choice; **PROPOSED** marks a suggested option or starting value. Numbers are starting values to be tuned, not established facts.
**Builds on:** M0, M1 and M2 (all closed; M2 on 9 November 2026 with check 9 carried forward) · Design Draft v0.5
**Date:** 9 November 2026

---

## 1. What M3 is for

M2 ends with a world where some peoples farm, live in villages, store food, keep specialists and own unequal property. Each village is still on its own. M3 lets villages **come under leaders who rule more than one of them**:

- chiefdoms first, then in some places **states**;
- polities that **fight**, **conquer** and **break apart**.

Growth in scale must be paid for with institutions. Without them, or under stress, large polities fragment, and later something new can grow in their place.

Behaviours tested (Design Draft section 11):

- **5. Scale needs institutions, or it breaks apart.** Oversized polities break up; collapses occur in some histories; recovery follows.
- **6. Conflict has causes and costs.** War follows competition; conquest builds empires that are hard to hold.

Also in M3 (Design Draft section 12): **individual-to-group folding at the scale of polities**, with notable people kept individual. M3 also takes up the items carried forward from M2 (section 9).

Out of scope for M3, left to later milestones:
- the general technology network, metals, writing as a technique, and trade beyond tribute and raiding (M4);
- religion as a layer of its own, beyond the ritual specialists M2 already has (M5);
- the long-run economy (M6).

---

## 2. Before anything else: one planet for every machine

The M2 gate found that GitHub's machines of different processor types build the same planet slightly differently. Rainfall differed by up to 188 mm a year in some cells, and biome and capacity differed in 2 cells. The cause is that each cell's rain follows its most nearly upwind neighbour, and when two neighbours are almost equally upwind, the last digits decide.

**PROPOSED:** break near-ties deterministically by rounding the scores before choosing, and check the same fingerprint on every machine type in CI. This changes every planet, so G3 re-checks M0–M2 behaviour on the new planets (section 8, check 1), and saves from before the change will not load into the new world generation.

---

## 3. Leaders and polities

**Leaders.** Every band and village already has a leader in M2: the head of its richest household, where there is surplus. In M3 leaders gain or lose **standing**, from three sources:
- generosity: feasts and gifts paid from real stores;
- success in war;
- descent from earlier leaders.

Standing decides whether other villages follow them.

**Polities.** A polity is a set of settlements under one leader. It is plain data: its seat, its member settlements, its leader, its institutions, its founding event, and a name built from its people's language. Settlements join a polity in three ways:

| Way | When |
|---|---|
| **Alliance** | A neighbouring village under threat, or drawn by a leader's standing and generosity, accepts that leader; more likely between kin and speakers of close languages |
| **Fission inside a polity** | A daughter village founded by a member stays in the polity |
| **Conquest** | Defeated in war, it is annexed or made to pay tribute (section 5) |

**Tiers** (used for the gate and the map; they are measured, never assigned):

| Tier | Test |
|---|---|
| Autonomous | One settlement |
| Simple chiefdom | A seat and at least two other villages, paying tribute to the seat |
| Complex chiefdom | Sub-leaders over groups of villages: two levels of rule above the village |
| State | Three or more levels of rule above the village, with full-time administrators (following the archaeological convention of "three or more" levels: Wright 1977; Wright & Johnson 1975) |

**Tribute** is food moved from members to the seat. It is conserved and recorded like every other food flow, and it pays for the polity's specialists: administrators, warriors and ritual specialists. Polities have no money until M4 or M6.

**Succession.** When a leader dies, a successor comes by custom: through a child, through a sister's child, or chosen by the council. This becomes a new custom that drifts like the M1 customs. A contested succession (several heirs of similar standing) is a moment of weakness (section 4).

---

## 4. Institutions, capacity and break-up

Holding many settlements costs effort, which rises with:
- their number;
- their distance from the seat;
- how different they are in language and customs;
- for conquered settlements, how recent the conquest is.

This is the polity's **load**.

**Institutions** raise what a polity can hold, its **capacity**. Each one costs real food every year, through the specialists who run it:

| Institution | Effect | Paid for by |
|---|---|---|
| Council of village heads | Smaller load from member villages; smoother succession | Feasts (food) |
| Tribute collectors | Tribute from farther villages; the cost of distance falls | Administrators |
| Law and judges | Fewer quarrels and secessions over disputes | Administrators |
| Warriors kept by the leader | Defence and conquest; holding conquered villages | Warriors |
| Officials over districts | The tier above sub-leaders; a state needs them | Administrators |

A polity adds an institution when its load presses on its capacity and its surplus can pay for one, and drops it when the surplus fails. Each change is an event with recorded causes.

**Break-up.** Each year each member settlement may **secede**. The chance rises with:
- the polity's overload (load ÷ capacity above 1);
- stress: famine, a lost war, a contested succession, heavy tribute;
- the settlement's distance and difference from the seat.

A settlement that secedes takes its people and stores, may set up a polity of its own, and its secession is an event that names its causes.

**Collapse** is a measured outcome, not a rolled event: a polity loses at least half its people within a century through secession and defeat. **Recovery** is also measured: a polity of comparable size forms again in the same region.

**Knock-out experiment.** In "no institutions" histories, polities cannot build institutions. Behaviour 5 predicts they stay small and short-lived. This mirrors M2's no-storage experiment.

---

## 5. Conflict

**Who fights.** Neighbouring polities and settlements within reach of each other, at a distance in cells set by terrain and, later, by transport.

**DECISION 1 below:** whether foragers raid too.

**Why they fight.** Each year the chance that one side raids or makes war on another rises with:
- **scarcity** (the attacker's food per person against its need, and land pressure);
- **proximity**;
- **opportunity** (relative strength);
- **cultural distance**;
- **grievance** (earlier raids and killings remembered for a few generations);
- the attacking leader's standing and position. A new leader, or a leader with warriors to feed, is more likely to fight.

Every war is an event that names these causes.

**What it costs.** Fighting kills people on both sides: young men above all, but not only them. Each such death is recorded with a new cause, "killed in war", traced to the war event.

Plausibility guide, not a target: estimates for prehistoric and ethnographic foragers put war at about 12–16% of adult deaths (Bowles 2009, Table 1), though these estimates are disputed.

Wars also cost food (fields left unworked, stores taken) and land.

**What it can win:**

| Outcome | Effect |
|---|---|
| Raid | Stores taken (moved, not created) |
| Tribute | The loser pays a yearly share to the winner |
| Annexation | The loser's settlements join the winner's polity |
| Land | The winner's people settle land the loser abandons |
| Captives | **DECISION 2** |

**Empires.** A polity that has annexed settlements of other peoples is an empire. Behaviour 6 predicts that such polities are hard to hold: their load is high, through distance, difference and recent conquest, so they last less long the further they over-reach.

Circumscription (Carneiro 1970) is not built in as a rule. Where farmland is hemmed in by desert, mountains or sea, losers cannot simply move away, so conquest should pay more there. That is a prediction the gate looks for, not something added.

---

## 6. Folding at the scale of polities

Individuals already fold into groups beyond 20,000 people (M0–M2). As polities grow, the people who matter to the story must stay individual even inside folded groups:
- leaders and their heirs;
- sub-leaders and officials;
- war leaders;
- followed families.

**PROPOSED:** notables are drawn from their group's counts and still counted in them, so nobody is counted twice. They are kept individual while they hold a role, and for the rest of their lives once they have held one, so that their genealogies are complete. Their deaths come from the same rates as their group's.

---

## 7. Inequality that compounds (carried forward from M2, check 9)

M2's inequality appears with farming and then settles. Options from the M2 gate report: (c) let advantage compound. In M3:

- **Land becomes scarce and inherited.** A village's farmland is divided into plots that belong to households. When the good land is taken, new households have none of their own: they work others' plots for a share of the harvest, or move away. Plots pass to heirs by the inheritance custom.
- **Herds breed.** A household's animals are wealth that grows by itself in good years and dies in bad ones. Real pastoral societies pass wealth on strongly and are among the most unequal small-scale societies (Borgerhoff Mulder et al. 2009).

Both are **DECISION 3**.

Draft animals and the plough are techniques, so they belong to M4's technology network.

---

## 8. Gate G3

Histories: **50 on 5 planets** (the new planets from section 2), plus **20 "no institutions" histories**. The length is set by DECISION 4.

| # | Check | Pass mark (PROPOSED) |
|---|---|---|
| 1 | **M0–M2 still hold** on the new planets: survival, accounting, life expectancy, spread, drift, farming conditions, adoption dates, foragers keep land, specialists follow surplus, no storage no specialists | As in G1 and G2 |
| 2 | **Polities form, and states in some histories but not all** | Chiefdoms in ≥80% of farming histories; states in at least one history and not in all; formation dates vary by thousands of years |
| 3 | **Oversized polities break up** | Rank correlation of secession rate with overload, across polities and years: clearly positive |
| 4 | **Collapse in some histories, recovery after it** | At least one collapse in ≥20% and ≤90% of histories with chiefdoms; recovery after at least half of the collapses |
| 5 | **No institutions, no large polities** | "No institutions" histories: largest polity far smaller than with institutions (median under a quarter), and no states |
| 6 | **Conflict rises with scarcity and proximity** | Rank correlations of war rate with scarcity and with closeness: both positive |
| 7 | **Conflict has costs** | Deaths in war a plausible share of adult deaths (PROPOSED: between 2% and 30%, median within 5–25%); losers lose people, food or land, with every flow recorded |
| 8 | **Conquest builds empires that are hard to hold** | Empires in some histories; rank correlation of empire duration with overextension: clearly negative |
| 9 | **Inequality compounds** (from M2) | Household inequality rises with years of farming and with surplus (M2 check 9's wording) |
| 10 | **Traceable** | Every polity founding, state threshold, secession, collapse, war and conquest has a complete cause chain |
| 11 | **Same rules, different histories** | Polities' number, size and dates vary widely across histories of one planet |
| 12 | Speed | Reported; see DECISION 4 |

---

## 9. Carried forward from M2

1. World generation's upwind choice (section 2): first.
2. Inequality that compounds (section 7, check 9).
3. **Speed.** The longest planet-4 G2 histories needed nearly 11 hours of computing for 3,000 years after the first village. M3 adds systems and needs longer histories. **PROPOSED:** a speed pass before the M3 systems: profile, vectorise the band and group loops, and cut the record churn further. Target: half the computing per simulated year on big worlds.
4. From M1: island peoples do not diverge faster; outbreaks about 8% of deaths; planet 3's weak drift.
5. Bands cannot cross barren land on foot. Not proposed for M3.

---

## 10. What the observer sees

- **Polities layer:** borders and seats, coloured by polity; tiers shown by the seat's symbol.
- **Wars layer:** raids and wars as they happen, with lines from attacker to defender and recent battlefields marked.
- **Polity page:**
  - leaders over time with their genealogy;
  - tier, institutions and what they cost;
  - tribute flows;
  - member settlements, with their languages;
  - wars, conquests and secessions, each linked to its "why" chain.
- **Chronicle:** successions, wars, conquests, secessions and collapses, narrated only from logged events.

---

## 11. Decisions for Ben

**DECISION 1: Who fights?**
- **A. Everyone (PROPOSED).** Foragers raid too, as the evidence suggests they did. Bands already exist, so raids among them are a small step. This changes M0–M2 behaviour (deaths, spread), which check 1 must show still holds.
- **B. Only farmers and polities.** Prehistory stays exactly as in M2, so each G3 history could start from a saved world at its first farming village. That would make G3 several times cheaper (DECISION 4), but foragers would never fight.

**DECISION 2: Captives.** Historically, captives (mostly women and children) were often taken into the victors' societies, and later states kept slaves.
- **A. Captives join the victor's people (PROPOSED)** with low standing at first, counted and recorded, and with their own language and customs carried in (which feeds language shift and borrowing). Slavery as an institution waits for a later milestone.
- **B. No captives.** Wars kill and take land and stores, but never people.
- **C. Captives and slavery** as an institution from M3, with its own costs and break-up pressure.

**DECISION 3: Compounding inequality.** Both mechanisms (PROPOSED), land only, herds only, or neither (leave check 9 carried forward again).

**DECISION 4: How long G3 histories run.** Real states came several thousand years after the first villages; in Mesopotamia, roughly five to six thousand.
- **A. To 6,000 years after the first farming village (PROPOSED)**, with a cap of 30,000 years. With DECISION 1A this needs the speed pass first: without it, planet-4 histories could need over 20 hours of computing across several machines.
- **B. To 3,000 years after the first village**, as in G2. Cheaper, but states may rarely have time to form.
- With DECISION 1B, either length is much cheaper: the time before farming is computed once per history and shared by the knock-out experiment.

**DECISION 5: Order of work.** **PROPOSED:**
1. world generation fix;
2. speed pass;
3. leaders and polities;
4. institutions and break-up;
5. conflict;
6. inequality;
7. folding of notables;
8. observatory;
9. G3.

A short gate attempt after step 4, covering behaviour 5 only, would catch problems early.

---

## Sources

- Borgerhoff Mulder, M., et al. (2009). Intergenerational wealth transmission and the dynamics of inequality in small-scale societies. *Science*, 326(5953), 682–688.
- Bowles, S. (2009). Did warfare among ancestral hunter-gatherers affect the evolution of human social behaviors? *Science*, 324, 1293–1297.
- Carneiro, R. L. (1970). A theory of the origin of the state. *Science*, 169, 733–738.
- Wright, H. T. (1977). Recent research on the origin of the state. *Annual Review of Anthropology*, 6, 379–397.
- Wright, H. T., & Johnson, G. A. (1975). Population, exchange, and early state formation in southwestern Iran. *American Anthropologist*, 77(2), 267–289.
