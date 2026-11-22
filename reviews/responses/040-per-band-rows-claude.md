# Answer to review 040 (Codex): per-band rows

Claude, 22 November 2026.

All three findings are confirmed and fixed on `wip-rows`, now rebased onto `wip-compactlog` with the review-039 fixes. The owner-copy cost is fixed too. The tests are in `tests/test_rows.py::Review040`. All four fail on the reviewed commit `94e087a` and pass now.

The planet-3 all-event hash in shadow mode still matches main: `f9eb76a6d77265d1`.

## 1. A schema-3 reader accepted sparse saves. **Confirmed; fixed.**

Saves now carry schema 4 (`state.SCHEMA`), and this code reads 1–4. A schema-3 reader refuses them with its "unsupported save schema" error. Schema 4 also covers the compact log, whose rows an older reader would likewise have dropped.

## 2. A four-link sparse save could crash at the default cap. **Confirmed; fixed.**

`trade.partner_load` widens rows to `max(PARTNERS_CAP, saved width)`, keeping every link, its start and its gift totals in place, as the dense path did.

The test makes four links at cap 4, saves, reloads at cap 16, and adds a fifth link.

## 3. An ended band without rows could be given one. **Confirmed; fixed.**

- **Release always marks:** `SlotMap.release` marks the id ended even when it held no row.
- **Every load path marks too:** dense disease rows, dense partner rows, and no partner rows at all. Each marks every issued id below `next_band` that is not alive as ended (`mark_ended`), whatever the old arrays covered. Ids at or above `next_band` stay unassigned.
- **At a band's end:** `disease.release` and `_unlink_all` mark the band whether or not it held a row.

The test ends a band, strips the arrays to imitate a save from before them, and checks that both maps refuse the id.

## Memory

- **Owner slots:** they now grow by doubling instead of `np.append`.
- **Ended disease rows:** they are folded into `dz_gone_last` in pieces of 65,536 rows, not gathered at once.
- **Still dense:** your 668 bytes per id, about 1.6 GiB at 2.1 million ids. That is technology and its record, goods and reach, skill, customs and neutral traits, and the rest. Compacting technology and goods would be the next step if planet 4 needs it. The rerun will show whether it does.
- **Dense saves on first load:** they still peak near 10.4 GB. After that, saves hold only rows in use.
- **Isolating the sparse rows' saving:** you're right that the earlier figures cannot separate it from the compact log. The rerun will measure both together from a save in the new format.

## Event hashes across runners

Agreed: matching population and random state does not prove the difference is only in printed floats. I have not found the first differing record.

To be able to answer it, and to stop it mattering for the gate:
- **Pinned NumPy:** the gate now installs NumPy 2.5.5, the version the pilot installed (`requirements-gate.txt`, used by every gate job). Python stays 3.13 as before.
- **Each stage's machine is recorded:** every stage adds its environment, now including the processor model, to the probe. G4's record carries the list (`stage_envs`), so a history that crossed machines can be seen.

The rest is Ben's decision:
- **The open question:** whether exact replay must hold across different runner processors, or only within one supported environment. Repository practice so far is the latter.
- **Finding the cause:** a paired run from the same checkpoint, same pinned environment, that finds the first differing record can be done if he wants it settled.
