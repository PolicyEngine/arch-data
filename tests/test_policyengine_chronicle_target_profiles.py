from __future__ import annotations

import json
from pathlib import Path

import pytest

import policyengine_chronicle.target_profiles as target_profiles_pkg
from chronicle.bundle import build_bundle
from policyengine_chronicle.consumer import _select_rows, build_consumer_artifact
from policyengine_chronicle.target_profiles import (
    TARGET_PROFILE_SCHEMA_VERSION,
    load_target_profile,
    target_profile_from_mapping,
)

_PROFILE_DIR = Path(target_profiles_pkg.__file__).parent


def _packaged_profile_ids() -> list[str]:
    return sorted(path.stem for path in _PROFILE_DIR.glob("*.json"))


def test__given_uk_local_profile__then_it_declares_measurement_contracts() -> None:
    # When
    profile = load_target_profile("uk_local_geography")

    # Then
    assert profile.country == "uk"
    assert profile.default_operation == "sum"
    assert profile.base_period_policy == "latest_not_after_build_base_period"

    constituency_metrics = [
        target.binding("policyengine").metric_name
        for target in profile.targets_for_geography("constituency")
    ]
    assert constituency_metrics[:4] == [
        "hmrc/self_employment_income/amount",
        "hmrc/self_employment_income/count",
        "hmrc/employment_income/amount",
        "hmrc/employment_income/count",
    ]
    assert "uc_hh_3plus_children" in constituency_metrics
    assert "rent/private_rent" not in constituency_metrics

    local_authority_metrics = [
        target.binding("policyengine").metric_name
        for target in profile.targets_for_geography("local_authority")
    ]
    assert "uc_households" in local_authority_metrics
    assert "ons/equiv_net_income_bhc" in local_authority_metrics
    assert "rent/private_rent" in local_authority_metrics
    assert "uc_hh_0_children" not in local_authority_metrics


def test__given_count_like_profile_rows__then_they_are_still_sum_measurements() -> None:
    # When
    profile = load_target_profile("uk_local_geography")
    employment_count = next(
        target
        for target in profile.targets
        if target.target_id == "hmrc.employment_income.count"
    )

    # Then
    assert profile.default_operation == "sum"
    assert employment_count.measurement["concept"] == "uk.person.count"
    assert employment_count.binding("policyengine").payload["value_variable"] == (
        "person_count"
    )


def test__given_uk_firms_profile__then_it_declares_chronicle_only_firm_targets() -> None:
    # When
    profile = load_target_profile("uk_firms")

    # Then
    assert profile.country == "uk"
    assert profile.default_operation == "sum"
    assert profile.base_period_policy == "latest_not_after_build_base_period"
    assert [
        target.target_id for target in profile.targets_for_geography("country")
    ] == [
        "ons.uk_business.enterprise_count.turnover_bands",
        "ons.uk_business.enterprise_count.employment_bands",
        "hmrc.vat.registered_trader_count.turnover_bands",
        "hmrc.vat.net_liability.turnover_bands",
        "ons.uk_business.enterprise_count.sic_turnover_bands",
        "ons.uk_business.enterprise_count.sic_employment_bands",
        "hmrc.vat.registered_trader_count.sic_sectors",
        "hmrc.vat.net_liability.sic_sectors",
    ]

    targets_by_id = {target.target_id: target for target in profile.targets}
    turnover_count = targets_by_id["ons.uk_business.enterprise_count.turnover_bands"]
    assert turnover_count.measurement["entity"] == "firm"
    assert turnover_count.chronicle_selector == {
        "source_name": "ons",
        "source_measure_id": "enterprise_count",
        "record_set_id": "ons.uk_business.cy2025.enterprise_count.by_turnover_band",
        "groupby_dimension": "uk.firm.annual_turnover",
    }
    assert turnover_count.binding("microcosm").metric_name == (
        "ons/uk_business/enterprise_count/turnover_bands"
    )

    registered_count = targets_by_id["hmrc.vat.registered_trader_count.turnover_bands"]
    assert registered_count.binding("axiom").payload["filter_rule"] == (
        "uk:policies/govuk/vat#firm_vat_registered"
    )

    sic_turnover = targets_by_id["ons.uk_business.enterprise_count.sic_turnover_bands"]
    assert sic_turnover.chronicle_selector == {
        "source_name": "ons",
        "source_measure_id": "enterprise_count",
        "record_set_id": (
            "ons.uk_business.cy2025.enterprise_count.by_sic_turnover_band"
        ),
        "dimensions": ["uk.firm.sic_code", "uk.firm.turnover_band"],
    }
    assert sic_turnover.binding("microcosm").payload["groupby_variables"] == [
        "sic_code",
        "annual_turnover",
    ]

    sic_population = targets_by_id["hmrc.vat.registered_trader_count.sic_sectors"]
    assert sic_population.chronicle_selector["record_set_id"] == (
        "hmrc.vat.fy2024_25.registered_trader_count.by_sic"
    )
    assert sic_population.binding("axiom").payload["filter_rule"] == (
        "uk:policies/govuk/vat#firm_vat_registered"
    )

    vat_liability = targets_by_id["hmrc.vat.net_liability.turnover_bands"]
    assert vat_liability.measurement["concept"] == "uk.tax.vat.net_liability"
    assert vat_liability.binding("axiom").payload["value_rule"] == (
        "uk:policies/govuk/vat#net_vat_liability"
    )
    assert vat_liability.binding("axiom").payload["filter_rule"] == (
        "uk:policies/govuk/vat#firm_vat_registered"
    )

    sic_vat_liability = targets_by_id["hmrc.vat.net_liability.sic_sectors"]
    assert sic_vat_liability.measurement["groupby_dimension"] == "uk.firm.sic_code"
    assert sic_vat_liability.binding("axiom").payload["value_rule"] == (
        "uk:policies/govuk/vat#net_vat_liability"
    )


