# Review request 035: comprehensive pre-gate review, part 2 of 4 — state and per-band arrays

**From:** Claude, 21 November 2026.

**Scope:** every piece of per-band, per-cell and per-polity state added or changed in M4a. This includes (not a complete list):
- technology: `tech`, `tech_record`, `tech_scribes`, `tech_prev_*`, `tech_import`, `tech_writing_log`;
- trade: goods, partners, partner gifts, `goods_reached`, `treasury`, `trade_links`;
- land: `land_*`, game, forest, fertility, salt;
- disease: `dz_imm`, `dz_active`, `dz_last`, `dz_since`, `dz_log`;
- groups' pregnancies;
- places: `w.places` and its layers.

## Please check, for each

1. **Growth** when band ids pass the array's size.
2. **Inheritance at a split** (`new_band` with a parent) and at fission.
3. **Combining at a merge,** a consolidation, a migration and a capture. Is anything counted twice, or lost?
4. **Clearing at a band's end:** stale values that a reused or later read could pick up.
5. **Saves:** round-trip exactly; older saves load with sensible derived values.
6. **The digest:** everything that changes the history is in it, and nothing that does not.

Rank the risks, and say which should block the gate. Same format as before (AGENTS.md).
