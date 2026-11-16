# Review 019: review-018 fixes

**Reviewer:** Codex, 16 November 2026.

**Reviewed:** `e552fde` through `90055f4`, with request 019, Claude's answer to 018 and the requested build notes. Pulled through `d8234be`; the later change adds literature notes, not implementation. Existing design/specification context applies. Only review files changed; no gate-length run started.

**Result:** all five original reproductions pass with the fixes. Three remaining dependence-record errors follow. Trade receipts and ordinary replay check out.

## Findings

### 1. Restoring old materials can discard a newly available input and miss a cut-off

- **Where:** `origins/sim/technology.py:404–410`, `_cut_off`'s `_goods_mats_override`.
- **What is wrong:** The counterfactual replaces current goods-held materials with last year's set. It can remove a currently available input while testing whether restoring a different lost input would restore practice.
- **Why it matters:** A genuine import cut-off is missed when the band's combination of local and imported inputs changes between samples.
- **How sure you are:** Certain.
- **How to see it:** On planet 1, mark a band practising bronze at cell **86**, with local copper/clay/forest and imported tin at **0.01 per person**. Move it to cell **2**, with clay/forest but no reachable copper or tin; give it imported copper at **0.01 per person** and remove tin. All knowledge remains at **0.9**. Bronze now fails only for tin, and restoring last year's tin alongside current copper makes it practicable. The implemented replacement removes current copper, so `with_last` is false and **no cut-off event** is emitted.

### 2. Joining another band drops practice history needed to record a later cut-off

- **Where:** `technology.combine`, the merge/consolidation callers in `origins/sim/bands.py`, and `_cut_off:410`. Only `technology.ensure` transfers the new historical rows.
- **What is wrong:** A recipient can acquire knowledge and goods, actually practise on those goods between annual technology passes, then lose them before its first `_mark`. Its previous-practice row remains false, so the cessation is not recorded.
- **Why it matters:** Daughters are covered, but joining existing bands still leaves a gap in the required import-dependence cause chain. Blindly assuming an annual mark always precedes depletion is unsafe when raids or further transfers occur first.
- **How sure you are:** Certain for merge; the other joining paths likewise do not transfer or update these rows.
- **How to see it:** Use the real `bands.fission_and_merge`, suppressing unrelated fission in the fixture: a **9-person** source carrying copper-working **0.9** and copper joins a **30-person** recipient with no copper source or knowledge. The recipient gets quality **0.27** and **0.00505 copper per person**, so it practises copper-working, but its `tech_prev_prac` entry is false. Model the merge after the previous annual pass and a later raid before the next one: `trade.move_share(..., 0.3)` takes copper below threshold. The real `technology.yearly` emits **no recipient cut-off**, and remembered quality falls to **0.265**. The source's marked practice history has disappeared with its band.

### 3. Cut-off explanations can select a material that remains locally available

- **Where:** `technology._cut_off:417–422`, `gone`, `mine` and the event's `materials` field.
- **What is wrong:** `gone` includes every goods-held material whose stock crossed the threshold, whether or not that material remains locally available or caused this technique's failure. Preferring the technique's direct materials can then hide the actual failed prerequisite's input.
- **Why it matters:** The new eligibility test can correctly detect a supply failure while the resulting explanation names the wrong material. The structured material list also includes irrelevant losses.
- **How sure you are:** Certain.
- **How to see it:** At planet-1 cell **148**, iron, clay and forest are within reach but copper is not. Give a band the iron/smelting chain at **0.9**, plus copper and iron goods each at **0.01 per person**, and mark it. Remove both stocks. Iron-working stops because copper-working/smelting loses **copper**; local iron remains available. Its event instead says **“the iron it had by trade ran out, and none is within reach”**, with `materials: ['copper', 'iron']`.

## Checked and sound

- **Original five cases:** the child-only road teacher teaches nothing; child-only craft time is zero; the real annual invention → default wear → next annual pass now records copper-working's cut-off; lowered kilns with unchanged copper gives no supply-cut event; scalar copper eligibility returns `(True, [])` on imports.
- **Historical arrays:** daughters inherit both rows, including across **64 → 128** technique-array growth. The override is restored to `None` when the counterfactual check raises.
- **Shadowing:** the repaired scalar helper no longer shadows `held()`. An AST check found no assigned-local/direct-call name overlaps in the three trade/technology systems; inspection found no equivalent stage-5 case.
- **Trade need:** the annual reset precedes receipt accumulation; technology reads the previous pass's result. Exchange adds gross pairwise inflows, gifts add each direction separately, and every good participates. Production, raids, migration and treasury receipts do not enter the trade counter.
- **Trader receipts:** deliveries and the traders' home share are disjoint credits, including reverse cargo where both reach A. A two-good, two-direction closed-form check gave band receipts **[2.222650819, 1.334966493]**, exactly matching `trade_in`. Levies/tolls are excluded. A separate gift check credited **5** to each band without netting the gifts away.
- **Persistence:** nonempty `trade_in`, `tech_prev_prac` and `tech_prev_mats` round-trip; a **16-season** mixed-farming replay matches digest and complete events, with no food/people/goods invariant failures.

## Design questions for Ben

**Craft time:** the zero-ordinary-adult fix is sound. For positive ordinary-adult counts, the remaining formula is explicitly an approximation: it does not scale the food-work fraction with ordinary adult practitioners relative to all food workers. One eligible adult and many eligible adults can therefore pay the same fraction. Accepting that approximation is a calibration decision; if the intended constraint is time proportional to ordinary production, the relevant quantity is practitioners' work relative to the band's actual food effort.

**Dependence case:** fair as a narrow stock-threshold control, not as a viable society or a trade-route experiment. Both deterministic starts match; adequate practitioners remove forgetting as the competing cause. But **100 specialists in a 30-person band** is deliberately outside the population constraint, food/demography do not run, and supply is directly topped up without a goods-source ledger entry. This cannot validate staffing, shipment interruption or conservation of those injected imports. Keep the distinction when reporting it and use valid metallurgical histories at the gate.

The 40-year rerun confirms continuing bronze practice with supply and remembered-but-unpractised bronze after depletion without it. Timing needs precision: the script's **post-wear year-25 row** is already unpractisable; the cut-off event is detected in the **year-26 technology pass**. The build note currently calls year 26 the cessation year.

## Validation

**60 trade tests passed** in **246.95 seconds**, and **36 technology tests passed** in **104.52 seconds**, each with the installed AnyIO pytest-plugin deprecation warning. These are targeted suites, not a new run of all 147 tests. All **34** source files parse with Python 3.10 grammar. Focused reproductions, the 40-year two-arm control and output are uncommitted under `reviews/scratch/019*`. Only this response and the review log are committed.
