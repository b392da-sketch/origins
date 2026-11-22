# Review 040 — per-band rows

Reviewed `wip-rows` at `94e087a` against its compact-log base `f5696ae`, with main at `82627bd`. **Hold checkpoint rollout on findings 1–2.** The normal lifecycle and retirement paths checked below retain the intended behavior. The outstanding findings in review 039 belong to the compact-log base.

## Ranked findings

### 1. The dense reader silently accepts sparse saves and loses their disease and partner state

- **Where** — `origins/state.py:20–21`, `origins/persist.py:63–65,99–106,127–142,233–271`.
- **What is wrong** — The writer still declares schema 3 while replacing the dense partner and disease arrays with different keys. The previous reader accepts schema 3 and treats missing dense keys as a save from before those features.
- **Why it matters** — Opening a sparse checkpoint on the previous revision can start a history with cleared immunity, exposure dates, links and gift totals. The save opens cleanly in the same Python and NumPy environment. Rolling back the code or handing the checkpoint to an older checkout could silently change the continuation.
- **How sure you are** — Certain.
- **How to see it** — Save a sparse world with four links and a named disease with immunity **0.75** and a known exposure year. The reviewed branch retains them. The base reader loads the same ZIP with **zero links**, immunity **0.0**, and an empty warning. A distinct schema that the old reader rejects would make the incompatibility explicit.

### 2. A four-link sparse save can crash on the first partnership pass at the default cap

- **Where** — `origins/sim/trade.py:101–125,128–164,272–278,334–340,422–452`, `origins/persist.py:236–248`.
- **What is wrong** — Dense conversion widens rows to at least `PARTNERS_CAP`. Sparse loading uses only the saved width. The old growth path also widened the dense rows. The annual pass still computes free places using the current cap.
- **Why it matters** — A narrow sparse checkpoint resumed under a larger cap can advertise free places it has no storage for. Fixed-arm gate continuations use the same cap within the arm. This defect affects a checkpoint resumed with settings that raise the cap, including a four-partner save opened with defaults.
- **How sure you are** — Certain.
- **How to see it** — With `PARTNERS_CAP=4`, save a band of 200 people with four partners and an eligible fifth band on the same cell. Reload at cap 16 and force successful formation. Dense migration widens to 16 and the actual annual pass adds the fifth link. Sparse load retains width 4, the allowance reports **10**, and `_link` raises `IndexError` while looking for an empty slot. Keep width and allowance consistent on restore, preserving existing link positions and gifts.

### 3. A legacy band ended before the arrays existed can still be assigned rows

- **Where** — `origins/rows.py:30–57`, `origins/sim/disease.py:709–731`, `origins/sim/trade.py:128–139`, `origins/persist.py:236–247`.
- **What is wrong** — Legacy conversion marks only the IDs already covered by the old arrays as ended, and the no-partners path marks none. An ended, issued ID with no old row remains assignable. `SlotMap.release` also leaves an absent ID unmarked.
- **Why it matters** — Both maps can accept an ended band that should be rejected under the new contract. This weakens the intended guard against accidental reads or population transfers involving ended bands. I found no ordinary phase that attempts that reassignment.
- **How sure you are** — Certain about the guard gap.
- **How to see it** — Take a save with three living bands and an ended fourth band. Remove the disease and partner arrays to represent a save from before those features. On restore the ended band's slot is **−1** in both maps, and both `assign(ended_id)` calls succeed. Mark issued ended IDs independently of old array coverage. Unissued IDs at or above `next_band` should remain never assigned.

## Lifecycle, retirement and old formats

- **Ended rows.** Captures and marriages combine exposure after the people move and while the two bands still have rows. A band that has just lost its last person can still hold its row until the ending pass. Consolidation and small-band merging carry exposure before release; partner lapse records are written before the corresponding rows are cleared. I found no normal ended-row lookup in these paths. The observatory has no direct reader of these five sparse arrays. The disease contacts pass and G4 help observer index live bands and rely on all of them getting rows on creation or load. The six focused lifecycle tests passed.
- **Retirement.** For known dates, the per-slot maximum over current rows and the maximum over ended rows preserves the dense value. In a paired fixture, an ended band's year **180** outweighed a live band's year **90**, both implementations chose the same slot for reuse, and both wrote **180** to the retired record. Resetting the retired column cleared the historical maximum before a new band inherited the row. There is one literal distinction: an artificial dense column containing only **−2** reduces to **−2**, while `last_any` has a **−1** floor. That difference is immaterial to the current consumers. `_free_slot` takes the maximum with a nonnegative disease birth year, and `_retire` already clamps the reported date at **−1**. A live band's **−2** remains available for its own exposure classification. `origins/sim/disease.py:167–180,427–464`.
- **Legacy inputs.** I verified four-link dense conversion, missing gift totals starting at zero, explicit `dz_seen` producing **−2** for a living exposed band, and unused IDs staying unassigned. The no-array path initializes living bands to defaults. Without `dz_seen` or saved dates, immunity is used as the old reader's fallback for unknown-date contact. Finding 3 limits the ended-ID guard when old arrays were absent or too short. Valid sparse save/load preserved the slot-map order and digest in the focused fixtures.

