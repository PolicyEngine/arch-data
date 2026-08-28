# Lane C2 — Belgium national accounts and JRC external rows

## Outcome and source-boundary decisions

This lane adds the hash-pinned Eurostat `nasa_10_nf_tr` package and extends the
JRC EUROMOD Belgium comparator. The Eurostat build preserves all 84 JSON-stat
cube positions and emits facts for exactly the 78 populated publisher
observations. The JRC build now contains 41 facts: 25 administrative External
statistics, 14 model-output values, and 2 EU-SILC survey aggregates. No R2
upload was performed; both manifests record only the content-addressed keys.

The cached PDF resolves three material ambiguities in the task shorthand:

- The Annex columns put most requested External series in publisher periods
  2021–2023, not 2022–2024. Chronicle preserves the printed periods. A consumer
  that needs another period owns the contract for aligning it; Chronicle
  returns the published level and never an aligned number.
- The `poa=2,273k` and `psu=79k` observations are in the SILC column. Their
  External cells are `NaN`, so they are stored as `survey_aggregate` and are
  validation-only.
- The Annex names NBB for child-benefit amounts, not FAMIFED or a regional
  agency. It names FPD/SFPD only for elderly-income-support recipient counts,
  whose External cells are absent. The `yse` source continuation is a dash, so
  no primary issuer was invented.

These findings come from commands C1–C3 below. All fact-table values and source
coordinates come mechanically from command C4; all build and validation counts
come from commands C5–C8.

## Artifact pins

| Artifact | SHA-256 | Bytes | Command |
|---|---|---:|---|
| `nasa_10_nf_tr.json` | `30d3f5bf3d1414c78633d13f505558b837b84e92c24b17050249ab19cec20a6d` | 5,098 | C1 |
| curated JRC CSV | `2ef69251a72caaab042706c77143fa4f86dde2f800747ebb421b5f7b9a45e394` | 6,956 | C1 |
| cached JRC PDF | `7c4b0aa4f1f96161e1ce7e4ad300a3fa56cdad7241f82fb650eeec03d30f087b` | 4,184,683 | C1 |

Recorded storage pointers (metadata only; not uploaded in this lane):

- `raw/eurostat/eurostat-nasa-10-nf-tr/2024/30d3f5bf3d1414c78633d13f505558b837b84e92c24b17050249ab19cec20a6d/nasa_10_nf_tr.json`
- `raw/belgium/jrc-euromod-be-baseline-statistics-2025/2025/2ef69251a72caaab042706c77143fa4f86dde2f800747ebb421b5f7b9a45e394/jrc_euromod_be_baseline_statistics_2025.csv`

The JRC CSV's original header plus 18 rows are byte-for-byte unchanged; 23 rows
were appended. After stripping its trailing newline, the Eurostat
`SOURCE_URL.txt` equals the manifest `source_url`. The request included B3N,
but the returned cube has no B3N category. Its six null coordinates are
PAID/D42 and RECV/D5 for each of 2022–2024; none was turned into a fact.

## Eurostat fact table

Command C4 emitted this inventory. “Parsed row” is the 1-based row in the
complete 84-coordinate JSON-stat parse; `H…` is the selected-row virtual-sheet
value cell. Source values are current-price million euro (`CP_MEUR`); compiled
facts apply the declared `value_scale: 1000000`. Eurostat marks every populated
2024 observation provisional (`status=p`).

