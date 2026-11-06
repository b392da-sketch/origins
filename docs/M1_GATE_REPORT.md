# Gate G1 report — M1 "spreading and drifting apart"

7 November 2026. Specification: `docs/M1_SPECIFICATION_v1.md`. Build notes, including everything tried and changed: `docs/M1_BUILD_NOTES.md`.

## Summary

**All nine checks that have a pass mark pass, over 60 histories of 5,000 years** (12 on each of the 5 planets). The gate was stopped at 60 at Ben's instruction, above the agreed minimum of 50 and short of the 75 target. Check 5 (how many languages count as "several families' worth") was left in the specification for Ben to set from these runs, and check 11 (speed) has no target; both are reported below.

Two things the specification hoped for did **not** happen, and they are reported as findings rather than hidden inside passing checks:

1. **Island peoples do not drift apart faster.** Language pairs separated by sea share as many words as pairs on the same land that split at the same time (18% vs 18% at 3,000–5,000 years apart; within 4 points at every depth). In this model, isolation only removes borrowing, which is small; sound change and word replacement run at the same rate everywhere. Real island languages are often thought to diverge faster through founder effects (small groups, quick change); M1 has no mechanism for that.
2. **Disease outbreaks cause 9.3% of all deaths.** Infectious disease was a leading cause of death among foragers, but most of it is everyday illness (already inside "accident or illness"); epidemic outbreaks at forager densities were probably rarer. A candidate for retuning (the rate, or making outbreaks depend more strongly on crowding).

## Results

