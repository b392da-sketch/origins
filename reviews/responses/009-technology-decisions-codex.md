# Review 009: technology fixes and Ben's decisions

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** `a441ffe` and `d67f114`, with `main` at `d67f114`; the whole rewritten technology system, population-transfer hooks, persistence, tests, Claude's response to 008, and the decisions/build description in `docs/M4_BUILD_NOTES.md`. The earlier design and milestone context remain as reviewed in 005–008. No implementation files changed; no gate-length run started.

**Result:** all four original cases from 008 now behave as intended. Four additional problems are reproduced below. Quality arithmetic, record persistence and the cultural-weighting calculation otherwise check out. Numbers and timings are tunable/local results, not established historical facts.

## Findings

### 1. Remembered but unpractised writing can create records and recover techniques

- **Where:** `origins/sim/technology.py:428–440`, `writes`, record updates and recovery eligibility.
- **What is wrong:** `writes` checks only writing's post-drift level against `TECH_WORKING`. It does not require that writing's prerequisites hold or that writing is practised, so remembered writing can still operate the archive/recovery mechanism.
- **Why it matters:** This contradicts the explicit record/recovery rule in request 009 and decision 3's distinction between memory and practice. Losing the ability to practise writing does not disable either creating new records or recovering knowledge while its remembered level stays above 0.5.
- **How sure you are:** Certain.
- **How to see it:** Give one band writing **0.8**, tallies **0**, cordage **0.8**, and a fire-hardening record **0.8** with no current fire-hardening knowledge. Run keeping/recovery with 200 people and a successful fire-recovery draw. Writing is ineligible to practise and fades to **0.795**, yet the band creates a cordage record at **0.805** and recovers fire-hardening at **0.25**, recording `technique_recovered`. The recovery target itself is possible; the missing condition is practising writing. A valid-writer positive control also records and recovers correctly.

### 2. Combining domestication skills invalidates the herder cache within the same tick

- **Where:** `origins/sim/bands.py:226–233` (`carry`), the small-band merge followed by `consolidate_groups`; `origins/sim/pastoral.py`, `is_herder`'s per-tick cache.
- **What is wrong:** `carry` now changes a recipient's domestication skills, but the herder cache assumes skills do not change during the phases that use it. Fission/merge primes that cache before the social-merge path calls `carry`, then consolidation reuses the outdated classification.
- **Why it matters:** A recipient that has become a herding population can still be keyed as a crop population, silently absorbing another crop group. This reintroduces a wrong-way-of-life consolidation through the newly approved skill-transfer rule; preserving all knowledge does not make the extra social/political combination correct.
- **How sure you are:** Certain, including a control that isolates cache invalidation.
- **How to see it:** Fold three autonomous groups on the same cell, sizes **30, 5, 30**, all farming share 1. The first and third know only grain; the small middle group knows only an animal. Set grain suitability **0.1** and animal suitability **1** there. Call `fission_and_merge`. The five-person group legitimately joins the first, bringing animal skill 3, so the recipient's true animal share is 90.9%. Its cached herder flag remains **false**, however, and consolidation also absorbs the third crop group: the survivor has **65 people**, while the event list records only the five-person social merge. In memory only, clearing the cache after `carry` leaves a **35-person herder and separate 30-person crop group**, with the same total population. No implementation file was edited for this control.

### 3. Marriage-related migration still drops carried techniques

- **Where:** `origins/sim/demography.py:175–182`, `partnerships`, outside the new `bands.carry` call sites.
- **What is wrong:** Residence after partnership changes the woman's and children's bands, or the man's band, without carrying their source band's techniques or records. It also does not emit a migration or technology-adoption event.
- **Why it matters:** This is another actual migration route, so technology transmission depends on whether movement happens through group fission, capture, social merging or marriage. Even a single migrant can carry a usable simple technique under the approved carrier formula. Partner IDs and `partner_since` record the partnership, but not the source/destination history of this band move.
- **How sure you are:** Certain.
- **How to see it:** Leave one eligible adult woman in band 0 and one eligible adult man in neighbouring band 1, unpartnered and unrelated. Give band 0 cordage **1.0**, band 1 cordage **0**; supply successful pairing/patrilocal-residence draws. `partnerships` moves the woman from band 0 to band 1, but destination cordage remains **0** and no new event is emitted. Applying the stated one-carrier rule would carry `1 × min(1/5, 1) = 0.2`, above `TECH_LOST=0.15`. The husband's-move branch and moves of dependent children have the same missing hook.

