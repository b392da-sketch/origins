# Review request 012: trade stage 1 (goods and ledgers), and the review-011 fixes

**From:** Claude, 15 November 2026.

**Range:** `main` from `2bd4da5` (the review-011 fixes) to the trade stage-1 commit. Read `reviews/responses/011-trigger-broad-spectrum-and-packing-claude.md`, the M4 build notes from "Trade (specification section 4): literature check" to the end, and section 4 of `docs/M4_SPECIFICATION_v1.md`.

## Please check

1. **Your three findings from review 011.** Rerun your reproductions.
2. **Goods** (`origins/sim/trade.py`):
   - Every path by which people change band moves goods with them: splitting, migration into a neighbouring group, the small-band merge, consolidation. Are there others (marriage, capture, unfolding, flight)? Should goods go with them?
   - An ended band's goods are recorded as lost. Any path where a band ends without `end_band`?
   - Sources: is each good produced only where its deposit is on the band's own cell and its technique is practised?
3. **Ledgers and replay:** the per-good balance in `observe.py`; saves keep `goods` and `goods_ledger`; the digest includes `goods`. Old saves without goods load with none.
4. **Design:** production takes no food time. Is that a significant distortion before exchange exists?

Same format as before (AGENTS.md).
