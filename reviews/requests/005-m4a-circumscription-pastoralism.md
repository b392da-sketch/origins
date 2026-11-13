# Review request 005: M4a steps 1–2 (circumscription and pastoralism)

**From:** Claude, 13 November 2026.

**Range:**
- the merges of `seat-memory` and `event-store-disk` into `main`;
- the commits "M4a step 1: circumscription" and "M4a step 2: pastoralism".

The background is in `docs/M4_SPECIFICATION_v1.md` (section 2, items 1 and 3; Ben's decisions 4 and 5) and `docs/M4_BUILD_NOTES.md`.

## Please check

1. **`polity._flight`** (circumscription):
   - Can a village flee to land that another polity holds, or to a cell it is already in?
   - Is the rewiring of settlements that answered through the fleeing village correct (`polity_via` → seat)? Can it create a loop or leave a stale chain?
   - Is anything from the start of the year used after it has changed (the error class behind the loop in G3 run 3)?
   - Does the event's cause text match what the code tested?
2. **`sim/pastoral.py`** (pastoralism):
   - Does pasture per person compare like with like, here and in neighbouring cells? (Here, the band is already counted; there, it is added.)
   - Does it draw no random numbers, as it claims, and is its order deterministic?
   - Does moving a herding band interact badly with farming's fields and harvest (`crop_store`, `season_food`), with `still_years`, with polity membership and load, or with folding into groups?
3. **Saves and replay:** `herder_since` and `first_herders` are saved, and older saves load without them. Does a save round-trip exactly (`persist.digest`) mid-history with herders present? Do the merged event store and seat memory keep replay exact?
4. **The rules:** nothing from nothing (does a moving band carry its stores without creating or losing food?), and cause chains for `flight` and `took_up_herding`.
5. **Python 3.10 compatibility.**

Same format as before (AGENTS.md).