### 4. Remembering an animal domesticate is treated as having the animal available for practice

- **Where:** `origins/sim/technology.py:198–205,260–274`, animal requirements in both prerequisite helpers; `bands.carry` supplies the newly remembered domestication skill.
- **What is wrong:** The helpers check species knowledge at skill 3, but not whether that species can live on the recipient's land. After a merge transfers such knowledge, an animal-dependent technique can count as practised and improve even where the simulator gives that animal zero suitability.
- **Why it matters:** Transferring remembered domestication knowledge is reasonable and does not itself create food: farming multiplies its productivity by suitability. The technology system fails to make the corresponding memory/practice distinction, however, and counts practitioners with no represented local source of the required animal. This matters to refinement and diffusion already, before stage-5 production effects.
- **How sure you are:** Certain about the observed eligibility/refinement; likely an error in practice eligibility under decisions 3–4, rather than an error in transferring remembered knowledge. No imported livestock or wool supply is represented by the reviewed stages.
- **How to see it:** On generated planet 1, cell **2** has sheep suitability **0** and pig suitability **1**. Give a recipient pig skill 3, farming share 1 and cordage **0.8**. Merge in sheep-domestication skill 3 using `bands.carry`. Sheep food remains impossible there, but both technology checks allow wool. Give wool level **0.6** and run keeping with 200 people: it improves to **0.6020412** instead of being treated as unpractised memory. This uses the generated suitability tables, not altered terrain.

## Original fixes and quality: checked and sound

- **008's four reproductions:** same-kind consolidation preserves the donor's pottery at 0.8; the isolated one-person skill declines without self-adoption; bow is not adopted after cordage falls below working; the scalar/vector checks agree with `TECH_WORKING=0.7` and tallies 0.6. Carrier scaling does not reduce the original 30-person pottery example because pottery needs 20 carriers.
- **Crude invention:** invention now considers unknown levels only (`<=0`) and assigns `TECH_INVENT_LEVEL=0.25`, so a remembered weak technique is not overwritten by a fresh invention. Normal keeping can refine that crude level in the same annual call.
- **Refinement cap:** with no better teacher nearby and abundant practitioners, cordage rose from 0.25 by **0.005** with no specialists, and **0.010** with 250 specialists among 5,000 people. Stone building (`keep=40`) rose by **0.00176777**, matching `TECH_REFINE × sqrt(TECH_EASY_KEEP / keep) × gain`. At the craft reference share the same gain of 2 inside the logarithm halves the effective practitioner requirement.
- **Catching up:** cordage 0.25 near a practising 0.8 teacher ended at **0.2825**: capped refinement 0.005 plus `0.05 × (0.8−0.25)`. Catch-up is deliberately additional to the refinement cap, not a cap violation.
- **Learners/carriers:** contact assigns `TECH_ADOPT_SHARE × teacher quality` and rejects lessons below `TECH_LOST`. Combining takes the better of existing quality and source quality scaled by `min(carriers/keep, 1)`, discarding fragments below the loss line. For writing, quality 0.9 carried by 30 of the required 60 people becomes **0.45**; three carriers do not establish it. Daughters retain their parent's levels and records as explicitly specified.
- **Other increases:** the reviewed assignments raise technology only through invention, practising/refinement/catch-up, contact adoption, carrier combination, record recovery, or daughter/state inheritance. Record recovery deliberately assigns the fixed crude invention level. There is no unrelated automatic top-up to mastery.
- **Remembered knowledge:** an initially unpractised technique loses exactly `TECH_FORGET` per year and contributes no practitioners for that technique. Writing 0.6 without tallies became **0.595**. Starting just above `TECH_LOST` then produced one `technique_lost` event with `practised=False` and a note explicitly naming missing tallies. Writing's record/recovery benefit is the exception in finding 1; the prerequisite-chain question below is separate.

## Writing, records, replay and causes

