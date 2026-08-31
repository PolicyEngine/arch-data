## Summary

- replace the intermediary SFPD pension CSV with the official February 2025
  monthly-statistics PDF and direct source-cell selectors;
- add four exact February 2025 facts: employee/self-employed pension
  beneficiaries and monthly expenditure, plus GRAPA beneficiaries and monthly
  expenditure;
- add a source-scoped European document-number format for SFPD while preserving
  the original default grammar and existing single-dot behavior;
- audit the six original Belgium selectors from #69: all remain registered,
  unique, valid, and resolve 587 facts on current main;
- add a validated six-artifact offline-fetch handoff and five ready-to-file
  follow-up issue bodies for Opgroeien, AVIQ, Iriscare, Ostbelgien, and ECB
  HFCS, without adding placeholder facts.

## Source pin and fact scope

Official SFPD artifact:

- URL: `https://www.sfpd.fgov.be/files/3432/fr_stat_2502.pdf`
- SHA-256:
  `0d6173e71a0e9c2cd220cd024a5b5fecbb6ca79f8b791cbd2b3368e7f8412106`
- size: 2,319,705 bytes
- printed page 22, table 2.2: 2,435,457 employee and/or self-employed
  pension beneficiaries and EUR 3,759,582,728.06 monthly expenditure;
- printed page 36, table 2.4.1: 117,650 GRAPA beneficiaries and
  EUR 86,398,449.47 monthly expenditure.

All four facts are February 2025 `observation` assertions with
`administrative` provenance, Belgian country scope, exact publisher periods,
and full source-cell lineage. The pension beneficiary snapshot is explicitly
dated 1 February 2025. The pension total is narrowed to the employee and/or
self-employed regimes actually covered by table 2.2.

No aging, period alignment, reconciliation, imputation, take-up mechanics,
target profile, model binding, solver construction, PolicyEngine-computed
value, or Axiom concept is included.

## Validation

- `validate-package sfpd-legal-pension-caseload-2025 --year 2025`: PASS,
  4 record sets/rows/measures and zero errors/warnings;
- source suite: PASS, 13,644 full-document source cells, 4 facts, 100% lineage,
  zero agent-acceptance errors;
- package bundle and consumer artifact build/load: PASS, 4 rows;
- parser/SFPD plus the five existing packages exposed by the first CI run:
  27 passed after restoring the original default grammar;
- six original issue-69 package validators: PASS;
- focused parser/offline/SFPD/selector tests: PASS;
- facts-only and consumer tests: 33 passed;
- ruff: PASS;
- `git diff --check origin/main`: PASS;
- `ledger-source-fidelity`: PASS;
- `ledger-boundary`: PASS.

The first CI run caught row shifts caused by an overly broad shared number
grammar. The final implementation scopes European parsing to SFPD and restores
the prior default for all existing packages. The relevant single-package
bundle and consumer artifact pass; the all-source 151-package bundle remains a
required final-head CI gate.

## Follow-ups and governance

The regional child-benefit and HFCS sources require native exports or official
publisher responses. Their deterministic retrieval instructions are in
`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json`; no values were transcribed.

The literal `ledger-source-ingestor.allowed_paths` list omits several paths
this task explicitly requires (`PROGRESS.md`, `db/data/**`, the root handoff,
issue drafts, and the pre-existing Belgium test). This PR makes no contract,
schema, core, model, or consumer-owned behavior change; maintainer acceptance
or a registry clarification is still needed for the path inconsistency.

Refs #69
