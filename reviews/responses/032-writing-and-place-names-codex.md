# Review 032 — writing and place names

Codex, 21 November 2026. Reviewed `cbcedad..d7ddb9c`.

Resolve findings 1–4 before starting G4a under the current specification. Finding 1 can also be resolved by an explicit scope decision from Ben. Findings 5–6 affect how the results and cause chains can be read. Writing's rarity in these trials is consistent with Ben's decision to let the gate test it.

## Ranked findings

### 1. The build omits documented M4a place-name outputs

- **Where** — M4 specification sections 7 and 10, the build notes' “Not built” paragraph, `origins/sim/places.py:25–36,220–239` and `origins/server.py:646–685`.
- **What is wrong** — The specification calls for region names and for local names and historical layers in the observatory. The simulation creates no region features, and the observatory exposes neither the place map nor the layer history. The build notes record these omissions without a corresponding change to the approved scope.
- **Why it matters** — The stored geography names cannot deliver the specified observer view, and a successful gate run would leave those deliverables incomplete.
- **How sure you are** — Certain.
- **How to see it** — Check `KINDS` and the feature builders for regions, and look for a place endpoint among the observatory routes. `places.display` and `places.history` exist as Python helpers only.

### 2. A name can omit a sound change made on its naming tick

- **Where** — `origins/engine.py:33–37` and `origins/sim/places.py:173–207,249–264`.
- **What is wrong** — The language phase changes the lexicon before the places phase. On that tick, `generic` excludes the rule at its cutoff, so a compound can combine the already changed descriptor with a pre-change generic. The stored layer then skips the naming tick when calculating its later form.
- **Why it matters** — The generic can stay wrong for the lifetime of the layer and be inherited in that form by daughters.
- **How sure you are** — Certain. Reproduced with a rule that transforms the river generic.
- **How to see it** — Apply `laryngeal_loss` to the naming language at tick 42 and query its river generic at 42 and 43. The one at 42 still contains the proto token. A layer made at 42 cannot pick up that rule later because `evolve` requires `t > after`. The same cutoff also excludes a rule on a dead language's end tick if the history contains one there.

### 3. Conquest-aware replacement can be skipped or depend on band order

- **Where** — M4 specification section 7 and `origins/sim/places.py:323–334,346–378`.
- **What is wrong** — An existing name in the newcomer's lineage bypasses the naming decision, so conquest never creates a replacement layer for such a people. When the decision runs, the conquest check uses only the first band seen for each holder language. Another band of the same language may be the one that was conquered.
- **Why it matters** — Conquests can leave no trace in the place's name history, and the keep probability can depend on iteration order even when the inhabitants and their conquest histories are identical.
- **How sure you are** — Certain. Reproduced the representative-band case and traced the early exit.
- **How to see it** — Put two bands of the holder language and a newcomer by the same river. Make the newcomer the seat of the polity that recently conquered the second holder band. The call to `keep_chance` gets `conquest=False` when the first holder band is unconquered. If the newcomer already has a layer, the call is skipped entirely.

### 4. The gate record cannot distinguish active writing from remembered writing

- **Where** — `gates/g3.py:56–62,93–120`, `gates/g2.py:37–74` and the 21 November decision in the build notes.
- **What is wrong** — The current export gives technique events and endpoint skill thresholds. It lacks observations of when qualifying seats actively wrote, their scribe counts, and when writing stopped being practised. A polity's tier history alone cannot supply those observations.
- **Why it matters** — Ben explicitly left the finding about writing's survival to G4a. Two histories with the same invention and loss events can spend different lengths of time writing, including different intervals when a script was remembered but could no longer be used.
- **How sure you are** — Certain for the current gate record.
- **How to see it** — A band with writing stored at 0.6 counts as holding working writing in `tech_held` whether it has no scribes or 30. The trial script already reports a separate practising count. The gate export has no equivalent endpoint or time series to compare with complex-chiefdom or state tenure.

