# Review request 028: diseases from animals (M4 specification section 6), and the review-027 fix

**From:** Claude, 20 November 2026.

**Range:** `main` from the merge of `wip-review027` to the merge of `wip-disease`. Read the build notes sections "Diseases from domestic animals: literature check", "Diseases: comparing the two literature checks" and "Diseases from animals, as built". Ben's decisions (20 November 2026) were:
- the full model now;
- flight and isolation now, blame with M4b;
- hunger's effect per disease;
- reservoirs, with few epidemics before herds;
- k from 3,000 to 500,000;
- test herd diseases in a world that has herds.

## Please check

1. **`origins/sim/disease.py`:**
   - emergence (herd pressure × time since domestication; wild);
   - reservoirs (`_respill`: herd diseases where people herd the host, wild ones in the region of origin);
   - persistence by k;
   - spread along contacts;
   - immunity by age (`_age_and_wane`);
   - deaths by age, hunger and crisis (`_epidemics`, `_kill`, individuals and groups);
   - the responses.
2. **State:**
   - `dz_imm` grows with bands, is inherited at a split (`ensure`) and combined at joining (`combine` via `bands.carry`);
   - `dz_active`;
   - `w.diseases` in saves and the digest;
   - the new custom's width in older saves (`customs.widen`);
   - the new random stream, appended.
3. **The knock-out:** with `DISEASE` False, M1's outbreaks run exactly as before.
4. **Records:**
   - `new_disease` and `outbreak` events and their cause chains;
   - deaths' `death_hazard`;
   - the G3 record's disease fields;
   - G1's exposure counts.
5. **Ledgers:** people killed by disease in groups (`_kill` edits `G.F`/`G.M` directly), counts and `deaths_by_cause`.
6. **The review-027 fix** (`land.move_crop_loss`): examples compared by their own attributed loss.
7. **The trials and their reading** (planet 3 only; the herd trial is still running on GitHub, runs 44651931880 and 44627692405).

Same format as before (AGENTS.md).
