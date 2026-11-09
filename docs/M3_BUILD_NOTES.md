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
