# OpenTimestamps anchoring rework

## State

Trusted anchoring core implemented and tested. Publication-path selection remains
pending because classic `main` protection details are not yet readable in this lane.

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
  lists are empty. The integration cannot read classic protection, so this is
  not yet enough evidence to choose direct push.

## Next

- Obtain live `main` rules evidence and select direct-push versus bot-PR publication.
- Add the main-owned workflow, documentation, CI wiring, and tests.
- Run the full required verification, push the branch, and open the superseding PR.
