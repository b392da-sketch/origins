# Review 021: the review-020 fixes and Ben's land decisions

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `1c3362a..03e3612`, including Claude's answer, the trial driver and the M4 build notes. The original review-020 cases pass as tested. The following cases remain open.

## Findings

### 1. The forest that supplies smelting fuel can go untouched

- **Where** · `origins/sim/land.py:159–187,240–248` and `origins/sim/trade.py:199–211`.
- **What is wrong** · Production can draw on living wood anywhere within two rings, but `note_fuel` books every unit at the production site. Clearance only occurs where that site has a forest biome. The same booking also charges local forest for tin and iron made where coal gives full fuel.
- **Why it matters** · The output limit responds to forest cover but wood use need never reduce the supplying forest. Several producers can keep drawing on the same unchanged stock. Goods balance because production is booked at the amount actually made. The resource feedback is where the source is lost.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **5020**, enable smelting at 0.9 and zero forest except at cell **5039**, within reach. The trade phase produces **0.4275** tin, books **2.565** fuel-using goods at 5020 and **zero** at 5039. Cell 5020 has no natural forest cover. After `land.yearly`, 5039 still has its full cover.

### 2. A band can abandon farming permanently because its yield estimate cannot refresh

- **Where** · `origins/sim/farming.py:299–317,333–338,396–405,435–445`.
- **What is wrong** · The old realised return continues to cap the yearly work choice even after farm share reaches zero or the band moves to another cell. At zero share, the harvest path never updates the estimate.
- **Why it matters** · A band that left tired soil can reject fresh land indefinitely despite retaining domesticated crops and facing the same foraging returns. This changes recovery, adoption and population outcomes in the real-yields arm.
- **How sure you are** · Certain.
- **How to see it** · At fertile planet-1 cell **2**, give a band a domesticated crop, foraging return 1, old realised farm return **0.05** and farm share **0.011**. `farming.yearly` sets the share to zero. Repeated harvest and choice passes leave it there. Replacing the old estimate with the unobserved value makes the same band put **0.15** of its work into farming at the next choice.

### 3. Unused pasture can make crop land look idle

- **Where** · `origins/sim/farming.py:412–432`, especially the shared `caps` denominator for worked and wanted crop shares.
- **What is wrong** · The share of cropland worked is divided by the maximum of crop suitability and animal suitability. When the band knows no usable animal, `best_all` still returns the first animal index, and its theoretical pasture capacity can override the real crop capacity.
- **Why it matters** · It depresses measured crop use and keeps more land in fallow the following year. This is the same underlying estimate used to set forest clearance and soil recovery.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **778**, give a band only domesticated grain. Grain suitability is **0.3491** and the unpractised goat entry has suitability **0.6046**. With effort to grow half the cell's nominal grain capacity, the live path records worked and wanted shares of **0.2887**. The next fallow is **0.7113**, instead of 0.5 against that grain capacity.

### 4. An irrigator who worked no fields can salt another band's crops

- **Where** · `origins/sim/farming.py:410–434` and `origins/sim/land.py:136–156,250–260`.
- **What is wrong** · The bookkeeping takes the best irrigation quality among bands with positive farm share and multiplies it by all crop use on the cell. It accepts the irrigation value even when that band supplied zero effort. The manure maximum also applies across the whole cell, independently of how much land the claiming band worked.
- **Why it matters** · Salt can rise without a unit of irrigated cropping, and a small mixed farm can shelter the rest of a cell from soil exhaustion. This weakens the connection between G4a's soil and salting outcomes and the practices credited with them.
- **How sure you are** · Certain.
- **How to see it** · At dry river cell **778**, use two crop-capable bands with positive farm share. Put all effort into the unirrigated band, enough to work 90% of the cell, and give the other band irrigation 0.9 and zero effort. Use stays **0.9**, yet salt increases by **0.000549** in a year. With the unused irrigation removed, the salt increment is zero.

### 5. The movement test can attribute departures to land loss when the band would leave anyway

