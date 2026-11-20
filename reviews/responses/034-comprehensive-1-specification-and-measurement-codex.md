# Review 034 — M4a specification and gate measurements

Codex, 21 November 2026. Reviewed M4a from the M3 close through `1638523`. This is part 1 of the comprehensive review. Ben approved the 6,000-year post-village horizon, the two-thirds threshold among measurable histories, and the half-median mark for check 6. The gate run itself still awaits his approval.

**Gate recommendation.** Findings 1–8 need resolution before committing the G4a histories. Several concern observations that must be collected during the run. Finding 9 blocks a claim that all required chains were checked. Finding 10 blocks using mixed-mechanism save continuations for the affected G1 comparison. The comprehensive review can continue while the gate plan is corrected.

## Ranked findings

### 1. The standard gate workflow cannot launch or resume the population knock-out

- **Where** — `gates/plan.py:43–68`, `gates/run_job.sh:13–40` and `gates/g4.py:232–249,277–295`.
- **What is wrong** — G4 has a direct `--no-pop` option and a distinct checkpoint suffix. The shared planner and runner know only the existing storage and institution arms.
- **Why it matters** — The proposed 20 knock-outs will be absent if the normal workflow is used as-is. A manual run also needs an explicit plan for continuation and publication.
- **How sure you are** — Certain. Checked the planner with the proposed shape.
- **How to see it** — Add `nopop_seeds: "1-4"` to a five-planet request. The planner emits only the 50 main runs. The job runner's case and checkpoint logic have no named branch for the new arm.

### 2. Check 10 can pass on a single qualifying year and an incomplete exposure comparison

- **Where** — `gates/g4_report.py:205–234` and `gates/g3.py:143–175`.
- **What is wrong** — One dense herding year makes the whole spell count as dense herding. The report does not compare wild-origin or small-group spell durations. It pools old-source contact rows even when none of their recipients were naive, and a missing exposure group can still allow a pass.
- **Why it matters** — Both halves can receive a pass without evidence for Ben's definition. A spell with four low-population years and one dense herding year counts as 100% dense-herding persistence.
- **How sure you are** — Certain. Reproduced through the report.
- **How to see it** — Supply that five-year spell, one qualifying contact with deaths among naive recipients, another with no naive recipients, and no long-ago recipients. The report passes with persistence at 100% and the long-ago rate printed as `nan`. The joint yearly rows, disease host and arrivals already support a more faithful calculation. Spells running at the endpoint need to be identified as incomplete.

### 3. Check 9 can pass without a yield or hunting comparison

- **Where** — `gates/g4.py:49–61,194–205` and `gates/g4_report.py:184–203`.
- **What is wrong** — The record has endpoint soil and game stocks but no yields or hunting pressure. The yearly probe counts the first village per cell and treats any positive irrigation skill as irrigation. The report omits game, accepts one of salt and fertility as sufficient, and counts `land_move` without `land_abandoned`.
- **Why it matters** — The proposal is sound as a description of associations only if actual exposure and outcomes are measured. A fall in soil fertility across currently occupied cells alone cannot establish the approved crop, game and movement behaviours. Lost and abandoned cells are also excluded at the endpoint.
- **How sure you are** — Certain. Reproduced the incomplete pass.
- **How to see it** — Give the report five farmed cells with fertility falling as cropping years rise, no irrigated cells, constant game and one event of each counted type. Check 9 passes. Inspect the land record for the missing outcomes and the separate soil-linked abandonment event in `farming.py:371`.

### 4. Check 1 can certify unmeasured prior checks and miss the carried-forward tests

- **Where** — `gates/g4_report.py:74–102`, `gates/g3_report.py:85–114` and `gates/g2_report.py:30–44`.
- **What is wrong** — G4 treats the absence of a printed G3 failure as “all pass,” including G3 checks with no verdict. The nested check inherits G2's survival, accounting and cause-chain summary, which does not recheck all M0–M1 behaviour. G4 records no direct comparison for the carried-forward island and barren-land checks, and reports no comparison of the named-outbreak death share with the M1 result.
- **Why it matters** — The all-earlier-gates claim exceeds what the record can establish. Results from an incomplete roster can receive ordinary PASS marks.
- **How sure you are** — Certain. Exercised the G4 verdict with an unmeasured G3 table row.
- **How to see it** — Give G4 a G3 table with an applicable row marked “—” and no failures. G4 prints “all pass.” Explicitly carry forward the prior waivers and identify any legacy experiment that will be waived, rerun or recorded as unmeasured.

