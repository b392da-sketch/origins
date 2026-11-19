# Review 010: fixes, skilled practitioners and technology effects

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** `90d0478` through stage-5 commit `7631a7f`, on `main` at `5eac503`, with Claude's response to 009 and the requested build-note sections. Existing design/milestone context remains as reviewed in 005–009. No implementation files changed; no gate-length run started. All rates are tunable starting values, not historical facts.

**Result:** the four original 009 cases and the practised-prerequisite ruling check out. Five additional result errors follow. Ordinary save/replay and a short full-engine conservation check pass; those checks do not validate the teaching, food-composition or decision formulas.

## Findings

### 1. Contact teachers and the best practitioner still include people with no skilled adults

- **Where:** `origins/sim/technology.py`, `best_cell` construction in `keep_and_spread`, and lines 477–505 (`teach_cell`, teacher eligibility/weights).
- **What is wrong:** Keeping counts `TECH_PRACTISE_SHARE × adults + specialists`, but contact counts and samples teachers using the band's entire population. The best-quality calculation also admits a band without checking that it has any skilled practitioners.
- **Why it matters:** Losing knowledgeable adults does not remove their band as a source of knowledge. Its children can teach the remaining aggregate skill to adults elsewhere, undermining the reason for the literature change. Teacher probabilities and their recorded practitioner counts also use a different population measure from keeping.
- **How sure you are:** Certain for contact; the same absent skilled-count condition is visible in `best_cell`.
- **How to see it:** Put two folded groups on one cell: **20 ten-year-old children** with cordage 0.8, and **40 adults aged 25** without cordage, with no specialists. `_adults` correctly returns **[0, 40]**. Supply a successful adoption draw. The children's cordage declines to **0.7678112**, but the adults learn **0.4606867** from them. The event calls the children “20 of the 60 people within reach [who] practised it,” although that source has zero skilled practitioners under the new formula.

### 2. A crop-only effect increases animal food on mixed farms

- **Where:** `technology.farm_multipliers`; `farming.season_food_live`, where total `grown` is multiplied and then split using the unchanged animal fraction.
- **What is wrong:** Crop and animal bonuses are weighted into a multiplier on the whole farm output, then divided using the old composition. A crop bonus therefore increases herd food too, and an animal bonus can increase standing crops.
- **Why it matters:** Effects reach the wrong source and season. Ploughing can create immediately available herd food instead of increasing only the crop awaiting harvest. The aggregate total remains ledgered, so conservation checks miss this composition error.
- **How sure you are:** Certain.
- **How to see it:** Use grain and cattle values both **1**, farming share 1, and 240 effort units, outside harvest. Without the plough, production is **150 herd food + 150 standing crop**. Give practised plough/draft-animal quality **1**, clearing the cache between cases: production becomes **187.5 herd + 187.5 crop**. A 50% crop-only plough bonus corresponds to **150 herd + 225 crop**, the same combined 375. No land cap binds in this example.

### 3. Annual work choice and harvest use different plant/animal mixtures

- **Where:** `origins/sim/farming.py:265–275`, particularly `(VA > VP).astype(float)`, versus `season_food_live`'s `VA / (VP + VA)`.
- **What is wrong:** Choice treats the farm as entirely animals or entirely plants according to which raw value is larger. Production uses a continuous mixture. Calling the same multiplier function with different mixtures does not give the same return.
- **Why it matters:** Effort is chosen using a technology return the band does not receive. Crop/herd-specific bonuses can be overstated or ignored, with a discontinuity around equal raw values.
- **How sure you are:** Certain.
- **How to see it:** In finding 2's equal-value plough case, harvest passes animal share **0.5**, obtaining per-worker multiplier **1.25**. Instrumenting the real `farming.yearly` call shows animal share **0**, because `VA > VP` is false, and multiplier **1.5**. This is independent of the subsequent output-splitting error in finding 2.

### 4. The effect cache misses inherited knowledge and annual domestication changes

- **Where:** `technology.practised_quality:565–579`, its tick/array-length cache; `technology.ensure`/`World.new_band`; farming's skill updates before annual work choice.
- **What is wrong:** Combining/yearly technology changes clear the cache, but other changes determining practised quality do not. Daughters within existing array capacity inherit into rows cached as zero; annual farming can make a remembered technique practicable without refreshing its effect.
- **Why it matters:** Same-season capacity, crossing eligibility or work choice can use obsolete effects. Reloading the same state discards the cache and can answer differently at that point. Food production normally warms the cache before fission and before the annual farming update.
- **How sure you are:** Certain for both reproductions. The replay comparison below concerns a same-tick effect read, not a failure of ordinary between-tick replay.
- **How to see it:** (a) Give a parent tallies/writing quality 1, warm effects, then create a daughter without growing the 64-row arrays and move ten parent members into it. The daughter inherits writing **1**, yet its cached capacity multiplier is **1.0**. Save/load that state: the loaded daughter gets **1.6**, with an equal state digest. (b) On suitable land with wild goats, give a farmer goat skill **2.9999**, farming share 0.8 and remembered milking quality 1. Warm effects, then run `farming.yearly`, which raises goat skill to **3**. Cached milking quality remains **0**; clearing the cache gives **1**. Work choice occurs after that skill update in the same function.

### 5. Founding conquest ignores the village's technology capacity