@pytest.mark.parametrize("forbidden", ["registry", "aggregation", "target_value"])
def test__given_forbidden_profile_option__then_profile_is_rejected(
    forbidden: str,
) -> None:
    # Given
    payload = {
        "schema_version": TARGET_PROFILE_SCHEMA_VERSION,
        "profile_id": "bad",
        "country": "uk",
        "label": "Bad profile",
        "defaults": {
            "base_period_policy": "latest_not_after_build_base_period",
            "operation": "sum",
        },
        "targets": [
            {
                "target_id": "bad.target",
                "family": "bad",
                "geography_levels": ["country"],
                "chronicle_selector": {"source_name": "bad"},
                "measurement": {"entity": "household", "concept": "bad"},
                "bindings": {
                    "policyengine": {
                        "metric_name": "bad",
                        forbidden: "not allowed",
                    }
                },
            }
        ],
    }

    # When / Then
    with pytest.raises(ValueError, match=forbidden):
        target_profile_from_mapping(payload)


@pytest.mark.parametrize(
    "forbidden",
    ["runtime_code", "python_code", "solver", "execute", "module", "command"],
)
def test__given_runtime_binding_option__then_profile_is_rejected(
    forbidden: str,
) -> None:
    # Given
    payload = _minimal_profile_payload()
    payload["targets"][0]["bindings"]["policyengine"][forbidden] = "not allowed"

    # When / Then
    with pytest.raises(ValueError, match=forbidden):
        target_profile_from_mapping(payload)


@pytest.mark.parametrize(
    ("container", "forbidden"),
    [
        ("chronicle_selector", "value"),
        ("chronicle_selector", "target_value"),
        ("measurement", "value"),
        ("measurement", "aggregation"),
        ("measurement", "registry"),
    ],
)
def test__given_nested_forbidden_profile_option__then_profile_is_rejected(
    container: str,
    forbidden: str,
) -> None:
    # Given
    payload = _minimal_profile_payload()
    payload["targets"][0][container][forbidden] = "not allowed"

    # When / Then
    with pytest.raises(ValueError, match=forbidden):
        target_profile_from_mapping(payload)


def test__given_filter_threshold_values__then_profile_is_allowed() -> None:
    # Given
    payload = _minimal_profile_payload()
    payload["targets"][0]["measurement"]["filters"] = [
        {"concept": "uk.tax.income_tax", "operator": ">", "value": 0}
    ]

    # When
    profile = target_profile_from_mapping(payload)

    # Then
    assert profile.targets[0].measurement["filters"][0]["value"] == 0


def test__given_non_sum_default_operation__then_profile_is_rejected() -> None:
    # Given
    payload = {
        "schema_version": TARGET_PROFILE_SCHEMA_VERSION,
        "profile_id": "bad",
        "country": "uk",
        "label": "Bad profile",
        "defaults": {
            "base_period_policy": "latest_not_after_build_base_period",
            "operation": "count",
        },
        "targets": [],
    }

    # When / Then
    with pytest.raises(ValueError, match="operation 'sum'"):
        target_profile_from_mapping(payload)


