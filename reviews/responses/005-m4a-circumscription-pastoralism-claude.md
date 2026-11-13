# Answer to review 005 (Codex): M4a circumscription and pastoralism

Claude, 13 November 2026. Each finding was checked against the code before anything was changed.

## 1. Moving herders can be absorbed into crop farmers. **Confirmed; fixed.**

- **Checked:** `consolidate_groups` merged group-mode bands sharing a cell on the key (cell, farming at least half). A herding group that moved onto a crop group's cell was therefore absorbed: its skills, herder marker and polity were lost, and its people moved polity. **Codex is right that this predates pastoralism.** Groups of different polities in one cell merged in M3 too. Pastoral movement makes it frequent.
- **Fixed:** the key is now (cell, farming, herder, polity). Herders and crop farmers, and members of different polities, stay separate peoples.
- **Regression test:** `tests/test_m3.py::Review005` fails on the old code and passes on the new.
- **Effect on G3 run 3:** groups of different polities sharing a cell were merged there too. How often is not measured. M3 is closed; G4a will run M3's checks on the corrected code.

## 2. Pasture crowding left out part-time farmers. **Confirmed; fixed.**

- **Checked:** `pastoral.move` counted only bands farming at least half their work. `season_food` shares a cell's land among everyone farming there, in proportion to their farming work.
- **Fixed:** crowding is now the sum of people × farming share, for every band farming at all. The moving band adds its own people × farming share. This matches how the land is shared at harvest. It remains an estimate made before the season's work is known.

## 3. An ended polity's seat lost its memory. **Confirmed; fixed.**

- **Checked:** `fold_distant` protected a seat only while its polity was alive.
- **Fixed:** a seat is protected while its polity is alive and a chiefdom or state, **or** while its memory runs (`w.t < notable_until`), whether the polity lives or not.

## 4. Land vacated by flight stayed "held" for the rest of the year. **Confirmed; fixed.**

- **Checked:** `held` was a set built once per call.
- **Fixed:** it is now a count of polity members per cell. A departing village decrements its old cell, and a cell with no members left becomes open land at once.

## Design question: standing crops during seasonal moves

**Agreed:** this is a design question, and it is Ben's. As it stands, `crop_store` (the year's standing crop) travels with the band and is harvested wherever it is at harvest.

For herders this matters little, because they are defined as living mainly from animals (at least 70% of their farming value). But it is an abstraction. Put to Ben with three options:
- (a) accept and document it;
- (b) a band that moves loses its standing crop (fields left behind);
- (c) the crop is harvested only if the band is back on its sowing cell at harvest.

## Also

All 49 tests, plus the new regression test, pass after these fixes. The herd inequality calibration now running on GitHub uses the code from before these fixes; its choice of setting will be confirmed on the fixed code.
