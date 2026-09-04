# Operational rename, slice 1 (chronicle#143, mechanism 3)

Lane C5's handoff notes previously lived here; its durable record is
`LANE_C5_REPORT.md`. This file now tracks the active lane on this branch.

## State

- Branch: `ops-rename-slice1`, cut from `origin/main` at `ff3efd3`.
- Scope: env names, R2 bucket configurability, `ledger.db` -> `chronicle.db`,
  and the docs for all three. Code and docs only; no infrastructure changes.
- Out of scope and deliberately untouched: the `ledger` console-script alias,
  the Supabase `"ledger"` schema and mirror table names, governance role ids and
  concept authorities, hash domains and schema ids, anything under `releases/`.
- This PR does not touch the source-data boundary. No package spec, parser,
  selector, manifest, or fact value changes.

## Done

- Read `AGENTS.md`, `docs/storage-architecture.md`,
  `docs/agent-source-package-harness.md`, and the mechanism-3 migration spec in
  the first comment of PolicyEngine/chronicle#143.
- Enumerated every ledger-named env read in tracked Python: the four real
  variables (`LEDGER_SOURCE_ARTIFACT_CACHE_DIR`, `LEDGER_SOURCE_ARTIFACT_FETCH`,
  `LEDGER_PE_US_DATA_ROOT`, `LEDGER_PE_UK_DATA_ROOT`) plus
  `POLICYENGINE_LEDGER_SCHEMA`. `LEDGER_MIRROR_TABLES`,
  `LEDGER_MIRROR_PRIMARY_KEYS`, and `LEDGER_DB_SCHEMA_VERSION` are module
  constants, not env reads, and name out-of-scope surfaces.
- Added `chronicle/env.py`: one shared `env_value`/`env_flag`/`env_names`
  helper reading `CHRONICLE_<X>` first, then `POLICYENGINE_LEDGER_<X>` and
  `LEDGER_<X>` with a once-per-process `ChronicleEnvDeprecationWarning` naming
  the preferred variable.
- Replaced all three ad-hoc helpers (`db/supabase_client._env`,
  `chronicle/source_package._env_value`/`_truthy_env`,
  `db/pe_source_inventory._env_value`) with the shared helper.
- Made the R2 bucket names configurable via `CHRONICLE_R2_RAW_BUCKET` and
  `CHRONICLE_R2_DERIVED_BUCKET`, plumbed through fetch-artifact, publish-raw,
  publish-derived and bootstrap-r2. Defaults unchanged at `ledger-raw` and
  `ledger-derived`. Both manifest write paths now preserve a recorded
  `storage.r2` block instead of restating it under a renamed bucket.
- Emitted `chronicle.db` for new suite outputs, with `ledger.db` still accepted
  on read and on derived-artifact kind inference.
- Added `tests/test_chronicle_env.py` plus artifact tests: 75 hermetic tests
  covering the lookup ladder, precedence, the once-per-process warning, and every
  real call site.
- Swept the docs. `docs/storage-architecture.md` gained an "Environment Variable
  Rename Window" section (the old text stated the fallback direction backwards)
  and a "Bucket Cutover" section; `docs/agent-source-package-harness.md` and
  `README.md` follow. Verified 186 distinct `ledger-raw` objects across 154
  tracked manifest files, every key content-addressed by sha256.

## Review fixes (gate round 1)

The Fable+Sol gate requested changes; both findings are applied on this branch.

- **[high] `fetch-artifact` could attach a recorded R2 URI to new bytes.** The
  preserve rule keyed on the bucket, so a repeated fetch that did not re-upload
  into the same bucket kept the recorded `storage.r2` block while rewriting the
  entry's `sha256`/`size_bytes`. Reproduced against this branch's parent by
  serving two different bodies from one URL: the entry ends up declaring the
  fetched bytes' `sha256` under a key addressed by the superseded bytes' one,
  both when the fetch only registers the bytes and when the bucket default has
  moved.
  The rule now keys on identity — the recorded key's `{sha256}/{filename}` tail
  against the fetched bytes. Identical preserves the block exactly; different
  raises `SourceArtifactRevisionError` before the cached artifact or its
  manifest entry is touched, naming recorded and fetched `sha256`/`size_bytes`
  and the ADR rule that same vintage plus new bytes is a new release revision.
  `--record-revision` opts in: the new bytes get their own content-addressed key
  under the configured bucket, never the old key, and the superseded block moves
  to `storage.previous_r2`. `publish-raw` applies the same check before treating
  a recorded block as history (`recorded_r2_identity_mismatch`, nothing
  uploaded).
