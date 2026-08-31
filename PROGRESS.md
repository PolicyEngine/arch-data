# Belgium public facts wave progress

## State

- Active role: `ledger-source-ingestor`.
- Branch: `be-public-calibration-facts`, based on clean `origin/main` at
  `10597ae`.
- Phase: local work complete; external GitHub handoff blocked.
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
- Added a schema-validated offline-fetch handoff for the native Opgroeien
  caseload and expenditure exports, official AVIQ and Iriscare annual-report
  PDFs, the blocked Ostbelgien Statistik HTML response, and the ECB HFCS wave
  2023 statistical-tables ZIP. No unresolved source has a placeholder fact.
- Prepared separate, ready-to-file follow-up issue bodies for Opgroeien, AVIQ,
  Iriscare, Ostbelgien, and ECB HFCS. They all reference open issue 69 and the
  deterministic handoff; GitHub issue creation remains pending the network
  retry.
- Validated the SFPD package with zero errors or warnings; its suite preserves
  13,644 full-document cells, resolves four facts with 100% lineage, and builds
  and reloads a four-row facts-only consumer artifact.
- Revalidated all eight other `pdf_text_numbers` packages after the European
  number-parser change, plus the six original issue-69 packages. All passed.
- Focused parser, offline-fetch, SFPD, selector, facts-only, and consumer tests
  passed. Ruff and `git diff --check origin/main` passed.
- Obtained `PASS` verdicts from both required judges:
  `ledger-source-fidelity` and `ledger-boundary`.
- Started the 151-package merged-bundle regression, then stopped it after
  20m49s and 7.4 GB of temporary output because it remained far from complete;
  the package-specific bundle and consumer artifact passed. The temporary test
  output was removed.
- Recorded the governance inconsistency that the literal source-ingestor path
  globs omit user-required progress, raw-artifact, offline-handoff, issue-draft,
  and pre-existing Belgium-test paths. No contract, schema, core, model, or
  consumer-owned behavior changed.
- Completed self-review and committed the exact proposed draft-PR body.
- Retried issue creation, branch push, and draft-PR creation. GitHub DNS/API
  access is unavailable, and `gh auth status` reports an invalid token; no
  issue, remote branch, or PR was created, and nothing was merged.
- Wrote the final report to `BELGIUM_PUBLIC_FACTS_REPORT.md`.

## Next

- Restore GitHub DNS/API access and refresh `gh` authentication.
- File the five committed follow-up issue bodies, push the branch, and open a
  draft PR referencing (not closing) issue 69 with the committed PR body.
- Verify the remote head and rendered PR body; do not merge.
