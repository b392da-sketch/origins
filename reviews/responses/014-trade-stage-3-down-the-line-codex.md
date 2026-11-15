# Review 014: down-the-line exchange and the review-013 fixes

**Reviewer:** Codex, 15 November 2026.

**Reviewed:** pulled `main` to stage-3 commit `6d55f51`, including fixes from `d2c36b7`, then fast-forwarded to `222833e` (documentation/project-principle updates only; implementation unchanged). Read Claude's response to 013, the requested build notes and the existing project/design rules under `AGENTS.md`. The newer stage-4 decisions are context, not an implementation reviewed here. No implementation changes or gate-length runs.

**Result:** the four review-013 fixes and the partnership teaching record check out. Three findings follow: simultaneous exchange can amplify inequality at high-degree receivers, “first arrivals” repeat after wear, and exchange logs hide transit flows. Per-good conservation, nonnegativity, the outgoing cap, pair geometry and current-format replay pass focused checks.

## Findings

### 1. Many simultaneous inflows can drive a recipient past every donor and away from equality

- **Where:** `origins/sim/trade.py:385–395`, pairwise proposals followed by outgoing-only scaling.
- **What is wrong:** Each pair independently proposes a fraction of its equilibration amount from the same starting stocks. The combined inflows are not bounded by the receiver's approach to equality. The half-stock outgoing cap prevents negative stocks but does not stabilize this simultaneous equilibration.
- **Why it matters:** A well-connected recipient can become much richer per person than all its suppliers, and subsequent updates can keep reversing the gradient. This is an artifact of combining the pair updates, rather than the stated partial movement toward equal holdings per person; it can distort the hub behaviour that later trade is meant to measure.
- **How sure you are:** Certain for the numerical counterexample. This is a dense-network case, not a claim that it occurred in the private planet-3 trial.
- **How to see it:** Put **101 equal-sized bands** on one exchange cell, one with zero fine stone and the other 100 with **100 each**, with no transport bonuses. At `DTL_RATE=0.1`, every donor gives the poor band 5, well below its own half-stock cap. The recipient ends with **500**, while every donor ends with **95**; per-person ordering has reversed and holdings variance increases **98.03 → 1,607.93** (equal populations make the variance comparison equivalent per person). With fixed population/topology and exchange alone, its next holdings are **250, 125, 62.5, 246.875, 123.4375, 61.71875…**. Total stock remains 10,000 and no invariant fails. The same **500/95** result also reproduces with **101 individual bands (3,030 people) across a central cell and its six neighbours**, after the real fission/merge phase retains all of them; food/people/goods checks pass.

### 2. The same band/good can have a “first arrival” every year

- **Where:** `trade.down_the_line:402–422`, especially the current-stock threshold at line 403.
- **What is wrong:** Arrival detection tests only this year's holdings against `ARRIVE_MIN`; it does not retain whether that band already received the good. Wear can put an already-reached band below the threshold between exchanges, causing another event that says the good “first reached” it.
- **Why it matters:** Arrival counts and dates do not reliably measure new diffusion. Repeated threshold crossings inflate the apparent number of newly reached bands and generate additional events/work at the low-stock frontier.
- **How sure you are:** Certain.
- **How to see it:** Use two equal-sized neighbouring bands, add **0.008 salt/year** at the source, run normal down-the-line exchange and then the ordinary **50% salt wear**, recording both source production and wear. Over 20 annual steps, the same recipient produces **18 `good_arrived` events**, one every year from fixture years 27–44. Its final post-wear stock is about **0.0007273**, below `ARRIVE_MIN=0.001`, so the next exchange is treated as another first arrival. Conservation passes throughout.

### 3. The exchange log measures net change, omitting goods passed through a band

- **Where:** `trade.down_the_line:400–401` and `424–426`.
- **What is wrong:** `received` and `given` accumulate the positive/negative parts of each good's **net band delta**, rather than the actual incoming/outgoing pair flows. A band can receive and pass on the same amount of a good yet have no log row at all, even before thinning.
- **Why it matters:** The advertised units received/given understate trade volume and hide precisely the intermediaries and hubs needed to assess exchange along a chain. Global moved ledgers remain correct, so conservation does not detect this measurement error.
- **How sure you are:** Certain.
- **How to see it:** On a three-band line with equal populations, start fine-stone holdings **[100, 50, 0]** and land pairs A–B and B–C. Exchange moves **2.5 A→B and 2.5 B→C**, leaving **[97.5, 50, 2.5]**. The moved-in/out ledgers each increase by **5**, but the log has only A giving 2.5 and C receiving 2.5. B's actual **2.5 received and 2.5 given** are absent. The log cap is not reached in this reproduction.

## Review-013 fixes: checked and sound