| Concept (`layout.groupby_value_id`) | ESA item | Direction | Year | Compiled value (EUR) | Source coordinate |
|---|---:|---|---:|---:|---|
| `belgium_household_operating_surplus_gross` | B2G | PAID | 2022 | 36,960,000,000 | `source_index=0`, parsed row 1, `H2` |
| `belgium_household_mixed_income_gross` | B3G | PAID | 2022 | 36,718,000,000 | `source_index=3`, parsed row 4, `H3` |
| `belgium_household_disposable_income_gross` | B6G | PAID | 2022 | 329,780,000,000 | `source_index=6`, parsed row 7, `H4` |
| `belgium_household_compensation_of_employees_paid` | D1 | PAID | 2022 | 6,011,000,000 | `source_index=9`, parsed row 10, `H5` |
| `belgium_household_wages_and_salaries_paid` | D11 | PAID | 2022 | 4,758,000,000 | `source_index=12`, parsed row 13, `H6` |
| `belgium_household_employers_social_contributions_paid` | D12 | PAID | 2022 | 1,253,000,000 | `source_index=15`, parsed row 16, `H7` |
| `belgium_household_property_income_paid` | D4 | PAID | 2022 | 4,940,000,000 | `source_index=18`, parsed row 19, `H8` |
| `belgium_household_interest_paid` | D41 | PAID | 2022 | 4,572,000,000 | `source_index=21`, parsed row 22, `H9` |
| `belgium_household_other_investment_income_paid` | D44 | PAID | 2022 | 0 | `source_index=27`, parsed row 28, `H10` |
| `belgium_household_rents_paid` | D45 | PAID | 2022 | 368,000,000 | `source_index=30`, parsed row 31, `H11` |
| `belgium_household_current_taxes_on_income_paid` | D5 | PAID | 2022 | 69,114,000,000 | `source_index=33`, parsed row 34, `H12` |
| `belgium_household_net_social_contributions_paid` | D61 | PAID | 2022 | 99,704,000,000 | `source_index=36`, parsed row 37, `H13` |
| `belgium_household_social_benefits_paid` | D62 | PAID | 2022 | 64,000,000 | `source_index=39`, parsed row 40, `H14` |
| `belgium_household_operating_surplus_gross` | B2G | RECV | 2022 | 36,960,000,000 | `source_index=42`, parsed row 43, `H15` |
| `belgium_household_mixed_income_gross` | B3G | RECV | 2022 | 36,718,000,000 | `source_index=45`, parsed row 46, `H16` |
| `belgium_household_disposable_income_gross` | B6G | RECV | 2022 | 329,780,000,000 | `source_index=48`, parsed row 49, `H17` |
| `belgium_household_compensation_of_employees_received` | D1 | RECV | 2022 | 277,464,000,000 | `source_index=51`, parsed row 52, `H18` |
| `belgium_household_wages_and_salaries_received` | D11 | RECV | 2022 | 209,481,000,000 | `source_index=54`, parsed row 55, `H19` |
| `belgium_household_employers_social_contributions_received` | D12 | RECV | 2022 | 67,983,000,000 | `source_index=57`, parsed row 58, `H20` |
| `belgium_household_property_income_received` | D4 | RECV | 2022 | 40,867,000,000 | `source_index=60`, parsed row 61, `H21` |
| `belgium_household_interest_received` | D41 | RECV | 2022 | 6,334,000,000 | `source_index=63`, parsed row 64, `H22` |
| `belgium_household_distributed_income_of_corporations_received` | D42 | RECV | 2022 | 23,090,000,000 | `source_index=66`, parsed row 67, `H23` |
| `belgium_household_other_investment_income_received` | D44 | RECV | 2022 | 10,463,000,000 | `source_index=69`, parsed row 70, `H24` |
| `belgium_household_rents_received` | D45 | RECV | 2022 | 980,000,000 | `source_index=72`, parsed row 73, `H25` |
| `belgium_household_net_social_contributions_received` | D61 | RECV | 2022 | 64,000,000 | `source_index=78`, parsed row 79, `H26` |
| `belgium_household_social_benefits_received` | D62 | RECV | 2022 | 108,435,000,000 | `source_index=81`, parsed row 82, `H27` |
| `belgium_household_operating_surplus_gross` | B2G | PAID | 2023 | 41,351,000,000 | `source_index=1`, parsed row 2, `H28` |
| `belgium_household_mixed_income_gross` | B3G | PAID | 2023 | 38,850,000,000 | `source_index=4`, parsed row 5, `H29` |
| `belgium_household_disposable_income_gross` | B6G | PAID | 2023 | 359,164,000,000 | `source_index=7`, parsed row 8, `H30` |
| `belgium_household_compensation_of_employees_paid` | D1 | PAID | 2023 | 6,174,000,000 | `source_index=10`, parsed row 11, `H31` |
| `belgium_household_wages_and_salaries_paid` | D11 | PAID | 2023 | 4,919,000,000 | `source_index=13`, parsed row 14, `H32` |
| `belgium_household_employers_social_contributions_paid` | D12 | PAID | 2023 | 1,255,000,000 | `source_index=16`, parsed row 17, `H33` |
| `belgium_household_property_income_paid` | D4 | PAID | 2023 | 11,584,000,000 | `source_index=19`, parsed row 20, `H34` |
| `belgium_household_interest_paid` | D41 | PAID | 2023 | 11,184,000,000 | `source_index=22`, parsed row 23, `H35` |
| `belgium_household_other_investment_income_paid` | D44 | PAID | 2023 | 0 | `source_index=28`, parsed row 29, `H36` |
| `belgium_household_rents_paid` | D45 | PAID | 2023 | 400,000,000 | `source_index=31`, parsed row 32, `H37` |
| `belgium_household_current_taxes_on_income_paid` | D5 | PAID | 2023 | 72,794,000,000 | `source_index=34`, parsed row 35, `H38` |
| `belgium_household_net_social_contributions_paid` | D61 | PAID | 2023 | 108,000,000,000 | `source_index=37`, parsed row 38, `H39` |
| `belgium_household_social_benefits_paid` | D62 | PAID | 2023 | 62,000,000 | `source_index=40`, parsed row 41, `H40` |
| `belgium_household_operating_surplus_gross` | B2G | RECV | 2023 | 41,351,000,000 | `source_index=43`, parsed row 44, `H41` |
| `belgium_household_mixed_income_gross` | B3G | RECV | 2023 | 38,850,000,000 | `source_index=46`, parsed row 47, `H42` |
| `belgium_household_disposable_income_gross` | B6G | RECV | 2023 | 359,164,000,000 | `source_index=49`, parsed row 50, `H43` |
| `belgium_household_compensation_of_employees_received` | D1 | RECV | 2023 | 299,696,000,000 | `source_index=52`, parsed row 53, `H44` |
| `belgium_household_wages_and_salaries_received` | D11 | RECV | 2023 | 226,018,000,000 | `source_index=55`, parsed row 56, `H45` |
| `belgium_household_employers_social_contributions_received` | D12 | RECV | 2023 | 73,677,000,000 | `source_index=58`, parsed row 59, `H46` |
| `belgium_household_property_income_received` | D4 | RECV | 2023 | 52,674,000,000 | `source_index=61`, parsed row 62, `H47` |
| `belgium_household_interest_received` | D41 | RECV | 2023 | 15,962,000,000 | `source_index=64`, parsed row 65, `H48` |
| `belgium_household_distributed_income_of_corporations_received` | D42 | RECV | 2023 | 25,012,000,000 | `source_index=67`, parsed row 68, `H49` |
| `belgium_household_other_investment_income_received` | D44 | RECV | 2023 | 10,605,000,000 | `source_index=70`, parsed row 71, `H50` |
| `belgium_household_rents_received` | D45 | RECV | 2023 | 1,094,000,000 | `source_index=73`, parsed row 74, `H51` |
| `belgium_household_net_social_contributions_received` | D61 | RECV | 2023 | 62,000,000 | `source_index=79`, parsed row 80, `H52` |
| `belgium_household_social_benefits_received` | D62 | RECV | 2023 | 116,832,000,000 | `source_index=82`, parsed row 83, `H53` |
| `belgium_household_operating_surplus_gross` | B2G | PAID | 2024 | 41,447,000,000 | `source_index=2`, parsed row 3, `H54` |
| `belgium_household_mixed_income_gross` | B3G | PAID | 2024 | 39,700,000,000 | `source_index=5`, parsed row 6, `H55` |
| `belgium_household_disposable_income_gross` | B6G | PAID | 2024 | 369,313,000,000 | `source_index=8`, parsed row 9, `H56` |
| `belgium_household_compensation_of_employees_paid` | D1 | PAID | 2024 | 6,359,000,000 | `source_index=11`, parsed row 12, `H57` |
| `belgium_household_wages_and_salaries_paid` | D11 | PAID | 2024 | 4,978,000,000 | `source_index=14`, parsed row 15, `H58` |
| `belgium_household_employers_social_contributions_paid` | D12 | PAID | 2024 | 1,381,000,000 | `source_index=17`, parsed row 18, `H59` |
| `belgium_household_property_income_paid` | D4 | PAID | 2024 | 10,622,000,000 | `source_index=20`, parsed row 21, `H60` |
| `belgium_household_interest_paid` | D41 | PAID | 2024 | 10,226,000,000 | `source_index=23`, parsed row 24, `H61` |
| `belgium_household_other_investment_income_paid` | D44 | PAID | 2024 | 0 | `source_index=29`, parsed row 30, `H62` |
| `belgium_household_rents_paid` | D45 | PAID | 2024 | 396,000,000 | `source_index=32`, parsed row 33, `H63` |
| `belgium_household_current_taxes_on_income_paid` | D5 | PAID | 2024 | 77,033,000,000 | `source_index=35`, parsed row 36, `H64` |
| `belgium_household_net_social_contributions_paid` | D61 | PAID | 2024 | 112,346,000,000 | `source_index=38`, parsed row 39, `H65` |
| `belgium_household_social_benefits_paid` | D62 | PAID | 2024 | 86,000,000 | `source_index=41`, parsed row 42, `H66` |
| `belgium_household_operating_surplus_gross` | B2G | RECV | 2024 | 41,447,000,000 | `source_index=44`, parsed row 45, `H67` |
| `belgium_household_mixed_income_gross` | B3G | RECV | 2024 | 39,700,000,000 | `source_index=47`, parsed row 48, `H68` |
| `belgium_household_disposable_income_gross` | B6G | RECV | 2024 | 369,313,000,000 | `source_index=50`, parsed row 51, `H69` |
| `belgium_household_compensation_of_employees_received` | D1 | RECV | 2024 | 310,278,000,000 | `source_index=53`, parsed row 54, `H70` |
| `belgium_household_wages_and_salaries_received` | D11 | RECV | 2024 | 233,080,000,000 | `source_index=56`, parsed row 57, `H71` |
| `belgium_household_employers_social_contributions_received` | D12 | RECV | 2024 | 77,198,000,000 | `source_index=59`, parsed row 60, `H72` |
| `belgium_household_property_income_received` | D4 | RECV | 2024 | 52,437,000,000 | `source_index=62`, parsed row 63, `H73` |
| `belgium_household_interest_received` | D41 | RECV | 2024 | 13,943,000,000 | `source_index=65`, parsed row 66, `H74` |
| `belgium_household_distributed_income_of_corporations_received` | D42 | RECV | 2024 | 26,144,000,000 | `source_index=68`, parsed row 69, `H75` |
| `belgium_household_other_investment_income_received` | D44 | RECV | 2024 | 11,223,000,000 | `source_index=71`, parsed row 72, `H76` |
| `belgium_household_rents_received` | D45 | RECV | 2024 | 1,128,000,000 | `source_index=74`, parsed row 75, `H77` |
| `belgium_household_net_social_contributions_received` | D61 | RECV | 2024 | 86,000,000 | `source_index=80`, parsed row 81, `H78` |
| `belgium_household_social_benefits_received` | D62 | RECV | 2024 | 124,608,000,000 | `source_index=83`, parsed row 84, `H79` |

