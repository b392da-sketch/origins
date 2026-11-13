# Review 004: G3 run 3 report against records and code

Codex, 13 November 2026. Reviewed `main` at `1ab128b448be0715769c919ca02ede421a3c1932`. No simulation, test, gate, or design files changed. No gate-length history run.

**Conclusion:** most arithmetic reproduces, and check 5 fails exactly at its stated boundary. The herd comparison omits a consequential sample-count filter; the rank correlations mishandle ties; and the evidence supports a narrower traceability statement than “every cause chain is complete.” I would have Claude answer these findings before using this review to close M3. Whether to waive a mark remains Ben's decision.

## Records and method

Fetched `origin/gate-results` at `ea0177c0194ffe433311f6f97949d35120fedd8c`. It now contains all **70** completed histories. The requested `report_68_histories.md` and 68-history snapshot are preserved in its parent, `84f23f8`; I extracted that snapshot separately and used it for the numbers below. It contains 50 institution histories (47 farming) and 18 knockouts (17 farming). Thus the report was a real dated snapshot, rather than a description of the latest branch.

Independent scripts load JSON directly and recompute grouping, medians, ranks, durations, collapse/recovery, demographic ratios, and rates; they do not call `g3_report.report`. Scripts and outputs are under ignored `reviews/scratch/`: `review004.py`, `review004_more.py`, `review004_extra.py`, `herd_thresholds.py`, and their logs. The collapse calculation generates the five planets for seat distances but does not simulate histories. I also inspected `g3.py`, `g3_report.py`, the G2 recorder/report, the rank helper, explanation validator, relevant simulation code and fix, design/specification, build notes, prior review responses, and gate report.

## Findings

### 1. The herd comparison silently excludes small comparison groups, then calls them absent

- **Where:** `docs/M3_GATE_REPORT.md:192–195`.
- **What is wrong:** Using the stated split (herd share >0.5 versus ≤0.5), **27** histories contain both kinds, **0** contain only herding records, and **20** contain only crop records. The reported 12 mixed / 12 herding / 23 crop grouping reproduces only when each kind must have **at least 100 sampled rows**. Those last two categories therefore mean “only one kind reaches 100 observations,” not “only one kind exists.” This filter is not disclosed.
- **Why it matters:** With all nonempty comparison groups, the within-history median gap is **0.1606** (range **−0.19255 to +0.77155**, positive in **19/27**). Requiring 100 observations per kind gives exactly the reported **0.0399**, range **−0.09905 to +0.273**, positive in **7/12**. The smaller effect is a selected-subsample result. It does not establish that most of the pooled difference is between histories; medians do not provide such a decomposition. Conversely, the unrestricted comparison includes very small groups and should not automatically replace the filtered estimate as a strong inference.
- **How sure:** Certain about the arithmetic and omitted filter; the inferred decomposition is unsupported by these summaries.
- **How to see it:** For every institution/farming history, split `gini_log` on column 7 at 0.5, count each part, and subtract the two column-2 medians. Repeat with minimum counts 1 and 100. `herd_thresholds.log` records both. The pooled figures do reproduce: **38.9379%**, Gini **0.5825 versus 0.3672**.

The population label also needs qualification: `surplus.yearly` records inequality only for individual bands with at least three households, `log_row` thins those records, and `g2.finish` caps each history at 6,000 rows. These are sampled eligible band observations, not a census of all village-years, and pooling histories with per-history caps changes the weights.

### 2. “Rank correlation” assigns different ranks to equal values

- **Where:** `gates/g1_report.py::_spearman` (lines 19–24), used by `g3_report.py` checks 3, 8, 9 and the hierarchy comparison.
- **What is wrong:** `argsort(argsort(x))` assigns arbitrary distinct ranks to ties rather than the common average rank. The reported correlations therefore depend on ordering within equal values. This is especially relevant for herd shares, land scarcity, and levels of rule.
- **Why it matters:** The reported **0.32** scarcity and **0.01** herd coefficients reproduce with that helper, but independently assigning average ranks gives **0.344125** and **0.017376** respectively. Both verdicts remain the same. For log population versus depth using settlements ≥2, the old values reproduce **0.147209**, range **−0.073059 to +0.578948**; average ranks give **0.154030**, range **−0.143730 to +0.624197**. The report's numerical comparisons should use a defined, order-independent statistic.
- **How sure:** Certain.
- **How to see it:** For `x=[0,0,0,1,1,1]`, `y=[0,1,2,3,4,5]`, the helper gives **1.0**. Reverse both arrays, preserving exactly the same paired observations, and it gives **0.6** here. Average ranks give **0.878310** in both orders. `review004-extra.log` and `review004.log` contain the actual-record and synthetic calculations.

