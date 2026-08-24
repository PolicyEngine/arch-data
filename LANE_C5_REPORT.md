# Lane C5 — Belgium 2025 source vintages

## Outcome and source-boundary decisions

This lane adds four source-backed package streams without storing any aging
factor, ratio, aligned value, calibration target, or PolicyEngine-computed
number:

- `fpb-economic-outlook-2026-2031-june-2026`: 990 publisher cells from the
  Federal Planning Bureau workbook, 99 for each year 2022–2031.
- `eurostat-gov-10a-taxag-2025`: 12 non-overlapping Belgian tax observations.
- `eurostat-spr-exp-func-2024`: nine non-overlapping Belgian ESSPROS function
  observations.
- `statbel-population-structure-2025`: 18 NUTS1 × sex × age-band population
  observations.

The prior Eurostat artifacts and package specifications are unchanged. Their
compact, sorted fact digests remain
`9db298bc05f4c7c1987367d4c31feb3b91d9ed70320f5d808898b978e85dd1a9`
for `gov_10a_taxag` and
`51768608362aaf40a16ee5be00c0ce849c5b37918975cc647bfde3fde1048266`
for `spr_exp_func`.

No source was fetched, no R2 object was uploaded, no push was made, and
`.lane-raw/` was not committed. Manifests record content-addressed R2 pointers
only.

## Artifact pins

| Artifact | SHA-256 | Bytes | Role |
|---|---|---:|---|
| `DATA_FOR_MLT_FR.xlsx` | `b51b41fbe6a3bd797a2fc9de648af66ec318e872b4d90200e2e8edbe9d26e56e` | 238,644 | FPB fact values |
| `FOR_MIDTERM_2631_13322_FR.pdf` | `3e4af4a5e6de8e24beab59a4e9d1c564bed8e429c887c45ca6fce99397754587` | 4,363,762 | FPB status boundary and units only |
| `gov_10a_taxag_2022_2025.json` | `da84f990bbf077162e4f43f64b94a28e376859075d831efdbadbe6aef3eda3ea` | 3,502 | Eurostat 2025 tax vintage |
| `spr_exp_func_2023_2024.json` | `91ea617950583ca0704863125f6bbb4292b0f12da95bffae422c5d406bd3d81d` | 3,892 | Eurostat 2024 ESSPROS vintage |
| `TF_SOC_POP_STRUCT_2025.zip` | `33910ea36437e39cfffd82ad82c759a2a8d1f2ab7662d45ce71c8ec9f336716c` | 2,551,751 | Verbatim Statbel source capture |
| `TF_SOC_POP_STRUCT_2025.txt` inside ZIP | `92182df1a3ea6fb5aa16a1008a24fc03a19b7d86a7af6004e154f16685890f85` | 103,971,495 | 466,822 publisher data rows |
| curated Statbel CSV | `2243aa1be7600535dba7e3d804ef482b6edac07c1e3813f4882c3bf4a34ff2ad` | 5,210 | Deterministic parsed artifact |

The unchanged prior Eurostat raw pins are
`5b4e4b99f0778855e164481a52eb16306ef4ac99afef874a91f22315bd0c472a`
(3,346 bytes) and
`24ad3c0115efef790ff8cb2ff8fb269d4ceb7de70ac3fad673ebd1340e4f650f`
(4,130 bytes).

## FPB annex

### Observation/projection boundary

The statistical-annex tables do not contain a footnote or visual marker that
separates observations from projections. The boundary instead appears in the
publication text: printed page 19 (PDF page 23) calls 2026 the “première année
de la période de projection”. Printed page 3 (PDF page 7) describes 2026–2031
in conditional language while describing 2024 and 2025 in the past tense.
Accordingly:

- 2022–2025: `assertion: observation` — 396 facts.
- 2026–2031: `assertion: source_projection` — 594 facts.

All 990 facts retain `provenance_class: model_output`, because the workbook is
the FPB's HERMES outlook output. The projection assertion is a publisher fact;
Chronicle does not turn it into a consumer forecast or aligned target.

The PDF unit captions are: T01, printed page 45/PDF 49, “Pourcentages de
variation en volume - sauf indication contraire”; T06, printed 48/PDF 52,
“Millions d'euros”; T07, printed 49/PDF 53, “En milliers (moyennes
annuelles)”; T11, printed 53/PDF 57, “Millions d'euros”; T17, printed 58/PDF
62, “Millions d'euros”; and T24, printed 65/PDF 69, “Millions d'euros”. T01's
employment-change row carries its own thousand-person indication, and the T07
unemployment-rate row is stored as percent.

### Fact inventory

