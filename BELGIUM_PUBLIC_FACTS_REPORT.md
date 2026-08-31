# Belgium public facts wave final report

## Outcome

The locally reviewable wave is complete at implementation head
`206ebfa38bdc65ed4d89f416cf3cbf78eada81dd`, based on `origin/main`
`10597ae602767b046ca1b294949e5df7bfd3b367` on branch
`be-public-calibration-facts`. The commit containing this report necessarily
follows that reviewed implementation head; its exact hash is reported in the
final handoff response because a Git commit cannot contain its own hash.

The existing `sfpd-legal-pension-caseload-2025` selector now builds four direct
publisher facts from the official SFPD February 2025 monthly-statistics PDF.
The intermediary handwritten CSV was removed. No regional child-benefit or
HFCS value was transcribed or represented by a placeholder fact: six blocked
official artifacts have deterministic offline-fetch instructions and five
separate follow-up issue bodies.

Chronicle remains facts-only. This wave adds no aging, period alignment,
cross-source reconciliation, imputation, take-up mechanics, support-aware
activation, target profile, model binding, solver construction,
PolicyEngine-computed value, or Axiom concept.

## SFPD package and source pin

Artifact:

- publisher: Service fédéral des Pensions (SFPD);
- URL: `https://www.sfpd.fgov.be/files/3432/fr_stat_2502.pdf`;
- filename: `fr_stat_2502.pdf`;
- SHA-256:
  `0d6173e71a0e9c2cd220cd024a5b5fecbb6ca79f8b791cbd2b3368e7f8412106`;
- size: 2,319,705 bytes;
- vintage: `monthly_social_benefits_2025_02`;
- parser: `pdf_text_numbers`, preserving 13,644 full-document cells.

| Fact | Exact publisher period | Source cell / number text | Value |
|---|---|---|---:|
| Employee and/or self-employed legal-pension beneficiaries | Snapshot at 2025-02-01 | Table 2.2 `E881` / `D881` `2.435.457` | 2,435,457 |
| Employee and/or self-employed legal-pension monthly expenditure | February 2025 | Table 2.2 `E878` / `D878` `3.759.582.728,06` | EUR 3,759,582,728.06 |
| GRAPA beneficiaries | February 2025 | Table 2.4.1 `E1756` / `D1756` `117.650` | 117,650 |
| GRAPA monthly expenditure | February 2025 | Table 2.4.1 `E1757` / `D1757` `86.398.449,47` | EUR 86,398,449.47 |

Every fact has `assertion: observation`, `provenance_class: administrative`,
country geography `BE` / `current`, exact URL/hash/size/vintage provenance,
and source-cell keys. Page/line/number/table-title guards bind table 2.2 to
printed page 22 and table 2.4.1 to printed page 36. The GRAPA count uses a
declared `value_scale: 1000` solely to restore SFPD's single-dot grouped integer
from the parser's backward-compatible decimal representation.

The pension population is deliberately narrowed to the employee and/or
self-employed regimes in table 2.2; it is not labelled as an all-regime total
and does not include a civil-servant column. Its published expenditure total
includes the table's pension-plus-bonus, other pension-bonus, and well-being
bonus components; Chronicle preserves that publisher total without
reclassification.

The manifest's R2 metadata reuses the content-addressed object path first
recorded for the same PDF on the inspected unmerged GRAPA branch. The Git blob,
hash, size, and metadata match. Authenticated R2 availability was not verified,
so the pointer must be treated as metadata pending an authenticated inventory
or read.

## Original issue-69 selector audit

Issue 69 is open. The six original selectors all remain registered and unique
on current main and resolve 587 valid facts in total. PR 207 supplied geography
and offline-fetch authoring prerequisites; it did not supply these fact
packages.

