# Origins

A self-running world that begins with three neighbouring bands of 30 people (one people of 90) about 50,000 years before the present, and lets them make of it what they will.

**Where it stands (14 November 2026):**
- **Complete:** M0 "the first people survive", M1 "spreading and drifting apart", M2 "farming is an option, not a destiny" and M3 "scale needs institutions; conflict has causes and costs". Each closed with Ben's approval after its gate; failed and waived checks are carried forward (see the gate reports in `docs/`).
- **In build:** M4a "knowledge and exchange". Done so far: circumscription, pastoralism, herd inequality and the technology network. Still to come: trade, the land answering back, diseases from animals, and writing and place names. Then gate G4a, and M4b "how wars are fought, and who people are to each other".

Design and specifications are in `docs/` (and in Ben's project files).

## Start it

**Windows:** double-click `start_windows.bat`. It looks for Python 3.10 or newer, installs NumPy once if needed, and opens the observatory at http://127.0.0.1:8770.

If it says Python was not found, install Python from https://www.python.org/downloads/ (tick **Add python.exe to PATH** during installation), then run it again.

**macOS/Linux:** `sh start_mac_linux.sh`, or `python3 run.py`.

Keep the window open while you watch; closing it (Ctrl+C) saves the world to `saves/autosave.zip` and the next start continues from there. The three previous autosaves are kept as `autosave.bak1`–`bak3`. If an autosave can't be read, it is set aside as `unreadable-autosave-….zip`, never overwritten.

## Using the observatory

- **Run / Pause.** Normal speed is 300 simulated years per real day (one season every 72 seconds) until the first farming village, then 20 years per real day.
- **+10 / +100 / +1000 years** fast-forwards, then pauses.
- **Click a band** to see its people, food, land and history. **Follow** it to slow the whole world to a speed you set with the slider (from two minutes per season up to many seasons a minute). Stop following to return to 300 years a day. Following a *group* brings it back to life as named individuals.
- **Click a person** for their family, their name and how it came to sound that way in their own language, and their birth and death.
- **Show** recolours the map: land; related languages in related colours; shared customs; recent floods, fires, eruptions, earthquakes, outbreaks and sea crossings; farming and its spread; surplus; polities (seats ringed, thicker for complex chiefdoms and states); and wars.
- **Peoples and languages** lists the living languages; open one for its descent, sound changes, closest relatives and its words beside the proto-language.
- **Why?** Click any birth, death or event to trace its causes, step by step.
- **Unknown land** stays dark until someone reaches it.

## What it contains

- **A generated planet** (a quarter of Earth's surface, 40,962 cells of about 3,100 km²): plate tectonics with mountain belts, volcanoes and earthquake zones; rivers, lakes, climate with seasons, biomes, wild food; minerals and domesticable species placed for later milestones.
- **People** with kinship, body condition, partnerships, births and deaths; bands that forage, share food, move, split and merge. Above 20,000 individuals, distant bands fold into groups that follow the same rules.
- **Languages** from a PIE-inspired proto-language: regular sound changes, word replacement, borrowing, splitting and language shift. Personal names are built from each language's own words, so they change as the language changes.
- **Customs** (eight named practices plus neutral drift), copied between neighbours and changing at random; marriage residence decides where couples live.
- **Hazards:** floods, wildfires, volcanic eruptions, earthquakes and disease outbreaks, each where it can happen; rare sea crossings to visible islands.
- **Farming (M2)** as an option, not a destiny: wild plants and animals are tended, cultivated and domesticated where people stay put; bands farm when it pays better than foraging, and villages follow. Surplus feeds specialists; households hold property and inherit it by custom, and inequality is measured between households.
- **Polities and conflict (M3):** villages join chiefdoms and states only as far as their institutions can bear the load (councils, collectors, warriors, officials); polities split, fall and are conquered. Wars have recorded causes (scarcity, strength, cultural difference, grievance, a new leader, warriors to feed) and costs (deaths, captives, stores and settlements taken). Where open land lies nearby, villages under rule can flee to it, so states form more readily where people are hemmed in (Carneiro 1970).
- **Pastoralism and herds (M4a):** herding peoples move with their herds; herds breed for the well-off and shrink for the poor (a poverty trap).
- **A technology network (M4a):** 27 techniques, from fire-hardened points and cordage to pottery, irrigation, the plough, smelting and writing, each needing other techniques, materials, domesticates, land or a settled people. Inventions are rare and crude, improve slowly with practice, spread by contact, migration, marriage and capture, and are lost where too few skilled people remain or forgotten when they can no longer be practised. Writing keeps records from which lost knowledge can be recovered. Each technique changes something that already exists: foraging and farming returns, storage, sea crossings, land, or what a polity can manage.
- Saves that reload exactly; a check every season that no person or food appears or disappears without a recorded cause; every death and event traceable to its causes.

## What it does not contain yet

Trade, the land answering back (soil exhaustion, salting), diseases from animals, writing and place names (rest of M4a); how wars are fought and who people are to each other (M4b); belief and religion (M5); and god powers. The observatory does not yet show technology.

## Verifying

```
python -m unittest discover -s tests -v        # automated tests
python -m gates.g0 runs --workers 2             # gate G0: 5 planets x 20 histories x 2,000 years (hours)
python -m gates.g0 shock
python -m gates.g0 report
python -m gates.g1 run --jobs 1:1,2:1 --years 5000 --workers 2   # gate G1 histories
python -m gates.g1 groups --worlds 1-5
python -m gates.g1 report
python -m gates.g2 run --jobs 1:1 --workers 1    # gate G2 histories (long; best run on GitHub)
python -m gates.g2 report
python -m gates.g3 run --jobs 1:1 --workers 1    # gate G3 histories (long; best run on GitHub)
python -m gates.g3 report
```

Gate reports: `docs/M0_GATE_REPORT.md`, `docs/M1_GATE_REPORT.md`, `docs/M2_GATE_REPORT.md`, `docs/M3_GATE_REPORT.md`. Build notes for each milestone (trials, failed attempts, decisions) are in `docs/M*_BUILD_NOTES.md`.

## On GitHub

- **tests** runs the automated tests on Python 3.10 and 3.13 for every change to `main`.
- **gate** runs a gate on GitHub's machines, one history per machine, many at once. To start one, push a request file (see `gates/requests/`) to the `gate` branch, or use *Run workflow* on the Actions page and name the file. Results and the report appear on the `gate-results` branch under `results/<label>/`. All numbers in `origins/params.py` are tunable starting values, not measurements; the simulation is synthetic and uncalibrated.

## Independent review

Codex reviews every gate report before Ben decides on it, and each completed build step before its code goes into a gate run. Requests and answers are in `reviews/` (rules in `reviews/README.md`, log in `reviews/LOG.md`). Claude reproduces each finding before acting on it. Codex writes only to `reviews/` (`AGENTS.md`). Working rules for Claude sessions are in `CLAUDE.md`.
