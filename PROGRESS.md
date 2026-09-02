# PR #229 completion

## State

The pending-proof classification fix and direct-push publication workflow are
complete and locally verified. Final repository verification, reporting, and
GitHub delivery remain. The worktree started from `ots-anchor-main` at
`03b27674`, matching the locally cached remote-tracking ref; GitHub DNS is
currently unavailable.

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

## Next

- Run focused tests, lint, formatting, actionlint, guard checks, and real-proof
  status against the journal checkout.
- Update this log and `out.md`, edit PR #229 when GitHub is reachable, and push
  `ots-anchor-main` without merging it.