| Workbook table | Selected rows/year | Years | Facts | Canonical scaling |
|---|---:|---:|---:|---|
| T01 Chiffres clés | 4 | 10 | 40 | percent unchanged; thousand-person change ×1,000 |
| T06 A.5 | 3 | 10 | 30 | million EUR ×1,000,000 |
| T07 B.1 | 10 | 10 | 100 | thousand persons ×1,000; rate unchanged |
| T11 C.1 | 20 | 10 | 200 | million EUR ×1,000,000 |
| T17 D.1 | 7 | 10 | 70 | million EUR ×1,000,000 |
| T24 D.7 | 55 | 10 | 550 | million EUR ×1,000,000 |
| **Total** | **99** | **10** | **990** | |

Each selected line is its own semantic concept, while the requested dotted
source-record surface is preserved. Source labels remain verbatim in
`layout.groupby_value_label`.

Both unemployment definitions are represented once: the standardized Eurostat
rate is T01 row 18 and the BFP rate `(VI)/(III)` is T07 row 18. T07's
“Pour mémoire” row 22 repeats the standardized Eurostat value byte-for-byte and
is not emitted a second time.

Pinned 2025 cells and compiled facts:

| Cell | Publisher value | Source record | Compiled value |
|---|---:|---|---:|
| `T11!AE8` | 320,578 million EUR | `fpb.economic_outlook_2026_2031.cy2025.household_account.compensation_of_employees.amount_meur` | 320,578,000,000 EUR |
| `T17!AE8` | 77,771 million EUR | `fpb.economic_outlook_2026_2031.cy2025.general_government_account.direct_taxes_households.amount_meur` | 77,771,000,000 EUR |
| `T24!AE20` | 5,602 million EUR | `fpb.economic_outlook_2026_2031.cy2025.social_benefits_detail.social_security_cash_unemployment.amount_meur` | 5,602,000,000 EUR |

## Eurostat vintage layout

The 2025 tax artifact is a complete 24-row cube. Its package emits 12 facts:
D51A_C1 and D51B_C2 for 2022–2025, plus D2, D5, D51, and D61 for 2025. The
existing package continues to own D2/D5/D51/D61 for 2023–2024. No coordinate
is emitted by both vintage packages. The six 2025 values are 75,518.7;
106,046.8; 103,324.3; 97,512.6; 75,791.1; and 26,308.0 million EUR for D2,
D5, D51, D61, D51A_C1, and D51B_C2 respectively.

The 2024 ESSPROS artifact is a complete 18-row cube. Its package emits only the
nine 2024 function observations; the prior package remains the sole owner of
the nine Belgian 2023 facts. The 2024 published total is 177,883.87 million
EUR. The eight functions are SICK 50,457.08; DIS 17,863.64; OLD 74,545.99;
SRV 9,262.13; FAM 13,162.10; UNE 5,734.36; HOU 1,306.85; and EXCL 5,551.71
million EUR.

All 21 compiled facts are observations. Eurostat's source statuses remain in
row lineage: 2025 tax rows are `p` and 2024 ESSPROS rows are `e`; no new
assertion class was invented for those flags.

## Statbel 2025 curator and population comparison

The exact curator invocation was:

```sh
.venv/bin/python curate_statbel_2025.py
```

It exited zero without stdout/stderr. The temporary script was removed after
execution; its exact body was:

```python
import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path

SOURCE = Path(".lane-raw/TF_SOC_POP_STRUCT_2025.zip")
OUTPUT = Path("db/data/statbel/population_structure_nuts1_2025/statbel_population_structure_nuts1_2025.csv")
SOURCE_URL = (
    "https://statbel.fgov.be/sites/default/files/files/opendata/"
    "bevolking%20naar%20woonplaats%2C%20nationaliteit%20burgelijke%20staat%20%2C%20leeftijd%20en%20geslacht/"
    "TF_SOC_POP_STRUCT_2025.zip"
)
REGIONS = (
    ("04000", "BE1", "Brussels Capital Region"),
    ("02000", "BE2", "Flemish Region"),
    ("03000", "BE3", "Walloon Region"),
)
SEXES = (("M", "male"), ("F", "female"))
AGE_BANDS = (
    ("0_17", "Aged 0 to 17", lambda age: age < 18),
    ("18_64", "Aged 18 to 64", lambda age: 18 <= age < 65),
    ("65_plus", "Aged 65 and over", lambda age: age >= 65),
)

totals = defaultdict(int)
with zipfile.ZipFile(SOURCE) as archive:
    with archive.open("TF_SOC_POP_STRUCT_2025.txt") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        for row in csv.DictReader(text, delimiter="|"):
            age = int(row["CD_AGE"])
            for age_band, _, contains in AGE_BANDS:
                if contains(age):
                    totals[(row["CD_RGN_REFNIS"], row["CD_SEX"], age_band)] += int(row["MS_POPULATION"])
                    break

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fieldnames = (
    "value_id", "period", "geography_id", "geography_level",
    "geography_name", "geography_vintage", "person.sex",
    "person.age_band", "age", "value", "source_url",
)
with OUTPUT.open("w", encoding="utf-8", newline="") as output_file:
    writer = csv.DictWriter(output_file, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for region_code, geography_id, geography_name in REGIONS:
        for sex_code, sex in SEXES:
            for age_band, age_label, _ in AGE_BANDS:
                writer.writerow({
                    "value_id": f"{geography_id.lower()}_{sex}_{age_band}",
                    "period": 2025,
                    "geography_id": geography_id,
                    "geography_level": "nuts1",
                    "geography_name": geography_name,
                    "geography_vintage": "NUTS_2024",
                    "person.sex": sex,
                    "person.age_band": age_band,
                    "age": age_label,
                    "value": totals[(region_code, sex_code, age_band)],
                    "source_url": SOURCE_URL,
                })
```

