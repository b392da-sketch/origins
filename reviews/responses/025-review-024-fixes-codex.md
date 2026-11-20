# Review 025: the review-024 fixes

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `e261a39..8d2b2ff`, the review-024 answer, the M4 build notes and the knockout driver. The five original cases pass. Two follow-up findings affect the choice of example event and the unlinked-loss tally.

## Findings

### 1. Partial transfers keep the undivided comparison value for a crop-loss example

- **Where** · `origins/sim/land.py:463–484,519–526`.
- **What is wrong** · `move_crop_loss` scales the linked amounts by the transferred fraction. It copies `land_acc_ktop` at full size when the example moves and leaves the same full size behind. Later seasonal observations compare against those undivided values to decide whether to replace the events.
- **Why it matters** · Both bands can retain an example that overstates the amount it represents in their own crop account. A later season contributing more linked loss than the inherited example can be blocked from becoming the recorded example. The linked totals are still correct.
- **How sure you are** · Certain.
- **How to see it** · Book a **100**-unit linked soil loss at cell **2** and move one tenth to an empty band. The linked accumulators are **90** and **10**, while both example sizes are **100**. At harvest book **20** linked soil loss at **778** for the receiver. Its crop record keeps cell 2's event even though **778** supplied the larger share of its linked loss.

### 2. Rounding residue can count as unlinked loss in the trial

- **Where** · `origins/sim/farming.py:496–504`, `origins/sim/land.py:386–391,424–438` and the unlinked-event tally in `local/scripts/knockout_land.py`.
- **What is wrong** · The total loss is computed from the product of the yield factors while its linked parts are computed separately. Their floating-point sums can differ slightly. The event stores any positive difference unrounded and the driver counts every value greater than zero.
- **Why it matters** · An event with all its crop loss linked can enter the count of events with unlinked losses. The amounts at issue are negligible food quantities, but each one contributes a full event to the published tally.
- **How sure you are** · Certain for the reproduction. The effect on the reported trial count is unmeasured.
- **How to see it** · Start with **100** potential crop, fertility **0.2** and salt **0.6**, with both land events active. The live formulas give **68.05714285714286** total loss and **68.05714285714285** linked parts. In a harvest and partial-transfer fixture with no wild loss, `land_hunger` writes **8.88 × 10⁻¹⁶** as unlinked, which passes the trial driver's test.

## Checked and sound

- **Review 024 cases.** An old-format archive with `land_crop_cell` and nonempty numerical loss rows loads and can close a band with `LAND=False`. Older crop amounts start unlinked. In the original whole-band fixture, the retained event and its **12**-unit example stay paired. A salt flag below the threshold contributes no linked salt loss. The **49** linked and **51** unlinked crop case produces **25** total and **12.25** linked per season. The original game-share knockout no longer yields a false game link.
- **Crop arithmetic.** For crop potential `C`, fertility factor `f` and salt factor `s`, the two parts `C(1−f)` and `Cf(1−s)` sum algebraically to `C(1−fs)`. On **1,000** samples they agreed within **1.82 × 10⁻¹²**. With the fertility penalty disabled, the soil part was zero. With the salt penalty disabled, the salt part was zero. The order allocates the interaction to the soil-first convention used by the implementation. A positive part is booked only against that kind's active event at the growing cell.
- **Transfers and rollover.** The total and per-kind amounts are conserved through partial transfers. Both soil and salt examples carried to an empty recipient in a post-harvest transfer. Harvest divides the accumulated amounts by four, keeps the chosen IDs and clears the current-year rows. Dropping the receiving band clears its amounts and IDs. The in-progress comparison value is the exception in finding 1. An example ID represents a contribution to its kind's sum, and the full sum can include other seasons and cells.
- **Census parity.** Across **1,000** mixed rows per configuration, vector counts and capped amounts matched scalar `_links` plus `crop_linked`. The configurations covered default shares, slow game off, fast game off, both game shares off, forest off, and all three shares off. This establishes parity for the two implementations. Wild attribution still credits the whole net wild pool when either wild condition has an eligible link, so those amounts are pooled exposure estimates.
- **Replay and physical outcomes.** A quarter-0 save with both soil and salt losses in the current and previous harvest accounts preserved the amounts, example IDs and comparisons. Digest and complete events matched for **16** more seasons with no invariant failures. A separate **32**-season mixed-farming fixture at `e261a39` and `8d2b2ff` produced the same **74** people and bitwise-identical physical stocks, land factors, farming state, physical people arrays, food ledger and random-stream states.

## Trial and interpretation

The reported **326,460** people match the prior land-on endpoint. This is consistent with the unchanged crop multiplication and the independent short comparison. The **67,259** total linked band-seasons also matches the prior trial, with **72** moving from wild-only to both pools. The unchanged whole-percent **45%** does not establish that the linked quantity was unchanged. The **1,594** unlinked-event tally uses the broadened per-kind accounting and the raw-value test described in finding 2. The trial checkpoint is external and I did not rerun its 300 years.

## Validation

**52 focused tests passed** in 151 seconds, with one AnyIO pytest-plugin deprecation warning. The run covers all land tests, the review-019 trade cases and the existing exact-replay regression. Additional scripts and results are under ignored `reviews/scratch/`. All source files parse with Python 3.10 grammar. No full suite or gate-length run was started.
