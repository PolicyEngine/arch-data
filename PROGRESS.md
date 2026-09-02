# Epoch dual-domain acceptance progress

## State

- Branch: `epoch-dual-domain` from `origin/main` at `ff3efd3`.
- Assignment: chronicle#143 mechanism 1, step 1 (dual-domain acceptance; emit unchanged).
- Approved role: `ledger-contract-maintainer`.
- Implementation, adversarial review, and local verification are complete.
- Publication is the current step: commit the final report, push the branch,
  open the requested PR without merging it, and record its URL.

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
- Made bundle ingestion validate Chronicle-only and mixed-epoch rows, with
  cross-epoch duplicate accounting and unknown-domain rejection.
- Added Chronicle relational emission/load coverage with valid SQLite foreign
  keys, invariant build/build-artifact digests, and Ledger-default output.
- Made source-package and offline-fetch readers accept both registered schema
  ids while scaffolds and administrative generators still emit Ledger ids.
- Addressed adversarial audit findings in governance schema validation,
  source-cell/suite lineage resolution, explicit Ledger-canonical build hashing,
  the Statbel package generator, and `validate-facts` CLI coverage.
- Preserved the bundle reader's historical permissive row-shape boundary while
  adding a non-mutating dual-epoch identifier gate; the two full-build bundle
  regressions and Chronicle/mixed/unknown-domain cases pass.
- Passed the complete test suite: 783 passed, 1 skipped, 14 warnings.
- Passed repository-wide Ruff lint and formatting for every changed Python file.
  The exact repository-wide format check still identifies eight untouched
  baseline files, all byte-identical to `origin/main`.
- Built the sdist and wheel offline with uv from cached build dependencies, then
  installed the wheel into a clean venv and passed the epoch import smoke.
- Passed independent `ledger-contract` and `ledger-boundary` judge reviews.
- Confirmed no changes under `releases/`, frozen fixture directories, frozen
  schema directories, or `.github/chronicle-agents.yml`.
- Removed the generated `.gitnexus/` index and incomplete ignored local `.venv/`.

## Next

- Push `epoch-dual-domain` and open the requested PR against `main`.
- Record the PR URL in `out.md`, commit that final state, and push it.
- Do not merge the PR and do not comment on issue #143.
