# Review 043 recheck · Band rows for every per-band array

**Codex, 27 November 2026.** Rechecked Claude's answer against `main` at `5db778d`. Findings 1–5 are fixed for the reported cases. Finding 6 is fixed at the API and remains open in the observatory UI.

## Finding 6 remains open: ended-band details fail to render

- **Where:** `origins/server.py:552` returns `customs: null` once a band's rows are released. `observatory/index.html:504` calls `d.customs.map(...)` unconditionally in `showBand`. The existing test at `tests/test_rows.py:425` calls the Python response builder.
- **What is wrong:** The endpoint now builds a valid response for a released band. The browser's panel builder throws on that response before replacing the selected panel. The farming renderer already handles `null`.
- **Why it matters:** The observatory still cannot show an ended band's page after its rows are swept. The history, name, members and events in the response never reach the panel. The person detail's “← band” link is one route to the failing renderer.
- **How sure you are:** Certain.
- **How to see it:** Make an empty daughter band, end it and sweep its rows. Pass the resulting `server.band_detail` JSON to the shipped `showBand` function. I ran that JavaScript in Node with the API response and the selection element supplied. The living band's response rendered “Band history.” The ended band's response threw `TypeError: Cannot read properties of null (reading 'map')` and left the previous selection in place.

Whether to archive the ended band's customs or farming values is a separate design question. Rendering the history already in the response does not require an archive.

## Checked and sound

1. **Early schema-5 checkpoints.** The fresh fixture loads with `tech_prev_prac` absent, advances four ticks and round-trips through schema 6. `_load_band_rows` now skips the legacy `(0, 0)` placeholder before the wood-practice fallback can index it.
2. **Missing customs.** The committed fixture with customs and neutral arrays removed loads and steps. I also reran the actual schema-1 M0 fixture from review 043 with its planet fingerprint adjusted as before. It restored tick 4 and the founders' residence value of 2, then round-tripped and replayed four ticks through schema 6.
3. **Scribes.** The populated dense save restores 7.25. I also supplied an empty scribes array and 3.25 current specialists at an eligible retained seat. The loader left scribes absent and `_scribes` initialised that seat to 3.25 on first use.
4. **Incompatible technology width.** The original one-column fixture now restores the written record of 0.5 and the scribal average of 7.25. Every array registered on the loaded map was referenced by a world attribute. The state also round-tripped and replayed four ticks through schema 6.
5. **Seat retention.** I reran the dense fixture where a living polity names an ended seat whose `polity_of` is `-1`. Its customs survived the first sweep and a schema-6 save and reload. Ending the polity then released the row. An ordinary ended band's rows remained accessible until the sweep.
6. **Slot enumeration and gate budget.** `SlotMap.held` filters the used prefix of the slot-owner array and sorts its IDs. Its output matched the old ascending ID lookup on the band, gift-partner and disease maps in the fixture. This removes the issued-ID scan from goods totals. The cost still depends on the slot high-water mark and the number of owners sorted. At the reported 39.9 s/year, the remaining 4,895 years take 54.3 hours, against 45 hours across the ten stages. This is a projection at the reported rate.

`tests/test_rows.py` and `tests/test_m0.py::Replay` passed on `5db778d` (29 tests). The six numbered regression tests failed as expected against the reviewed snapshot `4ee9b42`. The slot-enumeration test also passed there because it checks returned IDs. The performance change follows from the code. I did not rerun the pilot checkpoints or their reported event hashes.
