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
