# Progress: chronicle#179 passive pass-through anchors

## State

In progress on branch `passive-pass-through-anchors`, based on the pre-fetched
`origin/main` commit `2d2c6d8`. Work is offline in
`.claude/worktrees/passive-179`.

## Done

- Read the applicable repository instructions in `AGENTS.md` and the parent
  `CLAUDE.md`.
- Confirmed that the existing `irs_soi.table_1_4` package already pins the
  supplied TY2023 workbook, so this task will extend that package rather than
  duplicate it.
- Began mapping record-set, fact, provenance, source-identity, test, and
  changelog conventions.

## Next

- Finish source/convention inspection and confirm all requested source cells.
- Add Form 8960 TY2023 amount and count facts plus the line 4 arithmetic test.
- Extend Table 1.4 with Schedule E entity income/loss returns and amounts by AGI
  class.
- Run the repository's deterministic, governance, boundary, formatting, and
  unit checks; record results and consumer concept IDs in the final output.
