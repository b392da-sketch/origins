# Review 024: the review-023 fixes

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `fe6fb13..f20c2a4`, the review-023 answer, the M4 build notes and the knockout driver. The original cases pass. The new arrays replay from a current save. Five follow-up findings concern older saves, crop-event attribution and exposure counts.

## Findings

### 1. Older saves can crash when a band ends with the land switched off

- **Where** · `origins/persist.py:228–232`, `origins/sim/land.py:438–461,465–469,493–499` and `origins/sim/bands.py:317–325`.
- **What is wrong** · A save from review 023 can load nonempty loss amounts and empty new provenance arrays. `drop_crop_loss` checks only the older accumulator's length before accessing all the arrays. With `LAND=False`, the food phases and transfers never grow the new rows first.
- **Why it matters** · The land-off arm can stop on the first extinction or remnant merge when started from an older land-enabled checkpoint.
- **How sure you are** · Certain.
- **How to see it** · Build a save with the review-023 fields `land_land_crop_acc`, `land_land_lost_crop` and `land_land_crop_cell`, and omit the three new arrays. Reload. The old accumulator has **64** rows while `land_acc_top` and the two event arrays have **zero**. Set `LAND=False` and call `bands.end_band` for band 0. The crop cleanup raises **IndexError**.

### 2. A merge can split the peak loss from its event IDs

- **Where** · `origins/sim/land.py:438–454,478–488`.
- **What is wrong** · `move_crop_loss` chooses the in-progress event IDs by comparing the bands' accumulated losses, then chooses the peak value independently by comparing their largest seasonal losses. The number and the IDs can describe different seasons.
- **Why it matters** · After a merge the final harvest can cite a smaller loss's events even under the stated largest-season rule. A later loss between the retained IDs' actual amount and the recorded maximum cannot correct the mismatch.
- **How sure you are** · Certain.
- **How to see it** · The receiving band loses **12** twice at cell **2** and the joining band loses **20** once at **778**, each with a soil event. Move the whole loss. The result has a total of **44** and a peak of **20**, with only cell **2**'s event. The winning season according to the peak was at **778**.

### 3. Crop records can cite a land condition that reduced no yield

- **Where** · `origins/sim/land.py:346–353,465–488`.
- **What is wrong** · At booking time the code copies every active soil and salt flag from the peak season. A salt flag can remain active below the yield-penalty threshold. The stored loss can then be wholly due to fertility, while the only cause ID points to salt.
- **Why it matters** · The exposure count can register the whole crop loss as linked to a land condition that contributed zero to it.
- **How sure you are** · Certain.
- **How to see it** · At cell **2**, keep a previous salt event active with salt at **0.2**, between the re-arm and yield thresholds. Set fertility to **0.7** with no soil event. On **100** units of potential crop, fertility takes **18** and salt takes **0**. Book the 18 at harvest and record a shortfall. `felt` returns the salt event.

### 4. A representative season can make the census drop a genuine link or credit the whole crop loss

- **Where** · `origins/sim/land.py:368–370,404–418,473–489,515–524`.
- **What is wrong** · All seasonal crop losses are summed, but the largest season's IDs determine whether the entire total is linked. A larger unlinked season removes links for smaller linked seasons. A slightly larger linked season assigns all the smaller unlinked losses to its events.
- **Why it matters** · A peak-season event is a defensible example of where losses occurred. It does not support the linked amount used by the event and census. The same rule can attach new provenance to old amounts from a legacy save if the first new loss is smaller than the carried amount.
- **How sure you are** · Certain.
- **How to see it** · Record **49** of linked loss at cell **2**, then **51** with no event at **778**. At harvest the seasonal estimate is **25** and none is linked. Reverse which field has the larger loss and all **25** is linked, even though only **51/4** comes from the linked season.

### 5. Vectorised exposure counts and event lookup diverge under yield knockouts

- **Where** · `origins/sim/land.py:346–366,510–516`.
- **What is wrong** · `_links` checks whether the relevant yield factor is reduced. The vector code tests whether the underlying stocks are reduced, regardless of the configured food shares.
- **Why it matters** · Removing one component from wild yield can leave a false census link to that component when the other component still reduces food. A trial can then register exposure that the equivalent death event would omit.
- **How sure you are** · Certain.
- **How to see it** · Use a forest cell with a game event, depleted game and forest, and no forest event. Set both game food shares to zero and retain positive wild loss from forest. With a **9**-unit shortfall and **6** wild loss, the census adds one wild-only band-season. `felt` returns no link because the game yield factor is exactly **1**.

## Checked and sound

- **Original cases.** A world with no active farmers harvests the existing **25** crop and credits the farmed ledger. The remnant brings the expected stores, crop and in-progress loss. A later sowing and recovery of the old field leave the last harvest's event IDs intact. The hunger record separates a wholly unlinked pool from the linked pool and labels the annual crop estimate. The census registers a qualifying meal with no death event.
- **End-band paths.** The remnant merge transfers crops before closing the old band. Consolidation retires groups directly after the paired transfer. Fission and joining a neighbouring group move the paired crop and loss amounts proportionally. Other calls to `end_band` are the zero-member cleanup. Marriage and capture move people without transferring field ownership under the current rules. The cleanup is consistent for current saves.
- **Default census.** With the starting yield shares, the vector and scalar link tests agreed on **1,000** mixed rows combining wild flags, crop references, positive and zero losses, and shortfalls. The counts partition correctly and the loss cap is applied per band-season. The difference under knockouts is finding 5.
- **Persistence.** A quarter-0 save preserved non-default previous-harvest IDs, current IDs and peak loss, along with the census counts. It replayed exactly for **16** seasons in digest and events, with zero food, people or goods invariant failures. Ignoring `land_crop_cell` avoids inventing historical event IDs from a cell alone. Older saves retain numerical losses and need the shape handling and attribution covered above.

## Trial and interpretation

- The matched endpoints **503,114** off and **326,460** on give a **35.1%** difference for this checkpoint and configuration. The trial driver subtracts the starting census and grouped-death totals. The checkpoint is external and I did not rerun the reported histories.
- The category counts sum to **67,259**, or **83.7%** of the **80,344** short band-seasons. The reported **45%** is a deficit-weighted ratio of linked loss, capped per band-season, to total food lacked. Its crop part inherits the representative-season selection in finding 4. It describes exposure under the model's accounting convention. The **one crop-only** row says little about the size of crop losses when both pools contributed.
- The **797 of 3,829** figure is **20.8%** of individual hunger deaths with a link. The **7,732** event records remain a mortality-selected sample, distinct from the exposure census. The **1,057** events with unlinked losses are counted from rounded event values, so positive unlinked amounts below **0.05** can round to zero and fall out of that count.

## Validation

**47 focused tests passed** in 136 seconds, covering all land tests, the review-019 trade regressions and the existing exact-replay regression. One AnyIO pytest-plugin deprecation warning. The source files parse with Python 3.10 grammar. Focused reproductions and replay output are under ignored `reviews/scratch/`. No full suite or gate-length run was started.
