# Review 016: traders, routes, tolls and rulers' stores

**Reviewer:** Codex, 15 November 2026.

**Reviewed:** pulled `main` to `1f7cae6`, including the review-015 answer/fixes from `d848936`, stage 4b and the requested build notes through Ben's curation decision. Followed `AGENTS.md` and the existing project rules. Curation is not implemented or reviewed here. No implementation files changed; no gate-length runs.

**Result:** the five review-015 reproductions and the reforming wait check out. Three findings follow. A*'s heuristic is conservative on the current grid; carrying conserves goods for the supplied cost/tax inputs, and treasury lifecycle/growth checks pass. Correct arithmetic does not validate the geographic costs or toll assignments.

## Findings

### 1. Landing from the sea charges a climb from the seabed

- **Where:** `origins/sim/traders.py:120–126` (`_cost`), particularly `elevation[v] - elevation[u]`.
- **What is wrong:** A sea cell's elevation is its negative seabed height, but a landward step treats the trader as starting at that height. A boat travels at the sea surface, so ocean depth should not become an uphill climb on landing.
- **Why it matters:** Sailing routes acquire artificial coastal penalties, affecting route selection, reach, losses and gravity weights. This can suppress maritime transport before any wear-rate calibration.
- **How sure you are:** Certain.
- **How to see it:** On planet 1, sea cell **4997** is at **−1,763.93 m**, adjacent land cell **19931** at **45.21 m**. With canoe/sail quality 1 and no pack/cart bonus, `_cost` charges **4.61828** for the landward step. Starting the land ascent at sea level gives **1.09042** under the same formula. The extra **3.52786** is entirely seabed depth. Neither endpoint pair qualifies for the both-coastal-land water discount.

### 2. A detour can create an impossible toll-free passage

- **Where:** `traders._carry:269–286`, which builds `crossed` from the original road and never examines the chosen detour's holders.
- **What is wrong:** Avoiding one polity changes only accumulated cost and the evaded list. A different polity crossed by that detour is never charged. Independently chosen detours also need not describe one jointly feasible road.
- **Why it matters:** This can remove bottlenecks even when every possible road crosses a taxing polity. It is a failure of the stated “each polity the road crosses” rule, not just a slightly approximate travel cost.
- **How sure you are:** Certain for the counterexample.
- **How to see it:** Use a four-cell diamond: A–K–B and A–L–B, each costing **2**, with K and L owned by different third polities. The original road goes through K; blocking all K land selects the equally cheap road through L. Blocking both leaves no road. `_carry` nevertheless records K evaded, **zero tolls paid**, and zero receipts at both K and L. All conservation checks pass, but no such untaxed road exists.

### 3. The route cache is not a pure function of its key

- **Where:** `traders.path:135–138`; `_step_costs`, `_cost` and range pruning read inputs absent from that key.
- **What is wrong:** The key identifies the planet only by seed and omits cost-affecting parameters and `TRADE_RANGE`. Different supported resolutions of the same seed, or different cost configurations in one process, can reuse incompatible answers.
- **Why it matters:** Routes, reach and therefore goods outcomes can depend on prior cache fills outside the current world. Discarding the cache on reload is not equivalent in those cases. This is conditional on sharing the process across such worlds/configurations; ordinary replay with one fixed planet/configuration passed below.
- **How sure you are:** Certain.
- **How to see it:** (a) Cache planet-1 land route **2→21890** under `TRADE_RANGE=0.01`, then restore range **30**. The warm cache still returns `(inf, ())`; clearing it returns cost **1** and the adjacent route. (b) With all transport qualities 1, cache **2→5506** on seed 1 at level 5: cost **0.4**, direct edge. Query seed 1 at level 6: the warm result repeats that edge, which is **not adjacent on the new grid**. A cold query returns cost **0.88402**, route **2→21890→5506**. Both endpoints are land in both worlds.

## Review-015 fixes and reforming wait: checked and sound

- The sailing partner pair is emitted once and transfers **5**, not 10. Working-only links no longer reduce the ordinary **5-pottery** transfer; remote partners still receive none.
- Real ending, merging and consolidation now add lapse records carrying the full **9.75 / 0.25 shell** totals, even when the thinned gift log retained only the first exchange. Links/counters are cleared afterwards.
- Held goods are marked reached before the no-pair return; later import after wear creates no false first-arrival event in the previous fixture.
- A candidate at exactly **2×** supply now qualifies.
- A real swap sets the same `_parted` result in both endpoint orders. After save/load it remains blocked at **39 ticks** and becomes eligible at **40 ticks** (10 years); normal formation can then reconnect it, and annual cleanup removes the expired entry. Original and loaded states/events/digests match. The parting map is included in persistence and the digest.

## Search and travel checks

For the current level-6 grid, the longest neighbour edge is **1.0946669 mean cell spacings**. Multiplying it by 0.8 gives **0.8757335 ≤ 1**. By the triangle inequality, the heuristic's decrease over an edge is therefore no larger than the cheapest permitted step cost. Actual ascent/high-ground costs only add to that bound; blocked cells do not invalidate it. Thus the heuristic is conservative and consistent on this grid, up to floating-point roundoff.