## JRC requested fact table

This table includes the 23 appended rows plus the two pre-existing 2023
child-benefit and unemployment-benefit External amount rows needed to show the
complete requested series. The rest of the original 18-row curated file was not
rewritten. Publisher and compiled values are generated by C4; PDF locations and
issuers are verified by C2.

| Fine series | Metric | Year | Publisher value | Compiled fact | Provenance | Source row and report evidence |
|---|---|---:|---:|---:|---|---|
| `a3_1_self_employment_income_external_2022` | `self_employment_income_yse` | 2022 | 1,257 thousand | 1,257,000 count | administrative | CSV 22 / `G22`; A3.1 report 112, PDF 114; source row is `-` on PDF 115, so no issuer is identified |
| `a3_2_employment_income_external_2021` | `employment_income_yem` | 2021 | 147,112 million EUR | 147,112,000,000 EUR | administrative | CSV 27 / `G27`; A3.2 report 114, PDF 116; RSZ/ONSS on PDF 115 |
| `a3_2_employment_income_external_2022` | `employment_income_yem` | 2022 | 161,644 million EUR | 161,644,000,000 EUR | administrative | CSV 33 / `G33`; A3.2 report 114, PDF 116; RSZ/ONSS on PDF 115 |
| `a3_2_employment_income_external_2023` | `employment_income_yem` | 2023 | 175,998 million EUR | 175,998,000,000 EUR | administrative | CSV 39 / `G39`; A3.2 report 114, PDF 116; RSZ/ONSS on PDF 115 |
| `a3_4_capital_income_tax_external_2021` | `capital_income_tax_tinkt_s` | 2021 | 3,522 million EUR | 3,522,000,000 EUR | administrative | CSV 28 / `G28`; A3.4 report 118, PDF 120; NBB on PDF 118 |
| `a3_4_capital_income_tax_external_2022` | `capital_income_tax_tinkt_s` | 2022 | 4,152 million EUR | 4,152,000,000 EUR | administrative | CSV 34 / `G34`; A3.4 report 118, PDF 120; NBB on PDF 118 |
| `a3_5_income_support_external_2021` | `income_support_bsa_s` | 2021 | 215 thousand | 215,000 count | administrative | CSV 20 / `G20`; A3.5 report 120, PDF 122; POD MI/SPP IS recipients on PDF 124 |
| `a3_5_income_support_external_2022` | `income_support_bsa_s` | 2022 | 241 thousand | 241,000 count | administrative | CSV 23 / `G23`; A3.5 report 120, PDF 122; POD MI/SPP IS recipients on PDF 124 |
| `a3_5_unemployment_benefits_external_2021` | `unemployment_benefits_bun` | 2021 | 992 thousand | 992,000 count | administrative | CSV 21 / `G21`; A3.5 report 120, PDF 122; RVA/ONEM on PDF 125 |
| `a3_5_unemployment_benefits_external_2022` | `unemployment_benefits_bun` | 2022 | 813 thousand | 813,000 count | administrative | CSV 24 / `G24`; A3.5 report 120, PDF 122; RVA/ONEM on PDF 125 |
| `a3_5_old_age_pension_silc_2022` | `old_age_pension_poa` | 2022 | 2,273 thousand | 2,273,000 count | survey_aggregate | CSV 25 / `G25`; A3.5 report 120, PDF 122; SILC column, External is `NaN`, source is `-` on PDF 124 |
| `a3_5_survivor_pension_silc_2022` | `survivor_pension_psu` | 2022 | 79 thousand | 79,000 count | survey_aggregate | CSV 26 / `G26`; A3.5 report 120, PDF 122; SILC column, External is `NaN`, source is `-` on PDF 124 |
| `a3_6_income_support_external_2021` | `income_support_bsa_s` | 2021 | 1,656 million EUR | 1,656,000,000 EUR | administrative | CSV 29 / `G29`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_income_support_external_2022` | `income_support_bsa_s` | 2022 | 1,809 million EUR | 1,809,000,000 EUR | administrative | CSV 35 / `G35`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_income_support_external_2023` | `income_support_bsa_s` | 2023 | 2,049 million EUR | 2,049,000,000 EUR | administrative | CSV 41 / `G41`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_income_support_elderly_external_2021` | `income_support_elderly_bsaoa_s` | 2021 | 767 million EUR | 767,000,000 EUR | administrative | CSV 30 / `G30`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_income_support_elderly_external_2022` | `income_support_elderly_bsaoa_s` | 2022 | 824 million EUR | 824,000,000 EUR | administrative | CSV 36 / `G36`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_income_support_elderly_external_2023` | `income_support_elderly_bsaoa_s` | 2023 | 941 million EUR | 941,000,000 EUR | administrative | CSV 42 / `G42`; A3.6 report 125, PDF 127; NBB amounts on PDF 124 |
| `a3_6_child_benefits_external_2021` | `child_benefits_bch_s` | 2021 | 7,305 million EUR | 7,305,000,000 EUR | administrative | CSV 31 / `G31`; A3.6 report 125, PDF 127; NBB on PDF 124 |
| `a3_6_child_benefits_external_2022` | `child_benefits_bch_s` | 2022 | 7,738 million EUR | 7,738,000,000 EUR | administrative | CSV 37 / `G37`; A3.6 report 125, PDF 127; NBB on PDF 124 |
| `a3_6_child_benefits_external_2023` | `child_benefits` | 2023 | 8,191 million EUR | 8,191,000,000 EUR | administrative | Existing CSV 7 / `G7`; A3.6 report 125, PDF 127; NBB on PDF 124 |
| `a3_6_unemployment_benefits_external_2021` | `unemployment_benefits_bun` | 2021 | 8,197 million EUR | 8,197,000,000 EUR | administrative | CSV 32 / `G32`; A3.6 report 125, PDF 127; RVA/ONEM on PDF 125 |
| `a3_6_unemployment_benefits_external_2022` | `unemployment_benefits_bun` | 2022 | 6,670 million EUR | 6,670,000,000 EUR | administrative | CSV 38 / `G38`; A3.6 report 125, PDF 127; RVA/ONEM on PDF 125 |
| `a3_6_unemployment_benefits_external_2023` | `unemployment_benefits` | 2023 | 6,391 million EUR | 6,391,000,000 EUR | administrative | Existing CSV 9 / `G9`; A3.6 report 125, PDF 127; RVA/ONEM on PDF 125 |
| `a3_6_old_age_survivor_pension_external_2023` | `old_age_survivor_pension_il_ext_poapsu` | 2023 | 64,443 million EUR | 64,443,000,000 EUR | administrative | CSV 40 / `G40`; A3.6 continuation report 127, PDF 129; NBB on PDF 126 |

The other two administrative JRC facts are the pre-existing 2023 national-
income-tax and employee-SIC External sums. They were moved out of the formerly
mixed `model_output` record set into the administrative record set without
changing their CSV rows or values.

## Microcosm mapping

Chronicle does not activate targets. For Microcosm consumption, the eligible
source facts and the hard exclusions are:

- Candidate calibration-grade source sums: all 78 Eurostat facts
  (`administrative`, `aggregation: sum`) and all 25 JRC External administrative
  facts (5 recipient-count sums and 20 annual-amount sums). Each remains subject
  to the exact definition and period below.
- Validation-only: the 2 SILC `poa`/`psu` recipient-count facts and all 14 JRC
  `model_output` facts, including EUROMOD values, ratios, Gini, and poverty
  statistics. A `sum` aggregation never overrides survey/model provenance.
- Do not simultaneously target overlapping national-account rows: B2G/B3G/B6G
  are duplicate balancing levels under PAID and RECV; D1 equals the D11+D12
  hierarchy; D4 overlaps its components; D62 overlaps benefit-specific sums.
- The YSE External count is stored exactly as JRC's External statistic, but the
  report gives no primary issuer. That unknown issuer is a downstream caveat.
- Any selection, reconciliation, aging, period alignment, support-aware
  activation, or solver construction belongs to Microcosm, never Chronicle.

### National-account definitional gaps

Every row covers institutional sector `S14_S15`, which includes NPISH alongside
households. That is a common scope gap against household/person microdata. PAID
and RECV are sector-account uses/resources, not person-level signs.

| ESA item | Likely Axiom/EUROMOD target | Known gap |
|---|---|---|
| B2G | household gross operating surplus | Gross production balance for household/NPISH producers, not generic cash capital income; repeated under both directions. |
| B3G | `yse` / mixed income | Gross of consumption of fixed capital and combines labour and capital returns of unincorporated enterprises; broader than survey self-employment cash income; repeated under both directions. |
| B6G | gross disposable income | National-account balancing item with imputed components and NPISH, not a simple sum of survey cash disposable income; repeated under both directions. |
| D1 | compensation of employees | D11 + D12; do not target alongside both components. PAID is households/NPISH as employers; RECV is the resident-sector resource. |
| D11 | `yem` / wages and salaries | ESA cash-and-in-kind wages under residence/sector accounting differ from EUROMOD/SILC and ONSS wage concepts. |
| D12 | employers' social contributions | Includes actual and imputed contributions. On the resource side it is imputed to households and is not cash wages or disposable income. |
| D4 | property income | Overlaps D41, D42, D44, D45 and may contain other ESA components; not an independent survey capital-income target if components are used. |
| D41 | interest | FISIM-adjusted ESA interest, not gross bank interest and not taxable movable income. |
| D42 | distributed corporate income | Broader than a taxable-dividend variable; only RECV cells are populated. |
| D44 | insurance/pension/fund investment income | Income attributed to policyholders, pension-entitlement holders, and collective-fund shareholders; not taxable movable income and not necessarily cash received. |
| D45 | rent | Rent on natural resources, not tenant housing rent or ordinary dwelling rental income. |
| D5 | personal/current tax | Current taxes on income, wealth, etc.; broader than personal income tax alone. Only PAID cells are populated. |
| D61 | social contributions | Broad ESA net-social-contribution aggregate across actual/imputed and contributor classes; not employee contributions alone. |
| D62 | cash social benefits | All social benefits other than social transfers in kind; broader than any individual EUROMOD benefit. PAID is a household/NPISH-sector use, not a benefit deduction. |

### JRC comparator gaps

- `yem`: ONSS excludes a substantial portion of holiday pay, performance
  bonuses, and meal vouchers that EUROMOD employment income includes (report
  100, PDF 102; C2).
- `yse`: the report attributes the survey/external gap to insufficient EU-SILC
  coverage and underreporting of small self-employment incomes; no External
  issuer is identified (reports 100/113, PDFs 102/115; C2).
- `tinkt_s`: the NBB comparator is the advance levy on movable property and
  covers more sources than capital income alone (report 101, PDF 103; C2).
- `bsa_s`: validation covers regular support only and excludes equivalent
  support received by precarious foreign populations; the family-income
  condition also differs from administration (report 101, PDF 103; C2).
- `bsaoa_s`: stored values are NBB annual amounts. FPD/SFPD is listed only for
  recipient counts, for which External values are absent (report 122, PDF 124;
  C2).
- `bch_s`: child disability is unobserved in the input, so higher disability
  allowances cannot be simulated. The Annex amount source is NBB, not
  FAMIFED/regional agencies (reports 102/122, PDFs 104/124; C2).
- `bun`: ONEM/RVA recipient and amount concepts differ from SILC reporting,
  especially for short unemployment spells (reports 101–102, PDFs 103–104;
  C2).
- `il_ext_poapsu`: NBB publishes one combined old-age-plus-survivor-pension
  amount; it cannot support separate `poa` and `psu` amount targets.
- `poa`/`psu` counts: 2,273k/79k are SILC observations with External `NaN` and
  cannot be relabelled as SFPD administrative totals (report 120, PDFs 122/124;
  C2).

## Command ledger

All commands ran from
`/Users/maxghenis/TheAxiomFoundation/_cape-prep/chronicle-be` with network
disabled. The repository's default uv cache was not writable in the sandbox,
so repository commands use a task-specific cache plus `--offline --no-sync`.

### C1 — artifact hashes, sizes, unchanged JRC prefix, and URL equality

```sh
shasum -a 256 \
  db/data/eurostat/nasa_10_nf_tr/nasa_10_nf_tr.json \
  db/data/jrc/euromod_be_baseline_statistics_2025/jrc_euromod_be_baseline_statistics_2025.csv \
  /Users/maxghenis/TheAxiomFoundation/_cape-prep/Y15_CR_BE_final.pdf
