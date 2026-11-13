# Review 008: technology network, stages 1–4

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** `main` at `069a9c9`: all of `origins/sim/technology.py`, its engine/state/persistence/explanation hooks, `TECH_*` parameters and `tests/test_m4.py`, against M4 specification sections 3.1–3.4 and the technology build notes. The design and M3 background remain as reviewed in 005–007. Effects (stage 5) are outside this review. No implementation files changed; no gate-length run started.

Four reproduced findings follow. The save/replay and large-world timing checks passed; the passing suite does not cover most of the new invention/keeping/spreading behaviour.

## Findings

### 1. Population consolidation can erase technology without a loss event

- **Where:** `origins/sim/technology.py`, per-band `tech` state and `ensure`; `origins/sim/bands.py`, `consolidate_groups`; `origins/sim/groups.py`, `merge_into` and `transfer`.
- **What is wrong:** Daughters inherit technology, but combining group populations leaves only the destination band's technology levels in use. The absorbed people's techniques are not transferred, and the keeping/loss system never records their disappearance.
- **Why it matters:** A representation change can destroy an invention despite preserving its practitioners. Knowledge survival then depends on band ordering and representation, rather than the stage-3 population/contact mechanism. This also contradicts the specification's requirement that migrating people carry skills; the issue occurs before any stage-5 effects are needed.
- **How sure you are:** Certain for the reproduction; frequency in full histories is unmeasured.
- **How to see it:** Start two 30-person bands, fold them with `groups.fold`, place both on the same cell, and leave both autonomous and foraging so their grouping keys agree. Give only the later band pottery level **0.8**, then call `bands.consolidate_groups`. The earlier band survives with **60 people and pottery 0**; the ended band's historical row still has 0.8. Population is conserved, and the event list contains only the original founding events: no `technique_lost` event explains the loss. The same lack of technology handling exists in the direct population-transfer helper. This needs an integration rule for combining knowledge, not a change to the numerical loss rate.

### 2. A band can adopt its own declining skill from itself

- **Where:** `origins/sim/technology.py:359–365,380–398` (`keep_and_spread`), and `_source`.
- **What is wrong:** The band's own people contribute to `skilled` using its pre-drift working level. If drift then takes it below `TECH_WORKING`, the same band becomes an adoption candidate and can be selected as its own teacher.
- **Why it matters:** Adoption can undo the intended decline without any outside contact, and the resulting event falsely says the band learned from neighbours. Adoption counts can therefore include refreshes from oneself rather than diffusion between peoples. The event is structurally resolvable, so reference validation does not catch the false explanation.
- **How sure you are:** Certain.
- **How to see it:** Exercise the keeping/spreading phase with one band, population **1**, fire-hardening level **0.5**, and no other practitioners within reach. Its keep requirement is 5, so default drift gives `0.5 + 0.02 × ln(1/5) = 0.46781124`. Supply a successful adoption draw. Instead of retaining that decline, the phase restores level **0.5** and emits `technique_adopted` with **`source` equal to the adopting band's own ID**, saying “learned ... from neighbours: 1 of the 1 people within reach practised it.” No rate or threshold was changed to obtain the result; the successful random draw was supplied explicitly.

### 3. Adoption can proceed after its prerequisite has stopped working that year

- **Where:** `origins/sim/technology.py:296–297,322,369–381`: `possible_all` is computed before keeping, then reused unchanged for adoption.
- **What is wrong:** The adoption gate uses prerequisites from before the year's skill drift, even when the resulting prerequisite level is now below the working threshold. It can finish with a newly adopted technique that fails its own prerequisite check.
- **Why it matters:** This violates the stage-4 requirement that adoption needs prerequisites. It is separate from whether an already-known technique may remain in memory after a prerequisite disappears: this is acquisition of a new dependent technique after the system has computed the prerequisite's failure.
- **How sure you are:** Certain.
- **How to see it:** Use two neighbouring 2-person bands. Both start with cordage **0.5**, and only the teacher starts with bow **0.8**, so prerequisites initially hold. During keeping, four cordage practitioners give `0.5 + 0.02 × ln(4/5) = 0.49553713`, below `TECH_WORKING=0.5`; the teacher's bow remains working. Supply a successful bow-adoption draw for the learner. It ends with **bow 0.5 and cordage 0.49553713**, and `prerequisites_met(..., bow)` is false. This was reproduced through `keep_and_spread` with the actual precomputed `_possible` matrix and default drift/threshold values.

