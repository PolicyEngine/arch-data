# Lane C5 progress

## State

- Branch: `be-2025-vintages` from `origin/main` at `5c15bfd`.
- Worktree inputs are staged under `.lane-raw/` and must remain uncommitted.
- FPB and Statbel 2025 implementations are complete and validated; Eurostat
  vintage packages are prepared for the next commit.
- The requested staged C2 report is absent, but root `LANE_C2_REPORT.md` is byte-identical
  to the sibling lane's staged copy (SHA-256 `4590e0dc...50f06e7`) and is the pattern used.

## Done

- Read the repository Chronicle boundary rules in `AGENTS.md`.
- Read `.lane-raw/SOURCES.md` and confirmed all five named publisher artifacts are present.
- Confirmed the worktree is otherwise clean apart from `.lane-raw/` and the shared `.venv` link.
- Verified all five staged artifact SHA-256 pins exactly.
- Mapped FPB workbook cells: 990 facts across T01/T06/T07/T11/T17/T24, with
  2022–2025 observations and 2026–2031 `source_projection` facts.
- Confirmed PDF boundary evidence: printed page 19 calls 2026 the first projection year;
  annex table units appear on printed pages 45, 48, 49, 53, 58, and 65.
- Chosen Eurostat layout: two vintage-specific source-package aliases share new manifest
  entries, preserving the prior package YAMLs, raw bytes, and fact outputs unchanged.
- Reproduced the Statbel curator logic: 18 NUTS1 × sex × age-band cells totaling 11,825,551.
- Added the hash-pinned FPB workbook and publication PDF plus the
  `fpb-economic-outlook-2026-2031-june-2026` package alias.
- Built 990 line-specific publisher facts (99 per year): 396 observations for
  2022–2025 and 594 `source_projection` facts for 2026–2031.
- Passed FPB `validate-package` and `build-suite`: 990 facts, full cell lineage,
  zero acceptance errors, and pinned 2025 cells 320578 / 77771 / 5602 million euro.
- Re-ran the Statbel 2026 curator logic on the 2025 ZIP and added the hash-pinned
  raw capture plus its deterministic 18-row curated CSV.
- Passed Statbel 2025 `validate-package` and `build-suite`: 18 facts totaling
  11,825,551, 66 constraints, full lineage, and zero acceptance errors.

## Next

- Add and validate the two Eurostat vintage packages without duplicating overlap facts.
- Extend Belgium tests, run full requested validation, and write `LANE_C5_REPORT.md`.
