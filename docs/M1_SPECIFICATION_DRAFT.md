# M1 Specification — Draft

**Milestone:** M1, "spreading and drifting apart" (behaviour 2, plus natural hazards)
**Status:** draft for Ben's review; nothing has been built. Items marked **PROPOSED** await his decision. Numbers are starting values to be tuned, not established facts.
**Builds on:** M0 (closed 6 November 2026) · Design Draft v0.5
**Date:** 6 November 2026

---

## 1. What M1 is for

M0 showed that people survive and spread. M1 makes the people who spread **become different from one another**: separated groups drift apart in language, customs and tools, so that a world that began with one people of 90 becomes, over thousands of years, a patchwork of peoples who no longer understand each other. M1 also adds **natural hazards**, so that droughts, floods, fires, eruptions and outbreaks shape where people live and how they fare.

**In M1:**

- Languages that change by regular sound changes and word replacement, split as speakers separate, and borrow from neighbours; personal names built from each language's own words (the PIE-inspired names of M0 evolving)
- Customs: a small set of observable cultural traits (named variants) plus neutral drift, inherited, copied from neighbours, and changing at random
- Tool styles drifting the same way (style only; new techniques are M4)
- Short sea crossings (**PROPOSED**, section 4)
- Hazards: floods, wildfires, volcanic eruptions, earthquakes, disease outbreaks, alongside the existing good and bad years
- Observatory: language and culture map layers, a language family tree, name histories, hazards on the map
- One M0 limitation closed: a test that groups and individuals behave alike **at the food limit**, not only during growth

**Not in M1:** technology and innovation (M4), farming (M2), leadership and conflict (M3), belief and religion (M5; customs here are not yet beliefs), god mode (M5), glacial cycles (optional, later).

---

## 2. Languages

### 2.1 Representation

- Each **language** is a vocabulary of about 100 core meanings ("water", "fire", "mother", "eat", "two", "people" and so on), each a word written in a small phoneme inventory.
- Languages descend from one **proto-language**: PIE-inspired, as decided in v0.3, using the same element stock as M0's names. As before, this is an aesthetic choice for a fictional world, not a claim about who these people are.
- Every band or group speaks one language. A language is shared by many bands; change happens to the language, not band by band.

### 2.2 How languages change

