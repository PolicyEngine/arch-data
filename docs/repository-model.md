# Chronicle Repository Model

Chronicle is global at the schema layer. Jurisdiction packages are modular source
packages that build source-backed Chronicle records for one jurisdiction or source
family.

## Names

```text
GitHub repositories after the rename:
  PolicyEngine/chronicle
  PolicyEngine/ledger-us
  PolicyEngine/chronicle-uk

Python distributions:
  policyengine-chronicle
  policyengine-ledger-us
  policyengine-chronicle-uk

Python imports:
  policyengine_chronicle
  policyengine_chronicle_us
  policyengine_chronicle_uk
```

The `policyengine-` prefix belongs in published distribution names, where
generic names collide. Public imports use the explicit `policyengine_chronicle`
namespace to avoid colliding with unrelated `chronicle` packages.

## Ownership

`chronicle` owns the stable contract:

- source artifact metadata
- parsed source cells
- source record specs
- aggregate facts
- aggregate constraints
- source-to-canonical concept alignments
- stable keys
- validation
- relational DB schema
- fixture/build harness

Jurisdiction packages own source implementations:

- source manifests
- artifact retrieval specs
- source-specific parsers
- selector specs
- source-record specs
- fixture builds for that jurisdiction

They must emit the shared Chronicle schema. They should not define a different fact,
constraint, lineage, validation, or DB model.

## Current State

The current in-repo US loaders are a prototype so the core contract can move
quickly while SOI fixtures exercise the schema. Once the contract stabilizes,
the US loaders should move to `policyengine-ledger-us`, with the core repository
retaining only a small test fixture and the shared harness.