- **[low] Env isolation was scoped to one module.** The autouse fixture moved to
  `tests/conftest.py` and now clears all three prefixes for every test.
  `db.supabase_client` resolves `LEDGER_SCHEMA` at import — during collection,
  before any fixture — so `tests/test_chronicle_namespace.py` re-imports it
  under the cleared environment instead of asserting the constant it bound at
  collection time.

`storage.previous_r2` is a sibling key, chosen because every reader
(`inventory-artifacts`, `publish-raw`, `source_package._artifact_content`, the
suite's raw-R2-link acceptance check) reads `storage.r2` alone, and
`publish-raw` already spreads the rest of the `storage` block when it writes
back, so a revision survives publication untouched. All 180 tracked manifest
entries that carry a `storage.r2` block are content-addressed and agree with
their declared `sha256` and `filename`, so the identity check never fires on
tracked data.

## Review fixes (gate round 2)

The second Fable+Sol gate requested changes again. Seven findings, each fixed
with a regression test on this branch. Plan, in dependency order:

1. **[high] `CHRONICLE_SCHEMA` does not reach the Supabase mirror writer.**
   `chronicle/harness.py` and `chronicle/mirror.py` default the schema to the
   literal `"ledger"`; only `db.supabase_client` reads the renamed variable.
   Resolve through the shared helper whenever no explicit `--schema` is given.
2. **[high] The derived-fact boundary check is not rename-safe.**
   `chronicle/consumer_contract.py` matches the `.ledger_derived` suffix only.
3. **[high] `fetch-artifact` cannot address a package's non-default manifest.**
   Seven tracked packages keep a `manifest_*_source_package.yaml`; three
   directories keep two. A fetch into one of them writes a third manifest and
   never sees the recorded block.
4. **[high] Revision protection vanishes when the entry has no `storage.r2`.**
5. **[medium] Recorded-R2 locator fields must be cross-checked**, not read as
   key-or-URI, before a block is preserved or published.
6. **[medium] `_read_manifest` must reject a malformed document**, not treat a
   non-mapping YAML payload as an absent manifest.
7. **[low] Schema resolution must be lazy** so no legacy variable is read at
   collection, before the autouse isolation fixture runs.

## State (round 2)

- Read both gate rounds on PolicyEngine/chronicle#226 and the code each finding
  names.
- Scanned all 154 tracked manifest files (187 `files` entries, every one
  carrying `storage.r2`): every recorded block supplies provider, bucket, key
  and uri; every key is content-addressed; every declared `sha256`/`filename`
  agrees with its key tail; no `uri` contradicts its `key`. Strict locator
  validation therefore refuses nothing that is tracked today.
- All seven findings are applied, each with a regression test, and each
  reproduced against this branch's previous head (`34d1d0f`) first.

### What each fix does

1. `chronicle/env.py` gains `default_chronicle_schema()`: one home for the
   `CHRONICLE_SCHEMA` -> `POLICYENGINE_LEDGER_SCHEMA` -> `LEDGER_SCHEMA` ->
   `"ledger"` ladder. `load_supabase_mirror`, its harness wrapper and the
   `--schema` CLI default all resolve through it when no schema is supplied;
   an explicit `--schema` still wins. Defaults unchanged.
2. `chronicle/consumer_contract.py` matches the whole final dot-segment of a
   `source_record_id` against both `ledger_derived` and `chronicle_derived`.
3. `fetch-artifact --manifest <filename>` selects which of a package's
   manifests the entry belongs to (default `manifest.yaml`); the name must be
   a filename inside `--out-dir`.
4. Revision protection now compares against the entry's recorded identity --
   the recorded key's `{sha256}/{filename}` once published, the declared
   `sha256` before that -- so a registered-but-unpublished entry, or one whose
   upload failed, is protected exactly like a published one.
5. `_validated_recorded_r2` cross-checks every supplied locator field against
   every other and against the content-addressed key shape. A contradiction is
   `RecordedR2LocatorError` at fetch time and `recorded_r2_locator_invalid` at
   publish time, never a preserved block.
6. `_read_manifest` refuses a non-mapping or unparseable document
   (`MalformedManifestError`) before the publisher is read at all;
   `inventory-artifacts` and `publish-raw` report it instead of crashing.
7. `db.supabase_client` resolves both schemas per call rather than at import,
   and `tests/conftest.py` strips the rename window in `pytest_configure`, so
   no module can read or warn from an operator's shell during collection.

All four refusals share a `SourceArtifactManifestError` base, so the
`fetch-artifact` CLI reports every one as exit 1 with nothing written.

### Reproduced against `34d1d0f` (the round-1 head)

Running the same operations against a checkout of the previous head:

1. `load_supabase_mirror` default `schema='ledger'`; with
   `CHRONICLE_SCHEMA=chronicle_probe` the load still reports `schema='ledger'`.
2. `'.chronicle_derived'.endswith('.ledger_derived')` is False: the boundary
   never fired for the chronicle spelling.
3. `fetch_source_artifact()` rejects `manifest_filename` as an unexpected
   keyword; a fetch into `ira_contributions/` writes `manifest.yaml`.
4. A fetch of different bytes over a registered (unpublished) entry was
   accepted silently: the entry's `sha256` was rewritten with no refusal.
5. A block whose `key` and `uri` named different objects was preserved
   verbatim, key sha `c63744a4...` beside uri sha `1e9b3fdb...`.
6. A list-valued `manifest.yaml` was overwritten by the fetch.
7. Importing `db.supabase_client` under `LEDGER_SCHEMA=zzz` bound
   `LEDGER_SCHEMA='zzz'` and emitted a `FutureWarning` at collection.

## Verification

- `uv run pytest -q`: green.
- `uv run ruff check .`: clean.
- `uv run ruff format --check .`: clean for every file this branch touches. 13
  files are unformatted on `main` already and are byte-identical here; CI runs
  `ruff check` only, so they are pre-existing and out of scope.
- CI's db CLI gate (`chronicle init` / `load all` / `stats`): passes.
- `CHRONICLE_R2_RAW_BUCKET=zzz CHRONICLE_SCHEMA=zzz uv run pytest -q`: green.
  Before the shared fixture it failed five tests — four bucket-default
  assertions in `tests/test_chronicle_artifacts.py` and the collection-time
  schema constant in `tests/test_chronicle_namespace.py`.

## Next

- Push and open the PR against `main`. Do not merge.
- Follow-up PR, after Max creates and backfills the new buckets: flip
  `DEFAULT_R2_RAW_BUCKET` / `DEFAULT_R2_DERIVED_BUCKET` to `chronicle-raw` /
  `chronicle-derived`.

## Review fixes (Sol gate round 3)

### State

- Detached HEAD: `fb1bc1df`, the PR #226 head supplied for the ten-finding Sol
  gate round.
- Scope: ten operational-rename findings in artifact fetch/publish/inventory,
  Supabase compatibility aliases, and the README cutover procedure. No tracked
  `db/data/**` manifest will be changed.
- `CLAUDE.md`, one of the requested initial reads, is absent from both this
  worktree and `/Users/maxghenis/PolicyEngine/chronicle`; `AGENTS.md` and the
  remaining requested guidance/code/tests are present.
- PR #227 is available read-only at
  `/Users/maxghenis/PolicyEngine/_worktrees/chronicle-227-fix`. Applicable
  non-microdata hunks from `daafac0` and `c0d9d74` will be ported with the same
  function names and shapes.

### Done

- Re-established the lane state in this committed progress log before making
  gate-round code or test changes.
- Read `AGENTS.md`, the Bucket Cutover and Publisher Revisions contracts in
  `docs/storage-architecture.md`, the README cutover instructions, and the
  named implementation/test surfaces. Confirmed Chronicle must preserve
  publisher bytes and provenance, refuse unsafe fetches before I/O, and leave
  schema/bucket value cutovers explicit.
- Reproduced findings 1, 4, 5, and 8 with 11 failing cases: mismatched manifest
  identity reached the publisher read, quoted year keys bypassed revision
  protection, duplicate year spellings and malformed entries reached I/O, and
  both refetch and revision discarded entry metadata.
- Ported the non-microdata parts of #227's `_assert_manifest_identifies`,
  `_select_vintage_entry`, `_FETCH_OWNED_FIELDS`, and in-place
  `_upsert_manifest` flow. Fetch now validates manifest identity and entry
  shape before I/O, resolves either year-key spelling while refusing both,
  preserves the recorded key spelling, and carries forward every field it does
  not own. The 11 focused cases now pass.
- Reproduced finding 2 with both default sweeps reporting only one of four
  supported manifest names, and finding 7 with all four falsy non-mapping
  `files` values producing `(inventory.valid, publish.valid) == (True, True)`.
- Ported #227's `is_manifest_filename` / `package_manifest_paths` shapes and
  made default root sweeps discover `manifest.yaml`, `manifest.yml`, and both
  `manifest_<package>` extensions. Both sweeps now share `_manifest_files`, so
  only `None` means absent and every other non-mapping value is reported. All
  106 artifact tests pass.
- Reproduced finding 3 as a green preserved-bucket skip for a key routed to the
  wrong package/year, and finding 6 as both a fetch reaching I/O and a green
  publish skip for a self-consistent `s3://` block under `storage.r2`.
- Raw publish now compares the recorded key with the canonical
  source/package/year key before any bucket-change skip. Recorded R2 validation
  also requires `provider='r2'` (and therefore an `r2://` effective URI). The
  focused canonical-key/provider tests, including the existing URI-only and
  stale-country cases, pass without uploads or manifest rewrites on refusal.
- Reproduced finding 9 with the shipped import raising `ImportError` for
  `LEDGER_SCHEMA`, then restored `LEDGER_SCHEMA` and `TARGETS_SCHEMA` as
  deprecated aliases of the stable defaults. Runtime queries remain on the
  lazy functions and still honor post-import environment changes; 55 focused
  namespace/env/client cases pass (1 skipped for absent real credentials).
- Reproduced both parts of finding 10: the README did not state that an
  unqualified mirror load writes to `ledger`, and it named the absent
  `supabase/migrations/20260504_chronicle_bronze.sql` file.
- README now instructs operators to create and apply the deployment migration,
  states the `ledger` runtime default, and gives both supported ways to target
  `chronicle`. The storage architecture and source-package harness use the same
  truthful procedure; no documentation names the absent SQL file. Both README
  regression tests pass.
- Adversarial review tightened the same contracts before final verification.
  Mixed-case package manifests were reproduced as omissions from both root
  sweeps and from the stray-default guard; default discovery now filters every
  recursive filename through the case-insensitive #227 helper. Missing
  `provider` and missing `uri` locators were each reproduced reaching publisher
  I/O; `storage.r2` now requires explicit `provider: r2` and an `r2://` URI.
  The artifact file's 112 tests pass.
- Clarified that *all* schema environment overrides, including deprecated
  spellings, precede the `ledger` default. The README test now also requires
  the create/apply-migration instruction, so deleting the guidance cannot pass
  vacuously. All 14 mirror tests pass.
- Completed the remaining non-microdata preflight port from #227. Reproduced
  four invalid explicit/inferred artifact filenames reaching `_read_artifact`,
  including `filename=manifest.yaml`, which could overwrite the selected
  manifest, and reproduced an undiscoverable `custom.yaml` manifest reaching
  publisher I/O. Ported `is_bare_filename`, `bare_filename`,
  `_infer_artifact_filename` from `daafac0`, and the manifest-like artifact
  refusal plus discoverable `_manifest_path` restriction from `c0d9d74`. All
  117 artifact tests pass after the pre-I/O fix.

### Next

- None in this lane. All ten Sol findings, the non-microdata #227 port
  completeness pass, and adversarial follow-ups are committed and verified.
  The final evidence and per-finding commit map are in the runner's external
  `-o out.md` report, not a repository-root file.

### Final verification

- `uv run ruff check .`: exit 0 (`All checks passed!`).
- `uv run ruff format --check` on all six changed Python files: exit 0
  (`6 files already formatted`).
- Full `uv run pytest -q -p no:cacheprovider`: direct exit 0, 995 passed,
  1 skipped, 18 warnings in 1539.05 seconds.
- A fresh `/tmp` copy of tracked USDA `fy69_to_current` reports two manifests
  and two artifacts in inventory. Publish includes both: FY2024 is one safe
  preserved-bucket skip and the known misrouted FY2025 package/year key is one
  explicit failure, with zero uploads. No tracked manifest was changed.
- The external `-o out.md` report records every failing-first command and
  observation, regression test, fix commit, and exact #227 port provenance.

## Review fixes (Sol gate round 2, eight findings)

### State

- Detached HEAD began at `c36f3fc8`, the supplied head of PR #226; base is
  `main` at `9da02431`. The worktree was clean at intake.
- Scope is the eight supplied findings: cutover compatibility, shared-file
  revision ownership, artifact/manifest path safety, duplicate YAML keys,
  malformed revision history, and import-time Supabase alias compatibility.
- No tracked `db/data/**` manifest will be modified. The whole-tree cutover
  regression will operate on a temporary copy and use a non-writing uploader.
- PR #227 is available read-only at
  `/Users/maxghenis/PolicyEngine/_worktrees/chronicle-227-fix` at `5557cb9e`.
  Applicable non-microdata hunks will be ported with the same function names
  and shapes so its later rebase stays straightforward.

### Done

- Read the existing `PROGRESS.md`, the Bucket Cutover and Publisher Revisions
  sections of `docs/storage-architecture.md`, and all six requested code/test
  files: `chronicle/artifacts.py`, `chronicle/harness.py`,
  `chronicle/source_package.py`, `db/supabase_client.py`,
  `tests/test_chronicle_artifacts.py`, and `tests/test_chronicle_env.py`.
- Read the GitNexus debugging/refactoring workflow guidance. No GitNexus MCP
  graph tools are exposed in this session, so dependency tracing will use
  repository search, focused tests, and the stacked PR's committed diffs.
- Confirmed the baseline gaps in the named code: `_read_manifest` still uses
  `yaml.safe_load`; `_root_manifest_paths` passes a non-default value to
  `rglob`; manifest-declared filenames reach direct path joins and reads;
  fetch updates only its selected manifest; `_superseding_storage` converts a
  non-list `previous_r2` to an empty history; and the Supabase compatibility
  constants are hard-coded defaults.
- **Finding 6 reproduced and fixed.** Red command:
  `UV_CACHE_DIR=/tmp/chronicle-uv-cache uv run pytest -q -p
  no:cacheprovider tests/test_chronicle_artifacts.py::test_fetch_refuses_duplicate_manifest_keys_before_publisher_io`
  exited 1 with four failures; every duplicate (`source_id`, `package_id`,
  `files`, vintage) reached the publisher-read sentinel. Test-only commit:
  `56f9ce1`. Ported #227 commit `7f9bfe6`'s `StrictManifestLoader` and
  `load_manifest_document` verbatim into `chronicle/registration.py`, switched
  artifact manifest reads to it, and shared it with source-package artifact
  manifest reads. Fix commit: `77e6fda`. The same focused command now exits 0
  with 4 passed.

### Next

1. Add focused failing regressions before each remaining fix and capture every red
   command/observation for the external `-o out.md` report.
2. Commit each coherent red-test and implementation step, updating this log.
3. Run focused tests, lint/format checks on changed files, and the full suite
   with the directly captured exit code and counts.
