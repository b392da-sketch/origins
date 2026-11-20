# Review 023: the review-022 fixes and the contributing-cause rule

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `fb622b0..25541fb`, including Claude's answer, the M4 design and build notes, and the land knockout driver. The original regression cases pass. The new accounts replay from a normal save. The remaining findings concern which harvest a loss belongs to, which bands receive it, and what the trial counts.

## Findings

### 1. Rollover can record a harvest loss while skipping the standing crop itself

- **Where** · `origins/sim/farming.py:447–456,516–521` and `origins/sim/land.py:440–453`.
- **What is wrong** · The no-farming return now rolls over crop losses, but it still returns before releasing standing crops at harvest. Release is skipped only when *every* living band has stopped farming. Continuing farm work anywhere would let the same standing crop be harvested.
- **Why it matters** · A band can miss the food it already grew, while its account starts reporting the unrealised portion as a loss from the latest harvest. One unrelated band's work determines whether that food gets released and booked.
- **How sure you are** · Certain.
- **How to see it** · With every farm share at zero, put **25** food units in a living band's `crop_store` and call `season_food_live` in the harvest quarter. The band receives **0**, the standing crop stays at **25**, and the loss rollover runs.

### 2. A remnant merge retires standing crops and their loss with the old band

- **Where** · `origins/sim/bands.py:185–217,314–322`, compared with the standing crop transfers at lines 124–129, 158–162 and 267–271.
- **What is wrong** · The small-band merge moves people, goods and stores, but leaves standing crops and the new crop loss on the band it ends. The ended band's standing crop can no longer be harvested. The end-band path accounts for spoiled stores and does nothing with these crop rows.
- **Why it matters** · The outcome differs from the other ways of joining an existing band. The receiver gets the people but cannot harvest or explain the crop they had grown. The food invariant excludes standing crops before harvest, so it cannot detect this disappearance.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **2**, let a **9-person** remnant with **40** standing crop, **16** accumulated crop loss and **20** stored food join a larger band through `bands.fission_and_merge`. The receiver gets **20** stored food and **zero** of either crop row. The retired rows retain **40** and **16**. Ordinary fission, neighbouring-group migration and group consolidation each make the intended paired transfer.

### 3. A subsequent sowing can reassign the previous harvest's entire loss to another cell

- **Where** · `origins/sim/land.py:368–380,424–453`.
- **What is wrong** · One `land_crop_cell` describes both the past harvest's apportioned loss and the in-progress loss accumulator. Any positive new loss immediately overwrites that cell, before rollover. When combining losses from different places, `move_crop_loss` also keeps the receiving band's cell whenever it is nonnegative, even if it has no remaining loss of its own.
- **Why it matters** · The event can attach the amount to the wrong depletion history or omit a genuine source. A seasonal move can cause this without any transfer of people between bands. Checking the old source's current flags can also hide a historical loss after the cell recovers.
- **How sure you are** · Certain.
- **How to see it** · Give a band **40** crop loss at harvest from cell **2**, then take **1** additional crop loss on cell **778** in the next quarter. Mark distinct soil events on both cells. With a **20**-unit shortfall and no wild loss, `land_hunger` reports **10** crop loss per season from the previous harvest and cites the event at **778** only.

### 4. The hunger event includes losses for which it supplies no cause link

- **Where** · `origins/sim/land.py:365–405` and `local/scripts/knockout_land.py:59–64`.
- **What is wrong** · One eligible cause link is enough to create the event. The note, structured amounts and capped percentage then use all recorded losses, including a pool from which `felt` returned no link.
- **Why it matters** · Readers cannot tell how much of the reported exposure is tied to the listed events. The same amount affects the role assigned to each food pool in the trial. Exposure can legitimately include an unflagged loss if the record identifies it as such.
- **How sure you are** · Certain.
- **How to see it** · Give a band a **10**-unit shortfall, **5** wild loss and **6** crop loss. Give it a soil link at the crop source and no eligible wild link. The event reports **100% at most** with data for both pools. Its only event reference supports the crop pool, which contributes **60%** under this accounting convention.

### 5. The event sample misses band-seasons with exposure and no logged death

