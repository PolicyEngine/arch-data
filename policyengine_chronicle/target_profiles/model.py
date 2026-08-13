"""Chronicle-owned target profiles for government statistics source records.

Target profiles describe which source-backed Chronicle facts a downstream build
may select and the semantic quantity those facts represent. They do not contain
target values, runtime hooks, or solver instructions. Values come from Chronicle
fact rows selected by the profile's selectors.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from chronicle.core import ASSERTION_POLICIES, DEFAULT_ASSERTION_POLICY

TARGET_PROFILE_SCHEMA_VERSION = "policyengine_ledger.target_profile.v1"
FORBIDDEN_VALUE_KEYS = {"aggregation", "operation", "registry", "target_value", "value"}
FORBIDDEN_RUNTIME_KEYS = {
    "callable",
    "command",
    "execute",
    "executable",
    "function",
    "import",
    "imports",
    "module",
    "python_code",
    "runtime_code",
    "script",
    "solver",
}
BINDING_KINDS = {
    "input_substitution_counterfactual",
    "parameter_gated_threshold",
    "baseline_flag_crosstab",
}
BINDING_KIND_REQUIRED_FIELDS = {
    "input_substitution_counterfactual": {
        "zeroed_input",
        "folded_into",
        "output_variable",
        "output_delta",
    },
    "parameter_gated_threshold": {
        "gate_parameter",
        "gated_variable",
        "gate_comparison",
    },
    "baseline_flag_crosstab": {
        "affected_flag_variable",
        "count_of",
    },
}
BINDING_REDUCE_VALUES = {"any"}
CONDITION_ENTITIES = {"person", "benunit", "household"}
CONDITION_REDUCE_VALUES = {
    "any",
    "any_child_under",
    "count",
    "sum",
}


@dataclass(frozen=True)
class TargetProfileBinding:
    """Backend-specific semantic reference for one source quantity."""

    backend: str
    metric_name: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class TargetProfileTarget:
    """One profile target family and its source quantity contract."""

    target_id: str
    family: str
    geography_levels: tuple[str, ...]
    chronicle_selector: Mapping[str, Any]
    measurement: Mapping[str, Any]
    bindings: Mapping[str, TargetProfileBinding]
    tolerance: float | None = None
    assertion_policy: str | None = None

    def binding(self, backend: str) -> TargetProfileBinding:
        """Return the binding for ``backend`` or raise a useful error."""
        try:
            return self.bindings[backend]
        except KeyError:
            raise KeyError(
                f"Target profile row {self.target_id!r} has no {backend!r} binding."
            ) from None


@dataclass(frozen=True)
class TargetProfile:
    """A Chronicle-owned source profile referenced by downstream builders."""

    profile_id: str
    country: str
    label: str
    base_period_policy: str
    default_operation: str
    default_assertion_policy: str
    targets: tuple[TargetProfileTarget, ...]

    def targets_for_geography(
        self,
        geography_level: str,
    ) -> tuple[TargetProfileTarget, ...]:
        """Return profile rows active for a geography level."""
        return tuple(
            target
            for target in self.targets
            if geography_level in target.geography_levels
        )


def load_target_profile(profile_id: str) -> TargetProfile:
    """Load a packaged Chronicle target profile by ID."""
    if not profile_id or "/" in profile_id or "\\" in profile_id:
        raise ValueError(f"Invalid target profile id {profile_id!r}.")
    path = files(__package__).joinpath(f"{profile_id}.json")
    try:
        payload = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"No packaged target profile {profile_id!r}.") from exc
    return target_profile_from_mapping(payload)


def target_profile_from_mapping(raw: Mapping[str, Any]) -> TargetProfile:
    """Validate and parse a JSON-like target profile mapping."""
    schema_version = raw.get("schema_version")
    if schema_version != TARGET_PROFILE_SCHEMA_VERSION:
        raise ValueError(
            "target profile schema_version must be "
            f"{TARGET_PROFILE_SCHEMA_VERSION!r}, got {schema_version!r}."
        )
    _reject_forbidden_value_keys(raw, context="target profile")
    profile_id = _required_string(raw, "profile_id")
    country = _required_string(raw, "country")
    label = _required_string(raw, "label")
    defaults = _required_mapping(raw, "defaults")
    base_period_policy = _required_string(defaults, "base_period_policy")
    default_operation = _required_string(defaults, "operation")
    if default_operation != "sum":
        raise ValueError(
            f"target profile {profile_id!r} must use operation 'sum', "
            f"got {default_operation!r}."
        )
    default_assertion_policy = defaults.get(
        "assertion_policy", DEFAULT_ASSERTION_POLICY
    )
    if default_assertion_policy not in ASSERTION_POLICIES:
        raise ValueError(
            f"target profile {profile_id!r} defaults.assertion_policy must be "
            f"one of {sorted(ASSERTION_POLICIES)}, got "
            f"{default_assertion_policy!r}."
        )
    targets = tuple(
        _target_from_mapping(target)
        for target in _required_mapping_sequence(raw, "targets")
    )
    if not targets:
        raise ValueError(f"target profile {profile_id!r} must declare targets.")
    duplicate_ids = sorted(
        target_id
        for target_id in {target.target_id for target in targets}
        if sum(target.target_id == target_id for target in targets) > 1
    )
    if duplicate_ids:
        raise ValueError(
            f"target profile {profile_id!r} has duplicate target_id(s): "
            f"{duplicate_ids}."
        )
    return TargetProfile(
        profile_id=profile_id,
        country=country,
        label=label,
        base_period_policy=base_period_policy,
        default_operation=default_operation,
        default_assertion_policy=default_assertion_policy,
        targets=targets,
    )


def _target_from_mapping(raw: Mapping[str, Any]) -> TargetProfileTarget:
    _reject_forbidden_value_keys(raw, context="target profile row")
    target_id = _required_string(raw, "target_id")
    family = _required_string(raw, "family")
    geography_levels = tuple(_required_string_sequence(raw, "geography_levels"))
    if not geography_levels:
        raise ValueError(f"target profile row {target_id!r} needs geography_levels.")
    chronicle_selector = _required_mapping(raw, "chronicle_selector")
    measurement = _required_mapping(raw, "measurement")
    _reject_forbidden_contract_keys(
        chronicle_selector,
        context=f"target profile row {target_id!r} chronicle_selector",
    )
    _validate_chronicle_selector(
        chronicle_selector,
        context=f"target profile row {target_id!r} chronicle_selector",
    )
    _reject_forbidden_contract_keys(
        measurement,
        context=f"target profile row {target_id!r} measurement",
    )
    bindings_payload = _required_mapping(raw, "bindings")
    bindings = {
        backend: _binding_from_mapping(
            backend,
            payload,
            target_id=target_id,
        )
        for backend, payload in bindings_payload.items()
    }
    if not bindings:
        raise ValueError(f"target profile row {target_id!r} needs bindings.")
    tolerance = raw.get("tolerance")
    if tolerance is not None:
        if not isinstance(tolerance, int | float) or isinstance(tolerance, bool):
            raise ValueError(f"target profile row {target_id!r}: invalid tolerance.")
        tolerance = float(tolerance)
    assertion_policy = raw.get("assertion_policy")
    if assertion_policy is not None and assertion_policy not in ASSERTION_POLICIES:
        raise ValueError(
            f"target profile row {target_id!r} assertion_policy must be one of "
            f"{sorted(ASSERTION_POLICIES)}, got {assertion_policy!r}."
        )
    if assertion_policy is not None and "assertion" in chronicle_selector:
        raise ValueError(
            f"target profile row {target_id!r} declares both assertion_policy "
            f"{assertion_policy!r} and a chronicle_selector on 'assertion'; "
            "the selector already pins the axis — declare one or the other."
        )
    return TargetProfileTarget(
        target_id=target_id,
        family=family,
        geography_levels=geography_levels,
        chronicle_selector=chronicle_selector,
        measurement=measurement,
        bindings=bindings,
        tolerance=tolerance,
        assertion_policy=assertion_policy,
    )


def _binding_from_mapping(
    backend: str,
    raw: Any,
    *,
    target_id: str,
) -> TargetProfileBinding:
    if not isinstance(backend, str) or not backend:
        raise ValueError(f"target profile row {target_id!r}: bad binding backend.")
    if not isinstance(raw, Mapping):
        raise ValueError(
            f"target profile row {target_id!r}: binding {backend!r} must be an object."
        )
    _reject_forbidden_value_keys(raw, context=f"{backend} binding")
    _reject_forbidden_contract_keys(
        raw,
        context=f"target profile row {target_id!r} {backend} binding",
    )
    metric_name = _required_string(raw, "metric_name")
    _validate_binding_payload(
        raw,
        context=f"target profile row {target_id!r} {backend} binding",
    )
    return TargetProfileBinding(
        backend=backend,
        metric_name=metric_name,
        payload=dict(raw),
    )


def _validate_chronicle_selector(
    selector: Mapping[str, Any],
    *,
    context: str,
) -> None:
    if "dimension_values" not in selector:
        return
    dimension_values = selector["dimension_values"]
    if not isinstance(dimension_values, Mapping):
        raise ValueError(f"{context}.dimension_values must be an object.")
    for name, value in dimension_values.items():
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"{context}.dimension_values keys must be non-empty strings."
            )
        if isinstance(value, list | tuple):
            if not value:
                raise ValueError(
                    f"{context}.dimension_values[{name!r}] must not be empty."
                )
            for index, item in enumerate(value):
                if not _is_scalar(item):
                    raise ValueError(
                        f"{context}.dimension_values[{name!r}][{index}] "
                        "must be a scalar."
                    )
        elif not _is_scalar(value):
            raise ValueError(
                f"{context}.dimension_values[{name!r}] must be a scalar "
                "or a non-empty list of scalars."
            )


def _validate_binding_payload(raw: Mapping[str, Any], *, context: str) -> None:
    kind = raw.get("kind")
    if kind is not None:
        if kind not in BINDING_KINDS:
            raise ValueError(
                f"{context}.kind must be one of {sorted(BINDING_KINDS)}, "
                f"got {kind!r}."
            )
        missing = sorted(
            field
            for field in BINDING_KIND_REQUIRED_FIELDS[kind]
            if not isinstance(raw.get(field), str) or not raw.get(field)
        )
        if missing:
            raise ValueError(
                f"{context} kind {kind!r} is missing required field(s) "
                f"{missing}."
            )
    reduce = raw.get("reduce")
    if reduce is not None and reduce not in BINDING_REDUCE_VALUES:
        raise ValueError(
            f"{context}.reduce must be one of {sorted(BINDING_REDUCE_VALUES)}, "
            f"got {reduce!r}."
        )
    for key in ("filters", "household_conditions"):
        if key in raw:
            _validate_predicate_sequence(raw[key], context=f"{context}.{key}")


def _validate_predicate_sequence(value: Any, *, context: str) -> None:
    if not isinstance(value, list | tuple):
        raise ValueError(f"{context} must be a list of predicate objects.")
    for index, item in enumerate(value):
        if not _is_predicate_shape(item):
            raise ValueError(f"{context}[{index}] must be predicate-shaped.")
        entity = item.get("entity")
        if entity is not None and entity not in CONDITION_ENTITIES:
            raise ValueError(
                f"{context}[{index}].entity must be one of "
                f"{sorted(CONDITION_ENTITIES)}, got {entity!r}."
            )
        reduce = item.get("reduce")
        if reduce is not None and reduce not in CONDITION_REDUCE_VALUES:
            raise ValueError(
                f"{context}[{index}].reduce must be one of "
                f"{sorted(CONDITION_REDUCE_VALUES)}, got {reduce!r}."
            )


def _is_predicate_shape(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if not ("variable" in value or "concept" in value):
        return False
    if "operator" in value:
        return "value" in value
    if "equals" in value:
        return True
    if "in" in value:
        return isinstance(value["in"], list | tuple) and bool(value["in"])
    if "lower" in value or "upper" in value:
        return True
    return False


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _reject_forbidden_value_keys(raw: Mapping[str, Any], *, context: str) -> None:
    forbidden = FORBIDDEN_VALUE_KEYS | FORBIDDEN_RUNTIME_KEYS
    present = sorted(key for key in forbidden if key in raw)
    if present:
        raise ValueError(
            f"{context} must not declare {present}; Chronicle profiles use "
            "implicit Chronicle source selection, sum-only measurement, no "
            "runtime execution hooks, and values coming from Chronicle facts."
        )


def _reject_forbidden_contract_keys(value: Any, *, context: str) -> None:
    """Reject target-value or registry controls nested in contract payloads.

    Filter thresholds such as ``{"operator": ">", "value": 0}`` are valid
    measurement predicates, so this recursive guard allows ``value`` only in
    recognized filter predicate objects. Other ``value`` keys are rejected so
    target amounts cannot hide inside selectors or measurement contracts.
    """

    if isinstance(value, Mapping):
        forbidden = FORBIDDEN_VALUE_KEYS - {"value"}
        if not _is_filter_predicate(value):
            forbidden = forbidden | {"value"}
        forbidden = forbidden | FORBIDDEN_RUNTIME_KEYS
        present = sorted(key for key in forbidden if key in value)
        if present:
            raise ValueError(
                f"{context} must not declare {present}; Chronicle target profiles "
                "use implicit source selection, sum-only measurement, no "
                "runtime execution hooks, and values coming from Chronicle facts."
            )
        for key, item in value.items():
            _reject_forbidden_contract_keys(item, context=f"{context}.{key}")
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _reject_forbidden_contract_keys(item, context=f"{context}[{index}]")


def _is_filter_predicate(value: Mapping[str, Any]) -> bool:
    return (
        "value" in value
        and "operator" in value
        and ("concept" in value or "variable" in value)
    )


def _required_string(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"target profile field {key!r} must be a non-empty string.")
    return value


def _required_mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"target profile field {key!r} must be an object.")
    return value


def _required_mapping_sequence(
    raw: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    value = raw.get(key)
    if not isinstance(value, list | tuple):
        raise ValueError(f"target profile field {key!r} must be a list.")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ValueError(
                f"target profile field {key!r} row {index} must be an object."
            )
        rows.append(row)
    return tuple(rows)


def _required_string_sequence(raw: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key)
    if not isinstance(value, list | tuple):
        raise ValueError(f"target profile field {key!r} must be a list.")
    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ValueError(
                f"target profile field {key!r} item {index} must be a non-empty string."
            )
        strings.append(item)
    return tuple(strings)


__all__ = [
    "BINDING_KINDS",
    "TARGET_PROFILE_SCHEMA_VERSION",
    "TargetProfile",
    "TargetProfileBinding",
    "TargetProfileTarget",
    "load_target_profile",
    "target_profile_from_mapping",
]
