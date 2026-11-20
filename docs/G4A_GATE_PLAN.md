# Gate G4a: plan and measurements (draft for Ben)

Claude, 21 November 2026. **Status: a proposal.** Ben approves the gate run; nothing here runs until he does. The checks and pass marks are those of `docs/M4_SPECIFICATION_v1.md` section 9 (approved 12 November 2026). This document says how each check is measured from the gate record, which the specification leaves open. All parameter values are tunable starting values, not facts.

## Histories

| Arm | Planets | Seeds | Histories | Runs to |
|---|---|---|---|---|
| Main | 1–5 | 1–10 | 50 | 6,000 years after the first farming village (as G3), or 30,000 years |
| Knock-out: no population effect (`TECH_POP_EXPONENT` 0; check 6) | 1–5 | 1–4 | 20 | the same |

G3 ran 70 histories in the same shape (50 with institutions, 20 knock-outs).

**Planet 4:** in G3 its histories reached 2.6 million people and needed several machine stages and checkpoints. With M4a's extra arrays it may need more. The comprehensive review measures this first.

## What the record adds to G3's (`gates/g4.py`)

The G4a record is the G3 record, so G3's checks can be re-run on it (check 1). It adds the items below.

- **A century census of bands (for checks 2, 3 and 5).** Every 100 simulated years, for up to 2,000 living bands, drawn at random from the gate's own sampling stream (not the simulation's):
  - the people within reach (two rings, as invention uses);
  - the skilled practitioners within reach;
  - the strongest need of any technique the band could invent;
  - the number of techniques it knows, and how many of them it practises;
  - its share of work in farming.

  Inventions and losses per band in each century are counted from the events.
- **Where each technique came from (check 4).** For each living band at the end, for each technique it knows: whether the band or one of its ancestor bands invented it, or it came from others. The answer is worked out from the invention events and the bands' parent links, with no new simulation state.
- **Spread by distance (check 4).** For each technique, the cell and year of its first invention. For each band's first adoption of it, the cell and year (up to 20,000 rows, sampled). The report works out contact steps as cell steps over land on the planet's grid.
- **Fall-off of goods (check 7).** At the end, each good's holdings per person by cell steps from its nearest source. Each year, the food given by partners in need, beside the share of bands short of food that year.
- **The land (check 9).** At the end, for every lived-in cell: fertility, salt, slow and fast game, forest, the year its use began, whether it is irrigated, and the hunting pressure. Also the land's exposure census (`land_exp_*`) and the counts of `land_hunger` and `land_move` events.
- **Writing against tenure (reported beside the checks, Ben, 21 November 2026).** The writing log (`writing_log`), every polity's history at tier 2 or above (kept whole), and writing's inventions with their stimulus.
- **Traceability (check 11).** Sampled cause chains, 200 each, for inventions, losses, adoptions, goods' first arrivals, trade routes, new diseases and place names.

## How each check is measured (`gates/g4_report.py`)

| # | Check | Measured as | Pass mark (specification) |
|---|---|---|---|
| 1 | M0–M3 still hold | G3's report run on the G4a records (G3's checks; M0–M2 through G3's re-check) | all G3 checks that applied in G3 |
| 2 | Innovation tracks connected population | per history: Spearman correlation, over band-centuries, of inventions in the century with skilled practitioners within reach at its start; also shown for foragers and farmers apart | median across histories above 0.3 |
| 3 | Risk matters too, or doesn't | the same correlation with need, beside check 2 | none (reported) |
| 4 | Diffusion follows contact | (a) per band, the share of techniques it knows that came from others; median over bands, then over histories. (b) per technique, Spearman correlation of a band's first-adoption year with its cell steps from the first invention | (a) median above 0.6; (b) positive in most histories |
| 5 | Isolation causes loss | losses occur; loss rate per band-century by quintile of people within reach falls as reach rises (Spearman over quintiles negative); techniques known fall with reach | all three hold in most histories |
| 6 | Knock-out: no population effect | check 2's median correlation in the knock-out arm, against the main arm | clearly lower (proposed: below half the main arm's) |
| 7 | Trade follows supply and distance | fine stone, salt and shell held per person fall with cell steps from the source (Spearman negative); partner help per year rises with the share of bands short of food (Spearman positive) | both in most histories |
| 8 | Goods are conserved | accounting failures (goods, food, people) | none in any history |
| 9 | The land answers back | among cells irrigated in dry land, salt rises with years of use; fertility falls with years of continuous cropping; slow game is lower where hunting pressure is high; `land_hunger` and `land_move` events occur | all in most histories that farm; stated as exposure, not cause (Ben, 20 November 2026) |
| 10 | Diseases from animals | from the disease record: share of disease-spell years with herders and dense populations around, against wild-origin and small-group starts; first-contact deaths per person among bands that never met the disease, against those that met it within a generation and longer ago | as reworded by Ben, 20 November 2026 |
| 11 | Traceable | sampled chains resolve | all |
| 12 | Same rules, different histories | which techniques appear, where and when, across histories | none (reported) |
| 13 | Speed | computing seconds per history | none (reported) |

**Historical comparisons**, reported beside the checks, not as pass marks:
- the order of first appearance of pottery, copper working, bronze, iron and writing, against the archaeological sequence;
- the years from the first village to the first state, against Borcan, Olsson and Putterman (2021);
- the place-name record: share of names kept by newcomers by feature size, and layers per place.

## Open points for Ben

1. **Check 6's mark** ("falls clearly") needs a number. Proposed: the knock-out arm's median below half the main arm's.
2. **"Most histories"** in checks 4b, 5, 7 and 9. Proposed: at least two thirds of the histories where the check can be measured.
3. **History length:** 6,000 years after the first village, as in G3, so the two gates can be compared.
