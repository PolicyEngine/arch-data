# Catalog curation backlog

These series lineages remain split because the catalog builder scopes
concept and alias inheritance to an exact geography and entity slice.
Curating an alias cannot move an observation across entity keys, and the
catalog must not lose observations merely to present one lineage.

On 2026-08-07, a disposable-copy experiment attempted each entity-drift
fold by deleting the unpinned row and adding its canonical concept to the
docket-pinned row. Regeneration restored both rows and produced a catalog
and UUID registry byte-identical to the originals: all seven pairs still
held one observation on each entity. They must remain split until the
upstream observation metadata is corrected.

| Concept | Docket-pinned entity and UUID | Other entity and UUID | Blocker |
| --- | --- | --- | --- |
| `bls.cpi.u.headline_mom` | `household/cpi_u_all_items`, `3e796803-a194-4c83-9dc9-27cc870ff08e` | `economy/aggregate`, `70ca2ecf-4323-4453-b42f-23350cb95f22` | May and June observations disagree on entity. |
| `bls.cpi.u.core_mom` | `household/cpi_u_less_food_energy`, `d85c3c7f-874b-4caa-bfad-1ec7a473c293` | `economy/aggregate`, `e5e402d5-1a65-4c5d-a67a-07e3cf03cbf8` | May and June observations disagree on entity. |
| `bls.cps.unemployment_rate` | `person/civilian_labor_force`, `8dbbd54f-4bfd-4735-ad0d-5b55b8bb4ec5` | `economy/aggregate`, `db2f3857-e0fa-48f8-9ab1-6c8989307fd2` | May and June observations disagree on entity. |
| `fed.g17.industrial_production.total_index_mom` | `economy/aggregate`, `dbfd5050-e5df-40af-8922-dc8927d6363a` | `institutional_sector/total_industrial_production`, `d5634fc4-dbe0-4203-a5b7-728708b85a14` | May and June observations disagree on entity. The same-dimension `us.frb` spelling is folded into the latter row separately. |
| `fed.g17.capacity_utilization.total_industry` | `economy/aggregate`, `9668ecdb-5f61-422d-a653-8e8956257ade` | `institutional_sector/total_industry_capacity`, `978252a9-c452-41eb-aece-323340e796fc` | May and June observations disagree on entity. |
| `census.housing_starts.saar` | `economy/aggregate`, `8c999902-84e2-4e90-b49c-325cd535062a` | `dwelling/housing_start`, `d0212a1e-b360-460a-80a8-1cf4ad5ce427` | May and June observations disagree on entity. The same-dimension `us.census` spelling is folded into the latter row separately. |
| `bls.import_price_index.all_imports_mom` | `economy/aggregate`, `1d271205-0e71-4a74-9d5f-47e77577e2b2` | `household/all_imports`, `e8e6e43e-2c46-4620-a070-91d2da004b1c` | May and June observations disagree on entity. |

## Initial claims cadence metadata

The `us.dol.initial_claims.sa` rows are one weekly series, not a legitimate
weekly/monthly aggregate split. The two observations declared as monthly
carry week-ending identifiers (`2026-06-06` and `2026-06-13`) and values in
weekly thousands, immediately preceding the weekly observations beginning
`2026-06-20`. After folding their two concept spellings, they remain on
`person/ui_initial_claimant` with monthly cadence under UUID
`830e68bb-9ed6-493c-a8a4-440ba8e53f76`; the docket-pinned weekly rows remain
on `person/ui_claimant` under UUID
`1ad67747-d9d8-4ff9-9ebc-58206e658518`. Correct the two upstream rows'
period and entity metadata before folding these lineages; an alias cannot
bridge either mismatch safely.