- **Where:** `conflict._room_for`'s autonomous-village fallback to `P.POLITY_CAPACITY`, versus `polity.capacity(p, w)` and `_new_polity`.
- **What is wrong:** Existing polities use technology-adjusted capacity, but an autonomous village's pre-conquest check still uses bare base capacity. The polity it would found is evaluated differently immediately afterwards.
- **Why it matters:** Tallies/writing can enable an existing polity to hold a conquest but do not provide the corresponding benefit to the same village's founding conquest.
- **How sure you are:** Certain.
- **How to see it:** Give an autonomous farming attacker practised tallies/writing quality **1**. Put a two-settlement target polity at 150 people per settlement, its seat on the attacker's cell and its other settlement on adjacent land. On generated planet 1, the unmodified `_conquest_load` returns **4.5170992**. The prospective institution-free polity has capacity **4.8**, but `_room_for` returns false against **3.0**. `CONQUEST_ROOM=1`, so this is not an institution or safety-margin difference.

## Original fixes: checked and sound

- **Unpractised writing:** the former case now creates no cordage record and recovers no fire-hardening; writing only fades. Recovery requires writing with its post-drift prerequisites satisfied.
- **Herder cache:** the 30/5/30 case leaves the correct **35-person herder and separate 30-person crop group**. Carrying skills removes the recipient's cached herder answers. Finding 4 concerns the separate new effect cache.
- **Marriage:** the controlled residence move now carries cordage **0.2** and emits route `marriage`. Both residence branches have the hook; dependent children are deliberately not additional carriers.
- **Domesticates:** sheep knowledge on sheep-unsuitable planet-1 cell 2 no longer allows wool practice; wool **0.6 → 0.595**. Crops also require local suitability.
- **Prerequisite chains:** remembered kilns without pottery no longer unlock smelting; both levels fade **0.8 → 0.795**. Recursive scalar and catalogue-ordered vector checks matched in **3,240** varied cases at working thresholds 0.5 and 0.7.

## Adults and refinement

The individual and group adult tests both use **15 inclusive to 60 exclusive**. A fixture containing ages 14.75, 15, 59.75 and 60 yielded 15 adults before and after folding.

Specialists are added once explicitly in `share × adults + spec`, with the separate approved teaching gain affecting fidelity/refinement. The base adult share includes specialists too: 15 adults and 3 specialists give **6.75**, whereas sampling only non-specialists then adding specialists gives 6. The implementation matches the literal build-note formula. If unique headcounts rather than weights are intended, that overlap needs a design clarification; it is distinct from finding 1.

With abundant practitioners, no specialists and cordage quality **0.9**, isolated refinement adds **0.0005**, matching `0.005 × sqrt(5/5) × (1−0.9)`. Specialist gain and difficulty remain in the cap. Catch-up, carrier combination, contact learning, recovery and inheritance remain separate approved routes: the cap does not bound their combined gain. No unexplained mastery top-up was found.

## Effects, sources, conservation and replay

- With a fresh cache, practised effects require the full technique chain, suitable domesticates, farming share, materials and terrain. Unknown/merely remembered techniques get zero. Finding 4 is the invalidation gap.
- Hunting/copper tools affect foraging effort; fish traps/canoes additionally require coast, lake or river. Improved effort still depletes wild stock. A controlled harvest of **2,990.496863** matched stock depletion to numerical tolerance, with nonnegative stock and no accounting failure. Return per worker-day uses raw effort as intended.
- Farm gains remain bounded by adjusted per-field capacity. With effectively unlimited effort, the plough-only fixture stopped at **109,500**, exactly `FARM_CAPACITY × SEASON_DAYS`; plough did not enlarge the field. Only irrigation, terracing and milking raise the per-field multiplier. Findings 2–3 concern allocation/choice, not a failed aggregate ledger.
- Storage applies the container/building multiplier to perishables and retains the grain-spoilage term. Land advantage uses plough plus draft-animal quality. Polity capacity uses the seat's tallies/writing; finding 5 is the missed founding-admission path. Techniques awaiting later systems receive no unrelated effects.
- A **16-tick full-engine run** with quality-1 techniques and mixed subsistence passed food/people invariants. Original and save-loaded worlds matched in digest and complete event contents. This ordinary boundary replay passes despite the same-tick cache counterexample.

## Sail reach and draws

The new search enumerates `land → sea → sea → land`, retains old one-sea routes, excludes occupied destinations/immediate land neighbours, and filters land reachable under the existing two-step walking rule. A four-cell line had no destination without sail and reached the far land with sail; its cause named the boats and range.

There remains one attempt draw per eligible band with a nonempty reachable set, not per destination. **The total draw count is not globally unchanged:** that line used zero draws without sail and one with sail. Sail can create a nonempty set where none existed; changed outcomes can also change later eligibility. Draws remain confined to `crossing` and deterministic from state.

## Gate records

An isolated record-generation check, writing under `reviews/scratch/`, correctly distinguished **1 current herder** from **2 living former herders**, counted a migration route, stored loss metadata/connected population and first-invention year, and resolved **3/3** sampled technology events. Sampling uses the gate's independent diagnostic generator.

`tech_held` summarizes positive levels, working levels and median positive quality, including remembered/unpractisable knowledge. It is not a count of effect-eligible techniques: a remembered bow without cordage appears as one positive/working entry. Downstream reports must preserve that distinction. Current-herder counting now uses the actual predicate, not `herder_since`.

## Design question for Ben

Sail's range effect is binary: any positive practised sail quality, with a positive `TECH_EFFECT['sail']`, unlocks the full two-sea-cell range. Quality 0.25 and quality 1 therefore give the same range. Confirm whether this discrete exception is intended under “each effect scales with quality”; I have not imposed a new probability rule as a finding or fix. The specialist-count overlap noted above is likewise an interpretation of the stated formula.

## Validation

**75 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **471.98 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts/controls/output are under uncommitted `reviews/scratch/`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