The exact raw-copy command was:

```sh
cp .lane-raw/TF_SOC_POP_STRUCT_2025.zip \
  db/data/statbel/population_structure_nuts1_2025/TF_SOC_POP_STRUCT_2025.zip
```

| NUTS1 / sex | 0–17 | 18–64 | 65+ |
|---|---:|---:|---:|
| BE1 male | 137,223 | 409,193 | 68,929 |
| BE1 female | 131,517 | 412,811 | 96,122 |
| BE2 male | 673,449 | 2,042,553 | 683,817 |
| BE2 female | 642,319 | 2,014,794 | 807,834 |
| BE3 male | 376,599 | 1,111,407 | 326,852 |
| BE3 female | 359,663 | 1,108,708 | 421,761 |

The 18 cells total 11,825,551 people. FPB T07's 2025 annual-average
population is 11,850,400. The difference is 24,849 people, or 0.209689% of the
FPB value. The regression declares a 0.25% ceiling. This is not presented as
pure rounding: Statbel is a 1 January stock and FPB is an annual average; the
tolerance simply records the observed cross-basis proximity without altering
either publisher fact.

## Validation tails

| Package | Package validation | Suite build tail |
|---|---|---|
| FPB outlook | 990 record sets, rows, measures, records, and regions; no errors | 990 facts; 7,622 cells; 396 observations; 594 source projections; lineage 1.0; acceptance errors 0 |
| Eurostat tax 2025 | 5 sets; 12 rows; 5 measures; 12 records; no errors | 12 facts; 24 source rows; 195 cells; 72 constraints; lineage 1.0; acceptance errors 0 |
| Eurostat ESSPROS 2024 | 1 set; 9 rows; 1 measure; 9 records; no errors | 9 facts; 18 source rows; 150 cells; 54 constraints; lineage 1.0; acceptance errors 0 |
| Statbel population 2025 | 1 set; 18 rows; 1 measure; 18 records; no errors | 18 facts; 18 source rows; 209 cells; 66 constraints; lineage 1.0; acceptance errors 0 |

All suite reports were `valid: true`. The only package-build warning was that
Axiom CLI concept validation was not configured; concept evidence, provenance,
raw R2 links, full-source parsing, and source lineage all passed.

Focused regressions:

```text
43 passed, 12 warnings in 3.60s
```

Merged bundle regression:

```text
1 passed, 13 warnings in 886.91s (0:14:46)
157,177 facts; 148 packages; 42 sources; 192 periods
0 aggregate-key duplicates; 117 pre-existing semantic duplicate keys
```

Warnings are upstream PyIceberg deprecations plus openpyxl's existing
header/footer parser warning. Ruff check and format-check passed.

### Chronicle judge reviews

- `ledger-source-fidelity`: **PASS**. An independent read-only review verified
  all five staged artifact pins, all FPB labels/cells/counts/scaling, Eurostat
  non-overlap and prior-output stability, an independent Statbel re-aggregation
  of all 466,822 source rows, and clean suite lineage. No correction required.
- `ledger-boundary`: **PASS**. An independent read-only review found no stored
  aging factor, ratio, reconciled/aligned value, imputation, target value,
  activation decision, or solver construct. The population comparison remains
  QA only and the target-surface section assigns every consumer operation to
  the consumer. No correction required.

## Command ledger

Commands ran from
`/Users/maxghenis/TheAxiomFoundation/_cape-prep/chronicle-be4` with network
disabled.

### C1 — pins

