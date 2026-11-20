# Review 036 — M4a interactions and invariants

Codex, 21 November 2026. Reviewed through `5ba79ef`. This is part 3 of the comprehensive pre-gate review.

**Gate recommendation.** Findings 1–3 should block G4a. They allow the run to combine mismatched measurements, certify invalid cause chains, or miss broken conservation state. Resolve finding 4 before claiming complete source attribution for trade. Finding 5 blocks the affected G1 replay verdict. Finding 6 is a smaller observer-state issue. The existing blockers in reviews 034 and 035 remain open at this revision.

## Ranked findings

### 1. G4 can finish a history with a probe file from another checkpoint

- **Where** — `gates/g4.py:241–273` and the equivalent world/sidecar writes in `gates/g1.py:387–413`.
- **What is wrong** — The G4 worker replaces the world archive before writing the probe sidecar. On resume it reads both and ignores the saved year in the sidecar. A stop between those writes leaves a new world and old probes. G1 uses the same two-file pattern and also lacks a pairing check.
- **Why it matters** — A resumed gate record can silently skip annual exposure, census or hazard observations and still be labelled completed. A world digest can match while the record used for the verdict has changed.
- **How sure you are** — Certain. Reproduced acceptance through the G4 worker.
- **How to see it** — Put a world at year 100 and a valid year-99 JSON sidecar under the same checkpoint stem. Resume with the completion condition met. The worker calls its result writer with the year-100 world and only the year-99 probes.

### 2. Check 11's validator accepts cycles and unknown references

- **Where** — `origins/explain.py:40–51,106–111,269–311` and `gates/g4.py:207–220`.
- **What is wrong** — A revisited reference is skipped regardless of whether it is a shared ancestor or closes a cycle. An unsupported reference becomes an “unknown reference” leaf and also passes. Shared known-good references additionally change whether a sample fits within the node budget.
- **Why it matters** — The traversal is bounded, but PASS establishes less than a complete causal chain. It can accept an unsupported edge or a circular explanation. A large otherwise valid sample can receive a different verdict depending on which earlier samples populated the cache.
- **How sure you are** — Certain. Reproduced each case with small graphs. The cycle fixture demonstrates a validator defect and does not imply cycles were found in a generated history.
- **How to see it** — Give an event itself as its cause, or call `resolvable` on `{"bogus":123}`. Both return true. With a two-node budget, a three-node chain fails alone and succeeds after the two-node ancestor chain has been cached.

### 3. The seasonal conservation checks can miss malformed population and treasury balances

- **Where** — `origins/sim/observe.py:33–61` and `origins/sim/trade.py:679–702`.
- **What is wrong** — The population check tests the integrality of grouped women only and rounds total grouped population. The goods check includes treasury in the net balance but checks negative stock only in band goods. The numeric comparisons also fail to flag non-finite balances reliably.
- **Why it matters** — The gate can certify invalid states loaded from checkpoints or produced by a defect. Aggregate conservation also misses the extinct-group food corruption in review 035 because that problem changes allocation rather than total stocks.
- **How sure you are** — Certain. Reproduced with the actual seasonal observer. No ordinary path to the negative treasury fixture was observed.
- **How to see it** — Start a season with a grouped male count of 29.75 where 30 are expected, and offset −1 treasury salt with +1 band salt. The observer records no failure. The group sum rounds to the expected population, and the negative treasury is outside the element-wise check.

### 4. A return-cargo arrival links to the receiving band as its only band cause

- **Where** — `origins/sim/traders.py:404–442` and `origins/explain.py:40–51,195–205`.
- **What is wrong** — In the return direction, `src` is the other seat, and the arrival data records it correctly. The structured cause still points only to the dispatching seat, which in this direction is also the recipient.
- **Why it matters** — The goods stay balanced, and the route's traders are a valid participant, but the chain omits the donor. A check that only follows the listed references cannot detect that omission.
- **How sure you are** — Certain. Reproduced a return delivery and validated the resulting chain.
- **How to see it** — Send A's traders to B, with salt at B only. The first arrival at A records `source=B`, but the chain links only to A and a note about A's traders.

### 5. G1's replay advances the two worlds differently if a history ends

- **Where** — `gates/g1.py:397–409` and `origins/engine.py:41–53`.
- **What is wrong** — The observed world is stepped in ten separate annual calls while its twin is stepped in one 40-season call. Each call stops at extinction, but a later call still takes one tick before it checks for extinction again. The ten-call loop also probes only the first world.
- **Why it matters** — Extinction during the replay window can look like a save divergence. A digest match on a surviving world does not establish equality of the G1 probes.
- **How sure you are** — Certain. Reproduced the unequal terminal advancement, and separately verified matched probes on a surviving history.
- **How to see it** — Run the two call patterns from the same terminal world. The ten-call branch advances nine extra ticks. For a live world, apply the same annual loop and separate copies of the probe state to both branches and compare the records as well as the worlds.