- **Where** · `origins/sim/demography.py:64–73`, `origins/sim/groups.py:245–263`, `origins/sim/foraging.py:199–210` and `local/scripts/knockout_land.py:51–64`.
- **What is wrong** · The accounts are recorded for bands that eat, but `land_hunger` is generated only through death hooks. Grouped deaths require more than the group-event threshold, and the individual path also includes deaths of people with condition below 0.5 whose recorded cause can be something other than hunger.
- **Why it matters** · The build describes one event for each band with shortfall and land loss. The reported event count, food-pool mix and median instead describe a selected sample of mortality-triggered band-seasons with at least one eligible land link. The individual exposure numerator and the grouped death total also cover different things.
- **How sure you are** · Certain.
- **How to see it** · A band can have a positive shortfall and a positive linked wild loss in `forage_and_eat` for a season with no deaths. There is no call to create its event. A grouped loss below the threshold likewise increments `group_hunger_deaths` without reaching the hook.

## Checked and sound

- **Review 022 regressions.** The mixed crop case respects the fallow cap in the live harvest. The ordinary-only wild case restores **4.64** food units. Empty crop-loss years replace the previous estimate. All three explicit standing-crop transfers pair the crop with its loss amounts. The realised farming comparison adds only the lost crop return on the same moving-average terms. Hunger deaths can now traverse a single shared event to multiple sources. Coal practice fails the wood-work test, and the scalar and vector prerequisites agree on the continuation threshold in the tested cases. Fuel-only clearing sets the start year.
- **Wild gain.** With zero added stock the two harvest passes give exactly zero deltas, including zero-effort and negligible-stock cases. Ordinary shares use effort and broad shares use effort times access, the same weights as the live harvest. In a two-band check with equal effort and gear access only in the first band, the cell gains **4.6362** ordinary food and loses **0.6604** broad food. The net band gains are **1.6577** and **2.3181**, summing to the net cell gain. This is a current-season harvest comparison at fixed effort and starting stock. Stores, gifts and the final allocation to eaters are outside that comparison.
- **Cache and replay.** Repeated same-tick calls reuse a single event ID in memory, including when two death paths ask for it. Ordinary saves occur between completed ticks, after `engine.step` advances `w.t`. A mid-year round trip and **16** further seasons matched digest, complete events and food, people and goods invariants. The cache itself is transient. An explicit save and retry of the same already-handled tick creates a duplicate ID on reload. That case is outside the normal tick-boundary save path.
- **Arrays and older saves.** `farm_rr_lost`, `land_crop_cell` and `tech_prev_wood` round-tripped with non-default values and are covered by the digest. Growth beyond band 64 preserved prior rows and daughter wood history. A save with all three new fields removed restored zero observed crop-yield loss, an unset crop source and wood history derived from old practice. That last fallback preserves the legacy rule, including its optimistic treatment of coal smelters, until the first new practice mark.
- **Other food paths.** Gifts, tribute and raids move edible stores or available food without the crop-loss estimate. Partners and captives can also change bands. Under the approved exposure interpretation the estimate describes a producer's missing harvest, so those paths need no automatic transfer proportional to all food or people moved. A claim about food available to a particular recipient would require a separate storage and transfer comparison.

## Trial and interpretation

- The matched 300-year endpoints are **513,874** with land off and **324,815** with land on, a **36.8%** difference for this checkpoint and configuration. The prior implementation has different crop room, so compare matched arms from the same version. The checkpoint is external and I did not rerun the reported histories.
- The **7,439** events and median **43%** are event-weighted exposure statistics with the selection and source limitations above. The capped ratio compares estimated gross lost production with a seasonal post-sharing deficit. In particular, an annual crop loss divided by four is a budget convention. It can be above or below the food that would have been available in a particular season. The phrase “at most” reflects capping the reported ratio at 100%, and supplies no independently established upper bound on attributable shortfall.
- The **756 of 3,815** figure is **19.8% of individual hunger deaths in the trial with a land-hunger link**. The reported zero crop-only events applies to that event sample. It does not exclude crop-only exposure among all bands that went short. The **20 of 20** move checks verify reference resolution.

## Validation

**42 focused tests passed** in 127 seconds, with one AnyIO pytest-plugin deprecation warning. These cover all land tests, review 019's trade regressions and the existing exact-replay regression. The source files parse with Python 3.10 grammar. Additional reproductions and the replay are under ignored `reviews/scratch/`. No full suite or gate-length run was started.
