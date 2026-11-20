# Review 028: diseases from animals and the review-027 fix

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `555df19..2b92945` for the disease implementation and `0c44947` for the land fix. Read the M4 specification, the three requested build-note sections, the trial driver and the M3 carry-forward decisions. The findings concern the simulator's accounting, records and gate measurements.

## Findings

### 1. Joining bands double-counts the incoming people in the immunity weight

- **Where** · `origins/sim/disease.py:69–78`, `origins/sim/bands.py:117–128,199–208,237–244,265–269`.
- **What is wrong** · Migration, remnant merge and consolidation transfer people before `carry` calls `disease.combine`. The destination size already includes those people. `combine` adds them again to its denominator. It also uses one weight for both age columns, which cannot preserve age-specific shares when the cohorts differ.
- **Why it matters** · Migrants' immunity history has too little influence on the joining band's state. If the movers have a different age mix, even a corrected all-ages weight would misstate at least one column.
- **How sure you are** · Certain.
- **How to see it** · Move 30 people from a fully immune band into a 30-person band with zero immunity and the same age mix. After the move the destination's size is **60**. The helper sets both shares to **one third** rather than **one half**. This reproduces before any disease draw.

### 2. Mortality and survivor immunity use incompatible population bases

- **Where** · `origins/sim/disease.py:336–348`.
- **What is wrong** · Death probability is clipped against the total cohort instead of the share modeled as affected. The immunity update then treats the whole affected share as surviving and applies the result to the smaller survivor population.
- **Why it matters** · With a case multiplier above one, deaths can exceed the modeled cases. Even below that limit, resistance can accumulate too quickly. Tests with zero fatality cannot catch the survivor mismatch.
- **How sure you are** · Certain.
- **How to see it** · In a synthetic adult cohort of 100, start with 20 immune, 40 affected this pass and eight expected deaths among the affected. The implemented update returns **0.60**, while 52 immune among 92 survivors gives **0.5652**. Separately, a synthetic affected fraction of **0.5** and a combined fatality multiplier of **2** yields a cohort death probability of **1.0** in the code.

### 3. A group can deliver a birth after all of its members have died

- **Where** · `origins/sim/disease.py:375–390`, `origins/sim/groups.py:265–289` and the phase order in `origins/engine.py:20–25`.
- **What is wrong** · The grouped mortality path removes female and male counts and leaves pending deliveries untouched. On the next tick, births run before the empty-band cleanup. The legacy hazard path has the same omission.
- **Why it matters** · A delivery can restore a group with zero survivors. The population ledger balances because it records the delivery as a birth, so that invariant alone cannot detect the invalid state.
- **How sure you are** · Certain.
- **How to see it** · Fold a band, set one delivery due, and use the grouped death helper with a deterministic all-deaths fixture. Its age rows fall to **zero** and all deaths enter the counters. Calling `groups.births` before the cleanup produces **one** newborn in the empty band.

### 4. The G1 contact numerator and denominator count different populations at risk

- **Where** · `origins/sim/disease.py:132–162` and `gates/g1_report.py:236–246`.
- **What is wrong** · Contact arrivals increment the numerator immediately, once per cell and named disease. The later denominator omits cells that any disease has activated. It also counts cells once across all diseases. The revived-reservoir starts do not enter the new-start numerator.
- **Why it matters** · The reported quantity cannot be interpreted as the yearly probability that a contacted area falls ill. Matched exposure and outcome units are needed to retain the G1 mark with named diseases.
- **How sure you are** · Certain.
- **How to see it** · In a two-occupied-cell fixture, start with only the first cell active, let it acquire one successful contact arrival in the second, and suppress unrelated starts. The counters add **one contact arrival over zero contacted cell-years**. The receiving cell becomes active before the denominator is counted.

### 5. The disease records cannot substantiate the sampled contact histories

- **Where** · `origins/sim/disease.py:124–148,326–333,375–390` and `gates/g3.py:121–133`.
- **What is wrong** · `outbreak` links to the original disease event and records the year's provenance as totals in a note. It keeps no structured origin or destination for a particular contact arrival and no link to the outbreak it continued. The G3 output drops even those provenance totals and omits susceptibility, exposure denominators and contact history. Group deaths increment the aggregate outbreak total without a per-group cause record.
- **Why it matters** · A sample can resolve 100% of its references and still leave G4a check 10 unmeasurable. It cannot identify first contact between long-separated peoples or compare deaths in previously exposed and unexposed populations. The same annual event also has one display cell and deaths from all affected cells, so the existing G1 hazard watch can pair a local population trajectory with an unrelated aggregate death count.
- **How sure you are** · Certain.
- **How to see it** · In the two-cell fixture, the event has a valid reference to `new_disease` and a note saying one contact arrival and one continuing cell. The G3 row contains only year, disease, cell count and deaths. Neither record identifies which cell acquired the disease, its prior exposure or its local deaths.

