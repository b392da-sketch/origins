# Independent reviews

Codex reviews the work; Claude answers. The rules are in `AGENTS.md` at the top of the repository.

- `requests/`: what to review (written by Claude, or by Ben).
- `responses/`: Codex's reviews (`…-codex.md`) and Claude's answers (`…-claude.md`).
- `LOG.md`: one line per request and response.
- `scratch/`: Codex's working files (not committed).

## How Claude answers a review (Ben, 12 November 2026: "not uncritically")

Each finding is checked before anything is changed. Claude reproduces the problem with a test, a calculation or the code itself, and gives it one of three answers:
- **confirmed**, with the evidence, the fix and its commit;
- **not a problem**, with the reason and the evidence;
- **unclear**, with what was tried, put to Ben.

Nothing is fixed on the reviewer's word alone. Disagreements with the reviewer are written out, so Ben can judge both sides.