### 4. The prerequisite helpers disagree when the working threshold is tuned

- **Where:** `origins/sim/technology.py:155–164` (`held`, `prerequisites_met`), compared with `_possible`.
- **What is wrong:** `_possible` uses `P.TECH_WORKING`; `prerequisites_met` calls `held` with its hard-coded default of **0.5**. Thus the advertised tunable threshold does not govern both checks.
- **Why it matters:** A calibration change can make diagnostics say a prerequisite is met when invention/adoption refuses it, or the reverse. This is not an observed discrepancy with the current default of 0.5.
- **How sure you are:** Certain under the stated parameter change.
- **How to see it:** Set tallies to **0.6** and `TECH_WORKING=0.7`. The scalar helper reports that writing's prerequisites are met; `_possible` reports false for the same band and technique. Restore the parameter after the check. At the current defaults, 2,700 scalar/vector comparisons across varied locations, levels, farming shares and domesticates agreed.

## Checked and sound

- **Catalogue structure and materials:** all 27 techniques form the declared dependency order. The pottery → kilns → smelting and tallies → writing chains reflect the qualitative sequences cited in the specification. Scalar/vector checks agree at default thresholds, including domesticate plus farming-share requirements, local hill/water terrain and material alternatives. The `keep` numbers are explicitly starting values; the cited qualitative literature does not establish those particular practitioner counts as facts. Species/category questions are separated below.
- **Invention formula:** the multiplication in `yearly` matches its docstring, including need floor, population exponent and difficulty factor. Comparing a uniform draw with the result implicitly saturates probabilities above 1. Its connected population sums each band's people once, including all bands on the same cell; direct sums matched the computed values.
- **Knock-out:** `TECH_POP_EXPONENT=0` removes the direct population multiplier from invention. Holding need/prerequisites/draw fixed, a fire-hardening invention decision was identical with 90 versus 90,000 connected people under exponent 0, while the same draw distinguished them under exponent 1. This is a knock-out of the invention population term, not of population's other roles in keeping, diffusion or pressures.
- **Reach:** `_reach` matched explicit two-ring sums for every technique in the checked cells, including repeated band cells. `ring2` includes the centre once, and the aggregation does not double-count a shared cell's inhabitants.
- **Keeping/loss direction:** writing at level 0.8 with 1, 60 and 120 nearby practitioners ended at **0.7181131, 0.8000000 and 0.8138630** respectively, matching the intended negative/zero/positive log drift around `keep=60`. This is a deterministic directional proxy for the Henrich mechanism, not its full stochastic teaching model. In a one-person band with starting level 0.16 (below working level, hence zero counted practitioners), writing was zeroed and one loss event emitted; another keeping call did not emit a second loss event while it remained zero.
- **Random streams:** technology uses only `w.rng['technology']`. Other generator states were unchanged by the isolated technology phase. It makes one invention and one adoption draw matrix per active yearly call, sized by living bands × techniques; event/source loops introduce no extra draws. The stream was appended to `STREAMS`.
- **Save/replay:** a world with generated inventions and populated `tech_firsts` round-tripped with identical digest, technology levels, first-event map and event contents. Continuing original and loaded worlds for 12 engine ticks produced equal digests and events. `tech_firsts` is not included in `persist.digest`, so I compared it explicitly rather than relying on the digest alone. Removing `tech` and `tech_firsts` from a save loaded zero levels and an empty map as intended. Daughter inheritance is also covered by the repository test.
- **Cause references and titles:** generated invention, adoption and loss events resolved through `explain.resolvable`, and the new titles identify techniques. Structural resolution is weaker than truthful attribution: finding 2's self-teaching event also resolves.
- **Python 3.10:** all `origins/` source parses with the 3.10 grammar; no incompatible API was found in the reviewed hooks. Runtime checks here used Python 3.12.14 and NumPy 2.3.5, not an actual 3.10 interpreter.

