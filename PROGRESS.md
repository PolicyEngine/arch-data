# PR #228 gate round 1 fix progress

## State

- Branch: `fix-228-r2` at reviewed head `af418dc`.
- Assignment: address all four gate round 1 findings with reproductions and
  regression coverage.
- Applicable repository instructions: `AGENTS.md`; no `CLAUDE.md` is present.
- All four gate round 1 findings are fixed with regression coverage; final
  repository verification is in progress.
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
- Reject canonical duplicate cell/row lineage aliases during fact validation
  with the explicit `duplicate_lineage_key` issue code.
- Deduplicate canonical lineage defensively in both consumer and relational
  emission while keeping ordinals, relationship counts, and build hashing
  consistent.
- Bootstrap the Statbel generator from its own checkout before importing the
  epoch registry; cover direct-file execution with an isolated subprocess whose
  `PYTHONPATH` and site packages cannot mask cross-worktree resolution.
- Preserve null and integer identity values during bundle coverage
  canonicalization and sort mixed scalar identities deterministically.

## Next

- Run focused verification, repository-wide Ruff lint, changed-file Ruff format
  check, and the complete pytest suite with its exit code captured directly.
- Write the final report to `out.md`.
