# Origins

A self-running world that begins with three neighbouring bands of 30 people (one people of 90) about 50,000 years before the present, and lets them make of it what they will. Milestones M0 ("the first people survive") and M1 ("spreading and drifting apart") are complete; M2 ("farming is an option, not a destiny") is being specified. Design and specifications are in `docs/` (and in Ben's project files).

## Start it

**Windows:** double-click `start_windows.bat`. It looks for Python 3.10 or newer, installs NumPy once if needed, and opens the observatory at http://127.0.0.1:8770.

If it says Python was not found, install Python from https://www.python.org/downloads/ (tick **Add python.exe to PATH** during installation), then run it again.

**macOS/Linux:** `sh start_mac_linux.sh`, or `python3 run.py`.

Keep the window open while you watch; closing it (Ctrl+C) saves the world to `saves/autosave.zip` and the next start continues from there. The three previous autosaves are kept as `autosave.bak1`–`bak3`. If an autosave can't be read, it is set aside as `unreadable-autosave-….zip`, never overwritten.

## Using the observatory

- **Run / Pause.** Normal speed is 300 simulated years per real day: one season every 72 seconds.
- **+10 / +100 / +1000 years** fast-forwards, then pauses.
- **Click a band** to see its people, food, land and history. **Follow** it to slow the whole world to a speed you set with the slider (from two minutes per season up to many seasons a minute). Stop following to return to 300 years a day. Following a *group* brings it back to life as named individuals.
- **Click a person** for their family, their name and how it came to sound that way in their own language, and their birth and death.
- **Show: Languages / Customs / Hazards** recolours the map: related languages in related colours, shared customs, and recent floods, fires, eruptions, earthquakes, outbreaks and sea crossings.
- **Peoples and languages** lists the living languages; open one for its descent, sound changes, closest relatives and its words beside the proto-language.
- **Why?** Click any birth, death or event to trace its causes, step by step.
- **Unknown land** stays dark until someone reaches it.

## What it contains

- **A generated planet** (a quarter of Earth's surface, 40,962 cells of about 3,100 km²): plate tectonics with mountain belts, volcanoes and earthquake zones; rivers, lakes, climate with seasons, biomes, wild food; minerals and domesticable species placed for later milestones.
- **People** with kinship, body condition, partnerships, births and deaths; bands that forage, share food, move, split and merge. Above 20,000 individuals, distant bands fold into groups that follow the same rules.
- **Languages** from a PIE-inspired proto-language: regular sound changes, word replacement, borrowing, splitting and language shift. Personal names are built from each language's own words, so they change as the language changes.
- **Customs** (eight named practices plus neutral drift), copied between neighbours and changing at random; marriage residence decides where couples live.
- **Hazards:** floods, wildfires, volcanic eruptions, earthquakes and disease outbreaks, each where it can happen; rare sea crossings to visible islands.
- Saves that reload exactly; a check every season that no person or food appears or disappears without a recorded cause; every death and event traceable to its causes.

## What it does not contain yet

Farming and settlement (M2), leaders, states and conflict (M3), technology and trade (M4), belief and religion (M5), and god powers.

## Verifying

```
python -m unittest discover -s tests -v        # automated tests
python -m gates.g0 runs --workers 2             # gate G0: 5 planets x 20 histories x 2,000 years (hours)
python -m gates.g0 shock
python -m gates.g0 report
python -m gates.g1 run --jobs 1:1,2:1 --years 5000 --workers 2   # gate G1 histories
python -m gates.g1 groups --worlds 1-5
python -m gates.g1 report
```

Gate reports: `docs/M0_GATE_REPORT.md`, `docs/M1_GATE_REPORT.md`; G1's result files are in `gates/results_g1/`.

## On GitHub

- **tests** runs the automated tests on Python 3.10 and 3.13 for every change to `main`.
- **gate** runs a gate on GitHub's machines, one history per machine, many at once. To start one, push a request file (see `gates/requests/`) to the `gate` branch, or use *Run workflow* on the Actions page and name the file. Results and the report appear on the `gate-results` branch under `results/<label>/`. All numbers in `origins/params.py` are tunable starting values, not measurements; the simulation is synthetic and uncalibrated.
