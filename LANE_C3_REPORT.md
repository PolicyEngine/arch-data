# Lane C3 — Statbel fiscal income distribution 2023

## Outcome and source-boundary decisions

This lane adds source package `statbel-fiscal-income-distribution-2023` for
Statbel's *Fiscale statistiek van de inkomsten*, income year 2023 and assessment
year 2024. The source is IPCAL/SPF Finances administrative tax-return data, not
a survey. The package contains 14,600 publisher-cell facts: 3,650 each for
Belgium, the Flemish Region (BE2), the Walloon Region (BE3), and the Brussels
Capital Region (BE1). All facts are `assertion: observation` with
`provenance_class: administrative` and `entity: return`.

All eight NL workbooks are preserved verbatim and hash-pinned. Chronicle's
current declarative source-package loader has one primary parsed artifact, so a
deterministic curator creates one complete 1,131-row CSV from A.1, B.1, B.3,
B.4, and B.5. Each selected fact cell retains its workbook, worksheet, row,
cell address, and exact XLSX XML `<v>` numeric lexeme. Euro facts are represented
to cents directly from that lexeme using `Decimal` and `ROUND_HALF_UP`. Ratio
facts use the publisher-decoded decimal spelling while retaining the exact XML
binary-double tail in provenance. The curator does not create aggregates,
reconcile sources, age values, impute values, align periods, or construct
targets. Its sum checks are validation assertions only and are not stored as
facts.

The selected publisher tables are:

- A.1: all six four-column components, their total rows, and all 101 published
  €1,000 income classes. The A.1 Home overview's zero-income declaration count
  is a separate fact.
- B.1: the total, deciles 01–10, top-decile percentiles 091–100, and every
  populated published upper bound. Decile and percentile rows are separate
  record sets so the two overlapping partitions cannot be mistaken for one
  additive detail set.
- B.3: declaration/professional-income category by total/decile.
- B.4: declaration type by exact published age category and decile.
- B.5: declaration type by decile and exact published dependants category.
- A.2, A.3, and B.2 are retained as raw source captures but do not emit facts in
  this lane, as allowed by the task priority.

The package records that declarations are tax-return units: a joint declaration
is counted once. A.1 and B.1/B.3/B.4/B.5 exclude declarations with zero total
net taxable income; Statbel reports the excluded 523,770 Belgium declarations
separately in A.1 Home. Total net taxable income uses the same concept as the
existing commune package. B.1 total tax is enrolled tax, including the
publisher's negative low-decile cells caused by refundable credits. Published
decile and percentile bounds are facts; blank open-ended bounds are omitted and
never imputed.

### Publisher inconsistencies preserved, not reconciled

The requested exact national-to-commune tie cannot be asserted from the staged
and existing publisher-backed facts:

| Publisher-backed value | EUR |
|---|---:|
| A.1 Belgium total net taxable income | 274,707,991,587.37 |
| B.1 Belgium total net taxable income | 274,707,991,587.39 |
| Sum of 565 existing Statbel commune facts | 274,707,991,587.82 |

The existing commune cells therefore sum €0.45 above A.1, while B.1 is €0.02
above A.1. The test pins the €0.45 residual rather than manufacturing the
requested equality. Chronicle preserves all three publisher-backed values.

Three other source details are deliberately left visible:

- B.4 literally labels its first category `Minder dan 24 jaar`, but its
  declaration and amount cells equal Statbel Home's `<15` plus `15–24` bins,
  i.e. the publisher data run through age 24. Chronicle retains the literal
  category and does not impose a numeric age boundary.
- National A.1 total professional income is €269,350,984,468.67 from the exact
  XML lexeme `269350984468.67499`; its 101 independently rounded class cells sum
  €0.01 higher. Neither side is reconciled.
- Exact age cells such as 25–29 and 30–34 remain distinct. No synthetic 25–34
  fact or other downstream band is stored.

## Artifact pins

