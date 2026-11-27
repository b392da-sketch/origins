# Review 043 · Band rows for every per-band array

**Codex, 27 November 2026.** Reviewed `7093fe8..4ee9b42` on `wip-bandrows`. The slot conversion reduces the data held for ended bands. I found two ways an older checkpoint can fail to load, two ways it can lose history during migration, and two reads of released rows.

## Findings

### 1. Schema-5 saves made before technology practice is recorded fail to load

- **Where:** `origins/persist.py`, `_load_band_rows` and the `tech_prev_wood` fallback in `from_file` (lines 127–133 and 533–539).
- **What is wrong:** The schema-5 writer represents absent `tech_prev_prac` as a boolean array of shape `(0, 0)`. The converter recognises empty placeholders only up to one dimension, so it creates sparse practice rows with zero columns. The wood fallback then indexes those columns using `WOOD_TECHS`.
- **Why it matters:** An ordinary early checkpoint cannot be resumed after the upgrade. The test labelled “schema 5” in `BandRows` builds its input from a 60-year schema-6 save and leaves the schema number at 6. It never exercises the old writer's placeholder.
- **How sure you are:** Certain.
- **How to see it:** Save a fresh `World.new(1, 1, generate(1))` with the writer on `7093fe8`. That revision reads it. The branch raises `IndexError: index 4 is out of bounds for axis 1 with size 0` on the same bytes.

### 2. Legacy saves with no customs array fail to load

- **Where:** `origins/persist.py`, `_load_band_rows` and its call to `_customs.widen` (lines 111–129 and 518–519). See also `origins/sim/customs.py`, `widen`.
- **What is wrong:** The conversion clears every band-row attribute before looking up its saved array. The legacy path leaves `w.customs` as `None` when customs are absent. Previously the loader kept the world constructor's defaults for absent arrays.
- **Why it matters:** The branch still accepts schema 1 at the schema check, yet an M0 save can fail before it restores people and languages.
- **How sure you are:** Certain.
- **How to see it:** I used the schema-1 save made by the historical writer at `5d04b77` from review 041, with only its planet fingerprint adjusted for the current generated planet. Main loads it at tick 4 with an 11-column customs table. The branch fails in `customs.widen` with `AttributeError: 'NoneType' object has no attribute 'shape'`.

### 3. Dense migration discards saved scribal history

- **Where:** `origins/persist.py`, `_load_band_rows` and `from_file` (lines 133–136 and 459–461). The fallback value comes from `origins/sim/technology.py`, `_scribes`.
- **What is wrong:** The converter loads `tech_scribes` and drops the source key. The later old-save check interprets that dropped key as evidence that the save predates scribes and unregisters the rows it just loaded.
- **Why it matters:** The next read reconstructs history from current specialists at eligible seats, with zero elsewhere. The saved average affects scribal capacity and written records. Resuming a dense checkpoint can therefore diverge even though it opens successfully.
- **How sure you are:** Certain.
- **How to see it:** On `7093fe8`, step a planet-1 world 15 years so its practice arrays are present, set one living band's scribal average to `7.25`, and save with the native schema-5 writer. Reload it and read the value through `technology._scribes`. Main returns `7.25`. The branch returns `0.0` for the same band.

### 4. Reinitialising a legacy technology table also erases valid written records

- **Where:** `origins/persist.py`, `from_file` (lines 453–458), and `origins/sim/technology.py`, `init` (lines 151–154).
- **What is wrong:** If the legacy `tech` table has an incompatible width, the loader runs `_tech.init`, which replaces both the technology table and the independent `tech_record` and `tech_scribes` tables. The replaced records and scribes remain registered with the slot map.
- **Why it matters:** Main reinitialises the incompatible table and preserves compatible records. The branch resets the records to zero, and the orphaned arrays still take space and participate in slot growth and clearing.
- **How sure you are:** Certain for a dense input with independently compatible records. I exercised the fallback with a modified fixture.
- **How to see it:** In the populated schema-5 fixture from finding 3, also set `tech_record[band_id, 0] = 0.5` before saving. Replace only the saved `tech` table with a one-column table in the archive. Main restores the recorded `0.5`. The branch returns `0.0` and has two arrays in `w.band_rows.arrays` that no world attribute references.

### 5. A living polity can lose its ended seat's rows while it still names that seat

- **Where:** `origins/sim/bands.py`, `release_rows`, `_seat_of_living_polity` and `sweep_rows` (lines 256–292). Compare `origins/persist.py`, `_load_band_rows` (lines 99–108), and `origins/sim/conflict.py`, `cultural_distances`.
- **What is wrong:** Release and sweep find the polity through the seat's `polity_of` entry. If that entry is unset or belongs to another polity, they release the slot even if a living polity still names the band as its seat. The legacy loader makes the retention decision from the polity records, so it can preserve a seat that the next sweep drops.
- **Why it matters:** The retention rule given in the request is based on the living polity's seat. Losing customs or specialists before it moves can break a reader of that seat, including conflict's cultural-distance calculation. I verified the mismatched state directly. Its frequency in an unmodified run is unknown.
- **How sure you are:** Certain for the state named in the request.
- **How to see it:** Put a living member in polity 0, give that polity a second band as its seat, set the seat's `polity_of` to `-1`, and end the seat with `bands.end_band`. The polity stays alive and still names the same seat. Reading the seat's customs succeeds on main and raises `KeyError` on the branch. Saving that state on main and importing it on the branch preserves the row until the first `sweep_rows` call, when the same failure occurs.

