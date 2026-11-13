# Review 005: M4a circumscription, pastoralism, seat memory and disk events

**Reviewer:** Codex, 13 November 2026.

**Reviewed:** `main` at `e566ca2`, including the two merges and steps 1–2 named in the request. Read against the design, M3 decisions and gate closure, and M4 specification section 2 and decisions 4–5. No implementation files changed; no gate-length runs started.

Four reproduced findings follow. These are implementation/integration problems; the standing-crop question below is a separate design question. Rates and capacities are tunable starting values, not measurements.

## 1. Moving herders can disappear into crop farmers, losing their knowledge and political identity

- **Where:** `origins/sim/pastoral.py:67–74`; `origins/engine.py`, pastoral followed by fission/merge; `origins/sim/bands.py:206–229` (`consolidate_groups`); `origins/sim/groups.py:405–423` (`merge_into`).
- **What is wrong:** Pastoral movement permits a herding group to enter a crop-farming group's cell, after which consolidation treats both as the same population because both have `farm_share >= 0.5`. The earlier band survives with its own farming skills, language, customs and polity; the other band's people and stores are absorbed, but its skills, herder marker and political identity are not carried over, and no social transition is logged.
- **Why it matters:** This makes a seasonal pasture move silently eliminate a pastoral people, erase domestication knowledge and transfer its people between polities. Which way of life survives depends on band order. Population and food totals can remain correct, so accounting checks miss it. The consolidation helper predates this step; the new movement directly exposes herders to it every season.
- **How sure you are:** Certain for the reproduced case; frequency in full histories is unmeasured.
- **How to see it:** Start two 30-person bands, fold both with `groups.fold`, and put each in a separate polity using `_new_polity`. Give the earlier band crop skill 3, no animal skill, `farm_share=1`, and the destination cell. Give the later band animal skill 3, `farm_share=1`, animal value 0.1 at home and 1 at that destination; give the destination crop value 1. Run `pastoral.move`, then `bands.consolidate_groups`. Observed: the herder moves, records `herder_since=400`, then ends; the crop band has 60 people in its original polity, animal skill **0**, and `herder_since=-1`. The 90-person world total is unchanged. These are the same movement and consolidation calls used by the seasonal phase order.

## 2. Pasture crowding excludes people who still use farmland

- **Where:** `origins/sim/pastoral.py:39–41,53–64`, compared with `origins/sim/farming.py:320–349` (`season_food_live`).
- **What is wrong:** The pasture calculation counts a band's people only when its farming share is at least 0.5. Seasonal production shares the cell's capacity among **all** bands with positive farming effort, including those just below that threshold. Thus an occupied destination can look empty, and the claimed improvement can reverse in the actual production calculation.
- **Why it matters:** Herding bands can move towards competition that lowers their food production, while their recorded cause says the pasture is better. Moving first also means the new crowding affects that season's food immediately.
- **How sure you are:** Certain for the reproduced reversal. Its prevalence is unmeasured; this is a constructed crowded-cell case.
- **How to see it:** Use a 30-person herding band with animal skill 3, farming share 1, animal suitability 0.5 at home and 1 in its only usable neighbouring cell. Put 3,000 people farming share **0.49** with the same animal skill in that neighbour. Hold both populations and effort fixed (`effort = population * SEASON_DAYS * FORAGE_RATE`), and compare `season_food_live` at the original locations with the same call after `pastoral.move`. The move reports **2.0 times** the grazing per person, but the herder's seasonal farm food falls from **4,106.25 to 2,190.0**. No parameters were retuned. A group count was used to construct the crowding; the production calculation operates on the same totals for multiple bands.

## 3. A living former seat loses its memory protection when its polity ends

- **Where:** `origins/sim/bands.py:243–248` (`fold_distant`); `origins/sim/polity.py`, `_end_polity` and the update of `notable_until` in `yearly`.
- **What is wrong:** The new protection requires `p.alive` even while `w.t < p.notable_until`. Dissolution or absorption ends the polity without necessarily ending its seat's population, immediately making that former seat eligible to fold.
- **Why it matters:** The approved brake is intended to preserve individuals and family lines for a while after a polity drops below chiefdom. Losing the polity entirely bypasses that protection, cutting those lines before the 100-year memory expires.
- **How sure you are:** Certain.
- **How to see it:** In a fresh world at tick 400, create a polity at a living individual band, set its tier to 0 and `notable_until=800`, and call `fold_distant` with `INDIVIDUAL_THRESHOLD=1` to force eligibility to matter. With the polity alive the seat stays individual. Repeat after `_end_polity` (the band still alive): the seat folds immediately, with **100 years** of protection left. The threshold override only forces folding pressure; the faulty eligibility condition is independent of world size.