A binary predictor can validly be used with Spearman correlation if ties are handled. But per-history correlations answer a within-history association question, omit histories with no predictor variation, and do not test a between-society contrast. Here 43 histories have some recorded herd-share variation, whereas only 12 have at least 100 observations of each majority type. These are different denominators and different questions. The correlation also does not isolate herds from scarcity, location, history, or sampling differences; no causal herd effect follows from it alone.

### 3. Check 10 does not establish complete cause chains throughout a history, and the fix is post-run

- **Where:** `gates/g3.py::finish` (lines 66–83, 96–100); `origins/explain.py::resolvable`; `docs/M3_GATE_REPORT.md:206–211`.
- **What is wrong:** The validator samples up to 400 events per history and follows references only to depth 6. At that depth it accepts a node without checking the node's outgoing references. The rule-chain check inspects living members only at the final state, stops at the seat, and treats a missing/cross-polity parent as a reason to stop rather than a failure. Thus “every cause chain is complete” and an all-history tree-integrity claim exceed what these checks prove. The report does correctly label the table's 27,200 as sampled events.
- **Why it matters:** There can be unresolved deeper references or transient/broken rule chains despite passing counters. A direct reproduction with existing event IDs 0–7 and each node referring to its successor returns **True** at default depth even though the chain leads to nonexistent event 8; extending validation to depth 8 returns **False**. This demonstrates a coverage limit, not an assertion that these particular records contain such a missing event.
- **How sure:** Certain about coverage. I do not claim another broken recorded cause chain was found.
- **How to see it:** `review004_extra.py` patches only the description lookup in a scratch reproduction and calls the real `explain.resolvable`; output: `deep missing reference accepted True depth8 False`.

The new guard blocks the described self-attack and stale attacking representative. Its wording is broader than the code: it does not require the defender to retain its original side, only to differ from the attacker; other members of the start-of-year attacking list can also have changed. I have not established a new loop from these remaining stale inputs. The recorded local rerun through year 8,600 is useful evidence for the particular year-7,523 failure, but is not a completed corrected G3 history, let alone a corrected ensemble. The 41/73,602 figure is a diagnostic from one other history, not a bound on downstream effects of changing wars. The original run still has a loop and fails its implemented check. Accepting a fix plus narrower regression evidence instead of a rerun is a waiver for Ben to make explicitly.

### 4. Check 5b adds a full decade to each observed longest hold

- **Where:** `gates/g3_report.py::held`, lines 196–201; run-3 historical-duration comparison.
- **What is wrong:** A single large sample counts as ten years, and samples at years 100 and 110 count as twenty. The observed interval is zero and ten years respectively. `collapses()` instead starts at zero, so the two duration calculations disagree by one sample interval.
- **Why it matters:** The reported longest-hold median **230** is a sample-bin estimate; the observed endpoint-span median is **220**, with range **80–910**, rather than **90–920**. Summing sampled polity-years as ten per row is an integration approximation, but should not be presented as an observed continuous duration. Neither statistic is the same as the historical mean lifespan of an empire; taking each history's longest hold further selects extremes.
- **How sure:** Certain about the arithmetic; the appropriate estimator/comparison is a measurement choice.
- **How to see it:** Run `held`'s recurrence on one row or two adjacent rows, or subtract ten from each positive longest hold in `review004.log`. This does not change the knockout comparison, whose sampled holds are all zero.

### 5. Three of the seven no-state histories were not observed for 6,000 farming years

- **Where:** `docs/M3_GATE_REPORT.md`, run-3 “Farming to first state” comparison.
- **What is wrong:** “No state within 6,000 years in 7” includes planet 3 seed 5, observed for **1,488** post-village years; planet 4 seed 3, **2,423**; and planet 4 seed 6, **4,022**. Only the other four no-state histories reach 6,000 post-village years.
- **Why it matters:** The cap censors three histories before the claimed endpoint. They might form states before year 6,000. The reported median 1,168 is valid for the 40 observed first states, but is not an uncensored median delay for all 47 farming histories.
- **How sure:** Certain.
- **How to see it:** For institution histories with a first village and no `state` in `polity_firsts`, subtract `first_village_year` from `completed_years`. The seven differences are 1,488, 2,423, 4,022, and four instances of 6,000.

## Checked and sound

