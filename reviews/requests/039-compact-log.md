# Review request 039: the compact log

**From:** Claude, 22 November 2026. **Branch:** `wip-compactlog` (on main). **Not yet merged.** Ben's decision: `docs/COMPACT_LOG_PROPOSAL.md` (all five kinds, 22 November 2026).

## What changed

Five kinds of happening are now rows of numbers in `origins/sim/minorlog.py`, not events in `w.events`:
- `helped_by_partners`;
- `partnership_formed` and `partnership_lapsed`;
- `gift_exchange` (a partnership's first gifts);
- `land_move`.

In the planet-4 pilot they were 15 of 16.9 million events by year 5,765.

- **Recording:** `trade.py` and `foraging._land_move` call `minorlog.helped`, `formed`, `lapsed`, `first_gifts` and `land_move` in place of `w.event`. Every row is kept, nothing thinned. `w.counts` counts each kind. `_unlink_all` takes `joined=<band id>` in place of a `why` string.
- **Reading:** `minorlog.as_event(w, kind, row)` rebuilds the event the old code wrote: kind, t, cell, band, data and causes, with its note written from the numbers. References are `{"log": [kind, row]}`. `explain.describe` and `explain.resolvable` accept them. An unknown kind or an out-of-range row does not resolve.
- **Saving:** the tables are saved in `arrays.npz` (`minor_*`) and included in `persist.digest`. A fresh world and a reloaded one carry the same keys.
- **Gate:** G4's check-11 samples draw from events and rows together, without listing millions of references. `land_events["land_move"]` counts rows.
- **Observatory:** band history merges rows with events. A row's reference is `log:<kind>:<row>`.
- **Shadow mode (checking only):** with `minorlog.SHADOW = True`, each row is also written as the full old event, from `as_event`, and counts and arrays behave as before.

## Evidence

From the planet-3 save at year 9,910, 20 years:

| Code | Digest | Hash of every new event |
|---|---|---|
| main `c4e592a` (old) | `a7fb50fc52bd7b03adae` | `f9eb76a6d77265d1` |
| `wip-compactlog`, shadow mode | `a7fb50fc52bd7b03adae` | `f9eb76a6d77265d1` |

This covers 51,814 happenings of the five kinds. `tests/test_minorlog.py` checks:
- the rows and counts;
- resolution, and that bad references fail;
- the save round trip and the digest;
- that shadow mode leaves the history unchanged;
- the growing givers list (a growth bug found and fixed while building).

## Please check

1. **Exactness.** Is every row read back as exactly the event the old code wrote, in all reason branches? Formed: near or swap. Lapsed: out of reach, ended, joined, or swap. Check data key order and the rounding of gifts and help. Is there any path where the old event's id was used and the row's index now stands in a different place? Known cases are `b.last_move` ("land move N") and nothing else.
2. **Anything still reading these kinds from `w.events`:** gates, reports, the server, observatory views, tests, places, explain caches.
3. **Older saves:** their existing events of these kinds stay events. Do reports and views count both?
4. **Size at gate scale:** memory and save size of the tables against the events they replace, and anything that still grows per happening.

Same format as before (AGENTS.md).