- **Where** · `origins/sim/foraging.py:34–59,64–93` and `origins/sim/climate.py:75–83`.
- **What is wrong** · The code divides actual stock by the current wild factor. That scales the stock left from earlier seasons as well as current regrowth. It also adds a soil or salt link for any positive farm share even when the stock comparison alone determines the move.
- **Why it matters** · A resolvable `land_move` can give a false causal explanation. Its count cannot stand as the number of land-caused migrations for check 9.
- **How sure you are** · Certain.
- **How to see it** · Hold pre-regrowth stock and the natural target each at **100 per person**, with wild factor **0.8**. The live regrowth rule gives **89**. Restoring the natural target for that season gives **100**, but the movement test imputes **111.25**. At **121.47** next door and the **1.15** threshold, the band would still leave in the natural-regrowth comparison, yet the code records a land-driven departure. Separately, a band with 10% farm share, a soil crossing and wild stocks of 100 here and 200 there gets a soil-linked move even with the wild factor at 1.

### 6. Hunger links can cite losses in a food source the band does not use

- **Where** · `origins/sim/land.py:310–326`, `origins/sim/demography.py:64–73` and `origins/sim/groups.py:249–261`.
- **What is wrong** · Positive farm share qualifies a band for the crop attribution even when it grows no crops. Wild attributions need no evidence of wild harvest. Within a food pool, `felt` assigns the same combined factor to every flagged event. When both game and forest qualify, for example, it sorts by event ID regardless of which caused more of the loss.
- **Why it matters** · The 644 linked individual hunger deaths in the trial measure exposure under a proxy. Even that exposure can be to an unused food source. A gate claim needs inspected cases where the affected food actually contributed to the shortfall, and it should distinguish individual deaths from group famine events.
- **How sure you are** · Certain.
- **How to see it** · Set a band's crop value to zero and keep its farm share positive, as for a band working only herds. Set soil fertility to 0.5 and add a soil crossing. `land.felt` reports the soil event with zero crop capability. Both hunger paths then accept it through the same rule. With two flags for the same pool, the `(factor, event_id)` sort shows that the earlier event wins the tie.

### 7. Simultaneous loss of wood and imports can leave a technique lapse unexplained

- **Where** · `origins/sim/technology.py:417–432,480–495`.
- **What is wrong** · The two attribution tests restore either historic imports or natural wood. A technique that needs both restored fails both tests.
- **Why it matters** · A band can stop making bronze without the required record of its lost trade input, even though smelting's separate loss of wood is recorded.
- **How sure you are** · Certain.
- **How to see it** · At planet-1 cell **2**, mark a band practising the bronze chain at 0.9 with imported copper and tin and local wood. Keep copper, remove tin and zero forest. `_cut_off` records **smelting/no fuel** only. Restore wood in that same fixture and bronze gets **cut off/tin**.

## Checked and sound

- **Original fixes.** The sole-crop fixture books the same worked share at fresh and worn fertility. A sole farm without soil loss or salting books its worked share before those effects. The sums use each band's normalised contribution, so they no longer depend on the first band encountered. With the existing shared allocation and positive capacities, each contribution is bounded by its labour allocation times its crop fraction times cropped share. An all-herd band supplies zero crop work, although it still competes for the shared farming allocation and counts toward farmed seasons. `land.use` and `land_need` average over those seasons, so a cell worked briefly can carry the same use as a cell worked at that intensity all year. The annual figures should be read on that basis.
- **Other regressions.** Zero wood stops the original tin case. The broad pool uses the natural seasonal maximum and is independent of the new land factors. Occupied crossings get logged after arrival if still below threshold, and recovery clears the prior event slot. Both move and death records can now link to stored events. The bronze counterfactual correctly returns copper and tin when wood remains available. Disabled years clear the accounts at harvest.
- **Food and goods ledgers.** Fallow and fertility affect quantities before they enter standing crop or the food ledger. Smelted output is scaled before stock and the production ledger are credited. No unbooked food or goods flow appeared in the focused replay. The spatial debit of wood is the separate problem in finding 1.
- **Replay.** A quarter-2 save with a finite realised return and a standing crop preserved the realised-return array, including unobserved values. It matched through 16 further seasons in digest, complete events and the food, people and goods checks. The existing replay regression also passed. Old saves receive unobserved farming returns and a default unset personal land link.
- **Search bound.** In the current catalogue the largest relevant set of goods-held inputs has two members (copper plus tin or iron), so the search checks at most three combinations for a flagged band-technique. Each of those checks reruns eligibility for every living band. Few isolated events are cheap, while widespread shortages give roughly quadratic work in band count if the number of flagged cases scales with it. No larger combinatorial search occurs with the current catalogue.
- **Stock recurrences.** At fixed 30% use and zero fuel, forest tends to **70%** of natural cover, and the best-wooded neighbour rule preserves the best supply within reach. Fertility has a positive resting term at partial use and generally settles above zero. On a fully steep, open slope it can still reach zero when use is at least **0.833**, because additive erosion exceeds the recovery available even at zero fertility. The result follows the current erosion calibration, including erosion on naturally open slopes. Salt likewise reaches its cap whenever its equilibrium exceeds 1. Slow game can die out at sustained pressure above **0.278** with no inward drift, which matches Ben's design. No second forest-style decay to zero at *every* positive level of use was found.