def test_every_packaged_profile_selector_uses_supported_keys() -> None:
    # Given the packaged target profiles
    profile_ids = _packaged_profile_ids()
    assert profile_ids

    # Then every chronicle_selector resolves against the supported vocabulary
    for profile_id in profile_ids:
        profile = load_target_profile(profile_id)
        for target in profile.targets:
            for level in target.geography_levels:
                _, issues = _select_rows(
                    profile.profile_id,
                    target,
                    [],
                    geography_level=level,
                )
                unknown = [
                    issue for issue in issues if issue.code == "unknown_selector_key"
                ]
                assert not unknown, (
                    f"{profile_id}/{target.target_id} ships an unsupported "
                    f"selector: {[issue.message for issue in unknown]}"
                )


def _minimal_profile_payload() -> dict[str, object]:
    return {
        "schema_version": TARGET_PROFILE_SCHEMA_VERSION,
        "profile_id": "test_profile",
        "country": "uk",
        "label": "Test profile",
        "defaults": {
            "base_period_policy": "latest_not_after_build_base_period",
            "operation": "sum",
        },
        "targets": [
            {
                "target_id": "test.target",
                "family": "test",
                "geography_levels": ["country"],
                "chronicle_selector": {"source_name": "test"},
                "measurement": {"entity": "household", "concept": "test"},
                "bindings": {
                    "policyengine": {
                        "metric_name": "test",
                    }
                },
            }
        ],
    }


# --- uk_national ------------------------------------------------------------

UK_NATIONAL_COUNTERFACTUAL_KINDS = {
    "input_substitution_counterfactual",
    "parameter_gated_threshold",
    "baseline_flag_crosstab",
}
# Families whose facts are (or include) source projections the calibration
# intends to use: OBR EFO forecast lines, SLC borrower forecasts, and the
# Scottish budget forward years (#154 semantics; checklist row for the
# uk_national profile).
UK_NATIONAL_PROJECTION_FAMILIES = {
    "obr",
    "slc_borrowers",
    "scotgov_social_security",
}
# Every source package the uk_national selectors draw facts from. The
# resolution test builds exactly this subset so a selector pointing at an
# unbuilt package fails loudly rather than resolving zero rows silently.
UK_NATIONAL_SOURCE_PACKAGES = (
    "dwp-benefit-cap-november-2025",
    "dwp-benefit-statistics-february-2026",
    "dwp-pip-daily-living-foi-2025",
    "dwp-uc-households-children-may-2025",
    "dwp-uc-households-family-type-may-2025",
    "dwp-uc-payment-distribution-may-2025",
    "dwp-uc-scotland-youngest-child-may-2025",
    "dwp-uc-two-child-limit-2025",
    "hmrc-cgt-statistics-2025",
    "hmrc-salary-sacrifice-reform-2029-headcounts",
    "hmrc-salary-sacrifice-relief-2024-25",
    "hmrc-spi-income-bands-2023-24",
    "isc-annual-census-2023",
    "isc-annual-census-2024",
    "obr-efo-expenditure-march-2026",
    "obr-efo-receipts-march-2026",
    "ons-families-households-2025",
    "ons-mye-2023-england-regions",
    "ons-mye-2023-uk-countries",
    "ons-mye-2024-uk",
    "ons-national-balance-sheet-land-2025",
    "ons-public-sector-employment-2026",
    "ons-savings-interest-income",
    "scotgov-council-tax-bands-2025",
    "scotgov-scottish-budget-social-security-assistance-2026",
    "slc-student-loan-borrower-forecasts-england-2025",
    "slc-student-loan-repayments-england-2025",
    "slc-student-loan-repayments-northern-ireland-2025",
    "slc-student-loan-repayments-scotland-2025",
    "slc-student-loan-repayments-wales-2025",
    "slc-student-support-england-2025",
    "voa-council-tax-bands-2025",
)
# Signed exceptions to the every-target-resolves rule. Empty by design: any
# entry needs the same review a package exclusion gets.
UK_NATIONAL_COVERAGE_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset()


