# Review 038 — speed fixes from the G4a pilot

Reviewed `wip-speed` at `85c6430`, against its merge base `36491ca` and current main `71dd3e1`. **Hold the speed-only merge on finding 1. Hold full G4a dispatch on the time budget.** The reported 40-year comparison is good evidence for the speed improvement on that slice. The same-tick capacity case below shows that the old and new routines can return different results.

## Ranked findings

### 1. Prestige can change polity capacity after a casualty in the same tick

- **Where** — `origins/sim/trade.py:761–775` on the branch and `prestige_factor` at `36491ca`; `origins/state.py:Bands.__len__, World.new_band`; `origins/sim/technology.py:capacity_multiplier`; `origins/sim/polity.py:capacity, _new_polity`; `origins/sim/conflict.py:_fight`.
- **What is wrong** — The premise that the old cache never hits is false on ordinary worlds. Issued bands stay in the record, including after packing, so the number of band records can equal `len(w.band_sizes()) == w.next_band`. On a hit, the old code looks up current polity membership but uses the size snapshot from the first qualifying prestige call of the tick. The branch looks up both membership and size fresh.
- **Why it matters** — A death or transfer can change the denominator before a later capacity call. Capacity is used by institution, secession and conquest logic. The standard polity pass precedes conflict, and existing-polity attacks use the already calculated capacity. I did not establish a divergence through an unmodified engine tick. The replacement still changes the callable's same-tick contract.
- **How sure you are** — Certain. I reproduced the difference through real casualty and capacity routines in both trees. The reported pilot digest can still match if its slice does not encounter a consequential change.
- **How to see it** — Give two 30-person bands membership of the same polity, and put enough shell in its treasury for a prestige factor of 0.5. Call `polity.capacity`, use `conflict._kill` to remove ten people from one member, and call capacity again at the same tick without creating a band. Both trees have three band records and three size slots. The base stays at prestige **0.5** and capacity **3.15**. The branch gives **0.6** and **3.18**. At the next tick both give prestige **0.6**. To retain the old timing, preserve when the size snapshot is created and invalidated, and keep membership current. The snapshot can use a compact representation. In the next profile, count actual cache misses separately from time spent summing packed flags to check its length.

### 2. The size helpers disagree about invalid IDs and differ from their stated indexing contract

- **Where** — `origins/state.py:534–581` on the branch.
- **What is wrong** — `band_size(next_band)` silently gives zero while the dense array and bulk lookup raise. A negative index such as `-1` selects the last entry in the dense array, raises in the bulk helper and normally returns zero in the scalar helper. The bulk cast also silently turns a float such as `1.9` into band ID 1.
- **Why it matters** — Absent IDs can look like empty bands or select a different band, instead of exposing an upstream error. The branch's reviewed simulation callers supply valid nonnegative integer IDs, so I found no ordinary-path outcome change from this boundary case.
- **How sure you are** — Certain for the tested inputs.
- **How to see it** — Use a world with three populated bands. Compare `w.band_sizes()[i]`, `w.sizes_of([i])` and `w.band_size(i)` for `i = -1, 3, 1.9`. Either preserve the old indexing where intended or document and enforce the same nonnegative-integer contract in both helpers.

### 3. A language pair can return an old result if it is queried after a lexicon change in the same tick

- **Where** — `origins/sim/trade.py:323–336,339–423`, `origins/sim/language.py:243–322,399–400`, `origins/engine.py:28–38`.
- **What is wrong** — The cache key contains only tick and language IDs. Replacement or borrowing can change shared roots without changing either ID or tick.
- **Why it matters** — The current engine runs trade before language and has no subsequent trade-closeness reader in that tick. The issue therefore affects repeated or standalone calls that span the language pass. Scoping the cache to one partnership pass would make its lifetime match the proven read window.
- **How sure you are** — Certain about the stale lookup. I found no ordinary engine path that uses it.
- **How to see it** — Query two languages with identical roots, then change one of the second language's roots in place, keeping IDs and tick fixed. Base reads the new value **0.9913978494623656**. Branch returns the cached **1.0**. A one-tick advance expires it.

## What still limits a planet-4 history

There are five nominal 4.5-hour stages, including checkpoint reload time within each stage's budget. With a first farming village near year 19,000, the approved six-millennium window ends near year **25,000**. At year **5,765** that leaves about **19,235 years**. At the reported branch rate of **15–19 s/year**, those remaining years alone would take **80–102 hours** if that rate stayed flat. The three stages left after the pilot checkpoint allow **2.53 s/year** on average before reloads. Even allocating all five stages to the remaining slice gives **4.21 s/year**. These are budget scenarios. Neither the G3 village date nor a constant late rate is guaranteed for G4a.

The following priorities preserve the rules. The order reflects demonstrated scaling and expected call frequency. Re-profile a common checkpoint after finding 1 is resolved before claiming end-to-end savings.

