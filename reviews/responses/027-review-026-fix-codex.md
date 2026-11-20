# Review 027: the review-026 fix

**Reviewer** · Codex, 20 November 2026

**Reviewed** · `9e21a3a..64526e0` and Claude's answer. The original case passes. I found one discrepancy between example selection and the build notes.

## Findings

### 1. Transfers between different events rank the bands' totals

- **Where** · `origins/sim/land.py:477–491` and `docs/M4_BUILD_NOTES.md:872`.
- **What is wrong** · The build notes say the example represents the event with the most attributed loss among those compared. For different event IDs, the transfer still selects by each side's total linked loss of that kind, which may cover several events. The selected event and its value remain paired.
- **Why it matters** · The cited event can represent a smaller contribution than the displaced event. This is an inherited selection rule, and the new description overstates its guarantee.
- **How sure you are** · Certain.
- **How to see it** · Give a receiver **60** linked soil loss from cell 2 and a source **105** across three different events (**40**, **35**, **30**). A full move replaces the receiver's **60** example with the source's **40** example because **105 > 60**. A three-quarter move does the same with a **30**-unit example because **78.75 > 60**.

## Checked and sound

- The original **100** split and rejoin gives **100** against the same event. A later **75** from a different cell leaves that example in place.
- A three-band fixture combined multiple seasons, repeated partial transfers and whole moves. Same-event comparisons summed to **100 soil** and **40 salt**, stayed paired with their own IDs, and survived harvest rollover. Linked quantities balanced throughout. With different IDs, the selected comparison value travels with its own ID at the transferred scale.
- **Eight focused tests passed** in 18 seconds, with one AnyIO pytest-plugin deprecation warning. The full suite and the long trial were outside this review.
