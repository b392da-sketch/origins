# Review 030 — review-029 fixes

Codex, 20 November 2026. Reviewed `e46a8af..417e838`.

## Findings

### 1. Partial moves and new conceptions can still overfill pregnancy slots

- **Where** — `origins/sim/groups.py:217–239,337–367,408–448`.
- **What is wrong** — The split and transfer draw uses the fraction of women moving, but the binomial count has no bound based on how many women move or stay. The later conception draw can also add more pregnancies than there are women available.
- **Why it matters** — A valid group can immediately become invalid after a move or conception. Later mortality cleanup can discard a pregnancy solely because of that move or draw.
- **How sure you are** — Certain. Reproduced through `split` and `births`. `transfer` uses the same pregnancy draw as `split`.
- **How to see it** — Give two women one pending pregnancy each, and split off one woman. The draw can send both pregnancies with her. Separately, with one eligible woman and an empty pending queue, the Poisson conception draw can return two. Both results leave two pregnancies with one woman. Ageing and unfolding retain the limitations recorded in review 029.

### 2. An older save's epidemic rows crash the G1 probe

- **Where** — `origins/sim/disease.py:505–512`, `gates/g1.py:126–138` and `gates/g3.py:130–144`.
- **What is wrong** — Loading preserves old nine-field log rows. G1 reads the death count at index 14, and G3 exports the old rows under the new 15-field header.
- **Why it matters** — A resumed G1 run can stop at its first unread old row. G3 can silently present an old row's death count as the new column for deaths among previously unexposed bands.
- **How sure you are** — Certain. Reproduced the G1 exception and G3 export with a review-029-format row.
- **How to see it** — Load a save with a disease row ending in `[..., true, 1]` and probe it with an unread row. G1 raises `IndexError`. G3 exports that same row as nine values under 15 column names.

### 3. The exposure record can turn a previously exposed band into a naive one

- **Where** — `origins/sim/disease.py:82–107,505–512` and `origins/persist.py:231–235`.
- **What is wrong** — The loader ignores the older `dz_seen` array, so `_last_rows` can only recover exposure when immunity is positive. A later join takes the numeric maximum, so `-1` (never met) beats `-2` (met, date unknown).
- **Why it matters** — Previously exposed bands and their deaths can be counted as naive when an older save is resumed.
- **How sure you are** — Certain. Reproduced both paths.
- **How to see it** — Load a review-029-format save with `dz_seen=True` and zero immunity. The band becomes `-1`. Give another band positive immunity so the fallback marks it `-2`, then move people from it into a band marked `-1`. The destination is again marked `-1`.

### 4. G1 dates batched outbreaks at the end of the batch

- **Where** — `gates/g1.py:126–147,394–404`.
- **What is wrong** — The probe groups rows by their recorded year and cell, then dates every watch entry with the current probe year and takes its births baseline then. The built-in replay check advances 40 seasons before probing again.
- **Why it matters** — The one- and 20-year recovery windows can start up to nine years late in the ten-year batch, and births between the epidemic and the delayed probe are excluded.
- **How sure you are** — Certain. Reproduced the delayed probe and traced the batch in the worker.
- **How to see it** — Feed a probe at year 12 two unread epidemic rows from years 2 and 3. It creates two watch entries dated year 12. Calling the probe repeatedly at that same world time does not recover the intervening measurements.

### 5. Time since exposure cannot identify first contact between long-separated peoples

- **Where** — `origins/sim/disease.py:58–63,97–107,404–430` and M4 specification, G4a check 10.
- **What is wrong** — The interval records time since the most recent circulation among any previously exposed band at the destination. It tracks no history of contact between the source and destination peoples. Each joined band also has one exposure date, and each cell row pools the people and deaths of destination bands with different dates.
- **Why it matters** — The export can compare deaths per person by recorded band exposure. It cannot measure the check's comparison after first contact between long-separated peoples, or assign deaths to distinct exposure intervals within a mixed cell.
- **How sure you are** — Certain from the recorded fields.
- **How to see it** — A year-100 contact row can show one year since last exposure because one band met the disease in year 99, even if a much larger band last met it in year 20. Their people and deaths are pooled. The same row could be produced if source and destination had traded every year or had never met.