wc -c \
  db/data/eurostat/nasa_10_nf_tr/nasa_10_nf_tr.json \
  db/data/jrc/euromod_be_baseline_statistics_2025/jrc_euromod_be_baseline_statistics_2025.csv \
  /Users/maxghenis/TheAxiomFoundation/_cape-prep/Y15_CR_BE_final.pdf
diff -u \
  <(git show origin/main:db/data/jrc/euromod_be_baseline_statistics_2025/jrc_euromod_be_baseline_statistics_2025.csv | sed -n '1,19p') \
  <(sed -n '1,19p' db/data/jrc/euromod_be_baseline_statistics_2025/jrc_euromod_be_baseline_statistics_2025.csv)
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync python - <<'PY'
from pathlib import Path
import json
import yaml

base = Path("db/data/eurostat/nasa_10_nf_tr")
manifest = yaml.safe_load((base / "manifest.yaml").read_text())
file_spec = manifest["files"][2024]
fetches = json.loads(Path("FETCH-MANIFEST-EUROSTAT.json").read_text())["fetches"]
fetch = next(item for item in fetches if item["dataset_id"] == "nasa_10_nf_tr")
print((base / "SOURCE_URL.txt").read_text().strip() == file_spec["source_url"])
print(fetch["source_url"] == file_spec["source_url"])
print(fetch["sha256"] == file_spec["sha256"])
PY
```

Output: the three pins and byte counts in the artifact table; the `diff` had no
output; both URL equalities and fetch-manifest hash equality printed `True`.

### C2 — cached-PDF verification

The requested `uv run --with pdfplumber` resolver could not write its cache in
this detached sandbox. No package was downloaded: the already-cached
pdfplumber 0.11.10 interpreter was invoked directly.

```sh
/Users/maxghenis/.cache/uv/archive-v0/HLlfXwC9DMcE0Q6gCdMwl/bin/python -c \
  'import pdfplumber; print(pdfplumber.__version__)'
