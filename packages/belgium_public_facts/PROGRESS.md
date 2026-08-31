# Belgium public facts wave progress

## State

- Active role: `ledger-source-ingestor`.
- Base: clean `origin/main` at `10597ae`.
- Phase: inventory and current-main selector audit.

## Done

- Read `AGENTS.md`, `.github/chronicle-agents.yml`, the complete source-package
  harness, and the facts-only ADR.
- Confirmed Chronicle must retain publisher-period facts only and must not add
  Microcosm bindings, aging, reconciliation, imputation, take-up mechanics, or
  Axiom concepts.
- Confirmed the offline-fetch handoff contract exists on current main.

## Next

- Inspect issue 69 and its six original selectors against current `origin/main`.
- Inventory existing Belgian packages, official artifact pins, and package tests.
- Add only publisher-backed, deterministic source packages that form a coherent
  review wave; record inaccessible/interactive sources as explicit follow-ups.
- Run package/build and focused test gates, Chronicle judge reviews, self-review,
  final checks, push, and open a draft PR without merging.
