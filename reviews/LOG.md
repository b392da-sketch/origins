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
