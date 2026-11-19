# Review 015: partners trade, swaps and gift totals

**Reviewer:** Codex, 15 November 2026.

**Reviewed:** pulled `main` to `dff92f0`, including the review-014 fixes and stage 4a, then fast-forwarded to `d398d07` (additional stage-4b literature notes only; implementation unchanged). Read the requested response/build notes and existing project rules under `AGENTS.md`. No implementation changes or gate-length runs.

**Result:** the original three review-014 reproductions now pass. Five additional findings follow, including one remaining receipt-history gap. Current-format replay, legacy link widening and the ordinary partner-trade path pass focused checks. The square-root allowance and event thinning are design judgements below; the knockout's size ratio is not evidence that partner trade created hubs.

## Findings

### 1. Coastal sailing partners can be counted twice

- **Where:** `origins/sim/trade.py:483–506` (`_partner_pairs`), called after `_pairs`.
- **What is wrong:** Partner insertion excludes same-cell/adjacent-land pairs but does not exclude an existing across-one-sea-cell sail pair. The same endpoints therefore receive both kind 2 and kind 3 edges.
- **Why it matters:** Working goods get two exchange proposals between the same bands, increasing their effective rate and counting two contributions to the dense-network limit. Arrival-route attribution can also favour the extra partner edge.
- **How sure you are:** Certain.
- **How to see it:** On planet 1, coastal cells **28 and 5824** share a sea neighbour but are not adjacent. Link equal-sized bands there and supply practised sail quality 1 at one end. The final pair list is **[(0,1,2), (0,1,3)]**. Starting with 100/0 fine stone, exchange transfers **10**, versus **5** through either single unboosted edge. Conservation still passes.

### 2. Working-only links throttle goods they cannot carry

- **Where:** `trade.down_the_line:535–550`, the common `cond`/`lim` calculation before the per-good kind-3 filter.
- **What is wrong:** The dense-network limiter counts partner rates for every good, then zeroes partner flows for non-working goods afterwards. Inactive edges can therefore reduce an ordinary neighbour edge's pottery, textile, shell or gold flow.
- **Why it matters:** Adding working-goods-only partnerships changes unrelated local exchange, even when none of those goods can move along the new links. This confounds the intended comparison with partner trade disabled.
- **How sure you are:** Certain.
- **How to see it:** An equal-sized giver has one ordinary neighbour and 16 non-neighbour partners. With 100/0 pottery on the neighbour edge, the ordinary transfer would be **5**. Adding the 16 kind-3 edges reduces it to **2.94117647**; the remote partners receive **zero pottery**. The limiter sums 17 rates although only one edge is active for pottery. This also reproduces with actual planet-1 pair enumeration: giver cell **12954**, neighbour **3262**, remote partner cell **829**.

### 3. Ending a band erases its unarchived gift totals

- **Where:** `trade.band_ended:150`, `_unlink_all:242–246`, `_unlink:220–225`; consolidation's `_unlink_all` call in `bands.py`.
- **What is wrong:** Movement lapses and swaps archive `gift_totals` before unlinking, but ending, small-band merging and consolidation clear the counters without preserving them in any event or durable partnership record.
- **Why it matters:** Under the new approved compression, the first event and thinned log do not preserve every later gift. Deleting the cumulative record loses unsampled quantities and breaks the intended per-partnership accounting history.
- **How sure you are:** Certain, reproduced through all three paths.
- **How to see it:** Begin with 100 shell at one endpoint and exchange gifts for two years: cumulative gifts are **9.75 out and 0.25 back**. With a test gift-log cap of 1, only the first 5-shell row remains. End or merge the endpoint: the only new event is `band_extinct` or `merge`, neither carries the totals, and both link counters become zero. Absorb the linked group by real consolidation: the counters disappear with **no event added**. The global moved ledger remains, but cannot replace the lost per-link record.

### 4. Receipts are still forgotten when there are no exchange pairs

- **Where:** `trade.down_the_line:511–517` versus receipt-history update at line 544; production in `trade.yearly`.
- **What is wrong:** The function returns before marking held goods as reached when the world has fewer than two bands or no eligible pairs. Production/other receipt routes do not independently update that memory.
- **Why it matters:** A good previously held can later be described as first reaching the band after its stock wears down. This is a remaining gap in review 014's promised “by any route” history, despite the original low-stock frontier case now passing.
- **How sure you are:** Certain.
- **How to see it:** Put two bands far enough apart that neither neighbour nor partner edges exist. Through the real yearly production path, produce **10 salt** locally at A; normal wear leaves **5**, but `goods_reached[A,salt]` remains false. Stop production and apply 20 normal yearly wear steps. Move B next to A with salt to supply: the real exchange emits a `good_arrived` event saying salt first reached A, despite its earlier local production. No fabricated empty-pair return is needed for this reproduction.

### 5. Exactly twice the supply is rejected

- **Where:** `_switch:387–389`, using strict `>` rather than the documented “at least” `PARTNER_SWITCH_GAIN` multiple.
- **What is wrong:** A candidate at exactly twice the worst partner's score cannot be selected under the stated inclusive rule.
- **Why it matters:** This is a small boundary mismatch in Ben's decision, not a claim that it explains the trial's turnover.
- **How sure you are:** Certain.
- **How to see it:** Four current partners each hold one unit of the same working good per equal population; an available candidate holds two. Force the settled band's switch draw to succeed and disable random formation. The score ratio is exactly **2**, but no swap occurs.

## Review-014 reproductions: checked

