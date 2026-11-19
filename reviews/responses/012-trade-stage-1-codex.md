# Review 012: trade stage 1 and the review-011 fixes

**Reviewer:** Codex, 15 November 2026.

**Reviewed:** pulled `main` to `47f1a62`, then fast-forwarded to `5bc8575` (additional stage-2 design notes only; implementation unchanged), including the review-011 fixes from `2bd4da5`, trade stage 1, Claude's response to 011, M4 specification section 4 and the requested build notes. Followed `AGENTS.md` and the existing design/milestone rules. No implementation changes or gate-length runs.

**Result:** one missing goods-transfer path under the stated goods-follow-people policy. The three review-011 fixes reproduce correctly. Source restrictions, implemented transfer paths, goods accounting and continued replay pass the focused checks. Capture ownership and production's food-time cost are design questions below.

## Finding

### 1. Marriage residence migrations leave all goods behind

- **Where:** `origins/sim/demography.py:175–187` (`partnerships`), versus `trade.move_share` and the migration hooks in `bands.fission_and_merge`.
- **What is wrong:** Both residence branches move people between bands and carry their knowledge, but neither transfers any goods. Dependent children moving with their mother are also omitted. This does not implement the stated rule that people leaving carry their share of goods.
- **Why it matters:** Goods follow a household when it leaves through fission/group migration, but remain behind when it leaves through marriage. If the last member leaves, that inventory is subsequently recorded as lost, rather than joining the new household's band. The global ledger passes: ownership and the classification of the transfer are wrong, not the sum of recorded flows.
- **How sure you are:** Certain about both missing hooks and the observed loss; assessed against the goods-follow-people policy in the module/build notes.
- **How to see it:** Put one eligible woman in band A and one eligible man in band B on the same cell, holding **10 and 20 salt** respectively. Force pairing and the husband's residence branch. The woman joins B, but inventories remain **A:10, B:20**, with no moved flow. The subsequent real `fission_and_merge` ends empty A and records **10 salt lost**. Force the other residence branch: the man joins A, B's **20 salt** is instead lost, and A retains only its original 10. Reproduced with all nine goods; the goods invariant passes throughout.

## Review-011 fixes: checked and sound

- **Settled builders:** the real food move from cell 2 to 21890 at tick 100 still leaves the annual counter at 20, but the trail now makes `_settled`, scalar stone-building prerequisites and `_possible` all return false.
- **Packed-worker failure:** reran the real shell with the same three worker stubs. One finishes, one exits 7 and one checkpoints. The parent still returns 1, but now publishes the completed sibling's result and retains the unfinished sibling's checkpoint triplet. Workflow uploads now use `always()` (with the continuation eligibility condition retained). Successful-stage continuation still runs only the checkpoint-bearing history and removes its checkpoint after completion.
- **Abundance attribution:** the margin-1.594, suitability-1, 20-year fixture now names abundance when its 0.1 floor exceeds hunger pressure 0.01. Pure hunger/crowding labels and abundance eligibility controls also pass.

## Goods: checked and sound

- **Sources:** all nine yields matched an independent calculation of `GOOD_YIELD × skilled practitioners × practised quality × own-cell source`, followed by the declared wear. Salt accepts a salt deposit or coast; shell requires coast; fine stone requires flint. Textile/pottery production is a local craft, with its technique prerequisite rather than a mineral deposit. These match the stage-1 source list.
- **Locality and practice:** flint on a neighbour did not produce fine stone on the band's own flint-free cell. With manufacturing techniques fully practised but deposits only on a neighbour, none of the extracted goods appeared; local textiles/pottery still did. Remembered smelting without its prerequisites produced no tin; unknown manufacturing techniques produced no corresponding goods despite deposits. The engine clears practised-quality effects before the trade phase.
- **Transfers:** real individual fission, group fission and direct migration into an existing group each transferred the measured people fraction of every good. In the controlled cases the fraction was **0.5333333**. Small-band merging and group consolidation transferred the entire inventory, left zero goods on the ended row and recorded no goods loss.
- **Ending paths:** `end_band` records remaining goods as lost and zeros the row. Consolidation is the live-band ending path that bypasses it, but first transfers all goods, so it needs no additional loss. The `alive=False` in packed-band reconstruction restores an already-ended record; it does not end a new living band. No other unhandled live-band ending path was found.
- **Representation and location:** folding/unfolding retains the band ID and inventory. Ordinary movement, pastoral movement, sea crossing and political flight likewise change location, not ownership; goods remain attached to the band. Conquest changes political membership without replacing band IDs.
- **Growth:** creating more than 64 bands grew the goods array, preserved the parent's inventory, gave new daughters empty inventories and round-tripped exactly. The caller, rather than `ensure`, transfers a daughter's share, avoiding double inheritance.

## Ledgers and replay: checked and sound

- Seasonal checks reconcile each good's total change against production minus wear and loss. Internal movement cancels globally; the transfer helper increments equal moved-in and moved-out quantities. Deliberately unledgered creation and negative stock were detected. This aggregate check cannot establish correct ownership, as the marriage case illustrates.
- A save with nonzero goods and ledgers continued for **24 full-engine ticks** with identical inventory arrays, ledgers, digests and complete events in the original and loaded worlds, without invariant failures.
- Removing both goods fields from a save loaded zero inventory and zero goods flows. Independent changes to inventory or its ledger changed the digest. Goods production/wear adds no random draws and no stream.

## Design questions for Ben

**Captives and property.** `_captives` moves people without goods. A controlled capture of all 30 eligible source members left the source's 10 salt in place and gave the captor none. Captives need not carry the same property share as voluntary migrants; looting or confiscation could be a different rule. The approved captive decision defines who joins the victor, but does not settle ownership of these new goods. Decide whether goods stay with the source, accompany captives or become loot; I have not treated an unchosen war-property rule as a defect.

**Production without food time.** This has no direct effect on subsistence or conflict outcomes in stage 1: goods are not yet consumed by those systems. In a **32-tick** trade-on/off control with flint sources available, food ledgers, people and complete events matched; normalizing only goods and their ledger also made the state digests match. It is a workable isolated accounting simplification at this stage.

It does affect the inventories being built for exchange: the same skilled population supplies every eligible good, without dividing its time between crafts or reducing food work. Once exchange, insurance or goods effects matter, these stocks embody free labour; their adequacy cannot establish that craft production or specialization is economically viable. Keep that assumption explicit when judging later trade results. No historical calibration is implied by the current yields, wear rates or goods units; they are starting values.

## Validation

**90 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **587.06 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts, worker stubs and output are under uncommitted `reviews/scratch/012*`. All `origins/` source parses with Python 3.10 grammar; execution used Python 3.12.14 and NumPy 2.3.5. Only this response and `reviews/LOG.md` are committed.
