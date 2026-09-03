"""Build and verify facts-only Chronicle consumer artifacts.

Chronicle publishes source-backed fact rows and the hashes needed to verify
them. Selection, measurement, period-alignment, and model-binding contracts
belong to consumers such as Microcosm.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from chronicle.consumer_contract import _hash_key
from chronicle.core import (
    ALLOWED_ASSERTIONS,
    ALLOWED_PROVENANCE_CLASSES,
    DEFAULT_ASSERTION,
)
from policyengine_chronicle.schema import (
    CONSUMER_FACT_SCHEMA_SHA256,
    validate_consumer_fact_row,
)

CONSUMER_ARTIFACT_SCHEMA_VERSION = "policyengine_ledger.consumer_artifact.v2"
SOURCE_ACCESS_VALUES = frozenset({"public", "licensed", "restricted"})
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")
_PACKAGE_IDENTITY_FIELDS = (
    "source_id",
    "package_id",
    "chronicle_source_commit",
    "source_access",
)


@dataclass(frozen=True)
class ConsumerArtifact:
    """A verified facts-only Chronicle consumer artifact."""

    path: Path
    manifest: dict[str, Any]
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ConsumerArtifactBuildReport:
    """Build summary for one facts-only consumer artifact."""

    schema_version: str
    output_dir: str
    fact_row_count: int
    artifact_sha256: str
    source_id: str | None = None
    package_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report."""
        return {key: value for key, value in asdict(self).items() if value is not None}


def build_consumer_artifact(
    output_dir: str | Path,
    *,
    facts_path: str | Path,
    replace: bool = False,
    source_id: str | None = None,
    package_id: str | None = None,
    chronicle_source_commit: str | None = None,
    source_access: str | None = None,
) -> ConsumerArtifactBuildReport:
    """Build a reproducible facts-only artifact from consumer fact rows.

    ``facts_path`` is a ``consumer_facts.jsonl`` file or a bundle directory
    containing one. The artifact contains canonical fact rows and a manifest
    that pins their schema and content hashes. Target contracts are packaged
    by the consumer, not Chronicle.
    """
    package_identity = _validate_package_identity(
        source_id=source_id,
        package_id=package_id,
        chronicle_source_commit=chronicle_source_commit,
        source_access=source_access,
    )
    output_path = Path(output_dir)
    if output_path.exists():
        if not replace:
            raise FileExistsError(
                f"Output directory exists: {output_path}. Pass replace=True."
            )
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    rows = _load_consumer_rows(_resolve_facts_path(facts_path), validate_schema=True)
    facts_out = output_path / "consumer_facts.jsonl"
    with facts_out.open("w") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True))
            file.write("\n")

    facts_sha256 = _sha256_file(facts_out)
    manifest = {
        "schema_version": CONSUMER_ARTIFACT_SCHEMA_VERSION,
        "consumer_fact_schema_versions": sorted(
            {row.get("schema_version") for row in rows}
        ),
        "consumer_fact_schema_sha256": CONSUMER_FACT_SCHEMA_SHA256,
        "fact_row_count": len(rows),
        "facts_sha256": facts_sha256,
        **package_identity,
    }
    artifact_sha256 = _artifact_manifest_sha256(manifest)
    manifest["artifact_sha256"] = artifact_sha256
    _write_json(output_path / "manifest.json", manifest)

    return ConsumerArtifactBuildReport(
        schema_version=CONSUMER_ARTIFACT_SCHEMA_VERSION,
        output_dir=str(output_path),
        fact_row_count=len(rows),
        artifact_sha256=artifact_sha256,
        source_id=source_id,
        package_id=package_id,
    )