### 5. Checks 2, 3 and 6 use a different invention exposure from the specification

- **Where** — M4 specification §§3.2 and 4.2, `origins/sim/technology.py:603–618`, `gates/g4.py:63–81` and `gates/g4_report.py:36–52,103–113,150–155`.
- **What is wrong** — Invention uses all people within two rings. The specification calls for skilled people weighted by contact and says trade raises this reach. The report correlates skilled reach with raw inventions. Its need column is the maximum pressure across all kinds of need, even for techniques already known or unavailable. Partial centuries and bands that disappear mid-century count as full observations.
- **Why it matters** — The report can confuse opportunity, survival and population with the mechanism. The approved half-median comparison uses 20 knock-outs and all 50 main runs, though only 20 main runs have matched knock-outs. Taken alone it can pass when correlation rises if the main median is negative. In that case check 2 already fails.
- **How sure you are** — Certain from the calculations.
- **How to see it** — Add a distant trade link or replace unskilled adults with specialists while keeping local headcount fixed. The population multiplier is unchanged. A main median of −0.20 and a knock-out median of −0.15 satisfy the code. Show coverage and paired changes as a robustness check alongside the approved comparison.

### 6. Checks 4 and 5 can reach the wrong conclusion about diffusion and loss

- **Where** — `gates/g4.py:126–166`, `gates/g4_report.py:55–71,115–148` and `gates/g1_report.py:22–40`.
- **What is wrong** — Any ancestral invention classifies the present holding as own, even after loss and reacquisition. First-adoption distance is an overland path from one first invention, with no observed transmission origin or intervening trade, sea or migration links. Check 5 ranks empty bins with real values and uses current reach and holdings as a substitute for a drop after isolation.
- **Why it matters** — The provenance and distance tests do not measure actual acquisition and contact. Check 5 can pass with the observed loss gradient in the opposite direction.
- **How sure you are** — Certain. Reproduced both the provenance and loss examples.
- **How to see it** — A band invents pottery, loses it, then adopts it through trade. The export says zero of its one technique came from others. For check 5, give 16 observations low reach and no losses, four high reach and all the losses, and increasing toolkit counts. The loss bins are `[nan, nan, nan, 0, 1]` and yield Spearman −0.50. The check's conditions pass.

### 7. Check 7 can pass without the bad-year comparison

- **Where** — `gates/g4.py:47–48,167–193`, `gates/g4_report.py:157–177` and `origins/sim/trade.py:461–497`.
- **What is wrong** — The report reads only fine stone although the plan names salt and shell too. It excludes years with zero recorded help, compares aggregate transfers with a last-season shortfall share across all bands, and allows the fine-stone half alone to pass.
- **Why it matters** — The eligible population is bands with partners and a bad year. The current variables can move with population or with help already received. They cannot show that trade or partner help rises with need among eligible bands.
- **How sure you are** — Certain. Reproduced the pass.
- **How to see it** — Supply declining fine stone, increasing salt and shell, and no partner help. The report passes and prints “0 of 0” for help. Preserve zero-transfer years and a compatible measure of need before transfers if using gifts as the comparison.

### 8. The proposal drops previously agreed trade comparisons and cannot report writing against tenure yet

- **Where** — Build notes, trade decisions and follow-ups on 15–16 November, `docs/G4A_GATE_PLAN.md` histories table, `gates/g3.py:48–62,124–132` and `gates/g4_report.py:262–286`.
- **What is wrong** — The plan has only the main and population arms. It does not schedule the agreed curation knock-out or the dependence comparison in metal-working histories, and gives no disposition for the fixed-four partner comparison or the prestige knock-out. The writing and polity histories are now retained, but the report only counts histories with any sampled active writing.
- **Why it matters** — The gate would leave named experiments unevaluated and give Ben no comparison of active writing with tier-2 and tier-3 tenure.
- **How sure you are** — Certain for the current plan and report.
- **How to see it** — Read the arms table and search the report for uses of `writing_log` and `polity_log` in its writing output. The former is used as a boolean per history and the latter is not joined to it. Ben can decide which previously agreed comparisons are needed before the gate or deferred.

