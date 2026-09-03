# PR #228 gate round 1 fix progress

## State

- Branch: `fix-228-r2` at reviewed head `af418dc`.
- Assignment: address all four gate round 1 findings with reproductions and
  regression coverage.
- Applicable repository instructions: `AGENTS.md`; no `CLAUDE.md` is present.
- Publication ordering is fixed; three findings remain in progress.
- No network access or push will be attempted.

## Done

- Read `AGENTS.md`, `HEAD_SHA.txt`, and `_inputs/peer-round1.md`.
- Confirmed the reviewed head matches `HEAD_SHA.txt`.
- Confirmed runner-owned inputs, logs, and `out.md` are untracked and will not be
  included in implementation commits.
- Reproduced all four findings on the reviewed implementation.
- Made derived publication validate the resolved build identity before uploads
  or metadata output, with omitted/supplied-output regression cases proving no
  uploader call and no metadata truncation.

## Next

- Reject canonical duplicate lineage identities and deduplicate relational and
  consumer emission defensively.
- Restore the Statbel generator's isolated direct-file invocation.
- Preserve non-string bundle identities through coverage canonicalization.
- Run focused verification, repository-wide Ruff lint, changed-file Ruff format
  check, and the complete pytest suite with its exit code captured directly.
- Write the final report to `out.md`.