/Users/maxghenis/.cache/uv/archive-v0/HLlfXwC9DMcE0Q6gCdMwl/bin/python -c \
  'import pdfplumber; path="/Users/maxghenis/TheAxiomFoundation/_cape-prep/Y15_CR_BE_final.pdf"; pages=(102,103,104,114,115,116,118,120,122,124,125,126,127,129); p=pdfplumber.open(path); [print(f"=== PDF PAGE {n} ===\\n"+(p.pages[n-1].extract_text(x_tolerance=2,y_tolerance=3) or "")) for n in pages]'
```

This printed the Annex headers, all table rows in the JRC fact table, the
issuer continuations, and the narrative definition warnings cited above.

### C3 — cube structure and populated-coordinate check

```sh
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("db/data/eurostat/nasa_10_nf_tr/nasa_10_nf_tr.json").read_text())
print(data["id"], data["size"], len(data["value"]), data["dimension"]["na_item"]["category"]["index"])
PY
```

The dimension sizes multiply to 84, `value` contains 78 populated entries, and
the returned `na_item` index contains 14 categories with no B3N.

### C4 — fact and lineage inventory used by both tables

```sh
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync python - <<'PY'
from chronicle.source_package import load_source_package
from chronicle.sources.cells import build_source_cell_key
from chronicle.sources.rows import build_source_row_key