### 6. The census can change a saved array despite leaving every random stream untouched

- **Where** — `gates/g4.py:63–81`, `origins/sim/technology.py:403–408` and `origins/sim/trade.py:799–817`.
- **What is wrong** — The census reads trade need through the ordinary simulation accessor. That accessor creates or pads `trade_in` when it is missing or short.
- **Why it matters** — The gate probe can change the serialized world and its digest. The new entries are zeros and the model would allocate them on its next read, so the fixture did not show a changed simulation outcome.
- **How sure you are** — Certain. Compared the digest and all RNG states around the census.
- **How to see it** — Call the century census at year 100 on a world before its receipt array has been allocated. The digest changes and every simulation RNG state stays identical.

## Interaction audit

| Interaction | Result |
|---|---|
| Food, trade and people | Traced standing crops, harvest, spoilage, tribute, loot, gift-partner help and grouping against the seasonal accounts. In short fixtures, partner help moved the same amount out of the giver as into the recipient. Standing crops were counted once when harvested after a band stopped farming. Treasury transfer on conquest and release on dissolution conserved 20 seeded units. Return trade conserved its seeded stock. Loot transfers existing stock, and captives carry no separate goods, as Ben decided. The observer coverage gap is finding 3. |
| Land, mobility and the start of farming | Regrowth and land multipliers affect actual food availability. The farming trigger takes the larger of remembered hunger pressure and crowding against unaided land, plus the approved settled-abundance floor. Actual yields can lower later farming effort and recorded soil loss can explain abandonment. The G4 observations therefore need to distinguish tending, the first village, actual cultivation and later abandonment, as in review 034. Pastoral movement precedes seasonal work, and circumscription runs after harvest. The existing abstraction carries standing crops with the people. |
| Named epidemics and pregnancy | Ordinary births and fission precede the annual hazards phase. Named-disease, war and ordinary mortality reduce pending group pregnancies through the shared helper. Group birth caps and joint split draws passed earlier fixtures. Unfolding and extinct-group retirement remain covered by review 035. Transfers that fail to carry exposure state also remain open there. |
| Trade, technology and writing | The annual technology pass reads last year's receipts before trade clears and refills them. Imported materials and local fuel are prerequisites at practice time. An invention or lesson after the harvest cannot change that harvest. Scribe averages follow support at qualifying seats and can outlast a tier drop, as decided. The log is a sampled, post-technology and pre-trade observation. It cannot establish instantaneous loss when a polity falls or describe every within-year resupply. |
| Polities, conflict and place names | The polity pass precedes conflict. Where conquest changes ownership, place naming later in the season sees the recorded affected-band list and the current speakers. Named layers can link to the recorded conquest and donor naming. Old conquests without moved-band lists are limited to their recorded target. Review 035's missing historical event coverage in the digest applies here. |
| Cause coverage | Traced the writers for inventions, adoption, losses, recovery, cut-offs, partner formation and lapse, gifts, help, first arrivals, trade routes, tolls, land crossings and impacts, named outbreaks, herding, flight and place naming. `describe` has a generic title fallback and follows stored causes, which may be notes. Named outbreak events cite the named origin, while per-cell arrivals carry route and source-cell evidence in the separate log. A passing traversal does not demonstrate that every event category occurred or that sources were independently verified. Findings 2 and 4 and review 034's coverage limitation apply. |
| Random streams | The M3 stream list is a prefix of the current one. Technology, trade, named disease and places append their own streams. Land, traders and seasonal pastoral movement add no direct draw, and circumscription uses its polity stream. Group mortality, births and unfolding retain their existing streams. The probe uses its own seeded generator, and no simulation RNG advanced in the controlled census check. |

## Validation

- 18 focused tests passed, with 173 deselected. Short cases exercised a current world saved in fast checkpoint format plus JSON probe serialization. A matched pair replayed with identical events, digest, G4 census and G1 hazard watch, including the one-year follow-up.
- Created fresh historical saves with the actual M3-close code `77ad160` and early-M4a code `8c1b397`. Two independent loads of each on current code continued for 12 seasons with matching events and digest and no invariant failures. This checks repeated continuation on current code. Long historical saves and cross-version identity with the old simulators were outside the fixture.
- No gate-length run was started.
