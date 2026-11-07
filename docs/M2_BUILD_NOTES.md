# M2 build notes

Working notes for M2 "farming is an option, not a destiny": what was built, what was tried and changed. All rates are tunable starting values in `origins/params.py`, not measurements.

## What was built

| Part | Where | Notes |
|---|---|---|
| Domestication | `sim/farming.py` | Tending → cultivation → domestication of the nine wild progenitors, per band; skills inherited at splits and learned from neighbours; a domesticated species can be raised wherever it suits. |
| Farming | `sim/farming.py`, `sim/foraging.py` | Each year a band splits its work by comparing food per day of work (farming discounted for risk) with inertia. Crops come in once a year; herds give food every season. Farmed land is shared by the bands working it. |
| Storage and villages | `sim/foraging.py`, `sim/farming.py` | Farmers store grain (a granary of about 400 days, 5% loss a season). Bands living mainly from farming stop moving and are villages; the first village to farm mainly for 75 years is recorded as the world's first farming village. |
| People in villages | `sim/demography.py`, `sim/groups.py`, `sim/hazards.py` | Shorter birth spacing in villages (weaning foods); outbreaks start more often in villages and less often among foragers (M1's open item). |
| Surplus and property | `sim/surplus.py` | After harvest, stored food beyond the needs until the next harvest feeds specialists (a leader, ritual specialists, craft workers), who do not produce food. In farming bands, households hold fields and stores; holdings grow or shrink with each year's luck and pass to children's households; Gini coefficient measured between households. |
| Knock-out | `params.STORAGE` | With storage off, every store keeps the foragers' size and spoilage; no surplus can accumulate. |
| Gate G2 | `gates/g2.py`, `gates/g2_report.py`, GitHub workflow | Histories until 3,000 years after the first farming village (or 25,000 years); knock-out histories; parameter overrides per gate request. |

## Tried and changed

- **Granaries too small.** A band farming half its work could store only about 260 days of food, less than the nine months to the next harvest, so no surplus and no specialists appeared. Granaries now reach full size once a band farms half its work.
- **Villages split at forager size (50).** Villages now grow to 150 before founding a daughter village (groups as before, 200).
- **Domestication stalled.** With progress after cultivation tied mostly to farming effort, and farming not yet worth the effort, domestication would have taken about 13,000 years. Progress is now driven by farming or by food pressure, whichever is greater (a few thousand years).
- **Farmers' food security.** Farmers' fertility followed a season-by-season food measure that peaked at harvest. It now measures what they hold against the needs of every season until the next harvest.
- **Grain spoilage** used the foragers' rate for the non-farming share of work; a band farming half its work now stores mostly grain.

## A bug found during M2 that also affected M1

**Negative food stores.** When a group that had taken people in earlier in the same season then split, it handed on a share of food computed from its size at the start of the season, which could exceed what it held, leaving it with negative food. The accounting check did not catch it because the world's total food still balanced. Starving villages with full harvests coming (about 10 hunger deaths per 1,000 people a year, against 1.4 for foragers) exposed it. The bug came in with the speed change made shortly before gate G1's histories ran ("group fission into an occupied neighbour transfers directly"), so it very likely inflated G1's hunger deaths (9.2% of all deaths). Fixed: shares now use the current size; standing crops travel with the people; villages and foragers on the same land stay separate groups; a new check fails any negative store. Effect in a test world from year 4,000: village hunger deaths fell by about 98% and village population doubled in 70 years instead of shrinking. Gate G1 is being rerun with the fix (farming switched off, all 75 histories) on GitHub.

## Memory

A farming world on planet 1 passed 4 GB at about year 5,000 here (2.2 million person rows by year 4,000: people are never removed, so that every death stays explainable). Person fields now use 32-bit integers (they always fit), and ended bands keep only their last few steps.

## Open findings

- **Outbreaks in villages** cause about 18–20% of deaths on planet 3 once villages dominate. Tested from the same farming world at year 7,000 over 100 years: halving the village outbreak rate gave 17% outbreak deaths and 11% hunger (population +6%); halving outbreak deaths as well gave 9% outbreak deaths but 16% hunger (population +15%). Outbreak and hunger deaths trade against each other because food still limits population: fewer epidemic deaths mostly become hunger deaths. Kept as set; to be judged from the gate, not tuned blind.
- **Hunger** is still about 9% of deaths in farming worlds; to be measured again once the gate runs.

## After the second G2 run

- Planet 4 (the largest world) is slow: at year 4,500 without farming, about 476,000 people, 0.9 s of computing per simulated year, 2 GB of memory and 659,000 band records (every band that ever existed is kept for the history). Band records are now compact; the best crop for every band is chosen at once (same results); histories can continue across up to three GitHub machines (about 13 hours).
- Inequality: Gini between households in farming villages is about 0.37–0.55 late in histories and zero without storage. The second run could not show whether it rises with time, because its log kept only the end of each history and measured time from when a band became a village (a daughter village restarts that clock while carrying its households' holdings). Now measured against how long a people has farmed, from logs sampled across the whole history.

## Band churn (found during the third G2 run)

GitHub machines running long planet 4 histories ran out of memory ("the hosted runner lost communication… starves it for CPU/Memory"), several while saving a checkpoint. Cause: about 400 new band records a year, nearly all groups that lived a season or two. A large group splits into the neighbouring land with the most food per person, and next season that new group moves on into land already held by another group and is merged into it (a change of representation, not a social event). In planet 2 at year 1,800, 3,098 of 3,640 bands created in 50 years ended that way (median life about six weeks); by year 7,000 on planet 4 there were 1.5 million band records. Changes:

- a group (a local population) moves only into land not already held by a group of its own kind; moving into another group's land would only merge them, and splitting and sharing already move people between neighbouring groups;
- a group never splits into its own land (it would be recombined at once);
- when groups combine, the standing crop goes with the people (it was lost before; the food accounting did not see it because standing crops are not yet food).

Effect in planet 2 at year 1,800: band records 8,219 instead of 31,621; new bands in 50 years 287 instead of about 2,100–3,600; population 243,800 against 228,300, within the run-to-run variation seen before. Because this changes how groups move, gates G1 and G2 are both rerun.
