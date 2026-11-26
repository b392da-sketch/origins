# Review 042 — lazy loading and compact columns

Reviewed `wip-lazyload` at `07f62da` against `2ed0ee0`, with main at `c966fd5`. **Hold rollout of the split-column save format on finding 1.** The branch preserved the tested wide-format history, and the new layout cuts the raw compact-table payload substantially. It still decodes and copies all five tables together at the restore point where memory matters most.

## Ranked findings

### 1. The previous reader accepts the new format and silently drops its compact history

- **Where** — `origins/state.py:20–21`, `origins/sim/minorlog.py:377–410`, `origins/persist.py:275–285,410–413`.
- **What is wrong** — Split-column saves still declare schema 4. The previous reader accepts this schema and looks for the old `minor_<kind>` keys. With only `_i` and `_f` keys present, it initializes empty tables without an error. The other metadata, including the saved counts, still loads.
- **Why it matters** — Rolling back the code or opening a newer checkpoint in an older checkout silently erases all compact explanations and undercounts the previous history. The gate report and traceability samples then work from an incomplete record. This is the same compatibility failure that prompted the schema change in review 040.
- **How sure you are** — Certain.
- **How to see it** — Save a branch world with one help row, two formation rows and one first gift. The branch and the previous reader both accept schema 4. The previous reader returns zero rows for all five kinds, still reports the saved help counter as one, and fails to resolve `{"log":["helped_by_partners",0]}`. The branch resolves it. Use a schema marker that the previous reader rejects while retaining the wide-format migration.

### 2. Restore still materializes every compact table before rebuilding the first one

- **Where** — `origins/persist.py:103–106,410–413`, `origins/sim/minorlog.py:60–88,392–410`.
- **What is wrong** — `_prefixed(arrays, "minor_", strip=False)` constructs an eager dictionary of the entire compact section. The dictionary stays alive while the constructors copy each table into its backing buffers. Wide migration also creates selected-column temporaries, int64 casts and a range-check temporary.
- **Why it matters** — The largest component still has a whole-section overlap. On the pilot's wide checkpoint, roughly **1.4 GB** of decoded table inputs can overlap most of the **843 MB** of narrowed payload, plus conversion scratch. A split checkpoint is cheaper but still duplicates its whole compact section temporarily. This limits the savings available when a heavily populated history first resumes from wide format.
- **How sure you are** — Certain about the lifetime and observed synthetic peak. Full runner RSS remains unmeasured.
- **How to see it** — At one-tenth of the five pilot table sizes, I loaded the same arrays through the current eager-prefix call and through `minorlog.load(w, lazy_arrays)` directly, in fresh processes. The table-by-table route lowered peak RSS from **299 to 198 MiB** for wide inputs and from **200 to 136 MiB** for split inputs. This isolated fixture tests the compact section only. Let each table consume its own members and release the source before moving to the next.

### 3. Repeated reads now decode fresh copies of the same array

- **Where** — `origins/persist.py:73–80,406–407,414–416,432–438`, `origins/sim/trade.py:partner_load`, `origins/sim/disease.py:load_rows`.
- **What is wrong** — Several consumers read a member to check its size and then read it again to use it. The old dictionary returned the same instance for both. `partner_load` also keeps its first `partner_of_rows` read in `of` while the loop decodes a second copy into `r`.
- **Why it matters** — This adds redundant allocation and archive decoding. At 1.7 million disease-log rows, the repeated `dz_log` read alone decodes about **220 MiB** twice. The first disease-log read is temporary and normally dies before the second. The two partner-link reads do overlap, including while the replacement row buffers are built. Older dense saves can also decode `dz_last` or `dz_seen` twice.
- **How sure you are** — Certain.
- **How to see it** — Count calls to `_LazyArrays.__getitem__` during a normal restore with a nonempty disease log. I observed two each for `dz_log`, `dz_active`, `dz_since`, `partner_of_rows`, `trade_in` and all four saved previous-technology fields. Read each member into a local once and use that array for both the check and the consumer.

### 4. Whole-number validation can truncate values before it checks them

- **Where** — `origins/sim/minorlog.py:66–88,90–103`.
- **What is wrong** — The append path calls `int()` before validating. Wide conversion casts to int64 before testing the int32 range, and the range check uses `abs` on signed integers. A fraction can silently lose its fractional part, and a wide value beyond int64 can hit the signed minimum sentinel during the cast and bypass the later check.
- **Why it matters** — A malformed reference or a future caller's fractional value can become a different, valid-looking tick, ID or offset. The tested simulation writers supply integer values, so I found no normal gate path that triggers this.
- **How sure you are** — Certain for the tested inputs.
- **How to see it** — Insert `after=1.75` through either append or wide migration. Both read back as **1**. A wide fixture with `after=2**63` emitted a NumPy cast warning and loaded as **0** locally, without the stated `OverflowError`. Validate finiteness, integrality and the signed range before narrowing. The append check also rejects the valid signed int32 minimum, though no current field uses that value.