### 6. The knockout preserves the old outbreak routine but changes the wider history

- **Where** · `origins/sim/hazards.py:182–188` and `origins/sim/customs.py:87–125`.
- **What is wrong** · `DISEASE=False` dispatches to the old outbreak routine. The epidemic-response custom still changes the size of the draw for inventions, the range for copying, and the denominator used in cultural distance.
- **Why it matters** · The off arm is a valid switch for the named-disease mechanism within the current revision. It does not reproduce a pre-change history from the same seed.
- **How sure you are** · Certain.
- **How to see it** · Compare the pre-disease revision with the reviewed revision switched off. At the same starting state the hazard RNG and outbreak records match after the isolated hazard phase. The first customs pass starts with the same RNG state but finishes with different states because the widths are **10** and **11**.

## Checked and sound

- **Routing and responses.** The stated emergence inputs are wired to the selected domesticated host and its recorded domestication age. The wild path is separate. Existing named entries are reused for reservoir returns, with matching-host and origin-region checks. The persistence check reads the preceding circulation array, and contact arrivals do not become additional same-pass sources. Contact construction includes local neighbours, reciprocal trade seats and listed gift partners. The response column affects the intended local and outgoing terms. Flight and isolation are modeled through those terms.
- **Age-state implementation.** The child and adult columns update separately and nonlasting entries wane. Aging and susceptibility use fixed cohort fractions, a model approximation rather than the actual age counts. The mortality bookkeeping discrepancy is covered above.
- **Ledgers and links.** The group helper removes integral counts and adds the same number to the overall, cause and age death totals. Individual deaths go through `demography.kill` and carry the named event in `death_hazard`. A herd-origin event can reference the recorded domestication. Individual death and disease-origin references resolve in the focused tests. This verifies the links that exist.
- **State and replay.** The disease stream is appended. Immunity rows grew past band 64 and copied the parent's row. A real pre-change archive widened customs with the new column set to its first variant and loaded empty named disease state. A current archive retained named traits, circulation and immunity, and matched digest and complete events after **12** further seasons with zero ledger failures.
- **Review 027.** The receiver keeps its **60**-unit crop example against the incoming **40** example in the **105**-unit total-transfer fixture. The current-year comparison uses each scaled example. Post-harvest selection by linked amount remains as described in the build notes.

## Trials and design questions for Ben

- The planet-3 trial gives a useful paired comparison for that starting save. It has no domesticated animal in the observed window, so it exercises the wild path and the old outbreak baseline. The **79** events count named disease-years with circulation somewhere. They do not count 79 independent introductions or distinct epidemic episodes. A fall in the share of deaths assigned to disease alongside an increase in the hunger share does not isolate the claimed crowding mechanism. The change in causes also changes both denominators, and the versions produce different population paths.
- G4a should distinguish a first animal-origin record from persistence and from the first arrival by contact. The implementation permits a new origin in small communities, including a wild-origin record, and applies the persistence rule later. The current wording of G4a check 10 reads more narrowly. Confirm which of those outcomes it should mark before treating a single-history trial as gate evidence.
- Both requested GitHub run pages showed **in progress** when checked. The authenticated run API returned forbidden and the completed history outputs were unavailable for independent comparison. The visible workflow runs have different dispatch commits, and the on run's title identifies a separate source revision. Match the effective source revisions and switches in the artifacts before attributing differences to the knockout. [Named model on](https://github.com/b392da-sketch/origins/actions/runs/44651931880) · [Named model off](https://github.com/b392da-sketch/origins/actions/runs/44627692405)

## Validation

**14 focused tests passed** in 68 seconds, with one AnyIO pytest-plugin deprecation warning. The run covers the disease tests, the review-025 land regressions and the existing exact-replay regression. Synthetic accounting fixtures, pre-change archive checks and the short replay are under ignored `reviews/scratch/`. All source files parse with Python 3.10 grammar. I did not start a full suite or a gate-length run.
