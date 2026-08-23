# Lane C4 — JRC EUROMOD-BE Annex 3 model columns

## Outcome

This lane extends the JRC EUROMOD-BE 2025 comparator from 41 to 90 source
facts by appending 49 publisher cells:

- 26 `validation.series = euromod` model-output rows;
- 23 `validation.series = ratio` rows, only where the report prints the
  relevant comparator ratio;
- no new External or SILC facts, no imputation, alignment, reconciliation, or
  PolicyEngine-computed values.

All 49 additions are `provenance_class: model_output` and validation-only.
The package now contains 32 EUROMOD rows, 29 ratio rows, 27 External rows, and
2 SILC rows. Provenance totals are 63 model outputs, 25 administrative facts,
and 2 survey aggregates.

The explicit `yse` amount instruction is represented by the 2021–2023 A3.2
EUROMOD cells even though their External and ratio cells are blank. All other
EUROMOD/ratio additions use the same period as a packaged External or SILC
fact. The original CSV header plus 41 rows remains byte-for-byte identical to
the C2 artifact: SHA-256
`2ef69251a72caaab042706c77143fa4f86dde2f800747ebb421b5f7b9a45e394`.

## Artifact pins

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| Cached JRC PDF | `7c4b0aa4f1f96161e1ce7e4ad300a3fa56cdad7241f82fb650eeec03d30f087b` | 4,184,683 |
| C2 curated CSV prefix (header + 41 rows) | `2ef69251a72caaab042706c77143fa4f86dde2f800747ebb421b5f7b9a45e394` | 6,956 |
| Lane C4 curated CSV | `1258dc2a6dd76d3fcf5895c62d36229c03b9cc1c8fac5be49619cf7adbc1496d` | 15,198 |

The manifest declares, but this lane does not upload, the content-addressed
key:

`raw/belgium/jrc-euromod-be-baseline-statistics-2025/2025/1258dc2a6dd76d3fcf5895c62d36229c03b9cc1c8fac5be49619cf7adbc1496d/jrc_euromod_be_baseline_statistics_2025.csv`

## PDF extraction

The cached `pdfplumber` 0.11.10 interpreter and these file-page numbers were
used. Printed report pages are two lower than PDF file pages.

```sh
/Users/maxghenis/.cache/uv/archive-v0/HLlfXwC9DMcE0Q6gCdMwl/bin/python - <<'PY'
import pdfplumber

path = ".lane-raw/Y15_CR_BE_final.pdf"
pages = (114, 116, 120, 122, 127, 129)
with pdfplumber.open(path) as pdf:
    for number in pages:
        print(f"=== PDF PAGE {number} ===")
        print(
            pdf.pages[number - 1].extract_text(
                x_tolerance=2,
                y_tolerance=3,
            )
            or ""
        )
PY
```

| Annex table | Printed report page | PDF file page |
|---|---:|---:|
| A3.1 recipient counts | 112 | 114 |
| A3.2 annual amounts | 114 | 116 |
| A3.4 direct taxes and SIC amounts | 118 | 120 |
| A3.5 benefit recipient counts | 120 | 122 |
| A3.6 benefit annual amounts | 125 | 127 |
| A3.6 combined-pension continuation | 127 | 129 |

For administrative facts, each ratio below is the report's rightmost
EUROMOD/External ratio. For the A3.5 `poa` and `psu` survey facts, it is the
middle EUROMOD/SILC ratio because the External cells are blank.

## New rows

Values below are verbatim printed cells before the package's declared scaling.
Count records use `unit: count` with `value_scale: 1000`; amount records use
`unit: eur` with `value_scale: 1000000`; ratios use `unit: ratio` and
`value_scale: 1`.