### 9. Check 11 can pass with entire categories absent

- **Where** — `gates/g4.py:207–220`, `gates/g4_report.py:236–245` and `origins/sim/trade.py:370–377`.
- **What is wrong** — The verdict requires any category and all its sampled chains to resolve. It does not show required categories that were never observed. “Trade” samples route openings and first arrivals, leaving out gift exchanges or other exchanges recorded separately.
- **Why it matters** — The result can be read as coverage of every required kind of causal record.
- **How sure you are** — Certain. Reproduced through the report.
- **How to see it** — An otherwise empty traceability fixture with one resolved invention gets PASS. Report coverage and absent categories independently of whether the sampled references resolved.

### 10. Reloading a modern M1 off-arm continuation can erase valid counters

- **Where** — `origins/persist.py:249–253`.
- **What is wrong** — The review-031 quarantine is triggered by any nonempty disease catalogue with `ob_*` counters. A current save can have both when legacy outbreaks have been switched on after named outbreaks. A later load can overwrite earlier quarantined totals too.
- **Why it matters** — G1 loses valid M1 exposure data on each reload in that continuation, and its replay digest changes.
- **How sure you are** — Certain. Reproduced in a current-format fixture.
- **How to see it** — Save a disease catalogue with named diseases switched off, `ob_new_starts=2` and `unattributed_ob_new_starts=17`. On load the valid counter disappears and the unattributed one becomes 2. The original old-save fixture still behaves as intended.

## Specification and recorded decisions

| Item | Assessment against the current build |
|---|---|
| §2.1 States and circumscription | Flight under pressure and constrained destination choice are implemented in `polity._flight`. Tallies and writing affect capacity. State classification still comes from hierarchy and officials, with no direct metals prerequisite or capacity term. Treat the knowledge brake as a soft, partly implemented mechanism in the lag comparison. |
| §2.2–4 Seat memory, herding, event store | The 100-year seat protection, seasonal pastoralism and the disk-backed event store are present. The November 13–14 crop carry-over and common-pasture/private-herd decisions are reflected in farming and surplus. G3's herd inequality comparison is inherited by G4. It still needs evidence across histories. |
| §2.5–6 Carry-forward and working arrangements | Check 1 lacks the direct measurements in finding 4. Local runner handover and independent review are documented and in use. Whole-chain traversal replaced the old six-step cap. |
| §3.1 Nodes and effects | The agreed catalogue, material/animal/terrain prerequisites, working quality, gradual effects and settled-building conditions are present. The amended farming trigger combines hunger, crowding and the settlement floor, and broad-spectrum gear is back on, as decided. Fortification's military effect is M4b. Some named effects are proxies or limited to trade; avoid treating all listed technologies as distinct effects on production or rule. |
| §3.2 Invention | Annual prerequisite and need-dependent invention, difficulty, stimulus and the no-population switch are present. The connected population input, and the recorder's need and outcome comparisons, diverge as in finding 5. |
| §3.3 Keeping and loss | The agreed skill quality, practice required down the chain, specialist teaching, remembered-but-inactive skills and recovery from records are present. The smooth annual skill update represents the documented implementation of the learning model. Check 5 does not yet test losses around isolation or collapse. |
| §3.4 Contact, trade, migration, capture | All routes are implemented, with cultural closeness and transfer of domestication skill as decided. Writing's exception for daughters and partial movement follows the later scribes decision. The path and current provenance measurements need finding 6 resolved. |
| §4.1 Goods and ledger | The nine-good ledger is live. Food moves through the food account, herds through the surplus system; neither is a general goods-ledger commodity. Flint and shell stand in for broader proposed categories. No money. Cloth and pottery remain trade goods. |
| §4.2 Exchange at three scales | Gift partnerships, help in need, working goods, down-the-line links, hub switching and specialist traders are present. The later decisions endorse the hub and toll design, directional roads, payment and levy in goods, and thinning repeated exchange records. The agreed trade-volume increase in invention reach is absent. |
| §4.3 Trade effects | Imported material access and cut-off, metal tool effects, salt benefits, prestige capacity, craft time, route teaching and trade need from receipts are implemented, as is curation. Trade as a war motive is explicitly deferred to M4b. See findings 7–8 for the evidence. |
| §5 Land | Slow and fast game, forests and fuel, slope erosion, crop use, fallow, manuring, salting and recovery are implemented. The latest fuel thresholds, crop-room/yield changes and hunger exposure accounting supersede the earlier binary famine claim. The report should preserve Ben's contribution/exposure wording and test the physical outcomes in finding 3. |
| §6 Named diseases | Named origin, reservoir, immunity, response custom and the later persistence and first-contact definitions are implemented. Flight and isolation are current scope; blame is M4b. Herd and wild origins follow the later decision that emergence and persistence differ. Check 10 has the required basic rows but the reducer needs finding 2 resolved. Compare the share of deaths under the current mechanism explicitly if evaluating the carried-forward M1 question. |
| §7 Writing and place names | Writing follows tallies and administration, raises capacity, has retained records, stimulus, tallies with keepers and the tier-2+ scribal baseline. Regions and the observatory place view are built. New and inherited forms, conquest layers and their cited source events are present. Chronicles are M4b. The report needs the promised tenure comparison, regardless of whether writing proves rare. |