- The 128-row stage-1 save now retains band 127's entire **[10…90]** inventory and its ledger while adding empty partnership storage. Small legacy saves also retain goods and previous RNG streams.
- The real food move **829 → 13004** outside recipient cell 12954's two-ring reach now yields **zero partner help**, before annual link cleanup.
- The 100-shell gift fixture now adds one `gift_exchange` event recording **5 shell** from the correct band, with the partner identities and resolving causes; inventory and moved ledgers agree.
- The behavioural three-group consolidation fixture now removes the B–C link from both absorbed bands immediately. This reruns the actual consolidation rather than inspecting its source text.
- A lesson accepted only because its selected teacher is a partner now has **`route="partnership"`**, closeness 1 and a cause naming the partnership. Selecting the nonpartner still fails the controlled 0.9 lesson draw; disabling trade removes the boost.

## Pair geometry and flows: checked and sound

- Synthetic undirected coastal geometry with multiple sea paths produced each band pair once. Same-cell and adjacent-land pairs remained available without sail; across-one-sea-cell pairs required positive **practised** sail at either endpoint. Duplicate sea paths collapsed, and adjacent pairs were not also emitted as sea pairs.
- Frozen pre-exchange stocks prevent same-year relaying within this operator. Flows are signed toward equal **per-person** holdings: with 100/0 stocks and populations 10/30, the unboosted pair transfers **7.5**, not 5.
- Sole-giver controls with **21 recipients** exercised both positive and negative pair orientations. Each good's giver retained exactly half to floating precision; recipients each got **1/42 of the original stock**. Random mixed-direction cases also conserved each good and remained nonnegative. Finding 1 is compatible with these bounds.
- Reversing goods iteration and shuffling pairs preserved holdings to **1e-12** in the tested cases. Floating sums are not promised bit-identical under arbitrary pair permutations, and diagnostic event/list order follows iteration order. The normal fixed ordering remains deterministic for replay.
- Largest-donor arrival selection uses the actual signed, scaled flows; an unequal-donor case with the larger contribution on a reverse-oriented edge named the correct neighbour, and its cause chain resolved. Finding 2 concerns whether it is a first arrival, not this donor selection.
- Exchange itself advanced no RNG streams.

## Transport judgement

Using the better **practised** endpoint quality is a reasonable implementation of transport being available to serve a pair, consistent with this stage's stated rule. It does not add both endpoints' quality for the same technique. Different techniques may be supplied by different endpoints.

Controlled equal-population 100/0 cases transferred approximately **10** with the selected pack/cart bonuses, **7** with the canoe bonus alone, **10** when land transport was better on a wet pair, and **3.75** across the sea with sail qualities 0.25/0.75. Wet links use the better land/water multiplier; sea links scale by the better sail quality. These coefficients are starting values. Labour/transport costs remain deferred to stage 5 as Ben decided; no new design change is proposed here.

## Logs, saves and replay

With a test log cap of **4**, repeated exchange increased the sampling stride; after saving and continuing, both worlds ended with identical log rows and thinning state (**48 offered rows, stride 16, 3 retained rows**), goods, events and digest. I compared `exchange_log` and `log_strides` explicitly: the digest alone does not cover this diagnostic log. Removing the new trade metadata loaded an empty log while retaining goods. A **24-tick full-engine** comparison with active links/goods also matched complete events, diagnostic logs, strides and digest, with no food/goods invariant failures.

These checks validate persistence and deterministic thinning, not the log's interpretation as gross received/given; finding 3 remains. The thinned log is a sample, not a complete history of every band's transfers.

## Speed

Short synthetic benchmarks used actual planet-1 geometry, uniformly sampled land locations, cached practised qualities and population counts, and positive stocks of all nine goods. They are not full simulated-year or gate timings.

| Bands | Occupied cells | Pairs | `_pairs`, median of 3 | Whole exchange with existing stocks |
|---|---:|---:|---:|---:|
| 2,000 | 1,848 | 1,048 | 0.0067 s | 0.015 s |
| 10,000 | 6,780 | 27,105 | 0.032 s | 0.055 s |
| 40,000 | 11,491 | 434,242 | 0.16 s | 0.44 s |

The cell loop visits occupied cells. Pair generation is modest here; dense cells still generate all qualifying band-to-band pairs, so cost grows with occupancy as well as band count. The 40,000-band pair arrays alone occupy about **9.94 MiB**, excluding temporary Python lists.

An arrival-heavy 40,000-band case, with half the inventories initially zero, took **3.86 s** and generated **179,910** arrival events; the benchmark counted events without storing them on disk. Thus first-arrival scans/record construction can cost much more than `_pairs`, and this is not a full EventStore/runtime estimate. Finding 2 can make that work recur.

I did not reproduce the private year-8,500 snapshot or certify its fall-off table. The newer notes correct spacing to about 60 km and distinguish holdings per person from archaeological chipped-stone shares; the approved stage-4 mechanisms remain for the next review.

## Validation

**101 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **833.99 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused reproductions and benchmark output are under uncommitted `reviews/scratch/014*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
