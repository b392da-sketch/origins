# M3 gate report (provisional): "scale needs institutions; conflict has causes and costs"

10 November 2026. For Ben's decision. All rates are tunable starting values (`origins/params.py`), not measurements.

> **Correction (12 November 2026):** the logs that checks 4, 5, 5b, 8 and 9 and the historical comparisons are computed from covered only the end of each history:
> - polities: about the last 1,000 of 6,000 years;
> - wars: the last few hundred years;
> - household inequality: the last 600 years.
>
> The figures below for those checks describe the end of each history, not all of it. Fixed for G3 run 2 (GitHub run 43026594859), which also includes the changes from your decisions. See `M3_BUILD_NOTES.md`, 11–12 November.

## In short

- **Gate G3, run 1:** 63 of 70 histories finished (45 with institutions on 5 planets, 18 with institutions switched off). **7 of the 11 checks with a pass mark pass.** Checks 1, 4, 5 and 9 fail. The figures below are from 62 histories; adding the 63rd (planet 4 seed 1) changed none of the verdicts.
- **Lost to memory:** seven planet-4 histories (seeds 5–9, and seeds 1–2 without institutions).
  - At year 14,726, planet 4 seed 6 held 4.0 million events: 2.1 million wars and 1.2 million group hunger deaths. Kept as Python dicts, they take about 7 GB. GitHub's machines have 16 GB, and the save needs more on top.
  - **Fix (11 November):** events older than the newest 20,000 are now kept as compact text, about a fifth of the memory. A test shows that results are identical with and without it.
  - The seven histories are being rerun with run 1's simulation plus only this fix (run 42845720805, `g3-run1-rerun3`).
  - This is the on-disk event store planned for M4, brought forward in a simpler form.
- **Decisions for you:** checks 4, 5 and 9 (below), and whether M3 continues to conflict refinements and notables, or reworks institutions first.

**Runs:** GitHub Actions 42642951715 (`g3-run1`) and 42708701695 (`g3-run1-rerun`, planet 1 seed 3 and planet 4 seed 6, lost while writing checkpoints). Gate branch code: `fc929b5` and earlier; Python 3.13, NumPy 2.5.4.

## Results

| Check | Result | Evidence |
|---|---|---|
| 1. M0–M2 still hold | **FAIL** | 44 of 44 survived; 0 accounting failures; life expectancy 26.2–27.8. One cause chain of 4,833 is broken (see below). That single break also fails G2 check 10. G2 check 9 is G3 check 9. |
| 2. Polities form; states in some | PASS | chiefdoms in 42 of 42 histories with farming; states in 34, 219–5,492 years after the first village |
| 3. Oversized polities break up | PASS | secession rate rises steadily with overload, from 0.012 a year (within capacity) to 0.147 (load 1.75× capacity) |
| 4. Collapse in some, recovery | **FAIL** | collapse in 42 of 42 histories (mark: 20–90%); recovery after 308 of 308 |
| 5. No institutions, no large polities | **FAIL** | largest polity median 20 settlements with institutions vs 18 without (mark: under a quarter); no states without institutions (passes that half) |
| 5b. How long polities stay large (no mark) | — | longest time one polity held 10+ settlements: median 50 years with institutions (20–340) vs 10 without; polity-years at 10+ settlements per history: 2,495 vs 660 |
| 6. Conflict rises with scarcity and proximity | PASS | by rule; this checks the bookkeeping |
| 7. Conflict has costs | PASS | war deaths are 5.2–7.0% of deaths at 15 and over (median 5.9%) |
| 8. Empires are hard to hold | PASS | rank correlation of empire duration with overextension: −0.48 |
| 9. Inequality compounds | **FAIL** | correlation of Gini with years of farming −0.00 (mark: above 0.2); with surplus 0.24; Gini 0.33 in the first 100 years of farming, 0.38 after 500 |
| 10. Traceable | PASS | 24,800 of 24,800 sampled polity events |
| 11. Variation | — | largest polity 17–34 settlements across planets |
| 12. Speed | — | 1.3–7.6 h of computing per history (median 3.4 h) |

## The failures

### Check 1: one broken cause chain (found and fixed after the run)

In planet 1 seed 7, an infant's death as an orphan cited its mother, but she had no recorded death. Here is how it happened:

1. A raid took the infant as a captive without its mother.
2. The mother's band was later folded into a group, so her record ends without a death.
3. The infant was then counted as orphaned.

