# Review 035 — M4a state and per-band arrays

Codex, 21 November 2026. Reviewed through `56c4098`. This is part 2 of the comprehensive pre-gate review.

**Gate recommendation.** Findings 1–4 should block the affected G4a runs. They affect food, replay verification, trade contact and simulated exposure. Findings 5–6 should block conclusions from the affected trade and herding records. Finding 7 is the earlier representation issue, now reproduced directly. It matters especially if G4a compares continuity at polity seats.

## Ranked findings

### 1. An ended group can erase the last living group's seasonal food needs and work

- **Where** — `origins/sim/bands.py:77–81,318–329` and `origins/sim/groups.py:77–97,112–126,165–185`.
- **What is wrong** — Ending an empty grouped band leaves its group row active. The compact living-band index maps the dead band to −1. The food calculation uses that index in an advanced-indexed assignment, so the dead row's zero can overwrite a living group's entry at the last position.
- **Why it matters** — A living group's work and need change because an unrelated group died. The old group row stays active through ordinary compaction and can keep affecting the calculation in subsequent seasons or after a save.
- **How sure you are** — Certain. Reproduced with the normal end-band and food-account functions.
- **How to see it** — Fold the last living band first and a second band after it. Empty and end the second band. `needs_and_work` gives zero need and work for the last live position. Compaction retains the ended group's row. Mark only that group row inactive and the living values return.

### 2. The replay digest ignores state that can change the next simulation step

- **Where** — `origins/persist.py:64–89,332–369`, `origins/sim/technology.py:267–274,650–655` and `origins/sim/places.py:467–517`.
- **What is wrong** — The save includes `still_years`, `forage_rr` and `tech_firsts`, but the digest leaves them out. The event component covers only the length and last event. Place naming now actively reads earlier conquests, including their moved-band lists.
- **Why it matters** — A replay can pass the digest while its technology options, first-invention evidence or next place-name decision differ. The gap is in detection. The ordinary save round-trip preserved those values in the inspected path.
- **How sure you are** — Certain. Reproduced unchanged digests for these mutations.
- **How to see it** — Move a stationary forager's `still_years` across the settlement threshold. `_settled` changes and the digest stays identical. Changing an earlier conquest's affected bands also leaves the digest unchanged if another event follows it. The places pass reads that earlier event.

### 3. An empty trade attempt can become a saved contact

- **Where** — `origins/sim/traders.py:274–286,340–347,384–396`, `origins/sim/technology.py:719–731,941–953` and `origins/sim/disease.py:293–314`.
- **What is wrong** — The trader pass appends a link before it knows that any goods will move. `_carry` returns immediately when there is no cargo. The link is retained as contact for subsequent phases and across a save.
- **Why it matters** — A candidate route with no recorded exchange can still teach, make an inventor eligible for stimulus or serve as simulated contact under the named-disease rules. That changes what the trade and exposure results mean.
- **How sure you are** — Certain. Reproduced with two seats and valid roads.
- **How to see it** — Give a polity enough specialists for traders and place a second reachable seat. Give neither seat any goods. The trade pass writes a link despite producing no route row or route-opening event. Loading the save preserves the link.

### 4. Captives and spouses move without their recorded exposure state

- **Where** — `origins/sim/bands.py:236–243`, `origins/sim/conflict.py:163–188,324–331`, `origins/sim/demography.py:181–203` and `origins/sim/disease.py:123–140`.
- **What is wrong** — Fission, group migration and whole joins account for immunity. The capture and marriage paths move people and call only the technology transfer. Their recipient's immunity and last exposure remain unchanged. Marriage also passes one technology carrier even when children move with that person.
- **Why it matters** — The recipient's susceptibility and exposure class depend on the route through which the same people joined it. That distorts the simulated first-contact comparison.
- **How sure you are** — Certain. Reproduced capture through the fight path and traced the marriage branch.
- **How to see it** — Move 30 previously exposed people by capture into a naive band of 30. It reaches 60 people while its recorded immunity stays at zero and its last exposure remains −1. The ordinary join arithmetic would assign half immunity when the newcomers were fully immune.

### 5. A merger can manufacture a history of practising on imported materials

- **Where** — `origins/sim/technology.py:466–514,1016–1021`.
- **What is wrong** — The join independently ORs prior practice, goods-held material and wood flags, then treats them as one band's prior state when attributing a cut-off. Each part can come from a different band.
- **Why it matters** — Losing local access after a move can be recorded as a loss of imports, inflating the dependence evidence.
- **How sure you are** — Certain. Reproduced with the real combine and cut-off functions and local materials held absent in the fixture.
- **How to see it** — Join a band that practised copper working with local copper to a band that had traded copper but never practised it. With neither local nor held copper now available, the combined flags trigger `technique_cut_off` naming imported copper, although neither band practised that way previously.

### 6. A whole consolidation leaves recent trade and herding history on the absorbed row

- **Where** — `origins/sim/bands.py:236–282`, `origins/sim/trade.py:799–817`, `origins/sim/pastoral.py:104–111` and `gates/g3.py:93–97`.
- **What is wrong** — Consolidation moves people and goods, but neither last year's receipts (`trade_in`) nor prior herding (`herder_since`) move to the continuing row. A consolidation is described as a change of representation.
- **Why it matters** — The same local population can lose last year's trade pressure for invention, and the “ever herded” count can fall because the recorded row was absorbed. A later pastoral move can appear to be the first.
- **How sure you are** — Certain. Reproduced through `consolidate_groups`.
- **How to see it** — Co-locate two groups with the same consolidation key. Store last year's receipts and a historical herding date on the second group only. After consolidation, the surviving group's trade need is zero and its prior-herder marker remains −1.

