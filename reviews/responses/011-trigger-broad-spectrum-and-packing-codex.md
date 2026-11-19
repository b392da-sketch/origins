# Review 011: farming trigger, broad-spectrum food and gate packing

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** pulled `main` to `4a65922`, then fast-forwarded to `eaea8fb` before committing (only additional build notes; implementation unchanged); reviewed the requested changes from `7649b88`, Claude's response to 010, the farming-trigger proposal and the specified M4 build notes, under `AGENTS.md` and the existing design/milestone rules. Only review files changed; no gate-length run started.

**Result:** the five review-010 fixes and both subsequent decisions check out. Three findings follow. Broad-pool accounting and ordinary save/replay pass. The quoted planet-wide tending rates could not be independently reproduced from the available inputs; see the arithmetic section.

## Findings

### 1. A forager that has just moved still qualifies as a settled builder

- **Where:** `origins/sim/technology.py:225–230` (`_settled`), `foraging.move`, and `farming.yearly:223–224`; phase order in `origins/engine.py`.
- **What is wrong:** `_settled` trusts `still_years`, but food movement updates the trail without resetting that counter. It is corrected only by annual farming, in quarter 3. Technology is evaluated in harvest quarter 2, before that correction.
- **Why it matters:** A formerly sedentary forager can practise or acquire building techniques after leaving its settlement, despite the approved requirement to stay in one place for 20 years. Scalar and vector prerequisites agree on the obsolete answer. Clearing the technology cache does not correct the underlying counter.
- **How sure you are:** Certain.
- **How to see it:** On planet 1, set a forager's farming share to zero and `still_years` to 20 at tick 100. Put ordinary stock 1 at cell 2 and 1,000,000 at adjacent land cell 21890, then call the real `foraging.move`. It moves to 21890 and records trail entry `(100, 21890)`, but `still_years` remains 20. Both `prerequisites_met(stone_building)` and `_possible` return true. A move in quarter 2 similarly precedes that year's technology phase and the counter reset.

### 2. One failed packed worker loses its healthy siblings' results and continuation artifacts

- **Where:** `gates/run_job.sh:35–43`; `.github/workflows/gate.yml:60–72` and the corresponding continuation upload steps.
- **What is wrong:** Any worker returning nonzero makes the shell exit before copying completed results into `out/`. The workflow's result and checkpoint uploads also require step success, so neither runs after that failure. Continuation then treats the missing checkpoint artifact as nothing to continue.
- **Why it matters:** Packing expands a single history's failure to other histories on its runner: completed sibling results and valid unfinished sibling checkpoints disappear with the runner. These histories are absent from the gathered evidence, even if their own processes succeeded.
- **How sure you are:** Certain for the shell reproduction and workflow conditions; no remote failure was induced.
- **How to see it:** Run the actual shell script in an isolated directory with three short worker stubs: `1:1` writes a finished result, `1:2` exits 7, and `1:3` writes a valid checkpoint triplet. The parent exits 1, leaves `run_w1_s1.json` outside `out/`, and leaves the third history's checkpoint on disk. Neither artifact upload can preserve those files after the failed step. In the successful control, two finished results are published, only the unfinished history resumes in stage 2, and its checkpoint is removed on completion.

### 3. Abundance-driven tending can be recorded as hunger or crowding

- **Where:** `origins/sim/farming.py:229–250` and `_first:337–346`.
- **What is wrong:** The transition uses the maximum of pressure and the species-specific abundance floor, but the cause selects abundance only when both pressure components are exactly zero. Positive pressure below the floor is therefore named as the route even when the floor enabled the successful draw.
- **Why it matters:** The recorded cause misidentifies why farming started, distorting comparisons of the proposed pressure and abundance routes.
- **How sure you are:** Certain.
- **How to see it:** Use wild grain with suitability 1, 20 settled years after the annual update, zero crowding pressure and margin 1.594. Hunger pressure is 0.01; the abundance floor supplies 0.1. A farming draw of `2.5e-7` succeeds against the actual probability `5e-7`, but would fail against hunger alone (`5e-8`). Skill becomes approximately 0.0005, yet the event says “it gathered 1.59 times its food needs (pressed for food)” and omits the abundance route. The same mismatch applies to weak positive crowding below the floor.

