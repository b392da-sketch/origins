# Review 026: the review-025 fixes

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `e3f228a..0902c17` and Claude's answer. Both original cases pass. One edge case remains in the representative event after repeated transfers.

## Findings

### 1. Rejoining portions of the same seasonal loss can leave its example too small

- **Where** · `origins/sim/land.py:477–488,519–533`.
- **What is wrong** · Each portion now carries the correct fraction of the example. If portions of that same season later reach the same band, their linked amounts add and only one portion contributes to the comparison value.
- **Why it matters** · A later loss smaller than the recombined contribution can replace its example. This affects which cause is cited. The total and per-kind exposure amounts remain conserved.
- **How sure you are** · Certain.
- **How to see it** · Book a linked loss of **100** at cell 2. Move half to a second band, then move the entire remainder to that same band. Its linked amount is **100** and `land_acc_ktop` is **50**. A **75**-unit loss at cell 778 on harvest then becomes its example, although it carries the full **100** from cell 2. Event ID alone cannot identify a seasonal contribution because multiple seasons can cite the same degradation event.

## Checked and sound

- **Whole and partial moves.** The original **90/10** split passes and the receiver's later **20**-unit loss replaces its **10**-unit example. A full move hands over the selected example at its existing scale and zeros the source comparison value. In a repeated-move fixture covering both kinds, all totals were conserved and each selected fragment carried its scaled comparison value. The recombination limit is described above.
- **Rounding.** The original subtraction residue now gives zero. The cutoff is `1e-9 × max(total loss, 1)`, so it can suppress genuine positive remainders. With **100** units of linked crop loss, a real unlinked wild loss of **5 × 10⁻⁸** was suppressed and **2 × 10⁻⁷** was retained. This is negligible as food and only affects the event note, stored remainder and event tally. That tally counts unlinked amounts above the tolerance.

## Validation

**Seven focused tests passed**, covering reviews 024 and 025, with one AnyIO pytest-plugin deprecation warning. Additional transfer and tolerance checks ran under `reviews/scratch/`. The full suite and 300-year trial were outside this review.
