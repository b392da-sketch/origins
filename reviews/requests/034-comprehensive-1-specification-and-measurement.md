# Review request 034: comprehensive pre-gate review, part 1 of 4 — the specification, item by item, and measurement

**From:** Claude, 21 November 2026. Prepared while Ben was away; he hands it to you.

**Why:** the CLAUDE.md rule (Ben, 20 November 2026): before a milestone's gate runs, a whole-milestone review in three or four requests. This is the first. The others are 035 (state and per-band arrays), 036 (interactions and invariants) and 037 (performance at gate scale, and drift between documents and code). Do them in order, one request per session. Rank the risks you find across the whole of each request, and say which should block the gate.

**Scope:** all of M4a as on `main` (from the M3 gate's close, 13 November 2026, to now): `docs/M4_SPECIFICATION_v1.md` sections 2–7 and 9; `docs/M4_BUILD_NOTES.md`; the new gate plan `docs/G4A_GATE_PLAN.md` (a proposal, not yet approved by Ben); and the gate code `gates/g4.py`, `gates/g4_report.py`.

## Please check

1. **The specification, item by item.** For each item in sections 2–7 (carried-forward items, the technology network, trade, the land, diseases, writing and place names):
   - is it built as specified, or as a later recorded decision by Ben changed it?
   - is anything specified missing, or built beyond the specification without a recorded decision?
2. **Each G4a check (section 9), against the gate plan and the code.**
   - Can it be measured from what `gates/g4.py` records, with the reading the plan gives?
   - Is the reading faithful to the check's wording?
   - Could it pass for the wrong reason, or fail for a reason unrelated to the behaviour (for example a sample too small, or a quantity recorded at the wrong time)?
   - Checks 6, 9 and 10 carry proposed readings; say whether they are sound.
3. **Ben's decisions recorded in the build notes** since 13 November: does the code match each one?
4. **The review-031 fixes,** which Ben decided would be verified here (spell restarts, spells year by year, G1 follow-up dating, older counts set aside), and the review-033 fixes.

Same format as before (AGENTS.md).
