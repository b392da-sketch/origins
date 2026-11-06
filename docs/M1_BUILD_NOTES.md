# M1 build notes

Working notes for M1 "spreading and drifting apart": what was built, what was tried and did not work, and the numbers chosen. All rates are tunable starting values in `origins/params.py`, not measurements.

## What was built

| Part | Where | Notes |
|---|---|---|
| Plate tectonics | `worldgen.py` (`_plates`) | 14 irregular plates; convergent boundaries raise mountains (up to about 5.5 km); volcanic belts on convergent boundaries and rifts, plus 4 hotspots; seismic zones along all boundaries. M0 saves no longer load against the new planets (decided by Ben). |
| Proto-language | `lang/proto.py` | 93 core meanings in PIE-inspired forms; scholarly and readable spellings. |
| Sound changes | `lang/changes.py` | 31 regular change types (Grimm-like fricatives, satem/centum, laryngeal loss, rhotacism, final-vowel loss, and so on). Each applies to every word at once, which is what keeps words traceable. |
| Languages | `sim/language.py` | Checked every 25 years: sound change (about one per 450 years), word replacement, borrowing from languages in contact, splitting, language shift. Every word and name can be replayed from its proto-form. |
| Names | `state.People.name` | Built from the speaker's language's own words for the M0 name elements, so names change as the language changes. |
| Customs | `sim/customs.py` | 8 named customs with variants plus 12 neutral traits. Marriage residence now sets where a new couple lives (M0's fixed 50/50 is the founders' starting custom). |
| Hazards | `sim/hazards.py` | Floods (rivers, more in wet years), wildfires (burnable land, more in dry years), eruptions (volcanic belts; large ones cool the region), earthquakes (plate boundaries), disease outbreaks (start more often where crowded, spread only through contact, leave immunity). Lost wild food recovers over years. Every hazard death names its hazard. |
| Sea crossings | `sim/hazards.py` (`crossings`) | A hungry coastal band with no relief on foot may cross one ocean cell to empty land on the far side. |
| Observatory | `server.py`, `observatory/index.html` | Map layers for languages (related languages in related colours), customs and hazards; language pages (descent, sound changes, closest relatives, word list against the proto-language); each person's name history; each band's customs and their changes. |
| Gate G1 | `gates/g1.py`, `gates/g1_report.py` | Sliced, checkpointed histories with measurements taken during the run. |

## Tried and changed

- **Languages split far too often at first.** With splits after 75 years of separation of any fragment, 90 people produced 64 languages in 600 years (about 250 speakers each). Now a separated community must have at least 250 people and stay apart about 150 years; small outlying fragments keep the speech of the largest community. Result: about one language per 1,200–1,500 speakers, in the range reported for forager languages.
- **Languages scattered like confetti on the map.** Bands wander and split, so with no other force, bands of many languages ended up interleaved (only about 45% of neighbouring bands spoke the same language). Added **language shift**: a band where at least half the people within two rings speak another language takes it up with chance 0.8 per 25-year check (children follow; adults keep their own speech and names). Neighbour agreement rose to about 55–70%. It remains patchier than real language maps; band mobility (an M0 behaviour) is the underlying cause.
- **Customs did not vary with distance.** With frequent random invention and weak copying, near and far bands were almost equally different (rank correlation about 0.05). Slower invention and more copying between neighbours gave correlations of about 0.2 at year 1,000. In two dimensions, drift with distance is known to be weak (it grows only with the logarithm of distance in stepping-stone models), so the gate measures cultural distance as customs and language together, and reports each part separately.
- **Group test.** M0's test that groups and individuals have the same birth and death rates failed by a few points once hazards were added, because one outbreak is a large, rare event that happened in one twin and not the other. The test now compares everyday rates and leaves out hazard deaths (which are applied to both by the same code).
- **Groups at the food limit (gate check 10).** Halving wild food at year 800 did not make the world crowded (food received stayed at 100% of needs while people spread to new land). The experiment now cuts wild food to 30% and checks that food gathered ÷ needed falls below 1.3, where food limits births.
- **Outbreaks** at first caused about 10% of all deaths; the starting and spreading rates were halved.
- **Groups at the food limit, second and third attempts.** Cutting food to 30% at year 800 gave rates within 11%, but planets 3 and 4 were still spreading into empty land (planet 4 had only about 3,000 people at year 800), so they were not at the food limit. The final test cuts wild food to 20% from year 800, or later once 15,000 people live there, measures rates over years 100–300 of the test, and requires food gathered ÷ needed below 1.5 (where food holds births down). Result: births 0.91–0.96× and deaths 0.92–0.97× of individuals' rates on all five planets. Groups run slightly lower on both, a small systematic difference worth watching.
- **Spread measured by food capacity.** At year 5,000 people occupy only 35–62% of the cells of their starting land mass, but those cells hold 80–99% of its food capacity: the rest is mostly ice, desert and high mountains. The gate's "until the reachable land is full" is measured by food capacity.

## Open findings from the first G1 histories
- Outbreaks cause about 9% of all deaths. Infectious disease was a leading cause of death among foragers, but whether epidemic outbreaks (as opposed to everyday illness) should be this large a share at low density is doubtful.
- Island languages do not yet diverge faster than mainland languages split the same time ago (19% shared words either way at 3,000–5,000 years apart). Borrowing is the only process that differs with isolation, and it is small.