## Review-010 fixes and decisions: checked and sound

- The 20-child cordage source no longer teaches the 40 adults; zero-skilled sources are excluded from contact and best-practitioner calculations.
- The equal-value crop/herd fixture now gives **150 herd + 225 standing crop** with the plough, versus **150 + 150** without it. Actual annual work choice agrees with the harvest's 0.5 animal mixture and weighted worker multiplier 1.25.
- Inherited writing gives the daughter capacity multiplier **1.6** immediately and after reload. Annual goat domestication changes milking quality from **0 to 1** before work choice.
- A controlled two-settlement founding conquest has load **4.4938347**, below technology-adjusted capacity **4.8** but above bare capacity **3**; `_room_for` now admits it.
- **15 adults, including 3 specialists, give 6 skilled practitioners.** Individual/group adult boundaries and the isolated near-mastery gain of approximately 0.0005 remain correct.
- On a two-sea-cell route, voyage draw 0.4 fails at sail quality 0.25 and succeeds at 0.75. Both use two crossing draws. Corresponding one-sea routes succeed at both qualities with only the original attempt draw.

## Other checks and limits

- Scalar/vector prerequisites matched in **2,700** comparisons covering farming-share and 19/20-year settlement boundaries. Finding 1 concerns stale input, not a disagreement between implementations.
- A shared-cell fixture with gear access **[1, 0.5, 0]** harvested **100 ordinary + 199.994003 broad** food. Each band's allocation matched ordinary effort share plus broad reach share; the ungeared band received no broad food. Broad yield respected the remaining-effort limit at return 0.3. Harvest equalled depletion, food balance passed, and regrowth ledgered the net changes of both pools.
- Wet/dry gear access matched the weighted practised qualities divided by the local full-gear pool share. Missing prerequisites still remove access through practised-quality checks.
- Removing `stock_broad` from an otherwise valid save initialized it to `broad_max` at the restored season, food modifier and hazard level. A **16-tick** full-engine comparison with active techniques and mixed subsistence matched digests and complete events, with no conservation failures.
- Crowding matched an explicit cell-plus-neighbours population/capacity sum on every planet-1 cell. It uses unaided capacity, not stock, gear or stores.
- Pure hunger, pure crowding and zero-pressure abundance produced the appropriate first-tending labels. Abundance failed below suitability 0.5, without local wild presence, and below 20 settled years. The floor is evaluated separately per species. Farming draws remain on the farming stream with eligibility/count determined by state and earlier draws; saving does not introduce an extra draw.
- With distinct history keys, packed workers have separate result, checkpoint, planet and log filenames. The successful shell control continued only the checkpoint-bearing history and removed its completed checkpoint; the planner preserved the requested history/kind set. Finding 2 is the failure-path gap.

## Tending-rate arithmetic

For direct new tending starts in a fixed annual state, sum over eligible **band–species pairs** with skill zero, local wild presence and sufficient still years:

`lambda = 5e-6 * sum(suitability * max(hunger, crowding_pressure, eligible_abundance_floor))`.

The old trigger uses hunger alone. Thus 0.0002 and 0.0004 starts/year correspond to weighted opportunity sums **40 and 80**. Their reciprocals are correctly **5,000 and 2,500 years**. Linearity of expectation makes the sum valid; for such small rates the probability of at least one start is approximately the sum.

I found neither the referenced planet-3 year-8,500 save nor a per-band/species calculation in the available repository or scratch artifacts, so **the sums 40/80 and the quoted snapshot rates remain unverified**. Their reciprocals describe waiting under frozen conditions, not an estimated waiting time from the first people: population, movement, margins, settlement duration and eligibility evolve. A calculation of the next *world-first* event must also exclude species whose first tending is already recorded. The later technology-off outcome is not itself a contradiction: more eligible draws change the farming stream's subsequent assignment to events.

## Design questions for Ben

No new design change proposed. Whether tending should be less rare remains the build notes' existing gate question; the arithmetic above does not settle it.

## Validation

**85 tests passed**, one installed AnyIO pytest-plugin deprecation warning, in **547.92 seconds** (`python -m pytest -q -p no:cacheprovider tests`). Focused reproductions, worker stubs and outputs are under uncommitted `reviews/scratch/011*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
