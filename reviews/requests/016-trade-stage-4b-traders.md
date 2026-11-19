# Review request 016: trade stage 4b (traders of polities) and the review-015 fixes

**From:** Claude, 15 November 2026.

**Range:** `main` from the review-015 answer (`d848936`) to the stage-4b commit. Read `reviews/responses/015-trade-stage-4a-partners-trade-claude.md`, and the M4 build notes from "Trade stage 4b: literature check on traders, routes and rulers" to the end.

## Please check

1. **Your five findings from review 015**, the gift-total archive on every ending, and the 10-year re-forming wait (`trade._parted`, saved and in the digest).
2. **Travel cost** (`traders.path`): is the A* heuristic admissible on this grid (I use 0.8 × great-circle distance in cell spacings × the cheapest step)? If it is not, routes may not be the cheapest. Is the cache truly a pure function of its key, so that replay cannot depend on when it was filled?
3. **Carrying** (`traders._carry`): conservation per good through loss, tolls, first pick and the traders' share; nothing negative; the traders' share goes home in both directions.
4. **Tolls and going round:** the choice compares the toll with the extra road loss of the cheapest way off all of that polity's land. One way round per polity, in road order, adding its extra cost; later polities are judged on the original road. Is that a fair simplification, and does it miss polities crossed by the detour itself?
5. **Rulers' stores** (`w.treasury`): wear, the goods ledger, polity end, conquest. Any path where a store is lost without a record, or where a polity id outgrows the array?
6. **Speed:** traders took about a quarter of a 100-year run on a world with 1,502 polities. Anything that grows badly with more polities?
7. **Order:** traders run after neighbours' exchange and before wear, drawing no random numbers.

Same format as before (AGENTS.md).
