# M3 build notes

Numbers in `params.py` are tunable starting values, not facts.

## Step 1: every machine builds the same planet (9 November 2026)

**Cause found.** Eight cells of the geodesic grid lie exactly on latitudes 27° and 30° (and two on the poles). The rainfall model switches wind direction at 30° (`alat < 30`). The latitude comes from `arcsin`, whose last digit differs between processors, so on some machines these cells counted as tropical and on others as mid-latitude. Their upwind neighbour changed, and the change was carried downwind. That explains the planet-4 differences seen in the M2 gate: rainfall differing by up to 188 mm in some cells, and biome and capacity in 2.

**Fix.** World generation now rounds after every step whose last digits can differ between processors:
- latitude and longitude, to 1e-9°;
- elevation, to 1 cm, since powers differ between processors;
- temperatures, to 1e-6 °C;
- the upwind choice and the moisture carried, to 1e-9;
- rainfall, to 0.001 mm;
- plate and region assignment, which use matrix products, to 1e-9;
- convergence and seasonal productivity, to 1e-9.

Values that sit exactly on a threshold now fall on the same side on every machine. A difference can survive only if a value lies within about 1e-15 of a rounding boundary.

**A second cause, found by the new workflow.** After the first fix, planet 1 still differed on half the machine types: elevation in 15–28 cells by up to 500 m, with knock-on changes to rivers and capacity. The grid normalised each new vertex with a dot product (`p @ p`), which NumPy hands to the BLAS library; some BLAS builds fuse the multiply and add, so the grid points themselves differed in the last digit, and the noise and plate boundaries amplified that. The dot product is now written out as plain multiplications and additions, which every machine computes the same way.

