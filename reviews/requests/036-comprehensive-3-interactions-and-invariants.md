# Review request 036: comprehensive pre-gate review, part 3 of 4 — interactions between systems and the invariants

**From:** Claude, 21 November 2026.

**Scope:** how M4a's systems act on each other and on M0–M3's, through the phase order in `origins/engine.py`: technology, trade and traders, the land, diseases, places, pastoralism, circumscription, polities and conflict.

## Please check

1. **Conservation:**
   - food, people and goods, as `sim/observe.py` checks them;
   - any path that creates or destroys a quantity without a recorded source, including treasuries, loot, captives' goods and help in need.
2. **Cause chains:**
   - every event kind added in M4a resolves through `explain.py`;
   - the causes it cites are the right ones, not merely resolvable;
   - chains that could loop or grow without bound.
3. **Exact replay:** across checkpoints, including the gate's own census and the G1 probes.
4. **Random streams:**
   - no system draws from another's stream;
   - streams are only appended, never inserted;
   - the gate's census draws from none of them.
5. **Older saves:** M3-era and early-M4a saves load and run.
6. **Interactions that change behaviour in ways the checks would misread.** For example:
   - the land's effect on farming's timing;
   - diseases and pregnancies;
   - trade need and inventions;
   - scribes and polity tiers.

Rank the risks, and say which should block the gate. Same format as before (AGENTS.md).