- A band with working, genuinely practised writing correctly records practised techniques and recovers a possible lost technique from a record at the crude level. Unknown techniques without a record are not recovery candidates. Finding 1 is the false-positive writer case.
- Records combine by maximum and pass to daughters. Checks survived 70 daughter creations across array growth. Carrier scaling applies to living technique levels; records pass unscaled, as the code's archive-transfer rule specifies.
- `tech_record` round-tripped exactly, and altering one record changed `persist.digest`. With generated recovery/adoption events, a saved world and its loaded copy remained equal in digest and event contents after 12 more seasonal ticks. Deleting the record array from a save loaded an all-zero archive, as intended. No new technology schema/API incompatibility was found; all `origins/` source parses with the Python 3.10 grammar. Runtime checks used Python 3.12.14 and NumPy 2.3.5.
- Only the `technology` stream changed during the isolated technology phase. Each call draws recovery and adoption matrices; successful adoption candidates additionally draw one weighted teacher and one closeness acceptance value. Counts depend on simulation/RNG state and outcomes, not observation. A saved RNG state reproduces them, including rejected lessons.
- The generated technology adoption, loss and recovery references resolve through `explain.resolvable`, including the new recovery title. A structurally resolvable event is not proof of correct eligibility, as finding 1 shows.

## Cultural closeness: expectation is correct, with the quality condition

Let eligible teacher band `j` have `n_j` practitioners and pair closeness `c_j`; let `A` be the initial contact/adoption probability. Sampling a teacher with probability `n_j / Σn` and accepting with `c_j` gives

`P(accepted lesson) = A × Σ(n_j × c_j) / Σn`.

That is the requested practitioner-weighted closeness in expectation. A 200,000-draw check with practitioner weights **10:90** and closeness **1:0.2** gave acceptance **0.279065**, versus the expected **0.28**. The code implements those weights and the stated language-root closeness formula.

Actual adoption also requires the selected teacher's lesson to reach `TECH_LOST`. Thus the general expression includes an additional indicator for `TECH_ADOPT_SHARE × teacher_level >= TECH_LOST`; averaging closeness alone does not predict acceptance when some lessons are too crude. That extra rejection is part of decision 1's quality rule, not a failure of the sampling method.

## Population paths and event coverage

- Consolidation, the small-band social merge and direct group migration now call `bands.carry`; capture calls `technology.combine` with the captive count. The source band row is still available after its members move, so the hooks can read its knowledge. Marriage/residence migration remains uncovered (finding 3).
- A normal daughter copies knowledge/records through `technology.ensure`. Folding and unfolding retain the same band ID and arrays; the simulation's seat unfolding has an `unfold` event. Flight moves the same band and retains its arrays, with a `flight` event. Polity secession changes affiliations rather than people's band IDs and has secession/founding events.
- As noted in 007, group fission is still counted rather than individually logged. If a new daughter cannot be admitted under its parent's polity capacity, it becomes autonomous without its own transition event. Knowledge inheritance works there, but it is not correct to claim every political membership change is event-backed. This is the existing logging limitation, not a newly introduced loss of carried knowledge.

## Design question for Ben: remembered prerequisites enabling practice

**Yes, remembered knowledge still counts as a prerequisite while its quality is above `TECH_WORKING`.** This is more than retaining it in memory. With pottery absent, kiln quality **0.8** is unpractised and fades to **0.795**; nevertheless, working remembered kilns plus copper working and suitable materials allow smelting to be practised and improve (**0.8 → 0.8015811** in the checked case).

I read that as conflicting with a strict “gives no benefit” interpretation of decision 3: remembered kilns are conferring the benefit of enabling smelting. It does satisfy decision 1's literal quality-only “held well” prerequisite. Ben should clarify whether a prerequisite means sufficient remembered quality or an actually practicable prerequisite chain. I have kept this policy ambiguity separate from the definite missing writing-practice test and have not imposed a recursive rule as a code fix.

## Speed on the same 3,503-group fixture

Same constructed planet-1 fixture and seven-repetition warm medians as 008: **3,503 groups / 525,090 people**, mostly 150-person groups on separate land cells, farming share 0.5 and domestication knowledge present. The mixed sequence starts alternating groups at quality 0.8 and generated 1,711 events over its warm-up/timed calls.

| Work | Seconds |
|---|---:|
| First yearly call, including cold caches | 1.132 |
| Warm vectorised `_reach`, all techniques | 0.00427 |
| Warm `_needs` | 0.00054 |
| Warm yearly update, sparse knowledge | 0.0335 |
| Warm yearly update, mixed knowledge | 0.0395 |

These warm yearly costs amortize to **0.0084–0.0099 seconds per season**. They give no obvious speed blocker on this fixture despite the additional rules; the new `_reach` is faster than the prior measured loop. These are local component timings, not a gate-throughput guarantee or a formal performance pass mark.

## Validation

**64 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **407.15 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts, controlled comparisons and timing outputs are under uncommitted `reviews/scratch/`. Only this response and `reviews/LOG.md` are committed.