| Check | Result | Evidence |
|---|---|---|
| 1. M0 still holds | PASS | survival 60 of 60; highest population ÷ capacity 0.750 (≤ 1.0); life expectancy 28.3–28.6, births per woman 4.22–4.28, median band 23–26 (60 of 60 in all ranges); 0 accounting failures; exact replay 5 of 5; cause chains complete for 25,213 of 25,213 sampled deaths and events |
| 2. Spread | PASS | at year 5,000, occupied land holds 80%–100% of the starting land mass's food capacity (median 88%; at least 80% in 59 of 60 histories, pass mark 90%), on 35%–64% of its cells (the rest is mostly ice, desert and high mountains); 60 of 60 histories made at least one sea crossing (median 64), and 60 have people on more than one land mass at the end (every planet has islands within one sea cell) |
| 3. Drift with distance | PASS | rank correlation between distance apart and cultural distance (400 random band pairs per history, final year): 0.14–0.73 (median 0.45); clearly positive (above 0.2) in 56 of 60 histories (pass mark 90%). Parts on their own: customs median 0.36, language median 0.29 |
| 4. Drift with time | PASS | core vocabulary kept per 1,000 years: median 81% (range across languages and spans 78%–85%; pass band 70–90%); rank correlation between time since sister languages split and words they share: median -0.47 (must be clearly negative) |
| 5. Languages multiply | — | living languages at year 5,000: 91–316 (median 155); ever spoken 477–2013; families (languages sharing an ancestor less than 2,500 years back): 41–115 (median 60); speakers per language median 1,195; shared words for language pairs split the same time ago: 0–500 years apart: 86% across the sea vs 89% on the same land; 500–1000 years apart: 76% across the sea vs 72% on the same land; 1000–2000 years apart: 54% across the sea vs 54% on the same land; 2000–3000 years apart: 38% across the sea vs 36% on the same land; 3000–5000 years apart: 18% across the sea vs 18% on the same land. The pass count is for Ben to set from these runs. |
| 6. Regular sound change | PASS | 111,600 of 111,600 words rebuilt exactly from the proto-language by replaying every recorded change (each rule is applied to the whole vocabulary at once); 12,000 of 12,000 living people's names rebuilt from their language's words; sound changes per history 744–2034 |
| 7. Hazards in the right places | PASS | hazards logged in impossible places: 0; frequencies (all land, peopled or not): flood once per 57 years per affected cell; wildfire once per 340 years per affected cell; eruption once per 3,994 years per affected cell; earthquake once per 600 years per affected cell; plausibility ranges: flood 1/15–1/200; wildfire 1/50–1/2,000; eruption 1/1,000–1/20,000; earthquake 1/100–1/3,000 |
| 8. Hazard responses | PASS | flood: 968409 with deaths (mean 0.3% of the area's people); local population lower a year later in 45%, back to 90% within 20 years in 73%; wildfire: 724263 with deaths (mean 0.3% of the area's people); local population lower a year later in 56%, back to 90% within 20 years in 85%; eruption: 6488 with deaths (mean 20.5% of the area's people); local population lower a year later in 79%, back to 90% within 20 years in 81%; earthquake: 99743 with deaths (mean 0.9% of the area's people); local population lower a year later in 43%, back to 90% within 20 years in 72%; outbreak: 37625 with deaths (mean 1.6% of the area's people); local population lower a year later in 55%, back to 90% within 20 years in 68%. Every hazard death names its hazard in its cause chain (check 1). |
| 9. Outbreaks spread by contact | PASS | yearly chance a peopled area falls ill: 36.1% when in contact with an outbreak (18,441,621 of 51,081,903 area-years) vs 0.011% otherwise (45,816 new outbreaks in 401,407,056 area-years): 3,163 times higher (pass mark 10×) |
| 10. Groups match individuals at the food limit | PASS | groups ÷ individuals from the same world made crowded (wild food cut to 20% from year 800, or later once 15,000 people live there; rates over years 100–300 of the test): planet 1 (from year 800): births 0.95×, deaths 0.97× (food gathered ÷ needed 1.47 for individuals, 1.45 for groups; population 24,551 → 12,616); planet 2 (from year 800): births 0.96×, deaths 0.97× (food gathered ÷ needed 1.46 for individuals, 1.43 for groups; population 31,580 → 23,977); planet 3 (from year 800): births 0.95×, deaths 0.96× (food gathered ÷ needed 1.46 for individuals, 1.44 for groups; population 28,778 → 24,622); planet 4 (from year 990): births 0.96×, deaths 0.92× (food gathered ÷ needed 1.46 for individuals, 1.45 for groups; population 15,119 → 33,791); planet 5 (from year 850): births 0.91×, deaths 0.94× (food gathered ÷ needed 1.48 for individuals, 1.42 for groups; population 13,216 → 8,788) (pass: within 15%, with food gathered ÷ needed below 1.5, where food holds births down) |
| 11. Speed | — | 5,000 years took 798–3151 s (median 1284 s) of computing per history; median by planet: 1: 1434 s, 2: 1187 s, 3: 831 s, 4: 2233 s, 5: 1258 s |

Final populations at year 5,000: 120,900–479,423 (median 249,124).
Deaths by cause, all histories: accident or illness 38.0%, old age 24.2%, infancy and early childhood 17.9%, disease outbreak 9.3%, hunger 9.2%, childbirth 1.0%, flood 0.1%, wildfire 0.1%, orphaned infant 0.1%, earthquake 0.0%, volcanic eruption 0.0%.

## How the gate was run, and what changed while it ran

- **Machine.** All 60 histories ran in the cloud workspace (Python 3.13, NumPy 2.5), two at a time, in checkpointed slices of up to two hours; save and reload are exact, so a sliced history is the same history. The code was also checked to run on Ben's computer (Python 3.10).
- **Memory fix during the run.** One history on planet 4 (the largest planet) was stopped by the workspace's memory limit at over 4 GB, because rows for ended groups were never released. Rows of ended groups are now dropped every 50 years; a 60-year comparison from a saved world gave identical population, births, deaths and events with and without it. Histories already running continued on the earlier code until their next slice; behaviour is the same either way. The stopped history was rerun from the start. A duplicated job that I started by mistake was stopped after 12 minutes, before it wrote anything.
- **Measures settled during the gate** (each change is recorded in the build notes, with its reason):
  - *Spread (check 2)* is measured by the share of the starting land mass's **food capacity** that is occupied, not the share of cells: people occupy 35–64% of the cells, but the empty ones are mostly ice, desert and high mountains, and the occupied land holds 80–100% of the food.
  - *Drift with distance (check 3)* uses cultural distance as **customs and language together** (each half of the measure). Each part is also reported alone: customs median correlation 0.36, language 0.29.
  - *Groups at the food limit (check 10)* starts from a world with at least 15,000 people (planet 4 had only about 3,000 at year 800 and was still spreading into empty land) and cuts wild food to 20%, so that food holds births down. Groups' births and deaths run 3–9% lower than individuals' on every planet: inside the 15% mark, but consistent, so worth watching.

## For Ben to decide

1. **Check 5, languages multiply.** At year 5,000: 91–316 living languages per history (median 155), 477–2,013 ever spoken, 41–115 families with a common ancestor less than 2,500 years back (median 60), about 1,200 speakers per language. For comparison, forager languages are often reported in the hundreds-to-low-thousands of speakers. Proposed mark: at least 50 living languages by year 5,000 in at least 90% of histories (all 60 meet it).
2. **Whether to close M1** with the two findings above carried forward, or to address either first (founder effects for small isolated groups; outbreak frequency).

All rates are tunable starting values (`origins/params.py`), not measurements.

## Decision (Ben, 7 November 2026)

- Check 5 pass mark adopted: **at least 50 living languages by year 5,000 in at least 90% of histories.** Result: 60 of 60, so check 5 passes.
- **M1 closed.** The two findings (islands not diverging faster; outbreak share of deaths) are carried forward as open items for later milestones.

## Rerun after the stored-food fix (7 November 2026)

During M2 a bug was found that could leave a group with negative stored food (see `docs/M2_BUILD_NOTES.md`). It entered the code just before G1's histories ran, so gate G1 was rerun on GitHub with the fix: all 75 histories (5 planets × 15), farming switched off. Full report: `docs/M1_GATE_RERUN_REPORT.md`.

- **Every check still passes**, now on 75 histories, including check 5 under the approved mark (98–350 living languages; all 75 have at least 50).
- **Deaths by cause changed:** hunger 11.2% (was 9.2%), outbreaks 6.0% (was 9.3%). The rerun also carries M2's lower outbreak rate for foragers, so these cannot be separated cleanly; what the rerun shows is that the bug was not inflating G1's hunger deaths overall, as I had suspected: fewer outbreak deaths mostly became hunger deaths, as in the M2 tests.
- The two open findings stand: island languages still do not diverge faster (18% vs 18% shared words at 3,000–5,000 years).
