# PR #228 gate round 1 fix progress

## State

- Branch: `fix-228-r2` at reviewed head `af418dc`.
- Assignment: address all four gate round 1 findings with reproductions and
  regression coverage.
- Applicable repository instructions: `AGENTS.md`; no `CLAUDE.md` is present.
- Work is in progress; no network access or push will be attempted.

## Done

- Read `AGENTS.md`, `HEAD_SHA.txt`, and `_inputs/peer-round1.md`.
- Confirmed the reviewed head matches `HEAD_SHA.txt`.
- Confirmed runner-owned inputs, logs, and `out.md` are untracked and will not be
  included in implementation commits.

## Next

- Inspect the PR diff and affected publication, validation, emission, generator,
  and coverage code paths.
- Reproduce all four findings on the reviewed head and record commands/results.
- Add regression tests and implement each fix in small named commits.
- Run focused verification, repository-wide Ruff lint, changed-file Ruff format
  check, and the complete pytest suite with its exit code captured directly.
- Write the final report to `out.md`.
