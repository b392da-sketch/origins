# Review 022: the review-021 fixes and Ben's land decisions

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `e85485d..ef87313`, including the review-021 answer, the M4 build notes and the knockout driver. The seven original cases pass in the focused tests. The new food accounts replay exactly. The cases below identify remaining gaps in crop accounting, causal attribution and wood work.

## Findings

### 1. A usable herd can still enlarge the crop room past the fallow limit

- **Where** · `origins/sim/farming.py:452–481`, `origins/sim/land.py:146–162,275–277`.
- **What is wrong** · The crop numerator can use pasture-sized room, while its denominator is now crop capacity alone. The resulting worked share can exceed the active cropped share or even 1. The cell's work sum is clipped, but the irrigation and manure numerators still receive the unclipped weights.
- **Why it matters** · Adding a small herd can make the same fields produce more crops and record more land as worked than the fallow setting permits. At high use, the inconsistent weights can also distort the new irrigation and manure averages.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **778**, give a single band domesticated grain (value **0.3491**) and a usable tended goat (value **0.0907**, pasture suitability **0.6046**). Set fallow to 20% and saturate labour. Before clipping, the reported worked fraction is about **1.10**, computed as `(0.6046 / 0.3491) × (1 − 0.0907 / (0.3491 + 0.0907)) × 0.8`. The live path records **1.0** worked and **1.0** wanted on a cell with only **0.8** available for production.

### 2. The estimated wild loss can exceed the extra food that restored regrowth would yield

- **Where** · `origins/sim/foraging.py:141–152,199–210`.
- **What is wrong** · The estimate applies the fraction harvested at the depleted stock level to the restored food. At fixed effort that fraction falls as stock increases. Added ordinary food can also displace broad-spectrum food, which the estimate leaves untouched.
- **Why it matters** · Restricting the calculation to current regrowth leaves out earlier depletion, but the estimate is upward-biased within that season. It can pass the food account test even when restoring current regrowth would leave the band hungry.
- **How sure you are** · Certain.
- **How to see it** · With ordinary stock **100**, effort **100**, and **20** more units of regrowth under natural conditions, the code credits **12.64** units. Applying the same harvest equation to stock **120** and subtracting the actual harvest yields **4.64** additional units with broad-spectrum food disabled. A shortfall of **10** passes the current attribution test and persists in the fixed-effort comparison.

### 3. Crop losses can outlive their harvest or stay with the wrong band

- **Where** · `origins/sim/farming.py:436–443,478–502`, `origins/sim/land.py:380–390`, `origins/sim/bands.py:124–126,157–159,266–267`.
- **What is wrong** · When nobody farms, the early return skips the harvest rollover and leaves the last crop loss active. The loss accumulator also stays with its original band through fission, migration and consolidation, while the standing crop it describes is transferred.
- **Why it matters** · A forager can cite a loss left over from a previous year's harvest. A receiving band can harvest a reduced crop with no matching loss, while the source keeps the whole loss estimate.
- **How sure you are** · Certain.
- **How to see it** · Book **40** units of crop loss at a harvest, giving **10** per season. At the following harvest set every farm share to zero and run `season_food_live`. The old **10** remains, and a same-cell soil flag is cited against a new **8**-unit shortfall. For transfer, compare the three explicit `crop_store` moves with the absence of a corresponding `land_crop_acc` move.

### 4. The fresh-soil abandonment comparison can restore too much of a mixed farm's return

- **Where** · `origins/sim/farming.py:296–327,343–364,468–495`.
- **What is wrong** · The fresh-soil comparison scales the entire realised crop-and-herd return by the ratio of nominal mixed returns. It assumes the realised mix matches the nominal mix even when crop capacity, pasture and fallow bind differently. It also applies today's factor to an average that includes earlier seasons.
- **Why it matters** · The logger can say that soil tipped a village below half-time farming even when restoring the missing crop yield would still leave it below the line.
- **How sure you are** · Certain for the counterfactual arithmetic.
- **How to see it** · Take a recorded return of **0.50** per worker-day with **0.48** from herds and **0.02** from crops, a crop factor of **0.4**, and nominal multipliers **0.7** worn and **1.0** fresh. Holding effort and capacity fixed, fresh soil gives **0.53**. The logger estimates **0.7143**. At farm share **0.5**, forage return **0.5** and the default risk factor, `_land_abandoned` emits an event using the larger estimate. With the actual restored crop increment the next share would still fall below 0.5.

### 5. The cited events can account for less food than the test says was recoverable

- **Where** · `origins/sim/land.py:345–367`, `origins/sim/demography.py:64–73`, `origins/sim/groups.py:249–261`.
- **What is wrong** · The sufficiency test sums both pools before checking which events exist. The crop pool describes the past harvest, while the event lookup uses the band's current cell and current factors. Both death callers retain only the first returned event, including cases that need both pools.
- **Why it matters** · A traversable chain can link to an event that cannot explain the measured shortfall. This can also attach the destination's soil history to a crop loss on the land the band left.
- **How sure you are** · Certain.
- **How to see it** · Record **6** crop loss per season, **5** wild loss and a **10**-unit shortfall. Give the cell only a soil event. `felt` returns that event even though the crop loss alone covers only **6**. Adding the missing wild event lets `felt` return both, but either death caller still keeps only one.

### 6. Coal practice can satisfy the wood resumption rule

