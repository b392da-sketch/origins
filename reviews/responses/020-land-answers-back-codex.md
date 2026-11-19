# Review 020: the land answers back and the review-019 fixes

**Reviewer** · Codex, 19 November 2026
**Reviewed** · `dc02324..a729391` and the review-019 implementation in `0132315`. Read request 020, the review history, the design and M4 specification (especially §5 and G4a check 9), the build notes, and the carried-forward decisions in the M3 gate report.

## Findings

### 1. A poor harvest counts as resting land, even when the same fields are worked

- **Where** · `origins/sim/farming.py:394–404`; `origins/sim/land.py:128–142,170–187`.
- **What is wrong** · The numerator for land use is crop output after fertility and salinity losses, divided by a capacity that omits those losses. In mixed cells the denominator also takes the first positive crop capacity encountered, even for a band producing only herd food, so the same seasonal crops can yield a different use value if bands choose different crops and their order changes.
- **Why it matters** · Low yield alone grants more inferred fallow recovery and leaching and reduces further soil wear, salt accumulation, erosion and clearance. Conversely, crop productivity bonuses can make the model count more land as worked even with the same field area. These feedbacks change the measured soil and fallow effects.
- **How sure you are** · Certain.
- **How to see it** · On planet 1, cell 2, use a single domesticated crop, saturate crop capacity, hold fallow at 10%, and call `season_food_live`. Fresh soil gives `land_crop / land_cap = 0.90`. Fertility 0.25 gives **0.495** with the same effort and cropped share. The yearly update treats **50.5%** as unused in the second case. The capacity order dependence follows from `seen[c]` in `note_crops`.

### 2. Clearing the forest never raises the fuel cost of smelting

- **Where** · `origins/sim/technology.py:102–107,245–264`; `origins/sim/trade.py:195–208`; `origins/sim/land.py:172–176`.
- **What is wrong** · Smelting checks a permanent forest-biome flag within two rings and production proceeds at the same rate after the living forest is gone. Fuel units are booked after production, and the subtraction clips at zero forest with no cost or production limit.
- **Why it matters** · M4 §5 calls for a fuel cost for metalworking as forest is cleared. In the model a smelter can keep consuming fuel after running out of both wood and reachable coal.
- **How sure you are** · Certain.
- **How to see it** · Give a band pottery, kilns, copper-working and smelting at quality 0.9 at planet-1 cell **5020**, which has tin and no coal within reach. Set every `w.forest` entry to zero before computing practice. Smelting still has quality **0.9** and `trade.yearly` produces **0.4275** tin, with **2.565** total fuel-using goods booked at the cell.

### 3. Losing large game reduces the separate broad-spectrum food pool

- **Where** · `origins/sim/climate.py:22–37,44–49,68–80`; `origins/sim/land.py:91–97`.
- **What is wrong** · The new ordinary-wild-food game and forest factors also multiply broad-spectrum maxima. The same factors apply to all of that pool, including the portion provided by fishing gear.
- **Why it matters** · The build describes the game shares as parts of *ordinary* food. The extra loss suppresses the fallback food that makes diet broadening possible and contributes to the game and forest knockout results.
- **How sure you are** · Certain.
- **How to see it** · On a forest cell, hold climate and gear fixed, set slow game to 0.1, fast game to 0.5 and forest cover to zero. `broad_max` falls to **56.7%** of its previous value, the same multiplier as ordinary stock. The actual broad-stock regrowth in `regrow` uses that same scaled target.

### 4. Empty-cell crossings are suppressed after people arrive

- **Where** · `origins/sim/land.py:219–242`.
- **What is wrong** · A crossing sets its flag before the occupancy check. This consumes the crossing without writing an event. If a previous episode ended after an earlier event, the event ID can also remain in the slot and be reported when the new empty-cell crossing sets the flag.
- **Why it matters** · A new population can live on degraded land indefinitely with a missing or stale source for its explanation. Recovery above the re-arm threshold is required to clear the flag.
- **How sure you are** · Certain.
- **How to see it** · On planet 1, lower game to 0.1 in empty cell **2**, run `land.yearly`, move a band there, and run it again while game is still below 0.3. The flag is true in both passes, the event stays **−1**, and `land.history` returns an empty string after arrival. To see the stale ID variant, first record an occupied crossing, recover above 0.6, and repeat the empty-cell case.

