# Epoch dual-domain acceptance progress

## State

- Branch: `epoch-dual-domain` from `origin/main` at `ff3efd3`.
- Assignment: chronicle#143 mechanism 1, step 1 (dual-domain acceptance; emit unchanged).
- Approved role: `ledger-contract-maintainer`.
- Implementation is in progress; dual-epoch bundle, relational, and remaining
  schema readers are the current step.

## Done

- Read `AGENTS.md`, `.github/chronicle-agents.yml`,
  `docs/chronicle-governance.md`, and `docs/adr-chronicle-fact-identity-v2.md`.
- Confirmed the worktree began clean at the requested base commit.
- Retrieved and read Max's first-comment migration spec through the GitHub API.
- Completed the initial inventory of hashed domains, schema ids, validators,
  emitters, tests, and role-path implications.
- Confirmed that the live facts-only consumer artifact is v2→v3; retired
  target-profile and resolved-target v1 contracts must not be reintroduced.
- Added the central frozen Ledger/Chronicle epoch registry with Ledger as the
  single emission default.
- Wired fact, source-cell, source-row, source-column, source-row-value, and all
  eight consumer-contract hash builders to the registry with invariant digest
  suffixes across epochs.
- Added dual-epoch lineage validation, consumer-row schema normalization,
  artifact loading (including declared row-schema pins), mixed-epoch acceptance,
  and clear unknown-domain errors.
- Pinned all existing fixture and consumer-schema bytes by SHA-256; focused
  identity/artifact/schema verification passes (96 tests).

## Next

- Wire bundle, relational, source-package, offline-manifest, and derived-artifact
  surfaces to the registry while preserving every Ledger-default byte.
- Record required files outside the role's declared `allowed_paths` for explicit
  PR disclosure.
- Add adversarial tests without modifying goldens, fixtures, or `releases/`.
- Run focused tests, full verification, wheel build, and clean-venv import smoke.
- Write `out.md`, push the branch, and open (but do not merge) the requested PR.