| Priority | Remaining cost | Exact optimisation to measure |
|---|---|---|
| 1 | **Population and membership rescans inside frequently called paths.** `band_size` dropped the historical arrays but still scans living individual membership and the group active flags and band IDs on each call. A small `sizes_of` request also scans those populations. Prestige additionally compares every historical `polity_of` entry for each funded capacity call. | Maintain or reuse an index of individuals and active group rows by band, and a phase-local index of polity members. Preserve group-row order, the base prestige snapshot's lifetime and ascending ID order in the prestige reduction. Refresh membership and population at the corresponding split, merge, migration, capture, death and unfold boundaries. Consider passing sizes from callers that already have the same post-move quantity. |
| 2 | **Dense historical scratch and accounting.** Each cold `practised_quality` builds a float32 array as large as `w.tech` even though it fills only live rows. The engine clears that cache at every phase boundary. Other costs include the `next_band` position array on live-index rebuild, `band_sizes` and `groups.sizes` in movement and observation, and goods sums and validity scans over all allocated rows each season. | Compute eligibility and effects in living-band order and pass compact results to callers. Preserve evaluation and refresh boundaries. Reuse a compact size aggregation across bulk calls while population is unchanged. Move seasonal consumers to compact sizes where their input set and reduction order are equivalent. Keep the observer's validation of ended rows and its reduction semantics when reducing ledger work. |
| 3 | **Living-band interactions and route searches.** Same-cell and neighbouring-cell exchange enumerates pairs. Conflict and gift candidate selection walk nearby bands. Technology works over live bands × techniques, nearby occupied cells and current links. Directed traders compare each active origin with all live seats, then search up to 12 candidates in both directions and can reroute around tolls. Historical polity and language registries also get walked even when most entries ended. | Profile these phases on the late slice. Reuse ordered cell and seat indices, avoid repeated eligibility work on the same snapshot and batch exact candidate calculations while preserving tie breaks, RNG draw order and accumulation order. For routes, keep the existing shortlist and cache semantics unless a separately verified equivalent algorithm replaces them. |
| 4 | **Checkpoint, restore and finish.** These scale with the 16.9 million events already present, plus historical band and person arrays. The save iterates and re-encodes the event stream. Restore decodes it and rebuilds the cold store, and materializes the archive's array member in memory. The branch leaves persistent array layout unchanged. | Measure save, reload and final record build separately on the same checkpoint. Reuse a streamed cold-event representation and avoid reading the full array member into a temporary buffer, while preserving IDs, event mutability and replay. Before adding stages, measure how their additional reload and upload costs reduce usable time. |

The synthetic timings below isolate array work. They use a planet-4 grid and vary the issued-ID count and group-row count independently. They are local one-thread timings, with no late-world routes, war or checkpoint data. Each row reports milliseconds per call.

| Issued IDs | Group rows | Full size array | Single size | Ten selected sizes | Full polity membership scan | Zero one technique matrix |
|---:|---:|---:|---:|---:|---:|---:|
| 170,000 | 1,400 | 0.325 | 0.012 | 0.040 | 0.029 | 0.68 |
| 1,700,000 | 1,400 | 7.689 | 0.012 | 0.042 | 0.318 | 24.28 |
| 1,700,000 | 14,000 | 8.281 | 0.034 | 0.144 | 0.291 | 22.39 |

The single lookup removes the issued-ID dependence measured here. The remaining small lookups grow with population records. At 1.7 million IDs, a funded prestige call still includes the all-ID mask before the size lookup. The usual doubled capacity of 2,097,152 rows makes one 27-column float32 quality matrix **216 MiB**. At four times that capacity, the M4 band arrays measured in review 037 would alone account for about **13.6 GiB**. For scale only, extrapolating the pilot's average ID issuance rate unchanged to year 25,000 would reach about 7.4 million IDs, enough to cross into that capacity. Actual issuance is unmeasured and may change in either direction. One history per runner controls concurrency and leaves the single-history risk to be measured.

Both `tools/profile_ckpt.py` on `profile` and the paired `tools/timing.py` runs time engine stepping. They install the G4 wrappers without setting their probe state and omit the worker's annual `g2.probe` and G4 `census`. Their timed intervals therefore omit worker overhead. Compare future timing runs with the same checkpoint and settings, and report worker and engine-only time separately. Compare the full state that controls the next tick and event tails as well as the digest, since a short matching slice cannot cover the timing case in finding 1.

## Checked and sound

- For valid positive and zero integer IDs, `sizes_of` returns repeats in requested order and preserves array shape, including empty selections. Both helpers matched the full calculation bit for bit with 65 group rows, several rows per band, inactive rows, fractional stress counts over multiple magnitudes, and individual members. The code keeps the original age-bin reduction and adds group rows in ascending row order before adding individual counts.
- The pasture vector matched the scalar outputs bit for bit across sampled planet-1 land cells and varied skill vectors. `move` retains neighbour order and the same strict comparison, so ties keep the first candidate.
- The herder cache's change of key shape leaves the same band-and-cell key and cached booleans. `carry` still invalidates all cached cells for the receiving band after a whole-band skill merge. I found no new stale-value path in normal stepping. A same-tick caller supplying different tables or mutating skills outside that invalidation would still see the old limitation, which predates this branch.
- `Bands.__len__` matched the historical count before packing, after packing, and after save/restore. Packing and array loading invalidate the stored count. Growing adds zero flags, and new band insertion changes the live dictionary count directly.

## Validation

- Ran the paired casualty and closeness fixtures against source archives of both reviewed trees. Also checked indexed sizes, vector pasture and packed counts in the branch archive.
- A short planet-1 run matched across the two trees at year 20, including continued saves, the state digest, and a hash of all recorded events. The focused set passed seven tests, including herder invalidation. Across the trade and disease files, 93 tests passed in the initial run. The sole failure was the dependence test because my scratch archive omitted its tracked helper. The test passed after I copied the helper from the reviewed commit.
- The performance fixture made one active group row per selected ID and timed repeated calls to `band_sizes`, `band_size`, `sizes_of`, the prestige membership mask and `np.zeros_like(w.tech)`. It used 1,400 and 14,000 synthetic group rows with the same age arrays. Results show scaling of individual kernels.
- The pilot timing and digest are the request's reported measurements. The Actions API returned HTTP 403 here and the original stage-2 checkpoint was unavailable in the workspace. I did not rerun a gate-length history.