| Record id | Period | Printed value | Record unit / printed table unit | Report / PDF page |
|---|---:|---:|---|---|
| `a3_5_income_support_euromod_2021` | 2021 | 133 | count (printed thousands) | 120 / PDF 122 |
| `a3_5_unemployment_benefits_euromod_2021` | 2021 | 1,930 | count (printed thousands) | 120 / PDF 122 |
| `a3_1_self_employment_income_euromod_2022` | 2022 | 851 | count (printed thousands) | 112 / PDF 114 |
| `a3_5_income_support_euromod_2022` | 2022 | 159 | count (printed thousands) | 120 / PDF 122 |
| `a3_5_unemployment_benefits_euromod_2022` | 2022 | 1,930 | count (printed thousands) | 120 / PDF 122 |
| `a3_5_old_age_pension_euromod_2022` | 2022 | 2,273 | count (printed thousands) | 120 / PDF 122 |
| `a3_5_survivor_pension_euromod_2022` | 2022 | 79 | count (printed thousands) | 120 / PDF 122 |
| `a3_2_self_employment_income_euromod_2021` | 2021 | 20,965 | EUR (printed millions) | 114 / PDF 116 |
| `a3_2_employment_income_euromod_2021` | 2021 | 197,874 | EUR (printed millions) | 114 / PDF 116 |
| `a3_4_capital_income_tax_euromod_2021` | 2021 | 1,412 | EUR (printed millions) | 118 / PDF 120 |
| `a3_6_income_support_euromod_2021` | 2021 | 1,055 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_income_support_elderly_euromod_2021` | 2021 | 0 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_child_benefits_euromod_2021` | 2021 | 6,885 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_unemployment_benefits_euromod_2021` | 2021 | 10,416 | EUR (printed millions) | 125 / PDF 127 |
| `a3_2_self_employment_income_euromod_2022` | 2022 | 21,981 | EUR (printed millions) | 114 / PDF 116 |
| `a3_2_employment_income_euromod_2022` | 2022 | 212,332 | EUR (printed millions) | 114 / PDF 116 |
| `a3_4_capital_income_tax_euromod_2022` | 2022 | 1,646 | EUR (printed millions) | 118 / PDF 120 |
| `a3_6_income_support_euromod_2022` | 2022 | 1,242 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_income_support_elderly_euromod_2022` | 2022 | 0 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_child_benefits_euromod_2022` | 2022 | 7,160 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_unemployment_benefits_euromod_2022` | 2022 | 11,010 | EUR (printed millions) | 125 / PDF 127 |
| `a3_2_self_employment_income_euromod_2023` | 2023 | 23,764 | EUR (printed millions) | 114 / PDF 116 |
| `a3_2_employment_income_euromod_2023` | 2023 | 228,596 | EUR (printed millions) | 114 / PDF 116 |
| `a3_6_income_support_euromod_2023` | 2023 | 1,356 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_income_support_elderly_euromod_2023` | 2023 | 0 | EUR (printed millions) | 125 / PDF 127 |
| `a3_6_old_age_survivor_pension_euromod_2023` | 2023 | 62,827 | EUR (printed millions) | 127 / PDF 129 |
| `a3_5_income_support_ratio_2021` | 2021 | 0.62 | ratio | 120 / PDF 122 |
| `a3_5_unemployment_benefits_ratio_2021` | 2021 | 1.95 | ratio | 120 / PDF 122 |
| `a3_2_employment_income_ratio_2021` | 2021 | 1.35 | ratio | 114 / PDF 116 |
| `a3_4_capital_income_tax_ratio_2021` | 2021 | 0.40 | ratio | 118 / PDF 120 |
| `a3_6_income_support_ratio_2021` | 2021 | 0.64 | ratio | 125 / PDF 127 |
| `a3_6_income_support_elderly_ratio_2021` | 2021 | 0.00 | ratio | 125 / PDF 127 |
| `a3_6_child_benefits_ratio_2021` | 2021 | 0.94 | ratio | 125 / PDF 127 |
| `a3_6_unemployment_benefits_ratio_2021` | 2021 | 1.27 | ratio | 125 / PDF 127 |
| `a3_1_self_employment_income_ratio_2022` | 2022 | 0.68 | ratio | 112 / PDF 114 |
| `a3_5_income_support_ratio_2022` | 2022 | 0.66 | ratio | 120 / PDF 122 |
| `a3_5_unemployment_benefits_ratio_2022` | 2022 | 2.37 | ratio | 120 / PDF 122 |
| `a3_5_old_age_pension_ratio_2022` | 2022 | 1.00 | ratio | 120 / PDF 122 |
| `a3_5_survivor_pension_ratio_2022` | 2022 | 1.00 | ratio | 120 / PDF 122 |
| `a3_2_employment_income_ratio_2022` | 2022 | 1.31 | ratio | 114 / PDF 116 |
| `a3_4_capital_income_tax_ratio_2022` | 2022 | 0.40 | ratio | 118 / PDF 120 |
| `a3_6_income_support_ratio_2022` | 2022 | 0.69 | ratio | 125 / PDF 127 |
| `a3_6_income_support_elderly_ratio_2022` | 2022 | 0.00 | ratio | 125 / PDF 127 |
| `a3_6_child_benefits_ratio_2022` | 2022 | 0.93 | ratio | 125 / PDF 127 |
| `a3_6_unemployment_benefits_ratio_2022` | 2022 | 1.65 | ratio | 125 / PDF 127 |
| `a3_2_employment_income_ratio_2023` | 2023 | 1.30 | ratio | 114 / PDF 116 |
| `a3_6_income_support_ratio_2023` | 2023 | 0.66 | ratio | 125 / PDF 127 |
| `a3_6_income_support_elderly_ratio_2023` | 2023 | 0.00 | ratio | 125 / PDF 127 |
| `a3_6_old_age_survivor_pension_ratio_2023` | 2023 | 0.97 | ratio | 127 / PDF 129 |

## Blanks and exclusions

- Every one of C2's 21 appended External facts and two appended SILC facts has
  a nonblank same-period EUROMOD counterpart and a printed relevant ratio.
  The documented missing-counterpart set is therefore empty.
- A3.2 `yse` prints EUROMOD amounts of 20,965, 21,981, and 23,764 million for
  2021–2023. Its External and ratio cells are `NaN` in every year, so only
  the explicitly requested EUROMOD rows are present.
- A3.5 `poa` and `psu` have blank External and External-ratio cells. Their
  packaged 2022 comparators are SILC, and the printed EUROMOD/SILC ratios are
  1.00.
- A3.6 `bsaoa_s` EUROMOD cells are printed zeroes and its ratios are printed
  `0.00`; these are values, not blanks.
- A3.4 `tinkt_s` External and External-ratio cells are blank for 2023–2024.
  The unpaired 2023/2024 EUROMOD cells are absent.
- A3.5 `bsa_s` and `bun` External and External-ratio cells are blank for
  2023–2024. Requested A3.6 rows have blank 2024 External/ratio cells.
- A3.1 `yse` has a populated 2021 External cell, and A3.6
  `il_ext_poapsu` has populated 2021/2022 External cells, but those periods
  are not facts in the package. Under the same-period rule, this lane does not
  expand their External scope; the requested combined-pension pair remains
  2023 only.
- No blank cell was converted to zero and no ratio was calculated from the
  printed values.

## Package structure and source boundary

The 18 record sets separate recipient counts from annual amounts and also
separate their ratios:

- person/count records preserve the table's thousands with scale 1,000;
- government/EUR records preserve the table's millions with scale 1,000,000;
- person recipient-count ratios and government amount ratios use distinct
  concepts so identically named `bsa_s` and `bun` metrics do not collide;
- every EUROMOD and ratio row is a publisher model output and validation-only.

Chronicle stores only JRC's published cells. It performs no aging, period
alignment, target activation, support selection, or solver construction.

## Validation commands and tails

```sh
.venv/bin/python -m chronicle.harness validate-package \
  jrc-euromod-be-baseline-statistics-2025 --year 2025

