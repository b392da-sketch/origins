# Review request 042: lazy loading and compact columns

**From:** Claude, 26 November 2026. **Branch:** `wip-lazyload` (on main `2ed0ee0`). **Not yet merged.** This is step 2 of Ben's plan of 26 November: find what fills memory, and fix the largest part exactly.

## What pilot 3 showed

Pilot 3 (gate run 45794080188) reported its stage-1 save, at year 5,733 on planet 4:
- **The compact log's tables, about 1.4 GB in memory:**

  | Table | Size |
  |---|---|
  | `minor_partnership_lapsed` | 400 MB |
  | `minor_partnership_formed` | 303 MB |
  | `minor_helped_by_partners` | 268 MB |
  | `minor_gift_exchange` | 217 MB |
  | `minor_land_move` | 212 MB |

  These are the largest arrays.
- **The next largest:** `tech_record` and `tech` (226 MB each), `goods` (151 MB), `neutral` (101 MB), `b_trail` (79 MB) and `skill` (75 MB).
- **Metadata is small:** bands 26 MB, languages 18 MB.

The loader also decoded every array before building any of the world.

## What changed

1. **Arrays read when used.** `persist.from_file` keeps the unpacked npz open while it builds the world. A `_LazyArrays` mapping reads each array only when its part asks for it, and keeps nothing itself. `_prefixed` reads only the arrays of one prefix. `_drop` now just hides names, since nothing is held.
2. **Compact columns for the compact log.** `minorlog.Table` keeps whole-number columns as int32 and amounts as float64. The whole-number columns are ids, ticks, cells, reasons, counts, indexes, names, `after` and `order`. The amounts are help, closeness, food per person-day and gifts.
   - Values beyond int32 raise `OverflowError` rather than wrapping.
   - `row(i)` rebuilds the float64 row that `as_event` reads; `col(name)` serves the feeds.
   - Saves hold `minor_<kind>_i` and `minor_<kind>_f`. Saves with one float64 array per kind (22–26 November) still load (`Table.from_wide`).

## Evidence

- **Planet-3 save at year 9,910:**

  | Loading peak | |
  |---|---|
  | main | 1.99 GB |
  | this branch | 1.57 GB |

  The digest is unchanged on loading (`d6db1c86f6441e307834`). The trace now shows a rising floor, not a spike after the arrays.
- **Shadow mode, 20 years from that save:** the all-event hash still matches the old code (`f9eb76a6d77265d1`).
- **Tests:** `tests/test_minorlog.py::CompactColumns` checks:
  - exact read-back, and older wide saves;
  - the int32 limit;
  - the save round trip, through the existing tests.
- **The full suite** is running.

## Please check

1. **`_LazyArrays`.** Does any consumer in `from_file`, `disease.load_rows` or `trade.partner_load` rely on dict behaviour it lacks: identity of a read array, mutation of a stored array, `len`, or `values`? Does reading an array twice anywhere give two copies that are both kept? Is the temporary file closed on every path, including exceptions?
2. **Exactness of the compact columns.** Can any whole-number column exceed int32 at gate scale, or hold a non-integer? Think of `after` and `order` across a 30,000-year history, `givers_from`, and land event ids. Is the old wide format converted exactly?
3. **What remains at planet-4 scale.** Pilot 3's stage-2 load trace will give the measured breakdown. From the code, what is the next largest part after these two?

Same format as before (AGENTS.md).
