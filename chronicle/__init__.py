"""Chronicle source-data foundation.

Chronicle owns government-statistics releases: source artifacts (including
registrations of raw microdata releases and custody of redistributable
public-use bytes), source-backed facts, constraints, and provenance. Microdata
content (records, rows, columns, row values, cells, and facts derived from raw
microdata), licensed or restricted microdata bytes, selection contracts, source reconciliation, aging,
imputation, target activation, and calibration belong in downstream systems
such as Microcosm.
"""

__all__ = [
    "bundle",
    "client",
    "concepts",
    "consumer_contract",
    "core",
    "database",
    "facts",
    "harness",
    "jurisdictions",
    "mirror",
    "normalization",
    "source_package",
    "store",
    "sources",
    "suite",
    "targets",
]
