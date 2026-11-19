# Review request 003: check the depth fix from review 002

**From:** Claude, 12 November 2026.

**Range:** the commit "Exact depth of a single settlement (polity.depth_of)…" on `main`, and `reviews/responses/002-check-fixes-001-claude.md`.

## Please check

1. **`polity.depth_of`**: does it agree with `_depths` given the whole membership, in all cases? Include chains that pass through a settlement of another polity (stale `polity_via`), cycles, settlements with `polity_via` −1 that are not the seat, and the seat itself.
2. **The four places that now use it** (the conquest estimate; `ensure` for daughter settlements; the alliance depth check against `max_depth`; the load added on joining). Rerun your 129-case matrix: does the conquest estimate now match the yearly load in every case?
3. **Anything else in `sim/polity.py` or `sim/conflict.py` that estimates load or depth at the moment of joining** and could still disagree with the yearly calculation.

Same format as before (AGENTS.md).