JRC_C4_SUITE_DIR=$(mktemp -d /tmp/chronicle-c4-jrc.XXXXXX)
.venv/bin/python -m chronicle.harness build-suite \
  jrc-euromod-be-baseline-statistics-2025 --year 2025 \
  --out "$JRC_C4_SUITE_DIR" --replace
.venv/bin/python -m chronicle.harness validate-source-rows \
  --input "$JRC_C4_SUITE_DIR/source_rows.jsonl"
.venv/bin/python -m chronicle.harness validate-source-cells \
  --input "$JRC_C4_SUITE_DIR/source_cells.jsonl"
.venv/bin/python -m chronicle.harness validate-facts \
  --input "$JRC_C4_SUITE_DIR/facts.jsonl"

.venv/bin/python -m pytest -q tests/test_belgium_targets.py
.venv/bin/python -m pytest -q
git diff --check
```

| Check | Tail / result |
|---|---|
| `validate-package` | valid; 18 record sets, 90 selected rows, 18 measures, 90 source records, 18 source regions; 0 errors, 0 warnings |
| `build-suite` | valid; 90 source rows, 637 source cells, 90 facts, 90 consumer facts, 180 constraints, lineage 1.0, 0 acceptance errors |
| source-row validator | valid; 90 rows; 0 errors, 0 warnings |
| source-cell validator | valid; 637 cells; 0 errors, 0 warnings |
| fact validator | valid; 90 facts; 25 administrative, 63 model-output, 2 survey-aggregate; 0 errors, 0 warnings |
| Belgium tests | 13 passed; 12 warnings |
| repository tests | 693 passed, 1 skipped, 14 warnings in 1,056.53s (0:17:36) |
| `git diff --check` | clean |

The build acceptance report has the expected single nonfatal
`concept_alignment_validation_skipped` warning because no Axiom CLI command
is configured. Evidence presence, row semantics, artifact R2 declaration,
selectors, lineage, and all other acceptance checks pass.

## Commit list

| Commit | Purpose |
|---|---|
| `b12bfde` | Branch base: merge PR #190, including C2 |
| `7a110c8` | Append JRC model/ratio cells, extend selectors/tests, and add the initial report |
| local report-only follow-up, `Finalize Lane C4 validation report` | Record the final 693-test pass and clean-diff audit |

No push, stash operation, R2 upload, or network access was performed by this
Codex session. During the final audit, both the local branch and the
`origin/jrc-euromod-columns` remote-tracking ref already pointed to `7a110c8`;
the report-only follow-up remains local.

LANE C4 DONE