def build_package_consumer_artifact(
    output_dir: str | Path,
    *,
    package: str | Path,
    year: int = 2023,
    chronicle_source_commit: str | None = None,
    replace: bool = False,
) -> ConsumerArtifactBuildReport:
    """Build a public package and wrap its facts as a pinned consumer artifact."""
    from chronicle.source_package import load_source_package
    from chronicle.suite import build_source_suite

    output_path = Path(output_dir)
    if output_path.exists() and not replace:
        raise FileExistsError(
            f"Output directory exists: {output_path}. Pass replace=True."
        )

    source_package = load_source_package(package)
    source_id, source_access = _source_package_publication_identity(
        source_package,
        year=year,
    )
    source_commit = _resolve_chronicle_source_commit(
        chronicle_source_commit,
        package_path=source_package.package_path,
    )

    with tempfile.TemporaryDirectory(prefix="chronicle-consumer-suite-") as tmp:
        suite_dir = Path(tmp) / "suite"
        suite_report = build_source_suite(
            source_package.package_path,
            suite_dir,
            year=year,
        )
        if not suite_report.valid:
            raise ValueError(
                "Cannot publish a consumer artifact from an invalid source-package "
                f"suite: {source_package.package_id}."
            )
        return build_consumer_artifact(
            output_path,
            facts_path=suite_dir,
            replace=replace,
            source_id=source_id,
            package_id=source_package.package_id,
            chronicle_source_commit=source_commit,
            source_access=source_access,
        )


def load_consumer_artifact(path: str | Path) -> ConsumerArtifact:
    """Load a facts-only consumer artifact and verify its manifest hashes."""
    artifact_path = Path(path)
    manifest = json.loads((artifact_path / "manifest.json").read_text())
    if manifest.get("schema_version") != CONSUMER_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported consumer artifact schema_version: "
            f"{manifest.get('schema_version')!r}."
        )
    if "profiles" in manifest:
        raise ValueError(
            "Consumer artifact manifests must not contain profiles; target profiles "
            "are consumer-owned contracts and must be loaded by Microcosm."
        )
    _validate_manifest_package_identity(manifest)
    manifest_schema_sha256 = manifest.get("consumer_fact_schema_sha256")
    if (
        manifest_schema_sha256 is not None
        and manifest_schema_sha256 != CONSUMER_FACT_SCHEMA_SHA256
    ):
        raise ValueError(
            "Consumer artifact declares consumer_fact_schema_sha256 "
            f"{manifest_schema_sha256!r}, which does not match the packaged "
            f"consumer-fact schema {CONSUMER_FACT_SCHEMA_SHA256!r}."
        )

    facts_file = artifact_path / "consumer_facts.jsonl"
    actual_sha256 = _sha256_file(facts_file)
    if actual_sha256 != manifest["facts_sha256"]:
        raise ValueError(
            "Consumer artifact fact rows do not match the manifest hash: "
            f"{actual_sha256} != {manifest['facts_sha256']}."
        )
    rows = _load_consumer_rows(facts_file, validate_schema=True)
    declared_row_count = manifest.get("fact_row_count")
    if declared_row_count is not None and declared_row_count != len(rows):
        raise ValueError(
            "Consumer artifact manifest declares fact_row_count "
            f"{declared_row_count} but the feed carries {len(rows)} rows."
        )
    artifact_sha256 = manifest.get("artifact_sha256")
    recomputed_artifact_sha256 = _artifact_manifest_sha256(manifest)
    if artifact_sha256 is not None and artifact_sha256 != recomputed_artifact_sha256:
        raise ValueError(
            "Consumer artifact manifest declares artifact_sha256 "
            f"{artifact_sha256!r}, but its canonical artifact identity hashes "
            f"to {recomputed_artifact_sha256!r}."
        )
    return ConsumerArtifact(
        path=artifact_path,
        manifest=manifest,
        rows=tuple(rows),
    )