## Source timing and retention: answers to the request

`_source` selects a band inside the given cell's two-ring neighbourhood from the supplied `held_` mask. It chooses the first eligible living-band entry, not a distance-ranked nearest teacher. That mask is captured **after this year's inventions**, so the source need not have held the technique at the start of the year: a forced example had band 0 invent fire-hardening and band 1 adopt it from band 0 in the same yearly call. It also precedes keeping drift, so a source can subsequently weaken. This phase ordering should be explicit when interpreting the recorded chronology; the self-source error is finding 2.

An already-known technique **can remain working without its prerequisites**, indefinitely if enough counted holders are nearby. Keeping does not call `_possible` or recheck materials, terrain or farming share. The writing drift example above deliberately lacks tallies and still gains skill at 120 practitioners. The terrain/farming restrictions currently constrain acquisition, not continued retention or the count of practitioners. This directly explains the trial-4 observation in the build notes. Whether remembered knowledge and usable/practised knowledge should differ is a design question below; adopting a new technique after its prerequisite fails is the separate finding 3.

## Speed on 3,503 constructed groups

Fixture: generated planet 1, **3,503 living group-mode bands / 525,090 people**, mostly 150-person groups on distinct land cells, farming share 0.5 and domestication skills present. Figures are local medians of seven repetitions after a warm-up. The sparse/mixed runs allow actual invention/adoption; the mixed sequence generated 1,774 events across its warm-up and timed calls. These are short component measurements, not a historical gate run.

| Work | Seconds |
|---|---:|
| First yearly technology call, including cold caches | 1.195 |
| Warm `_reach` over all 27 techniques | 0.0116 |
| Warm `_needs`, including the polity loop | 0.00054 |
| Warm yearly technology, sparse initial knowledge | 0.0347 |
| Warm yearly technology, alternating groups initially knowledgeable | 0.0509 |

The annual warm cost is roughly **0.009–0.013 seconds per season** when amortized over four seasons. Neither `_reach` nor `_needs` is an obvious affordability problem on this fixture; full-history performance still depends on adoption density, event history and the rest of M4. No speed pass mark is specified, and these host timings are not a throughput guarantee.

## Design questions for Ben

- **Retention versus practice:** should a people retain remembered knowledge when it loses a prerequisite or moves away from its required terrain/materials, while ceasing to count as practitioners or receive its effect? The current implementation treats all people in a band with a working level as practitioners, regardless of those conditions. Stage 5 needs this distinction settled; immediate destruction of remembered knowledge is not the only possible rule.
- **Animal categories:** currently any domesticated animal, including pigs alone, satisfies the animal requirement for wool, draft animals and pack animals. Which species should qualify for each technique before effects are wired in? The catalogue's coarse category is not evidence that these animals are interchangeable.
- **Contact approximation:** the specification describes cultural closeness/shared borders in diffusion, while the implemented formula and this request use an unweighted two-ring population. Confirm whether that is an accepted approximation for stages 1–4 or remains to be implemented. Likewise, `TECH_FARMING` currently tests allocated farming work (`farm_share`), not the measured fraction of food, although the build notes call it food share.

These questions are kept separate from implementation findings; no alternative design was implemented.

## Validation

**54 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **383.73 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. The three technology tests check catalogue order, daughter/save basics and a missing prerequisite; they do not exercise the keeping/adoption cases above. Focused scripts, timings and outputs are under uncommitted `reviews/scratch/`. Only this response and `reviews/LOG.md` are committed.
