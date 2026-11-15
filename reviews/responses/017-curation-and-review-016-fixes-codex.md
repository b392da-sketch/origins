# Review 017: curation and the review-016 fixes

**Reviewer:** Codex, 16 November 2026.

**Reviewed:** pulled `main` to `186ecfa`, covering the review-016 changes/answer through curation, the requested build notes and Ben's decisions, under `AGENTS.md` and the existing project rules. No implementation changes or gate-length runs.

**Result:** curation's declared rule, bounds, commodity scope, ledger and knockout switch check out. The original sea-landing, K/L-diamond and cache reproductions now pass. Three additional travel findings follow. The reported fall in first-arrival events needs a different interpretation from repeated stockouts; controlled examples below show how it can occur.

## Findings

### 1. An unavailable return road is replaced by the outward road

- **Where:** `origins/sim/traders.py:379–381`, especially `back = ... if bcells else out`.
- **What is wrong:** If B→A has no road within `TRADE_RANGE`, `_carry` reuses the A→B leg as though a return journey were possible. Reverse cargo and outbound traders' returning shares can consequently travel without a legal homeward road.
- **Why it matters:** This contradicts Ben's decision that each direction pays its own road. Ascent makes reach directional even on an undirected grid; the fallback can move goods through an explicitly rejected journey. The quantity ledger still balances.
- **How sure you are:** Certain.
- **How to see it:** Use a 20-step land corridor descending uniformly from **6,000 m to sea level**, with no alternatives and the default range **30**. Outward travel costs **26.5**; uphill return costs **39**, so `path(B,A)` returns `(inf, ())`. Give B 100 salt and call `_carry` with load cap 4. It removes **4** from B and credits A with about **2.762** plus the ruler's levy, using the outward cost for the impossible return. No invariant fails.

### 2. Toll-aware search can discard the feasible, better road at the range boundary

- **Where:** `traders.road:217–246`, one `best` augmented cost and one `terr` travel expenditure per cell.
- **What is wrong:** A prefix with lower travel-plus-toll cost can require more physical travel than another prefix to the same cell. Retaining only the former discards the remaining-budget distinction needed by the separate hard travel limit.
- **Why it matters:** `road` can return no route despite feasible alternatives; `_leg` then falls back to the original road and pays more toll than necessary. Correct τ does not make a single-label search correct for two different cost/budget quantities.
- **How sure you are:** Certain.
- **How to see it:** Three prefixes reach one junction: **3 travel + 2 tolls**, **4 travel + 1 toll**, and **5 travel + no toll**. All share a final **26-travel** corridor. At the default range 30, the complete 29/2-toll and 30/1-toll roads are feasible; the 31/no-toll road is not. With default τ≈5.1293, the search retains the cheapest augmented prefix (5/no toll), exhausts its range and returns no road. `_leg` falls back to **29 travel / 2 tolls**, surviving fraction **0.675308**. The feasible **30 travel / 1 toll** road survives **0.703777** and should win.

### 3. Lake exits still climb from the bed rather than the water surface

- **Where:** `traders._cost:121–123`; lake generation in `origins/worldgen.py`, where `filled - elevation > 25` identifies flooded ground.
- **What is wrong:** The new non-land origin height is `max(0, elevation[u])`. This fixes negative ocean depths, but a positive lake-cell elevation remains its ground/bed height, not the filled water surface.
- **Why it matters:** Lake-to-land steps retain an artificial depth penalty, affecting route costs, reach and losses. This is a related case beyond the original ocean counterexample, not a failure of the sea-level fix.
- **How sure you are:** Certain about the stored heights and computed penalty.
- **How to see it:** On planet 1, lake cell **4991** has bed elevation **352.82 m**. Re-running the original priority flood with the pre-lake land mask (`land | lake`) gives its water surface **671.26 m**. Adjacent land **19836** is **830.80 m**. With canoes and no pack/cart bonus, the charged step is **1.95596**, versus **1.31908** from the actual filled surface: **0.63688** extra from lake depth.

## Review-016 fixes: checked

- **Sea landing:** the original **4997→19931** step now costs **1.09042**, removing the former seabed charge. Finding 3 identifies the distinct positive-height lake case.
- **K/L diamond:** the toll-aware road now chooses one actual two-step road and pays K or L. It no longer reports a toll-free passage through a barrier that every road must cross. Finding 2 concerns a separate hard-range case.
- **Cache:** a result cached under range 0.01 no longer contaminates restored range 30. Seed 1 at levels 5/6 now retains different, valid routes for **2→5506**, and warm/cold results agree. The key includes the planet fingerprint, grid and the cost settings used by `path`; toll-aware `road` is not cached. The ordinary A* comparisons with independent Dijkstra still pass in **18** mixed transport/blocking cases.

## τ, re-entry, levy and both journey legs

The exchange rate is correct for the stated objective. A road of cost c with n toll entries preserves

`exp(−ROAD_LOSS × c) × (1−TOLL)^n = exp(−ROAD_LOSS × (c + nτ))`,

where `τ = −ln(1−TOLL)/ROAD_LOSS`. Thus minimizing augmented cost maximizes arriving quantity, subject to the physical travel budget. This uses the declared positive road-loss rate and fractional toll; it does not cure finding 2's budget-state loss.