def _validate_package_identity(
    *,
    source_id: str | None,
    package_id: str | None,
    chronicle_source_commit: str | None,
    source_access: str | None,
) -> dict[str, str]:
    identity = {
        "source_id": source_id,
        "package_id": package_id,
        "chronicle_source_commit": chronicle_source_commit,
        "source_access": source_access,
    }
    supplied = [value is not None for value in identity.values()]
    if any(supplied) and not all(supplied):
        missing = [key for key, value in identity.items() if value is None]
        raise ValueError(
            "Package consumer-artifact identity is incomplete; missing "
            + ", ".join(missing)
            + "."
        )
    if not any(supplied):
        return {}
    malformed = [key for key, value in identity.items() if not isinstance(value, str)]
    if malformed:
        raise ValueError(
            "Package consumer-artifact identity fields must be strings: "
            + ", ".join(malformed)
            + "."
        )
    assert source_id is not None
    assert package_id is not None
    assert chronicle_source_commit is not None
    assert source_access is not None
    if not source_id.strip() or not package_id.strip():
        raise ValueError(
            "Package consumer-artifact source and package IDs are required."
        )
    if not _GIT_COMMIT_RE.fullmatch(chronicle_source_commit):
        raise ValueError(
            "chronicle_source_commit must be a 40- to 64-character lowercase "
            "hexadecimal Git object ID."
        )
    if source_access not in SOURCE_ACCESS_VALUES:
        raise ValueError(f"Unsupported source access class: {source_access!r}.")
    if source_access != "public":
        raise ValueError(
            "Consumer artifacts may be built only for public source packages; "
            f"{package_id!r} is {source_access!r}."
        )
    return {key: value for key, value in identity.items() if isinstance(value, str)}


def _validate_manifest_package_identity(manifest: Mapping[str, Any]) -> None:
    identity = {key: manifest.get(key) for key in _PACKAGE_IDENTITY_FIELDS}
    supplied = [value is not None for value in identity.values()]
    if not any(supplied):
        return
    if not all(supplied):
        missing = [key for key, value in identity.items() if value is None]
        raise ValueError(
            "Consumer artifact package identity is incomplete; missing "
            + ", ".join(missing)
            + "."
        )
    _validate_package_identity(
        source_id=identity["source_id"],
        package_id=identity["package_id"],
        chronicle_source_commit=identity["chronicle_source_commit"],
        source_access=identity["source_access"],
    )


def _source_package_publication_identity(
    source_package, *, year: int
) -> tuple[str, str]:
    manifest_path = files(source_package.artifact.resource_package).joinpath(
        source_package.artifact.resource_directory,
        source_package.artifact.manifest,
    )
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}
    manifest_package_id = manifest.get("package_id")
    if manifest_package_id and manifest_package_id != source_package.package_id:
        raise ValueError(
            "Source-package and artifact manifest package IDs disagree: "
            f"{source_package.package_id!r} != {manifest_package_id!r}."
        )
    source_id = manifest.get("source_id") or source_package.artifact.source_name
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Source artifact manifest needs a non-empty string source_id.")
    artifact_year = source_package.artifact.artifact_year or year
    files_by_year = manifest.get("files") or {}
    file_spec = files_by_year.get(artifact_year) or files_by_year.get(
        str(artifact_year)
    )
    file_access = file_spec.get("access") if isinstance(file_spec, dict) else None
    # Fact-bearing packages predate #221's explicit access field and contain
    # redistributable publisher tables. Missing access therefore retains the
    # legacy public classification; explicit licensed/restricted values fail.
    source_access = file_access or manifest.get("access") or "public"
    if not isinstance(source_access, str):
        raise ValueError("Source artifact access must be a string.")
    _validate_package_identity(
        source_id=source_id,
        package_id=source_package.package_id,
        chronicle_source_commit="0" * 40,
        source_access=source_access,
    )
    return source_id, source_access


