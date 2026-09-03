"""PolicyEngine Chronicle public API.

Chronicle is PolicyEngine's source-backed fact store. This package is the stable
import path for consumers such as Microcosm and Thesis.
"""

from chronicle.core import (
    ALLOWED_ASSERTIONS,
    ALLOWED_PROVENANCE_CLASSES,
    DEFAULT_ASSERTION,
    AggregateConstraint,
    AggregateFact,
    Aggregation,
    EntityDimension,
    GeographyDimension,
    Measure,
    PeriodCoverage,
    PeriodDimension,
    SourceProvenance,
    SourceRecordLayout,
    ValidationIssue,
    ValidationReport,
    build_aggregate_constraints,
    build_fact_key,
    build_label,
    validate_fact,
    validate_facts,
)
from policyengine_chronicle.consumer import (
    ConsumerArtifact,
    build_consumer_artifact,
    build_package_consumer_artifact,
    load_consumer_artifact,
)

__all__ = [
    "ALLOWED_ASSERTIONS",
    "ALLOWED_PROVENANCE_CLASSES",
    "DEFAULT_ASSERTION",
    "AggregateConstraint",
    "AggregateFact",
    "Aggregation",
    "ConsumerArtifact",
    "EntityDimension",
    "GeographyDimension",
    "Measure",
    "PeriodCoverage",
    "PeriodDimension",
    "SourceProvenance",
    "SourceRecordLayout",
    "ValidationIssue",
    "ValidationReport",
    "build_aggregate_constraints",
    "build_consumer_artifact",
    "build_package_consumer_artifact",
    "build_fact_key",
    "build_label",
    "load_consumer_artifact",
    "validate_fact",
    "validate_facts",
]
