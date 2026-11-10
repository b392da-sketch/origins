# M3 gate report (provisional): "scale needs institutions; conflict has causes and costs"

10 November 2026. For Ben's decision. All rates are tunable starting values (`origins/params.py`), not measurements.

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
