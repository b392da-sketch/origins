# Review request 015: trade stage 4a (partners trade, hubs form), gift records, and the review-014 fixes

**From:** Claude, 15 November 2026.

**Range:** `main` from the review-014 answer to the stage-4a commit. Read `reviews/responses/014-trade-stage-3-down-the-line-claude.md`, and the M4 build notes from "Trade stage 4: literature check on directed trade" to the end (Ben's decisions for stage 4 are there).

## Please check

1. **Your three findings from review 014:** rerun your reproductions, especially the 101-band cell and the low-stock frontier (arrivals, and their cost).
2. **Partner pairs** (`trade._partner_pairs`): partners who are not on the same or an adjacent cell join the exchange as pairs of kind 3, for working goods only. Is any pair counted twice? Does the dense-cell limit treat them correctly?
3. **Link allowance** (`trade.allowance`): links grow with the square root of band size, at most 16. This was my choice, not Ben's; is it sound, and what does it do to bands that shrink below their links (they keep them and make no new ones)?
4. **Swaps** (`trade._switch`): draws from the "trade" stream in band order; the twice-as-well-supplied rule; the events for the dropped and the new partner. Can a band swap to a partner it has just dropped, or back and forth?
5. **Gift records** (Ben's decision): running totals in `w.partner_gave` reset on every new link, kept in saves and the digest; one event per partnership for the first exchange; totals carried by the lapse event; a thinned `gift_log`. Are totals lost anywhere a link ends (`band_ended`, `_unlink_all`, consolidation)? Does this still meet the specification's "each trade recorded with its partners, goods and quantities" (section 4.2)?
6. **Older saves:** four-link saves widen to 16 without changing links or goods.
7. **Event volume:** partnership formation and lapse are now the largest kinds of event. Worth thinning?

Same format as before (AGENTS.md).
