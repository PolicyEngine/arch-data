Refs #69.

## Source gap

The current `opgroeien-groeipakket-caseload-2025` package is a curated extract
of heterogeneous headline figures. It does not pin a native publisher export,
does not include expenditure, and labels the whole administrative scope as
NUTS BE2 without publisher-byte evidence that every row has that geography.

Opgroeien's official `Cijfers op maat` page embeds separate Power BI reports
for Groeipakket caseload and budget/expenditure. The current execution
environment cannot retrieve their native data exports. Rendered dashboard
cards, screenshots, accessibility text, and manual transcription are not
acceptable Chronicle artifacts.

## Deterministic handoff

Use the two Opgroeien entries in
`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json`:

- official landing page:
  `https://www.opgroeien.be/kennis/cijfers-en-onderzoek/groeipakket/cijfers-op-maat`
- caseload report ID and exact native-export procedure recorded in the handoff;
- expenditure report ID and exact native-export procedure recorded in the
  handoff.

## Acceptance criteria

- Pin unchanged native publisher export bytes with URL, SHA-256, size, report
  vintage/update timestamp, visual name, active filters, headers, and
  content-addressed raw-storage pointer.
- Preserve each publisher reference period, recipient unit, component,
  currency/scale, and administrative/geographic scope exactly.
- Add post-2019 caseload and expenditure facts only for cells that resolve from
  the pinned export. Do not force administrative coverage to BE2 without
  evidence in the export.
- Do not calculate annual totals, per-recipient amounts, reconciliations,
  imputed periods, take-up, or model bindings.
- Run `validate-package`, source-cell preservation, fact-load,
  consumer-artifact, raw-facts-boundary, ruff, and `git diff --check` checks.

