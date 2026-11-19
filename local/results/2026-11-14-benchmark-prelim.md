# Result: 2026-11-14-benchmark-prelim

Request: `local/requests/2026-11-14-benchmark-prelim.json`. Raw timings: `local/results/2026-11-14-benchmark-prelim/p3.json`.

## Machine: NOT Ben's laptop

This ran in a **Claude Code cloud container**, not on Ben's laptop (i5-13420H, 12 threads, 16 GB, Windows). The timings describe this container only and are not the laptop benchmark that `docs/HANDOVER_CLAUDE_CODE.md` asks for. The request should be run again on the laptop for laptop numbers.

- CPU: Intel(R) Xeon(R) Processor (model not exposed), 4 vCPUs
- Memory: 15 GB, no swap
- OS: Linux 6.18.44 x86_64 (glibc 2.39)
- Python 3.13.18, NumPy 2.5.3
- Priority: `nice -n 10` (below normal), one process, nothing else heavy running

## What ran

- Commit: `8ab3c07` (= `main` at run time)
- Setup check: `python -m pytest -q tests`: 81 passed (480 s)
- Command: `python local/scripts/bench.py 3 1 10000 local/results/2026-11-14-benchmark-prelim/p3.json 8500 local/bench/p3s1_8500.zip`
- Run P3: planet 3, seed 1, fresh, 10,000 years. Started 2026-11-14 04:42 UTC
- **Total time: 2303.6 s (38.4 min)**, mean 0.230 s per simulated year
- **Peak memory (max RSS): 861.9 MB**
- Saved world at year 8,500: `local/bench/p3s1_8500.zip` (61 MB, not committed; `local/bench/` is in `.gitignore`)
- The run finished normally, with no errors or warnings.

Parameters are the current `params.py` values (tunable starting values, not facts).

## Per 500-year block

| To year | Seconds | s / year | Population | Bands | Polities | First village | Peak MB | Three slowest phases (s) |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 500 | 6.1 | 0.012 | 1,040 | 35 | 0 | – | 233.3 | foraging_and_eating 1.8, technology 1.1, hazards 0.8 |
| 1,000 | 31.1 | 0.062 | 39,553 | 845 | 0 | – | 233.3 | conflict 6.4, partnerships 5.5, technology 3.1 |
| 1,500 | 111.7 | 0.223 | 126,545 | 958 | 0 | – | 248.8 | conflict 27.9, fission_merge 15.8, partnerships 9.6 |
| 2,000 | 101.3 | 0.203 | 133,725 | 888 | 0 | – | 287.8 | fission_merge 24.7, conflict 18.3, group_deaths 12.6 |
| 2,500 | 95.3 | 0.191 | 132,595 | 869 | 0 | – | 331.6 | fission_merge 23.4, conflict 17.8, group_deaths 11.8 |
| 3,000 | 98.9 | 0.198 | 145,667 | 883 | 0 | – | 343.1 | fission_merge 23.6, conflict 18.5, group_deaths 12.1 |
| 3,500 | 105.5 | 0.211 | 129,779 | 894 | 0 | – | 400.7 | fission_merge 25.3, conflict 19.3, group_deaths 12.7 |
| 4,000 | 114.8 | 0.23 | 137,630 | 882 | 0 | – | 413.9 | fission_merge 26.0, conflict 20.3, foraging_and_eating 13.2 |
| 4,500 | 115.3 | 0.231 | 136,719 | 894 | 0 | – | 422.5 | fission_merge 25.9, conflict 20.1, foraging_and_eating 13.2 |
| 5,000 | 118.3 | 0.237 | 133,530 | 880 | 0 | – | 438.1 | fission_merge 25.8, conflict 20.4, foraging_and_eating 13.5 |
| 5,500 | 112.9 | 0.226 | 134,698 | 891 | 0 | – | 550.8 | fission_merge 24.3, conflict 20.0, foraging_and_eating 16.7 |
| 6,000 | 136.0 | 0.272 | 136,780 | 887 | 0 | – | 567.0 | fission_merge 25.9, foraging_and_eating 25.1, conflict 23.4 |
| 6,500 | 145.4 | 0.291 | 129,203 | 887 | 0 | – | 578.3 | foraging_and_eating 26.9, fission_merge 26.7, conflict 25.1 |
| 7,000 | 144.2 | 0.288 | 144,938 | 903 | 0 | – | 598.7 | foraging_and_eating 26.7, fission_merge 26.0, conflict 24.5 |
| 7,500 | 139.4 | 0.279 | 136,752 | 890 | 0 | – | 610.2 | fission_merge 26.3, foraging_and_eating 25.4, conflict 23.5 |
| 8,000 | 126.2 | 0.252 | 136,278 | 909 | 0 | – | 624.3 | fission_merge 24.5, foraging_and_eating 22.4, conflict 21.6 |
| 8,500 | 153.1 | 0.306 | 138,321 | 888 | 0 | – | 698.0 | fission_merge 25.7, foraging_and_eating 25.0, conflict 23.5 |
| 9,000 | 129.1 | 0.258 | 134,693 | 891 | 0 | – | 698.0 | fission_merge 24.5, foraging_and_eating 22.8, conflict 21.7 |
| 9,500 | 160.9 | 0.322 | 146,996 | 893 | 0 | – | 851.8 | foraging_and_eating 38.0, conflict 26.3, fission_merge 26.1 |
| 10,000 | 158.2 | 0.316 | 144,853 | 905 | 0 | – | 861.9 | foraging_and_eating 38.9, conflict 25.8, fission_merge 25.5 |

## Slowest phases in the last block (years 9,501–10,000)

Block total: 158.2 s.

| Phase | Seconds | Share of block |
|---|---:|---:|
| foraging_and_eating | 38.9 | 25% |
| conflict | 25.8 | 16% |
| fission_merge | 25.5 | 16% |
| farming | 14.6 | 9% |
| group_deaths | 13.1 | 8% |
| technology | 7.7 | 5% |
| hazards | 7.7 | 5% |
| group_births | 4.8 | 3% |

## Anything odd

- **No farming villages and no polities appeared in 10,000 years** (`first_village_year` stays null; polities 0 in every block). The request expected the run to go "from foragers through farming to early polities", so the last blocks measure a forager world of about 135,000–147,000 people in about 900 bands, not a farming or polity world. The `farming` phase does take time (6–15 s per block), so the farming code runs, but no village forms. The year-8,500 save is therefore a forager world too.
- The `partnerships` phase takes 5.5–9.6 s per block during the growth years 500–1,500, then 0.0–0.3 s from year 2,000 on. Reported as measured, without interpretation.
- Peak memory climbs steadily (233 → 862 MB) while population and band counts stay flat after year 1,500.
- Seconds per year rise slowly at a flat population (about 0.19 at year 2,500, about 0.32 at year 10,000), mostly in `foraging_and_eating` (13 → 39 s per block).
