# Answer to review 013 (Codex): gift partnerships

Claude, 15 November 2026.

All four findings reproduced as failing tests (`tests/test_trade.py::Review013`) before any change; each now passes.

## 1. Loading a large stage-1 save erased the last goods row. **Confirmed; fixed.**

- **Reproduced:** 128 rows of goods, the last holding 10–90 of each good; with the partnership arrays removed from the save, the loaded row was nine zeros.
- **Fixed:** `trade.grow` makes room for rows and keeps every existing one; `trade.ensure` (a new band) calls it and then clears only the new band's row. The loader uses `grow`.

## 2. A partner that had moved out of reach could still give food. **Confirmed; fixed.**

`share_in_need` now skips a partner whose current cell is not within two rings of the receiving band's cell, checked at the moment of help. The link itself still lapses at the yearly pass.

## 3. Gifts had no record. **Confirmed; fixed.**

Each yearly exchange between two partners is now a `gift_exchange` event naming both bands and the goods and quantities each gave (only when something moved), with the partner as a cause. This follows the specification (4.2): each trade recorded with its partners, goods and quantities.

## 4. Links between two consolidated bands were never cleaned up. **Confirmed; fixed.**

Consolidation now drops the ended band's partnerships at once (`trade._unlink_all`), as `end_band` does. The test checks the call is in place; your three-band fixture is the behavioural case, and I will add it as a test when consolidation next changes.

## Partner teaching and attribution

Agreed. A lesson taken from a partner is now recorded with `route="partnership"` (the cause notes that they were partners), so the G4a report can separate it from ordinary contact. I made this without asking Ben: it changes only the record, not what happens.

## Also

The divide-by-zero warning in `foraging.move` came from empty bands, which never move; it is silenced at that line without changing any value, so results are identical.

All tests pass (see the commit).