### 6. G3 sampling favours shorter or more local disease histories

- **Where** — `gates/g3.py:128–144`.
- **What is wrong** — Once it keeps any disease, the sampler skips each history that exceeds the remaining row budget. Widely circulating or persistent diseases can be preferentially excluded. A history larger than the entire budget is retained only when it comes first, and then exceeds the budget.
- **Why it matters** — Kept histories remain complete, so herding and nearby population can be compared with persistence within those histories. The sample can underrepresent the persistent diseases check 10 is meant to assess. Unsampled global event totals cannot supply the missing local herding or population data.
- **How sure you are** — Certain. Reproduced through the G3 export.
- **How to see it** — Give one disease 100,001 rows and four other diseases one row each. With world and run seeds both 1, G3 retains all four short histories and drops the longest. Across permutations, the long history is included only if it comes first.

### 7. G1 check 9 can mix incompatible counters or pass without an unexposed comparison

- **Where** — `origins/sim/disease.py:195–212`, `origins/sim/hazards.py:203–233`, `origins/persist.py:139` and `gates/g1_report.py:236–247`.
- **What is wrong** — The report pools the same four keys across legacy and named runs and across old and new portions of resumed runs. Those keys describe different units and arrival routes across the versions. The pass condition also needs only a positive exposed denominator.
- **Why it matters** — A pooled ratio may not represent any one route or unit. Even a fresh named run can pass with no unexposed disease-cell-years to compare.
- **How sure you are** — Certain from the shared keys and pass formula.
- **How to see it** — For a fresh named run, one contact arrival over one exposed disease-cell-year and zero unexposed opportunities passes. For a resumed run, `w.counts` restores earlier totals under the same keys, so the report adds the new named increments to them and labels the result with both interpretations.

## Checked and sound

- The sole eligible woman's pregnancy moves with her when all eligible women move, and stays when none move. The original rounding fixture now keeps two pregnancies for two women. The cap runs after ordinary, hazard, conflict and disease mortality through the shared helper, and after maternal mortality directly. Full merges sum people and pending slots.
- The adult survivor calculation now weights both death shares. With an explicitly all-older weight the original fixture gives 0.347826. The live path always uses the starting value of 15% older adults, which gives about 0.3711 for the same inputs even in an all-older band.
- Later epidemics log the surviving people left after earlier epidemics that year. For a normally timed probe with current rows, G1 uses the first baseline and sums the year's deaths on that cell. Recovery population and births use that same cell.
- Fresh named runs use disease-cell-years on both sides of G1 check 9. A return from animals in an exposed cell contributes zero to contact arrivals. New diseases increment separate counters. The current report's two rates describe route-specific arrivals in exposed and unexposed units, so neither should be read as the total chance of illness in its group.
- `dz_last` preserves existing rows on growth, fills new rows with `-1`, inherits the parent row on splits and takes the latest of two known years at joins. A current-format save round-tripped the populated log and date array. Changing a date changed the digest. A 12-season replay matched events and digest with no invariant failures.
- A complete current G3 log has the origin host, local herder count, nearby population and arrival route needed to compare local circulation histories with herding and density. It also provides separate people and deaths for bands with and without recorded prior exposure. Findings 5 and 6 limit what those comparisons establish.
- The focused suite passed with 21 passed and 16 deselected. The simulation and gate sources parsed with the Python 3.10 grammar.

## Trial reading

The build notes report one 300-year planet-3 pair with no invariant failures. The on arm's single wild-origin disease circulated for four years across up to nine cells. This is an example of short wild-origin circulation. The off-arm disease share and on-arm disease count still need common units for a mortality comparison. The herd trial answer identifies both arms as pre-fix code `66dea8c`. Both runs were in progress when checked, so the pair provides no completed comparison for this review. [On run](https://github.com/b392da-sketch/origins/actions/runs/44688553058) · [Off run](https://github.com/b392da-sketch/origins/actions/runs/44699787372)
