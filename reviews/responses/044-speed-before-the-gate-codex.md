# Review 044 · Speed before the gate

**Codex, 28 November 2026.** Reviewed `dbbb14c..717a969` on `wip-speed`. I found two bounded changes in exact behaviour and a memory cost to include in the next pilot. The whole-number, finite-value cases I exercised matched the old code.

## Findings

### 1. Removing empty members from the prestige sum changes rounding for fractional group counts

- **Where:** `origins/sim/trade.py`, `prestige_factor` (lines 838–845). The group-count validation is in `origins/sim/observe.py`, `end_tick`.
- **What is wrong:** The compact sum omits empty members, which changes the grouping of additions in NumPy's reduction. This is exact for supported whole-person counts at gate scale. A fractional count within the observer's `1e-9` tolerance can still produce a different result.
- **Why it matters:** The optimisation relies on a stronger precondition than the count check enforces. States within the tolerance can give different prestige factors on resume. The difference in my fixture was one representable float step. I found no ordinary producer of fractional group counts.
- **How sure you are:** Certain for counts inside the tolerance. Normal whole-number states matched.
- **How to see it:** Give alternating bands in one polity people and leave the others empty. Perturb the nonzero age-bin counts by at most `5e-10` and compute prestige through the normal snapshot path with a positive, unsaturated treasury. Using RNG seed 44 to draw group sizes from 1 to 49 and these perturbations, main returned `0x1.beea6c66aa335p-14` and the branch returned `0x1.beea6c66aa334p-14` in a fixture with 131 band IDs. Rounding the bins back to whole numbers restored equality. Changing a member's `polity_of` within the same tick affected both results immediately.

### 2. The standalone partnership pass changes saved state even when no gifts can be given

- **Where:** `origins/sim/trade.py`, `partnerships_yearly` (lines 397–403) and `yearly` (lines 224–225). The band-row digest is built in `origins/persist.py`, `_band_rows_digest`.
- **What is wrong:** The new gift loop allocates `trade_in` before looking for a pair. The previous pass allocated it only when processing the goods of an eligible pair. An absent table and a table full of zeros are distinct saved states.
- **Why it matters:** Calling the partnership pass directly on an unlinked world changes its digest without a transfer. The gate's normal entry point initialises this array before calling the partnership pass, so this difference does not affect that path.
- **How sure you are:** Certain for the standalone call.
- **How to see it:** In a fresh world with no partner links or receipts, set the chance of new partnerships to zero and run `partnerships_yearly` directly. On main, `trade_in` is still absent. On the branch, it contains zeros. The ledgers match and the digests differ.

### 3. The speed measurements omit the skill cache's sustained memory cost

- **Where:** `origins/sim/farming.py`, `quality` (lines 82–101), and `docs/M4_BUILD_NOTES.md`, “Speed before the gate.”
- **What is wrong:** The process-wide cache holds the byte key and a NumPy array for each distinct row until the entire cache clears. It can hold 200,001 entries and survive the end of a world in the same process. The reported timings cover short replay windows and give no cache occupancy or memory figure for this change.
- **Why it matters:** The gate has already encountered memory limits on large checkpoints. Cache occupancy on a long run affects the headroom at save time, and clearing a full cache can turn repeated lookups back into misses. The bound below is a synthetic measurement. The gate's actual occupancy is unknown.
- **How sure you are:** Certain about retention and the measured bound.
- **How to see it:** In a fresh process, send `quality` 200,001 distinct nine-species float32 rows by varying one skill from 0 to 2. The dictionary, keys and arrays accounted for about 65 MiB by object size and increased peak RSS by about 69 MiB on this machine. The next distinct row clears the table. Log size and peak RSS during pilot 5 to measure actual exposure.

## Checked and sound

- **Gift arithmetic and views.** A three-band gift chain produced identical full digests with positive, zero and negative source amounts, and with zero, negative, normal and above-one gift shares in the fixture. Each direction clamps against the donor's current balance, while both offers are read before either transfer. The receipts and ledger are written in the same order. Gift logging and trader arrival logging append to their logs. Trader tolls and levies can grow the treasury, which has separate storage. These paths do not grow the band or partner slot maps while the row views are in use.
- **Herding and group keys.** On a 64-band fixture covering farming shares from 0 to 1, the batch keys and cache contents matched the scalar calls, including the absence of entries below half farming. The two versions selected the same move in a case with 13 herders and produced the same digest. Candidate order and each band's live crowding denominator are preserved.
- **Conflict and member caching.** Within one attacking side's search, no fight occurs until after the candidate list is complete. A repeated cell therefore contains the same eligible targets and the first member to encounter each target still supplies its origin and insertion order. `_fight` is the path that can change affiliations during this pass, and the cache clears immediately afterwards. `World.new_band` and the ending paths invalidate the living list, and the in-repo callers I checked read that list without mutating its ordering. Current polity membership remains a fresh lookup.
- **Quality and first arrivals.** Skill rows are keyed by the full float64 bytes. The result depends only on those values, so ordinary lookups across worlds cannot reuse a result for a different skill row. Current callers do not write to the returned values. First arrivals retain the original ordered inflows for their destination, including the existing tie-break by giver and route, by taking ascending indices from the same pair arrays.
- **Replay.** Replay, M2/M3 and targeted trade tests passed (32 tests). A separate 25-year paired run matched the full digest, events and population and recorded no invariant failures. I did not rerun the three reported pilot checkpoints. Event hashes cover the recorded events over their sampled windows. A state and RNG comparison at those same boundaries would also cover differences that have yet to produce an event.

## Remaining exact work, in priority order

1. **Partnership candidate search and trader routes.** Trade is the largest measured phase at about 8 s/year. Count candidate visits and route searches separately from gift transfers. Reuse per-cell candidate lists during the stable part of the partnership pass, preserving the per-band filters, sorted candidate order and number of random draws before any early exit. For traders, count shortlist and toll-aware searches. Reuse a search only with matching direction, travel costs and toll state. Opposite directions can differ.
2. **Conflict target/member matrices.** At about 4 s/year, count unique target cells, targets and matrix entries by side. Reuse the geometry for repeated cells while keeping the first origin and the original target-by-member arithmetic. Combining columns by cell before the floating-point reduction would require an equality check beyond an event hash.
3. **Population lookups during fission, merging and consolidation.** Fission and merging take about 3 s/year. `disease.combine` calls `World.band_size` after a move, and each call scans the individual and group indices again. Count calls and rows visited, then test maintaining exact destination counts through the mutating operations. Compare `pastoral.move`'s all-living `sizes_of` against `live_sizes` too. The former uses a search per holding person and group row. A synthetic comparison with 2.4 million issued IDs and 30,000 living group rows found that the new size lookup beat the dense lookup with 25,000 individuals, while the advantage narrowed or reversed at 250,000. The live mix matters.
4. **Polity membership and flight, then the smaller phases.** At about 3 s/year, count the full-ID `polity_via` scans in flight and subtree searches in secession. A reverse lookup must see reassignments immediately and return children in the same ID order. Revisit disease, foraging, herding and technology after measuring the above. Each is about 2–2.5 s/year in the reported profile.

At year 6,631 there are 4,617 years left to the pilot's year-11,248 target. Applying the reported 0.8 runner multiplier to 34.1 s/year gives 27.3 s/year and about 35 more simulation hours at a flat rate. If the gate has 27 simulation hours left at that point, the remaining years must average 21.1 s/year, about 23% less time per year than that estimate. Pilot 5 needs to establish sustained throughput and memory headroom as the world grows.
