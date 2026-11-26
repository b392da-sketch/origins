# Review log

| Date | Who | File | Summary |
|---|---|---|---|
| 2026-11-12 | Claude | requests/001-m3-after-run1.md | Review the changes since G3 run 1, before G3 run 2 |
| 2026-11-12 | Ben | — | Codex reviews deferred to M4; request 001 left as an example, not to be done |
| 2026-11-12 | Ben | requests/001-m3-after-run1.md | Codex reviews brought forward: request 001 active again |
| 2026-11-12 | Codex | responses/001-m3-after-run1-codex.md | Reactivated by Ben in chat; conquest load underestimated, recovery mark omitted, collapse hold mismeasured; focused reproductions and two existing tests pass |
| 2026-11-12 | Claude | responses/001-m3-after-run1-claude.md | All 3 findings confirmed and fixed; finding 1's effect on G3 run 2 being measured |
| 2026-11-12 | Claude | requests/002-check-fixes-001.md | Check the fixes for review 001 |
| 2026-11-12 | Codex | responses/002-check-fixes-001-codex.md | Recovery and continuous-hold fixes verified; conquest still truncates attacker ancestry, producing a reproduced load underestimate |
| 2026-11-12 | Claude | responses/002-check-fixes-001-claude.md | Depth finding confirmed; fixed with depth_of in four places (three not named in the review) |
| 2026-11-12 | Claude | requests/003-check-depth-fix.md | Check the depth fix from review 002 |
| 2026-11-12 | Codex | responses/003-check-depth-fix-codex.md | Conquest matrix now agrees; daughter-of-seat depth still undercounts load, and cycle handling differs between helpers |
| 2026-11-12 | Claude | responses/003-check-depth-fix-claude.md | Seat-daughter depth fixed; loops measured (none) and now checked in every gate history |
| 2026-11-13 | Claude | requests/004-g3-run3-report.md | Check the G3 run 3 report against the result files and code |
| 2026-11-13 | Codex | responses/004-g3-run3-report-codex.md | Independently recomputed 68-history results; omitted herd filter, tied ranks, traceability limits, hold offset and censored no-state histories; 49 tests pass; fetched completed 70-history results |
| 2026-11-13 | Claude | responses/004-g3-run3-report-claude.md | All 5 findings confirmed; ties, spans fixed; report revised on all 70 histories |
| 2026-11-13 | Claude | requests/005-m4a-circumscription-pastoralism.md | Review M4a steps 1-2 |
| 2026-11-13 | Codex | responses/005-m4a-circumscription-pastoralism-codex.md | Four reproduced findings: herder consolidation loses identity/skills, pasture ignores partial farmers, dissolved seats lose memory protection, flight holds vacated land; herder/disk replay checks and 49 tests pass |
| 2026-11-13 | Claude | responses/005-m4a-circumscription-pastoralism-claude.md | All 4 findings confirmed and fixed; crop-during-moves question to Ben |
| 2026-11-13 | Ben | — | Standing crops during moves: (a) accept for now, (c) harvest only on the sowing cell later |
| 2026-11-14 | Ben | — | Herd calibration (f) set: common pasture, private herds, HERD_GROWTH 0.005 |
| 2026-11-14 | Claude | requests/006-check-fixes-005-and-herds.md | Check the fixes for review 005 and the herd settings |
| 2026-11-14 | Codex | responses/006-check-fixes-005-and-herds-codex.md | Original four reproductions fixed; fission bypass and historical herder key still lose identity/skills; herd formula and artifact Ginis verified; regression detects both key changes; 50 tests pass |
| 2026-11-14 | Claude | responses/006-check-fixes-005-and-herds-claude.md | Both findings confirmed; one grouping key by current way of life for consolidation and fission |
| 2026-11-14 | Claude | requests/007-check-fixes-006.md | Check the fixes for review 006 |
| 2026-11-14 | Codex | responses/007-check-fixes-006-codex.md | Both original cases fixed; destination classification still uses source cell and new daughters retain the old index key; membership paths audited, 5,003-group timing measured; 50 tests pass |
| 2026-11-14 | Claude | responses/007-check-fixes-006-claude.md | Both findings confirmed and fixed; herding judged at the destination; per-tick cache |
| 2026-11-14 | Claude | requests/008-technology-stages-1-4.md | Review the technology network, stages 1–4 (prerequisites, invention, keeping and losing, spreading) |
| 2026-11-14 | Codex | responses/008-technology-stages-1-4-codex.md | Technology lost in consolidation, self-adoption, stale adoption prerequisites and tunable-threshold mismatch reproduced; replay/knock-out/reach verified, 3,503-group timings measured; 54 tests pass |
| 2026-11-14 | Claude | responses/008-technology-stages-1-4-claude.md | All four findings confirmed and fixed; knowledge combined on merge and migration; teachers and prerequisites judged after drift; domestication-skill merge gap and design questions put to Ben |
| 2026-11-14 | Ben | — | Technology decisions 1–7: quality, teaching and writing, remembered-not-practised, animals per technique, cultural closeness, domestication skills combined, three trial rules confirmed |
| 2026-11-14 | Claude | requests/009-technology-decisions.md | Check the fixes for review 008 and the technology decisions as built |
| 2026-11-14 | Codex | responses/009-technology-decisions-codex.md | Original fixes verified; unpractised writing, stale herder cache, marriage transmission gap and absent-animal practice reproduced; quality, records/replay, closeness and timings checked; 64 tests pass |
| 2026-11-14 | Claude | responses/009-technology-decisions-claude.md | All four findings confirmed and fixed; Ben: prerequisites must be practised |
| 2026-11-14 | Ben | — | A prerequisite counts only when practised |
| 2026-11-14 | Ben | — | Skilled adults keep techniques; refinement slows near mastery (literature check) |
| 2026-11-14 | Claude | requests/010-technology-fixes-and-effects.md | Check the review 009 fixes, skilled practitioners, refinement near mastery, and the effects (stage 5) |
| 2026-11-14 | Codex | responses/010-technology-fixes-and-effects-codex.md | Original fixes verified; non-skilled teachers, mixed-farm output/choice mismatch, effect-cache gaps and founding-conquest capacity reproduced; conservation/replay/gate records checked; 75 tests pass |
| 2026-11-14 | Claude | responses/010-technology-fixes-and-effects-claude.md | All five findings confirmed and fixed |
| 2026-11-14 | Ben | — | Sail reach scales with quality; specialists counted once |
| 2026-11-14 | Ben | — | Building techniques need a settled people (farming half its work, or staying put 20 years) |
| 2026-11-14 | Claude | requests/011-trigger-broad-spectrum-and-packing.md | Check the review-010 fixes, settled builders, broad-spectrum food, the new farming trigger and three histories per gate job |
| 2026-11-14 | Codex | responses/011-trigger-broad-spectrum-and-packing-codex.md | Review-010 fixes verified; stale settled-builder status, packed-worker artifact loss and abundance-route misattribution reproduced; broad-pool conservation/replay pass; snapshot tending rates unverified; 85 tests pass |
| 2026-11-14 | Claude | responses/011-trigger-broad-spectrum-and-packing-claude.md | All three findings confirmed and fixed (settled check sees recent moves; packed jobs keep siblings' results; abundance route named) |
| 2026-11-15 | Ben | — | Trade decisions 1–5: imported materials count; goods with effects as listed; band-level partnerships; sharing a starting value; no money until M6 |
| 2026-11-15 | Claude | requests/012-trade-stage-1.md | Check trade stage 1 (goods and ledgers) and the review-011 fixes |
| 2026-11-15 | Codex | responses/012-trade-stage-1-codex.md | Review-011 fixes verified; marriage migrations omit goods and can record them as lost; sources, other transfer paths, ledgers and replay pass; capture ownership and free production discussed; 90 tests pass |
| 2026-11-15 | Claude | responses/012-trade-stage-1-claude.md | Marriage goods finding confirmed and fixed |
| 2026-11-15 | Ben | — | Raid loot takes goods; craft time charged from the effects stage |
| 2026-11-15 | Claude | requests/013-trade-stage-2-partnerships.md | Check gift partnerships (trade stage 2), the review-012 fix and the loot rule |
| 2026-11-15 | Codex | responses/013-trade-stage-2-partnerships-codex.md | Marriage and raid-loot behaviour verified; legacy-save goods loss, out-of-reach seasonal help, missing gift records and orphan consolidation links reproduced; budgets, reserves, teacher selection and current replay checked; 95 tests pass |
| 2026-11-15 | Claude | responses/013-trade-stage-2-partnerships-claude.md | All four findings confirmed and fixed; partner lessons recorded as route partnership |
| 2026-11-15 | Claude | requests/014-trade-stage-3-down-the-line.md | Check down-the-line exchange (trade stage 3) and the review-013 fixes |
| 2026-11-15 | Ben | — | Down-the-line exchange: neighbours, size-weighted, transport effects now, long links tested after stage 4; yearly log plus first-arrival events |
| 2026-11-15 | Codex | responses/014-trade-stage-3-down-the-line-codex.md | Review-013 fixes verified; dense-network equilibration overshoot, repeated first arrivals and net-only exchange-volume logs reproduced; geometry, caps, transport, persistence and speed checked; 101 tests pass |
| 2026-11-15 | Claude | responses/014-trade-stage-3-down-the-line-claude.md | All three findings confirmed and fixed (dense-cell limit, arrivals remembered, gross flows logged); fall-off unchanged |
| 2026-11-15 | Claude | requests/015-trade-stage-4a-partners-trade.md | Stage 4a: partners trade, hubs, gift totals; review-014 fixes |
| 2026-11-15 | Codex | responses/015-trade-stage-4a-partners-trade-codex.md | Original review-014 cases pass; duplicate sea pairs, inactive-edge throttling, lost ended-link gift totals, no-pair receipt-memory gap and inclusive-threshold mismatch reproduced; replay/legacy/swaps checked; knockout confounds examined; 112 tests pass |
| 2026-11-15 | Claude | responses/015-trade-stage-4a-partners-trade-claude.md | Five findings confirmed and fixed; Ben: allowance kept with a fixed-four comparison, 10-year re-forming wait |
| 2026-11-15 | Claude | requests/016-trade-stage-4b-traders.md | Stage 4b: traders, routes, tolls, rulers' stores; review-015 fixes |
| 2026-11-15 | Codex | responses/016-trade-stage-4b-traders-codex.md | Review-015 fixes/wait verified; seabed landing penalties, untaxed detour polities and impure route-cache keys reproduced; A*, carrying, treasury lifecycle/replay and speed checked; 124 tests pass |
| 2026-11-16 | Claude | responses/016-trade-stage-4b-traders-claude.md | Three findings confirmed and fixed; Ben: levy, each way its own road, shortlist by gravity |
| 2026-11-16 | Claude | requests/017-curation-and-review-016-fixes.md | Curation (Ben) with knock-out; review-016 fixes |
| 2026-11-16 | Codex | responses/017-curation-and-review-016-fixes-codex.md | Original review-016 cases pass; unavailable-return fallback, constrained road-search labels and lakebed exit penalties reproduced; curation bounds/ledger/replay pass; arrival-count interpretation and knockout limits examined; 130 tests pass |
| 2026-11-16 | Claude | responses/017-curation-and-review-016-fixes-claude.md | Three findings confirmed and fixed; first-arrival reading corrected (pottery diverged by chance) |
| 2026-11-16 | Claude | requests/018-trade-stage-5-effects.md | Trade stage 5: what goods change, knock-out; review-017 fixes |
| 2026-11-16 | Codex | responses/018-trade-stage-5-effects-codex.md | Review-017 fixes verified; road teachers and craft time bypass practitioner counts; missed/false import cut-offs and inconsistent material explanations reproduced; conservation/replay and toll search checked; 141 tests pass |
| 2026-11-16 | Claude | responses/018-trade-stage-5-effects-claude.md | Five findings confirmed and fixed; Ben: trade need from goods received, dependence case now |
| 2026-11-16 | Claude | requests/019-review-018-fixes.md | Short review of the review-018 fixes and Ben's two decisions, closing the trade build |
| 2026-11-16 | Codex | responses/019-review-018-fixes-codex.md | Five original cases pass; remaining cut-off gaps from replaced current inputs and joining bands, plus wrong material attribution; receipts/replay sound; 60 trade and 36 technology tests pass |
| 2026-11-19 | Claude | responses/019-review-018-fixes-claude.md | Three findings confirmed and fixed; Ben: craft time scales with the makers; land design approved |
| 2026-11-19 | Claude | requests/020-land-answers-back.md | The land answers back (game, forest, soil, fallow, salt), knock-outs; review-019 fixes |
| 2026-11-19 | Codex | responses/020-land-answers-back-codex.md | Review-019 regressions pass; crop yield mismeasures land use, fuel ignores depletion, game loss shrinks broad food, crossing and cause links fail, joint cut-offs mislabel inputs, disabled accounts accumulate; replay and 13 focused tests pass |
| 2026-11-20 | Claude | responses/020-land-answers-back-claude.md | Seven findings confirmed and fixed; Ben: fuel limits output, real yields, fallow gives way to need; two further errors of mine found in trials and fixed |
| 2026-11-20 | Claude | requests/021-review-020-fixes.md | Short review of the review-020 fixes and Ben's land decisions |
| 2026-11-20 | Codex | responses/021-review-020-fixes-codex.md | Original cases and replay pass; remote fuel debit, stale farm returns, crop accounting, land attribution and joint supply loss gaps reproduced; trial measures checked; 24 focused tests pass |
| 2026-11-20 | Claude | responses/021-review-020-fixes-claude.md | Seven findings confirmed and fixed; Ben: resume wood at 20%, food account test, farm room from usable species, fuel wood spread and small; one more error of mine found in trial |
| 2026-11-20 | Claude | requests/022-review-021-fixes.md | Short review of the review-021 fixes |
| 2026-11-20 | Codex | responses/022-review-021-fixes-codex.md | Original cases and replay pass; mixed crop room, wild-loss estimate, stale crop losses, abandonment attribution, incomplete links, wood resumption and fuel history checked; 33 focused tests pass |
| 2026-11-20 | Claude | responses/022-review-021-fixes-claude.md | Seven findings confirmed and fixed; Ben: the land is a contributing cause of hunger (amounts stated, no sufficiency claim) |
| 2026-11-20 | Claude | requests/023-review-022-fixes.md | Short review of the review-022 fixes and the contributing-cause rule |
| 2026-11-20 | Codex | responses/023-review-022-fixes-codex.md | Original regressions pass; standing crops stranded at harvest and merge, crop sources overwritten, unmatched loss totals and mortality-selected exposure reproduced; 42 focused tests and mid-year replay pass |
| 2026-11-20 | Claude | responses/023-review-022-fixes-claude.md | Five findings confirmed and fixed: harvest with nobody farming, remnant crops, crop-loss events recorded at sowing, linked amounts only, every band-season counted |
| 2026-11-20 | Claude | requests/024-review-023-fixes.md | Short review of the review-023 fixes |
| 2026-11-20 | Codex | responses/024-review-023-fixes-codex.md | Original cases pass; legacy land-off cleanup fails and crop provenance and knockout census gaps reproduced; 47 focused tests and mid-year replay pass |
| 2026-11-20 | Claude | responses/024-review-023-fixes-claude.md | Five findings confirmed and fixed: older saves, linked crop loss booked by kind and amount each season, salt below threshold links nothing, one factor test |
| 2026-11-20 | Claude | requests/025-review-024-fixes.md | Short review of the review-024 fixes |
| 2026-11-20 | Codex | responses/025-review-024-fixes-codex.md | Original cases pass; partial transfers leave example sizes unscaled and roundoff can inflate the unlinked-event tally; census parity, paired physical outcomes, 52 focused tests and replay pass |
| 2026-11-20 | Claude | responses/025-review-024-fixes-claude.md | Both findings confirmed and fixed: example loss shared on partial moves; rounding residue not counted as unlinked |
| 2026-11-20 | Claude | requests/026-review-025-fixes.md | Short review of the review-025 fixes |
| 2026-11-20 | Codex | responses/026-review-025-fixes-codex.md | Both original cases pass; repeated transfers can understate a recombined loss example; tolerance suppresses negligible real amounts; seven focused tests pass |
| 2026-11-20 | Claude | responses/026-review-025-fixes-claude.md | Finding confirmed and fixed: an example's comparison value is the loss attributed to its event, adding across seasons and rejoined parts |
| 2026-11-20 | Claude | requests/027-review-026-fix.md | Short review of the review-026 fix |
| 2026-11-20 | Codex | responses/027-review-026-fix-codex.md | Rejoined examples and repeated transfers verified; different-event selection uses band totals contrary to the build notes; eight focused tests pass |
| 2026-11-20 | Claude | responses/027-review-026-fix-claude.md | Confirmed and fixed: examples compared by their own attributed loss during the year |
| 2026-11-20 | Claude | requests/028-diseases-from-animals.md | Diseases from animals (named diseases, reservoirs, immunity by age, persistence by k, spread, deaths, responses) and the review-027 fix |
| 2026-11-20 | Codex | responses/028-diseases-from-animals-codex.md | Immunity weights, survivor accounting, grouped births, G1 exposure, cause records and knockout drift reviewed; review-027 fix, 14 focused tests and exact replay pass |
| 2026-11-20 | Claude | responses/028-diseases-from-animals-claude.md | Six findings confirmed: immunity weight, cohort deaths and immunity, pregnancies after deaths (all paths), G1 matched units, per-cell disease log fixed; knock-out recorded. Ben: check 10 marks where diseases last |
| 2026-11-20 | Claude | requests/029-review-028-fixes.md | Review of the review-028 fixes |
| 2026-11-20 | Codex | responses/029-review-028-fixes-codex.md | Found pregnancy movement and rounding gaps, older-adult immunity and population baseline errors, and limits in G1 and G3 measurements. Fifteen focused tests and exact replay passed. The herd trial off arm failed. |
| 2026-11-20 | Claude | responses/029-review-028-fixes-claude.md | Six findings confirmed and fixed: pregnancies with women, adults' immunity with the old, epidemics in sequence, G1 contact only, per-cell record for check 10 |
| 2026-11-20 | Claude | requests/030-review-029-fixes.md | Review of the review-029 fixes |
| 2026-11-20 | Codex | responses/030-review-029-fixes-codex.md | Found pregnancy capacity gaps, old-save log and exposure errors, and limits in G1 recovery, G1 counters and G3 evidence. Twenty-one focused tests and exact replay passed. |
| 2026-11-20 | Claude | responses/030-review-029-fixes-claude.md | Seven findings confirmed and fixed; Ben: first contact defined (endemic source a generation, never-met bands), one more short review then fold into the comprehensive review |
| 2026-11-20 | Claude | requests/031-review-030-fixes.md | Last short review of the disease step |
| 2026-11-20 | Codex | responses/031-review-030-fixes-codex.md | Ranked G4a check 10 blockers for source-spell age and joint herding and density. Found G1 recovery timing and checkpoint attribution gaps. Twenty-six focused tests and exact replay passed. |
| 2026-11-20 | Claude | responses/031-review-030-fixes-claude.md | Four findings fixed (spell restart, spells year by year, G1 follow-up dating, older counts set aside); to be verified in the comprehensive pre-gate review |
| 2026-11-21 | Claude | requests/032-writing-and-place-names.md | Review the writing refinements (scribes at complex chiefdoms and states, stimulus diffusion, records without a script) and place names; the last M4a build step |
| 2026-11-21 | Codex | responses/032-writing-and-place-names-codex.md | Ranked six findings on missing place outputs, naming and conquest, writing evidence and cause attribution. Seventy-seven focused tests and current and legacy replay passed. |
| 2026-11-21 | Claude | responses/032-writing-and-place-names-claude.md | All six confirmed and fixed; Ben: regions and the place view built now, conquered peoples may take conquerors' names |
| 2026-11-21 | Claude | requests/033-review-032-fixes.md | Short review of the review-032 fixes, regions, conquest renaming and the place view |
| 2026-11-21 | Codex | responses/033-review-032-fixes-codex.md | Found duplicate and ambiguous conquest naming, incomplete writing tenure, cell language and stimulus cause issues. Twenty-one focused tests and exact replay passed. |
| 2026-11-21 | Claude | responses/033-review-032-fixes-claude.md | All five confirmed and fixed (one imposed name per people and pass; conquests by their own events; G3 keeps tier-2 and writing polities; cell panel in local speech; unneeded stimulus not a cause) |
| 2026-11-21 | Claude | requests/034-037 | Comprehensive pre-gate review, four parts: specification and measurement; state and per-band arrays; interactions and invariants; performance and drift |
| 2026-11-21 | Codex | responses/034-comprehensive-1-specification-and-measurement-codex.md | Audited M4a sections 2–7 and all 13 G4a checks. Found knock-out dispatch and multiple false-pass or missing-evidence paths. Verified the focused review-031 and review-033 cases. |
| 2026-11-21 | Codex | responses/035-comprehensive-2-state-and-per-band-arrays-codex.md | Audited M4a state lifecycle and found extinct-group food corruption, replay coverage gaps, phantom trade contacts and incomplete transfers. Twenty-five focused tests passed. |
| 2026-11-21 | Codex | responses/036-comprehensive-3-interactions-and-invariants-codex.md | Audited M4a interactions, conservation, causal chains, checkpoint and RNG behaviour. Found mismatched checkpoint acceptance, validation gaps and a trade cause error. Eighteen focused tests and two historical-save continuations passed. |
| 2026-11-21 | Codex | responses/037-comprehensive-4-performance-and-drift-codex.md | Measured gate-scale phase and checkpoint costs. Ranked incomplete-history publication, disease-log and report memory, the lifetime disease ceiling, and documentation drift. |
| 2026-11-21 | Claude | responses/034-...-claude.md, 035-...-claude.md | 034: all ten confirmed and fixed, Ben's decisions built; 035: all seven confirmed and fixed |
| 2026-11-21 | Claude | responses/036-...-claude.md | All six confirmed and fixed (checkpoint pairing; cycles and unknown references; conservation coverage; return-load cause; G1 replay; census side effect) |
| 2026-11-21 | Claude | responses/037-comprehensive-4-performance-and-drift-claude.md | All four confirmed and fixed (incomplete last stage and roster check; disease log as an array; one parse in the reports; disease slots retired by Ben's decision); drift corrected; the pilot measures the heavy path |
| 2026-11-22 | Claude | requests/038-speed-from-the-pilot.md | Speed fixes from the G4a pilot (band sizes, a cache that never hit, herders, band count, closeness), same digests at planet-4 scale, 3.7× faster |
| 2026-11-22 | Codex | responses/038-speed-from-the-pilot-codex.md | Reproduced a same-tick prestige mismatch, checked size and cache boundaries, and measured which remaining costs scale with living bands and historical IDs. |
| 2026-11-22 | Claude | responses/038-speed-from-the-pilot-claude.md | All three confirmed and fixed (prestige snapshot restored; size helpers refuse absent ids; closeness scoped to one pass); next speed-ups from Codex's ranked list |
| 2026-11-22 | Codex | responses/038-speed-from-the-pilot-codex-recheck.md | Verified finding 1 is resolved on main. The compact prestige snapshot matches the pre-speed snapshot timing, current membership lookup and ordered reduction. |
| 2026-11-22 | Claude | requests/039-compact-log.md | The compact log (Ben, 22 November 2026): five kinds of happening as rows; shadow mode reproduces main bit for bit |
| 2026-11-22 | Claude | requests/040-per-band-rows.md | Disease and partner rows kept only for bands holding one (Ben, 22 November 2026); same history as main at planet-4 scale; 3.4 GB in use against 5.9 |
| 2026-11-22 | Codex | responses/039-compact-log-codex.md | Reproduced mixed-checkpoint count loss, historical names and rounded gifts changing on read, and observatory gaps. Calculated about 963 MiB raw at pilot scale with two givers per help row. |
| 2026-11-22 | Codex | responses/040-per-band-rows-codex.md | Reproduced silent state loss when old code opens sparse saves, a four-link sparse resume crash, and a legacy ended-ID guard gap. Checked retirement, lifecycle, memory growth and the scope of cross-runner replay evidence. |
| 2026-11-22 | Claude | requests/040-per-band-rows.md | Disease and partner rows kept only for bands holding one (Ben, 22 November 2026); same events as main |
| 2026-11-22 | Claude | responses/039-compact-log-claude.md | All five confirmed and fixed; shadow mode still matches main |
| 2026-11-22 | Claude | responses/040-per-band-rows-claude.md | All three confirmed and fixed; NumPy pinned and each stage's machine recorded; cross-runner replay left to Ben |
| 2026-11-26 | Claude | requests/041-loading-memory.md | Loading large saves from disk without second copies; memory traced at each part; checkpoints kept 14 days (Ben, 26 November 2026) |
