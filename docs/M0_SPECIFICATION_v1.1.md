# M0 Specification — v1.1

**Milestone:** M0, "the first people survive"
**Status:** v1 approved by Ben on 5 November 2026. v1.1 (6 November 2026): the founding people are three bands of 30, decided by Ben after the first gate run; the individual-to-group threshold was brought into M0; built and gated (see `origins/docs/M0_GATE_REPORT.md`). Numbers are **starting values to be tuned**, not established facts. Where a range is called plausible, it is a broad reference for checking that the simulation is not absurd, not a target to fit exactly.
**Belongs to:** Design Draft v0.4
**Date:** 5 November 2026

---

## 1. What M0 is for

M0 builds the smallest world in which the founding band can live, eat, have children, die, move and split, and shows that it **endures** (behaviour 1). Everything later grows out of this layer, so it must work before anything is added on top.

**In M0:**

- A generated planet (land, water, elevation, rivers, climate, biomes, wild food)
- Individual people with kinship
- Forager bands that gather food through the seasons, share it, move, split and merge
- Births, deaths and ageing driven by nutrition and age
- Year-to-year climate variability (good and bad years)
- The map revealed as people reach new land
- A causal event log, saving and loading, exact replay
- A basic observatory: map, bands, people, genealogy, population chart, event log
- The first viability gate (section 11)

**Not in M0** (later milestones): discrete hazards such as floods and eruptions, language and culture drift, technology, minerals in use, domestication and farming, trade, conflict, leadership, belief and religion, god mode, glacial cycles. (The individual-to-group threshold was brought into M0 in v1.1: populations pass 20,000 within the 2,000-year gate.)

---

## 2. Time step

- **One tick = one season** (four a year). At 300 simulated years per real day, that is 1,200 ticks per day in live viewing.
- Gate tests run as fast as the computer allows, not on the clock.
- Every tick runs the same phases in a fixed order (section 9).

---

## 3. The planet in M0

The full generator is described in Design Draft section 4.1. M0 needs only part of it:

| Layer | In M0 | Notes |
|---|---|---|
| Geodesic hex grid, quarter-Earth area | Yes | About 41,000 cells of about 3,100 km² |
| Land and sea, elevation | Yes | Continents from layered noise; full tectonics can come later without changing the interface |
| Rivers and lakes | Yes | From water flow over elevation |
| Climate | Yes | Temperature by latitude and altitude; rainfall by latitude bands, ocean distance and rain shadow; four seasons |
| Biomes | Yes | From temperature and rainfall |
| Wild food | Yes | Per cell and season (section 4) |
| Climate variability | Yes | Each region's yearly "good or bad year" factor, correlated in space and time |
| Minerals, domesticable species | Generated but unused | Generated now so the same seed produces the same world later |
| Discrete hazards | No | M1 |

**Starting location:** a habitable cell with moderately good wild food and fresh water, chosen from the seed. Not the best place on the planet, and not the worst.

**Revealed map:** a cell becomes known when a band enters or neighbours it. Unknown cells are blank on the map.

---

## 4. Food

**Unit.** One **food unit** = one adult's food needs for one day (roughly 2,000–2,500 kilocalories). Everything is measured in these units.

**Wild food in a cell.** Each land cell has a wild-food stock that:

- **regrows** each season towards a maximum set by biome, season and that year's climate factor (fast in spring and summer, slow in winter, little in deserts and tundra)
- is **reduced** by foraging, with diminishing returns as the stock falls (the easy food goes first)
- includes plants, game and fish, with rivers, lakes and coasts adding to it

**Foraging.** Each working-age person contributes effort. Yield per person depends on the cell's stock, their age (children and elderly forage less; skill builds through young adulthood), and how many others are foraging the same cell.

**Storage.** M0 bands can hold only a small, perishable store, a few weeks' food, which spoils quickly. Real storage (and with it, surplus) belongs to M2.

**Sharing.** The band pools what it gathers and distributes it by need, which is the common forager norm. Needs vary by age, sex, pregnancy and nursing. If there is not enough, everyone gets a share of the shortfall, with small children protected first. (Alternative sharing rules can become a cultural trait in M1.)

---

## 5. People

Each person has:

| Field | Purpose |
|---|---|
| ID, name | Identity (PIE-inspired names; see section 5.1) |
| Sex, birth tick | Age, life stage |
| Mother, father | Kinship and genealogy |
| Partner | Current partnership |
| Band | Who they live and share with |
| Body condition | Energy reserve: falls with hunger, recovers with food |
| Children's ages | For birth spacing and nursing |
| Alive / death tick and cause | Demography and the event log |

### 5.1 Names (DECIDED)

Names are **inspired by Proto-Indo-European (PIE)**. This is an aesthetic choice for a fictional world: real PIE is a reconstructed language spoken tens of thousands of years after this world's start, and no claim is made that these people speak it.

- **M0:** a generator builds names from PIE-like sounds and from two-part compounds, the pattern reconstructed for PIE personal names and seen in its descendants (Greek *Sophoklēs*, *Periklēs*, built on the "fame" element *-klēs*; Slavic *Vladislav*, built on *slava*, "glory"). The founding band shares one naming stock.
- **M1 onward:** when languages appear, each lineage's words and names change through **regular sound changes** (systematic shifts applied to the whole vocabulary, as in real language history). Names in separated groups drift apart over generations, so a name's form shows its people and era. Every name keeps a traceable history back to its root.

People are stored as arrays (one row per person) rather than separate objects, so that tens of thousands can be updated quickly.

---

## 6. Births, deaths and partnerships

**Deaths.** Each season every person has a chance of dying, made of:

- a **baseline by age**: high in infancy, low through childhood and adulthood, rising steeply in old age
- **raised by poor body condition**: starvation-related deaths come from here
- a small **accident and illness** component

Every death records its cause (infancy, hunger, accident/illness, old age) and the person's condition, so the log can say *why*.

**Partnerships.** Adults form partnerships, preferring partners from their own or neighbouring bands, and never close kin (parent, child, sibling, half-sibling). Partnerships can end through death or, rarely, separation.

**Births.** A partnered woman of child-bearing age has a chance of conceiving each season, which:

- falls with poor body condition
- is near zero while she is nursing a young child, giving realistic spacing of roughly three to four years between births
- falls with age towards the end of the child-bearing years

Pregnancy lasts about three seasons. Nursing raises the mother's food needs.

**Plausibility ranges** (checks, not targets): life expectancy at birth roughly 25–40 years; a substantial share of people who reach adulthood living into their sixties and seventies; average completed family size roughly 4–7 births per woman; infant and child deaths high. The longevity ranges are broadly consistent with Gurven & Kaplan's cross-cultural study of hunter-gatherer longevity ("Longevity among hunter-gatherers: a cross-cultural examination", *Population and Development Review*, 2007). The other ranges are working assumptions to be checked against the literature before the gate is fixed.

---

## 7. Bands: movement, splitting and merging

**Movement.** Each season the band compares its current cell with neighbouring cells on expected food (for the season ahead), minus the cost of moving. It stays or moves. Seasonal rounds should emerge from this rather than being scripted.

**Splitting (fission).** When a band grows large (starting value: more than about 50 people), or food per person falls while neighbouring land is empty, it splits roughly along family lines. The new band moves to a nearby cell, preferring unoccupied ones. This is how the world fills.

**Merging.** A band that becomes too small to be viable (starting value: fewer than about 10 people) joins the nearest band.

**Contact.** Bands in neighbouring cells can exchange partners. In M1 this becomes the channel for cultural and genetic exchange.

---

## 8. Event log and causes

Every event is recorded with its time, place, the people or bands involved, and its **causes**:

| Event | Example of recorded causes |
|---|---|
| Death | Age, body condition, the band's food per person that season, the bad-year factor |
| Birth | Mother's condition, time since last birth |
| Band moves | Expected food here vs. there |
| Band splits | Band size, food per person, nearby empty land |
| Band merges | Band size |
| Cell discovered | The band that reached it |
| Bad year | The climate factor for that region |

Clicking any event in the observatory shows its causes, and the causes of those causes where they are events.

---

## 9. Order within a tick

1. Climate: set this season's conditions (and the yearly factor at the start of each year)
2. Wild food regrows
3. Bands decide whether to move
4. Foraging
5. Sharing and eating; body condition updates
6. Deaths
7. Partnerships form or end
8. Births
9. Bands split or merge
10. Map reveal
11. Record observations and check invariants

