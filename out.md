# Chronicle #143 mechanism 1, step 1 report

## Outcome

Dual-domain acceptance is implemented across Chronicle's fact identities,
artifact/schema pins, bundle ingestion, relational load path, source-package
readers, source lineage, and governance validation. Emission remains Ledger-era
through the single `EMIT_EPOCH = Epoch.LEDGER` default. Chronicle-era and mixed
rows are accepted; unknown identity domains are rejected with errors naming both
accepted forms.

PR: **PENDING — updated immediately after PR creation**

No PR was merged and no comment was added to issue #143.

## Scope and identity behavior

- Added `chronicle/epoch.py` as the immutable registry of Ledger identifiers and
  Chronicle successors.
- Preserved canonical payloads and digest suffixes across epochs; only the
  domain/schema string changes.
- Kept all default output Ledger-named, including package scaffolds and
  relational/build artifacts. Chronicle output requires an explicit epoch
  override and exists only to exercise acceptance before a future gated flip.
- Left the retired profile-bearing consumer artifact and resolved-target/target-
  profile contracts retired. The repository's live facts-only consumer artifact
  is `policyengine_ledger.consumer_artifact.v2`, so its successor is
  `policyengine_chronicle.consumer_artifact.v3`.
- Did not change any source values, reference periods, publisher provenance,
  fixture/golden bytes, frozen schemas, witnessed releases, CLI/env/bucket/
  Supabase names, or consumer-owned model contracts.

## Files changed

Progress and report:

- `PROGRESS.md`
- `out.md`

Epoch registry and runtime acceptance:

- `chronicle/epoch.py`
- `chronicle/artifacts.py`
- `chronicle/bundle.py`
- `chronicle/consumer_contract.py`
- `chronicle/core.py`
- `chronicle/database.py`
- `chronicle/source_package.py`
- `chronicle/sources/admin_packages.py`
- `chronicle/sources/cells.py`
- `chronicle/sources/offline_fetch.py`
- `chronicle/sources/rows.py`
- `chronicle/suite.py`
- `packages/statbel/fiscal_income_distribution_2023/build_package.py`
- `policyengine_chronicle/consumer.py`
- `policyengine_chronicle/schema.py`

Adversarial and end-to-end tests:

- `tests/test_belgium_targets.py`
- `tests/test_chronicle_artifacts.py`
- `tests/test_chronicle_bundle.py`
- `tests/test_chronicle_consumer.py`
- `tests/test_chronicle_consumer_contract.py`
- `tests/test_chronicle_core.py`
- `tests/test_chronicle_database.py`
- `tests/test_chronicle_governance.py`
- `tests/test_chronicle_offline_fetch.py`
- `tests/test_chronicle_source_cells.py`
- `tests/test_chronicle_source_package.py`
- `tests/test_chronicle_suite.py`
- `tests/test_policyengine_chronicle_schema.py`

## Role-path disclosure

Approved role: `ledger-contract-maintainer`.

The role directly permits `chronicle/core.py`,
`chronicle/consumer_contract.py`, `policyengine_chronicle/**`,
`tests/test_chronicle_consumer_contract.py`, and
`tests/test_chronicle_core.py`. The following required work is outside that
narrow allowlist and is disclosed explicitly:

- `PROGRESS.md` and `out.md`: required standing-order records.
- `chronicle/epoch.py`: the assignment's required central registry.
- `chronicle/artifacts.py`, `chronicle/bundle.py`, `chronicle/database.py`,
  `chronicle/source_package.py`, `chronicle/sources/cells.py`,
  `chronicle/sources/offline_fetch.py`, `chronicle/sources/rows.py`, and
  `chronicle/suite.py`: readers/validators needed for complete dual-epoch
  acceptance and end-to-end lineage, bundle, and relational coverage.
- `chronicle/sources/admin_packages.py` and
  `packages/statbel/fiscal_income_distribution_2023/build_package.py`: package
  generators that must continue to emit the registry's Ledger default.
- `tests/test_belgium_targets.py`, `tests/test_chronicle_artifacts.py`,
  `tests/test_chronicle_bundle.py`, `tests/test_chronicle_consumer.py`,
  `tests/test_chronicle_database.py`, `tests/test_chronicle_governance.py`,
  `tests/test_chronicle_offline_fetch.py`,
  `tests/test_chronicle_source_cells.py`,
  `tests/test_chronicle_source_package.py`, `tests/test_chronicle_suite.py`, and
  `tests/test_policyengine_chronicle_schema.py`: adversarial/end-to-end coverage
  required by the assignment but outside the role's three exact test paths.

These out-of-role paths are necessary to land acceptance at every Chronicle
ingress before an emit flip. They do not add facts or move a consumer-owned
measurement/selection responsibility into Chronicle.

## Deterministic verification

### Full tests

Command:

```text
uv run pytest -q
```

Result:

```text
783 passed, 1 skipped, 14 warnings in 1304.54s (0:21:44)
```

After the full run exposed a bundle-boundary regression during development, the
boundary was corrected and the two affected full-build tests plus the three
dual-epoch bundle ingestion tests passed independently:

```text
5 passed, 13 warnings in 916.77s (0:15:16)
```

The clean full-suite result above is after that correction.

### Ruff

Command and result:

```text
$ uv run ruff check .
All checks passed!
```

The exact repository-wide format command reports a pre-existing baseline
failure:

