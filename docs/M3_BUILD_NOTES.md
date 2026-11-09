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
