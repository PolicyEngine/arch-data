"""Consumer-fact row schema validation for Chronicle artifacts.

The pinned ``consumer_fact.v1`` schema is packaged with the wheel so builds and
loads validate every fact row against the exact contract the artifact claims.
The packaged schema bytes are the single source of truth: their sha256 is
recorded in each artifact manifest, and a load rejects any manifest that claims
a different schema.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from functools import lru_cache
from importlib.resources import files as _resource_files
from typing import Any

from chronicle.epoch import SCHEMA_IDS, canonicalize_key
from jsonschema import Draft202012Validator

_SCHEMA_PACKAGE = "policyengine_chronicle.schemas"
_SCHEMA_RESOURCE = "consumer_fact.v1.schema.json"

_TOP_LEVEL_KEY_DOMAINS = {
    "aggregate_fact_key": "aggregate_fact",
    "semantic_fact_key": "semantic_fact",
    "legacy_fact_key": "fact",
    "source_release_key": "source_release",
    "source_series_key": "source_series",
    "observed_measure_key": "observed_measure",
    "dimension_set_key": "dimension_set",
    "universe_constraint_set_key": "universe_constraint_set",
}


def _packaged_schema_bytes() -> bytes:
    return _resource_files(_SCHEMA_PACKAGE).joinpath(_SCHEMA_RESOURCE).read_bytes()


CONSUMER_FACT_SCHEMA_SHA256 = hashlib.sha256(_packaged_schema_bytes()).hexdigest()


@lru_cache(maxsize=1)
def consumer_fact_schema() -> dict[str, Any]:
    """Return the parsed, cached consumer-fact row schema."""
    return json.loads(_packaged_schema_bytes())


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(consumer_fact_schema())


def _epoch_validation_error(
    *,
    line_number: int,
    path: Any,
    location: str,
    error: ValueError,
) -> ValueError:
    return ValueError(
        f"Consumer fact row {line_number} of {path} failed epoch validation "
        f"at {location!r}: {error}"
    )


def _normalize_key(
    key: Any,
    *,
    domain_name: str,
    line_number: int,
    path: Any,
    location: str,
) -> Any:
    # Leave type errors to the frozen JSON schema so its established messages
    # stay stable. String identifiers receive the additive epoch check first.
    if not isinstance(key, str):
        return key
    try:
        return canonicalize_key(domain_name, key)
    except ValueError as error:
        raise _epoch_validation_error(
            line_number=line_number,
            path=path,
            location=location,
            error=error,
        ) from error


def normalize_consumer_fact_row_epochs(
    row: Any,
    line_number: int,
    path: Any,
) -> Any:
    """Return a Ledger-canonical copy of a dual-epoch consumer-fact row.

    The frozen v1 JSON schema remains the byte-identical validation contract.
    This adapter accepts either registered naming epoch on each identifier,
    independently, then normalizes only the copy passed to that schema. The
    caller's row is never mutated, and mixed-epoch rows remain valid.
    """

    normalized = deepcopy(row)
    if not isinstance(normalized, dict):
        return normalized

    schema_version = normalized.get("schema_version")
    if isinstance(schema_version, str):
        pair = SCHEMA_IDS["consumer_fact"]
        try:
            pair.infer_identifier_epoch(schema_version)
        except ValueError as error:
            raise _epoch_validation_error(
                line_number=line_number,
                path=path,
                location="schema_version",
                error=error,
            ) from error
        normalized["schema_version"] = pair.ledger

    for field_name, domain_name in _TOP_LEVEL_KEY_DOMAINS.items():
        if field_name in normalized:
            normalized[field_name] = _normalize_key(
                normalized[field_name],
                domain_name=domain_name,
                line_number=line_number,
                path=path,
                location=field_name,
            )

    concept_alignment = normalized.get("concept_alignment")
    if (
        isinstance(concept_alignment, dict)
        and "concept_alignment_key" in concept_alignment
    ):
        concept_alignment["concept_alignment_key"] = _normalize_key(
            concept_alignment["concept_alignment_key"],
            domain_name="concept_alignment",
            line_number=line_number,
            path=path,
            location="concept_alignment/concept_alignment_key",
        )

    lineage = normalized.get("lineage")
    if isinstance(lineage, dict):
        for field_name, domain_name in (
            ("source_cell_keys", "source_cell"),
            ("source_row_keys", "source_row"),
        ):
            keys = lineage.get(field_name)
            if not isinstance(keys, list):
                continue
            for index, key in enumerate(keys):
                keys[index] = _normalize_key(
                    key,
                    domain_name=domain_name,
                    line_number=line_number,
                    path=path,
                    location=f"lineage/{field_name}/{index}",
                )

    return normalized


def validate_consumer_fact_row_epochs(
    row: Any,
    line_number: int,
    path: Any,
) -> None:
    """Check every epoch-bearing identifier of a row without copying it.

    This is :func:`normalize_consumer_fact_row_epochs` minus the deep copy and
    the rewrite: it raises the same error for the same identifier and leaves
    the caller's row untouched, so a bundle build can validate ~150k rows
    without materializing a canonical copy of each.
    """

    if not isinstance(row, dict):
        return
    schema_version = row.get("schema_version")
    if isinstance(schema_version, str):
        try:
            SCHEMA_IDS["consumer_fact"].infer_identifier_epoch(schema_version)
        except ValueError as error:
            raise _epoch_validation_error(
                line_number=line_number,
                path=path,
                location="schema_version",
                error=error,
            ) from error
    for field_name, domain_name in _TOP_LEVEL_KEY_DOMAINS.items():
        if field_name in row:
            _normalize_key(
                row[field_name],
                domain_name=domain_name,
                line_number=line_number,
                path=path,
                location=field_name,
            )
    concept_alignment = row.get("concept_alignment")
    if (
        isinstance(concept_alignment, dict)
        and "concept_alignment_key" in concept_alignment
    ):
        _normalize_key(
            concept_alignment["concept_alignment_key"],
            domain_name="concept_alignment",
            line_number=line_number,
            path=path,
            location="concept_alignment/concept_alignment_key",
        )
    lineage = row.get("lineage")
    if isinstance(lineage, dict):
        for field_name, domain_name in (
            ("source_cell_keys", "source_cell"),
            ("source_row_keys", "source_row"),
        ):
            keys = lineage.get(field_name)
            if not isinstance(keys, list):
                continue
            for index, key in enumerate(keys):
                _normalize_key(
                    key,
                    domain_name=domain_name,
                    line_number=line_number,
                    path=path,
                    location=f"lineage/{field_name}/{index}",
                )


def validate_consumer_fact_row(
    row: Any,
    line_number: int,
    path: Any,
) -> None:
    """Validate one consumer-fact row against the pinned schema.

    Raises :class:`ValueError` naming the source ``path``, the 1-based
    ``line_number``, the failing JSON location, and the schema reason. The
    first error by schema location is reported so the message is stable.
    """
    normalized = normalize_consumer_fact_row_epochs(row, line_number, path)
    errors = sorted(
        _validator().iter_errors(normalized),
        key=lambda error: (
            [str(part) for part in error.absolute_path],
            error.message,
        ),
    )
    if not errors:
        return
    error = errors[0]
    location = "/".join(str(part) for part in error.absolute_path) or "<root>"
    raise ValueError(
        f"Consumer fact row {line_number} of {path} failed schema validation "
        f"at {location!r}: {error.message}"
    )


__all__ = [
    "CONSUMER_FACT_SCHEMA_SHA256",
    "consumer_fact_schema",
    "normalize_consumer_fact_row_epochs",
    "validate_consumer_fact_row",
    "validate_consumer_fact_row_epochs",
]
