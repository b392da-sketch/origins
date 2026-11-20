# Review 033 — review-032 fixes

Codex, 21 November 2026. Reviewed `d7ddb9c..1edee6e`.

The writing log now records use. Finding 3 should block G4a's comparison of writing with polity tenure until the relevant polity histories are retained. Carry the remaining findings into the comprehensive pre-gate review.

## Ranked findings

### 1. One conquest can add the same imposed name twice

- **Where** — `origins/sim/places.py:481–527`.
- **What is wrong** — Adoption draws separately for each conquered band, but the result is a layer shared by the whole language at that feature. After an adoption, `ours is theirs` is still false because the imposed layer is a separate object, even when both forms are identical.
- **Why it matters** — A single conquest can create duplicate historical layers and increase the chance of adoption based on how many bands represent the same language.
- **How sure you are** — Certain. Reproduced with one conquest and two conquered bands.
- **How to see it** — Give two bands of one language the same feature and conquer them in one event. Make both draws succeed. The pass appends two identical imposed forms, with both layers linked to that conquest. The next scheduled pass correctly excludes the old conquest.

### 2. Conquest links identify a polity and tick, leaving the target ambiguous

- **Where** — `origins/sim/places.py:467–478,493–499,515–527` and `origins/sim/conflict.py:395–411`.
- **What is wrong** — The lookup picks the latest conquest for each polity and tick without checking that it affected the band. The caller uses the band's current polity membership, which can change after the conquest.
- **Why it matters** — A resolvable naming chain can point to a conquest of a different target. If the band has changed polities, the code may cite the current polity's name as the conqueror's while omitting the conquest event.
- **How sure you are** — Certain. Reproduced the ambiguous event lookup.
- **How to see it** — Supply two conquest events for the same polity and tick with different targets. A naming layer for the first target links to the second event. Both events can resolve successfully.

### 3. G3 can discard the tenure history for a writer it reports

- **Where** — `gates/g3.py:54–62,116–123` and `origins/sim/polity.py:237–242,508–513`.
- **What is wrong** — G3 exports every writing row but samples the polity log. The guaranteed retention rule covers polities that reached five settlements. A complex chiefdom can qualify at three.
- **Why it matters** — The writing rows distinguish use from memory and identify seats. They cannot establish how long a missing polity stayed at tier 2 or 3, including intervals before and after it had scribes.
- **How sure you are** — Certain. Reproduced through the G3 writer.
- **How to see it** — Supply 1,501 polity histories of three settlements and two levels of rule. Choose the polity omitted by the seeded 1,500-history sample and give it a practising writing row. G3 exports that row and drops its entire polity history. Retained histories support a comparison at the ten-year sampling resolution.

### 4. A cell panel can show a name nobody in that cell uses

- **Where** — `origins/server.py:296–308,355–369`.
- **What is wrong** — `cell_places` uses the same feature-wide majority as the map. The clicked cell's speakers can all use another name for that feature.
- **Why it matters** — Regional and river names can be correct for the whole-feature map and misleading in a panel about one locality.
- **How sure you are** — Certain. Reproduced with two occupied cells in the same region.
- **How to see it** — Put one language in the clicked cell and twice as many speakers of a second language in another part of the region. Give both languages names for the region. The map and cell panel both show the second language's name. The place detail correctly lists both.

### 5. The stimulus exposure still appears as a causal edge

- **Where** — `origins/sim/technology.py:635–650`.
- **What is wrong** — The new `stimulus_needed` field correctly distinguishes a draw that needed the multiplier. The `False` branch still includes the source band in `causes`, although its own note says the invention would have occurred anyway.
- **Why it matters** — G3 can count the two cases correctly using the boolean. The cause graph still depicts exposure as a cause for both.
- **How sure you are** — Certain from the two branches and the zero-draw test.
- **How to see it** — In the existing zero-draw fixture, inspect the invention with `stimulus_needed=False`. Its causes still include `{"band": src}`.

## Checked and sound

- Region features covered all land in each of the 123 land-bearing regions returned by the planet-3 feature builder. Their anchors matched the nearest land cell to the region's centre. Both name templates use the current local lexicon.
- The original naming-tick sound rule is included. Newcomer retention now checks every holder band. The conquest adoption window excludes old events on the next scheduled pass, and its default probability falls from 50% to 10% as size rises from zero to one. The branch considers features used by the affected bands where both languages have a layer.
- Kept and replaced layers cite the earlier naming event when its ID is present. An imposed layer in the one-event fixture cited the source naming and the conquest, and the resulting references resolved. Legacy layers without an event ID still display.
- The map returns feature-wide names and place detail returns current names by language, forms then and now, and cause references. In a synthetic planet-3 world with 20,000 bands, 250 languages and about 5,800 named features, median function plus JSON serialization times were 69 ms for the map, 7 ms for one region detail and 7 ms for a cell. The full map response was about 0.84 MB. Each endpoint rescans living bands, and the server runs these reads under the world lock. These timings exclude network and browser rendering.
- All 21 focused tests in `tests/test_places.py` passed. Place layers and the writing log round-tripped and replayed for 12 seasons with matching events and digest. The simulation and gate sources parsed under the Python 3.10 grammar.
