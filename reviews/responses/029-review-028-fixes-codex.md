# Review 029 — review-028 fixes

Codex, 20 November 2026. Reviewed `1d9d196..532d5af`.

## Findings

### 1. Group movement can separate a pregnancy from the only woman

- **Where** — `origins/sim/groups.py:381–423`, `split` and `transfer`.
- **What is wrong** — Both paths draw pending pregnancies independently of the women who move. A pregnancy can stay with a group that has no women of childbearing age while the only possible mother leaves.
- **Why it matters** — The next mortality cleanup can erase a pregnancy solely because its mother moved.
- **How sure you are** — Certain. Reproduced for split. Transfer uses the same independent draws.
- **How to see it** — Start with a 25-year-old woman, a man and one pending pregnancy. Draw the woman to move, the man to stay and zero pregnancies to move. The source has zero women and one pregnancy, and the daughter has one woman and zero pregnancies. Applying the next cleanup to both drops the pregnancy.

### 2. The adult immunity update omits the mortality of people aged 50 and over

- **Where** — `origins/sim/disease.py:373–389`, `_epidemics`.
- **What is wrong** — Deaths for ages 50 and over use `po`. The shared adult immunity update uses only `pa`, the expected death share for ages 15–49, even in a band where every adult is older.
- **Why it matters** — The stored share of immune adult survivors can be too high, reducing susceptibility in later simulated epidemics.
- **How sure you are** — Certain.
- **How to see it** — Give a band of 60-year-olds prior immunity of 0.20, an illness share of 0.20 and expected death shares of 0.04 for ages 15–49 and 0.08 for older adults. The stored adult share is 0.375. The expected share among older survivors is `(0.20 + 0.20 − 0.08) / (1 − 0.08) = 0.347826`.

### 3. Group mortality can leave more pending pregnancies than women

- **Where** — `origins/sim/groups.py:206–213` and `303–314`, `keep_pregnancies` and maternal deaths in `births`.
- **What is wrong** — Rounding separately by due slot can retain every pregnancy as the number of women falls below the number pending. Maternal deaths remove women directly and skip cleanup of the remaining slots.
- **Why it matters** — Whole counts now survive splitting without producing negative draws, but the pending total can still exceed the number of possible mothers.
- **How sure you are** — Certain. Reproduced the rounding case and traced maternal deaths.
- **How to see it** — Put one pending pregnancy in each of three due slots with three women aged 15–49. Remove one woman and call the helper with the original count. Each slot rounds from two thirds to one, leaving three pregnancies for two women. In `births`, the maternal-death branch decrements the count after advancing the due slots and proceeds straight to conceptions.

### 4. The epidemic record and G1 hazard watch use different population baselines

- **Where** — `origins/sim/disease.py:121,351–399` and `gates/g1.py:106–139`.
- **What is wrong** — Every epidemic in a year logs the population snapshot taken before the first epidemic, even though deaths are applied in sequence. The hazard watch reconstructs its baseline from the year-end population of the cell and its neighbours plus only the focal cell's deaths. This omits epidemic losses in neighbouring cells and includes intervening population changes.
- **Why it matters** — The cell log can understate the death share of a later epidemic. The watch can overstate recovery when it starts from too small a baseline.
- **How sure you are** — Certain. Reproduced the stale population and traced the watch.
- **How to see it** — Start a cell with 30 people and run two epidemics that kill five each. Both log rows report 30 people and five deaths. The second epidemic began with 25. For the watch, if 100 people in a cell and its neighbours fall to 80 after five focal and 15 neighbouring deaths, the watch stores 85 as the baseline even with no other changes.

### 5. G1 check 9 can count reservoir arrivals as evidence of contact spread