## Memory at pilot scale

- The five replaced payloads save **1,280 bytes per allocated dense band row** at the default cap. At 2,097,152 rows this is **2.50 GiB** of old arrays. The two new band-ID-to-slot maps still use **16 bytes per allocated ID** together, or **32 MiB** at that capacity. The sparse payloads now scale with the concurrent slot high-water mark. At 14,000 held rows their used payload is about **17 MiB**. Backing arrays can grow above that, and saves include free slots below the high-water mark as well as the owner and free lists. Churn reuses those slots without growing the payload just because new IDs are issued.
- In a short run of 2,048 band creations and endings, the disease and partner payloads still used four slots. The other growing saved per-band arrays accounted for **668 bytes per allocated ID**, excluding the two slot maps and packed-band records. That includes technology and its record (108 bytes each), goods and reach flags (81), skill (36), customs and neutral traits (59), and the remaining farming, polity, technology and land bookkeeping. Packed-band columns and trails add about **143 bytes per packed slot**, excluding string storage. At a common capacity of 2,097,152, those three subtotals are about **1.62 GiB**. Actual capacities can differ. Individual histories, event and compact logs, cell arrays, and transient phase arrays are additional.
- Loading a **dense** save still inflates the whole array member and retains the old arrays during conversion. `last[dead].max(axis=0)` additionally materializes the dead-ID gather. At 1.7 million issued and 14,000 living IDs that temporary is about **412 MiB** for 64 int32 dates per dead band. The branch's reported **10.4 GB** restore peak is still relevant to the first dense-to-sparse handoff. The reported stepping RSS comparisons also change the compact-log mode, so they cannot isolate the savings from sparse rows.
- `SlotMap.assign` uses `np.append` on every new owner slot. Initial loading or a rising concurrency peak therefore copies a quadratic number of owner entries before reuse starts. At 14,000 distinct slots that is about **784 MB** of owner-copy traffic per map. The isolated one-map test took **0.043 s** locally, making it secondary to the large array loads at the scale measured. `origins/rows.py:30–49`, `origins/sim/disease.py:731–733`, `origins/persist.py:127–138`.

## Event hashes across GitHub runners

**The cause is undetermined.** CPU or NumPy/BLAS differences are plausible, but matching final population and RNG state does not establish that only printed floats differed. The event hash includes the full JSON values, notes, order and IDs. Two runs can consume the same random draws and still make different numerical or branch decisions. The two old timing commits, `e0f2994` and `1cfaeab`, differ only in the timing tool. Its hashing loop is the same. Their workflow installs an unpinned NumPy version and requests Python 3.13. The Actions API returned HTTP 403 here, so the actual runner versions, CPU and first differing event remain unverified.

The repository already promises exact save/replay and warns that future results may differ when Python or NumPy versions change. For a staged gate, apply the exact-match expectation across runners using the same supported execution environment. Otherwise checkpoint placement or runner assignment can affect the history. Pin and record Python, NumPy, BLAS/thread settings and runner architecture for the comparison. Compare the first differing record and the relevant state at that tick, then compare uninterrupted and staged continuations. That evidence can distinguish a representation-only difference from a simulation divergence. An exactness guarantee across arbitrary machines and versions would be a separate project decision. `CLAUDE.md`, `docs/DESIGN_DRAFT_v0.6.md` §13, `origins/persist.py:48–50,149–154`.

## Validation

Seventeen focused tests passed on `94e087a`. I also ran paired base and branch fixtures for both checkpoint failures, legacy migration, retirement and slot reuse, and measured array widths using small synthetic worlds. The planet-4 timings and memory figures are those in request 040. I did not independently reproduce the cloud hash mismatch or measure a full-sized sparse restore.
