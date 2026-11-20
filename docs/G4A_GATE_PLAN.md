# Gate G4a: plan and measurements (draft for Ben)

Claude, 21 November 2026. **Status: approved by Ben on 21 November 2026**, with his decisions on the three open points (end of this document). The gate runs after the comprehensive pre-gate review (requests 034–037) and its fixes (CLAUDE.md). The checks and pass marks are those of `docs/M4_SPECIFICATION_v1.md` section 9 (approved 12 November 2026). This document says how each check is measured from the gate record, which the specification leaves open. All parameter values are tunable starting values, not facts.

## Histories

| Arm | Planets | Seeds | Histories | Runs to |
|---|---|---|---|---|
| Main | 1–5 | 1–10 | 50 | 6,000 years after the first farming village (as G3), or 30,000 years |
| `nopop`: no population effect on invention (`TECH_POP_EXPONENT` 0; check 6) | 1–5 | 1–4 | 20 | the same |
| `nocuration`: no curation (`CURATION` False) | 1–5 | 1–2 | 10 | the same |
| `noprestige`: no prestige goods (`PRESTIGE_HOLD` 0) | 1–5 | 1–2 | 10 | the same |
| `fourpartners`: a fixed four partners per band (`PARTNERS_CAP` 4) | 1–5 | 1–2 | 10 | the same |

The three small arms are the comparisons agreed for the gate in November (Ben, 21 November 2026, after Codex review 034). Dependence on imported metal is measured inside the main histories that work metal. A request: `{"gate": "g4", "planets": "1-5", "seeds": "1-10", "arms": {"nopop": "1-4", "nocuration": "1-2", "noprestige": "1-2", "fourpartners": "1-2"}, "per_job": 1}`.

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

| # | Check | Measured as (after Codex review 034) | Pass mark |
|---|---|---|---|
| 1 | M0–M3 still hold | G3's report run on the G4a records; a G3 check without a verdict counts as unmeasured, not passed; G3 check 5 is not re-measured (no no-institution arm); check 9's herd half carried forward; M1's items beside it | all applicable G3 checks pass |
| 2 | Innovation tracks connected population | per history: Spearman, over whole band-centuries (the band lived to the next census, the century ended before the history), of inventions with the connected people invention itself uses (`technology.connected_people`); foragers and farmers apart | median above 0.3 |
| 3 | Risk matters too, or doesn't | the same, with the mean need of the techniques the band could invent then | none (reported) |
| 4 | Diffusion follows contact | (a) per band, the share of techniques it knows whose last recorded acquisition, in its line, was from others (lost and relearned counts as learned); (b) per technique, Spearman of years after its first invention with transmission steps from an invention, following each adoption's named source through any route | (a) median above 0.6; (b) positive in most |
| 5 | Isolation causes loss | Henrich-kind losses per whole band-century fall across fifths of connected people; and a band's techniques fall when its connected people fall between censuses of the same band (a panel) | both, with losses occurring, in most |
| 6 | Knock-out | check 2's median in the `nopop` arm, against the main arm's; the paired change on the same planet and seed is shown beside it | below half the main arm's, and the main arm's positive |
| 7 | Trade follows supply and distance | fine stone, salt and shell per person all fall with cell steps from their sources; among bands with partners, food given per band-season rises with the share short before help, year by year, zero years kept | both, in most |
| 8 | Goods are conserved | accounting failures over the whole roster | none |
| 9 | The land answers back | crop factor (fertility × salt, as harvests use it) falls with years cropped; slow game is lower where mean hunting pressure is high; salt rises with years irrigated on dry land where any is irrigated; land-linked hunger and moves or abandoned fields occur. Cells ever cropped or hunted are kept, not only those lived in at the end | all, in most; exposure, not cause |
| 10 | Diseases from animals | Ben's numbers (above): persistent spells, herds and dense populations, fading of wild and small starts (finished spells only), first-contact deaths per person pooled and within arrivals reaching both naive and exposed bands | all three halves |
| 11 | Traceable | every required kind of event present in some history, and every sampled chain resolving | both |
| 12 | Same rules, different histories | per technique: histories, earliest, median and latest year, planets | none (reported) |
| 13 | Speed | simulation hours, and minutes to build the record | none (reported) |

**Historical comparisons**, reported beside the checks, not as pass marks:
- the order of first appearance of pottery, copper working, bronze, iron and writing, against the archaeological sequence;
- the years from the first village to the first state, against Borcan, Olsson and Putterman (2021);
- the place-name record: share of names kept by newcomers by feature size, and layers per place.

## Ben's decisions (21 November 2026)

After Codex review 034:
- **Trade raises invention's reach** (specification 4.2): built; a traders' road adds half the people around the far seat.
- **The agreed comparisons** run as the three small arms above; dependence inside the main histories.
- **M1's carried-forward items** are re-measured beside check 1: island divergence (language pairs across the sea and on the same land) and the share of deaths from epidemics against M1's 9%. Barren land (G1 check 2) is not re-measured.
- **Check 10's numbers:** a disease persists if a spell on a cell lasts 10 years or more; herds and dense populations meet in a spell-year with 100 or more herders on the cell and 5,000 or more people around. Check 10 passes if most persistent spell-years meet both, finished wild-origin or small-group spells mostly end within 10 years, and deaths per person after first contact are heaviest among bands that had never met the disease.
- **Coverage:** a check counts as measured only if at least half the histories can measure it; otherwise it shows "—", never a pass.

Before review 034:

1. **Check 6's mark:** the knock-out arm's median correlation below half the main arm's.
2. **"Most histories"** (checks 4b, 5, 7 and 9): at least two thirds of the histories where the check can be measured.
3. **History length:** 6,000 years after the first village, as in G3, so the two gates can be compared.

Ben approved the plan on 21 November 2026.

## Pipeline check (21 November 2026)

`gates/g4.py` and `gates/g4_report.py` were run end to end on the planet-3 save at year 9,700, for 110 years: 664 s of simulation, 185 s to build the record, then the report. It is a check that the code runs and every check can be computed, not a result: one history, too short for most checks.
- **The record-building first took over an hour.** Every band in a cause chain was looked up by scanning all 2 million events, read from disk. Fixed in `explain.py`: an index of band origins, and gate samples share references already found good. Same answers; 60 sampled chains in 10 s, against 9–44 s each before.
- **Every check computes.** Checks 2 and 3 need several centuries of census rows, and check 10 needs diseases that persist; in this short run they show "nan", as expected.