- **Where** — `origins/sim/disease.py:150–199` and `gates/g1_report.py:236–247`.
- **What is wrong** — The exposed numerator counts any arrival in an exposed cell, including a return from its animals. The comparison denominator pools one opportunity per eligible cell per existing disease with one generic opportunity per peopled cell for new diseases. G1 calls both area-years and interprets the ratio as outbreaks spread by contact.
- **Why it matters** — The two rates measure different opportunity sets, and the reported ratio can rise entirely through reservoir arrivals. This can make G1 pass with no simulated transmission by contact.
- **How sure you are** — Certain. Reproduced a reservoir-only arrival in the exposed numerator.
- **How to see it** — Keep one disease active in one of two neighbouring peopled cells. Disable contact spread and allow the reservoir to seed the other cell. The counters give one exposed arrival in one exposed disease-cell-year, and zero arrivals over two other units. The log has one reservoir return and zero contact arrivals. G1's formula passes that comparison.

### 6. The G3 export cannot measure both halves of reworded G4a check 10

- **Where** — `origins/sim/disease.py:53–57,76–101,383–399` and `gates/g3.py:123–141`.
- **What is wrong** — The export records origin and annual circulation but lacks contemporaneous local herding and density around the affected cell. Thinning individual rows above 20,000 can also break local circulation sequences. For first contact, the log has a source cell, one all-bands-naive flag and total deaths. It has no interval of separation, nor separate people-at-risk and deaths for previously exposed and unexposed groups in a mixed cell.
- **Why it matters** — The record supports examples of individual arrivals and coarse comparisons by disease or cell. It cannot establish that persistence is concentrated where herds and dense populations overlap, or compare death rates by prior exposure after long separation.
- **How sure you are** — Certain from the exported fields and sampling.
- **How to see it** — A row with `never met it = false` could represent a cell where every band had prior exposure or one containing a single previously exposed band and many naive people. The same death total can result from different distributions of deaths between the two. A `kept` row supplies the cell headcount and no measure of local herding. A contact row supplies the source cell and no history of contact between the two populations.

## Checked and sound

- The original 30-into-30 immunity case now gives 0.5. The single demographic weight and fixed child share follow Ben's decision.
- The child and 15–49 cohort calculations reproduce 0.5652 for the original survivor example, and expected deaths stay within cases for all three age ranges.
- Ordinary group deaths, hazards, conflict and named-disease deaths clear pending pregnancies when the last eligible woman dies. Pending counts remain whole after the helper. A full merge moves all age counts and pregnancy slots and clears the source. Folding bins individual due dates. Unfolding assigns due dates to partnered women under 45 and can discard unmatched slots. Annual ageing can also move women out of the helper's 15–49 range before its next call.
- The exposed denominator is captured before contact attempts and bounds the exposed arrivals among diseases already present. The per-cell log distinguishes named epidemic routes and supplies the focal cell's death count. The underlying outbreak event retains its link to the disease's origin event.
- A save with populated `dz_log` and `dz_seen` restored both and replayed exactly for 12 seasons, with identical events and digest and no invariant failures. The legacy-format fallback starts with an empty log and infers exposure from positive immunity. Past exposure with zero remaining immunity is lost when loading that format.
- The disease-off arm keeps the legacy outbreak system within this revision. Both arms retain the epidemic response custom. The build notes record the resulting difference from pre-M4a code, consistent with Ben's decision.
- Focused tests passed: 15 passed, 16 deselected. The simulation sources also parsed with the Python 3.10 grammar.

## Trial reading

The reported 300-year planet-3 runs start from the same year-9,700 save and end at 326,491 with named disease off and 358,896 with it on. The notes report no invariant failures. The on arm has one wild-origin disease that circulated in one cell for three years. That documents a short wild-origin episode in one history. The table gives 317 disease deaths for the on arm and 18.7% of all deaths for the off arm, so a magnitude comparison needs common units. The hunger shares alone cannot establish how hunger mortality changed or why.

Both latest herd run titles name code `66dea8c`. When checked, the on run was in progress and the off run had failed. The off run reported empty `fromJson` inputs for the simulation job matrices. There was no completed paired result to review. [On run](https://github.com/b392da-sketch/origins/actions/runs/44688553058) · [Off run](https://github.com/b392da-sketch/origins/actions/runs/44688555405)