## Trials and event volume

- The matched land-on and land-off arms show a **35.5%** population difference after 300 years on the reported planet, for the bundle of land effects from that checkpoint. The 20,297 difference against fixed minimum fallow is a valid comparison of two fallow settings if run from that same checkpoint. The arm keeps **10%** fallow, and annual lag is one mechanism rather than an isolated explanation of the difference. Real-yield choice raised the reported endpoint by **13,047** against its disabled arm. The checkpoint is outside the repository, so I checked the comparisons and driver without rerunning the reported histories. The intermediate farmer-density arm needs its historical implementation as well as the checkpoint.
- The fuel arm labeled unlimited combines two changes. `FUEL_MIN=0` makes wood a valid material at zero cover, but `FUEL_FULL=1e-6` still gives **zero** production fuel at zero forest on a coal-free cell. It also makes the wood prerequisite pass on cells that were never wooded. That result is for those two threshold changes, so the difference of 1,025 people does not isolate the output limit.
- The driver averages bands' cell values. Multiple bands on the same cell give it multiple votes, and the farmed subset uses a farm-share threshold rather than actual cultivated area. The reported fallow and fertility means are band-weighted snapshots. The individual hunger count omits grouped deaths. The 20 link checks test whether references resolve, while checking outcomes requires the movement and food evidence in findings 5 and 6.
- **35,307 move events** alone fit comfortably in the current store. A synthetic batch of that size occupied **5.5 MB** of cold event JSON plus **0.28 MB** of offsets. Real event text and the hot in-memory window vary, and saved histories still need to stream all the rows. The more immediate performance issue is that `felt` builds the full wild-factor array twice per call, even when the cell has no flags, and `_land_move` builds it again once there are candidate links. The measured `felt` cost was about **0.88 ms/call** on the test planet. Calls also occur for moves that write no event and for hunger records, so event volume alone understates this work.

## Design questions for Ben

- **Wood lapses and recovery.** The reported maximum of 18 and 36 band-techniques lapsing more than three times merit checking whether the bands moved between wood supplies or stayed on a cell whose best woodland crossed the threshold repeatedly. Each actual transition is legitimate under the current rule. For a stable cell oscillating near 10%, a higher threshold for resuming practice could model the time needed to restore reliable supply. Apply any such hysteresis to practice itself if that is the intended behaviour, so the event log and production state agree.
- **Gate evidence for famine.** The stated attribution is useful for finding candidate cases. A qualifying case should show that a food source the band actually relied on was reduced, quantify the reduction in its food account, and trace the shortfall through available storage and transfers to hunger. A complete controlled replay is optional if the recorded contribution suffices to establish the link.

## Validation

**24 focused tests passed** in 89 seconds, covering all land tests, review 019's trade regressions and the existing exact-replay test. One AnyIO pytest-plugin deprecation warning. Custom cases and benchmark output are under ignored `reviews/scratch/`. All 35 source files parse with Python 3.10 grammar. No full suite or gate-length run was started.
