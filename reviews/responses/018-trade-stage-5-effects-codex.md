# Review 018: trade effects and review-017 fixes

**Reviewer:** Codex, 16 November 2026.

**Reviewed:** `ee14d2b` through `4315b47`, after pulling `main`; Claude's answer to 017, the requested M4 build notes and the existing design/specification context. Only review files changed. No gate-length run started. Rates remain tunable starting values.

**Result:** the three review-017 fixes check out. Five findings remain in the new effects and their explanations. Food/goods accounting and ordinary save/replay pass the focused checks; those checks do not establish that work or teaching is assigned to the right people.

## Findings

### 1. Road lessons admit teachers with no skilled practitioners

- **Where:** `origins/sim/technology.py:639`, `_trade_lessons`, versus the skilled-person checks in `keep_and_spread`.
- **What is wrong:** A road teacher needs positive, practicable knowledge, but no skilled practitioners. Ordinary contact excludes a source with zero skilled people; the new route bypasses that rule.
- **Why it matters:** Losing all knowledgeable adults does not remove the band as a road teacher. This reintroduces review 010's child-teacher problem through a different route and can keep techniques spreading after their practitioners disappear.
- **How sure you are:** Certain.
- **How to see it:** In a real founding world, make every member of band 0 ten years old, give it tallies quality 1 and no specialists, and link it to band 1 through `trade_links`. Skilled counts are **[0, 5.25, 4.75]**. Run the real `keep_and_spread` with successful random draws. Band 1 learns tallies at **0.57236898**, with an adoption event naming band 0 and route `trade`. No ordinary contact teacher qualifies for that technique.

### 2. Craft time is charged when no ordinary member can produce goods

- **Where:** `origins/sim/trade.py:756–778`, especially the constant practitioner share at line 776; its application in `foraging.forage_and_eat`.
- **What is wrong:** `craft_share` checks sources and technique quality but not the ordinary adult practitioners who actually make goods. Production uses `technology.skilled`; the food-time deduction does not use its adult eligibility or subtract specialists from that population.
- **Why it matters:** Food work can be lost to nonexistent production. A positive foraging contribution from children or older people is charged even when the production formula supplies no ordinary craftspeople. Conservation still balances because less food is harvested.
- **How sure you are:** Certain for the zero-practitioner case.
- **How to see it:** Put a founding band of ten-year-olds, with zero specialists and no techniques, on a productive coast offering salt and shell. It has **0** skilled practitioners and produces **0** goods, but `craft_share` is **0.025**. In otherwise identical one-season worlds, aggregate harvest is **10,631.421215** with the deduction and **10,670.780068** without it. Metal/salt effects are absent in this comparison.

### 3. Newly acquired import-dependent techniques can stop without a cut-off record

- **Where:** `technology.yearly:406` and `_cut_off:375–385`; subsequent invention, recovery, adoption and annual goods wear.
- **What is wrong:** The dependency mark is sampled before the year's acquisitions. A newly learned technique can practise on imports and lose access before the next annual sample, leaving `tech_import` false throughout. Inheritance can encounter the same unmarked interval.
- **Why it matters:** The required cause record is missing even though imports enabled actual practice and their depletion stopped it. Sampling existing known techniques once a year does not cover all transitions.
- **How sure you are:** Certain.
- **How to see it:** Use a 100-person band with no copper within reach and **0.505 copper**, just above the **0.5** material threshold. Run the actual `technology.yearly` with successful invention draws, then `trade.yearly`. Copper-working is learned but its dependency bit remains false. Default curated wear leaves **0.496527409 copper**. At the following annual technology call, copper-working is unpractisable, its remembered level is still positive (**0.17697605** in the reproduction), and there is **no `technique_cut_off` event**. A direct before/acquisition/after check produces the same omission.

### 4. A failed knowledge prerequisite is reported as imports running out

- **Where:** `technology._cut_off:377–384`.
- **What is wrong:** `was & known & ~with_goods` detects any loss of practicability, not specifically loss of an imported material. The event nevertheless always says that trade supplies ran out.
- **Why it matters:** Import-dependence counts and explanations attribute a technique's cessation to the wrong cause. They can report a supply failure while the imported stock is unchanged and sufficient.
- **How sure you are:** Certain.
- **How to see it:** At a cell with clay and forest but no reachable copper, give a 100-person band **2 copper** and pottery, kilns, copper-working and smelting at **0.8**. Mark dependencies. Lower only kilns below `TECH_WORKING`, leaving copper at **2**. `_cut_off` emits a smelting event saying **“the copper it had by trade ran out”**. The failed prerequisite is kilns, and imported copper remains four times the material threshold.

### 5. Scalar prerequisite explanations still reject usable imports

