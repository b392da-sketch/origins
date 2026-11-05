# Origins — M0 "the first people survive"

A self-running world that begins with three neighbouring bands of 30 people (one people of 90) about 50,000 years before the present. This is milestone M0 of the design in `../DESIGN_DRAFT_v0.5.md` and `../M0_SPECIFICATION_v1.1.md`.

## Start it

**Windows:** double-click `start_windows.bat`. It looks for Python 3.10 or newer, installs NumPy once if needed, and opens the observatory at http://127.0.0.1:8770.

If it says Python was not found, install Python from https://www.python.org/downloads/ (tick **Add python.exe to PATH** during installation), then run it again.

**macOS/Linux:** `sh start_mac_linux.sh`, or `python3 run.py`.

Keep the window open while you watch; closing it (Ctrl+C) saves the world to `saves/autosave.zip` and the next start continues from there. The three previous autosaves are kept as `autosave.bak1`–`bak3`. If an autosave can't be read, it is set aside as `unreadable-autosave-….zip`, never overwritten.

## Using the observatory

- **Run / Pause.** Normal speed is 300 simulated years per real day: one season every 72 seconds.
- **+10 / +100 / +1000 years** fast-forwards, then pauses.
- **Click a band** to see its people, food, land and history. **Follow** it to slow the whole world to a speed you set with the slider (from two minutes per season up to many seasons a minute). Stop following to return to 300 years a day. Following a *group* brings it back to life as named individuals.
- **Click a person** for their family, their PIE-inspired name and its etymology, and their birth and death.
- **Why?** Click any birth, death or event to trace its causes, step by step.
- **Unknown land** stays dark until someone reaches it.

## What M0 contains

- A generated planet (a quarter of Earth's surface, 40,962 hexagonal cells of about 3,100 km²): continents, mountains, rivers, lakes, climate with seasons, biomes, wild food, and (unused until later milestones) minerals and domesticable species.
- Individual people with kinship, body condition, partnerships, births and deaths; bands that forage, share food, move, split and merge.
- Good and bad years by region; hunger arising from too little food, never rolled as an event.
- Above 20,000 individuals, bands far from your focus fold into groups (counts by age and sex) that follow the same rules. Followed bands always stay individual.
- Saves that reload exactly; a check every season that no person or food appears or disappears without a recorded cause.

## What it does not contain yet

Hazards such as floods and eruptions, languages and sound change (names are PIE-inspired but do not change yet), technology, farming, trade, conflict, leaders, belief and religion, and god powers. These are later milestones in the design draft.

## Verifying

```
python -m unittest discover -s tests -v        # automated tests
python -m gates.g0 runs --workers 2             # gate G0: 5 planets x 20 histories x 2,000 years (hours)
python -m gates.g0 shock
python -m gates.g0 report
```

The latest gate result is in `docs/M0_GATE_REPORT.md`. All numbers in `origins/params.py` are tunable starting values, not measurements; the simulation is synthetic and uncalibrated.