An independent Dijkstra search agreed with A* in **18** sampled cases covering foot, full and mixed transport, with blocked cells and the range cutoff. Finding 3 is cache contamination, not a failure of the A* heuristic.

Lake access also checks out: the **final** planet constructor removes lake cells from `land`. On planet 1, entering lake cell **53** from **12378** without canoes returns no permitted step and no path. The earlier intermediate generation mask is not the simulation's land mask. Sea steps likewise require positive rounded sail quality. The landing elevation issue is finding 1.

## Carrying and treasury: checked and sound

An independent per-good oracle exercised all nine goods, both flow signs, a binding load cap and a compulsory toll. For a total **50-unit** load at cost 7, the split was:

| Fate | Units |
|---|---:|
| Road loss | 3.380309 |
| Transit toll | 2.330985 |
| Destination first pick | 4.428871 |
| A's traders' share, taken home | 9.964959 |
| Remaining delivery | 29.894877 |

The same accounting passed in both directions. Positive and negative flows use the correct source stock and destination ruler; the traders' share always goes to **A's seat**. On a return load, that share and the remaining delivery both enter A's pooled band stock. Sources, destinations and treasury rows remained nonnegative; total goods plus treasury fell only by recorded road loss. Initial proposals respect the half-stock bound, and scaling the sum of absolute loads cannot increase any proposal.

- An actual conquest transferred the defeated ruler's stock to polity **200**, growing the treasury array and preserving the entire vector. The actual polity-end hook then passed it to the living seat.
- Ending a polity with a dead seat recorded the whole treasury as lost. Both current polity-ending paths—ordinary `_end_polity` and conquest—have hooks; no additional unhandled ending assignment was found.
- High treasury row **130** wore at every good's declared rate and balanced against the ledger. Treasury is included in `trade.totals`, saved and digested.
- An eight-trader-year continuation matched goods, treasury, route/evaded sets, complete events, route log and digest with warm versus explicitly cleared caches **under fixed planet/settings**. New route/arrival references resolve. This does not cover the cross-configuration failures in finding 3.
- Code order is neighbour exchange, traders, then band/treasury wear. Traders use no random draws; ranking/ties and road search use deterministic order.

## Tolls: judgement on the simplification

For one isolated toll, comparing `1−exp(−ROAD_LOSS × extra_cost)` with `TOLL` is a coherent marginal goods-loss decision. Common survival factors cancel. The more serious issue is retaining the original road's ownership after choosing another road. Summing independent detour increments can also overcount overlapping extra distance or describe mutually incompatible avoidances. Finding 2 shows why I would not accept that part as a harmless approximation for a bottleneck gate: it can erase a bottleneck that is unavoidable.

## Speed

Every trader polity computes distances to **all** live seats and fully sorts them before retaining 12 candidates: approximately quadratic distance work and quadratic-times-log sorting as polity count grows. Each active polity then makes up to **12** base path queries and up to **3** carries; each crossed toll can add a blocked-land search. Changing borders create new blocked-set cache keys. The cache clears wholesale beyond 200,000 entries, which can create bursts of cold searches.

A short synthetic test isolated ranking/dispatch, with all polities having traders and cached qualities; path/carry calls were stubbed and their mock-call overhead remains included:

| Polities | Ranking/dispatch | Candidate path calls | Selected routes |
|---|---:|---:|---:|
| 500 | 0.19 s | 6,000 | 1,500 |
| 1,500 | 0.99 s | 18,000 | 4,500 |
| 3,000 | 3.19 s | 36,000 | 9,000 |

These are not full-year timings or a reproduction of the private 100-year trial. They identify the all-seat ranking loop as a scaling cost even before A*/cargo work. Cache hit/miss and blocked-search counts would separate that cost from road search in the real trial. No gate-length run was started.

## Design questions for Ben

- **First pick:** the code transfers `FIRST_PICK` to the destination ruler without any payment. Ben's earlier wording was a right to **buy** first; the as-built description says the ruler **takes** a share. As implemented it is another goods levy. Confirm that economic interpretation before treating the resulting hoard as a purchase mechanism; I have not invented barter prices or compensation.
- **One cost for both directions:** `_cost` is directional because climbing differs from descending, but a route's A→B cost is applied to every signed load and the traders' share is returned home without another travel charge. That is an implicit one-cost caravan approximation, not accounting for the loaded direction and both journey legs separately. Make that choice explicit when judging transport effects.
- **Nearest-12 preselection:** this is documented, but geographic nearness is neither cheapest road access nor strongest gravity. It can exclude a large, more distant centre or fill the shortlist with inaccessible seats. That speed/long-link tradeoff belongs in the interpretation of the thin-tail result; this review does not prescribe a different route model.

## Validation

**124 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **932.09 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts, oracles and outputs are under uncommitted `reviews/scratch/016*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