```text
$ uv run ruff format --check .
Would reformat: tests/test_chronicle_council_tax_nation_totals.py
Would reformat: tests/test_chronicle_facts_only.py
Would reformat: tests/test_chronicle_obr_council_tax_decomposition.py
Would reformat: tests/test_chronicle_pe_source_plan.py
Would reformat: tests/test_chronicle_source_rows.py
Would reformat: tests/test_etl_admin_packages.py
Would reformat: tests/test_etl_snap.py
Would reformat: tests/test_scale_value.py
8 files would be reformatted, 117 files already formatted
```

All eight reported files are byte-identical to `origin/main` (`git diff --quiet`
exit 0). A supplemental check over every Python file changed by this branch
passes:

```text
28 files already formatted
```

### Wheel and clean-venv smoke

The first isolated `uv build` attempt could not resolve Hatchling because the
sandbox has no DNS/network access. Retrying with the already cached Hatchling
build components and `--no-build-isolation` succeeded:

```text
Building source distribution...
Building wheel from source distribution...
Successfully built policyengine_chronicle-0.1.0.tar.gz
Successfully built policyengine_chronicle-0.1.0-py3-none-any.whl
```

The wheel was installed with `pip --no-deps` into a newly created temporary
Python 3.14 venv. An isolated import ran from `/private/tmp`, loaded
`chronicle` from that venv's `site-packages`, imported `chronicle.epoch`, and
asserted the Ledger default and registered fact prefix:

```text
wheel epoch import smoke: PASS
```

### Immutability and review checks

- `git diff --check`: PASS.
- No changed paths under `releases/`, `chronicle/fixtures/`, `docs/schemas/`,
  `policyengine_chronicle/schemas/`, or `.github/chronicle-agents.yml`.
- Frozen fixture SHA-256 assertions pass:
  - `facts.jsonl`: `b0dd06765db7932c16a678b1ab321a7d908af26e2f2014d7da99c0eb5127e401`
  - `consumer_facts.jsonl`: `6123f1cca28ccc72c053b105b8d50b5c25a72a5f5b92e73e7219f32de152a96a`
  - `soi_table_1_1_2023_cells.jsonl`: `615639f21ee63e54595c677e24c3eddff484c00a795a2f91b45a8575f021c7e2`
- Both frozen consumer-schema copies remain
  `76ac268e626c86146cee51193e0cbecbb197ddbf3bf410156fe7da7c0edae3ad`.
- Independent `ledger-contract` judge: **PASS**. Identifier normalization
  preserves publisher values, reference periods, provenance, and lineage; no
  Microcosm contract responsibility moved into Chronicle.
- Independent `ledger-boundary` judge: **PASS**. No reconciliation, aging,
  imputation, support-aware activation, solver construction, target profile, or
  model-measurement binding was added.
- `ledger-source-fidelity`: not required for the selected contract-maintainer
  role; no source facts or publisher artifacts changed.

## Consumer validators required before any emit flip

The following are identified by Max's #143 migration spec and Chronicle's own
handoff docs/tests/workflows. They are not changed in this Chronicle PR:

1. **Microcosm `require_pins` and facts-only artifact/target-contract load**
   must accept both consumer-artifact IDs (`policyengine_ledger...v2` and
   `policyengine_chronicle...v3`), both consumer-row schema IDs, all Ledger and
   Chronicle fact-key domains, and mixed-epoch rows. Exact key verification must
   infer the epoch from each row key. Chronicle's
   `docs/target-construction-harness-plan.md` assigns hash-pinned artifact and
   fact resolution to Microcosm CI.
2. **Brier append gate** must accept both naming epochs and recompute keys from
   the epoch declared by each key, byte-identically with Chronicle. The separate
   external assertion-ID (`av2`) contract remains in force.
3. **Vidimus `append_gate` and `release_chain`** must dual-accept the updated
   pins/specs and complete the required fresh byte-equivalence proof at
   Chronicle's current pin before consumption moves.
4. **Chronicle-hosted Thesis append workflow** must exercise those Vidimus
   changes in both trusted-base and ordinary `check_thesis_facts_append.py`
   paths, including `tests/test_policyengine_chronicle.py`,
   `tests/test_release_chain.py`, and
   `tests/test_thesis_append_adversarial.py`.

Scope distinctions: `microcosm-dynamics` is explicitly outside this migration;
Thesis branch-string pin tools are mechanism 2; and María's publish-flow naming
is mechanism 3. None is part of this acceptance-only code change.

## Residual risks

- Emit must not flip until the consumer validators above are proven dual-epoch
  capable. This PR intentionally leaves `EMIT_EPOCH` at Ledger.
- Bundle ingestion intentionally preserves its historical permissive behavior
  for non-identity row shape/type errors; strict row-shape and hash validation
  remains at the consumer-artifact boundary.
- Supabase mirror loading remains an opaque transport. It already accepts
  arbitrary row values, including Chronicle-era keys, but does not reject an
  unknown key domain itself.
- Bundle, coverage, and source-list metadata have no readers in this repository;
  their successor schema IDs are therefore registry-only until a reader exists.
- The repository-wide Ruff format baseline remains red in the eight untouched
  files listed above. Reformatting them would widen this migration PR without
  changing its behavior.
- Retired target-profile and resolved-target v1 contracts deliberately have no
  Chronicle successor. Reintroducing them would violate the current facts-only
  ADR and consumer boundary.
