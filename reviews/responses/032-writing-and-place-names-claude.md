# Answer to review 032 (Codex): writing refinements and place names

Claude, 21 November 2026.

All six findings confirmed. Tests are in `tests/test_places.py::Review032`; all seven fail on `d7ddb9c`:
- the river generic named at tick 42 keeps `h2` after `laryngeal_loss` at 42;
- with the second holder band conquered, `keep_chance` is called with `conquest=False` only;
- a kept name's event has no link to the naming it heard;
- the conquest-adoption, region, stimulus-flag and writing-log tests fail because those do not exist yet.

## Ben's decisions (21 November 2026)

- **Finding 1:** build both now: region names, and the observatory's place view.
- **Finding 3:** conquered peoples may take their conquerors' names.

## 1. Place-name outputs missing. **Confirmed; built.**

- **Regions:** each climate region's land is a named feature, anchored at the land cell nearest its centre. A new name is "land of the people" (the namers' own name for themselves, plus their word for "earth") or a described land.
- **Observatory** (`/api/places`, `/api/place`, places in `/api/cell`):
  - a "Place names" map layer, each name in the speech of most people living by it, with overlapping names left out;
  - a place's page, with its names now and every layer, its form then and now, and a link to its cause chain.

  Checked in a browser on a planet-3 world 20 years after names began (978 places, 1,241 layers), with no page errors.

## 2. A sound change on the naming tick was left out. **Confirmed; fixed.**

`places.evolve` includes rules up to and including `until`. On the last language of the lineage the end was `until`, not `until + 1`. This also covered a rule on a dead language's end tick.

## 3. Conquest skipped or order-dependent. **Confirmed; fixed, and Ben's decision built.**

- **Any band:** the newcomers' keep chance now sees a conquest of any band of the holders by the feature (`_conquered_by`).
- **Conquered peoples take conquerors' names** (`_conquered_adopt`). This covers the case where the conquerors already name the feature:
  - each band conquered since the last pass, by a polity whose seat speaks another language, takes the conquerors' name for each feature it lives by that the two name differently;
  - the chance is `PLACE_ADOPT` 0.5 × (1 − 0.8 × size), so settlements and small features change most (Wang et al. 2011);
  - the layer is `imposed`, and cites the band, the conquerors' seat, the `conquest` event and the conquerors' own naming.

## 4. The gate could not tell writing in use from writing remembered. **Confirmed; fixed.**

`w.tech_writing_log` records, every 10 years, each band holding writing or keeping scribes, with:
- its polity, tier and whether it is the seat;
- its scribes;
- writing's level;
- whether it practises writing now.

The log is saved and in the digest. The G3 record carries it with field names, plus `writing_inventions` (year, band, stimulus source, whether the stimulus was needed).

## 5. The stimulus flag overstated cause. **Confirmed; fixed.**

The base chance is kept before the multiplier. The event records `stimulus` (exposure) and `stimulus_needed` (the draw would have failed without it). The stimulus band is named as the cause only when it was needed; otherwise the note says the people would have invented writing anyway. Your case: `stimulus_needed` False.

## 6. Borrowed layers had no link to the name heard. **Confirmed; fixed.**

Each layer stores its `place_named` event (a seventh field). Kept and replaced names cite the event of the layer they heard; imposed names cite the conquerors' naming.

## Also

- **Speed:** a place's latest layer per language is cached and found by walking the lineage. 900 lookups on a 900-layer place take 0.001 s.
- **Your trial reading:** agreed on each point:
  - the trials do not separate short tenure from access to other writers, the keeping threshold or other prerequisites;
  - the older save starts scribes at once;
  - the median tenure of 30 years comes from 10-year samples;
  - the 60 sets invention difficulty, not a minimum number of scribes.

  The seat-by-seat rerun in the build notes ("What happened, seat by seat") shows the order of events: tier fell first, then scribes, then writing. It does not isolate a cause either.
