# Review 031 — review-030 fixes

Codex, 20 November 2026. Reviewed `528a7c9..3c2e85b`.

Start the comprehensive pre-gate review with findings 1 and 2 open. Both should block sign-off on G4a check 10. Finding 3 should block any sign-off that uses G1's named-outbreak recovery results. Finding 4 should block use of a mixed-version checkpoint for G1 check 9 unless its historical counters can be attributed. Carry these into the comprehensive review.

## Ranked findings

### 1. A same-year restart can qualify a young source as a generation-old source

- **Where** — `origins/sim/disease.py:177–187,247–254` and `gates/g3.py:136–151`.
- **What is wrong** — When a disease fails the persistence step and returns to the same cell later that year, `dz_since` keeps the old start year because the cell was active last year and is active at year's end. G3 starts a new spell at that arrival.
- **Why it matters** — A contact row can pass Ben's 25-year source criterion even though its source's current spell is younger. That puts deaths and people from the wrong arrivals into the first-contact comparison.
- **How sure you are** — Certain. Reproduced through the yearly simulation path.
- **How to see it** — Keep a source active from year 0 through 25. In year 26 let persistence fail and force an animal return to that same cell. In year 27 let it reach a naive neighbouring band. The contact row reports 27 years at the source, although the exported spell restarted in year 26.

### 2. Spell summaries cannot establish that herding and density coincided

- **Where** — `gates/g3.py:132–154`, especially the separate maxima at lines 144–145.
- **What is wrong** — G3 keeps joint herding and population observations on arrival rows. In subsequent years it reduces the spell to independently measured maxima. A spell can have its most herders and its highest nearby population in different years.
- **Why it matters** — The export can compare spell length with origin host, starting size, and either peak separately. It cannot establish that persistent circulation is found mostly where herds and dense populations meet during circulation.
- **How sure you are** — Certain. Reproduced through the G3 export.
- **How to see it** — After an identical arrival, give a spell a year with 1,000 nearby people and zero herders, then a year with 100 nearby people and 50 herders. The export says 1,000 and 50. It gives the same result if both maxima occur in the same year. The two histories can also have identical durations and deaths.

### 3. G1 fills the one-year recovery observation on the first probe

- **Where** — `gates/g1.py:136–150,397–404` and `origins/state.py:435–440`.
- **What is wrong** — G1 now stores the epidemic's year from the row, then immediately subtracts it from the probe's current year. Its normal probe runs after stepping across the year boundary, so the new watch already has age 1. The births baseline and one-year births are read in the same probe.
- **Why it matters** — The year-end population of the outbreak year is reported as the one-year follow-up, and the one-year births measure is always zero for these watches. The 20-year observation also comes one annual probe earlier relative to its births baseline.
- **How sure you are** — Certain. Reproduced with two consecutive probes.
- **How to see it** — Supply an epidemic row for year 2. At the normal post-year probe, `w.year` is 3. G1 immediately sets `after1` and `births1 = 0`. Add nine births before the next annual probe. The stored `births1` stays zero.

### 4. Pre-031 named-disease counters can still be reported as M1 outbreaks

- **Where** — `origins/persist.py:139`, `origins/sim/disease.py:239–245` and `gates/g1_report.py:236–256`.
- **What is wrong** — New increments have distinct keys. The loader still restores old counters unchanged, and the report assumes any `ob_*` totals come from M1. The named-disease implementation in the previous revision wrote to those keys too.
- **Why it matters** — Resuming such a checkpoint can produce a bogus M1 comparison alongside a valid named comparison. G1 combines the per-mechanism marks, so the stale totals can change the result.
- **How sure you are** — Certain from the previous and current writers, the loader and the report.
- **How to see it** — Resume a review-030 checkpoint produced with named diseases on and nonzero `ob_*` counters. Continue with named diseases on. The old named totals appear under “M1 outbreaks” and the new totals under “named diseases.”

## Checked and sound

- Pregnancy capacity held in the original fixtures. A split or transfer that moves one of two pregnant women moves one pregnancy and conserves both. The stressed conception case stays within the available slots. The ageing and unfolding limits from the earlier review remain.
- Both legacy row formats upgrade to the current header and G1 accepts the upgraded rows. The legacy `dz_seen` flag survives at zero immunity as `-2`, and joining preserves it against `-1`. A current-format save round-tripped `dz_since` and the populated log. Changing `dz_since` changed the digest. The 12-season replay matched events and digest with no invariant failures.
- G1's replay check now probes at each annual step. Watch entries retain the epidemic's recorded year. Finding 3 covers the conversion from that year to the recovery intervals.
- The three exposure groups are recorded as separate people and death counts. A controlled arrival with 25 source years and bands last exposed 24 and 25 years earlier places them in the recent and older groups respectively, with the naive group separate. After the source-age correction, use qualifying contact arrivals with naive people and compare deaths per person across the three groups. Older rows lack source age, older checkpoints start `dz_since` afresh, and their unknown exposure dates can be counted in the older group. A fresh history avoids those limitations.
- G3 retains all arrival rows and spells. It distinguishes a new arrival from a kept year even when the years are adjacent. Host and first arrival population allow comparisons of wild-origin and small starts with spell duration. Spells still circulating when observation ends are incomplete histories, and finding 2 limits the comparison with joint herding and density.
- On fresh runs, G1 uses distinct counters and prints both mechanisms separately when both have data. A named mechanism with one exposed arrival and no comparison opportunities failed even with a passing M1 row. Its detail still prints a ratio of a trillion in that case. That ratio is undefined, and the reported failure is correct.
- Focused tests passed with 26 passed and 16 deselected. The simulation and gate sources parsed with the Python 3.10 grammar.

## Trial reading

The build notes' latest 300-year planet-3 pair reports no invariant failures. Its five wild-origin diseases circulated for 1–18 years and faded in that history. The reported episode lengths give examples for the first half of check 10. The notes supply neither a comparison with persistent episodes in dense herding areas nor a qualifying three-group first-contact comparison. I did not start a gate-length run.
