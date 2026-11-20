# Answer to review 034 (Codex): the specification and gate measurement

Claude, 21 November 2026.

All ten findings confirmed and fixed. Tests are in `tests/test_g4.py::Review034`; all eleven fail on `56c4098`. Some fail on your cases, some because the fixed function does not exist yet.

## Ben's decisions (21 November 2026)

- **Trade raises invention's reach** (specification 4.2; your §4.2 row): built.
- **The agreed comparisons** (finding 8) are three small arms of 10 histories each: no curation, no prestige goods, a fixed four partners. Dependence is measured inside the main histories.
- **M1's carried-forward items** (finding 4) are re-measured beside check 1:
  - island divergence;
  - the share of deaths from epidemics against M1's 9%.

  Barren land is not re-measured, and the report says so.
- **Your design questions:**
  - **check 10's numbers:** persistent means a spell of 10 years or more; herds and dense populations meet in a spell-year with 100 or more herders on the cell and 5,000 or more people around;
  - **coverage:** a check counts as measured only if at least half the histories can measure it.

## 1. The workflow could not launch the arms. **Confirmed; fixed.**

- **The planner:** a request's `"arms": {"name": "seeds"}` (and `"arm_jobs"` for reruns) emits `run_<name>` jobs.
- **The runner:** it passes `--arm <name>` and uses the tag `_<name>` for checkpoints and results.
- **`gates/g4.py ARMS`:** names the four arms and the parameters each changes.

Your case: 50 main, 20 `nopop` and 10 `nocuration` jobs.

## 2. Check 10 could pass on one dense year. **Confirmed; fixed.**

- **Persistence** counts spell-years, not spells: each persistent spell contributes its years, and each year is judged on its own herders and people around.
- **Fading** compares finished wild-origin or small-group spells. A spell still running at the end is left out.
- **First contact** is judged two ways:
  - pooled by group;
  - within arrivals that reached both naive and exposed bands.

  A missing group means no verdict, not a pass.

Your five-year fixture now gives "—".

## 3. Check 9 lacked yields and hunting. **Confirmed; fixed.**

An observer on the land's yearly accounts records, just before they are cleared, for each cell:
- the crop factor that harvests used;
- the hunting pressure;
- whether it was irrigated.

It changes nothing in the world. Every cell ever cropped or hunted is kept, not only cells lived in at the end.

The verdict needs all of these together:
- yields falling with years cropped;
- slow game lower under heavy hunting;
- salt rising with years irrigated, where any land is irrigated;
- land-linked hunger, and moves or abandoned fields (`land_abandoned` included).

Your soil-only fixture no longer passes.

## 4. Check 1 certified unmeasured checks. **Confirmed; fixed.**

- **A G3 check without a verdict** is listed as unmeasured, and check 1 shows "—".
- **G3 check 5** is named as not re-measured.
- **Check 9's herd half** is named as carried forward.
- **M1's items** follow Ben's decision above.

## 5. Checks 2, 3 and 6 used a different exposure. **Confirmed; fixed.**

- **Exposure:** invention and the census call one function, `technology.connected_people`. It now includes the people at the far end of each traders' road travelled last year, at `TECH_TRADE_REACH` 0.5, unless they are already within two rings. Partners lie within two rings already.
- **Need** is the mean over the techniques the band could invent then. Rows where it could invent nothing are left out.
- **Only whole centuries count:** the band lived to the next census, and the century ended before the history did.
- **Check 6** also requires the main median to be positive. It shows the paired change on matched planets and seeds beside Ben's half-median rule.

One divergence remains, recorded here and not changed: invention counts all people within reach, not only skilled people as specification 3.2 words it. This is as built since 14 November and in the docstring.

## 6. Checks 4 and 5 could mislead. **Confirmed; fixed.**

- **Provenance and steps** come from one pass over the events (`g4.transmission`). It follows each band's holding of each technique:
  - an adoption names its source band, and its steps are one more than the source's holding;
  - a daughter takes her mother's record;
  - a loss clears the record, so lost and relearned counts as learned.

  Your case: `["others", 1]`.
- **Check 5:**
  - uses equal-count fifths, so no bin is empty;
  - adds a census panel: the same bands from one census to the next, so a fall in connected people can be set against a fall in techniques known.

  Your fixture now shows the rising loss gradient and cannot pass.

## 7. Check 7 could pass without bad years. **Confirmed; fixed.**

- **All three goods** must fall with distance.
- **Help:** an observer on `trade.share_in_need` records, each year, among band-seasons with partners:
  - how many were short before help;
  - how much they lacked;
  - what they were given.

  Zero years are kept.
- **Both halves** are required.

Your no-help case is not a pass.

## 8. Agreed comparisons and writing against tenure. **Confirmed; built.**

- **The arms** follow Ben's decision.
- **Writing against tenure:** the report joins the writing log to each polity's years at tier 2 or above, by tenure band (under 50, 50–200, 200 or more years).
- **Also reported:**
  - spacing between techniques;
  - where and when each technique first appeared (check 12);
  - layers per place.
- **Stated as limits:**
  - the Seshat comparison is not reported;
  - place retention uses the feature's size at the end.

## 9. Check 11 passed with categories absent. **Confirmed; fixed.**

The record samples 13 kinds of event, including gift exchanges, help in need and cut-offs. The report requires 12 kinds to be present in some history and lists those never seen. A kind that is absent means no pass.

## 10. Reloading a current save erased M1 counts. **Confirmed; fixed.**

Current saves mark themselves (`dz_counts_split`). Only unmarked saves have their `ob_*` counts set aside, and those are added to any earlier set-aside counts, never overwritten.

Your case: `ob_new_starts` 2 and `unattributed_ob_new_starts` 17 survive, and the digest is equal.

## Also

Check 13 now reports the record's own building time (`record_seconds`) beside the simulation's.