| Artifact | SHA-256 | Bytes | Use |
|---|---|---:|---|
| `statbel_fiscal_income_distribution_2023.csv` | `866a29188f3a2e343c89a16c134a9543c50c3ca75041cdecc814239fe4cddff0` | 1,383,565 | Primary deterministic cell extract |
| `fisc2023_A_1_NL.xlsx` | `b51711ed09bc4339bd331785c533d7d728c36c7e4f2e3eb63f91537838932f96` | 616,745 | Verbatim source capture; facts |
| `fisc2023_A_2_NL.xlsx` | `b5e4fc0ad47101bdf3664237020286824a09025ae38021d010448623d57ef683` | 411,403 | Verbatim source capture |
| `fisc2023_A_3_NL.xlsx` | `e2f10edd92c55c010a1ed0d2f0fd8757f39114ad2ef1da944b745cada9fc011a` | 361,545 | Verbatim source capture |
| `fisc2023_B_1_NL.xlsx` | `b5dd48ed14cfadd2aa65addd49828387fc70d517da87847608f1cf66eb516c38` | 326,306 | Verbatim source capture; facts |
| `fisc2023_B_2_NL.xlsx` | `4a80321f8d40478d183c6950defde45709619f9842bca45cfc6be26354e70224` | 451,903 | Verbatim source capture |
| `fisc2023_B_3_NL.xlsx` | `2ede83e4f813c7f7675281996ca2a1815e0dc1db1c219600370f2c26dfa57198` | 82,136 | Verbatim source capture; facts |
| `fisc2023_B_4_NL.xlsx` | `7b00e340c74c7de4d2cb1fa5ea2f86fe9bd15e9a259d98a4af92fc4fd322f660` | 101,224 | Verbatim source capture; facts |
| `fisc2023_B_5_NL.xlsx` | `ff84f65475e19037a82cd8f504ee1022372daa379abc8820cecbb4b1184ee3d4` | 360,249 | Verbatim source capture; facts |

The final generated metadata pins are:

| Generated file | SHA-256 |
|---|---|
| `source_package.yaml` | `9ce0e93f1aff29057b2e96fd0a255ed00e4f0ae6271067a264429a2cd04f610b` |
| `manifest.yaml` | `612a5debce569635dfabc7df48747c938388ad4e624f32eb02de6f2b0d7ac1e5` |

All nine manifest entries declare metadata-only R2 pointers under:

```text
raw/belgium/statbel-fiscal-income-distribution-2023/2023/<sha256>/<filename>
```

No upload occurred in this lane. A handoff caveat matters: the standard
`publish-raw` path builder derives its year segment from each manifest mapping
key, so the `A_1`…`B_5` entries would otherwise be written below `/A_1/`…`/B_5/`.
Fable must upload these captures explicitly to the manifest-declared `/2023/`
keys, or use an uploader that honors the declared keys.

## Fact and record-set inventory

National record sets are emitted first, followed by the same clean surface for
BE2, BE3, and BE1. Each geography has 14 record sets and 3,650 facts:

| Publisher surface | Record sets per geography | Facts per geography | Facts, all geographies |
|---|---:|---:|---:|
| A.1 Home zero-income declarations | 1 | 1 | 4 |
| A.1 six components by income class | 6 | 2,448 | 9,792 |
| B.1 decile values | 1 | 99 | 396 |
| B.1 top-decile percentile values | 1 | 90 | 360 |
| B.1 decile bounds | 1 | 9 | 36 |
| B.1 top-decile percentile bounds | 1 | 9 | 36 |
| B.3 declaration/professional-income categories | 1 | 154 | 616 |
| B.4 declaration type × age × decile | 1 | 600 | 2,400 |
| B.5 declaration type × decile × dependants | 1 | 240 | 960 |
| **Total** | **14** | **3,650** | **14,600** |

The package validator reports 56 record sets, 4,596 selected row/record-set
positions, 204 measure declarations, 14,600 source records, and 56 source
regions. The primary CSV full-row parser emits 1,131 source rows and 100,748
source cells. An independent exhaustive audit established the bijection:
14,600 selected XLSX numeric cells = 14,600 curated provenance mappings =
14,600 unique facts.

## For the target surface