I confirmed this by constructing the case directly.

**Fix (commit `804cf20`):**
- Children under 3 are now taken only together with their mother.
- The explanation now handles a mother whose record ends because her band was folded into a group.

This change to the simulation came after the run, so run 1's results do not include it. The next G3 run will.

### Check 4: collapse everywhere

Every history with chiefdoms has at least one collapse, and every collapse is followed by recovery. In the historical record, collapse and regeneration of large polities are common, arguably near-universal, over 6,000 years. So the 90% upper mark is probably the error rather than the model.

**Options:**
- (a) Drop the upper mark and keep "recovery after at least half".
- (b) Keep the mark and make collapse rarer.

**I lean to (a).**

### Check 5: institutions make polities last, not grow

- **Size:** the largest polity is about the same with and without institutions (20 vs 18 settlements). Something other than institutions caps size near 20, most likely the cost of distance and of cultural difference, combined with war.
- **Duration:** institutions make large polities last longer (a median longest hold of 50 years vs 10) and give about 4 times as many polity-years at 10+ settlements. They also make states possible (34 histories with states vs none without).
- **A wider problem:** even with institutions, a large polity typically holds together for only about 50 years. That is short for real chiefdoms and states, which usually lasted generations or centuries. The model churns too fast.

**Options:**
- (a) Revise check 5 to what the model shows: without institutions, no states, and large polities short-lived. This is a change to the approved specification.
- (b) Find and loosen the size ceiling (load from distance and culture, and conquest room), then rerun G3.
- (c) Lower the churn: secession and war rates, so polities last longer. Then rerun G3.

**What the records show** (polity-years at 10 or more settlements, across 45 histories with institutions and 18 without):
- **Large polities are made by conquest.** In the median polity of 10 or more settlements, every settlement was conquered; alliances hardly reach that size.
- **They are overloaded most of the time.** Load is above capacity in 64% of polity-years with institutions (median load ÷ capacity 1.29), and in 100% without (median 2.95). Overloaded polities lose members to secession, so they shrink back within decades.
- **Large polities rarely have many institutions.** The median polity of 10 or more settlements has 1 of the 5.
- **Levels of rule hardly grow with size:** a median of 2.

So the pattern is conquest overshooting capacity, then secession. War builds polities faster than institutions can be found to hold them. Institutions are rare discoveries (a 1% chance a year, then copied), so most conquerors have none.

**My view:** (b) and (c) together are the substantive answer. The churn is the bigger realism problem, and it probably also caps size. (a) alone would pass the check while leaving polities that come and go every few generations.

### Check 9: inequality still does not compound

The new mechanisms (an advantage from scarce heritable land, breeding herds) raise late Gini only slightly (0.33 → 0.38). They do not create a rising trend with time. Partible inheritance and yearly harvest luck still pull households back together within a few generations, as in M2.

**Options:**
- (a) Strengthen the compounding: more land advantage, inheritance favouring one heir where custom says so.
- (b) Carry it forward again.

**I lean to (a).** Impartible inheritance, for example to the eldest son, is the mechanism the literature points to. It fits the succession customs that already exist.

## Comparison with historical data (first pass)

| Measure | Historical | Model (G3 run 1) |
|---|---|---|
| Size against levels of rule | Correlation 0.78 between polity population and levels of hierarchy, over 414 polities in 30 regions from the beginnings of farming to about 1900 CE (Turchin et al. 2018, Seshat) | Rank correlation of log population with levels of rule: median 0.07 per history (−0.18 to 0.47) |
| How long large polities last | Mean about 220 years for 41 empires, 3000 BCE to 600 CE, and the chance of collapse does not depend on age (Arbesman 2011) | Longest time one polity holds 10 or more settlements: median 50 years per history |

**Caveats:**
- The model's polities span a narrow range (2–34 settlements), against Seshat's villages to empires. A narrow range alone lowers a correlation.
- Arbesman's empires are far larger than anything the model makes.

Even so, both comparisons point the same way as the check 5 analysis: polities that grow without adding levels of rule, and fall apart too fast.

**Not yet compared:** time from first villages to states, against Seshat's regional sequences. I haven't verified a published figure for it.

## Sources

- Arbesman, S. (2011). The life-spans of empires. *Historical Methods*, 44(3), 127–129.
- Turchin, P., Currie, T. E., Whitehouse, H., et al. (2018). Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization. *PNAS*, 115, E144–E151. https://doi.org/10.1073/pnas.1708800115

