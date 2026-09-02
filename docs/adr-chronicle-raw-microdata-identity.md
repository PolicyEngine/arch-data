# ADR: Raw microdata in Chronicle is identity, not content

Status: accepted 2026-09-02 (amends the facts-only store; narrows the
"no raw microdata" non-goal in `docs/storage-architecture.md` and
`docs/chronicle-governance.md`). The fail-closed registration path this
ADR relies on (`kind: microdata_release`, access-aware refusal in
`fetch-artifact` and `publish-raw`, `register-artifact`) lands with
chronicle#221. Until it merges, do not point the existing commands at a
licensed or restricted file: they materialize and upload bytes.

## Decision

Chronicle registers every raw microdata release its consumers build from, and
stores none of their content. "Content" means parsed rows, cells, or facts.
Custody of a redistributable public-use file's bytes is not content; custody
of licensed or restricted bytes is never taken at all.

1. **Registration.** A microdata release (CPS ASEC, ACS PUMS, SCF, SIPP, FRS,
   BE-SILC, the IRS PUF, and their successors in every jurisdiction) is a
   source artifact like any publisher workbook: publisher, source URL or
   access route, vintage, SHA-256, size, fetch time, licence, and an access
   class from a closed set (`public`, `licensed`, `restricted`), on a manifest
   declared `kind: microdata_release`. That kind is required, not inferred:
   it is what lets `validate-package`, the suite builder, and every parser
   refuse the file, so a public microdata release can never be mistaken for a
   public aggregate workbook. Registration is manifest-level. It uses the
   `fetch-artifact` / `publish-raw` path extended with an access-aware
   refusal (chronicle#221), and the content-addressed key convention in
   `docs/storage-architecture.md`: `raw/{country}/{source_id}/{package_id}/
   {year}/{sha256}/{filename}` for UK and New Zealand sources, the legacy
   `raw/{source_id}/...` shape for US sources. No source package parses the
   file.
2. **Bytes only where the publisher permits redistribution.** Public-use files
   whose terms allow redistribution (Census public-use files are the model
   case) are archived in the raw bucket under that key. Licensed or restricted
   files (FRS under the UKDS agreement, BE-SILC scientific-use files, the IRS
   PUF) are registered hash-only: no bytes in any Chronicle store, and no
   Chronicle credential grants access to them. Their bytes stay in the
   licensed environments consumers already operate.
3. **No rows, no cells, no facts.** No microdata record, column, or cell
   enters `source_rows`, `source_cells`, the relational registry, or the
   journal. No fact is computed directly from raw microdata by Chronicle, and
   none computed that way by a consumer enters Chronicle. An aggregate a
   publisher computes from its own microdata and publishes is an ordinary
   fact with ordinary provenance; an aggregate a consumer computes from
   microdata is that consumer's artifact.
4. **Consumers point at the registration.** A Microcosm source-stage manifest
   that names a microdata artifact carries the Chronicle artifact reference
   and the same SHA-256, so every root of a build graph resolves to one
   witnessed registration and a build fails closed when its local bytes
   differ from the registered ones.

## Why

- **The publisher record is the thing to witness.** Publishers revise and
  withdraw microdata files: the IRS withdrew the public-use file in 2026, and
  Census reissues ASEC files under the same vintage label. A registered hash
  with a witnessed fetch time is the only durable statement that a given
  release existed and had those bytes. This is the same transparency property
  Chronicle already provides for published tables, applied to the files
  calibration actually starts from.
- **Pins today are scattered and unwitnessed.** Microcosm pins raw inputs in
  per-country manifests, checkpoint metadata, code constants, and command-line
  arguments, with no shared registry, no licence record, and no timestamp
  anyone outside the build can check. A build's root inputs deserve the same
  declared identity as every other node.
- **Content would break what makes the store useful.** Row-level microdata
  would grow the relational registry and journal by orders of magnitude,
  churn on every reissue, and put access-controlled bytes inside the one
  system whose value is that anyone can verify it. Thesis resolves forecasts
  against Chronicle observations; microdata are not observations of anything
  Thesis scores.
- **This keeps the 2026-06-30 ruling.** PR #68 removed microdata parsers,
  adapters, and tracked raw storage from the package. Nothing here brings any
  of that back. Identity registration adds manifests and two manifest fields,
  not code paths that read microdata.

## Consequences

- Manifests gain `licence` (publisher terms, as an identifier or URL) and
  `access` (`public` | `licensed` | `restricted`). Registration of a
  `licensed` or `restricted` artifact records the checksum and access route
  and refuses bytes.
- `docs/storage-architecture.md` narrows its non-goal from "no raw survey or
  administrative microdata" to "no microdata rows or facts, no licensed or
  restricted microdata bytes"; its ownership matrix gains a row for microdata
  releases.
- `docs/chronicle-governance.md` allows registering microdata releases and
  forbids parsing them or holding gated bytes; the `ledger-boundary` judge
  contract in `.github/chronicle-agents.yml` names both refusals, so the
  configured judge cannot pass a change that does either.
- Microcosm's raw-input entries reference Chronicle registrations; the
  consumer side is tracked in PolicyEngine/microcosm.
- Flip conditions for revisiting content: a consumer other than Microcosm
  needs row-level evidence from Chronicle, or a publisher grants
  redistribution of a currently licensed file and Chronicle has an
  access-controlled tier designed for it. Neither holds today.