- **Where:** `technology.prerequisites_met:194–225`, called when explaining an unpractised technique's loss.
- **What is wrong:** `_possible` accepts materials held as goods, but the scalar check still accepts only `materials_near`. Its recursive prerequisite explanations consequently disagree with the practice calculation.
- **Why it matters:** Later forgetting events can name a missing material that the band actually holds in sufficient quantity. The helper's advertised answer to whether a technique is practicable is also false for imported materials.
- **How sure you are:** Certain.
- **How to see it:** In finding 4's world, copper-working remains practicable: `_possible(...)[copper_working]` is **True**. `prerequisites_met` for that same technique returns **`(False, ['needs copper within reach'])`**, despite the 2 copper held. Recursive smelting/bronze explanations inherit the discrepancy.

## Checked and sound

- **Return journey:** the shortlist now requires both directional paths and passes both to `_carry`. The illegal outward-road fallback is gone.
- **Toll search:** 500 small directed graphs matched an independent exhaustive state-label search, including reconstructed travel costs, different ranges and caps **0–8**. The dominance condition is valid: no more tolls and no more travel dominates both objective and remaining range. Exactness is conditional on the cap; `_leg` can still fall back to an original road paying more than eight entries. The cap bounds the alternative search, not all actual toll payments.
- **Lake surface:** `water_level` uses the existing filled surface, is assigned after random draws and is excluded from the fingerprint. The original **4991→19836** lake-exit regression now charges the surface climb.
- **Material eligibility:** the per-person threshold is inclusive, imported and local material availability are ORed, and the vector prerequisite chain carries that eligibility into dependent techniques. Holdings enable practice rather than consuming a fresh input quantity; ordinary wear remains ledgered.
- **Exception safety:** an injected exception in the second `_possible` call restores `_no_goods_materials` to false through `finally`.
- **Food effects:** metal gates copper-working's food effects; salt changes herd worker yield and the spoilage multiplier. Farming output enters `farmed`, wild output depletes stock, and spoiled food enters its existing flow. Craft effort is multiplied once before the crop/herd/forage allocation in each season; finding 2 concerns whose work is charged.
- **Road lesson order and draws:** last year's saved links are read before this year's trade replaces them. Dead endpoints are skipped; each route is processed in stored order and both directions are considered. There are two technology-stream draws per candidate, one for adoption and one for speech. Ordinary lessons run first, and already learned techniques are excluded. Finding 1 concerns teacher eligibility.
- **Replay/conservation:** a **24-season** full-engine comparison with known techniques, imported goods and mixed farming matched digests and complete events after save/load, with no food/people/goods invariant failures. Nonempty `tech_import` and `trade_links` round-tripped. Farmed food totalled **201,917.875910** in this control.

## Prestige cache

The cache is **not generally safe across membership changes within a tick**. In a direct check, three equal bands gave prestige factor **0.5**; removing two from the polity left the cached answer at **0.5**, while a fresh calculation gave **1.0**.

I did not establish a resulting error in the current engine path: annual capacity calculations begin after flight, repeated institution checks precede that polity's secessions, and later alliance/conquest normally uses stored `p.cap`. A new polity has an empty treasury. Thus I am recording the demonstrated cache limitation separately from the findings, rather than claiming a reproduced wrong annual decision. Any new capacity read after membership changes needs a fresh population calculation or invalidation.

## Design questions for Ben

**Trade need measures relative imported stock, not exchange activity.** It is finite and zero when no goods exist; the invention floor still permits trade-driven inventions. But one arbitrarily small imported holding among N otherwise empty bands scores N before clipping, hence maximum need even for a trace amount. Uniformly shrinking every stock leaves the score unchanged. Goods carried away from a source count as imports; an exporting source band scores zero for its own good, and pottery/textile exchange is excluded entirely because those goods have no geographic source. This implements the documented proxy, but its meaning and early saturation should be accepted explicitly before treating it as a measurement of “real trade.”

**A fair import-dependence experiment needs working metallurgy and a supply intervention.** Keep goods effects enabled in both arms of the same starting save. Select bands already practising bronze through imported tin, without an alternative reachable tin source, with viable copper/fuel/kilns and enough practitioners to maintain the chain. Continue supply in one arm and interrupt the relevant deliveries in the other. Record shipments, holdings per person, threshold crossing, practised versus remembered quality and the actual cause of cessation, while checking conservation and replay. Fix findings 3–5 before using cut-off events as evidence. Replicate across metallurgical histories; a small controlled case can first isolate the mechanism. The reported all-effects knock-out, with no metallurgy in either arm, cannot establish dependence on imported metal or isolate which of the seven effects caused its population difference.

## Validation

**141 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **1,058.73 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. All **34** `origins/` Python files parse with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Focused scripts and output are uncommitted under `reviews/scratch/018*`. Only this response and `reviews/LOG.md` are committed.
