# Review 013: gift partnerships, marriage goods and raid loot

**Reviewer:** Codex, 15 November 2026.

**Reviewed:** pulled `main` to `173d7ad`, including `dc128f3` through trade stage 2, Claude's response to 012, the partnership design/as-built notes and M4 specification section 4, under `AGENTS.md` and the existing project rules. No implementation changes or gate-length runs.

**Result:** marriage goods and raid loot pass behavioural reproductions. Four findings follow: a legacy-save inventory loss, seasonal help outside the stated reach, missing gift records and orphan links after consolidation. Current-format replay and food/goods conservation pass the focused checks; these do not establish correct ownership, reach or provenance.

## Findings

### 1. Loading a large stage-1 save can erase the final goods row

- **Where:** `origins/persist.py:190–204`, particularly the legacy partnership-array growth call at line 202; `trade.ensure`'s unconditional `w.goods[band_id] = 0`.
- **What is wrong:** A save with goods but no partnership arrays first restores its inventory, then calls the new-band initializer to grow partnership storage beyond 64 rows. That initializer also clears the final restored goods row.
- **Why it matters:** Existing goods disappear during an ordinary supported save migration, without a loss entry. The subsequent seasonal check starts from the already-damaged state, so it cannot detect this load-time loss.
- **How sure you are:** Certain. The loss requires nonzero inventory in the last allocated row; it does not affect every large save.
- **How to see it:** Create 128 populated bands, with a `(128, 9)` goods array and band 127 holding **[10,20,30,40,50,60,70,80,90]**. Save, remove `partner_of`, `partner_since` and the new trade RNG state to represent stage 1, then load. Band 127's inventory becomes **nine zeros**, losing 450 units; `goods_ledger` remains unchanged. A 64-row legacy control retains its goods and loads no links.

### 2. A living partner can provide food after moving out of reach

- **Where:** `trade.share_in_need:264–283`; annual range cleanup in `partnerships_yearly:209–218`; movement precedes eating in `engine.PHASES`.
- **What is wrong:** Seasonal help checks that a partner appears in the living-band index, but not that the partner is still within reach. A move can therefore take a linked giver beyond two rings before its next meal, while help remains enabled until annual cleanup.
- **Why it matters:** The stated two-ring limit does not bound the food insurance network between annual passes. Bands can receive immediate food from partners they can no longer reach, changing hunger and survival after movement.
- **How sure you are:** Certain about the transfers; likely a violation of the stated reach limit. An intentional annual grace period would need to be an explicit interpretation of that limit.
- **How to see it:** On planet 1, link a recipient at **12954** with a giver at **829**, within two rings. Give the giver 100,000 stored food, put ordinary stock 1 at 829 and 1,000,000 at adjacent cell **13004**, and zero the other wild pools. The real `foraging.move` takes the giver to 13004, outside the recipient's two-ring reach. The subsequent real `forage_and_eat` still records **2,523.062** food received from that giver. Food balance passes. A yearly partnership pass removes the same link. This differs from an ended partner: the living-index guard correctly prevents an ended band from giving food.

### 3. Actual gifts have no partner/quantity record

- **Where:** `trade.partnerships_yearly:219–227` and `move_good:183–191`; M4 specification section 4.2, “Each trade is recorded with its partners, goods and quantities.”
- **What is wrong:** Yearly shell/gold transfers update inventories and global moved totals, but create no exchange record naming the giver, recipient, good and amount. Formation/lapse events cannot identify subsequent gifts.
- **Why it matters:** The ledger proves global conservation but cannot explain how a particular band acquired its goods or reconstruct exchange along a chain. Checking that existing event cause chains resolve does not test these unrecorded transfers.
- **How sure you are:** Certain.
- **How to see it:** Give one linked band 100 shell and its partner zero; disable new formation and run `partnerships_yearly`. Inventories become **95 and 5**, and moved-in/out each increase by **5**, with **zero events added**. The identities and quantity of that exchange are absent from the recorded history.

### 4. Links between two consolidated-away bands are never cleaned up

