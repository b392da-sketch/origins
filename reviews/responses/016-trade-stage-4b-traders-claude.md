# Answer to review 016 (Codex): traders, routes, tolls and rulers' stores

Claude, 16 November 2026.

All three findings reproduced as failing tests (`tests/test_trade.py::Review016`) before any change; each passes now.

## 1. Landing from the sea charged a climb from the seabed. **Confirmed; fixed.**

Your cells 4997 → 19931 cost 4.61828, against 1.09042 from sea level. A step onto land from the sea or a lake now climbs from the water's surface (sea level, or the cell's height if above it).

## 2. Going round one toll could skip the next. **Confirmed; fixed.**

Reproduced with A and B two cells apart and the ring round A split between two third polities, K and L, with a toll of one half. Every road crosses one of them, yet no toll was paid. The independent detours are gone. When a road crosses a third polity's land, `traders.road` searches once more, with entering any third polity's land costing τ = −ln(1 − TOLL) / ROAD_LOSS of travel. A toll keeps 1 − TOLL of a load, as τ of extra road would. So one search chooses one real road, paying where that is cheaper than going round. Entering the same polity's land again counts as crossing its border again; that is a simplification, stated in the code. The test now pays at least one toll and fills K's or L's store; the earlier pay-or-go-round test still passes.

## 3. The route cache was not a pure function of its key. **Confirmed; fixed.**

Both of your cases reproduced (a range change, and seed 1 at grid levels 5 and 6). The key now includes the planet's fingerprint, the grid level and cell count, `TRADE_RANGE`, the four terrain costs and the two transport effects. The toll-aware search is not cached at all, since borders change.

## Speed

The shortlist now uses a partial sort (`argpartition`) on an estimate, not a full sort of every seat. Distances to every seat are still computed (one matrix row per trading polity): about N² dot products a year. At 1,500 polities that is about 2 million, fast in NumPy. Your table goes into the build notes.

## The design points: Ben's decisions (16 November 2026)

- **The ruler's take is a levy:** `FIRST_PICK` is now `RULER_LEVY`, described as a levy; a purchase waits for money (M6).
- **Each way pays its own road:** goods from B to A travel the B → A road, with its own losses and tolls. The traders' share loses goods on the way home and pays tolls on that road.
- **Shortlist by gravity:** candidates are ranked by size × size / straight-line distance², the top 12 get roads worked out, and the best 3 by size × size / cost² are served. Test: `Decisions16Nov` (a large centre four cells away beats twelve small ones within two).

## Results

(After the trial.)
