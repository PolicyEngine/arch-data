Refs #69.

## Source gap

Chronicle has no direct post-2019 German-speaking Community child-benefit
caseload and expenditure package. The official Ostbelgien Statistik page
returns HTTP 403 to automated retrieval in the current environment. Search
snippets and the manual HTML transcription on an unmerged branch are not
publisher artifacts and must not become facts.

## Deterministic handoff

Use the Ostbelgien entry in
`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json` to capture the raw official page
response/source from:

`https://ostbelgienstatistik.be/desktopdefault.aspx/tabid-3748/6766_read-39090/`

If the values are injected from a separate official endpoint, replace the
handoff with that endpoint and pin its native response rather than saving an
incomplete HTML shell.

## Acceptance criteria

- Pin unchanged publisher response bytes with URL, retrieval details,
  SHA-256, size, page update timestamp, and content-addressed raw-storage
  pointer.
- Verify the bytes themselves contain exact table labels, periods, units,
  caseload, and expenditure before authoring any facts.
- Preserve the German-speaking Community scope exactly. Do not use search
  snippets, OCR, screenshots, manual transcription, imputation, or derived
  amounts.
- Run `validate-package`, source-cell preservation, fact-load,
  consumer-artifact, raw-facts-boundary, ruff, and `git diff --check` checks.
