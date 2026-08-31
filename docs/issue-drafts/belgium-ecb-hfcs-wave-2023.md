Refs #69.

## Source gap

Chronicle has no official Belgium HFCS net-wealth/distribution/component
aggregate package. No ECB wave-2023 workbook bytes or checksum are present on
current main or in the inspected branches, so values must not be copied from
the rendered statistical tables.

## Deterministic handoff

Retrieve the official ECB HFCS Wave 2023 statistical-tables ZIP, version 5.0
(June 2026), through the ECB entry in
`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json`:

`https://www.ecb.europa.eu/home/pdf/research/hfcn/HFCS_Statistical_Tables_Wave_2023_June_2026.zip`

## Acceptance criteria

- Pin the unchanged outer ZIP with URL, SHA-256, size, ECB version/vintage, and
  content-addressed raw-storage pointer. List archive members deterministically
  and pin each selected native workbook member separately.
- Inspect workbook sheet names, row/column labels, units, weighting labels, and
  cells before authoring. Belgium asset/liability values refer to interview
  time during January-December 2023; income variables refer to 2022.
- Add only ECB-published Belgium net-wealth means/medians/quantiles,
  distribution shares/ratios, and component aggregates with exact source-cell
  lineage and `survey_aggregate` provenance.
- Do not interpolate quantiles, derive components or totals, reconcile to NBB,
  age values, or add model/target bindings.
- Run `validate-package`, source-cell preservation, fact-load,
  consumer-artifact, raw-facts-boundary, ruff, and `git diff --check` checks.