## Next

1. Merge the last histories into these figures.
2. Make the Seshat comparison.
3. Act on your decisions on checks 4, 5 and 9.
4. Rerun G3 with the fixes.

## Decisions (Ben, 11 November 2026)

- **Check 4: option (a).** Drop the upper limit of 90% on collapse; keep "recovery after at least half of collapses". This is a change to the approved specification, recorded as Ben's.
- **Check 5: options (b) and (c) together, provisionally.** Loosen the size ceiling (load from distance and culture, and conquest room) and lower the churn (secession and war rates), then rerun G3. Check 5's wording stands for now.
- **Check 9: option (a).** Strengthen the compounding of inequality, with inheritance favouring one heir where custom says so, then rerun G3.

The work starts on Thursday 12 November, when Ben's usage resets. Every change will be recorded in `M3_BUILD_NOTES.md`, and G3 will be rerun with all the fixes, including the captive-infant fix and the compact event record.

## Decisions (Ben, 12 November 2026)

1. **Inequality level:** diagnose and fix it against the literature's targets before G3 run 2. G3 trial 3 gave a median Gini of 0.66–0.73, against 0.48 for agriculturalists (Borgerhoff Mulder et al. 2009) and 0.27–0.35 by house size (Kohler et al. 2017).
2. **Check 9 reworded** to "inequality rises with scarce land and herds", in place of "inequality rises with time". This is the pattern the literature supports: Kohler et al. find inequality kept rising only where draft animals let advantage compound. The marks are mine:
   - rank correlation of Gini with land scarcity, and with the share of farming in herds: each with a median above 0.2;
   - median Gini of farming villages between 0.25 and 0.55.

   The trend with time is still reported, without a mark.
3. **States arrive too early** (448–1,458 years after the first village in trial 3, against 2.7–3.1 millennia historically): carried forward, not addressed in M3.

---

# G3 run 3 (12–13 November 2026): for Ben's decision on M3

**Run:** GitHub Actions run 43136210637 (`g3-run3`), from `main` at `8a0d4a1`. It includes every decision of 11 and 12 November and the fixes from Codex reviews 001–003.

**Histories:** 68 of 70: all 50 with institutions, and 18 of 20 without.
- **No institutions, planet 4 seed 3:** still in its last stage when this was written.
- **No institutions, planet 4 seed 1:** did not finish. It reached year 28,206 of 30,000 (8.3 million events, 900,000 people) in two stages, and no third stage was scheduled for it.
- Neither changes a verdict: they are 2 of the 20 knock-out histories.

All rates are tunable starting values, not measurements.

## Results

| Check | Result | Evidence |
|---|---|---|
| 1. M0–M2 still hold | PASS | all G2 checks that apply pass on these histories: survival, accounting, life expectancy 25.8–28.0, cause chains, farming conditions, adoption spread, foragers remaining, spread, demographic transition |
| 2. Polities form; states in some | PASS | chiefdoms in 47 of 47 histories with farming; states in 40, 305–5,571 years after the first village |
| 3. Oversized polities break up | PASS | yearly secession per member rises from 0.006 (within capacity) to 0.162 (1.75 times over); median rank correlation 0.99 |
| 4. Collapse happens, recovery follows | PASS | collapse in 47 of 47 histories with chiefdoms (a polity holding 10+ settlements continuously for 50+ years, losing half its people within a century); recovery after 705 of 712 |
| 5. No institutions, no large polities | **FAIL, on the line** | largest polity: median 24 settlements with institutions (18–38), 6 without (6–8). The ratio is exactly 0.25 against a mark of under a quarter. No states without institutions |
| 5b. How long polities stay large (no mark) | — | longest hold of 10+ settlements: median 230 years with institutions (90–920), never without; polity-years at 10+ settlements per history: 12,190 with, 0 without |
| 6. Conflict rises with scarcity and proximity | PASS | by rule; this checks the bookkeeping |
| 7. Conflict has costs | PASS | war deaths are 5.7–8.5% of deaths at 15 and over (median 6.9%) |
| 8. Empires are hard to hold | PASS | 58,289 empires; rank correlation of duration with overextension −0.35 |
| 9. Inequality rises with scarce land and herds | **FAIL, on herds** | land scarcity: median rank correlation 0.32 (passes); median Gini of farming villages 0.40 (passes, 0.23–0.84 across histories); herds: median rank correlation 0.01 (fails) |
| 10. Traceable | **FAIL, on one loop** | 27,200 of 27,200 sampled polity events have complete cause chains; one history ends with a looping chain of rule (below) |
| 11. Variation (no mark) | — | largest polity 18–38 settlements, 1,945–33,242 polities per history, across planets |
| 12. Speed (no mark) | — | 9,983–30,000 years in 1.0–9.9 h of computing (median 3.0 h) |