def _resolve_chronicle_source_commit(
    explicit: str | None,
    *,
    package_path: Path,
) -> str:
    if explicit is not None:
        if not _GIT_COMMIT_RE.fullmatch(explicit):
            raise ValueError(
                "chronicle_source_commit must be a 40- to 64-character lowercase "
                "hexadecimal Git object ID."
            )
        return explicit
    result = subprocess.run(
        ["git", "-C", str(package_path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip().lower()
    if result.returncode != 0 or not _GIT_COMMIT_RE.fullmatch(commit):
        raise ValueError(
            "Could not determine the Chronicle source commit. Pass "
            "chronicle_source_commit explicitly."
        )
    return commit


def _resolve_facts_path(facts_path: str | Path) -> Path:
    path = Path(facts_path)
    if path.is_dir():
        candidate = path / "consumer_facts.jsonl"
        if not candidate.exists():
            raise FileNotFoundError(
                f"No consumer_facts.jsonl in bundle directory {path}."
            )
        return candidate
    if not path.exists():
        raise FileNotFoundError(f"No consumer facts file at {path}.")
    return path


def _reject_non_finite(value: Any) -> Any:
    raise ValueError(f"Consumer fact contains a non-finite JSON number: {value!r}.")


def _assert_finite_numbers(value: Any, *, line_number: int, path: Path) -> None:
    """Reject non-finite numbers, including those in nested structures."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(
            f"Row {line_number} of {path} contains a non-finite number: {value!r}."
        )
    if isinstance(value, dict):
        for item in value.values():
            _assert_finite_numbers(item, line_number=line_number, path=path)
    elif isinstance(value, list):
        for item in value:
            _assert_finite_numbers(item, line_number=line_number, path=path)


def _recompute_aggregate_fact_key(row: dict[str, Any]) -> str:
    """Recompute the aggregate fact key from the row's content."""
    assertion = row.get("assertion")
    payload = {
        "source_release_key": row.get("source_release_key"),
        "source_series_key": row.get("source_series_key"),
        "observed_measure_key": row.get("observed_measure_key"),
        "aggregation": row.get("aggregation"),
        "period": row.get("period"),
        "geography": row.get("geography"),
        "entity": row.get("entity"),
        "dimension_set_key": row.get("dimension_set_key"),
        "universe_constraint_set_key": row.get("universe_constraint_set_key"),
        "assertion": None if assertion == DEFAULT_ASSERTION else assertion,
    }
    return _hash_key("ledger.aggregate_fact.v2", payload)


def _load_consumer_rows(
    path: Path,
    *,
    validate_schema: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    with path.open() as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            row = json.loads(line, parse_constant=_reject_non_finite)
            _assert_finite_numbers(row, line_number=line_number, path=path)
            if validate_schema:
                validate_consumer_fact_row(row, line_number, path)
            _validate_consumer_row_provenance(row, line_number=line_number, path=path)
            assertion = row.setdefault("assertion", DEFAULT_ASSERTION)
            if assertion not in ALLOWED_ASSERTIONS:
                raise ValueError(
                    f"Row {line_number} of {path} has unsupported assertion "
                    f"{assertion!r}."
                )
            key = row.get("aggregate_fact_key")
            if validate_schema:
                recomputed = _recompute_aggregate_fact_key(row)
                if key != recomputed:
                    raise ValueError(
                        f"Row {line_number} of {path} declares aggregate_fact_key "
                        f"{key!r} but its content hashes to {recomputed!r}; the "
                        "identity key does not match the row."
                    )
            if key in seen_keys:
                raise ValueError(
                    f"Row {line_number} of {path} repeats aggregate_fact_key "
                    f"{key!r}; consumer artifact fact rows must be unique."
                )
            seen_keys.add(key)
            rows.append(row)
    return rows


def _validate_consumer_row_provenance(
    row: Mapping[str, Any],
    *,
    line_number: int,
    path: Path,
) -> None:
    if "provenance_class" not in row:
        raise ValueError(
            f"Row {line_number} of {path} is missing required provenance_class."
        )
    provenance_class = row["provenance_class"]
    if type(provenance_class) is not str or (
        provenance_class not in ALLOWED_PROVENANCE_CLASSES
    ):
        raise ValueError(
            f"Row {line_number} of {path} has unsupported provenance_class "
            f"{provenance_class!r}."
        )
    has_survey_instrument = "survey_instrument" in row
    survey_instrument = row.get("survey_instrument")
    if provenance_class == "survey_aggregate":
        if type(survey_instrument) is not str or not survey_instrument.strip():
            raise ValueError(
                f"Row {line_number} of {path} needs a non-empty "
                "survey_instrument for survey_aggregate provenance."
            )
    elif has_survey_instrument:
        raise ValueError(
            f"Row {line_number} of {path} has survey_instrument outside "
            "survey_aggregate provenance."
        )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")


def _artifact_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    identity = {
        key: value for key, value in manifest.items() if key != "artifact_sha256"
    }
    canonical = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "CONSUMER_ARTIFACT_SCHEMA_VERSION",
    "ConsumerArtifact",
    "ConsumerArtifactBuildReport",
    "build_consumer_artifact",
    "build_package_consumer_artifact",
    "load_consumer_artifact",
]