- **Check 1's implemented G2 subset:** 50/50 survive; zero invariant failures; 5,517/5,517 sampled references; e0 **25.8049–27.9584**. Zero farming-condition violations; all 47 farming histories retain foragers and show growth and spread beyond the wild range. Adoption spread is **24,529** years, with three nonfarming histories. Birth-rate ratio median **1.21513**, density ratio **3.86460**; average-rank specialist correlation median **0.99714**. This is the subset the report names, not a fresh full G1/G2 gate: no-storage knockouts are explicitly unrun, and spread/drift are not comprehensively retested by this subset.
- **Check 2:** chiefdoms in 47/47 farming histories; states in 40/47; first-state delay **305–5,571**, median **1,168**, quartiles **660.5–2,526**. The seven remaining histories are censored without a state; the median describes the 40 that have one, not all histories' time to a state. Some capped histories do not have 6,000 post-farming years, so “no state within 6,000 years in 7” is stronger than their observation windows.
- **Check 3:** pooled rates **0.006065** within capacity and **0.161802** at overload bin 7 (load/capacity minus one ≥1.75); median per-history correlation **0.994505**. The numbers reproduce. This is an aggregate bin comparison, not a controlled causal estimate.
- **Check 4:** independent continuous-sample qualification and geographic recovery calculation reproduce **47/47**, **705/712**. The denominator excludes collapses too late to observe 1,000 years; the prose should retain that qualification.
- **Check 5:** farming-history median maxima **24 versus 6**, ranges **18–38 versus 6–8**, ratio exactly **0.25**, no knockout states. Strict `<0.25` fails. All polities ever sampled at ≥5 settlements are retained, so sampling smaller polities cannot hide a sampled knockout maximum ≥10. Ten-year sampling can miss brief peaks; the report generally acknowledges that resolution. Strong institutional effects in other measures support a discussion of waiver, not an arithmetic PASS.
- **Check 5b:** as implemented, longest holds **230 versus 0**, total sampled polity-years medians **12,190 versus 0** reproduce, subject to finding 4.
- **Checks 6–7:** independent pooled scarcity/distance rates satisfy the implemented inequalities; the report appropriately calls 6 bookkeeping. War-death fractions **5.6896–8.5231%**, median **6.8544%**, reproduce. The cost check's verdict tests the death-share window; it does not separately verify every transfer from the aggregate result JSON.
- **Check 8:** **58,289** retained qualifying empire IDs, **53,962** ended; average-rank duration/overextension correlation **−0.351582** (old helper **−0.351599**), so PASS survives tie correction. Small polities are subsampled by ID while all ever-large ones are retained: these counts describe the retained records, not necessarily every empire formed. Duration is first-to-last sampled existence of the polity, not specifically its time as a multi-language conqueror.
- **Check 9:** median of per-history Gini medians **0.3992**, range **0.2253–0.83585**. Thus the specified median-level test passes despite several extreme histories; it does not require every history to lie within the level window. The herd half still fails after tie correction.
- **Check 10:** **27,200/27,200** sampled validations; exactly one final recorded loop count, planet 2 seed 6. FAIL reproduces for the original run.
- **Checks 11–12:** the archived generated report gives polity totals **1,945–33,242** and sampled maxima **18–38**. Independent timing calculation gives **1.01297–9.92089 h**, median **2.96246 h**; the displayed **1.0–9.9**, **3.0** are correct. The 9,983–30,000-year observation range is the recorded range.
- **Latest records:** the two formerly missing knockouts now complete the set. The latest generated report retains the same verdicts and institution-history figures, but has **28,000/28,000** sampled validations and timing **1.0–10.7 h**, median **3.1 h**. A final decision should identify whether it uses the 68-history snapshot or the completed 70-history set.

## Design questions for Ben

1. Accepting check 5 “in substance,” carrying the herd condition, and accepting post-run regression evidence for check 10 are explicit gate decisions. None follows automatically from this review.
2. Should the herd question compare within-history associations, adequately represented crop/herd groups, or between-society wealth distributions? The three estimands differ. The median-history Gini level also weights histories equally, unlike the pooled row-level comparison.
3. The quoted Borgerhoff Mulder category means (**0.42 pastoralists, 0.48 agriculturalists, 0.27 horticulturalists, 0.25 foragers**) would support saying that pastoralists are not the highest category in that comparison. They do not by themselves show whether livestock has a conditional effect among otherwise comparable crop farmers. I could not independently consult the primary paper in this environment and do not certify its table, uncertainty, wealth definition, or the report's other external historical benchmarks. Comparing these literature measures to synthetic household wealth or maximum sampled polity holds needs those qualifications before treating agreement as validation.

## Validation

The existing full suite completed: **49 passed in 335.75 seconds**, Python **3.12.14**, NumPy **2.5.4**, pytest **9.2.0** (`reviews/scratch/onboarding-tests.log`). Python 3.10 was not exercised. No new repository tests or application fixes were made. The observatory served its page, initial state (90 people, paused, no error), bands, and geometry successfully; pause control returned success. The saved environment installation steps were rerun successfully. Those are environment smoke checks, not evidence that a gate passes.
