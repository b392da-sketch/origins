# Review 041 — loading large saves

Reviewed `wip-restore` at `089b20e` against `9264a97`, with main at `b51b096`. The gate workers now avoid reading the entire compressed save and decompressed NPZ into Python byte strings. The targeted replay checks agree with the previous loader. **The remaining copy and diagnostic costs need to be measured on a late planet-4 restore before treating the memory problem as resolved.**

## Ranked findings

### 1. Several of the largest arrays still have two live copies during restore

- **Where** — `origins/persist.py:175–179,228–234,262–269,278–285,304–323,352–353`, `origins/state.py:People.from_arrays, Bands.load_arrays`, `origins/sim/disease.py:RowLog.from_array`, `origins/sim/minorlog.py:Table, Ints, load`.
- **What is wrong** — The loader decodes every array into a dictionary and retains all of them until it returns. Goods, the technology record, packed bands, people, groups, disease history and the compact logs still allocate or copy into destination buffers. The new `np.asarray` calls remove copies for the fields they touch.
- **Why it matters** — Peak size depends on saved payload overlap as well as the size of the finished world. At the pilot's 4,194,304 allocated band rows, the goods and technology-record copies alone account for about **720 MiB**. A packed band archive near that row count can add about **572 MiB** of overlapping column data, before the disease log and other histories.
- **How sure you are** — Certain about the copy lifetimes. Their exact share of the runner's peak remains unmeasured.
- **How to see it** — Inspect ownership starting at the NPZ dictionary and follow its consumers. At current width, goods are nine float64 values per row and the technology record is 27 float32 values per row. `RowLog.from_array` allocates twice the used size and copies the used prefix. The compact-log constructors also hold both the decoded and copied prefixes while the dictionary lives.

### 2. Save tracing repeats JSON work, and the load labels obscure the largest late copies

- **Where** — `origins/persist.py:60–85,141–157,303–375`, `.github/workflows/gate.yml:27–29`, `gates/run_job.sh:37–44`.
- **What is wrong** — The workflow enables a second, full `json.dumps` of every metadata section. It uses a different encoder and separators from the actual save, so its displayed sizes are estimates of a different representation. On restore, “disease and places built” prints before compact-log loading and the disease cell and per-band rows. The next marker also includes land, people, groups and remaining metadata.
- **Why it matters** — The trace adds allocation and CPU work to a save close to the runner limit, and its final restore interval cannot identify which of several large reconstructions made a peak. The issue is the work behind the diagnostics. Output itself is about ten short lines per restore and two per save, and the wrapper only forwards the last 30 worker lines.
- **How sure you are** — Certain about the extra work, different sizes and marker placement. The local fixture did not raise the measured save peak.
- **How to see it** — A world with 650,000 synthetic polity rows produced a **34.6 MB** compact polity section. The trace estimated **42.4 MB**. Save took **3.37 s** with tracing off and **3.73 s** with it on, at the same **470 MiB** peak RSS to rounding. All decoded ZIP members were identical. Measure actual serialized bytes from the write path and add markers around the compact log and the packed people/groups reconstruction. Where available, include cgroup and scratch-space figures alongside process RSS.

### 3. The observatory's path-based load still retains the compressed checkpoint bytes

- **Where** — `origins/persist.py:399–401`, `origins/server.py:60,737`.
- **What is wrong** — The public `load(path)` helper still calls `from_bytes(f.read(), planet)`. The autosave and the observatory's load action both use it.
- **Why it matters** — A 2 GiB save still costs roughly 2 GiB of compressed input on this path while the world is constructed. The gate workers use the new streaming path, so the gap affects interactive and other callers of the existing helper.
- **How sure you are** — Certain.
- **How to see it** — Follow `persist.load(path)` from either server call. It reads the whole file before `from_file` runs through the bytes wrapper. Passing the path through directly would use the same parser without the extra buffer.

## Compatibility and replay

- `from_bytes` delegates to `from_file`. The migration rules remain in one implementation. Each ordinary NPZ member supplies its own mutable array. A dtype-preserving `np.asarray` can share with that member in the local dictionary; it does not make distinct saved fields share buffers. The fallback from practice to import dependence still uses an explicit copy. I checked restored array pairs for sharing and checked read/write flags on the changed fields.
- A real schema-3 save and schema-4 fixtures with both compressed and uncompressed inner NPZ payloads produced matching digests between the pre-change and branch loaders, including after one simulated year. On the branch, path, open-file and bytes inputs also agreed, and the caller's file object remained open.
- Two genuine early saves produced by the original schema-1 and schema-2 writers both failed the existing planet fingerprint check on both versions. As an isolated parser exercise, substituting the supplied planet's fingerprint let the schema-1 fixture load identically. The early schema-2 fixture then failed in both versions because `language.from_json` expects nine fields and its record has eight. These are inherited compatibility limits. A readable schema number alone does not make every historic save compatible.