- The **101-band cell** now ends its first step at **50 / 99.5**, rather than 500/95. Variance falls **98.03 → 24.02**; further fixed-network steps converge toward the common holding. The limiter gives nonnegative per-person averaging weights, with at least half the old value retained; adding working partner edges retains that numerical bound. Finding 2 concerns counting edges inactive for a particular good.
- The two-band **0.008 salt/year, 50% wear** frontier now emits **one** first-arrival event in 20 years, rather than 18. Subsequent threshold crossings skip the arrival-source scan when no new band is reached. This removes the repeated work in that case; it does not eliminate first-wave scans or the separate no-pair gap in finding 4.
- The **[100,50,0]** line now logs the middle band's **2.5 received and 2.5 given**, matching gross pair flows.

## Other implementation checks

- Same-cell/adjacent-land partners are not added again; ordinary two-ring land partners produce one kind-3 edge. Working goods pass, and non-working goods do not traverse it. Per-good totals and nonnegativity pass. Finding 1 is the missing sea-edge case.
- A genuine four-column legacy save **without gift counters or receipt memory** widens to 16, preserving goods, existing links and timestamps. New totals start at zero as documented; held goods are marked reached. Those legacy totals represent the period after conversion, not reconstructed earlier gifts.
- Running totals accumulate both directions, survive reload and are included in the digest. With a small log cap, continued worlds match gift logs, thinning state, totals, events and digest. A normal out-of-reach lapse carries the totals; a new link resets both slots and gets its own first exchange event.
- A **24-tick full-engine replay** with goods/links matches digest, complete events, both diagnostic logs and thinning state, without food/goods failures. Sampled new event references resolve. These checks do not recover the histories erased in finding 3.
- `_switch` takes its vector draw from the **trade** stream in sorted band order. It excludes existing partners, chooses the least-supplied current partner and best eligible candidate, and updates both endpoints' free counts. Its old/new events and normal swap gift archive are in place. The exact threshold exception is finding 5.

## Allowance and swap judgement

The allowance is bounded and internally consistent as an **admission rule**: sizes **1, 30, 60, 120, 480 and 3,000** give **4, 4, 5, 8, 16 and 16** slots. A band shrinking to allowance 4 retains its existing 16 links and cannot add a seventeenth. Settled bands may still replace links while over allowance. The current degree therefore need not follow the square-root curve; past size matters.

The square root and its band-level calibration remain Claude's stated modelling choice. An ethnographic average of 16 partners **per person** does not itself establish a cap of 16 **per band**. A growing capacity permits hubs but also imposes an age/size advantage; Ben should accept that assumption explicitly and judge it with a capacity-rule sensitivity comparison. It is not an implementation defect presented as a new design mandate. The current knockout leaves this rule, gifts, help and partnership teaching active.

A single swap cannot choose the partner it is dropping: that endpoint is still in its excluded current-partner set. There is **no permanent exclusion or cooldown**, and a later change of supply can justify returning. Reformation can even occur in the **same annual pass**: I forced A to drop B for a richer partner; a third full band then dropped A, opening a slot; normal formation re-created A–B later that pass. Both lapse and formation were recorded. Thus a successful trade-up is not a guarantee that the dropped edge stays absent; this can contribute to event turnover without being a violation of an approved no-return rule.

## Gift records and event volume

Ben's new totals/first-event/thinned-log plan supersedes the earlier yearly-event requirement. It preserves quantities by endpoint and good for an active link, and preserves completed-link aggregates **when the archive is actually written**. It intentionally does not preserve every annual date/quantity after thinning. Finding 3 prevents it from meeting even that aggregate guarantee for all ended partnerships.

I would not thin formation/lapse events indiscriminately: they carry identities, reasons, link lifetimes and now the gift archive. A fifth of events being formations is not by itself evidence that the records are unnecessary. Keep aggregate counts separately for reporting; first assess the demonstrated same-pass reformation and fix the archival gaps. If storage still needs compression, a durable compact lifecycle record must preserve those fields before narrative events can be sampled. This is a design recommendation, not an implemented change.

## Why a size difference can exist in the knockout

Two concrete effects can produce a large/small contrast without the new partner trade or swaps:

1. **Pooling different distances.** “Beyond 5 cells” combines a very steep gradient. In the reported knockout table, fine stone per person at 6 versus 8 cells is **0.00074 / 0.00014 = 5.29**. A difference in the two size cohorts' distance distributions can therefore create a ratio near the reported one without any within-distance size effect. The aggregate table does not show whether this happened.
2. **Size changes retention/dilution in ordinary exchange.** In matched seven-band star controls, give the centre one unit per person and six 30-person neighbours none, with no transport bonuses, partner links or production. Compare centre populations 30 and 300; apply the same ordinary exchange and 20% wear for 60 years. The larger centre retains **4.3752 times** the smaller centre's goods per person. Dividing out common wear gives approximately **0.625 versus 1/7**: the larger carrier dilutes its initial stock among fewer surrounding people relative to its own population. This is an ordinary size-weighted exchange effect, not a partner-created hub.

These demonstrate available explanations, not the attribution of the private 1,200-year result. Resolve that result with size cohorts matched at exact source distance and transport/exposure, and their movement/stock histories. Larger allowance also remains enabled in the knockout, affecting other partnership benefits. The corrected build-note conclusion—“hubs form” is not shown—is justified; neither 5× nor 7× isolates the new mechanism.

## Validation

**112 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **849.62 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts/output are under uncommitted `reviews/scratch/015*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
