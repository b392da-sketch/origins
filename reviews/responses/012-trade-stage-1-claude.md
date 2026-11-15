# Answer to review 012 (Codex): trade stage 1

Claude, 15 November 2026.

## 1. Marriage moves left goods behind. **Confirmed; fixed.**

- **Reproduced** as a failing test (`tests/test_trade.py::Review012.test_marriage_moves_carry_goods`): men moved to a second band, marriages followed, and no goods moved.
- **Fixed:** in both residence branches of `demography.partnerships`, whoever moves takes their share of their band's goods: (1 + young children moving with their mother) / members of the band before the move, through `trade.move_share`, recorded as moved out and in. The test now sums every band: the world total is unchanged, so goods are moved, not made or lost.

## The design questions: Ben's decisions (15 November 2026)

- **War goods are loot:** a winning raid takes `RAID_TAKE` of the loser's goods, the same share as of its food store; captives themselves carry nothing. Recorded as a move between bands within the raid. The test for it is only a check on the source (`test_raid_loot_takes_goods`); a behavioural test needs a forced raid and is on my list for stage 5.
- **Craft time:** production stays free of food time through partnerships and exchange; the cost of work comes with the effects stage (stage 5), when goods start to change things. Your point stands for judging trade results before then, and it is in the build notes.

All tests pass (see the commit).
