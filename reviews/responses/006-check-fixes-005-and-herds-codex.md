# Review 006: fixes for 005 and herd settings

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** `main` at `2cd4a36`, from `0fe3bf8` (review 005 fixes) through the herd-setting decision and request 006. Read with Claude's response to 005, the M4 build notes and the existing design/specification and M3 decisions reviewed in 005. No implementation files changed and no gate-length simulation run.

**Result:** all four original reproductions now behave as intended. Two related holes remain in the group-separation fix. The herd formula and the calibration figures check out; the new regression test detects the particular changes it exercises.

## Findings

### 1. Group fission bypasses the new polity and herder separation

- **Where:** `origins/sim/bands.py:73–77,104–122`, `fission_and_merge`'s `group_at` index and direct `groups.transfer` path.
- **What is wrong:** Consolidation now distinguishes herders and polities, but group fission still indexes destinations only by `(cell, farming)`. When an existing group occupies the chosen destination, people transfer straight into it without inheriting the source's skills, herder status or polity; the corrected consolidation helper never gets an opportunity to reject that combination.
- **Why it matters:** The same loss of knowledge and unrecorded political transfer identified in 005 still occurs when groups spread. This path explicitly claims to be equivalent to creating a daughter group and consolidating it; after the fix those operations are no longer equivalent. The path predates this review's commits: this is an incomplete fix, not a new regression caused by the changed key.
- **How sure you are:** Certain in the short reproduction; frequency in gate histories is unmeasured.
- **How to see it:** In `World.new(1, 1, generate(1))`, fold a 30-person crop band and a herding band into groups. Put the crop group at cell 21890 and the herding group at cell 2; set both farming shares to 1 and `village=True`. Give the crop group grain skill 3 and destination grain suitability 1; give the herder goat skill 3, goat suitability 0.1 at home and 1 at the destination, and `herder_since=400`. Set the herding group's age/sex counts to 201 adult men, just above `GROUP_FISSION_SIZE=200`, and put each band in its own polity. Other farming suitability is zero. Call `bands.fission_and_merge` with the world's unchanged fission generator. Observed sizes: **crop 30 → 140, herder 201 → 91**. The crop band retains polity 0 and goat skill **0**, while the source retains polity 1. No fission, alliance, conquest or social-merge event records the 110-person transfer. People and combined store/crop totals are conserved.

### 2. “Ever herded” is still being used as a current way of life in consolidation

- **Where:** `origins/sim/bands.py:217–226`; compare `origins/sim/pastoral.py:48–54,81–88` and `origins/sim/farming.py`, `ensure`.
- **What is wrong:** The new `herder` key tests `herder_since >= 0`, a historical marker that is never cleared when a people turns to crops and is inherited by daughters. A present crop farmer that herded in the past therefore shares the key of a present herder, so their groups still consolidate and retain only the earlier band's skills.
- **Why it matters:** Seasonal movement can still erase an actual herding group and its domestication knowledge. Conversely, present crop groups with different herding histories stay separate indefinitely even when their current farming status and polity agree. The build notes already identify the historical/current distinction for `herders_alive`; using the same marker in the new consolidation key makes it affect simulation behaviour too.
- **How sure you are:** Certain in the short reproduction.
- **How to see it:** Repeat 005's two 30-person farming-group collision, with both autonomous. The earlier group has `herder_since=100`, grain skill 3 and sheep skill 3; at the destination grain value is 1 and sheep value 0.1, so animals supply only **9.1%** of its farming value. It retains its earlier herding knowledge but is now crop-dominated. The incoming band has goat skill 3, no crop skill, and moves from goat value 0.1 to 1, recording its first herding move at tick 400. After `pastoral.move` and `consolidate_groups`, the incoming herder has ended and the crop-dominated band has **60 people**, still with goat skill **0**. Both keys said `herder=True`, despite their different current ways of life.

## Verification of the four original fixes

| Original reproduction | Result on current `main` |
|---|---|
| 30-person herder moves onto 30-person crop group in another polity | Both survive separately, 30 people each; identities and population totals preserved. Same-key groups still consolidate. Findings 1–2 describe additional cases. |
| 30-person herder considers a cell with 3,000 people farming share 0.49 | It now stays home: seasonal farm food remains **4,106.25**, instead of moving and falling to 2,190. The destination counts 1,470 farming-person equivalents, and home/destination/update arithmetic uses the same units. |
| Ended polity with a living individual seat and 100 years left on its memory | Seat stays individual under forced folding pressure, just as with the polity still alive. |
| First village vacates cell 2; later village seeks that land in the same `_flight` call | Later village reaches cell 2 immediately; blocked count is zero. An additional case with the seat still in cell 2 correctly leaves it closed after another member departs. |

The people × farming-share crowding is an estimate of work, not the actual age/specialist-adjusted seasonal effort; Claude's response explicitly acknowledges that limitation. The omitted-part-time-farmer error from 005 is fixed.

## Herd formula: checked and sound