| Process | What happens | Starting rate (PROPOSED) |
|---|---|---|
| **Sound change** | A rule drawn from a catalogue of common, well-attested change types applies to **every** word where its conditions hold, e.g. *p → f* (as in Grimm's law), voicing between vowels, *k → ch* before front vowels, loss of final vowels, vowel shifts. Regularity is the point: changes are systematic, so relationships stay traceable. | about one rule per 300–600 years per language |
| **Word replacement** | A meaning gets a new word: an invented form, or a semantic shift from another word. | tuned so about 70–90% of core vocabulary survives per 1,000 years |
| **Borrowing** | Where languages are in contact (neighbouring land, partners moving between bands), words pass from one to another. | rises with contact |
| **Splitting** | When the speakers of one language become separated (no contact across the gap for several generations), the language divides into daughter languages that change independently from then on. | checked every 25 years |

The retention band in the table is loosely anchored to the classic glottochronology estimate of about 80% of basic vocabulary per millennium (Lees 1953). The rate is known to vary widely between real languages (Bergsland & Vogt 1962), so it is a plausibility range, not a law to fit.

### 2.3 What the observer sees

- **A language family tree** growing over time, with dates of each split.
- **Each language's name** is its speakers' own word for "people" or "us", as many real ethnonyms are; it changes as the language changes.
- **Names change with their language.** A person's name is built from their language's words, so the same root becomes different names in different languages and eras. Clicking a name shows its history back to the proto-form, with each sound change that shaped it.
- **Word comparison:** any meaning traced across sister languages (the "water" word in every descendant).

---

## 3. Customs and tool styles

**Named customs (PROPOSED):** about eight observable practices, each with a few variants, e.g. how the dead are treated, body ornament, hair style, the season of gathering festivals, tool-shaping style, house or shelter form, marriage residence (with his people or hers), naming of children. They begin uniform and drift.

**How they change:**

- **Inheritance:** a new band keeps its parent band's customs.
- **Copying:** bands copy neighbours' customs a little, more when they exchange partners often.
- **Invention:** now and then a band adopts a new variant at random.
- **Conformity:** within a band, the common variant tends to win.

Customs carry no advantage in M1 (they don't yet affect survival), except **marriage residence**, which already exists as a rule. Their job now is to make separation visible and measurable. In M5 (belief) some of them will begin to matter.

**Cultural distance** between two bands is the share of customs on which they differ, plus the neutral drift. It is what the gate measures (section 7).

---

## 4. Spread across water (PROPOSED)

Real people reached islands and new continents across open water tens of thousands of years ago. Proposal:

- From coastal land, a band can cross **one cell of sea (about 56 km)**, rarely, when land on the far side is visible or reachable and the home land is crowded.
- **Wider crossings wait for boats** (a technique, M4).
- The crossing is recorded as an event with its causes ("crowded coast; land across the strait").

Without this, some planets' peoples stay forever on their first continent until M4. With it, islands and nearby continents fill slowly and their peoples diverge in isolation, which is exactly the behaviour M1 is about.

---

## 5. Natural hazards

All hazards come from the environment model, so they happen where they make sense; their effects are physical, and their consequences (hunger, deaths, people moving away) emerge from the existing rules and are explained by them.

| Hazard | Where | What it does | Frequency (PROPOSED: realistic) |
|---|---|---|---|
| **Drought** | Dry and variable climates | Already present as bad years; M1 adds multi-year droughts across a region | from the climate model |
| **Flood** | River and coastal land | Destroys a band's store; a few deaths; less food for a season | per river cell, rises with rainfall |
| **Wildfire** | Dry forest, grassland, savanna | Wild food much lower for several years, then recovers (sometimes richer) | dry seasons, dry years |
| **Volcanic eruption** | Volcanic mountain belts (**see note**) | Local destruction; ash lowers food in a wide area; large eruptions cool the climate for a few years | rare |
| **Earthquake** | The same belts | Few deaths for foragers (no buildings yet) | occasional |
| **Disease outbreak** | Anywhere, more likely with crowding and contact | An outbreak raises deaths in a band and spreads to bands in contact, then fades (survivors resist for a time) | rises with density and contact |

**Note on volcanoes:** M0's planet has mountain belts from noise, not real tectonic plates. M1 proposes adding a simple plate model to world generation, so that volcanoes and earthquakes sit along plate boundaries. This changes the planets themselves, so M0 save files would not carry over to M1.

**Famine is still never rolled.** A drought or fire reduces food; whether people starve depends on their numbers, stores and options, as now.

---

## 6. Performance

M1 adds languages, customs and hazards. To keep a 5,000-year gate practical (section 7), M1 includes a speed pass whose aim is that results stay identical while costs fall, checked by exact fingerprints as in M0.

---

## 7. Gate G1 (PROPOSED)

**Runs:** 5 planets × 10 histories × **5,000 years**. Language divergence needs time to show, and 2,000 years is too short. This is about 2½ times the computing of G0 per history, with half the histories.

| # | Check | Pass mark (PROPOSED) |
|---|---|---|
| 1 | **M0 still holds** | G0's checks for survival, no explosion, plausible demography, nothing from nothing, exact replay and explainability still pass over 5,000 years |
| 2 | **Spread** | Occupied land keeps growing until the reachable land is full; in worlds with islands within one sea cell, most histories reach at least one by sea |
| 3 | **Drift with distance** | In at least 90% of histories, cultural distance between bands rises with the distance between them (a clear positive correlation) |
| 4 | **Drift with time** | Sister languages share fewer words the longer ago they split; retention of core vocabulary is 70–90% per 1,000 years |
| 5 | **Languages multiply** | By 5,000 years, histories have several distinct language families' worth of languages (count to be set from the first runs and approved), and isolated peoples (islands) diverge fastest |
| 6 | **Regular sound change** | Every sound change applies to every word that meets its conditions; every name and word traces back to its proto-form |
| 7 | **Hazards in the right places** | Floods only on rivers and coasts, eruptions and earthquakes only in volcanic belts, fires only in burnable land; each hazard's frequency is within its set range |
| 8 | **Hazard responses** | After floods, fires, eruptions and outbreaks, the affected people show recorded consequences (deaths, moving away, fewer births) with complete cause chains, and populations recover |
| 9 | **Outbreaks spread by contact** | Outbreaks pass between bands in contact far more often than between bands that are not |
| 10 | **Groups match individuals at the food limit** | Birth and death rates of folded groups within 15% of individuals in the same crowded conditions |
| 11 | **Speed** | Reported; target to be set after the speed pass |

---

## 8. Questions for Ben

1. **Sea crossings:** allow rare one-cell crossings from the start, as proposed, or keep everyone on land until boats (M4)?
2. **Customs:** do the proposed eight named customs suit you? Add, remove or rename any (for example, would you like a music or song style among them?).
3. **Language names:** each language named by its own word for "people" or "us". Agreed?
4. **Plate model:** add simple tectonic plates to world generation, so that volcanoes and earthquakes are placed properly, at the cost of M0 saves not carrying over?
5. **Gate size:** 50 histories of 5,000 years, as proposed?
6. **Hazard frequencies:** realistic, as for M0's random events?

---

## Sources

- Lees, R. B. (1953). The basis of glottochronology. *Language*, 29(2), 113–127. (Average retention constant of about 0.805 per millennium.)
- Bergsland, K., & Vogt, H. (1962). On the validity of glottochronology. *Current Anthropology*, 3, 115–153.