**Checks.**
- The five planets are now bit-for-bit identical with all of NumPy's processor paths here (AVX-512, AVX2 and baseline); before the fix they differed.
- `tests/test_planet_identity.py` holds the exact digests.
- A new workflow, `.github/workflows/planets.yml`, runs that test on Linux (two Ubuntu versions), Linux on ARM, Windows (as on Ben's computer) and macOS on Apple silicon, with Python 3.10 and 3.13. It runs on every change to world generation and weekly, and it keeps planet 1 from each machine so any difference can be traced. After both fixes, all 10 machine and Python combinations build identical planets.

**Consequence.** Every planet changes slightly, so saves made before this change no longer load ("planet fingerprint mismatch"). G3 re-checks M0–M2 behaviour on the new planets.

## Step 2: speed pass (9 November 2026)

**Where the time goes** (planet 4 at year 6,000: 567,000 people in 5,567 bands, mostly folded groups, no farming yet; sampled with py-spy and cProfile). The work is spread across many systems, and there is no single bottleneck:

| Share | System |
|---|---|
| 28% | splitting and merging bands |
| 14% | deaths in folded groups (one binomial draw per age and sex per group, every season) |
| 12% | partnerships |
| 10% | farming choices |
| 6% | births in groups |
| 6% | foraging and eating |
| 5% | hazards |

One structural cost: several systems built arrays with one entry for every band that ever existed (1.2 million by then), not just the 5,567 living ones.

**Changes, all with identical results** (same digests after 5 years from saves at years 2,000 and 6,000, and on a world with 400 bands forced to farm):
- **A compact index of living bands** (`World.live_index`, `World.live_sizes`). Foraging and eating, food for groups, and splitting and merging now work on one entry per living band.
- **Group deaths and births** read band cells and margins through that index, instead of looking each band up one at a time.

**Result:** planet 4 at year 6,000 runs at 1.35 s per simulated year, down from 1.64 (about 18% faster), with the same results. That is well short of the target of half. The rest of the cost is the per-group, per-season random draws for deaths and births, and the Python loops over thousands of groups. Halving it would mean changing how those are drawn: for example, yearly rather than seasonal demography for folded groups. That changes the random draws, though not what they mean, and it is a design choice for Ben (Design Draft section 3 lists coarser steps for wandering bands as PROPOSED).

**What makes the long M3 histories possible regardless:** the gate workflow now has five stages in a row instead of three (each up to 4 h 30 min of computing on a fresh machine, carried by checkpoints that include the planet), so a history can use up to about 22 hours of computing. Public repositories have no Actions minute limit.

## Steps 3 and 4: leaders, polities, institutions and break-up (9 November 2026)

`origins/sim/polity.py`, run yearly after the harvest, following surplus. Everything in it is data plus a system, as the rules require.

- **Data:**
  - `Polity` records: seat, leader, institutions, tier, load and capacity.
  - Per band: `polity_of` (which polity) and `polity_via` (the settlement it is attached through).
  - A new random stream, `polity`, appended at the end of the list.
- **Joining:** an autonomous village, each year with a small chance, considers villages within two rings. It accepts the one whose leader has the greatest standing above its own (surplus in person-years plus specialists), discounted by cultural difference (customs, and shared word roots where the languages differ). Accepting an autonomous village founds a new polity seated there. A daughter settlement stays in its mother's polity, attached through her.
- **Levels of rule:** each member is attached through the seat or through another member. The depth of that tree is the number of levels of rule. The tier is measured from it, never assigned:
  - simple chiefdom: three or more settlements, one level;
  - complex chiefdom: two levels;
  - state: three or more levels, with officials.

  How deep a polity can grow depends on its institutions: one level without tribute collectors, two with them, and up to four with officials.
- **Tribute:** each member sends 30% of its surplus toward the seat, and a sub-leader keeps 30% of what passes through it. The food moves between stores; none is created or lost.
- **Load and capacity:**
  - **Load** is summed over members: √(size/150) × (1 + distance/4 cells) × (1 + 2 × cultural difference).
  - **Capacity** is 3 × (1 + the gains of the institutions held).
  - **Institutions** are added in order (council, tribute collectors, law, warriors, officials) when load passes 80% of capacity and the seat has enough specialists to staff one. They are lost when it no longer has. With institutions switched off (the knock-out), none is ever added.
- **Secession:** each member's yearly chance is (0.002 + 0.05 × overload + 0.02 × stress) × (1 + distance/4) × (1 + cultural difference), and law cuts it by 30%. Stress comes from a poor harvest at the seat, a contested succession, or hunger at home. A seceding member takes the settlements attached through it; two or more found a new polity.
- **Succession:** a leader holds the place until death. It then passes by the seat's new custom, "succession" (to a son, to a sister's son, or chosen by the council), which drifts like the other customs. With rival claimants it is contested with chance 25%, 20% or 10% by custom, weakening the polity for five years.
- **Events, each with a cause chain:**
  - polity founded, joined, secession, polity ended, seat moved, succession;
  - institution founded and lost;
  - the world's first simple chiefdom, complex chiefdom and state.
- **Logs for the gate:**
  - every 10 years, each polity's settlements, people, depth, load, capacity, institutions, tier and seat;
  - secession counts by overload.
- **Saves:** schema unchanged in form. Saves from before the custom was added gain it, at variant 0.

Smoke test (planet 4 at year 2,000, with 600 bands made to farm, over 150 years): 47 polities. By the end there were 8 simple chiefdoms, 4 complex chiefdoms and 2 states. Over the 150 years there were 141 joinings, 34 secessions, 17 polities ended and 35 institutions founded. All cause chains are complete, saves replay exactly, and there were no accounting failures.

Gate G3 machinery: `gates/g3.py` and `gates/g3_report.py`, plus "noinst" jobs in the planner and job runner. The report re-checks M0–M2 by running G2's report on the G3 histories, and has checks 2, 3, 4, 5, 10, 11 and 12 so far. Tests: 45 pass (4 new in `tests/test_m3.py`).

## Step 5: conflict (9 November 2026)

`origins/sim/conflict.py`, run yearly after polities. It uses a new random stream, `conflict`, and a new cause of death, "killed in war". Both are appended at the end of their lists.

