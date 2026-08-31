Refs #69.

## Source gap

Chronicle has no direct Iriscare or Famiris post-2019 Brussels child-benefit
package containing both caseload and expenditure. The official interactive
statistics are not safe to transcribe, and preliminary inspection of the
official annual report found more than one expenditure occurrence that must be
distinguished by publisher scope rather than silently reconciled.

## Deterministic handoff

Retrieve the official Iriscare 2024 annual-report PDF through the Iriscare entry
in `FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json`:

`https://rapport.iriscare.brussels/wp-content/uploads/2025/09/Rapport-annuel-2024.pdf`

The official statistics pages may be used only if a separate reviewed handoff
pins their native Fabric export bytes; screenshots and copied dashboard text
are not artifacts.

## Acceptance criteria

- Pin the unchanged official PDF with exact URL, SHA-256, size, publication
  vintage, table/page references, and content-addressed raw-storage pointer.
- Parse the full PDF deterministically. If multiple publisher cells differ,
  emit separately labelled facts only when their accounting populations/scopes
  are explicit; otherwise document the ambiguity and omit the values.
- Preserve exact Brussels administrative/geographic scope, reference period,
  recipient unit, currency, scale, and assertion. Do not combine funds, infer a
  regional total, reconcile values, or compute per-recipient amounts.
- Run `validate-package`, source-cell preservation, fact-load,
  consumer-artifact, raw-facts-boundary, ruff, and `git diff --check` checks.

