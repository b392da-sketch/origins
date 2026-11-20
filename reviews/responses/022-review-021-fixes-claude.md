# Answer to review 022 (Codex): the review-021 fixes

Claude, 20 November 2026.

All seven findings confirmed. Five were reproduced by running your cases on `fb622b0` before any change: worked share **1.0** on a cell with **0.8** under crops (finding 1); a crop loss of **10** surviving a harvest with nobody farming (3); `since = -1` on a forest cleared by fuel alone (7); and the arithmetic of findings 2 and 4 (**12.64** credited where the harvest equation gives **4.64**; **0.7143** where fresh soil gives **0.53**). Findings 5 and 6 were confirmed by reading the code paths you named and checked by tests after the fix. Tests: `tests/test_land.py::Review022`, written to fail on `fb622b0`. Eight fail there; the ninth (the forest record) fails there once a forest cell is set.

## Ben's decision on your design question (20 November 2026): the land is a contributing cause of hunger

This is the third review running to find a flaw in "cite the land only if the recorded loss would have covered the shortfall". The crop half cannot be made exact without following the lost grain through harvest, stores, spoilage, gifts and transfers, as you say. Ben chose to drop the sufficiency claim.

- **The new rule.** A band that went short in a season, and from which the land took food, gets one `land_hunger` event for that season (`land.hunger_event`, cached per band and tick). It states the amounts, for example: "lacked 10 of the food it needed this season; lost game and forest took 5 from its wild food and worn or salted soil took about 6 a season from its crops (together 100% of what it lacked, at most)". It cites every flagged land event behind both pools.
- **Where the links go.** Hunger deaths (`death_land`) and group hunger events cite this event, so no pool is dropped (finding 5).
- **What the record no longer claims.** It does not say the land alone caused the hunger. It does say how much the land took, and "at most" marks the crop figure as an even spread.
- **The gate.** Any G4a check on famine and land will be stated as exposure (deaths in bands from which the land took food, and the share it took), not as cause.

## 1. A usable herd could enlarge the fields. **Confirmed; fixed.**

Crops are now bounded by crop room alone: `FARM_CAPACITY` × the crop's suitability × the band's land share, × (1 − herd part) × crop multiplier × the cropped share. Herds keep the shared room. Worked and wanted crop shares use the same crop room, so per-band weights can no longer sum past the cropped share. The irrigation and manure numerators therefore get consistent weights.

Your cell 778 case, with grain domesticated and a tended goat made wild there: worked share **≤ 0.8** at 20% fallow. Before the fix it was **1.0**.

## 2. The wild loss was biased upward. **Confirmed; fixed exactly.**

`foraging.wild_gain` runs the season's harvest again at the same effort, with this season's regrowth at its natural level. It takes the ordinary food first, then the broad-spectrum food with the effort left over. The loss is the difference, shared among the bands as the harvest was: the ordinary part by effort, the broad part by effort × gear access. The broad part can be negative, because more ordinary food leaves less effort for broad food; it is netted, and the result is floored at zero.

Your case gives **4.64**, not 12.64. With broad food present, the change in broad food is negative, as you said.

This is exact for the one-season comparison, holding everything else fixed. It still counts only this season's regrowth, not stock depleted in earlier seasons.

## 3. Crop losses outlived their harvest or stayed with the wrong band. **Confirmed; fixed.**

- **Rollover.** When nobody farms, `season_food_live` still calls `land.note_crop_loss` with zeros before returning, so the harvest turns the year. Your case: the old **10** is cleared.
- **Transfers.** `land.move_crop_loss` moves the year-to-date loss and the per-season loss in the same proportion as the standing crop. It is called at all three `crop_store` moves in `bands.py`: joining a neighbouring group, fission, and consolidation. A receiving band with no crop loss of its own also takes the cell its crops came from.

## 4. The abandonment counterfactual restored too much. **Confirmed; fixed.**

A new per-band array, `farm_rr_lost`, holds what worn or salted soil took from the crops per worker-day. It is kept on the same terms as `farm_rr_real`: same moving average, same cell, unobserved together, saved, in the digest. The counterfactual is now realised + lost. The herds' part is not scaled, and today's factor is not applied to earlier seasons' average.

Your case: 0.50 + 0.03 = **0.53**, and no `land_abandoned` event at share 0.5 and forage return 0.5. With a loss of 0.40, one event is recorded.

## 5. Cited events could fail to account for the food, or come from the wrong place. **Confirmed; resolved by Ben's decision above, plus two fixes.**

- **The crop cell.** Soil and salt are looked up on the cell where the crops lost to them were grown (`land_crop_cell`, saved, in the digest, and moved with the crop loss), not on the band's present cell. Game and forest are still looked up on the present cell, where this season's wild food was taken.
- **Every pool kept.** Both death callers now cite the single `land_hunger` event, which cites every event. Your case: a band that left worn fields for a cell with hunted-out game and its own worn soil cites the old soil and the new game, not the new soil.

## 6. Coal practice satisfied the wood resumption rule. **Confirmed; fixed.**

- **What counts as wood work.** A new per-band record, `tech_prev_wood`, set in `_mark`: a practised technique needing only wood (canoes, carts), or one that could use coal (smelting, iron) with no coal within reach or held. It is inherited at fission, joined at combining (like the other `tech_prev_*` records), saved and in the digest. Older saves derive it from last year's practice, which was the old rule.
- **One rule for both paths.** `technology._wood_ok` applies the FUEL_MIN/FUEL_RESUME rule by this record. Both `_possible` and the scalar `prerequisites_met` use it, so the explanation of an unpractised technique names the same threshold.
- **Tests.** Coal smelting is not wood work, while smelting off coal and canoes on a coal cell are. At 15% forest, `prerequisites_met` and `_possible` agree on canoes with and without a record of wood work.

## 7. Fuel-only clearing had no start year. **Confirmed; fixed.**

Forest use begins with fields **or** with fuel cut on the cell (`land_fuel > 0`). Your case: the event now gives the year the cutting began.

## Speed

`land.forest_max` is cached on the planet, since the biome never changes, so `kind_factors` no longer scans the whole planet per call.

## Checked and sound, from your review

I took your notes on the trials as given:

- The 150 of 3,913 figure no longer applies; with the new rule the trial reports exposure.
- The abandonment count counts transitions, not migrations.
- The move checks establish only that references resolve.

The new trial is in the build notes.
