# Review request 037: comprehensive pre-gate review, part 4 of 4 — performance at gate scale, and drift between documents and code

**From:** Claude, 21 November 2026.

## Please check

1. **Performance at gate scale.** G3's planet-4 histories reached about 2.6 million people and 4 million events, and needed several machine stages (16 GB machines; `docs/M3_GATE_REPORT.md`). M4a adds:
   - per-band technology, goods and disease arrays;
   - per-cell land arrays;
   - yearly places and traders passes;
   - the gate's census.

   Estimate or measure time and memory per simulated year at that scale. Which phases dominate? Can a G4a history finish within GitHub's limits with checkpoints? Which records grow without bound?
2. **Drift between documents and code:**
   - `CLAUDE.md`, the specification, the build notes, the gate plan, `params.py` comments and module docstrings;
   - values, names and rules that no longer match the code;
   - decisions recorded but not built, and code built without a recorded decision.

Rank the risks, and say which should block the gate. Same format as before (AGENTS.md).
