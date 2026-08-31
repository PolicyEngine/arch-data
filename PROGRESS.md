# Belgium public facts wave progress

## State

- Active role: `ledger-source-ingestor`.
- Branch: `be-public-calibration-facts`, based on clean `origin/main` at
  `10597ae`.
- Phase: direct-publisher SFPD package implementation.
- Shell network access is unavailable (`github.com` cannot resolve); browser
  research remains available. Push, issue creation, and draft-PR creation must
  be retried after all local work is complete.

## Done

- Read `AGENTS.md`, `.github/chronicle-agents.yml`, the complete source-package
  harness, and the facts-only ADR before changing package content.
- Confirmed Chronicle must retain publisher-period facts only and must not add
  Microcosm bindings, target profiles, aging, reconciliation, imputation,
  take-up mechanics, PolicyEngine-computed values, or Axiom concepts.
- Confirmed issue 69 remains open and names SFPD pensions, regionalized child
  benefits, NBB national accounts, and other original Belgium source families.
- Confirmed the merged offline-fetch validation contract exists on current main.
- Identified current-main SFPD and Opgroeien packages as curated CSV extracts
  whose value artifacts are not immutable publisher downloads; they resolve as
  packages but do not satisfy this wave's stronger publisher-byte requirement.
- Inspected the unmerged `be-benefit-participation-facts` branch. Its official
  SFPD and Walloon Parliament PDFs are potentially reusable, while its manual
  dashboard/HTML transcriptions are excluded by this task's no-transcription
  rule.
- Confirmed the official SFPD February 2025 monthly-statistics PDF contains
  publisher tables for pension beneficiary counts, monthly pension expenditure,
  GRAPA beneficiary counts, and monthly GRAPA expenditure.
- Extended the shared document-number parser to preserve unambiguous European
  thousands/decimal formatting, with regression coverage for the SFPD number
  shapes; single-dot values remain backward-compatible decimals.
- Audited the six original issue-69 selectors on current main: all six aliases
  are registered, build 587 unique valid facts in total, and pass their package
  validators. PR 207 added only geography/offline-fetch prerequisites, not
  these fact packages.
- Pinned the verbatim official SFPD February 2025 PDF (SHA-256
  `0d6173e71a0e9c2cd220cd024a5b5fecbb6ca79f8b791cbd2b3368e7f8412106`,
  2,319,705 bytes) and replaced the intermediary pension CSV selectors with
  direct publisher-cell selectors for pension and GRAPA beneficiary totals and
  monthly expenditure.

## Next

- Select only official downloadable artifacts for implemented facts; add
  deterministic offline-fetch handoffs and explicit follow-up issues for
  blocked or interactive regional/HFCS sources.
- Implement a coherent reviewable package wave with direct publisher-cell
  lineage and focused tests, committing every coherent step.
- Run `validate-package`, package build/source-cell/consumer-artifact tests,
  ruff, `git diff --check`, deterministic and Chronicle judge reviews, and
  self-review.
- Write the final report file, verify the actual commit messages and proposed PR
  body, then retry push and draft-PR creation without merging.
