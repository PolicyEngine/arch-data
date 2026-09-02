# PR #229 completion

## State

The pending-proof classification fix, direct-push publication workflow, final
repository verification, and report are complete. GitHub delivery is blocked:
shell DNS prevents fetch/push/`gh pr edit`, and the authenticated connector's PR
body mutation was cancelled. PR #229 remains open and unmerged.

## Done

- Checked for another `ots-anchor-main` process; this sandbox denies process-list
  access to both `pgrep` and `ps`, so no process result was available.
- Attempted the required `git fetch origin`; DNS resolution for GitHub failed.
- Confirmed local `HEAD` and `origin/ots-anchor-main` both resolve to
  `03b27674028a0d8cf5bdc71437f5944661f3c6cb`, then reset the worktree to that
  remote-tracking ref.
- Read the inherited progress log. Attempted to read PR #229 with `gh`; the same
  GitHub DNS failure prevented access, so the supplied dispatch facts and PR-body
  requirements are the current source of truth.
- Accepted the Chronicle boundary and the prohibitions on changing `releases/`,
  `ledger/`, or proof bytes.
- Fixed proof classification to inspect local `ots info` structure first, give
  any Bitcoin block-header attestation precedence over leftover pending
  attestations, and then validate binding from the exact 0.7.2 output contract.
- Replaced permissive verify-output recognition with exact/full-line parsing:
  the exact mismatch line is the only mismatch, captured pending and paired
  Bitcoin-disabled/manual lines bind successfully, and unknown output fails
  closed.
- Updated the hermetic fake client with the captured four-calendar pending,
  mixed complete, mismatch, upgrade, and unrecognized outputs. All 17 focused
  tests pass; focused Ruff lint and formatting checks pass.
- Ran real status with the cached 0.7.2 executable. All 15 complete proofs were
  recognized, then calendar DNS errors prevented binding classification for the
  five pending proofs; the fixture suite covers their supplied captured output.
- Replaced bot-branch import, PR creation, and auto-merge machinery with a
  proof-only, non-force `git push origin HEAD:main` using only `contents: write`.
- Added best-effort start-of-job logging for the three supplied effective-rules
  and classic-protection API endpoints; metadata read failures warn but do not
  block the publication attempt.
- Retained the credential-free journal checkout, `run` + `verify` + `guard`,
  `ots/`-only staging and committed-scope checks, and dirty-worktree refusal.
- Added a three-attempt non-fast-forward path that fetches and rebases current
  `main`, refreshes the journal, reruns all checks, and recommits before retry.
  Failed-push classification uses fetched commit ancestry, covering server-side
  ref races and ambiguous successes without parsing Git's localized output.
- Updated both proof documentation sections to say automation pushes proof-only
  commits to `main` and to document bounded retries plus the guarantees against
  force-pushing or pushing the journal branch. `actionlint` passes.
- Reconfirmed all 20 `.ots` blob bytes are unchanged (combined checksum
  `420c3f54b47df5c58c58edc7202f580dcbad40193a4264bec20c133b71a375b1`)
  and there are no `releases/` or `ledger/` changes.
- Ran the final required suite: 17 focused tests, repository-wide Ruff lint,
  focused Ruff formatting, and actionlint all pass.
- Confirmed local proof structure with the real cached OpenTimestamps 0.7.2
  executable: 15 Bitcoin-complete and 5 pending. Calendar DNS prevents the full
  status binding pass, so the captured-output fixture tests are the documented
  no-network fallback.
- Wrote the final implementation, verification, integrity, and delivery report
  to `out.md`.
- Read PR #229 through the authenticated connector and prepared the replacement
  “Publication path” body at `/tmp/pr229-body.md`. The exact `gh pr edit` command
  failed on DNS, and the connector write was cancelled.

## Next

- When GitHub access is available, push `ots-anchor-main` and run
  `gh pr edit 229 --body-file /tmp/pr229-body.md` without merging the PR.