- **Sides:** a polity, or a settlement on its own. Forager bands fight too (decision 1A). Members of one polity never fight each other.
- **Reach:** two rings for villages and polities, one ring for foragers.
- **Who weighs war:** each year a quarter of the sides weigh war. A side that does attacks its most tempting neighbour with chance (chance of war) ÷ 0.25. That gives the same chance of war, capped at 0.25 a year, for a quarter of the work.
- **The chance of war:** 0.03 × (1 + 3 × scarcity) × (2 × strength share) × (1 + cultural distance) × (1 + 0.5 × grievance/10, capped at 3) × (1 − 0.15 per cell of distance, up to 2 cells) × 1.5 for a leader in the first three years. Grievance is the killings suffered from that side, decaying 7% a year.
- **Strength:** men of fighting age (16–45) within reach of the target, weighted by distance. Warriors kept by the leader add 50%. Defenders count 1.5 times. The stronger side wins with chance s²/(s² + (1 − s)²).
- **Deaths:** Poisson-drawn, about 0.3 × the fighters × the other side's strength share. They are mostly men of fighting age, recorded as "killed in war", and traced to the war event.
- **If the attacker wins:**
  - it takes 30% of the loser's stores (moved, not created);
  - 5% of the loser's young women and children join the winner's settlement, keeping their own speech (decision 2A);
  - a farming attacker takes the farming village with chance 0.3, and the whole polity if its seat fell. A conquered settlement weighs double on the conqueror's load, fading over a century.
  - a defeated polity carries the stress of a lost war for five years, which raises secession.
- **Logs:**
  - war counts against sides weighed, by scarcity and by distance;
  - a war log;
  - per polity, the number of languages spoken and of conquered settlements.

  An empire is a polity holding conquered settlements of another language.

**Smoke test** (planet 4 at year 2,000, 600 bands made to farm, 150 years): 6,987 wars, 32,612 deaths in war. Deaths in war were 3.7% of all deaths in that time, about 5% of deaths at 15 and over: the low end of the plausibility guide (Bowles 2009 estimates 12–16% of adult deaths among foragers, estimates that are disputed). This is a starting value for G3 to check. With the targets weighed as arrays, conflict adds about 10% to the computing time.

**Gate G3 checks 6–8 added:**
- **6:** war rates by scarcity and by distance. These enter by rule, so the check is of the bookkeeping, as in G2 check 7.
- **7:** war deaths since the first village as a share of deaths at 15 and over.
- **8:** empire duration against mean overextension.

Tests: 46 pass.

## Step 6: inequality that compounds (9 November 2026)

This is option (c) from the M2 gate (M3 decision 3: both mechanisms), added in `surplus.yearly` to each household's yearly change in holdings.

- **Scarce land:** a village's land is scarce from half of what its farmland can feed, and full at what it can feed. In a scarce village, a household's holdings drift up by 0.03 × scarcity × (its holdings ÷ the village mean − 1) a year, capped between −1 and 3. The drift is zero-sum: land changes hands, so what some gain others lose. Households with more land weather bad years and take over the land of those that fail.
- **Breeding herds:** holdings drift up by 0.02 × the share of farming in animals, and their luck spreads twice as widely, so herds breed in good years and die in bad ones.
- **Unchanged:** a new household still takes a 30% dowry from its mother, and holdings are still divided among the children at death. Inequality therefore rises only where compounding outruns division.

All four numbers are starting values; G3 check 9 tests them over thousands of years of farming.

## Step 7: notables stay individual (9 November 2026)

- **What changed:** when the world passes 20,000 individuals and distant bands fold into groups, the seats of chiefdoms and states are no longer folded. A seat that is already a group is unfolded each year, for up to 200 seats, the most loaded first. Their people, with leaders, heirs, households and genealogies, are then followed person by person. Unfolding is M0's existing `groups.unfold`, which recreates people from the group's counts with the same totals.
- **How it differs from the specification:** the specification proposed drawing notables out of their groups one by one. Keeping whole seats individual is simpler and keeps every count exact. The trade-off is that sub-leaders outside the seat, and war leaders of folded groups, are not followed as people.

