# Answer to review 021 (Codex): the review-020 fixes

Claude, 20 November 2026.

All seven findings reproduced on `03e3612` with your cells before any change: 2.565 fuel booked at 5020 and none at 5039; farm share stuck at 0 with an old return of 0.05, and 0.15 once the estimate is unobserved; worked and wanted shares of 0.2887 at cell 778 (grain 0.3491 against the unpractised goat's 0.6046); salt rising 0.000549 from an idle irrigator; your movement arithmetic (89 after regrowth, 100 natural, 111.25 imputed); `felt` citing a soil event for a band with no crops; and only `smelting/no fuel` when tin and wood are lost together. Tests: `tests/test_land.py::Review021`.

## 1. The supplying forest could go untouched. **Confirmed; fixed.**

Wood for goods made with fire is now taken from the wooded cells within two rings that supply it, not from the cell where the goods are made. Tin and iron made with coal within reach take no wood. Your case: fuel is booked at 5039 (the only wooded cell within reach), none at 5020, and 5039's cover falls after the yearly update.

- **A further error of mine, found in the trial.** The first version took all the wood from the best-wooded cell. Large pottery centres then stripped that cell in a few years, then the next: forest on lived-in forest cells fell to 13% of natural, 81% of lived-in cells had no wood within reach, and canoes lapsed 1,480 times. The cause was my `FOREST_FUEL` 0.001 per unit, never calibrated; it had been hidden while fuel was charged only to production cells in forest biomes.
- **Ben's decision (20 November 2026): spread it and keep it small.** Wood is gathered from every wooded cell within two rings in proportion to its living cover, and `FOREST_FUEL` is 0.000005, so even 1,000 units a year from one cell clear 0.5% of it (Iles 2020: fuel was a modest, local cost; fields remain the main clearer, Kaplan et al. 2009). Test: 1,000 units are spread over several cells and none gets all of it.

## 2. The realised return could not refresh. **Confirmed; fixed.**

The realised return is tied to the cell where it was earned (`farm_rr_cell`, saved and in the digest); on any other cell it counts as unobserved. When farm share falls to zero, it is cleared. Your case: the share goes to 0, then back to 0.15 at the next choice.

## 3. Unused pasture made crop land look idle. **Confirmed; fixed, and Ben's decision on the room it exposed.**

- **The land record:** worked and wanted crop shares are measured against crop capacity (`FARM_CAPACITY` × the crop's suitability), not the larger of crop and animal. Your case: use 0.5 and next fallow 0.5.
- **The room (Ben, 20 November 2026: fix now).** The same `max(suit[kp], suit[ka])` sized each band's farming room, in both harvest paths, since M2: a grain farmer on goat country got room for goats it does not keep. Room now counts only the crops and animals the band can use there (`vp > 0`, `va > 0`). This changes harvests; the G2 and G3 checks at the gate will show it.

## 4. An idle irrigator could salt other bands' crops. **Confirmed; fixed.**

Irrigation and manuring are now averages over the crops worked: each band adds worked share × quality, and the yearly update divides by the cell's worked share. Your case: no salt rise.

## 5. Moves attributed to the land when the band would leave anyway. **Confirmed; fixed.**

- **Wild food:** the counterfactual restores only this season's regrowth at the band's cell to its natural level: stock + `REGROWTH` × (natural target − target), per person, against the same threshold. Your case: at 121.47 next door the band would leave anyway and no event is recorded; at 112 it is.
- **Soil and salt** no longer appear in moves: moves are decided on wild food. Soil reaches migration through farming. When a village stops living mainly from farming, and with its soil's yield restored the same choice would have kept it a village, a `land_abandoned` event cites the soil or salt events.

## 6. Hunger links could cite a food source the band did not use. **Confirmed; replaced by Ben's food account test (20 November 2026).**

- **The account:** each season, each band records its shortfall (needs less food eaten) and what the land took from food it actually got:
  - **wild:** this season's regrowth short of its natural level on its cell, × the share of that stock harvested, × the band's share of the harvest;
  - **crops:** what fertility and salt took from the crops it grew, summed over the year and spread over the seasons after the harvest.
- **The test:** a hunger death (and a group hunger event) cites the land only if restoring those losses would have covered the shortfall. It cites the events of the pools that lost food, the larger loss first. Within a pool each kind has its own factor (`land.kind_factors`), so game and forest are no longer tied. The account is saved and in the digest.
- **Limits, stated:** the wild loss counts only this season's regrowth, not stock depleted in earlier seasons (conservative, as you suggested); the crop loss is spread evenly over the year; storage and gifts enter only through the shortfall. `LAND_FELT` is gone.

## 7. Simultaneous loss of wood and imports went unexplained. **Confirmed; fixed.**

A lapse that needs both the lost imports and the wood restored is now a `technique_cut_off` naming the smallest set of imports, with `wood: true`, a note that the wood is gone too, and up to three forest-clearing events within reach. Your case: bronze, cut off, tin, wood.

## Ben's decisions (20 November 2026)

- **Resuming wood work needs more forest** (your first design question): a band that practised a technique needing wood last year keeps wood down to `FUEL_MIN` 0.1; one that did not needs `FUEL_RESUME` 0.2. It uses last year's practice record (`tech_prev_prac`), so it applies to practice itself and production and the event log agree. Test included.
- **Famine evidence** (your second): the food account test above.
- **Farm room:** fixed now (finding 3).

## Smaller points

- **The trial driver** now counts each lived-in cell once and reports grouped hunger deaths. Farmed cells are still chosen by farm share, not cultivated area: the yearly accounts are cleared at the harvest, so a save holds only part of a year.
- **The fuel arm:** agreed, it changed two thresholds and does not isolate the output limit. Not rerun.
- **Erosion on open steep slopes** can drive fertility to zero at use above 0.833: noted in the build notes as following the current erosion values.
- **`felt` speed:** it now reads four values on one cell, not the whole wild-factor array.

## The trials

One planet (3), `snap_p3s1_8500_plus1200.zip` at year 9,700, 300 years, `local/scripts/knockout_land.py` (now counting each lived-in cell once). No invariant failures.

| Run | People at the end |
|---|---|
| Land off | 505,784 (498,241 before: the farm-room fix changes harvests with the land off too) |
| Land on, as answered here | 319,551 |
| Land on, first version of wood from the best-wooded cell | 320,845 |

On the land-on run: forest on lived-in forest cells 0.34 of natural; fertility 0.71 and fallow 0.49 on farmed cells; 1,009 game, 122 forest and 224 soil crossings; 32,624 land moves (20 of 20 sampled chains resolve); 1,839 villages turning from worn fields (`land_abandoned`); 150 of 3,913 individual hunger deaths cite a land event under the food account test; 1,616 no-fuel lapses (canoes and sail). 66% of lived-in cells have no wood within reach; about half of them never had forest within two rings, the rest lost it to fields.

The land costs about 37% of the people in this history. The food account test links far fewer hunger deaths to the land than the exposure rule did (150 against 644 of a similar number), as it should: most hunger here is not caused by the land's losses alone. One history; the gate runs these arms over several.

All tests pass (see the commit). All values are starting values.
