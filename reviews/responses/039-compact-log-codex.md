# Review 039 — the compact log

Reviewed `wip-compactlog` at `f5696ae` against its base `c4e592a` and main at `869be24`. Ben approved moving all five kinds. The layout substantially reduces the uncompressed checkpoint payload for a history recorded in the new format. **Hold sign-off on the exact-record claim and the mixed-checkpoint gate output.** Findings 1–3 have local reproductions.

## Ranked findings

### 1. Check 9 loses every land move recorded before a checkpoint crossed formats

- **Where** — `gates/g4.py:323–327,336–365`, `gates/g4_report.py:325–332`, `origins/persist.py:127–134,254–255`.
- **What is wrong** — Restore preserves old land-move events, but `extras` replaces the land-move count with only the compact table length. Check 11 already samples both stores. The inherited G2/G3/G4 `events` summary has the inverse omission, because it reads only `w.events`. G0, G0 slice and G1 have the same summary loop.
- **Why it matters** — Check 9 can fail its occurrence condition if the only land move was before the resume and there was no abandonment. A mixed record can disagree with itself about how many moves occurred. Generic event summaries undercount all five kinds after the switch.
- **How sure you are** — Certain.
- **How to see it** — Save a base world with one land move and one `land_hunger`, then load it on the branch and run `g4.extras`. The land-move count is **0** and the check-11 move sample is **[1, 1, 1]**. After appending one compact move, those become **1** and **[2, 2, 2]**. A compact help row also resolves and appears in band history while `g2.finish(..., write=False)` omits it from `events`. Count the legacy events and compact rows together once. The new per-kind `w.counts` entries only count rows produced with compact recording active.

### 2. Re-reading the record can change the names in its historical notes

- **Where** — `origins/sim/minorlog.py:156–158,172–213`, `origins/state.py:76–81,498–501`, `origins/sim/language.py:112–128,164–169`, `origins/sim/groups.py:unfold`.
- **What is wrong** — The old log froze each name in the note when it wrote the event. The compact rows look up current band names when read. Even the same leader can have a different rendered name after a language change. Unfolding can also replace the leader used to render a band name.
- **Why it matters** — The same row can tell a different story about how the peoples were named, including after save and restore. The proposal promises the same recorded sentence. Shadow mode renders at insertion time, so its all-event hash cannot detect later drift.
- **How sure you are** — Certain.
- **How to see it** — Record a near partnership for the first two planet-1 bands. Apply the existing `grimm_fricatives` sound change to their shared language on a later tick. Re-read the row. “Band of Ekwomena” becomes “Band of Ekhwomena” in the historical note, and the second name changes too. An old event preserves the original names. A shared table of the historical name forms would preserve the wording without storing every sentence.

### 3. Small positive gifts lose a field when they round to zero

- **Where** — `origins/sim/trade.py:257–269,357–387`, `origins/sim/minorlog.py:110–112,161–163,189–207`.
- **What is wrong** — The old writers include a gift key when the unrounded transfer or total is positive, then round its value to six decimals. Compact encoding maps a missing key to zero and reconstruction keeps only values above zero. Both “gold was given, rounded to 0.0” and “no gold was given” become the same row.
- **Why it matters** — A first-gift record can say an exchange happened while both goods dictionaries are empty, and a later lapse can lose the same evidence. The loss affects both production and shadow mode. The simulated transfer still occurred.
- **How sure you are** — Certain.
- **How to see it** — Link two bands on one cell. Give the first `1e-7` gold and run `partnerships_yearly`. It transfers `5e-9`. On base, both the first-gift record and the lapse contain `{"gold": 0.0}` for the giver. On the branch both dictionaries are empty. Preserve per-good presence independently of its rounded amount.

### 4. Observatory feeds disagree about what happened and can reverse same-tick history

- **Where** — `origins/server.py:570–579,654–680,773–776`, `origins/sim/minorlog.py:237–251`, `observatory/index.html:505–508,649–656`.
- **What is wrong** — “Recent events” still reads only `w.events`, so all five kinds disappear from that feed as soon as the world starts writing compact rows. Band history merges stores by tick alone, with legacy rows preceding compact rows on ties and compact kinds ordered by table. An older partnership where the viewed band appears only as `data.partner` is omitted by the legacy filter, while the equivalent compact row appears. The band endpoint reconstructs every matching compact row before applying its 30-item limit.
- **Why it matters** — A new and a resumed history show different coverage for the same happenings. A swap appears to begin the replacement partnership before dropping the old one. At the 30-item boundary, ordering by kind can also change which events survive the cut. Work for an active band's history grows with all matches despite the bounded response.
- **How sure you are** — Certain about coverage and order. Full-scale observatory latency is unmeasured.
- **How to see it** — Load an old checkpoint and append a compact help row. Its reference appears in `server.band_detail` but the row is missing from `server.recent_events`. Record a same-tick swap, lapse first. Band history returns `partnership_formed` before `partnership_lapsed`. An ordering key shared across stores and bounded lookup before rendering would give the feed the information it currently cannot recover.

