# Review request 004: the G3 run 3 report, against the results and the code

**From:** Claude, 13 November 2026. **For:** Ben's decision on closing M3.

**What to review:**
- the section "G3 run 3" at the end of `docs/M3_GATE_REPORT.md`;
- the result files on the `gate-results` branch, under `results/g3-run3/`: 68 history records, and `report_68_histories.md`, the output of `gates/g3_report.py` on them;
- `gates/g3_report.py` and `gates/g3.py` (what is recorded and how each check is computed).

## Please check

1. **Every number in the run 3 section follows from the result files.** Recompute them independently, not by rerunning `g3_report.py` alone:
   - the check table;
   - the herding and crop village comparison (39% of village-years over half herds; pooled median Gini 0.58 against 0.37; within the 12 histories with both kinds, a median difference of 0.04, higher in 7 of 12);
   - the historical comparisons: size against levels of rule (median 0.15), longest hold (median 230 years), and farming to first state (median 1,168 years, 40 of 47).
2. **Each check measures what its wording says**, especially 5 (and 5b), 9 (the three conditions, and whether a per-history median of rank correlations is a fair test for a variable that is mostly 0 or 1), and 10.
3. **The claims in "The three failures"** follow from the evidence, and nothing is overstated or left out. In particular:
   - the treatment of check 5 as met in substance;
   - the reading of the literature on herds (Borgerhoff Mulder et al. 2009);
   - check 10 passing with the fix.
4. **Anything in the records that the report should mention and does not.**

Same format as before (AGENTS.md). Design questions go to "Design questions for Ben".
