# Origins — working rules for Claude sessions

Ben owns the design. Read `docs/DESIGN_DRAFT_v0.6.md` (or newer) and the current milestone spec (`docs/M3_SPECIFICATION_v1.md`) before changing anything. Ben approves milestone gates only; propose design changes, don't make them silently.

## Rules
- **Behavioural gates decide progress, not test counts.** No new layer until the current gate passes. Record failed attempts and negative results in `docs/`.
- **Nothing from nothing.** Food, people (and later goods and money) are conserved; every quantity has a recorded source. `sim/observe.py` checks this every season.
- **Causes are recorded.** Every event or person-level happening must be explainable through `origins/explain.py`.
- **Data plus systems.** State is plain data (`state.py`, `sim/groups.py`); systems in `origins/sim/` declare what they read and write; the phase order is in `engine.py`. No version-layered subclasses.
- **Separate random streams** per subsystem (`state.STREAMS`). Never draw from another system's stream. Append new streams at the end; never insert.
- **Exact replay.** Saves round-trip exactly (`persist.digest`). Keep `tests/test_m0.py::Replay` passing.
- **Python 3.10+ and NumPy only** for running. Keep code 3.10-compatible (Ben's machine environment runs 3.10).
- Numbers in `params.py` are tunable starting values, not facts. Say so wherever results are reported.

## Layout
- `origins/worldgen.py` planet from a seed · `origins/grid.py` geodesic grid · `origins/noise.py`
- `origins/state.py` world state · `origins/engine.py` phase order · `origins/sim/*` systems
- `origins/persist.py` saves · `origins/explain.py` cause chains · `origins/interventions.py`
- `origins/server.py` + `observatory/index.html` the observatory
- `origins/lang/` proto-language and sound-change catalogue · `sim/language.py`, `sim/customs.py`, `sim/hazards.py` (M1)
- `gates/g0.py`, `gates/g0_slice.py`, `gates/g0_report.py` gate G0 · `tests/test_m0.py`

## Current milestone
M0 "the first people survive": gate G0 passed and **closed with Ben's approval on 6 November 2026** (`docs/M0_GATE_REPORT.md`).
M1 "spreading and drifting apart": specification **approved by Ben on 6 November 2026** (`docs/M1_SPECIFICATION_v1.md`, decisions in section 9); gate G1 passed on 60 histories and **closed with Ben's approval on 7 November 2026** (`docs/M1_GATE_REPORT.md`). Open items carried forward: island peoples do not diverge faster; outbreaks cause about 9% of deaths.
M2 "farming is an option, not a destiny": specification **approved by Ben on 7 November 2026** (`docs/M2_SPECIFICATION_v1.md`); gate G2: 9 of 10 checks passed on 70 histories; **closed with Ben's approval on 9 November 2026** with check 9 (inequality keeps rising with time) recorded as failed and carried forward (`docs/M2_GATE_REPORT.md`, decision and carried-forward items at the end). G1 rerun with the final code passes (`docs/M1_GATE_RERUN3_REPORT.md`).
M3 "scale needs institutions; conflict has causes and costs": specification **approved by Ben on 9 November 2026** (`docs/M3_SPECIFICATION_v1.md`, decisions in section 11); in build. Order: world-generation fix, speed pass, polities, institutions, behaviour-5 trial gate, conflict, inequality, notables, observatory, G3. Gates run on GitHub Actions (`.github/workflows/gate.yml`).
