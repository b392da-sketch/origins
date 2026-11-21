# The compact log: partnerships, help, gifts and land moves (proposal for Ben)

Claude, 22 November 2026. **Status: draft for Ben's decision.** Ben approved the idea on 21 November 2026. This document gives the details he asked to see first. All numbers are measurements from the G4a planet-4 pilot (checkpoint at year 5,765), not targets.

## Why

At year 5,765 the pilot history held 16.9 million events. Five kinds made 15 million of them:

| Kind | Events | As saved (JSON) |
|---|---|---|
| `helped_by_partners` | 3.76 M | 1,111 MiB |
| `partnership_formed` | 3.24 M | 974 MiB |
| `partnership_lapsed` | 3.21 M | 1,008 MiB |
| `land_move` | 2.44 M | 772 MiB |
| `gift_exchange` (first gifts of a partnership) | 2.33 M | 725 MiB |

Each is a full event: a dictionary with a written note, its causes and its data. They make most of the 5.4 GB event file in each checkpoint, most of the 3–6 minutes each save and restore takes, and much of the 10.4 GB peak at restore, on a 16 GB machine.

**No other event cites any of the five as its cause** (checked in the code). Each is the end of a chain, not a link inside one, so moving them breaks no chain.

## What changes

The five kinds leave the event list for **one table each**:
- **Kept whole.** Every row is kept, nothing thinned or sampled, unlike the gift log and the other gate logs.
- **Stored like other arrays.** Each table is held in a NumPy-backed array like the disease log (`RowLog`). It is saved in `arrays.npz` and included in the digest.

| Table | Columns (one row per happening) |
|---|---|
| help | tick, band, cell, food received, the givers (a separate list of band ids, with each row's start and count) |
| formed | tick, band, partner, cell, reason (new link within reach, or a swap for a better-supplied partner), closeness of speech |
| lapsed | tick, band, partner, cell, reason (out of reach, a band ended or joined another, with which, swapped for a better partner), years together, each side's gift totals per gift good (shell, gold) |
| first gifts | tick, band, partner, cell, each side's gifts per gift good |
| land moves | tick, band, cell, food per person-day where it was, next door, and with natural regrowth; the land events it cites (at most two: game, forest) |

**The notes are written when asked for, not stored.** Today each event stores its sentence, such as "X and Y lived within reach of each other (64% closeness of speech) and began to exchange gifts". The table stores the numbers and a reason code, and `explain.py` writes the same sentence when the record is read, using the bands' names. Band names are kept in the band record, so the sentence is the same.

**Causes resolve as before.** A row's causes are its bands, and for land moves its land events. `explain.resolvable` gains one reference kind, `{"log": [table, row]}`. The observatory's band history and the cause-chain view show rows from these tables beside events, in time order.

**Counts stay.** `w.counts` keeps a count of each kind. The gate's check 11 samples its chains for help, gift exchange and land moves from the tables, and the G4 record's land events count from them.

**Expected size** (estimated from the columns): about 0.6 GB in memory and in the save, against 4.6 GB of JSON now. The checkpoint's event file would shrink to about 2.3 million events at this point of the history.

## What does not change

- **No simulated outcome changes.** The same things happen, decided by the same draws. A digest test checks this against the current code, with the tables in place of the five event kinds.
- **The record's content.** Every happening of these five kinds is still recorded, with what moved and why. Only the form of the record changes.
- **Older saves** keep their events as events. The tables start empty, and explain reads both.

## For Ben to decide

1. The five kinds above, all moved, or only the four partner kinds (keeping land moves as events: 2.4 M, the smallest saving).
2. Whether the first gifts of a partnership should still be an event (they are 2.3 M; today the yearly gifts after the first are already in the thinned gift log).

Codex reviews the change before it goes into a gate run.