### 5. Famine and migration lack traversable links to land loss

- **Where** · `origins/sim/foraging.py:39–59`; `origins/sim/demography.py:48–69`; `origins/sim/groups.py:245–259`; `origins/explain.py:43–65,224–228`.
- **What is wrong** · The food-driven move stores event numbers in a replaceable string and creates no move event. Individual and group hunger explanations can follow climate or intervention events and have no land reference. The move text can also list soil or salt on a cell even when the move was decided solely from ordinary wild stock.
- **Why it matters** · G4a check 9 asks for famine and migration that trace to land degradation. Co-location or a matching string cannot show whether degraded land affected the outcome, and the reported count of 536 strings does not establish that link.
- **How sure you are** · Certain.
- **How to see it** · Record a game crossing at a band's home, give it a better stocked neighbour, and invoke `foraging.move`. The last-move string includes the land event number and the event log grows by **zero**. Record a hunger death on the affected cell with `demography.kill` and inspect `explain.describe`; the explanation has no reference to the crossing. A group death event's cause list has the same omission.

### 6. The cut-off fallback still includes unrelated imports when two inputs are jointly needed

- **Where** · `origins/sim/technology.py:420–440`, `_cut_off`.
- **What is wrong** · When no single restored mineral is sufficient, the fallback includes every lost import unavailable locally, including goods irrelevant to the technique.
- **Why it matters** · The event's structured material list can give a false account of trade dependence even after the original review-019 iron case is fixed.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **2**, mark the bronze chain at 0.9 with copper, tin and iron each held at 0.01 per person. Remove all three. Bronze requires **copper and tin** to return together. The event's `materials` is **`['copper', 'tin', 'iron']`** even though iron plays no part.

### 7. The land knockout accumulates several years in the annual accounts

- **Where** · `origins/sim/land.py:118–156,193`.
- **What is wrong** · The producers keep booking wild food, crops and fuel while `LAND=False`; the annual reset is skipped. The saved values therefore cover the entire disabled period.
- **Why it matters** · A fixed-off arm suppresses land effects as intended. If such a save is the common starting point for a branch that enables land, its first update uses obsolete multi-year takes, capacities, maxima and fuel, defeating a clean switch-on comparison.
- **How sure you are** · Certain.
- **How to see it** · Step a new world eight seasons with `LAND=False`. After two harvests `land_wild` and `land_take` still retain the accumulated values. Turn the switch back on and the counters are first cleared at the following harvest, after that inherited use has been applied.

## Checked and sound

- **Review 019.** The original bronze case names tin and keeps newly held copper. The original iron case names copper. `technology.combine` transfers both practice and materials rows for `migration`, `merge` and `combined`. The real neighbouring-group transfer, remnant merge and group consolidation each passed on both rows in focused fixtures. Merge followed by stock depletion produces the expected cut-off. The new craft charge multiplies the number of ordinary practitioners by their annual craft share in full-adult years, converts that to one season's effort and caps it at half the available effort. Halving the number of ordinary adults lowers the charge.
- **Annual accounting with land enabled.** Regrowth books the ordinary target once each season. Foraging books the ordinary take once for each used cell. Farming books the new standing crop once when produced, with one positive capacity contribution per active cell per season. The magnitude of the capacity proxy is covered in finding 1. Trade books the production units once per fuel-using commodity, before exchange and wear. Reset follows the harvest at quarter 2, so a normal accounting year is quarter 3 through quarter 2. The first window of a new world contains three seasons. A legacy mid-year save likewise starts with a partial window.
- **Food and fallow.** Actual ordinary and broad-stock changes enter the regrowth ledger, even when a smaller target makes the net change negative. Realized crops enter the standing crop account and the food ledger at harvest. The food invariant excludes standing crops until then. The live path applies fallow once to the crop capacity, leaving herds untouched.
- **Replay.** All 16 arrays are saved and hashed, including the annual accounts and event IDs. Older saves initialize natural land and empty accounts. A save at quarter 0 in the harvest-to-harvest window, with nonzero wild and crop accounts, round-tripped every array. Sixteen subsequent seasons matched digest and complete events with no food, goods or population invariant failures. The land phase draws no randomness.

