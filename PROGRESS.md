# OpenTimestamps anchoring rework

## State

Implementation and local proof verification are complete. Delivery is blocked
on establishing or authorizing a GitHub publication path for protected `main`.

## Done

- Confirmed the worktree is clean and starts at `origin/main` commit `ff3efd3`.
- Read the repository agent rules and accepted the Chronicle/Microcosm boundary.
- Read PR #182 at `545cfe56`: the anchoring tool, eight fake-client tests,
  documentation, and all 15 Bitcoin-complete proof blobs for manifests 0000–0014.
- Read PR #183's workflow at `87f21f2` and the Fable+Sol gate verdict.
- Recorded the four gate defects to fix: impossible journal direct publication,
  mutable journal code receiving write credentials, verification after push plus
  skipped complete-proof binding checks, and stale rebased outputs.
- Read the journal branch's `scripts/receipt_pins.py`, immutable
  `releases/README.md`, and `README.md`; confirmed `ots/**` is outside both
  `gate_surface` and `data_surface`, while `releases/**` must not change.
- Attempted `gh api repos/PolicyEngine/chronicle/rules/branches/main`; GitHub DNS
  is unavailable in this lane, so no publication-path assumption has been made.
- Re-read Sol's completed #182 verdict and addressed its output-spoofing,
  local-state, backup-loss, and symlink-escape findings in the trusted tool.
- Copied the 15 proof blobs for releases 0000–0014 byte-for-byte from `545cfe56`.
- Added `--manifests`, complete-proof binding re-verification, a testable
  `ots/`-only change guard, and 15 hermetic fake-client tests (all passing).
- Restored the original proof on upgrade timeout as well as explicit client
  failure, closing the independent core review's only finding.
- Queried GitHub through the authenticated connector: `main` is protected,
  required-status-check enforcement is off, and repository plus parent ruleset
  lists are empty. The integration cannot read classic protection, so direct
  `GITHUB_TOKEN` publication is not established and is never attempted.
- Added main-owned proof documentation, the root README overview, and explicit
  focused OTS lint/test steps without narrowing main's existing full CI suite.
- Replaced the provisional direct-push workflow with a fixed bot-branch PR
  publication path. It queries effective rules in the run log, imports only
  manifest-matched proof files from an earlier retry, re-verifies them with
  `main`'s script, uses a bounded fetch/rebase/rerun loop, and invokes
  `gh pr merge --auto`; it never pushes the journal or `main` directly.
- Ran the required focused suite: 15 tests passed; `ruff check .` passed. The
  repository-wide format check reports the same 14 pre-existing files on
  `origin/main`; both added Python files pass the focused format check.
- Added `/tmp/journal` at `origin/codex/thesis-ledger-facts` and verified all 15
  carried proof bindings against its real manifest bytes. Full `status` reports
  exactly manifests 0015--0019 as unanchored. Calendar DNS is unavailable, so
  their missing proofs could not be stamped in this lane.
- Confirmed all 15 committed proof blob IDs match `545cfe56` byte-for-byte and
  that the revised workflow passes `actionlint` (including ShellCheck).
- Closed the first PR-path review's race findings: refresh the journal before
  importing retry proofs, reject divergent main/bot proof edits, detect main
  movement before and after the bot push, reuse an unchanged verified bot head,
  and accept merge/auto-merge only when the PR still names the verified SHA.
- Final publication review confirmed two external prerequisites cannot be
  established in this lane: repository metadata currently has
  `allow_auto_merge: false`, and the Actions setting that permits
  `GITHUB_TOKEN` to create pull requests is unreadable. Direct token updates to
  protected `main` also remain unproven because classic protection is unreadable.

## Next

- Obtain the exact `main` protection/effective-rules output proving direct
  `GITHUB_TOKEN` updates are allowed, or authorization to enable repository
  auto-merge and Actions-created pull requests (or to use an approved App/PAT).
- Then finalize the selected workflow, write `out.md`, push the branch, and
  open the superseding PR.
