# Review request 040: per-band rows only for bands holding one

**From:** Claude, 22 November 2026. **Branch:** `wip-rows`, on top of `wip-compactlog` (request 039). **Not yet merged.** Ben's decision (22 November 2026, after the planet-4 pilot): keep per-band arrays only for bands holding people, with the same results to the last bit.

## Why

At year 5,765 the pilot had issued 1.7 million band ids, with about 14,000 bands alive. Every M4 per-band array held a row per id, 4.24 GiB in all (review 037's measure, and the stage-2 checkpoint). The largest were:
- disease immunity, 1 GiB;
- disease last circulation, 0.5 GiB;
- partner gifts, 0.5 GiB;
- partner links and start, 0.25 GiB each.

The pilot's first village came at year 5,248, so its history runs to about year 11,250. Ids issued by then would push these arrays past 16 GB.

## What changed

- **`origins/rows.py`:**
  - `SlotMap` gives each band holding a row a slot, and frees it when the band ends. Freed slots are reused, last freed first.
  - `SparseRows` is indexed by band id like the dense array it replaces: an int, ids, or `:`, then the trailing indices. Reading or writing an ended band's row raises `KeyError`, and so does assigning it a new one. A band that never had a row and is still alive gets one at the fill value: what the dense array held.
- **Disease** (`dz_imm`, `dz_last`):
  - rows are assigned in `ensure`, and in `yearly` and `combine` for a living band without one;
  - a row is released in `bands.end_band` and in `consolidate_groups`, the two places a band ends. Before release, its last-circulation years are folded into `w.dz_gone_last`;
  - `last_any`, the maximum over living rows and `dz_gone_last`, replaces `dz_last.max(axis=0)` in `_free_slot` and `_retire`. `_retire` also resets `dz_gone_last[d]`.
- **Partners** (`partner_of`, `partner_since`, `partner_gave`):
  - rows are assigned in `trade.ensure` and released at the end of `_unlink_all`, which is called only as a band ends, after its partnerships are cleared;
  - `partners`, `_unlink` and `gift_totals` treat a band without a row as having no links. That is what its cleared dense row held.
- **Saves:** the slot maps, the rows in use and `dz_gone_last` are saved and digested. Saves with a row for every id are converted on loading:
  - living bands keep their rows;
  - for disease, the other ids are marked ended and their last-circulation years are folded in;
  - partner rows are widened to `PARTNERS_CAP` where an older save held fewer links.

The digest's value changes, because the representation changed.

## Evidence

- **Planet 3 (local):** the same 20 years from the planet-3 save at year 9,910, with the compact log in shadow mode. The hash of every new event matches main (`f9eb76a6d77265d1`), and no read of an ended row was raised.
- **Planet 4 (GitHub):** 40 years from the planet-4 pilot's stage-2 checkpoint, a dense save converted on loading.

  | Run | Event hash | Population | Random-stream hash | In use while stepping | Seconds per year |
  |---|---|---|---|---|---|
  | main (old), run 44924108669 | `4f8cf50f99ce8211` | 2,149,608 | `26b26f25f4314fba` | not measured | to 18.3 |
  | this branch, shadow mode, run 44924111194 | `4f8cf50f99ce8211` | 2,149,608 | `26b26f25f4314fba` | not measured | 18.7–23.6 (shadow writes every row twice) |
  | this branch, no shadow, run 44925948088 | (compact log: 97,592 events, not 542,332) | 2,149,608 | `26b26f25f4314fba` | 3.3–3.4 GB | 15.3–18.7 |
  | main (old), run 44925960124 | `5a7fee6954a2b3b2` | 2,149,608 | `26b26f25f4314fba` | 5.8–5.9 GB | 20.2–25.0 |

  The peak at loading stays at 10.4 GB here, because this checkpoint holds dense rows and is converted after loading. Saves made by this branch hold only rows in use.

  **A pre-existing question for you:** the two runs of the old code on main gave different event hashes (`4f8cf50f…` and `5a7fee69…`), with the same population and random streams. Locally, the same code gives identical events in repeated runs and under different `PYTHONHASHSEED` values (planet-3 save, 20 years, 65,335 events). My guess is GitHub runners with different processors summing floats differently in the last bit. That would put a number in an event's data or note out by one rounding step without changing the history. Is that the cause, and does exact replay need to hold across machines?
- **Tests:** `tests/test_rows.py` checks:
  - slot reuse and refusal for ended bands;
  - ended bands' last years counting on;
  - save round trip;
  - loading an older dense save.

  The suite's older-save tests were rewritten to build real older-format saves.

## Please check

1. **Ended rows.** Can any path read or write an ended band's disease or partner row?
   - It would raise, and a raise there would stop a gate run.
   - Think of captives in `conflict._fight`, `demography` marriages between bands, the observatory and the server, and the gate's census.
   - Is there any path where the dense array's value of an ended row mattered?
2. **The aggregate.** Is `last_any` exactly the old `dz_last.max(axis=0)` in every case? Think of retirement, `-2` rows from older saves, and bands that ended before a disease existed.
3. **Older saves.** Is the conversion exact for each kind of older save (none, four-link, no gift totals, `dz_seen`)? Is marking ids at or above `next_band` as never assigned right?
4. **Memory.** What still grows with band ids issued? For example `goods`, `tech`, `tech_record`, `skill`, `neutral`, `customs` and `crop_store` remain dense, at about 0.9 KB per id.

Same format as before (AGENTS.md).