## Exactness and int32 at gate scale

- **Inputs from the current writers.** Ticks are integer calendar ticks and reach about **120,000** at 30,000 years. Cells, reason codes, row IDs, name indexes, the preceding event count (`after`), the global row sequence (`order`) and giver offsets are produced as integers. Lapse years come from an integer division. The amounts, closeness, food values and gifts remain float64. The normal negative sentinel is **−1**.
- **Counters and offsets.** The stage-1 save sizes imply about **15 million** compact rows at year 5,733 and about **7.1 million** giver IDs from the 57 MB int64 list. Extending those historical averages to 30,000 years gives roughly **79 million** rows and **37 million** giver IDs. This is a scale estimate, not a model bound. `after` can include many legacy ordinary events. On the current runner, an ordinary event store near the signed int32 ceiling would already need almost **16 GiB** just for offsets. The giver list would need roughly the same at its own ceiling, and compact rows would use much more. I see no practical int32 limit problem in the supported gate, while retaining explicit validation for unsupported values.
- **Wide migration and replay.** A genuine wide save and a split save from the same fixture restored on the branch with identical reconstructed rows, cause references and digests. Their digests still agreed after a simulated year. The hash on the previous writer differs in ordinary mode because `persist.digest` includes the names and bytes of the serialized arrays. The reported unchanged digest should specify whether it excludes compact tables in shadow mode or uses a common representation. This is distinct from a state change during migration. Historical schema-1 and schema-2 fixtures still hit the inherited planet fingerprint guard noted in review 041.

## What remains at planet-4 scale

| Table | Wide payload at year 5,733 | Split estimate at same row count |
|---|---:|---:|
| Lapses | 400 MB | 250 MB |
| Formations | 303 MB | 164 MB |
| Help | 268 MB | 149 MB |
| First gifts | 217 MB | 145 MB |
| Land moves | 212 MB | 135 MB |
| **Total** | **1,400 MB** | **843 MB** |

The estimates use the saved row widths and describe used payload. Backing capacity, temporary copies, the unchanged giver list and the name index are additional. They do not predict compressed archive size or full-process RSS.

- **Next largest named arrays.** Technology and its record are **226 MB each** in the stage-1 trace, followed by goods at **151 MB**, neutral traits at **101 MB**, packed trails at **79 MB** and skill at **75 MB**. `tech_record` and goods still copy into fresh destinations. Packed band columns, people and groups also decode one whole prefix and then copy into their structures. Their peak contribution can exceed the largest single member. At 4,194,304 allocated rows, the technology record and goods overlap alone would be roughly **720 MiB** if both were live together. In this loader those two particular copies are sequential.
- **Priority.** Remove the whole compact-section overlap first. Then use per-section trace data to prioritize the remaining copies. Where dtype and layout match, adopt the decoded destination buffers directly for the technology record and goods, preserving the legacy padding paths. Measure packed-band and people reconstruction separately. At the observed stage-1 scale, metadata is a lower priority than these arrays. Reassess the polity log at later years as it grows.
- **Pilot evidence.** The stage-1 job logged the array and metadata sizes in the request. Stage 2 was still in progress when checked and its logs had no retrievable restore trace. This review uses the stage-1 widths and the isolated measurements. [Pilot 3 stage 1](https://github.com/b392da-sketch/origins/actions/runs/45794080188/job/139820219239) · [Pilot 3 stage 2](https://github.com/b392da-sketch/origins/actions/runs/45794080188/job/139967116321)

## Checked and sound

- The audited restore consumers use key membership, indexing, iteration or `get`. I found no read that depends on a shared array identity or writes back into the mapping, and no live consumer requiring `len` or `values`. `_drop` hides names without releasing any arrays owned by the finished world.
- The NPZ and its scratch file are scoped to the same `ExitStack`, in reverse closing order. I verified cleanup after success and an injected failure in the compact-log consumer. A caller-supplied open save file remained open after restore.
- All **26** compact-log and row-persistence tests passed. I also ran paired loader and continuation fixtures, traced actual member access counts, and benchmarked the compact conversion in isolation. No full-sized planet-4 restore was run locally.
