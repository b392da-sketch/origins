# Review 038 follow-up — finding 1

22 November 2026. Re-checked Claude's answer and main at `e0dea1c` against the pre-speed implementation at `36491ca`.

**Finding 1 is resolved.** The prestige calculation again uses the population snapshot from the first funded lookup in the tick. A later funded lookup refreshes it if the tick or the band count changes. Membership is read afresh on each call. Packing an ended band preserves the band count and therefore the snapshot. `origins/sim/trade.py:762–794`, `origins/state.py:Bands.__len__, Bands.pack, World.new_band`.

The compact snapshot includes band IDs from living individual records and active group rows. `World.sizes_of` accumulates those group rows in their original order. The prestige calculation reconstructs the old member vector in ascending band-ID order, including zero slots, before summing it. This preserves the floating-point reduction inputs as well as the snapshot timing. `origins/state.py:534–539,569–593`, `origins/sim/groups.py:129–135`, `origins/sim/trade.py:775–794`.

## Verification

- Re-ran the original casualty scenario on main and the pre-speed base. Both held prestige at **0.5** after ten same-tick casualties. The reviewed `wip-speed` commit `85c6430` still fails the same assertion at **0.6**.
- The two implementations matched bit for bit across a same-tick membership departure, a refresh after creating a band in that tick, a next-tick refresh, and packing an ended band. An unfunded call left the snapshot uninitialized in both.
- With individual members, multiple active group rows for one band, an inactive row and zero-size members, the reconstructed snapshot matched the dense array bit for bit. Both implementations returned the same prestige factor.
- Both prestige tests in `tests/test_trade.py` passed. This recheck used small local fixtures. Planet-4 timing and the full gate remain outside its scope.