## Where memory goes at year 8,000

- **The decoded arrays set the floor.** Review 040's approximately 668 bytes of dense state plus 16 bytes of slot maps per allocated band ID give about **2.67 GiB** at 4,194,304 IDs. Packed band columns can add up to about **0.56 GiB** at that capacity. This is before people and group arrays, sparse row payloads, cell arrays and logs. The 1.7 million disease-history rows add about **220 MiB** at 17 float64 columns. Compact history tables grow separately with recorded happenings.
- **Metadata and restore copies are the likely next peaks.** Loading `meta.json` holds the serialized JSON and builds a Python object graph. At 3 million polity rows, the 12-column row-list containers alone would be about **526 MiB** at the measured 184 bytes per list, before the outer list and boxed numbers. In the 650,000-row fixture RSS went from about **0.03 GB** to **0.27 GB** after metadata parsing, consistent with roughly a gigabyte of resident metadata at 3 million similarly shaped rows. Actual field values and sharing determine the total. There are also packed band strings, languages, probes and the copies in finding 1. Worker probe JSON is parsed after the last loader marker.
- **The ordinary event cache has a smaller resident floor.** 6.8 million offsets take about **52 MiB**, plus hot rows, permanently retained outbreak dictionaries and a transient freeze batch. The cold JSON lives in a temporary file. Restore still walks and parses the entire stream, then serializes cold rows into that file, so it can cost substantial time and disk even when its RSS is comparatively small. The scratch NPZ is closed before this event rebuild. Disk-backed page cache and any `tmpfs` allocations are outside the process RSS trace. Trace peaks are cumulative process RSS in Linux KiB divided by a million, not an independent measurement of runner or cgroup headroom.

**First changes for exactness.** Adopt compatible decoded buffers for goods, technology records and packed columns, keeping the existing dtype, shape, default-padding and growth rules for older inputs. Then read the NPZ by consumer and release converted input arrays before building the next large section. Validate with digest and continuation tests across current and legacy layouts. Next, measure the polity log and compact tables independently. Stream or move the largest metadata member to a bounded representation only if its record order, values and lookup behavior can be kept exact. Check the NPZ member's uncompressed size and available scratch space before inflating, and report that alongside memory. Keep the tested fallback allocations for older formats.

## Workflow and retention

- All ten checkpoint artifact uploads now use **14 days**, with the last already at that value. The report still excludes checkpoint artifacts from download. Retention helps recover a failed handoff while the earlier artifact exists; it applies to new uploads and does not revive expired artifacts.
- Each stage stores a full snapshot. The four pilot-2 checkpoints listed in the request sum to about **6.3 GiB** before any artifact-wrapper compression. A sizing scenario of 100 histories each uploading ten 2 GiB checkpoints is about **2 TiB per gate run**. Actual usage depends on how many histories reach later stages, checkpoint sizes and retention policy. Holding the same volume for 14 days uses seven times the storage-days of a two-day policy. The repository's quota and billing allowance remain unverified.
- Pilot 2's stage-4 job reported **15.54** in the current peak RSS units. Stage 5 reported runner shutdown and exit **143**. This is consistent with memory pressure, but the job log does not identify the shutdown cause. Pilot 3 was still running stage 1 when checked, so it had yet to produce restore measurements. [Pilot 2 stage 4](https://github.com/b392da-sketch/origins/actions/runs/44973846305/job/137260773414) · [Pilot 2 stage 5](https://github.com/b392da-sketch/origins/actions/runs/44973846305/job/137340678450) · [Pilot 3](https://github.com/b392da-sketch/origins/actions/runs/45794080188)

## Checked and sound

- All five checkpoint workers switched to `from_file` and retained their existing checkpoint/planet handoff. The temporary NPZ is closed automatically after array decoding. It adds a local scratch requirement even for bytes inputs, which is distinct from resident array size.
- Eight focused tests passed. I also ran paired loader and continuation fixtures and the local traced-save benchmark. The review uses the request's late-history counts and the observed workflow logs for gate-scale conclusions.
