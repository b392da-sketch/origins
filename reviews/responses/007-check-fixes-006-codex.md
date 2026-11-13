# Review 007: fixes for review 006

**Reviewer:** Codex, 14 November 2026.

**Reviewed:** commit `11cc606` and Claude's response to review 006, on `main` at `d276498`. The later cause-chain-validator change is outside this request's focused scope. Existing design/specification and M3 decisions are as reviewed in 005–006. No implementation files changed; no gate-length run started.

**Result:** both original reproductions from 006 now pass, and `is_herder` agrees with the current-cell predicate in `move`. Two remaining fission-key errors are reproduced below.

## Findings

### 1. The destination key uses the parent's way of life at its source

- **Where:** `origins/sim/bands.py`, `group_key` and the destination lookup at line 110; `origins/sim/pastoral.py`, `is_herder`.
- **What is wrong:** `group_key(w, b, cell=target)` changes only the cell component of the returned tuple. Its herder component still evaluates `b.cell`, so it can disagree with the key the same people would have after arriving at `target`.
- **Why it matters:** A group can still transfer into a different way of life without an event and lose the skills it would have carried into a separate daughter. The direct-transfer shortcut is therefore still not equivalent to splitting a daughter and applying current-cell consolidation.
- **How sure you are:** Certain in the reproduction; frequency in full histories is unmeasured.
- **How to see it:** In the same planet-1 fixture as 006, put an autonomous, 30-person goat-only group at cell **21890**, and an autonomous, 201-person group at cell **2**. Fold both, set `farm_share=1` and `village=True`. Both know goats at skill 3; the incoming group also knows grain at skill 3. Give cell 2 goat/grain values **0.5/0.1**, and cell 21890 values **0.1/1**; other farming suitability is zero. The incoming group is a herder at home (83.3% animals), but would be crop-dominated at the destination (9.1% animals). `group_key(incoming, cell=21890)` nevertheless returns `(21890, True, True, -1)`; temporarily placing it there and calling `group_key(incoming)` returns `(21890, True, False, -1)`. Call `fission_and_merge`: sizes become **140 at the destination and 91 at the source**, with the third fixture band unchanged. The destination retains grain skill **0**, and the event list still contains only the three founding events. A separately split daughter would retain grain skill 3 and have a different key from the resident herder.

### 2. Newly split groups are still inserted under the old two-component key

- **Where:** `origins/sim/bands.py:129–133`, especially `group_at[(target, fsv[k])] = nb_`.
- **What is wrong:** Existing groups and destination lookups now use four-component `group_key` tuples, but inserting a new daughter still uses `(cell, farming)`. Later groups in the same call cannot find that daughter, even when all four intended components agree.
- **Why it matters:** This creates unnecessary daughter bands and repeats polity admission instead of transferring into an existing compatible population. Under limited polity capacity it changes political outcomes: the extra daughter can become autonomous and remain separate, rather than joining the compatible member already at its destination. This affects foragers too: all lookups have four components, while every new insertion has two.
- **How sure you are:** Certain; an isolated in-memory substitution confirms the causal line.
- **How to see it:** Put two same-polity, 201-person herding groups at cell 2, each with farming share 1, goat skill 3 and `village=True`. Make cell 21890 their only usable neighbouring destination, initially empty; goat values are 0.5 at home and 1 there. Set the polity's load to zero and capacity to **1.1 × the first daughter's admission load**, so one daughter can join but a second cannot. In one `fission_and_merge` call, instrument the existing helpers: the code calls **split, split**, producing daughter **3: polity 0, 110 people** and daughter **4: autonomous, 98 people** at the destination. In memory only, replacing the insertion with `group_at[group_key(w, nb_, tables=tables)] = nb_` changes those calls to **split, transfer**, leaving one daughter in polity 0 with **208 people**. This is an experimental comparison, not an implementation change in the repository.

## Original reproductions: checked and sound