## Hunting pressure and the trials

- **Pressure** · With fixed effort, shrinking ordinary stock increases the fraction removed, so using the degraded maximum can reinforce game loss. That is coherent with the chosen assumption that foragers take each component in proportion to its availability. The denominator is the sum of the year's **targets**. It varies with climate and depletion, and the numerator pools all ordinary food. Old stock survives a falling target under partial regrowth, so the ratio can even exceed one after an abrupt capacity shock. At steady stock, `REGROWTH = 0.55` puts a 0.55 ceiling on sustainable annual take divided by targets. The observed 0.49 is near that ceiling. At fixed pressure 0.49, with no drift, the stated calibration gives the fast pool a positive equilibrium of about **0.706** and the slow pool no positive equilibrium.
- **Knockouts** · The reported soil-off arm gains **103,481** people over the calibrated land-on arm, about **85%** of the **121,355** land-off gap. That supports soil as the largest reported marginal effect in that planet-3 snapshot **before fallow**. It does not partition the gap into additive contributions, establish the ranking with fallow enabled, or establish it across histories. Ecological feedback, demographic divergence and the initial switch-on all matter. The build notes omit the exact checkpoint, parameter overrides and trial script for those rows, so the individual interventions cannot be verified from the repository. For example, turning off `FOREST_WILD` alone leaves the forest-to-erosion path active, and turning off the crop fertility penalty changes the inferred use in finding 1. The game and forest comparisons also include the broad-pool effect in finding 3.
- **Fallow in the trial** · Going from fertility 0.874 to 0.881 changes the mean fertility yield factor from about **0.924 to 0.929** before salt, a gain of roughly **0.45%** even if those means represented the same fields. The figure is an average over lived-in cells whose occupancy can change. A crop-area-weighted mean would track the soil improvement where crops are grown. A binding fallow cap can readily outweigh that gain. The yearly labour choice still compares crops using `farming.yearly:277–296`, which omits fallow and the actual fertility/salt penalty. People can keep choosing crop work at its nominal return after that work ceases to pay, and village movement uses unadjusted potential in `best_farm_cell`. Together with finding 1, this limits the interpretation of the population difference.
- **Speed** · A 100-call benchmark of the yearly land phase alone on a 40,962-cell founding world took about **13 ms per call**. This does not measure a mature history. The large repeated operations to profile are the two whole-grid neighbour sweeps per year plus crowding, the repeated forest biome scans on seasonal maxima, and the per-band Python loop in crop accounting. The cut-off explanation does a whole-band eligibility pass per candidate lost material per affected band-technique pair, which can cost much more in a simultaneous shortage than in the original regression cases.

## Design questions for Ben

- **Which crowding should set fallow?** The code follows the approved crowding rule as built. Its input is all people in the cell and its ring divided by **natural wild-food** capacity. A nearby forager population can shorten a farmer's fallow without adding any tillage, while identical farming demand can give different fallow on equally good cropland with different wild-food capacities. If fallow is meant to follow competition for cultivable area, which people compete for that area depends on crop labour, reachable suitable fields and whether neighbouring foragers claim the same land. If regional food demand is the intended proxy, count the ring effect as part of the design and compare its fallow against observed crop use at the gate.

## Validation

All **13 focused tests** in `tests/test_land.py` and `tests/test_trade.py::Review019` passed in 46 seconds on Python 3.12, with one AnyIO pytest-plugin deprecation warning. The full test suite run was stopped during the long event-store test. All 35 source files parse with Python 3.10 grammar. No gate-length history was started.