| Alias | Selector `(source, geography, measure, period)` | Facts | Geography vintage |
|---|---|---:|---|
| `statbel-population-structure-2026` | `statbel_population_structure`, `nuts1`, `people`, 2026 | 18 | `NUTS_2024` |
| `statbel-fiscal-income-2023-nis-2025` | `statbel_fiscal_income`, `commune`, `belgium_pit_taxable_income`, 2023 | 565 | `NIS_2025` |
| `spf-finances-pit-2023` | `spf_finances_pit`, `country`, `belgium_pit_federal_and_local_tax_before_withholding`, 2023 | 1 | `current` |
| `onss-contributions-2024` | `onss_contributions`, `country`, `belgium_worker_article_17_uncapped_component_contribution`, 2024 | 1 | `current` |
| `onem-rva-unemployment-2024` | `onem_rva_unemployment`, `country`, `receives_unemployment_benefit`, 2024 | 1 | `current` |
| `nbb-national-accounts-household-disposable-income-2024` | `nbb_national_accounts`, `country`, `household_disposable_income`, 2024 | 1 | `current` |

Current artifact pins behind those selectors:

| Alias | Filename | SHA-256 | Bytes |
|---|---|---|---:|
| `statbel-population-structure-2026` | `statbel_population_structure_nuts1_2026.csv` | `b8456b6a7dfd71caf50184ded4f270206f3b36ae188392ade8c4375aad1ecd52` | 5,210 |
| `statbel-fiscal-income-2023-nis-2025` | `statbel_fiscal_income_commune_2023_nis_2025.csv` | `732bb3945d080c06bba2609bd55d24af0f12859840d6f6b7c3c85de8f93eed75` | 101,316 |
| `spf-finances-pit-2023` | `spf_finances_pit_country_2023.csv` | `7651aaf315f51b78d7fdbe162d6e346cc254793df02833d114c0ca5b1acf3957` | 287 |
| `onss-contributions-2024` | `onss_worker_contributions_2024.csv` | `7fcf5d07c717bcbbd18c2deddc4d7706155f7e4ffcc07161163eae3589ae1958` | 341 |
| `onem-rva-unemployment-2024` | `onem_rva_unemployment_2024.csv` | `b0b42bc0e0e5d449108290be3b235c4736f5e160a817ea5bf32edbc4779c62f7` | 687 |
| `nbb-national-accounts-household-disposable-income-2024` | `nbb_household_disposable_income_2024.csv` | `72067b13a0ae3d85cd10650bfb152aa3228657e12255c32175e11d06eee28bbe` | 292 |

All six `validate-package` commands returned zero errors and warnings. This is
a resolution audit; it does not claim that every existing curated artifact has
the stronger direct-publisher-byte fidelity added to SFPD in this wave.

## Unresolved official sources

`FETCH-MANIFEST-BELGIUM-PUBLIC-FACTS.json` validates under
`ledger.offline_fetch_manifest.v1` with required discovery notes and six
artifacts:

1. Opgroeien native Groeipakket caseload export;
2. Opgroeien native Groeipakket expenditure export;
3. official AVIQ 2021 annual-report PDF;
4. official Iriscare 2024 annual-report PDF;
5. raw official Ostbelgien Statistik family-allowance HTML/endpoint response;
6. official ECB HFCS Wave 2023 statistical-tables ZIP, version 5.0 / June 2026.

Each instruction requires unchanged native publisher bytes, exact filters and
period/scope/unit labels, SHA-256, byte size, content-addressed storage, and a
stop when native data are unavailable or ambiguous. No browser card,
screenshot, OCR output, search snippet, accessibility text, or manual
transcription is permitted.

Ready-to-file issue bodies are committed at:

- `docs/issue-drafts/belgium-opgroeien-native-exports.md`;
- `docs/issue-drafts/belgium-aviq-family-allowances.md`;
- `docs/issue-drafts/belgium-iriscare-family-allowances.md`;
- `docs/issue-drafts/belgium-ostbelgien-family-allowances.md`;
- `docs/issue-drafts/belgium-ecb-hfcs-wave-2023.md`.

## Deterministic validation evidence

- SFPD `validate-package`: PASS, four record sets, four rows, four measures,
  four source records, zero errors/warnings.
- SFPD `build-suite`: PASS, 13,644 source cells, four facts, 100% lineage, zero
  agent-acceptance errors; source-cell and raw-fact reports valid.