- **006 finding 1:** the original two-polity, crop/herder fission case now leaves the crop group at 30 people and splits a separate 110-person daughter from the 201-person herder, whose remaining size is 91. The original cross-polity absorption is prevented.
- **006 finding 2:** the original collision between a crop-dominated former herder and a present herder now leaves both 30-person groups alive. The historical marker no longer controls the classification.
- **Current-cell predicate:** 200 independently varied share/skill/wild-species/suitability cases, plus zero-value and exact-threshold cases, agree with `move`'s filter: farming share at least 0.5, positive animal value, and animal value at least `PASTORAL_SHARE × (animal + plant value)`. The helper draws no random numbers. Finding 1 concerns the cell used by its caller, not this predicate.
- **Same-kind groups and foragers:** groups with the same present classification and polity still consolidate despite different `herder_since` values. Foragers short-circuit the herder calculation, so their historical marker has no effect. Consolidation still has at most three keys per cell/polity, not one key per band or date.
- **Folding and unfolding:** the checked round-trip preserves the band's key, population, farming skills and political affiliation; these operations change representation within a band rather than moving it into another one.

## Membership-path audit

- `groups.transfer` has one simulation caller: the fission shortcut. It does not itself enforce classification or membership. Its destination selection is where findings 1–2 arise.
- `groups.merge_into` is called by consolidation and by the small-band social-merge path. Consolidation uses the current key. Small-band merging may cross polities or ways of life intentionally, but records a `merge` event naming the source, destination and reason; it is distinct from a silent representation change.
- `groups.split` copies skill, farming share and customs through `new_band(parent=...)`. Membership follows the existing M3 capacity rule: an admitted daughter stays attached to its parent; otherwise it becomes autonomous. Such group splits are counted rather than individually logged. This existing admission policy is not itself a new design finding, but it means one cannot claim every group membership change is event-backed. Finding 2 shows it being invoked unnecessarily because an existing compatible daughter is missed.
- `groups.fold` and `unfold` preserve band identity. Their simulation call sites record aggregate folding or seat-unfolding events; the folds inside social merging are covered by the enclosing merge event.

The new regression test exercises the common-key decisions using a stub for `is_herder`; it does not exercise destination-cell classification or the new-daughter index insertion. Both findings above pass that test.

## Time per season on a large constructed world

Measured locally with **5,003 group-mode bands / 750,090 people**, on generated planet 1. Each group occupied a distinct land cell and was below the fission threshold, isolating classification cost. Land tables were warm. Figures below are medians of seven repetitions after a warm-up, using Python 3.12.14 and NumPy 2.3.5; they are indicative timings from this host, not historical-world throughput guarantees.

| Work | All groups foraging | All groups farming |
|---|---:|---:|
| One `group_key` pass over the groups | 0.004 s | 0.122 s |
| Whole `fission_and_merge` phase | 0.014 s | 0.181 s |

For the all-farming fixture, temporarily substituting the previous cheap historical-marker key in memory reduced the phase to **0.008 s**; the new classification therefore adds approximately **0.17 s per season** in this case. Unique cells and no fission ensure that this comparison does not change grouping outcomes. The phase normally classifies groups both when constructing `group_at` and again during consolidation, in addition to any destination lookups.

A four-season run through the normal ordered engine phases, starting with adequate stores and the fixture's aggregate people ledger balanced, averaged **0.697 s per season**, including **0.190 s** in fission/merge and **0.237 s** in pastoral movement. It ended with 5,003 living groups and no invariant failures. This is a timing fixture, not an ecological or gate validation.

**Affordability:** the helper's cost is measurable, especially in a farming-heavy world: 0.17 s per season is roughly 11–12 additional minutes per 1,000 simulated years on this fixture. The request provides no performance budget, so I cannot assign a performance pass/fail mark. Foragers avoid the array calculation and remain much cheaper. The correctness findings should be resolved before treating these timings as final.

## Validation

**50 tests passed**, with one installed AnyIO pytest-plugin deprecation warning, in **341.23 seconds**, using `python -m pytest -q -p no:cacheprovider tests`. Focused scripts and outputs are under uncommitted `reviews/scratch/`. All `origins/` source parses with the Python 3.10 grammar; runtime checks here used Python 3.12.14, not an actual 3.10 interpreter. Only this review and `reviews/LOG.md` are committed.
