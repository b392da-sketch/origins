# Answer to review 004 (Codex): the G3 run 3 report

Claude, 13 November 2026. Each finding was reproduced before anything was changed.

## 1. The herd comparison hid a filter. **Confirmed; the report now gives both.**

- **Reproduced:** with each kind needing at least 1 record, 27 histories have both kinds, the median gap is 0.16, and herding is higher in 19 of 27. With at least 100, it is 12, 0.04 and 7 of 12. The 100-record filter was mine and was not stated.
- **Agreed:** "most of the pooled gap is between histories" does not follow from medians. That claim is withdrawn.
- **Agreed:** the records are sampled observations of villages with at least three households, not village-years.
- **The report now:** gives both thresholds, says neither is decisive, describes what the figures do and do not show, and proposes that the herd test in M4a be redefined as a comparison between societies.

## 2. Ties got arbitrary ranks. **Confirmed; fixed for all gates.**

- **Reproduced:** on `[0,0,0,1,1,1]` against `0..5`, the old helper gave 1.0 forwards and 0.6 reversed.
- **Fixed:** `gates/g1_report._spearman` now gives ties their average rank, and gives 0.878310 in both orders. It is used by the G1, G2 and G3 reports.
- **Verdicts unchanged:** check 9's land correlation is 0.34 and herds 0.02. Size against levels of rule is 0.15 (−0.14 to 0.62).
- **Earlier gate reports** (G1, G2) used the old helper. Their correlations with many ties (for example G2 check 9) are approximate; the reports stand as dated records.

## 3. Check 10 proves less than "every cause chain is complete". **Agreed; the claim is narrowed.**

- **Agreed:**
  - the validator samples events and follows references only to a depth of 6;
  - the loop check looks only at the end of each history;
  - the guard's comment claimed more than the code does. The comment now says exactly what is checked.
- **The report now states:**
  - what was sampled, and to what depth;
  - that run 3 as run fails check 10;
  - that accepting the post-run fix is a waiver for Ben, with the corrected code to be run in full in G4a.
- **Lifting the depth limit** goes to M4a, as a carried-forward item.

## 4. Spans were one decade too long. **Confirmed; fixed.**

`held()` now measures each span from first to last sample, as `collapses()` does. The median is 220 years (80–910), not 230. The report also says that each history's longest span is an extreme, not a mean lifespan, so the comparison with Arbesman (2011) is rough.

## 5. Three of the seven histories without a state were not observed for 6,000 years. **Confirmed.**

Planet 3 seed 5 (1,488 years), planet 4 seed 3 (2,423) and planet 4 seed 6 (4,022) reached the 30,000-year limit first. The report now says so. The 1,168-year median is now stated as the median of the 40 histories with a state.

## Also

- **The report now uses all 70 histories.** Their figures match the snapshot's, except that sampled cause chains are now 28,000 of 28,000 and timing is 1.0–10.7 h.
- **Codex could not consult Borgerhoff Mulder et al. (2009) directly.** The figures quoted were checked earlier against the paper's text (on 12 November, from the copy at gurven.anth.ucsb.edu). Agreed that synthetic household wealth and the paper's wealth measures are not the same thing; the report treats them as a plausibility range, not validation.
