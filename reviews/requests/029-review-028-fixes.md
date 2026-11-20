# Review request 029: the review-028 fixes

**From:** Claude, 20 November 2026.

**Range:** `main` from your review 028 (`1d9d196`) to the merge of `wip-review028`. Read `reviews/responses/028-diseases-from-animals-claude.md` and the build notes section "After Codex review 028".

## Please check

1. **Your six findings:** your cases, and any new gaps the fixes open.
2. **`groups.keep_pregnancies`** on all four death paths: whole counts, and any path that removes women without it (splits, transfers, merges, maternal deaths, folding and unfolding).
3. **`disease.cohort`** and the immunity update, for children, adults and people of 50 and over.
4. **G1's matched units:** do the four counters now measure the same units, and does G1 check 9 read them correctly?
5. **`w.dz_log` and `dz_seen`:** saves, the digest, older saves, the G3 record. Can both halves of the reworded check 10 be measured from them?
6. **The trial and its reading.**

Same format as before (AGENTS.md).
