# Review request 013: trade stage 2 (gift partnerships), the review-012 fix and the war-goods decision

**From:** Claude, 15 November 2026.

**Range:** `main` from `dc128f3` to the stage-2 commit. Read `reviews/responses/012-trade-stage-1-claude.md` and the M4 build notes sections "Trade stage 2: gift partnerships (design, before building)" and "... as built".

## Please check

1. **Review 012's finding** (marriage carries goods) and the loot rule (a winning raid takes `RAID_TAKE` of the loser's goods). A behavioural test of the loot rule would be welcome as a reproduction.
2. **Partnership links** (`partner_of`, `partner_since`): always symmetric? Can a link point to an ended band, to itself, or appear twice? What happens when a band ends by consolidation or merging rather than `end_band` (links are dropped at the next yearly pass)? Is that gap harmful (help in the seasons between)?
3. **Formation draws:** from the `trade` stream only, in an order that depends only on state?
4. **Help in need** (`share_in_need`, called inside `foraging.forage_and_eat` before eating): food moves between bands' food in hand and the total is unchanged. Does the giver always keep its own needs (for farmers, until the next harvest)? Can a band be both helped and a giver in one season? Does help change the recorded foraging return, the margin or storage in ways it should not?
5. **Techniques:** partners teach at closeness 1. Correct only when the teacher drawn is a partner?
6. **Saves and replay:** links round-trip; old saves load with none.

Same format as before (AGENTS.md).
