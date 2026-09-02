# PR #229 completion

## State

Work is in progress on the direct-push publication workflow and the pending-proof
classification fix. The worktree is on `ots-anchor-main` at `03b27674`, matching
the locally cached `origin/ots-anchor-main`; GitHub DNS is currently unavailable.

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

## Next

- Reproduce and fix pending/complete/mismatch classification with hermetic
  fixtures for the captured OpenTimestamps 0.7.2 output.
- Replace bot-branch/PR/auto-merge publication with a bounded, non-force direct
  push to `main`, and update documentation.
- Run focused tests, lint, formatting, actionlint, guard checks, and real-proof
  status against the journal checkout.
- Update this log and `out.md`, edit PR #229 when GitHub is reachable, and push
  `ots-anchor-main` without merging it.