for alias, year, value_column in (
    ("eurostat-nasa-10-nf-tr", 2024, 8),
    ("jrc-euromod-be-baseline-statistics-2025", 2025, 7),
):
    package = load_source_package(alias)
    rows = package.build_source_rows(year)
    cells = package.build_source_cells(year, source_rows=rows)
    facts = package.build_facts(year, cells=cells, source_rows=rows)
    rows_by_key = {build_source_row_key(row): row for row in rows}
    cells_by_key = {build_source_cell_key(cell): cell for cell in cells}
    print(alias, len(rows), len(cells), len(facts))
    for fact in facts:
        row = rows_by_key[fact.source_row_keys[0]]
        value_cell = next(
            cells_by_key[key]
            for key in fact.source_cell_keys
            if cells_by_key[key].column_number == value_column
        )
        print(
            fact.layout.groupby_value_id,
            fact.filters,
            fact.value,
            fact.period.value,
            fact.provenance_class,
            row.row_number,
            row.values.get("source_index"),
            value_cell.address,
        )
PY
```

Header output: Eurostat `84 1343 78`; JRC `41 294 41`.

### C5 — package validators

```sh
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
  python -m chronicle.cli validate-package eurostat-nasa-10-nf-tr --year 2024
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
  python -m chronicle.cli validate-package jrc-euromod-be-baseline-statistics-2025 --year 2025
