# Handover: Claude Code as the local runner

For a Claude Code session on Ben's laptop (Windows, 12 threads, 16 GB). Written 12 November 2026 by the Claude chat that builds Origins. The agreement is in `DESIGN_DRAFT_v0.6.md`, section 16, item 22.

## Your role

You run batches of local tests natively, fast, while the laptop is on. The chat keeps design, specifications, gate runs on GitHub, gate reports and the literature work. **Ben owns the design and approves gates.** Do not change simulation code, parameters or docs unless a request asks you to. Report what you find, and the chat decides.

Read `CLAUDE.md` first: the project's rules apply to you too.

## Setting up (once)

1. Clone `https://github.com/b392da-sketch/origins` (or pull, if a copy exists).
2. Use Python 3.10 or newer with NumPy (`pip install -r requirements.txt`).
3. Check that the tests pass: `python -m pytest -q tests`.

## The loop

1. `git pull`, then look in `local/requests/` for request files with no matching result in `local/results/`.
2. Run each request as it says, at most 4 processes at once so the laptop stays usable. Start each in its own process, at below-normal priority if you can.
3. Write `local/results/<request name>.md` (a summary) and, if the request asks, `local/results/<request name>/` (raw output files under 20 MB in all).
4. Append one line to `docs/LOCAL_LOG.md`: date, request, what ran, one-line result.
5. Commit only `local/results/` and `docs/LOCAL_LOG.md`, then push to `main`.

## Request format (`local/requests/YYYY-MM-DD-<topic>.json`)

```json
{
  "what": "One sentence: what question this answers.",
  "commit": "main or a commit hash to check out first",
  "start": "fresh | <path to a saved world>",
  "runs": [
    {"label": "A", "planet": 3, "seed": 1, "after_first": 1000, "params": {"NEW_HOUSEHOLD_START": 0.5}},
    {"label": "B", "planet": 3, "seed": 1, "after_first": 1000, "params": {"NEW_HOUSEHOLD_START": 1.0}}
  ],
  "report": ["median Gini", "rank correlation of Gini with land scarcity", "largest polity"],
  "script": "optional: a script under local/scripts/ to run instead of the default"
}
```

- **Saved worlds:** a request may ask you to make one first, for example planet 3 at year 8,500, just before farming. That cuts each test from about 2 hours to 20–30 minutes. Keep saved worlds out of git: they are 100 MB or more.

## Result format (`local/results/<request name>.md`)

- what ran (the commit, Python and NumPy versions, how long each run took);
- a table with one row per run and the numbers the request asked for;
- anything odd: errors, a run that died, numbers that look impossible.

Do not interpret beyond that; the chat does.