---

## 10. Observatory in M0

- **Map:** known cells by biome, rivers, unknown cells blank; bands as markers sized by population
- **Band view:** members, ages, condition, food this season, where it has been
- **Person view:** life events, parents, partner, children; a family tree
- **Charts:** world population, number of bands, births and deaths per year, food per person
- **Event log:** filterable, with the "why" chain
- **Controls:** pause, run at 300 years/day, fast-forward, save, load, new world from a seed
- **Follow a band (DECIDED):** choosing a band to follow lets the observer set a slower speed (for example a season per few minutes) to watch its daily life. There is one world clock, so the whole world slows while following. When the observer stops following, the clock returns to 300 years/day. Time spent slowed is not "caught up" afterwards; the world simply ran more slowly while watched.

---

## 11. The first viability gate (G0, behaviour 1)

**Proposed pass marks for Ben's approval:**

| # | Check | Pass mark |
|---|---|---|
| 1 | Survival | Across 5 generated worlds × 20 seeds each (100 runs) of 2,000 simulated years, at least 90 runs avoid extinction |
| 2 | No explosion | Population never exceeds the estimated wild-food carrying capacity of the land the bands occupy |
| 3 | Fluctuation, not a flat line | Population varies with good and bad years, then recovers |
| 4 | Plausible demography | Life expectancy, family size and band sizes fall inside the ranges in section 6 (median band size roughly 15–60) |
| 5 | Shock response | A forced three-year drop of 40% in wild food in one region raises hunger deaths and lowers births there, and the population recovers within about two generations |
| 6 | Spread begins | From one band, the occupied area grows over the run (full spread and drift are tested in M1) |
| 7 | Nothing from nothing | Every person is accounted for by births and deaths; every food unit by regrowth, consumption and spoilage |
| 8 | Exact replay | Same seed, same history; a saved world reloads and continues identically |
| 9 | Explainability | Every death and every band split in a sampled run has a complete recorded cause chain |
| 10 | Speed | 2,000 simulated years runs in a few minutes on your computer (exact target set once the first version exists) |

**Why 90%, not 100%:** small founding groups in harsh conditions really can die out; a world where extinction is impossible would be unrealistic. The gate tests that endurance is the norm, not a certainty.

**Growth will be slow, and that is correct.** Forager populations grew very slowly. Over 2,000 years the founding band may become only a few hundred to a few thousand people in a handful of bands. The full world fills over the 38,000-odd years of prehistory, which is where the 20,000-person individual threshold will eventually matter (M1 or later).

---

## 12. Engineering for M0

- **Python with NumPy;** browser 2D map served by a small local server
- **Project layout:** `world/` (generation), `sim/` (systems), `observatory/` (map and views), `tests/`, `gates/` (the G0 runner), `docs/`
- **Data plus systems:** state in arrays and tables; each phase in section 9 is a function with declared inputs and outputs
- **Separate random streams** for climate, demography, movement and generation
- **Git** from the first commit; a short `CLAUDE.md` with the project's rules and current milestone
- **Saves** as versioned files (compact format for people arrays); exact replay tested from the start

---

## 13. Decisions

1. **Founding people:** three neighbouring bands of 30 people of mixed ages (90 in all). Changed from one band of 30 on 6 November 2026: in the first gate, 37 of 100 single-band worlds died out because one isolated band runs out of partners who are not close kin.
2. **Gate G0:** the ten checks in section 11, as written.
3. **Names:** PIE-inspired in M0; changing through regular sound changes as languages develop (section 5.1).
4. **Speed:** 300 years/day normally (a season every 72 seconds); adjustable slower speed while following a band (section 10).

## 14. Before building

- **Python on your computer.** The earlier build ran through a bundled Python because the Windows `python` command was not available. This will be checked, and Python plus NumPy set up, before any code is written.
- **Version history and OneDrive.** Git repositories inside OneDrive-synced folders can be damaged when OneDrive syncs files mid-operation. Options: keep the working project in a folder outside OneDrive (for example `C:\Users\b392d\Projects\...`) with the design documents left here, or keep it here and push every change to a private GitHub repository as the safe copy.
