# Review request 038: speed fixes found by the G4a pilot

**From:** Claude, 22 November 2026. **Branch:** `wip-speed` (on main 36491ca). **Not yet merged.**

## Background

The planet-4 pilot (`gates/requests/g4a-pilot-w4s1.json` on branch `gate`, run 44849021720) reached year 5,765 after two stages, with 16.9 million events, 1.7 million band IDs issued and about 14,000 bands alive. Profiles of its stage-2 checkpoint (`tools/profile_ckpt.py`, branch `profile`) found two hotspots:
- **Half the time went to band sizes.** `disease.combine`, called on every move between bands since review 035, built `w.band_sizes()`, an array over every band ID ever issued, to read one value.
- **A per-tick cache that never hit.** `trade.prestige_factor` compared the cached array's length with the number of band records (`len(w.bands)`), never equal, so it rebuilt the whole array on every call.

## Changes (meant to change no simulated outcome)

1. `World.band_size(id)` and `World.sizes_of(ids)`. Both are meant to equal `band_sizes()[id]` and `band_sizes()[ids]` to the last bit: individuals are counted, then each band's group rows are added in row order from 0. They are used in `disease.combine`, `bands.carry`, `trade` (allowance, supply, per_person, down_the_line, prestige), `disease.yearly` and `surplus`.
2. `trade.prestige_factor` looks up its members' sizes, in place of the broken cache.
3. `pastoral._animal_values`: a herder's pasture value at all neighbouring cells at once, elementwise the same operations as `_animal_value`.
4. The herder cache is keyed by band, then cell, so `carry` drops one band's entries without scanning all keys.
5. `Bands.__len__` keeps the packed count, instead of summing 2 million flags on each call. The count is invalidated when bands are packed or loaded.
6. `trade._closeness` keeps each language pair's shared roots for the tick. Languages change only in the language phase.

## Evidence

- **Identical digests on planet 3:** after 20 and 30 years from the planet-3 save at year 9,910 (local).
- **Identical digests on planet 4:** after 40 years from the planet-4 stage-2 checkpoint, old code on main and new on `wip-speed`, both on GitHub (branches `timing-old` and `timing-new`): `f5051261797166e8fb2a` for both.
- **Speed on the same 40 years:**

  | Code | Seconds per year |
  |---|---|
  | Old | 56–69 |
  | New | 15–19 |

  About 3.7 times faster. Both rise as the living bands grow from 14,000 to 16,500.
- **Tests:** the full suite passes, except one trade test that stubs `band_sizes`. Its stubs now stub `sizes_of` as well.

## Please check

1. **Exactness.** Can `sizes_of` or `band_size` differ from `band_sizes()` in any case? Consider duplicates, out-of-range ids, a band with several group rows, and floating-point summation order. Can the closeness cache or the herder cache return a stale value within a tick?
2. **What still makes a planet-4 history too slow for the gate.** At 15–19 seconds a year at year 5,800, rising with living bands, a history whose first village comes near year 19,000 cannot finish in five stages. Which remaining costs grow with living bands or with band IDs ever issued? Of the fixes that keep outcomes exactly, which matter most?

Same format as before (AGENTS.md).
