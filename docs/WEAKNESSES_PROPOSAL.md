# Addressing the weaknesses: proposal and Ben's decisions

Claude, 27 November 2026. **Approved by Ben on 27 November 2026** ("I approve your proposals"). Nothing here changes the approved G4a plan; all of it starts after G4a closes.

The full text is in the Claude doc "Origins — Addressing the weaknesses (proposal)" and its Notion copy. This file is the repository's record of what was decided.

At M4a the project is a credible, literature-based and explainable simulation of early humanity. Its weak points are:
- scale;
- individuals at scale;
- calibration;
- a closed list of techniques;
- the parts of the vision not built yet (belief, cities, states, industry).

## Decisions

| # | Decision | Ben's answer (27 November 2026) |
|---|---|---|
| 1 | Scale design note first after G4a; a scale target | Approved. The note proposes the numeric target (seconds per simulated year and memory at a stated population), and Ben approves the number with the note. |
| 2 | Whether a compiled core is ever allowed | As proposed: not now. Vectorise first; a compiled extension is raised again only if profiles show it is needed. The Python-and-NumPy rule stands. |
| 3 | Individuals at scale | Approved: a followed sample of ordinary families stays individual in every polity. The sample's size is proposed in the scale note. People drawn on demand from group statistics come later, after the lineages, and only if exact replay can be kept. |
| 4 | Calibration targets | Approved: reported beside each gate, not pass marks at first. Sensitivity runs (key parameters ±50%) on each major mechanism. |
| 5 | Carried-forward failures | Approved, each a small build step with its own literature check, in this order: island divergence (M1), rising inequality (M2), the herd half of M3's check 9. They run alongside M4b. |
| 6 | Technology | Approved: local variants of existing techniques now; open-ended invention after M6. Variants are not in the approved M4b specification, so Claude drafts them as an amendment to it for Ben's approval before building. |
| 7 | Milestone order | Approved: M4b, then M5 belief and ritual, M6 cities, markets and money, M7 states and empires, then industry and beyond. |
| 8 | Process safeguards | Approved: a realism review at each milestone's start, and an unexpected-behaviour log in each milestone's build notes. Both added to `CLAUDE.md`. |

## Order after G4a

1. The scale design note, with its target and the followed-sample size.
2. Sensitivity runs on the M0–M4a mechanisms, with calibration targets reported.
3. M4b, with the three carried-forward fixes alongside it and the technique-variants amendment.
4. M5 onward, in the order above.

## Literature still to be checked before use

These are named in the proposal and have not yet been verified against the text:
- W. Brian Arthur, *The Nature of Technology* (2009);
- Ara Norenzayan, *Big Gods* (2013);
- Harvey Whitehouse, *Modes of Religiosity* (2004).

The calibration sources were checked when the proposal was written: Binford 2001 (via D-PLACE), Marlowe 2005, Bowles 2009, and Kohler et al. 2017.

All values the targets imply are tunable starting points, as for `params.py`.