- **Where** · `origins/sim/technology.py:125,188–230,305–319,399–404,678–685`.
- **What is wrong** · The rule treats practice of any technique listing forest as evidence of wood work, even if coal met the requirement. The scalar prerequisite explanation also accepts 10% forest for a band that the vector practice path requires to have 20%.
- **Why it matters** · A coal-using smelter can start canoes at 15% forest without recent wood work. At the same cover, a band without that history can get an unpractised-technique explanation that omits the applicable wood threshold.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **300**, give a band pottery, kilns, imported copper and smelting, with coal within reach and best forest cover **0.15**. With empty practice history, `_possible` rejects canoes but `prerequisites_met` returns **`(True, [])`**. Mark current practice through `_mark`. Coal-supported smelting then makes canoes eligible with the same forest cover.

### 7. Forest history omits the start of fuel-only clearing

- **Where** · `origins/sim/land.py:165–186,263–270,294–332`.
- **What is wrong** · The forest's recorded use begins only when there is cropping on the supplying cell. Remote fuel now clears the forest directly, but fuel use does not set or keep its start year.
- **Why it matters** · A lived-in cell cleared for fuel alone can emit a forest event claiming clearing since **year −1**. Later fuel-cutoff and food events can cite that history.
- **How sure you are** · Certain from the crossing predicate.
- **How to see it** · Hold crop use at zero on an occupied wooded cell, book positive fuel removal and cross the forest threshold. `_crossings` reads the fuel-depleted cover, but `active["forest"]` is false. On a cell with no earlier cropping, the event keeps the initial `since=-1`.

## Checked and sound

- **Review 021 cases.** Fuel is debited at the wooded source, and coal-smelted tin and iron book no wood. A band can retry farming after its share drops to zero, and observations from a different cell are ignored. The pure-grain worked share and zero-effort irrigator cases pass. The original false wild move is rejected, and direct wild moves omit soil. A band without crop or wild losses receives no food-account link. The bronze case records the joint loss as tin plus wood.
- **Movement and wood counterfactuals.** Restoring the current regrowth increment is exact for the one-season comparison holding old stock, destination and occupancy fixed. The two-input cutoff restores wood when testing subsets of lost imports. A wood-only lapse still uses the no-fuel path. The original single-wood-tech case keeps practice at 15% if active last year and requires 20% to resume after a lapse.
- **Food accounts and replay.** The seasonal shortfall uses actual food eaten after sharing. All four band accounting arrays and both realised-return arrays persisted exactly at quarter 0, with nonzero wild loss, a previous crop loss and an in-progress crop loss. A further 16 seasons matched digest and complete events, with zero food, people or goods invariant failures. The loss accounts are explanatory quantities and do not themselves credit food.
- **Farm room.** Both harvest paths now ignore the capacity of unavailable species. Pure herders lose any old benefit from a more suitable but unusable crop. `best_farm_cell` and pastoral movement already mask unusable species, so the change in harvest room does not change their ranking formulas. The remaining effect on mixed farms is finding 1.
- **Fuel units.** The proportional weights sum to one for every producer with wood, including shared sources. Fuel draw is then a forest-cover decrement in `land.yearly` and recovery uses the existing regrowth formula. At the starting rate, 1,000 units allocated to one cell request **0.005** of natural cover. There is no independent wood stock ledger. If simultaneous requested clearance exceeds available cover, clipping discards the excess, so the production limit remains a cover-based approximation. The approved alternative fuels for pottery and native copper still allow production when there is no forest to debit.

## Trials and interpretation

- **Population.** The common-checkpoint arms give **505,784** with land off and **319,551** with land on, a **36.8%** endpoint difference for the whole land package in this history. The corrected farm room also acts with land off, so compare these matched arms. The 320,845 earlier fuel variant combined a different allocation rule and fuel rate. Its endpoint alone cannot isolate the effect of spreading fuel. The checkpoint is external and I did not rerun the trials.
- **Famine and migration.** The **150 of 3,913** figure counts linked individual hunger deaths under the new rule. It does not establish how much hunger the modeled land loss caused, given findings 2, 3 and 5. The grouped hunger total is cumulative in the driver and has no matching linked-death denominator for the trial. The **1,839** abandonment records count transitions out of village farming, which can occur without subsequent migration. The **20 of 20** move checks establish resolvability of references, while the movement arithmetic and outcome evidence need their own checks.
- **Speed.** The move path caches the two seasonal target arrays. `kind_factors` still calls whole-planet `forest_max` to read a single cell, so each qualifying move or hunger account can still trigger a biome scan. That cost is separate from event storage.

## Design questions for Ben

- **Crop timing for famine evidence.** An even spread of the crop loss is suitable as a yearly exposure measure or a way to select cases for inspection. It can undercount the effect at harvest and overcount it after excess grain would have spilled or spoiled. Hunger deaths also reflect condition accumulated over prior seasons. For a gate claim that the harvest loss covered a particular shortfall, follow the affected crop through the harvest, stores and transfers, or test the case using those same rules with its yield restored.

## Validation

**33 focused tests passed** in 117 seconds, covering all land tests, the review-019 trade cases and the existing exact-replay regression. One AnyIO pytest-plugin deprecation warning. The additional cases and replay are under ignored `reviews/scratch/`. The source files parse with Python 3.10 grammar. No full suite or gate-length run was started.