Chronicle does not choose bands or activate targets. A Microcosm-BE v0.5 target
harvest can select and sum only the following publisher-cell families, with the
exact desired grouping chosen downstream by Fable/Max:

- Income-class masses and return counts:
  `statbel.fiscal_income_distribution.income_year2023.<component>.by_income_class_eur1000.<class>.<measure>`.
  Components are `taxable_income`, `professional_income`,
  `immovable_property_income`, `capital_and_movable_property_income`,
  `miscellaneous_income`, and `deductible_expenditures`; classes run from
  `class_under_1`, `class_1_2`, …, `class_99_100`, to `class_100_plus`.
  Candidate additive measures are `.declarations` and the component's `*_eur`
  amount. The publisher `total` and ratio/share facts are controls, not extra
  class cells to add. Zero-income returns are available separately under
  `...zero_income_declarations.total.declarations`.
- Decile tax and income masses:
  `...income_year2023.by_decile.decile_01.<measure>` through
  `decile_10.<measure>`, including `total_tax_eur`, `taxable_income_eur`,
  `payable_tax_eur`, and `tax_refund_eur`. Published `upper_bound_eur` exists for
  closed decile bounds. Negative low-decile `total_tax_eur` values must retain
  their signs.
- Top-decile detail:
  `...by_decile.percentile_091.<measure>` through
  `percentile_100.<measure>`, with published bounds where present. These ten
  percentile masses partition decile 10; a harvest must choose either decile 10
  or its percentile decomposition, never both.
- Declaration-category counts:
  `...declaration_type_professional_income.by_decile.<category>.<rank>.declarations`,
  `...declaration_type_age.by_decile.<declaration_type>.<exact_age>.<decile>.declarations`,
  and
  `...declaration_type_dependants.by_decile.<declaration_type>.<decile>.<dependants>.declarations`.
  B.3/B.4 total rows and their detail rows overlap; downstream selection must
  choose the intended partition and must not synthesize new Chronicle facts.
- Regional counterparts insert `.regions.be2`, `.regions.be3`, or
  `.regions.be1` immediately after `income_year2023`. Whether a target uses the
  national fact or regional facts is a downstream selection decision.

Any class-band choice, cross-source reconciliation, aging, imputation, period
alignment, support-aware activation, or solver-ready target construction belongs
to Microcosm, not Chronicle.

## Command ledger

All commands ran from
`/Users/maxghenis/TheAxiomFoundation/_cape-prep/chronicle-be2` with network
disabled. `.lane-raw/` remained an uncommitted staging directory.

### C1 — pattern, workbook, and artifact inspection

```sh
git show origin/be-national-accounts-packages:LANE_C2_REPORT.md
shasum -a 256 .lane-raw/fisc2023_{A_1,A_2,A_3,B_1,B_2,B_3,B_4,B_5}_NL.xlsx
wc -c .lane-raw/fisc2023_{A_1,A_2,A_3,B_1,B_2,B_3,B_4,B_5}_NL.xlsx
```

The workbooks were also inspected with read-only `openpyxl` and ZIP/XML probes.
All contain `Home`, `Schema`, and `Metadata`; the geographic sheets selected are
`België`, `Vlaams Gewest`, `Waals Gewest`, and
`Brussels Hoofdst. Gewest`. No selected workbook cell contains a formula.

### C2 — deterministic curator and generated pins

```sh
.venv/bin/python packages/statbel/fiscal_income_distribution_2023/build_package.py
ruff format packages/statbel/fiscal_income_distribution_2023/build_package.py \
  tests/test_belgium_targets.py chronicle/source_package.py
ruff check packages/statbel/fiscal_income_distribution_2023/build_package.py \
  tests/test_belgium_targets.py chronicle/source_package.py
shasum -a 256 \
  packages/statbel/fiscal_income_distribution_2023/source_package.yaml \
  db/data/statbel/fiscal_income_distribution_2023/manifest.yaml \
  db/data/statbel/fiscal_income_distribution_2023/statbel_fiscal_income_distribution_2023.csv
```

