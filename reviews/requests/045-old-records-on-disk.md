# Review request 045: old records on disk

**From:** Claude, 29 November 2026. **Branch:** `wip-cold`. **Not yet merged.** Ben chose this on 29 November 2026 over bigger runners or a shorter target. The figures are in `docs/M4_BUILD_NOTES.md`, "Old records on disk".

## Why

Pilot 5's world grew from 5.3 GB in memory (restored at year 7,508) to 8.0 GB (at year 8,773), with an 11.9 GB save peak. On that trend a planet-4 history would pass 16 GB before year 11,248. The growth was in:
- the compact log;
- people;
- the polity log, as Python lists;
- the disease log.

## What changed

- **`origins/spill.py`:**
  - `alloc` makes an array of `SPILL_MIN` (32 MB) or more as an `np.memmap` over a file in a temporary folder, which is removed at exit;
  - `regrow` grows a mapped array by truncating its file to the new size and mapping it again, so old rows are not copied;
  - `ORIGINS_SPILL=0` turns it off, and `ORIGINS_SPILL_DIR` names the folder.
- **Where it is used:**
  - `People._blank` and `_grow`;
  - `minorlog.Table` and `Ints`;
  - `disease.RowLog`;
  - the new `polity.PolityLog`.
- **`polity.PolityLog`:** a table with 10 int64 and 2 float64 columns, behaving as the list of 12-value rows: `append` (checked), `len`, iteration, indexing, slices and `del log[:-k]`.
  - `to_json(w, with_log=False)` for saves;
  - `log_arrays(w)` gives `polity_log_i` and `polity_log_f`, and `from_json(..., arrays)` reads them, falling back to old rows;
  - the digest hashes the arrays;
  - the schema is 7;
  - `gates/g3.py` puts `list(pl)` in the record.
- **Saving:**
  - `People.arrays()` returns views, not copies;
  - `meta.json` is converted part by part as written.
- **`gates/run_job.sh`:** TMPDIR goes to `/mnt/origins-tmp` when the runner has `/mnt` and `sudo`, and the job logs `df`.
- **Gate output:** the year lines add anon memory and free disk, and `[mem]` lines add anon.

## Evidence

- **Same events:**
  - planet 3, 20 years from year 9,910: `f9eb76a6d77265d1`;
  - planet 4, 5 years from year 6,631: `c3e0b565819d60f0`, with the same counts.
- **Memory on that planet-4 save:** after loading, 2.47 GB anon plus 2.43 GB of mapped pages, against 5.19 GB anon on main. Saving peaks at 2.68 GB anon; on main it did not finish within this container's 8 GB.
- **`tests/test_spill.py`:**
  - mapped arrays and growth;
  - a world with and without mapping digesting and replaying alike;
  - the polity table against the list it replaces;
  - saves as arrays, and older rows.
- **The full suite with `ORIGINS_SPILL_MIN=4096`:** the result is in the commit message.

## Please check

1. **Exactness and aliasing:**
   - anything holding a view of a people field, table or log across a `regrow` (the old mapping stays valid but no longer grows);
   - whether `np.memmap` subclass behaviour changes any result (ufunc outputs, `copy`, `tolist`, pickling, `tobytes` in the digest);
   - whether `PolityLog`'s types and rounding match the old rows exactly.
2. **Lifetimes and the runner:**
   - files and mappings freed when worlds are dropped (tests make many worlds in one process);
   - disk use on the runner, with several histories side by side, the lazy loader's unpacked npz and the event store's file in the same TMPDIR;
   - what happens if `/mnt` is missing, or when the disk fills.
3. **Memory accounting:** whether dirty mapped pages under memory pressure can still make the runner fail, and whether the gate should watch anon memory or something else.
4. **What still grows in memory:** Python metadata such as the bands' strings, languages, places and polities, the events' offsets and kept outbreaks, groups and packed bands. Please rank them for planet 4 at year 11,248.
