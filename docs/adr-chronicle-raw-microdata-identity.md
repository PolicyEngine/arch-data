# ADR: Raw microdata in Chronicle is identity, not content

Status: accepted 2026-09-02 (amends the facts-only store; narrows the
"no raw microdata" non-goal in `docs/storage-architecture.md` and
`docs/chronicle-governance.md`). The fail-closed registration path this
ADR relies on (`kind: microdata_release`, access-aware refusal in
`fetch-artifact` and `publish-raw`, `register-artifact`, the redistributable
licence allowlist) lands with chronicle#221. Until it merges, do not point
the existing commands at any microdata release, public or not: today they
materialize, upload, and parse every input, and a manifest without `kind`
is a publisher table by definition.

## Decision

Chronicle registers every raw microdata release its consumers build from, and
stores none of their content. "Content" means any parsed representation:
microdata records, rows, columns, row values, or cells, and any fact derived
from them by Chronicle or a consumer. Custody of a redistributable public-use
file's bytes is not content; custody of licensed or restricted bytes is never
taken at all.

1. **Registration.** A microdata release (CPS ASEC, ACS PUMS, SCF, SIPP, FRS,
   BE-SILC, the IRS PUF, and their successors in every jurisdiction) is a
   source artifact like any publisher workbook: publisher, source URL or
   access route, vintage, SHA-256, size, licence, an access class from a
   closed set (`public`, `licensed`, `restricted`), and the hash-source and
   verification fields defined below, on a manifest declared
   `kind: microdata_release`. That kind is required, not inferred: it is what
   lets `validate-package`, the suite builder, the source-package byte reader,
   and every parser refuse the file, so a public microdata release can never
   be mistaken for a public aggregate workbook. A manifest without `kind` is
   a publisher table; every existing manifest is one. Registration is
   manifest-level. It uses the `fetch-artifact` / `publish-raw` path extended
   with an access-aware refusal (chronicle#221), and the content-addressed key
   convention in `docs/storage-architecture.md`:
   `raw/{country}/{source_id}/{package_id}/{year}/{sha256}/{filename}` for
   publishers mapped to a country segment (UK and New Zealand today), and the
   legacy `raw/{source_id}/{package_id}/{year}/{sha256}/{filename}` shape for
   every unmapped publisher, US sources included. No source package parses
   the file.
2. **Bytes only with an affirmative redistribution permission.** Being
   downloadable is not a licence. Chronicle archives a release's bytes in the
   raw bucket only when its `access` is `public` **and** its recorded
   `licence` matches an entry in Chronicle's allowlist of redistributable
   terms, maintained in code with the evidence for each entry (for example a
   U.S. Government work under 17 U.S.C. §105, the Open Government Licence,
   CC0, CC BY). A file that is publicly downloadable under any other or
   unstated terms is classed `licensed`, whatever its access route. Licensed
   or restricted files (FRS under the UKDS agreement, BE-SILC scientific-use
   files, the IRS PUF) are registered hash-only: no bytes in any Chronicle
   store, and no Chronicle credential grants access to them. Their bytes stay
   in the licensed environments consumers already operate.
3. **No records, rows, columns, row values, cells, or derived facts.** No
   microdata record, row, column, row value, or cell enters `source_records`,
   `source_rows`, `source_columns`, `source_row_values`, `source_cells`, the
   relational registry, the derived-artifact bucket, or the journal, whether
   the release is public or gated. No fact derived from raw microdata by
   Chronicle or by a consumer enters Chronicle, however many intermediate
   artifacts stand between the microdata and the value. The only exception is
   assertion-based, as everywhere else in Chronicle: an aggregate that a
   publisher computes from its own microdata and publishes is an ordinary
   fact with ordinary provenance.
4. **What a registration attests.** `hash_source` records who computed the
   registered SHA-256: `chronicle_fetch` (Chronicle fetched the bytes and
   hashed them; the registration attests the bytes), `consumer_attested` (a
   consumer that holds the bytes recomputed the hash and recorded the
   evidence; the registration attests the bytes on that consumer's word), or
   `consumer_pin` (transcribed from a consumer's reviewed pin without
   recomputation; the registration attests the pin, not the bytes).
   `verified_at` is the date the recorded hash was last compared against the
   bytes by whoever holds them. The witnessed fetch time in the journal
   bounds when the registration existed; it bounds when the bytes existed
   only for `chronicle_fetch` and `consumer_attested` entries.
5. **Consumers point at the registration.** A Microcosm source-stage manifest
   that names a microdata artifact carries the Chronicle artifact reference
   and the same SHA-256, so every root of a build graph resolves to one
   witnessed registration and a build fails closed when its local bytes
   differ from the registered ones.

## Why

- **The publisher record is the thing to witness.** Publishers revise and
  withdraw microdata files: the IRS withdrew the public-use file in 2026, and
  Census reissues ASEC files under the same vintage label. A registered hash
  with a witnessed fetch time is the only durable statement that a given
  release existed with those bytes. This is the same transparency property
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
  of that back. Identity registration adds manifests and manifest fields, and
  the code it adds refuses to read microdata rather than reading it.

## Consequences

- Manifests gain `licence` (publisher terms, as an identifier or URL),
  `access` (`public` | `licensed` | `restricted`), `hash_source`, and
  `verified_at`; a microdata manifest declares `kind: microdata_release`.
  Registration of a `licensed` or `restricted` artifact records the checksum
  and access route and refuses bytes; registration of a `public` artifact
  archives bytes only when the licence is on the redistributable allowlist.
- `docs/storage-architecture.md` narrows its non-goal from "no raw survey or
  administrative microdata" to "no microdata records, rows, columns, row
  values, cells, or derived facts; no licensed or restricted microdata bytes";
  its ownership matrix gains a row for microdata releases.
  `docs/target-construction-harness-plan.md` is scoped to publisher aggregate
  artifacts; microdata releases are identity-only.
- `docs/chronicle-governance.md` allows registering microdata releases and
  forbids parsing them or holding gated bytes; the `ledger-boundary` judge
  contract in `.github/chronicle-agents.yml` names both refusals in the same
  canonical words, and `tests/test_chronicle_governance.py` pins that
  wording, so the configured judge cannot pass a change that does either.
- Microcosm's raw-input entries reference Chronicle registrations; the
  consumer side is tracked in PolicyEngine/microcosm.
- Flip conditions for revisiting content: a consumer other than Microcosm
  needs row-level evidence from Chronicle, or a publisher grants
  redistribution of a currently licensed file and Chronicle has an
  access-controlled tier designed for it. Neither holds today.