The final curator output was `csv_rows=1131`, `fact_cells=14600`, and
`record_sets=56`. A repeated run produced the same generated hashes.

### C3 — manifest inventory and package validation

```sh
.venv/bin/python -m chronicle.cli inventory-artifacts \
  --root db/data/statbel/fiscal_income_distribution_2023
.venv/bin/python -m chronicle.cli validate-package \
  statbel-fiscal-income-distribution-2023 --year 2023
```

### C4 — full package build suite

```sh
C3_SUITE_DIR=$(mktemp -d /tmp/chronicle-c3-statbel.XXXXXX)
.venv/bin/python -m chronicle.cli build-suite \
  statbel-fiscal-income-distribution-2023 \
  --year 2023 --out "$C3_SUITE_DIR" --replace
```

The final output directory was `/tmp/chronicle-c3-statbel.c4fel3`.

### C5 — emitted row, cell, and fact validators

```sh
.venv/bin/python -m chronicle.cli validate-source-rows \
  --input /tmp/chronicle-c3-statbel.c4fel3/source_rows.jsonl
.venv/bin/python -m chronicle.cli validate-source-cells \
  --input /tmp/chronicle-c3-statbel.c4fel3/source_cells.jsonl
.venv/bin/python -m chronicle.cli validate-facts \
  --input /tmp/chronicle-c3-statbel.c4fel3/facts.jsonl
```

### C6 — focused and repository tests

```sh
.venv/bin/python -m pytest -q \
  tests/test_belgium_targets.py tests/test_source_package_alias_drift.py
.venv/bin/python -m pytest -q \
  tests/test_chronicle_bundle.py::test_build_bundle_writes_merged_consumer_contract
.venv/bin/python -m pytest -q
```

The first repository run exposed only stale merged-bundle snapshot counts after
the new aliased package was automatically included (`1 failed, 697 passed, 1
skipped`). After updating those expectations, the isolated bundle test passed
in 806.57 seconds and the repeated full repository run passed.

### C7 — final diff and branch checks

```sh
git diff --check
git status --short --branch
git branch --show-current
```

## Validation output

| Check | Result |
|---|---|
| Artifact inventory | valid; 1 manifest, 9 artifacts, 9 R2 links, 0 missing files, 0 checksum mismatches |
| Package structure | valid; 56 record sets, 4,596 selected positions, 204 measures, 14,600 source records, 56 regions; 0 errors, 0 warnings |
| Build suite | valid; 1,131 rows, 100,748 cells, 14,600 facts and consumer facts, 70,080 constraints, lineage 1.0, 0 acceptance errors |
| Emitted row/cell/fact validators | all valid; 1,131 / 100,748 / 14,600; 0 errors and warnings |
| Focused tests | 26 passed, 12 dependency deprecation warnings in 3.03s |
| Isolated merged-bundle test | 1 passed, 13 dependency warnings in 806.57s |
| Repository tests | 698 passed, 1 skipped, 14 dependency warnings in 1,181.50s |
| `ledger-source-fidelity` judge | PASS; exhaustive 14,600-cell XLSX XML/CSV/fact bijection, exact raw lexemes and pins, correct cent/ratio representation, signs and IDs preserved |
| `ledger-boundary` judge | PASS; all facts are publisher administrative observations; no reconciliation, aging, alignment, imputation, target values, activation, or solver construction |

The acceptance report contains one non-fatal environmental warning:
`concept_alignment_validation_skipped`, because no Axiom CLI command is
configured. Evidence presence, concept resolution, row semantics, selectors,
lineage, facts, source regions, and all other package acceptance checks pass.

## Handoff

- Alias `statbel-fiscal-income-distribution-2023` resolves to
  `packages/statbel/fiscal_income_distribution_2023`.
- No push, network fetch, or R2 upload was performed.
- `.lane-raw/` and `.venv` remain untracked and are not part of the commit.
- Fable must honor the manifest-declared `/2023/<sha256>/` R2 keys when
  uploading all eight XLSX captures.
- Local commit message: `Add Statbel fiscal income distribution facts`.

LANE C3 DONE