```

### C6 — full package build suites

```sh
EUROSTAT_SUITE_DIR=$(mktemp -d /tmp/chronicle-c2-eurostat.XXXXXX)
JRC_SUITE_DIR=$(mktemp -d /tmp/chronicle-c2-jrc.XXXXXX)
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
  python -m chronicle.cli build-suite eurostat-nasa-10-nf-tr \
  --year 2024 --out "$EUROSTAT_SUITE_DIR" --replace
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
  python -m chronicle.cli build-suite jrc-euromod-be-baseline-statistics-2025 \
  --year 2025 --out "$JRC_SUITE_DIR" --replace
```

### C7 — emitted-row, cell, and fact validators

Run in the same shell as C6 so its two task-specific output variables remain
defined.

```sh
for VALIDATION_KIND in source-rows source-cells facts; do
  VALIDATION_FILE=$(printf '%s' "$VALIDATION_KIND" | tr '-' '_').jsonl
  UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
    python -m chronicle.cli "validate-$VALIDATION_KIND" \
    --input "$EUROSTAT_SUITE_DIR/$VALIDATION_FILE"
  UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync \
    python -m chronicle.cli "validate-$VALIDATION_KIND" \
    --input "$JRC_SUITE_DIR/$VALIDATION_FILE"
done
```

### C8 — repository tests

```sh
UV_CACHE_DIR=/tmp/chronicle-c2-uv-cache uv run --offline --no-sync pytest -q
```

### C9 — clean-diff and branch checks

```sh
git diff --check
git status --short --branch
git branch --show-current
```

## Validation output

| Check | Result | Command |
|---|---|---|
| Eurostat package structure | valid; 6 record sets, 78 selected rows, 6 measures, 78 source records, 6 regions; 0 errors, 0 warnings | C5 |
| JRC package structure | valid; 10 record sets, 41 selected rows, 10 measures, 41 source records, 10 regions; 0 errors, 0 warnings | C5 |
| Eurostat build suite | valid; 84 complete-cube rows, 1,343 cells, 78 facts, 78 consumer facts, 546 constraints, lineage 1.0, 0 acceptance errors | C6 |
| JRC build suite | valid; 41 rows, 294 cells, 41 facts, 41 consumer facts, 82 constraints, lineage 1.0, 0 acceptance errors | C6 |
| Eurostat row/cell/fact validators | all valid; counts 84 / 1,343 / 78; 0 errors and warnings | C7 |
| JRC row/cell/fact validators | all valid; counts 41 / 294 / 41; 0 errors and warnings | C7 |
| Repository test suite | 691 passed, 1 skipped, 14 warnings in 991.52s (0:16:31); exit 0 | C8 |
| `ledger-source-fidelity` judge | PASS; selected coordinates exactly equal all 78 populated cube observations, all JRC additions match cached PDF rows and publisher periods | independent judge review after C1–C7 |
| `ledger-boundary` judge | PASS; provenance split is correct and no target values, aging, alignment, reconciliation, activation, or solver construction entered Chronicle | independent judge review after C1–C7 |

Both acceptance reports contain one non-fatal environmental warning:
`concept_alignment_validation_skipped`, because no Axiom CLI command is
configured. Evidence presence, manual concept review, row semantics, package
acceptance, and both required Chronicle judge reviews pass.

## Handoff

- Final C9 checks reported no whitespace errors and confirmed branch
  `be-national-accounts-packages`.
- The local commit message is
  `Add Belgium national accounts and JRC external facts`.
- No push and no R2 upload were performed. The two manifests merely declare the
  required content-addressed R2 keys.
- A consumer using a fact outside its publisher period owns the alignment
  contract; Chronicle returns the published value and does not compute an
  aligned value.

LANE C2 DONE
