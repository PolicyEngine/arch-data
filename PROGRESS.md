# OpenTimestamps anchoring rework

## State

Design evidence reviewed; implementation is next. The lane currently has no DNS
access to GitHub, so the required live `main` rules API evidence remains pending.

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

## Next

- Obtain live `main` rules evidence and select direct-push versus bot-PR publication.
- Reuse the proven anchoring tool and proofs while addressing all gate findings.
- Add the main-owned workflow, documentation, CI wiring, and tests.
- Run the full required verification, push the branch, and open the superseding PR.