### 5. The stimulus flag identifies exposure to writing, including inventions that pass the baseline draw

- **Where** — `origins/sim/technology.py:618–642` and `local/scripts/trial_places.py:55–57`.
- **What is wrong** — Every successful invention with an eligible source is attributed to stimulus. The event does not distinguish a draw below the original chance from a draw that only succeeds with the multiplier.
- **Why it matters** — The flag supports counting inventors with a practising neighbour. Reading that count as inventions caused by the extra chance overstates the demonstrated effect.
- **How sure you are** — Certain. Reproduced through `technology.yearly`.
- **How to see it** — Give two nearby bands working tallies and scribes, and give only the first band working writing. A zero draw invents writing in the second band even at the positive baseline chance. The event still carries the first band as its stimulus source.

### 6. Borrowed layers lack a traversable cause linking them to the inherited name

- **Where** — `origins/sim/places.py:366–402` and `origins/explain.py:40–52,269–293`.
- **What is wrong** — The layer stores a donor-language ID and the event's note describes the source. The event's only structured cause is the band giving the new name, with no link to the donor's layer or its naming event.
- **Why it matters** — A borrowed name can pass `explain.resolvable` even though its earlier naming cannot be reached from the cause chain.
- **How sure you are** — Certain. Reproduced from a kept river name.
- **How to see it** — Open the cause chain of a `place_named` event with `how="kept"`. Its band reference takes you to the borrowing band's origin, and the donor name appears only in the note.

## Checked and sound

- Scribes grow towards the specialist count only at living qualifying seats and decay towards zero elsewhere. The retained average makes a drop in tier gradual, as Ben decided. Normal keeping uses 30 scribes within reach. `_possible` and `prerequisites_met` both enforce the one-scribe minimum for practice.
- Growth preserves existing scribe counts and a daughter starts with zero scribes and zero writing. Whole joins add scribes and clear their old row. Partial migration does not transfer the script. Working tallies with keepers receive the capacity bonus and compete with writing for that part of the multiplier.
- The stimulus multiplier uses a practising writer within two rings or an eligible trade link. Invention starts at the same crude level as other invention.
- The geographic cache is deterministic. River cells partition into streams following their higher-flow branches. Lake shores, local peaks and region-bounded coast components map to their documented use cells. Settlements persist by cell. The naming probability and the keep probability move in the documented directions for size, remoteness and population. The first-contact cases preserve older layers and apply later sound changes on the inheriting or borrowing lineage.
- A save with names and scribes round-tripped and replayed for 12 seasons with identical events and digest and no invariant failures. Two independent loads of a legacy-format fixture also replayed identically. They started with no names and derived scribes from the qualifying live seat only. The simulation sources parsed under the Python 3.10 grammar.
- All 77 focused tests in `test_places.py`, `test_m4.py` and `test_disease.py` passed.
- A short synthetic planet-3 timing covered the places phase only. The 40,962-cell feature cache took 0.016 s to build. A dispersed fixture with 20,000 bands and 250 languages took 0.058–0.073 s per measured naming pass. A forced single-feature stress case took 0.30 s for 300 layers and 8.41 s for 900, consistent with repeatedly scanning the accumulated layers for each potential donor. No gate-length run was started.

## Trial reading

The seeded trials show that writing was gone after 100 years in the two reported configurations and that complex chiefdoms fell from 28 to one in the tier-2 trial. That is consistent with the loss of scribal support. The trials do not isolate short polity tenure from access to other writers, the keeping threshold, or other prerequisites. In particular, the older save initializes scribes to 20–38 at the seeded complex seats immediately. A 25-year averaging period by itself does not show that those seats needed 25 years to acquire scribes before the trial. The median of 30 years comes from a polity log sampled every ten years, so it is a coarse tenure estimate. The 60 in the invention formula scales difficulty and is not a minimum number of scribes. The live path can invent with one. Ben's gate decision is consistent with these limits.
