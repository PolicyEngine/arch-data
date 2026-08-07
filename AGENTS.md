# Chronicle Agent Rules

Chronicle is a source-backed fact store. It may parse publisher artifacts, normalize
representation, preserve provenance, and declare target-profile contracts.

Every fact value must trace to a publisher. The boundary is who asserted the
value, not level versus projection: a publisher's own projection (CBO baseline,
BFP outlook, SSA trustees, TPC/JCT score) is a fact typed
`assertion: source_projection`. PolicyEngine-computed values — aged, uprated,
forecast, or reconciled levels — are never Chronicle facts.

Do not put Microcosm work in Chronicle:

- no cross-source reconciliation
- no aging to a build year
- no imputation
- no support-aware target activation
- no solver-ready target construction
- no target values in target profiles
- no PolicyEngine-computed values stored as facts

Resolving profile targets at a period other than a fact's reference period
requires the consumer's explicit `PeriodAlignmentDeclaration`; Chronicle records
the declaration and returns the published level, never the aligned number.

Only approved Chronicle agent roles in `.github/chronicle-agents.yml` should add or
modify source packages, target profiles, or contract schemas. Source-data PRs
need deterministic validation plus the listed Chronicle judge reviews before merge.