- Package-specific `build-bundle`: PASS, four facts, no duplicate keys or
  warnings.
- Facts-only consumer artifact build/load: PASS, four schema-v2 rows, all with
  source-cell lineage.
- All eight other `pdf_text_numbers` packages: PASS after the parser change.
- Six original issue-69 package validators: PASS (18 + 565 + 1 + 1 + 1 + 1
  source records).
- `tests/test_chronicle_source_cells.py` plus
  `tests/test_chronicle_offline_fetch.py`: 50 passed.
- Focused SFPD and Belgium package tests: 3 passed; the current Belgium
  selector uniqueness test separately passed.
- `tests/test_chronicle_facts_only.py` plus
  `tests/test_chronicle_consumer.py`: 33 passed.
- `ruff check .`: PASS.
- `git diff --check origin/main`: PASS.

The 151-package merged-bundle regression was started and then deliberately
interrupted after 20m49s because it had generated 7.4 GB of temporary output
while remaining far from complete. That temporary directory was removed. This
is an incomplete optional global regression, not a passing result. The
relevant SFPD bundle/consumer artifact passed, and the global golden source key
was updated from `sfpd_pensions` to `sfpd_monthly_social_benefits` with its fact
count unchanged at four.

Required judge evidence:

- `ledger-source-fidelity`: **PASS**, no blocking fidelity finding;
- `ledger-boundary`: **PASS**, no facts-only boundary blocker.

## Governance and external blockers

The literal `ledger-source-ingestor.allowed_paths` globs omit paths the user
explicitly required for this task: root `PROGRESS.md`, root offline handoff,
`db/data/**` publisher artifacts/manifests, issue drafts, and the pre-existing
`tests/test_belgium_targets.py`. The work makes no contract, schema, core,
geography transform, model, or consumer-owned change, but strict path
enforcement requires maintainer acceptance or a registry correction before
merge.

External operations could not complete:

- `gh issue create` failed with `error connecting to api.github.com`; none of
  the five follow-up issues was created;
- `git push --set-upstream origin be-public-calibration-facts` failed because
  `github.com` could not resolve;
- `gh pr create --draft` failed because `api.github.com` could not connect;
- `gh auth status` also reports the configured `MaxGhenis` token is invalid.

Therefore no remote branch or PR exists, the proposed body was not published,
and nothing was merged. Once DNS/network and authentication are restored:

1. file the five issue bodies above, retaining `Refs #69`;
2. push `be-public-calibration-facts`;
3. open (do not merge) a draft PR titled
   `Add Belgium pension, GRAPA, and source handoffs` against `main`;
4. use `docs/pr-drafts/belgium-public-facts.md` as the exact body;
5. verify the remote head and rendered PR body before handoff.

The proposed PR-body SHA-256 is
`54c492d27feafb4df68f97385b4c06cd2987ff389ffa84dfcc10f34b21244045`.
It references open issue 69 without closing it.

## Actual commit messages through the reviewed implementation head

1. `f5296028ed62722d199af4a88d07e8f5dd439e3c` — `Start Belgium public facts progress log`
2. `9c2ee9eb0d63309da03f580a7425eba491d32445` — `Track Belgium public facts wave at repository root`
3. `6fd6b91b9d3df9f07873fd917f18eb3979a657d9` — `Parse European-formatted publisher document numbers`
4. `339717e108242e5c157df1164f8a2ba29bc76cd3` — `Back SFPD pension and GRAPA facts with publisher PDF`
5. `a8b5cf46c6465e84e0e57f717049482a289e0667` — `Add offline handoffs for blocked Belgium sources`
6. `9abffbf830779840660e7ebe3b2dc218a7a92dc8` — `Draft follow-up issues for blocked Belgium facts`
7. `6d3694dfa03626625a1af9f802469d40f19d14b1` — `Normalize Belgium issue draft endings`
8. `94a298adf9909edfd15453f387a23b4aeec83125` — `Record Belgium validation and bundle coverage`
9. `206ebfa38bdc65ed4d89f416cf3cbf78eada81dd` — `Prepare Belgium public facts draft PR`