### 7. Unfolding can discard a pregnancy even when the group respects capacity

- **Where** — `origins/sim/groups.py:409–417,490–523`.
- **What is wrong** — The group can have a valid pending pregnancy for a woman of childbearing age. Unfolding recreates partners, then assigns pregnancies only to partnered women under 45 and clears all group slots.
- **Why it matters** — Changing the same population to individual detail can erase a pending birth. This is the limitation noted in reviews 029–031.
- **How sure you are** — Certain. Reproduced with a single woman and one pending pregnancy.
- **How to see it** — Unfold a group of one 25-year-old woman with one pending pregnancy. The woman is recreated and the due date is lost. The group was within the cap before unfolding.

## State lifecycle audit

| State | Growth, transfer and clearing | Save and digest |
|---|---|---|
| `tech`, `tech_record`, `tech_scribes` | Growth preserves rows. Daughters inherit levels and records, with scribal writing and scribes excluded as decided. Whole joins add and clear scribes, while partial joins exclude writing. Dead rows remain indexed by their original IDs and the practice paths select living bands. | Arrays round-trip and enter the digest. Older saves seed scribes from qualifying seats. `tech_firsts` is saved and omitted from the digest. |
| `tech_prev_prac`, `tech_prev_mats`, `tech_prev_wood`, `tech_writing_log` | Prior state grows lazily, copies into daughters and combines on whole joins and group migration. Finding 5 covers the resulting attribution problem. The writing log is append-only. The current import-history mechanism uses the three prior-state arrays, with no separate live `tech_import` array. | Saved and hashed. Older saves derive the wood flag from prior practice where necessary. |
| `goods`, `goods_reached`, `partner_of`, `partner_since`, `partner_gave` | Daughters start blank, then fission transfers a share of stock. Whole joins move the source stock. Raids move loot separately from captives, as decided. Annual pre-exchange marking picks up goods already held. End and consolidation clear both partnership directions, recording running gifts first. Dead goods flags remain historical. | Saved and hashed. Older saves widen partner slots and infer reached goods from holdings. |
| `treasury`, `trade_links`, route and gift state | Treasury grows by polity ID. Conquest transfers it and dissolution releases it to a living seat or records loss. Links are rebuilt annually, with the zero-cargo case in finding 3. Prior receipt state grows lazily and resets annually. | Treasury, links, receipts and behaviour-controlling trade sets survive save and digest. Sampled route, gift and exchange logs and their strides are saved. The digest covers some other observation logs, such as writing, while omitting these. It cannot serve as a complete equality test for gate records. |
| `land_*`, game, forest, fertility, salt, fallow | Cell quantities stay on their cells and annual accumulators reset. Per-band crop loss grows lazily, moves with its stock share, and clears on ordinary end. Whole consolidation moves the quantity out of the source. The retained zero-quantity source exemplar cannot enter a live band by ID reuse. | Shared array list drives save and digest. Older saves initialize missing histories and land quantities to defaults. |
| `dz_imm`, `dz_last`, `dz_active`, `dz_since`, `dz_log` | Band arrays grow and daughters inherit. Whole joins and group migration weight immunity by movers and preserve the latest recorded exposure. Capture and marriage are the exceptions in finding 4. Cell histories stay at the cell and spell restarts were already verified in review 034. Dead band rows remain historical. | All four arrays and the named catalogue and log survive save and digest. Older schemas upgrade the log and use date-unknown exposure where possible. Review 034 finding 10 still applies to modern mixed-mechanism reloads. |
| Group pregnancies | Growth and population-row compaction carry due slots. Whole joins add and clear them. Ordinary, hazard, conflict and named-disease mortality paths use the pregnancy cleanup. Bounded split and transfer draws preserve capacity for valid inputs. Findings 1 and 7 cover retirement and unfolding. | Group arrays, including slots and active flags, are saved and hashed. The invalid active flag in finding 1 is therefore preserved too. |
| `w.places` and layers | Append-only by feature, with language lineage rather than band ID as the holder. Names persist after settlement abandonment. Conquest reads recent events. Indexes rebuild from records and do not belong in the digest. | Layers and event IDs are saved. Older unnamed worlds start empty. Older layers lacking event IDs remain displayable. The digest coverage gap for earlier conquest inputs is in finding 2. |
| Other M4a-linked band and polity state | Farm skill and former herding marker copy on a split. Realized farm returns start fresh on a daughter and are checked against their origin cell. Living membership and seat succession are repaired at the annual polity pass. Band IDs increase monotonically even after compaction. | Farm-return fields, historical herding, polity membership, seat memory, conquest timestamp and polity objects survive save and digest. First-herder metadata is saved separately. |

## Validation

- 25 focused tests passed, with 166 deselected. Short fixtures crossed band ID 64, grew the land and treasury arrays, and replayed a modern save through 12 seasons with identical events and digest.
- The exact replay check is valid for that fixture. The negative tests in finding 2 show why digest equality alone is insufficient for the broader claim.
- Only review files were changed. No gate-length run was started.