- **Where:** `bands.consolidate_groups`' direct band ending, versus `trade.band_ended`/`_unlink_all`; `partnerships_yearly:210–213` iterates only living endpoints.
- **What is wrong:** Consolidation bypasses partnership unlinking. If both endpoints consolidate away before the next yearly pass, neither endpoint is visited by cleanup, so their link persists indefinitely rather than being dropped at that pass.
- **Why it matters:** Saved partnership state can permanently point between ended bands. This is a stale-state issue, not food being created or aid coming from the dead: help and teacher selection exclude those endpoints, and yearly gifts visit only living bands.
- **How sure you are:** Certain.
- **How to see it:** Fold three compatible bands A/B/C onto one cell and link B with C. Consolidate: B and C both end into A. Run yearly partnerships with formation disabled. `partners(B)` still returns C, and `partners(C)` still returns B, with their original timestamps. A single ended endpoint with a living partner is cleaned at the next pass; ordinary small-band merging calls `end_band` and unlinks immediately.

## Review-012 fix and loot decision: checked and sound

- Both forced marriage residence directions now move the departing person's inventory. In the previous 10/20-salt fixture, the destination ends with **30**, the emptied source with **0**, and ending it records no goods loss.
- A mother and child leaving a three-person source transfer **two thirds** of every good; the remaining person retains one third.
- Called the real `_fight` with forced winning/losing draws and zero casualties to isolate loot. A winning raid takes **30%** (`RAID_TAKE`) of all nine goods and the food store; a losing raid takes none. The winning control also takes a captive without moving an additional goods share. Goods totals and moved ledgers balance. This is a behavioural reproduction, not a source-text assertion.
- Ben's decision to defer craft food-time costs until stage 5 is now explicit; no further decision is requested here.

## Partnerships, sharing and teaching: checked and sound

- Formation maintains symmetric endpoints/timestamps, at most four partners, and no self-links or duplicates in the production path. Repeated formation with the same saved state gives identical links. Only the appended `trade` RNG advances; all previous stream states remain unchanged. Candidate sorting, capacity updates and vector draw counts depend on state and preceding draws, not wall time.
- Gifts conserve each good, with each direction's amount computed before either direction moves. Repeated links diffuse goods through the current yearly ordering; finding 3 concerns the missing history, not conservation.
- Sharing's giver budget is **20% of initial spare**, shared across all recipients, rather than 20% afresh for each request. In a control with 100 food and a 40-food reserve, total help was **12**, leaving the giver **88**; the second recipient could not draw another 12.
- For valid farming shares, `keep_need >= need_now`. An initially short band therefore has no giving budget, and a giver cannot donate below its reserve. Received food does not replenish that budget: no band is both a recipient and a giver or relays the same food in that season.
- The real eating path passes full farmers' reserve multipliers **2, 1, 4, 3** in quarters 0–3, including the current meal until the next harvest; a half-farming band's multipliers are **1.5, 1, 2.5, 2**. These are the existing food-security horizon's gross need estimates, not forecasts of future spoilage or demographic changes.
- Actual help raised the recipient's margin **0.8 → 1.3** and total food eaten **2,495.6875 → 5,018.75** in a controlled meal, while the recorded foraging returns and harvested food were unchanged. Eating/storage applied to the food remaining after transfers, and the full food balance passed.
- With two equally knowledgeable teachers, zero shared roots and a lesson draw of 0.9, the selected partner taught successfully at closeness **1**. Selecting the nonpartner failed, despite another available teacher being a partner. Disabling trade also removed the boost. The rule is conditional on the actual selected teacher.

## Saves, replay and limits

A current-format world with active links and nonzero goods continued for **24 full-engine ticks** identically before/after save-load: equal digests and complete events, with no food/goods invariant failures. Partnership formation/lapse/help event references resolve. This does not cover the old-format loss in finding 1 or the absent gift events in finding 3.

Old saves load with no links and retain their earlier RNG streams. The small-save goods control passes; larger saves have finding 1's specific failure. New band-array growth preserves existing links and starts new rows without partners.

The sampled trial in the build notes does not establish the behavioural insurance gate (“far less” loss in a bad year), source-distance fall-off, or rates across histories. I did not reproduce its private planet-3 snapshot or start a gate-length run. Rates and amounts here use tunable starting values, not historical calibration.

## Design questions for Ben

**Partner teaching and trade attribution.** The successful controlled partner lesson is still recorded as `route="contact"`; its cause names 0% shared words and the source, but not the partnership responsible for closeness 1. M4 distinguishes trade from ordinary contact diffusion. Make explicit how G4a will identify this partnership contribution: existing route counts alone will classify it as contact. This does not change the finding that the numerical teaching boost is correctly conditional on the selected partner.

## Validation

**95 tests passed** in **654.29 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Two warnings: the installed AnyIO pytest-plugin deprecation, and divide-by-zero in `foraging.move` during the partnership round-trip fixture. Focused scripts, outputs and controlled fixtures are under uncommitted `reviews/scratch/013*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