def test__given_uk_national_profile__then_structure_matches_migration_contract() -> (
    None
):
    # When
    profile = load_target_profile("uk_national")

    # Then
    assert profile.country == "uk"
    assert profile.default_operation == "sum"
    assert profile.base_period_policy == "latest_not_after_build_base_period"
    assert profile.default_assertion_policy == "observed_only"
    assert len(profile.targets) == 186

    assert {target.family for target in profile.targets} == {
        "obr",
        "isc",
        "hmrc_salary_sacrifice",
        "hmrc_spi",
        "hmrc_cgt",
        "dwp_benefit_cap",
        "dwp_pip",
        "dwp_legacy_benefits",
        "dwp_universal_credit",
        "dwp_two_child_limit",
        "ons_population",
        "ons_household_composition",
        "council_tax_stock",
        "scotgov_social_security",
        "ons_national_accounts",
        "ons_employment",
        "ons_land",
        "slc_repayments",
        "slc_borrowers",
        "slc_student_support",
    }

    for target in profile.targets:
        # Projection-backed families carry the explicit policy; everything
        # else rides the observed_only default so NPP and other ported
        # projections stay dormant until populace activates them.
        if target.family in UK_NATIONAL_PROJECTION_FAMILIES:
            assert target.assertion_policy == "allow_source_projection", (
                target.target_id
            )
        else:
            assert target.assertion_policy is None, target.target_id
        assert "assertion" not in target.chronicle_selector
        assert set(target.bindings) == {"policyengine", "axiom"}
        kind = target.binding("policyengine").payload.get("kind")
        assert kind is None or kind in UK_NATIONAL_COUNTERFACTUAL_KINDS, (
            target.target_id
        )


def test__given_uk_national_counterfactual_targets__then_payloads_declare_not_execute() -> (  # noqa: E501
    None
):
    # When
    profile = load_target_profile("uk_national")
    payloads = {
        target.target_id: target.binding("policyengine").payload
        for target in profile.targets
    }

    # Then: salary sacrifice is an input-substitution counterfactual...
    it_relief = payloads["hmrc.salary_sacrifice.it_relief_basic_rate"]
    assert it_relief["kind"] == "input_substitution_counterfactual"
    assert it_relief["zeroed_input"] == (
        "pension_contributions_via_salary_sacrifice"
    )
    assert it_relief["folded_into"] == "employment_income"
    assert it_relief["output_variable"] == "income_tax"

    # ...CGT is gated on the live annual exempt amount parameter...
    cgt = payloads["hmrc.cgt.gains_total"]
    assert cgt["kind"] == "parameter_gated_threshold"
    assert cgt["gate_parameter"] == "gov.hmrc.cgt.annual_exempt_amount"
    assert cgt["gated_variable"] == "capital_gains"

    # ...and the two-child limit reads the baseline flag, no second sim.
    tcl = payloads["dwp.uc.two_child_limit.households_affected"]
    assert tcl["kind"] == "baseline_flag_crosstab"
    assert tcl["affected_flag_variable"] == "uc_is_child_limit_affected"


def test__given_uk_national_profile__then_every_target_resolves_built_facts(
    tmp_path,
) -> None:
    # Given a bundle of exactly the packages the profile selects from
    profile = load_target_profile("uk_national")
    selector_sources = {
        target.chronicle_selector["source_name"] for target in profile.targets
    }
    package_sources = {
        alias.split("-", 1)[0] for alias in UK_NATIONAL_SOURCE_PACKAGES
    }
    assert selector_sources == package_sources

    bundle_dir = tmp_path / "bundle"
    report = build_bundle(
        bundle_dir, year=2023, sources=UK_NATIONAL_SOURCE_PACKAGES
    )
    assert report.valid

    # When
    artifact_dir = tmp_path / "artifact"
    build_consumer_artifact(
        artifact_dir, facts_path=bundle_dir, profile_ids=["uk_national"]
    )
    coverage = json.loads((artifact_dir / "coverage.json").read_text())[
        "uk_national"
    ]

    # Then every target resolves at least one built fact at every declared
    # geography level, with no selector issues.
    assert set(coverage) == {target.target_id for target in profile.targets}
    failures = []
    for target_id, levels in coverage.items():
        for level, info in levels.items():
            if (target_id, level) in UK_NATIONAL_COVERAGE_EXCEPTIONS:
                continue
            if info.get("issues") or info.get("matched_row_count", 0) < 1:
                failures.append((target_id, level, info))
    assert not failures, failures

    # The projection-only borrower forecasts are the reason those targets
    # carry allow_source_projection - prove the facts really are projections.
    borrower = coverage["slc.borrowers.plan_2_above_threshold"]["country"]
    assert borrower["assertions"] == ["source_projection"]