Counting re-entry as another toll is consistent with the explicit per-border-entry policy and makes fees additive on edges. A forced four-step road entering the same polity twice returned `[K,K]`; 100 goods became **86.711247**, exactly `100 × exp(−0.04) × 0.95²`. Contiguous cells in the same polity do not each add another entry. The policy charges fragmented territory more often than a once-per-polity journey rule would; that is the stated simplification. The route-log integer combines the two legs' paid lists and should not be read as a full count of every collection on both legs; the cash amounts record the actual deductions.

The levy is now explicitly `RULER_LEVY`, matching Ben's decision. An independent nine-good oracle used an outward road costing **2**, a homeward road costing **4**, and a compulsory toll each way. With a binding **50-unit** load:

| Cargo direction | Road loss | Tolls | Levy | Traders' share home | Remaining delivery |
|---|---:|---:|---:|---:|---:|
| A→B, share returns B→A | 1.400831 | 2.953752 | 4.655944 | 9.561853 | 31.427620 |
| B→A | 1.960528 | 2.401974 | 4.563750 | 10.268437 | 30.805311 |

Each row sums to 50. Every good balanced independently across bands, treasury and recorded loss, with nonnegative holdings. The outbound share incurs homeward road loss/toll; an incoming share is already home and is not charged another journey. Finding 1 is the unavailable-road exception, not a failure of this arithmetic when both roads exist.

The gravity shortlist uses the size product divided by squared straight-line distance (floored at one cell), then computes roads for the top 12 and selects the best road-based gravity scores. The forced large-far-centre regression passes in the full suite. This implements Ben's decision; it remains an estimate-based shortlist rather than a search over every possible road.

## Curation: checked and sound

- Tested holdings per person **0, 1e−8, 0.001, 1/900, 0.01, 0.4, 1 and 100**, including population normalization and the zero-population denominator safeguard. Effective tool-rate multipliers were **0.1** through the floor boundary, **0.5** at 0.01, **0.9756098** at 0.4, **0.9900990** at 1, and **0.9999000** at 100.
- With nonnegative holdings, positive `CURATION_HALF` and the declared floor in [0,1], the multiplier stays between the floor and 1. Wear is nonnegative and no greater than ordinary wear; subtracting it cannot make valid holdings negative. A zero stock loses zero goods despite the positive rate floor.
- Only **fine stone, copper, tin and iron** are curated. Salt, textiles, pottery, gold and shell keep their usual rates. Treasury wear also remains at the usual rates, as documented.
- `CURATION=False` restores the ordinary band wear calculation. The on/off commodity-matrix checks reconciled every band/treasury deduction with `goods_ledger['worn']` for all nine goods. Curation adds no random draws or unledgered quantity flow.
- A **24-tick full-engine replay** with curation on matched digests, complete events, all three trade logs and thinning state after save/load and a cleared route cache, with no food/goods invariant failures. The formula and parameter values remain starting assumptions, not measured use-lives.

## Knockout fairness and the first-arrival interpretation

The described design is a valid paired knockout **if** both branches load the identical year-9,700 checkpoint/RNG state, use the same post-fix code and other parameters, and run 300 years with only `CURATION` changed. In code, that flag selects only the wear modification; later differences in supply, partner switching, cargo allocation and population can be legitimate consequences. Neither identical future draw counts nor identical populations are required once states diverge.

The repository provides the results table, but not paired checkpoint hashes, run manifests or the private outputs. I therefore cannot independently certify that the actual two runs met those starting/configuration conditions. I did not rerun 300-year histories. The reported table's approximate boosts are arithmetically consistent: **4.29× at 8 cells, 105.6× at 12 and 323.5× at 14**. Holdings per person remain a different measure from archaeological chipped-stone shares.

The stockout reading is **not a direct explanation for a band whose `goods_reached` flag was already true**. Wear never clears that flag, so replenishment cannot make another first arrival. There are better candidate mechanisms, both reproduced by changing only wear in controlled same-input cases:

1. **Inheritance changes which first reaches are recorded as exchanges.** Starting with 0.0024 fine stone at a parent, ordinary wear leaves 0.00192; curated wear leaves 0.002352. A half-share daughter inherits **0.00096 off** or **0.001176 on**, across the 0.001 cutoff. Subsequent exchange records **one** arrival off and **none** on, although the daughter's final stock is higher on (**0.26963 versus 0.26750**). The on daughter was already marked reached from inheritance before exchange. The statistic counts recorded exchange arrivals, not every way goods reach new bands.
2. **Protected tools can crowd out other cargo.** With a binding two-unit trader load, retained fine stone took a larger cargo share. A controlled textile delivery was **0.00104338 off** but **0.00096318 on**: one crossed the first-arrival cutoff and the other did not. Textiles themselves were not curated. More tools do not guarantee earlier first arrival of every other good.

These demonstrate mechanisms, not attribution of the private totals **4,056/5,701**. Disaggregate those events by good, route and new-band/inherited history before explaining the difference. Topology and demographic changes may contribute too. The positive wear floor also means the extreme tail retains positive wear; finite-distance flattening does not establish a permanent plateau or historical calibration.

## Validation

**130 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **947.48 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts/oracles/output are under uncommitted `reviews/scratch/017*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
