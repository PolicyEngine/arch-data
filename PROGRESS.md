# PR #228 gate round 1 fix progress

## State

- Branch: `fix-228-r2` at reviewed head `af418dc`.
- Assignment: address all four gate round 1 findings with reproductions and
  regression coverage.
- Applicable repository instructions: `AGENTS.md`; no `CLAUDE.md` is present.
- All four gate round 1 findings are fixed with regression coverage.
- Final lint, format, and full-suite verification are complete and passing.
- The required final report is written to runner output path `out.md`.
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
- Passed repository-wide Ruff lint.
- Passed Ruff formatting for all 12 changed Python files.
- Passed the complete test suite with direct exit code 0: 792 passed, 1 skipped,
  and 14 warnings in 1364.36 seconds.
- Completed two independent read-only final reviews with no actionable findings.
- Wrote the reproduction, fix, test, commit, and verification report to
  `out.md` without adding runner-owned root artifacts to Git.

## Next

- No implementation work remains. Hand off the committed fix lane and `out.md`.
- Do not push; publication is outside this lane's instructions.