## Step 8: observatory for M3 (9 November 2026)

- **New map layers:**
  - **Polities:** settlements coloured by polity; seats ringed white, more thickly for higher tiers.
  - **Wars:** wars of the last 30 years drawn from attacker to target, fading with age and thicker with more killed. Conquests are red, successful raids orange, repelled attacks grey.
- **Polity page:**
  - tier and levels of rule; founding, linked to its cause chain; seat and leader;
  - load against capacity; institutions held and not held;
  - settlements by level, with their languages and whether they were conquered;
  - leaders over time, with contested successions marked;
  - a chronicle of its events (successions, secessions, institutions, wars, conquests), each linked to its "why" chain.
- **Elsewhere:** a band's page links to its polity. A Polities panel lists the largest chiefdoms and states, and the header counts chiefdoms and states.
- **Successors:** heirs are now chosen from people aged 20–59 where there are any, rather than the eldest man. With that, the test world's leaders served a median of 10 years. They died of old age (40%), in war (32%), of accident or illness (19%), or in outbreaks (7%), at a median age of 50.

Checked on a test world (planet 4, 600 villages, 150 years): all views render without errors. Tests: 46 pass.

## Tuning after the first trial results (9 November 2026, in progress)

**What the first finished trial histories and a local test showed** (planet 3, with farming started early):
- States formed within decades of the first chiefdom.
- Institutions made too little difference: the largest polity held 11–20 settlements with institutions and 6–14 without.

**Changes, all within the approved design:**
1. **Levels of rule** count only settlements with two or more others answering to them (district heads), not chains of daughter villages.
2. **Institutions are rare discoveries:** under pressure, a polity finds its next one with a 0.2% chance a year. It is 20 times as likely where a polity within three rings already has it to copy (secondary state formation). A copied institution's cause chain names the polity it was copied from.
3. **Institutions matter more:**
   - Without institutions a polity holds about three villages' load.
   - A council, tribute collectors, law and warriors add 1, 2, 1 and 1 times that base.
   - Officials over districts multiply the total by 3, and need tribute collectors and law first.

Being tested locally (1,500 years with and without institutions) before G3.

## Ben, 9 November 2026: open to the graphics card helping

Ben's laptop: an i5-13420H (8 cores, 12 threads), 16 GB of memory, a 2 TB drive and an RTX 3050 with 6 GB. He is open to using the graphics card to speed up the simulation (the display needs none of it).