Let `a` be the animal share and `H = LAND_HERDS`. The multiplier is

`1 − a × (1 − H) = (1 − a) + a × H`.

Thus crop-only villages retain the full land advantage; animal-only villages get `H` of it; mixed villages receive the weighted combination. With the approved `H=0`, animal shares 0, 0.25, 0.5, 0.75 and 1 give factors **1, 0.75, 0.5, 0.25 and 0**. With `H=1`, every factor is 1.

I exercised the actual `surplus.yearly` calculation with fixed positive household wealth, fixed crowding, and herd growth/luck disabled to isolate land drift: all 15 combinations of those five animal shares and `H` in {0, 0.5, 1} matched the expected wealth changes. Because the factor is constant within each band, the subsequent wealth-weighted centring also scales by that factor. `params.py` has the approved `LAND_HERDS=0` and `HERD_GROWTH=0.005`.

## Calibration: figures independently reproduced

Source: [GitHub run 43405974869](https://github.com/b392da-sketch/origins/actions/runs/43405974869), commit `28bb6c8abfa327dd274aa5de2d0fb569b118190d`. Downloaded its three individual result artifacts; each JSON was byte-for-byte identical to the corresponding published `results/m4a-herd-f/` file on `gate-results` at `77d7d674c64e5d33c08e82cb6c942b8fa832dbe6`. The run's request sets `HERD_GROWTH=0.005`, `LAND_HERDS=0`, and 1,000 years after the first village. The simulation code matches the reviewed code; the run's different parameter defaults are overridden by the request.

For each JSON, select `gini_log` rows whose animal-share column (index 7) exceeds 0.5; take the median of the Gini column (index 2). For the bracketed figure, further select crowding column (index 6) equal to zero.

| History / artifact ID | Herding records | Median Gini | Uncrowded records | Uncrowded median |
|---|---:|---:|---:|---:|
| Planet 1 seed 5 / 14031158321 | 5,987 | **0.4949** | 1,107 | **0.4915** |
| Planet 4 seed 10 / 14035343100 | 5,996 | **0.48855** | 3,006 | **0.4500** |
| Planet 5 seed 7 / 14032455101 | 5,991 | **0.4967** | 625 | **0.4804** |

These round to the build notes' **0.49 (0.49), 0.49 (0.45), 0.50 (0.48)**. Every history has 6,000 sampled inequality records in total. The minimum animal share among the selected rows is 0.944, 1 and 0.87 respectively, so using the pastoral threshold of 0.7 instead would select the same records. These are medians of sampled village records with at least three households, not population-weighted medians or a census of pastoral societies; logs are sampled every ten years, thinned, then capped at 6,000 in `g2.finish`.

The files report completion at years 13,273, 11,356 and 16,360, exactly 1,000 years after their first villages, zero accounting failures, zero final chain loops and 400/400 sampled polity references resolving per history. Those checks retain the sampling/end-state limits discussed in the M3 review; they do not rule out findings 1–2. The settings and comparison target are tunable assumptions, not established historical facts.

## Regression test and other checks

- **`tests/test_m3.py::Review005` is a real regression check:** it passes on current code and fails at line 120 when the pre-fix `consolidate_groups` from `23e95a3` is substituted in memory. Independently omitting just the polity component fails at line 120; omitting just the herder component fails at line 124. No source files were modified for these substitutions, and none of these runs skipped.
- **Its scope is narrow:** it calls consolidation directly and sets the historical marker manually. It does not cover fission transfers, former herders, or ensure that equal-key groups still merge. Its initial 20-year simulation and `skipTest` fallback also make it dependent on the fixture continuing to provide two individual bands; that is a coverage limitation, not an observed failure on the reviewed revision.
- **Group counts and foragers:** for a fixed cell/polity the key permits at most three consolidated groups: non-farmers, farmers without a herding history, and farmers with one. There is no new unique group key per band or date, so this does not create an unlimited accumulation of equal-key groups. Foragers with different `herder_since` values still merge when their polity agrees. Different polities are now deliberately kept separate, including among foragers; this is consistent with preventing representation changes from transferring political membership. The inappropriate split of current crop groups by historical marker is finding 2.
- **Replay and bookkeeping:** the herder round-trip, 12-tick continued replay, early disk-event freezing, unchanged random streams during pastoral movement, store preservation, yearly `still_years` reset, and flight/herding cause-resolution checks from 005 still pass. Standing crops travelling with bands remain Ben's explicitly accepted abstraction; no new design question is raised.
- **Python:** all `origins/` source parses with the Python 3.10 grammar. Runtime verification here uses Python 3.12.14 and NumPy 2.3.5; an actual 3.10 interpreter was not used.

## Validation

**50 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **351.46 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. The deliberately failing old-code/key-removal runs above were separate, successful checks of the regression test's sensitivity. Focused scripts and extracted result files are under uncommitted `reviews/scratch/`. Only this review and `reviews/LOG.md` are committed.