```sh
sha256sum \
  .lane-raw/DATA_FOR_MLT_FR.xlsx \
  .lane-raw/FOR_MIDTERM_2631_13322_FR.pdf \
  .lane-raw/gov_10a_taxag_2022_2025.json \
  .lane-raw/spr_exp_func_2023_2024.json \
  .lane-raw/TF_SOC_POP_STRUCT_2025.zip
```

### C2 — package validation

```sh
.venv/bin/python -m chronicle.harness validate-package fpb-economic-outlook-2026-2031-june-2026 --year 2026
.venv/bin/python -m chronicle.harness validate-package eurostat-gov-10a-taxag-2025 --year 2025
.venv/bin/python -m chronicle.harness validate-package eurostat-spr-exp-func-2024 --year 2024
.venv/bin/python -m chronicle.harness validate-package statbel-population-structure-2025 --year 2025
```

### C3 — suite builds

```sh
.venv/bin/python -m chronicle.harness build-suite fpb-economic-outlook-2026-2031-june-2026 --year 2026 --out "$fpb_out"
.venv/bin/python -m chronicle.harness build-suite eurostat-gov-10a-taxag-2025 --year 2025 --out "$gov_out"
.venv/bin/python -m chronicle.harness build-suite eurostat-spr-exp-func-2024 --year 2024 --out "$spr_out"
.venv/bin/python -m chronicle.harness build-suite statbel-population-structure-2025 --year 2025 --out "$statbel_out"
```

Each output variable above was an isolated directory created with
`mktemp -d`; no committed build output was produced.

### C4 — tests and formatting

```sh
.venv/bin/python -m pytest -q \
  tests/test_belgium_targets.py \
  tests/test_etl_eurostat.py \
  tests/test_source_package_alias_drift.py
.venv/bin/python -m pytest -q \
  tests/test_chronicle_bundle.py::test_build_bundle_writes_merged_consumer_contract
ruff check tests/test_belgium_targets.py tests/test_etl_eurostat.py tests/test_chronicle_bundle.py
ruff format --check tests/test_belgium_targets.py tests/test_etl_eurostat.py tests/test_chronicle_bundle.py
```

## For the target surface

Chronicle exposes facts only. A 2025 harvest can select these direct 2025
level families:

- FPB: `fpb.economic_outlook_2026_2031.cy2025.{family}.{line}.{measure}`,
  where `{family}` is `key_figures.price_indices`,
  `key_figures.domestic_employment`, `key_figures.unemployment`,
  `national_income_account`, `labour_market.levels`, `labour_market.rates`,
  `household_account`, `general_government_account`, or
  `social_benefits_detail`.
- Eurostat tax totals:
  `eurostat.gov_10a_taxag.cy2025.tax_revenue.country.{d2_be,d5_be,d51_be,d61_be}.revenue`.
- Eurostat income-tax split:
  `eurostat.gov_10a_taxag.cy2025.income_tax_revenue_by_taxpayer.country.{d51a_c1_be,d51b_c2_be}.revenue`.
- Statbel population:
  `statbel.population_structure.cy2025.people.by_nuts1_age_sex.{cell}.people`.

ESSPROS has a 2024 level, not a 2025 level:
`eurostat.spr_exp_func.cy2024.social_protection_expenditure_by_function.be.{function}.expenditure`.
Chronicle does not relabel it as 2025.

For consumer-declared ratio-of-facts aging, FPB supplies like-for-like pairs
for every selected line. Substitute `{from}` with 2023, 2022, or 2024 and keep
the same `{family}`, `{line}`, and `{measure}` on both sides:

```text
fpb.economic_outlook_2026_2031.cy{from}.{family}.{line}.{measure}
fpb.economic_outlook_2026_2031.cy2025.{family}.{line}.{measure}
```

The monetary ratio-pair families are `national_income_account.*.amount_meur`,
`household_account.*.amount_meur`,
`general_government_account.*.amount_meur`, and
`social_benefits_detail.*.amount_meur`. T07 level pairs use
`labour_market.levels.*.level_thousand`. Rates and annual changes remain facts
but are not generic nominal-level aging factors.

Eurostat also supplies within-source 2023→2025 and 2024→2025 tax pairs for all
six 2025 items. It supplies 2022→2025 pairs only for D51A_C1 and D51B_C2; the
existing aggregate-tax stream begins in 2023. Neither Statbel nor ESSPROS has
a within-source pair ending in 2025 in this lane.

Any choice of proxy family, ratio calculation, aging, cross-source mapping,
period alignment, target activation, or solver construction belongs to the
consumer. When a target period differs from a fact reference period, the
consumer must provide its explicit `PeriodAlignmentDeclaration`; Chronicle
returns the published levels, never the aligned number.

LANE C5 DONE