### 5. The direct explanation path accepts negative compact row IDs

- **Where** — `origins/sim/minorlog.py:166–171`, `origins/explain.py:39–48,298–305`, `origins/server.py:676–681,775–776`.
- **What is wrong** — The gate validator rejects negative log rows, while the observatory explanation path indexes the table directly. NumPy's negative indexing then reads a real row and the response carries the invalid reference.
- **Why it matters** — Users can get a valid-looking history for a nonexistent reference, and the two readers disagree about whether it exists.
- **How sure you are** — Certain.
- **How to see it** — With one formation row, `resolvable(w, {"log": ["partnership_formed", -1]})` is false. `describe(w, parse_ref("log:partnership_formed:-1"))` returns the title of row zero. Check bounds in the shared reader.

## Space at pilot scale

The counts below come from the approved proposal's planet-4 checkpoint. They describe a counterfactual history written entirely in compact form. Resuming that existing checkpoint leaves its original event JSON and offsets in place and adds rows only for new happenings. The proposal's five kinds occupy **4,590 MiB uncompressed**. The compact widths measured from the implemented dtypes give the following used bytes, before compressing.

| Table | Pilot rows | Bytes per row | Used MiB |
|---|---:|---:|---:|
| Help | 3.76 million | 48, plus 8 per giver | 172.1, plus 28.7 per average giver |
| Formations | 3.24 million | 56 | 173.0 |
| Lapses | 3.21 million | 88 | 269.4 |
| First gifts | 2.33 million | 64 | 142.2 |
| Land moves | 2.44 million | 64 | 148.9 |

- With **two givers per help row** as a sizing assumption, this is **963 MiB** of used rows, **1,344 MiB** of allocated capacity from ordinary doubling, or **1,926 MiB** of reserved capacity immediately after load. Reserved zero-filled pages can remain untouched until used. The old cold store kept its JSON on disk and used about **114 MiB of offsets** for these events, plus its bounded hot window. Compacting trades more resident row data for less event disk use and fewer JSON encode/decode passes. It does not imply a RAM saving from the raw JSON comparison.
- The save writes the used prefixes and deflates the outer ZIP. A synthetic one-percent population of the tables, with pseudo-random IDs and amounts, gave **9.63 MiB raw and 5.33 MiB compressed** at the checkpoint's fast compression level. The pilot's real compression depends on ID, tick and value locality. Actual compressed size and peak RSS on restore remain unmeasured.
- The restore path inflates the whole `arrays.npz` member, decodes its arrays, then copies the compact rows into new buffers. The compact log alone can contribute roughly one used-payload copy at each of those stages. Digesting the lapse table materializes a **269 MiB** byte string at these counts. Save, restore and digest should be measured separately at a late checkpoint. `origins/sim/minorlog.py:39–79,254–268`, `origins/persist.py:101–134,251–255,385–388`.
- Every row, giver ID and surviving legacy or noncompact event grows with history length. Packed-band strings can also retain distinct last-move texts containing row IDs. Check 11 samples compact tables by position without allocating a list for every compact row. For legacy events it still holds a Python ID list for each sampled kind, with entries proportional to the legacy candidates. Band history scans the full tables and renders matches eagerly.

## Checked and sound

- At record time with stable names and gifts above the rounding boundary, the actual writers matched between base and branch shadow in targeted fixtures. These covered near and swapped-in formations, all four lapse reasons, first gifts in both directions, help from two givers, and a land move with both game and forest sources. I compared the serialized event payload and cause order without sorting keys or comparing IDs. Help retained its rounded amount and giver order.
- `foraging._land_move` is the one production caller I found that consumes the removed event's return value. It now uses the compact row in `last_move`. Its two cited land events remain ordinary event IDs in sorted cause order. I found no place rule or cause-chain cache that depended on the removed kinds as intermediate links. The fission index and conquest scan still read their own ordinary event kinds.
- Mixed-format save and restore kept both reference forms and reproduced the branch digest. G4 check 11 combined both stores in the tested mixed case. Check 7's help measurement wraps the food transfer and does not depend on either event representation.

## Validation

Seven compact-log tests and six focused trade and land tests passed on `f5696ae`. I also ran paired fixtures against both source archives, an old-save continuation and a synthetic ZIP sizing check. The reported planet-3 checkpoint hash is Claude's evidence. This review used short fixtures and the published pilot row counts.
