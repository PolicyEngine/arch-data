Refs #69.

## Source gap

Chronicle has no direct AVIQ or FAMIWAL post-2019 Walloon child-benefit package
that includes both caseload and expenditure. A parliamentary answer on an
unmerged branch is not the requested agency artifact and omits expenditure.

## Deterministic handoff

Retrieve the official AVIQ 2021 annual-report PDF through the AVIQ entry in
`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json`:

`https://www.aviq.be/sites/default/files/documents_pro/2022-10/rapport_annuel_AVIQ_2021.pdf`

## Acceptance criteria

- Pin the unchanged official PDF with exact URL, SHA-256, size, publication
  vintage, table/page references, and content-addressed raw-storage pointer.
- Parse the publisher PDF deterministically and add only source-cell-backed
  family-allowance caseload and expenditure facts with exact reference periods,
  units, and Walloon administrative/geographic scope.
- Keep rounded or ambiguous values as documented gaps; do not substitute the
  parliamentary answer, reconcile AVIQ to FAMIWAL, derive missing periods, or
  compute per-recipient amounts.
- Run `validate-package`, source-cell preservation, fact-load,
  consumer-artifact, raw-facts-boundary, ruff, and `git diff --check` checks.