### 6. The observatory's history links can open an ended band's page and fail

- **Where:** `origins/server.py`, `band_detail` (lines 543–568), and `observatory/index.html`, the band link in the event detail (line 570).
- **What is wrong:** The event can still link to its band after the band ends. The band endpoint resolves its historical record and then reads its released customs row. The farming panel also reads released rows.
- **Why it matters:** Readers can see an end or merge in the history, then lose access to the linked band's page. The failure affects the band detail endpoint. Explaining the end event itself still works.
- **How sure you are:** Certain.
- **How to see it:** Create an empty daughter band, call `bands.end_band`, then open `/api/band?id=<daughter id>` or call `server.band_detail` for that ID. Main returns `alive: false`. The branch raises `KeyError` on the first customs lookup. I reproduced it after packing and after a schema-6 save and reload.

## What still grows at gate scale

This is a ranking of the reported hot paths by what drives their cost. The reported profile has no per-function times, so the order within a run depends on settlement density, churn and the number of polity seats.

1. **Repeated population scans in fission, merging and consolidation.** A move through `bands.carry` can call `disease.combine`, which asks `World.band_size` for the destination. Even for a single band, that scans the live individual index and active group rows. If transfers grow with the number of living bands, the work grows as transfers × (individuals + group rows). Individual membership lookups for splits and mergers also scan the live individual index. Consolidation's cell/kind dictionary itself is a single pass. The cost of moving people is the part to measure.
2. **Neighbour pairs in gift partnerships and conflict.** Partnership formation and switching visit nearby candidate bands per eligible band. The formation pass sorts candidates and draws for the candidate list before applying the local cap. Two nearby cells with `a` and `b` bands can contribute `a × b` candidate visits. Conflict visits neighbours from each member of a side, then builds a targets × members matrix for multi-member sides. The cost grows with density and polity size even on a fixed planet. Counting visited pairs and matrix entries would distinguish those costs from band growth.
3. **Polity membership and traders.** Polity secession can rescan all members per candidate breakaway and walk chains of rule. Conquest can call `polity.members_of`, which scans all living bands. Flight scans the full `polity_via` array per departure and prestige queries with goods scan the issued-ID prefix of `polity_of` per call. Traders compare each origin with all active seats before shortlisting 12, so the comparison grows with trading origins × seats. Route searches then depend on terrain and the tolls encountered. Which of these dominates depends on how common large polities, funded seats and flights become.
4. **Costs tied to issued IDs and recorded history.** `SlotMap.held` scans the whole slot array even though it returns only held IDs. The goods check does this twice per tick through `check_begin` and `check_end`: at a capacity of about 4.2 million slots that is about 8.4 million slot entries per tick before gathering any goods. Live-index rebuilds still initialise an issued-ID-sized table, and `World.band_sizes` in observatory and trader code still builds historical-length vectors. The 1.4 GB compact log and 1.1 GB events reported at year 6,353 are a separate, growing checkpoint cost.

The matching event hashes at years 9,910 on planet 3 and 5,765 on planet 4 support the comparisons over those windows. The 4.10 GB load at year 6,348 shows that the branch can open the checkpoint in the 8 GB workspace. The 11.27 GB load is from a different runner, and its 1,527 MiB save is from year 6,698. There is no paired event-hash run at 6,348. At the reported 39.9 s/year, the remaining 4,895 years from 6,353 to the pilot's year-11,248 target would take about 54 hours of simulation if the rate held. All ten 4.5-hour stages together budget 45 hours, including the stages already spent getting there.

## Checked and sound

- Native schema-6 replay preserved a deliberately unsorted free list `[6, 3, 5]`, reused the same slots in reverse order, restored the NaN and `-1` farming fills on reuse, and produced the same digest after reuse. The branch test for a correctly affiliated ended seat also passed through save, reload and sweep.
- Founders get the residence default at creation, and daughters inherit the parent row. The reuse path fills from the array defaults before inheritance. I also checked that widening a legacy customs row drops the narrow registration, that a fresh forage row starts at `P.FORAGE_RATE`, and that refreshing the practised-quality cache reuses its registered array.
- Interventions alter cell arrays. Capture and battle deaths move or remove people without releasing band rows during conflict. Conquest marks a defeated polity ended before transferring its members. The direct G2–G4 gate reads use living bands or living ID sets. G4's census checks previous panellists by ID membership and unregisters the temporary receipts array on its normal return path.
- The legacy conversion restored explicitly empty land accounts to their expected zero or `-1` fills. In a settled-goods fixture with a released band, the ID-ordered goods reduction matched the dense sum exactly. The end path had already charged the departed goods to the ledger.
