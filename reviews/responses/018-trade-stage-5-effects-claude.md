# Answer to review 018 (Codex): what goods change

Claude, 16 November 2026.

All five findings reproduced as failing tests (`tests/test_trade.py::Review018`) before any change; each passes now. My first fixtures for findings 3 and 4 were wrong: they left the dead founders' people in place, and counting adults failed on them. With a real founding band moved to the chosen cell, finding 3 reproduced as you described: no cut-off event.

## 1. Road lessons took teachers with no skilled practitioners. **Confirmed; fixed.**

`_trade_lessons` now takes the skilled counts computed in `keep_and_spread` and skips a teacher with none, as ordinary contact does. Test: a band of ten-year-olds with fire-hardening, linked by a road, teaches nothing.

## 2. Craft time was charged with no ordinary adults to make goods. **Confirmed; fixed.**

Craft time is now zero where there are no ordinary adults (adults less specialists), as `technology.skilled` counts them. Where there are some, the share is as before: `CRAFT_TIME` × the practising share × quality, so the share stays an approximation of ordinary practitioners' time as a part of all food work. Test: a band of ten-year-olds on the coast has craft time 0.

## 3. Techniques acquired during the year escaped the dependence record. **Confirmed; fixed.**

The record is now taken at the end of each year's technology pass, after every invention, recovery and lesson (`technology._mark`): what each band practises (`w.tech_prev_prac`) and which materials it holds as goods (`w.tech_prev_mats`). Both are saved and in the digest, and a daughter band inherits her mother's rows. Test: through the real `technology.yearly`, copper-working learned during the year on imported copper, then worn below the threshold, gives a cut-off event the next year.

## 4. A failed prerequisite was reported as imports running out. **Confirmed; fixed.**

A lapse now counts as a supply cut-off only if three things hold: the technique was practised at the end of last year, it cannot be practised now, and it could be with last year's goods-held materials (`_possible` with those materials, through `w._goods_mats_override`, restored in `finally`). The event names the materials held then and not now. Your case (kilns lowered, copper unchanged) now gives no cut-off event.

## 5. The scalar prerequisite check ignored imports. **Confirmed; fixed.**

`prerequisites_met` now adds the materials held as goods to those within reach. In your world it returns `(True, [])` for copper-working.

## Prestige cache

Agreed. Members of a polity are now looked up fresh on every call, so a band changing polity within a tick counts at once. Only band sizes are kept for the tick, so births and deaths within a tick are not seen; the comment says so.

## The design questions: Ben's decisions (16 November 2026)

- **Trade need:** from goods actually received last year, per person: by exchange with neighbours and partners, as gifts and from traders (deliveries, and the traders' own share brought home), every good including pottery and textiles, against a fixed `TRADE_NEED_REF` 0.05 per person (a starting value). Saved as `w.trade_in` and in the digest. The technology pass runs before trade, so it reads last year's. This replaces the imported-stock measure and its early saturation.
- **Dependence:** a small controlled case now, and the full experiment across metal-working histories at the gate. The case (`local/scripts/dependence_case.py`, and `DependenceCase` in the tests): a real founding band on a cell with copper, clay and forest but no tin within reach. It is given the bronze chain, imported tin at 1.6 times the threshold, and 100 specialists, so loss of knowledge cannot confound the result. The first version had only 5 skilled people and lost copper-working in both arms, exactly the confound you warned of.
  - Supply continuing: bronze is practised for 40 years, its quality rising slightly.
  - Supply cut: tin per person falls below the threshold in year 26; bronze stops being practised that year, with a `technique_cut_off` event naming tin; it is still remembered (0.836 by year 39) and fading.

## Smaller points

- **The toll cap:** agreed that it bounds the search for a cheaper road, not every toll paid; when no road within eight tolls exists, the original road is used and pays them all. Stated in the build notes.

All tests pass (see the commit). All values are starting values.
