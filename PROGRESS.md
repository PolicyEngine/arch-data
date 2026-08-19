# Progress: chronicle#179 passive pass-through anchors

## State

Form 8960 ingestion is implemented and locally validated. Table 1.4 Schedule E
entity measures are next. Work remains offline on branch
`passive-pass-through-anchors` in `.claude/worktrees/passive-179`.

## Done

- Read the applicable repository instructions in `AGENTS.md` and the parent
  `CLAUDE.md`.
- Confirmed that the existing `irs_soi.table_1_4` package already pins the
  supplied TY2023 workbook, so this task will extend that package rather than
  duplicate it.
- Mapped record-set, fact, provenance, source-identity, test, and changelog
  conventions; the repository has no Makefile or established changelog file.
- Added `soi-form-8960-2023`: 10 tax-year record sets and 20 administrative
  facts (return count plus USD amount for each requested line), pinned to
  Publication 4801 (Rev. 6-2026) and its supervisor-verified transcripts.
- Added source-level tests for every Form 8960 value, unit, provenance pin, and
  the published one-$1,000 line 4 rounding residual.
- Passed the focused tests (10 tests), source-package validation, and the full
  Form 8960 source-suite build (20 consumer facts; all reports valid).

## Next

- Extend Table 1.4 with Schedule E entity income/loss returns and amounts by AGI
  class.
- Update bundle and package fixture counts for the 180 net-new facts.
- Run the repository's deterministic, governance, boundary, formatting, and
  unit checks; record results and consumer concept IDs in the final output.
