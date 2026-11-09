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

**Checks.**
- The five planets are now bit-for-bit identical with all of NumPy's processor paths here (AVX-512, AVX2 and baseline); before the fix they differed.
- `tests/test_planet_identity.py` holds the exact digests.
- A new workflow, `.github/workflows/planets.yml`, runs that test on Linux (Intel and AMD), Linux on ARM, Windows (as on Ben's computer) and macOS on Apple silicon, with Python 3.10 and 3.13. It runs on every change to world generation and weekly.

**Consequence.** Every planet changes slightly, so saves made before this change no longer load ("planet fingerprint mismatch"). G3 re-checks M0–M2 behaviour on the new planets.