## The three failures

### Check 5: exactly at the mark

- **Size:** 6 settlements is exactly a quarter of 24, and the mark is "under a quarter". Trial 3 gave the same ratio.
- **Every other measure of what institutions do is decisive:**
  - without institutions there are no states;
  - no polity ever holds 10 settlements for even one sample;
  - there are no polity-years at that size, against 12,190 with institutions.
- **Recommendation:** treat check 5 as met in substance and record the ratio as at the line. I have not tuned anything towards the mark, and would not, because a tuning aimed at 0.24 would be aimed at the check, not at history.

### Check 9: land and level pass; herds do not

- **I was wrong about the reason.** I had expected herding villages to be too rare. They are not: in 39% of village-years, more than half of farming is in herds. Villages are mostly all crops or all herds.
- **Pooled across histories, herding villages are more unequal:** median Gini 0.58, against 0.37 in crop villages.
- **Within histories, the difference is small:**
  - in the 12 histories that have both kinds, herding villages are a median 0.04 more unequal (−0.10 to +0.27; higher in 7 of 12);
  - 12 histories have only herding villages, and 23 only crop villages;
  - so most of the pooled gap is between histories, not a within-history effect, and the per-history correlation the check uses is near zero.
- **The literature is also weaker here than the wording suggests.** Borgerhoff Mulder et al. (2009) find pastoralists (Gini 0.42) more unequal than horticulturalists (0.27) and foragers (0.25), but not more than agriculturalists (0.48). So "inequality rises with herds", measured against crop farmers, is not a strong prediction.
- **Options:**
  - **(a)** record the herd half as failed and carry it to M4a, where pastoralism (Ben's decision 4 for M4) will make herding a way of life of its own;
  - **(b)** reword the herd half to "herding societies are more unequal than forager and horticultural ones", which is what the literature supports.

  I lean to (a).

### Check 10: one looping chain of rule (found, fixed, measured)

- **Cause:** planet 2 seed 6, year 7,523. A settlement annexed earlier in the year was still treated as its old side's member in that year's later wars. It attacked itself, won, and annexed itself.
- **Fix:** commit `79c14e9`, after the run. A war is fought only if both sides are still what they were.
- **Verified:**
  - the same history rerun past that year, with no loop;
  - 49 tests pass.
- **How often:** 41 of 73,602 wars (0.06%) in a planet-3 history would have been fought on sides that had changed during the year. So run 3's results stand, with this noted.
- **Recommendation:** treat check 10 as passed with the fix, since every cause chain is complete.

## Comparisons with history (no marks)

| | Historical | G3 run 3 |
|---|---|---|
| Size against levels of rule | correlation 0.78 (Seshat; Turchin et al. 2018) | median rank correlation 0.15 per history (−0.07 to 0.58); 0.07 in run 1. Better, still weak |
| How long large polities last | mean about 220 years for 41 ancient empires (Arbesman 2011) | longest hold of 10+ settlements: median 230 years per history; 50 in run 1 |
| Farming to first state | 2.7–3.1 millennia (Borcan, Olsson & Putterman 2021) | median 1,168 years after the first village (quartiles 660–2,526), in 40 of 47; no state within 6,000 years in 7. Still too early; carried forward (Ben, 12 November) |

## Notes on the measurements

- **Logs:** they now cover whole histories. The largest polity log had 147,604 rows, far below its ceiling. Polity samples are 10 years apart, so sizes and holds are measured at that resolution.
- **Codex reviews:** 001–003 found five real bugs, all fixed before this run (`reviews/`). Request 004 asks Codex to check this report against the result files.

## Decisions for Ben

1. **Check 5:** accept as met in substance, with the ratio recorded at the line (recommended); or not.
2. **Check 9's herd half:** (a) carry to M4a's pastoralism (recommended), or (b) reword.
3. **Check 10:** accept as passed with the loop fix (recommended).
4. **Whether M3 closes.** I recommend closing on the above, carrying forward:
   - states too early;
   - the herd half of check 9;
   - size against levels of rule (weak).

   **First, Codex's request 004** should confirm this report against the result files.