**Proposed approach, to be brought to Ben as a design proposal when it is worth doing (likely after M4):**
- **An optional array backend (CuPy) for the heavy array work:** deaths and births across many groups, foraging sums, conflict distances. The default stays NumPy on the processor.
- **Two modes, because the graphics card's random numbers and rounding differ from the processor's:**
  - A graphics-card run would be a "fast mode": statistically the same, but not digit-for-digit the same as a processor run.
  - Exact replay and gate runs stay on the processor (GitHub's machines have no graphics cards).
- **Why not now:** most of today's computing time is Python logic per band, which a graphics card does not speed up. It is worth adding once array work dominates, at hundreds of thousands of groups.

## Smooth movement on the map (9 November 2026, Ben's request)

This is display only, in `observatory/index.html`; the simulation is untouched.
- **Gliding:** a band that moves to a new cell glides there with easing: over 5 seconds normally, and 1.8 seconds while fast-forwarding, when many bands move at every update. A move across the map's edge goes the short way round.
- **Spreading:** bands that share a cell are spread around its centre, each at a fixed offset, so a busy cell shows as a cluster.
- **Fades:** new bands fade in, and ended bands fade out over 1.5 seconds.
- **Splits:** a band that has just split off starts at its parent's position and glides out to its own cell. `/api/bands` now gives each band's parent.
- **Clicking** finds bands at their drawn positions.

Cost: about 4–5 ms to draw 1,700 bands in a headless browser here, against the 16 ms a frame has at 60 frames a second. The map animates only while something is moving.

## First trial gate (behaviour 5): results, 27 of 30 histories

Run 42558662526, with the code before conflict, before levels of rule were counted through district heads, and before the institution changes above. Histories ran to 3,000 years after the first village.

| Check | Result |
|---|---|
| 1 | M0 and M1 hold: 18 of 18 survived, no accounting failures, every cause chain complete. G2's "adoption dates" check fails because every one of these 18 histories farmed; it needs the full set. |
| 2 | FAIL: chiefdoms in 18 of 18, and states in 18 of 18 within 225 years of the first village. Too fast. |
| 3 | PASS: secession rises steadily with overload, from 0.4% a year to 15%. Rank correlation per history: median 0.99. |
| 4 | Collapses in every history: as measured then, 2,516 of them, with recovery after nearly all. |
| 5 | FAIL: the largest polity held 18–27 settlements with institutions and 10–14 without. |
| 10 | PASS: 10,800 of 10,800 polity events traceable. |

The local test with the new institution rules (planet 3, 1,500 years of farming) formed no state in 1,500 years. The largest polity reached 13 settlements, against about 8 without institutions. Secession rose from 1.2% a year without overload to 34% at heavy overload.

**Further changes:**
- **A daughter settlement leaves an overloaded polity:** it stays in its mother's polity only while that polity holds less than it can bear. Without institutions, polities had been kept large by their own daughters.
- **The report's collapse measure** now counts only established large polities: those that held 10 or more settlements for at least 50 years and lost half their people within a century. On the first trial that still gives 550 collapses, in every history.

**For Ben at G3:** the specification's mark, collapses in at most 90% of histories, may not fit a world where many polities rise and fall over thousands of years. In the archaeological record chiefdoms rise and fall repeatedly in most regions. This is to be raised with the G3 results, not changed now.

A second trial, with all the M3 code, follows.

## Watching changes nothing (9 November 2026, Ben's decision, option b)

Until now, following a band that was a folded group unfolded it into individuals: it drew random numbers and switched the band to individual rules. The band nearest the one being followed was also never folded, so a history someone watched could turn out differently from one nobody watched. Now:
- **Following** only chooses what the observatory shows and how fast time runs. A folded group is shown as a group.
- **Which bands fold** depends only on the world: those farthest from the seats of chiefdoms and states fold first, or, before any exist, those farthest from the people's first home. The merge rule no longer depends on the followed band.
- **Unfolding** happens only when the simulation itself calls for it (a band becoming a chiefdom's or state's seat). It is now an event with that cause.
- **People brought out of a group** are marked "ancestry unrecorded", on the "why" chain and on their page, and nothing about their past is invented.

Test: two copies of a world, one following a band, give identical digests after 10 years. Tests: 47 pass.

## Leadership follows each people's customs (9 November 2026, Ben agreed)

Until now, a council choosing the head of the richest household chose its man where there was one. That was an assumption built into the code, marked PROPOSED. It now follows custom:
- **A new custom, "who speaks for a household":** the man, the woman, or the elder of the two. It drifts like the others.
- **A fourth succession variant, "to a daughter":** succession through daughters is attested, for example among the Balobedu. Its chance of being contested is 25%, like "to a son".
- **Unchanged:** "to a son" and "to a sister's son" still pass to men, as those customs say. That matches the common pattern in matrilineal societies, where authority passes through the mother's line but is often held by her brothers and sons. Fighters are still men of fighting age, as in most recorded warfare.

Saves from before gain the new custom at variant 0. Tests: 47 pass.

## Planned: comparison with Seshat (for the G3 report)

Every rate in Origins is a starting value. For the M3 gate report, the patterns that can be compared with the Seshat Global History Databank (https://seshat-db.com/) will be: how polity population relates to levels of hierarchy, how long it takes from the first farming villages to the first states, and how often large polities fragment. The comparison will be of shape and order of magnitude, not a fit, since Origins' planets are not Earth.

## Second trial gate: results, 27 of 30 histories (night of 9 November 2026)

Run 42585528434, with all the M3 code as of the early evening: conflict, levels of rule through district heads, institutions as rare discoveries, and daughters leaving overloaded polities. It did not yet have the change that watching changes nothing, or leadership by custom. Histories ran to 3,000 years after the first village.

| Check | Result |
|---|---|
| 1 | PASS: M0–M2 hold. 19 of 19 survived, no accounting failures, life expectancy 26.7–28.0, every G2 check passes. |
| 2 | FAIL: chiefdoms in 14 of 14 histories with farming, but **no state in any**. The first trial's states-everywhere has swung to states-nowhere. |
| 3 | PASS: secession rises with overload, from 1.2% to 15% a year; rank correlation per history: median 1.00. |
| 4 | PASS: collapses of established large polities in 12 of 14 histories, with recovery after 18 of 18. |
| 5 | FAIL: **institutions make no difference**. The largest polity held 14–19 settlements with institutions and 14–19 without. |
| 6 | PASS: war is 3.5 times as likely for hard-pressed sides, and falls with distance. This is by rule, so it checks the bookkeeping. |
| 7 | PASS: deaths in war are 5.6–7.2% of deaths at 15 and over (median 6.7%), at the low end of the guide. |
| 8 | PASS: 6,425 empires. Rank correlation of duration with overextension is −0.63, so overextended empires fall sooner. |
| 10 | PASS: 10,800 of 10,800 polity events traceable. |

**Why check 5 fails:**
- **Institutions stay rare.** Polities rarely gather them: most held none; a few had up to four; none had officials, which is why there were no states.
- **Size doesn't depend on capacity.** Large polities ran at 1–3 times their capacity whether or not they had institutions. They stayed at about 17 settlements because conquest kept adding villages as fast as overload drove them out.

**Changes:**
- **Annexing needs room:** a polity annexes a conquered village only while its load is below its capacity. Otherwise it plunders and leaves, as conquerors without the means to govern did.
- **Institutions are found more readily:** a pressed polity finds its next institution with a 1% chance a year, up from 0.2%, and 20 times as fast where a neighbour has it.

Being tested locally, 1,250 years with and without institutions, before the full G3 gate.

## Local tests of the last changes (night of 9–10 November 2026)

Planet 3, from its first farming village, 1,250 years, the same world with and without institutions:

| Version | Largest polity, with institutions | Largest polity, without | States |
|---|---|---|---|
| Annexing needs room; institutions found at 1% a year | 10–13 | 5–9 | one, at year 479 (it did not last) |
| Also: council, collectors and warriors do what the specification says | 13–15 | 6–9 | one, from year 774 (still standing at 1,250) |

Institutions now roughly double what a polity can hold, short of the gate's mark of four times. What limits size is the steady loss of members even without overload (about 1.2% of members a year, after distance and cultural difference), against the rate at which villages join. Over 6,000 years of farming, institutions have far longer to gather and spread, so the full G3 gate is the real test. It is launched now; if check 5 still fails there, that goes to Ben with this analysis rather than more silent tuning.

## G3 run 1: two histories lost at their checkpoints (10 November 2026)

Two of 70 jobs failed: planet 1 seed 3 ("the runner has received a shutdown signal") and planet 4 seed 6 ("lost communication with the server"). Both failed at or just after their 4 h 30 min budget, when the checkpoint is written, so the save most likely exhausted the machine's memory.

**Cause:** the event record. A local farming world (planet 3, year 24,000) held 1.43 million events, 791,000 of them wars, mostly forager raids. As JSON that is 524 MB, and as Python objects several times that. A checkpoint wrote all of it as one giant string.

**Changes:**
- **Saves stream events** to their own file, one per line, so no single huge string is ever built. Older saves still load.
- **War events keep their reasons as four numbers**, and `explain.py` writes out the sentence.
- **A raid driven off with nobody killed** leaves no event; it stays in the war log. Few raids qualify, so this saves little.
- **The gate worker logs memory** every 500 years and at each checkpoint.

The two histories are rerun with this code. The on-disk event store planned for M4 is the full answer.