## Gate coverage by check

| Check | Can this record support the intended judgement? |
|---|---|
| 1 | Partial. Inherited verdicts and applicable legacy evidence differ. See finding 4. |
| 2 | It can calculate the advertised census association. Findings 5 and 6 explain why it is not yet a clean measurement. |
| 3 | Descriptive only. Use need for eligible inventions and show viable opportunity counts, rather than treating the maximum unrelated pressure as the cause. |
| 4 | Proxy measurements only. See finding 6. |
| 5 | No reliable isolation result from endpoint reach and current toolkit counts. See finding 6. |
| 6 | Mechanism toggle is available locally. Dispatch and the inputs to the approved half-median rule need findings 1 and 5 resolved. |
| 7 | Endpoint distance bins and help totals exist. The computed pass omits required evidence. See finding 7. |
| 8 | Invariant totals support the check for histories actually included. Require coverage of the approved roster and distinguish missing results from zero failures. |
| 9 | The proposed exposure reading is appropriate in principle. The record and verdict lack key variables. See finding 3. |
| 10 | The spell and arrival record is materially better. The verdict currently does not answer both halves. See finding 2. |
| 11 | Samples can be checked. Show coverage and limitations before using the aggregate verdict. See finding 9. |
| 12 | First invention year and cell exist. The report only counts whether a technique appeared, omitting the promised where and when variation. |
| 13 | Per-history elapsed seconds are usable as a descriptive figure. It is simulation time through completion and omits record construction, which the pipeline trial reports separately. |

The historical appendix reports order and state lag. It does not show the promised spacing between techniques, the Seshat technology-versus-scale comparison, or layers per place. Place retention uses final feature size, which can differ from size at the naming event for settlements. Report these as limits unless the necessary evidence is added.

## Checked and sound

- Review 031's same-year return resets the source spell. The G3 fixture retains paired herder and population values for every year and breaks the spell at a fresh arrival. G1's first follow-up is the next annual probe and recorded nine intervening births in the fixture. The older-counter quarantine passes its original test, with the additional modern-save case in finding 10.
- Review 033's focused cases pass. Separate conquest events link to their own affected bands, duplicate adoption in the pass is prevented, the cell endpoint uses local speech before falling back, and unnecessary stimulus stays out of causes. The G3 writer retains tier-2+ and writing-associated polity histories even when sampling smaller polities.
- Seven focused regression tests passed. Short synthetic fixtures exercised the G4 report, the gate planner and the earlier recording fixes. No gate-length run was started.

## Design questions for Ben

- Decide what minimum coverage is needed before the approved two-thirds rule is interpretable, especially when unmeasurable histories can be selective.
- Confirm numerical meanings for dense herding and persistent or short circulation. Choose them after agreeing on the actual numerators and denominators.
- Decide the disposition of the older gate experiments and the trade comparisons in findings 4 and 8 before an all-gates verdict is issued.