## 4. Flight's held-land snapshot blocks land vacated earlier in the same call

- **Where:** `origins/sim/polity.py:646–651,670–684,687–698` (`_flight`).
- **What is wrong:** `held` is built once, then retained after villages move and relinquish membership. The population counts are updated, but a cell vacated by its last polity member remains marked as held for later villages.
- **Why it matters:** A later village can be counted as hemmed in when suitable, empty land is now available. This overstates blocked flight and weakens the circumscription brake in an order-dependent way. It is a conservative stale-state error, rather than the self-annexation/loop error from G3.
- **How sure you are:** Certain.
- **How to see it:** On planet 1, place two member villages in cells **2** and **21890**, with their seat elsewhere. Give the earlier village domesticated animal skill and animal values 0.5 at cell 2 and 1 at cell **5506**. Give the later village domesticated plant skill and plant values 0.5 at 21890 and 1 at cell 2; other values are zero. With successful attempt draws, the earlier village leaves cell 2 for 5506; the later village is blocked, although nobody now occupies cell 2. Call `_flight` again with the remaining membership and no other changes: the later village moves to cell 2. The reproduction uses the generated grid and actual `ring2`, not substituted neighbourhoods.

## Checked and sound

- **Flight destinations and chains:** home and cells held at entry are excluded. Direct dependants are rewired to the seat; the membership list is shortened before load/tier/secession processing. Two successive departures from a seat → member → child chain left correct autonomous links and a seat-only membership list, with unchanged stores and resolvable event causes. No loop found in that check. The held-land snapshot issue is finding 4.
- **Pastoral arithmetic and order:** within the population it counts, home already includes the moving band and the destination adds it once. Counts are updated after each move. The generated neighbour arrays are sorted by cell number, so strict `>` gives the stated lower-cell tie break. All random-generator states were unchanged by a pastoral move.
- **Stores, farming and location:** a move preserves `b.store` and `crop_store`; food production reads the new cell. Farming's yearly trail check resets `still_years` after a pastoral move. Polity membership stays attached to band IDs and annual load reads current locations; consolidation is the separate problem in finding 1.
- **Herder replay:** a world with an actual `took_up_herding` event, herder marker and seat-memory record round-tripped with equal digests, equal markers/first-event pointer and equal event contents; the original and loaded worlds also matched after 12 further seasonal ticks.
- **Disk events:** forced freezing (`HOT=2`, `BATCH=4`) preserved event order/content, interleaved indexed reads during iteration, retained outbreak mutation, streamed save/load and continued replay. The full-suite event-store test additionally compares histories with early freezing against histories without freezing.
- **Older saves:** removing both herder fields from the save gave `first_herders=None` and all `herder_since=-1`, as intended.
- **Cause chains:** the constructed flight and herding events resolve through `explain`. Hunger/overload text in flight describes the predicates actually used. The misleading pasture gain under omitted competition is covered by finding 2.
- **Python 3.10:** all `origins/` source parses with the 3.10 grammar; no incompatible API found in the reviewed changes. Actual execution here uses Python 3.12.14, not a Python 3.10 interpreter.

## Validation

**49 tests passed**, with one warning, in 333.53 seconds using `python -m pytest -q -p no:cacheprovider tests`. The warning is an installed AnyIO pytest plugin's deprecated `CallSpec2` import. Focused checks ran with Python 3.12.14 and NumPy 2.3.5; temporary scripts, dependencies and outputs are under uncommitted `reviews/scratch/`.

## Design questions for Ben

- **Standing crops during seasonal migration:** `crop_store` explicitly represents standing fields, but it follows the band's ID through every pasture move and is harvested at its eventual location. This predates pastoralism in the handling of fission, and is numerically conserved. With repeated seasonal movement now introduced, should the plant fraction require returning to the fields, be abandoned, or remain an explicitly accepted abstraction? I have not counted a choice between these rules as an implementation finding.

The build notes already acknowledge that `herders_alive` counts former herders; this review does not present that known measurement issue as a new finding.
