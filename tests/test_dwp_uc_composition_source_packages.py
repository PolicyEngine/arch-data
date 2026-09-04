"""Regression tests for the Stat-Xplore UC composition histories (chronicle#233, #234).

The three chronicle#233 crosses (family type x child entitlement, number of
children x child entitlement, family type x payment indicator) and the two
chronicle#234 histories (monthly award band x family type, Scotland age of
youngest child) share one shape: nine monthly record sets, April to December
2025, benefit-unit entity, publisher labels as categorical identity.
"""

from __future__ import annotations

import pytest

from chronicle.consumer_contract import (
    consumer_fact_rows,
    validate_consumer_fact_contract,
)
from chronicle.core import validate_facts
from chronicle.source_package import load_source_package, validate_source_package

MONTHS = [f"2025-{month:02d}" for month in range(4, 13)]


def _fact(facts, *, period, **filters):
    matches = [
        fact
        for fact in facts
        if fact.period.value == period
        and all(fact.filters.get(key) == value for key, value in filters.items())
    ]
    assert len(matches) == 1, (period, filters, len(matches))
    return matches[0]


@pytest.mark.parametrize(
    ("alias", "rows_per_month", "geography_id", "groupby_dimension"),
    [
        (
            "dwp-uc-households-family-type-child-entitlement-april-december-2025",
            10,
            "K03000001",
            "dwp.uc_family_type",
        ),
        (
            "dwp-uc-households-children-child-entitlement-april-december-2025",
            16,
            "K03000001",
            "dwp.uc_number_of_children",
        ),
        (
            "dwp-uc-households-family-type-payment-indicator-april-december-2025",
            10,
            "K03000001",
            "dwp.uc_family_type",
        ),
        (
            "dwp-uc-payment-distribution-april-december-2025",
            135,
            "K03000001",
            "dwp.uc_monthly_award_band",
        ),
        (
            "dwp-uc-scotland-youngest-child-april-december-2025",
            23,
            "S92000003",
            "dwp.uc_youngest_child_age",
        ),
    ],
)
def test_uc_monthly_packages_cover_april_to_december_2025(
    alias,
    rows_per_month,
    geography_id,
    groupby_dimension,
):
    package = load_source_package(alias)
    report = validate_source_package(package.package_path, year=2025)
    facts = package.build_facts(2025)

    assert report.valid
    assert report.counts["record_set_count"] == 9
    assert report.counts["row_count"] == rows_per_month * 9
    assert report.counts["source_record_count"] == rows_per_month * 9
    assert len(facts) == rows_per_month * 9
    assert {fact.period.value for fact in facts} == set(MONTHS)
    assert all(fact.period.type == "month" for fact in facts)
    assert all(fact.measure.concept == "dwp.uc_benefit_units" for fact in facts)
    # The #188 histories' source concept is kept so consumers bound to
    # dwp.uc_households keep resolving after the May snapshots retire.
    assert all(fact.measure.source_concept == "dwp.uc_households" for fact in facts)
    assert all(fact.entity.name == "benefit_unit" for fact in facts)
    assert all(fact.geography.id == geography_id for fact in facts)
    assert all(fact.assertion == "observation" for fact in facts)
    assert all(fact.provenance_class == "administrative" for fact in facts)
    assert all(fact.layout.groupby_dimension == groupby_dimension for fact in facts)
    assert all(fact.source_row_keys for fact in facts)
    assert validate_facts(facts).valid
    assert validate_consumer_fact_contract(facts).valid
    assert len(consumer_fact_rows(facts)) == len(facts)


def test_family_type_child_entitlement_cross_keeps_both_publisher_dimensions():
    facts = load_source_package(
        "dwp-uc-households-family-type-child-entitlement-april-december-2025"
    ).build_facts(2025)

    with_element = _fact(
        facts,
        period="2025-04",
        family_type="Single, with children",
        child_entitlement="Yes",
    )
    without_element = _fact(
        facts,
        period="2025-04",
        family_type="Single, with children",
        child_entitlement="No",
    )
    assert with_element.value == 2_093_294
    assert without_element.value == 114_267
    assert {constraint.variable for constraint in with_element.constraints} == {
        "family_type",
        "child_entitlement",
    }
    assert (
        _fact(
            facts,
            period="2025-12",
            family_type="Couple, with children",
            child_entitlement="Yes",
        ).value
        == 851_844
    )
    # Childless family types never carry a child element.
    assert all(
        fact.value == 0
        for fact in facts
        if fact.filters["child_entitlement"] == "Yes"
        and fact.filters["family_type"]
        in {"Single, no children", "Couple, no children"}
    )


def test_number_of_children_child_entitlement_cross_preserves_publisher_categories():
    facts = load_source_package(
        "dwp-uc-households-children-child-entitlement-april-december-2025"
    ).build_facts(2025)

    # Digit-only publisher labels land as integers, as in the number-of-children
    # package this cross extends.
    assert {fact.filters["number_of_children"] for fact in facts} == {
        0,
        1,
        2,
        3,
        4,
        "5 or more",
        "Unknown or missing",
        "Not available prior to April 2019",
    }
    assert (
        _fact(
            facts, period="2025-04", number_of_children=2, child_entitlement="Yes"
        ).value
        == 1_084_955
    )
    assert (
        _fact(
            facts, period="2025-04", number_of_children=2, child_entitlement="No"
        ).value
        == 18_473
    )
    assert (
        _fact(
            facts, period="2025-12", number_of_children=1, child_entitlement="Yes"
        ).value
        == 1_122_012
    )


def test_payment_indicator_no_matches_the_no_payment_award_band_cell_for_cell():
    """DWP's Payment Indicator 'No' is the nil-award household; the award-band
    cube publishes the same households under its 'No payment' band."""
    indicator = load_source_package(
        "dwp-uc-households-family-type-payment-indicator-april-december-2025"
    ).build_facts(2025)
    bands = load_source_package(
        "dwp-uc-payment-distribution-april-december-2025"
    ).build_facts(2025)

    assert (
        _fact(
            indicator,
            period="2025-04",
            family_type="Single, with children",
            payment_indicator="No",
        ).value
        == 74_530
    )
    assert (
        _fact(
            indicator,
            period="2025-05",
            family_type="Single, with children",
            payment_indicator="No",
        ).value
        == 67_972
    )
    for period in MONTHS:
        for family_type in (
            "Single, no children",
            "Single, with children",
            "Couple, no children",
            "Couple, with children",
            "Unknown or missing family type",
        ):
            nil_award = _fact(
                indicator,
                period=period,
                family_type=family_type,
                payment_indicator="No",
            )
            no_payment_band = _fact(
                bands,
                period=period,
                family_type=family_type,
                monthly_award_amount_bands="No payment",
            )
            assert nil_award.value == no_payment_band.value, (period, family_type)


def test_payment_distribution_history_omits_the_pre_september_2022_band():
    """DWP's '£1500.01 or over' band applies to months up to August 2022 only
    (Stat-Xplore metadata); it is zero in every April to December 2025 cell and
    is not ported, so nothing can bind it by mistake."""
    facts = load_source_package(
        "dwp-uc-payment-distribution-april-december-2025"
    ).build_facts(2025)
    bands = {fact.filters["monthly_award_amount_bands"] for fact in facts}

    assert len(facts) == 27 * 5 * 9
    assert len(bands) == 27
    assert "£1500.01 or over" not in bands
    assert {
        "No payment",
        "£1400.01 to £1500.00",
        "£1500.01 to £1600.00",
        "£2500.01 or over",
    } <= bands
    assert all(fact.layout.table_record_kind == "detail" for fact in facts)
    assert (
        _fact(
            facts,
            period="2025-04",
            family_type="Single, no children",
            monthly_award_amount_bands="No payment",
        ).value
        == 345_734
    )
    assert (
        _fact(
            facts,
            period="2025-04",
            family_type="Single, with children",
            monthly_award_amount_bands="£1500.01 to £1600.00",
        ).value
        > 0
    )
    assert (
        _fact(
            facts,
            period="2025-12",
            family_type="Single, with children",
            monthly_award_amount_bands="£2500.01 or over",
        ).value
        == 93_095
    )


def test_scotland_youngest_child_history_carries_single_years_of_age():
    facts = load_source_package(
        "dwp-uc-scotland-youngest-child-april-december-2025"
    ).build_facts(2025)
    ages = {
        fact.filters["age_of_youngest_child_bands_and_single_year"] for fact in facts
    }

    assert ages == set(range(20)) | {
        "No children",
        "Unknown or missing",
        "Not available prior to April 2019",
    }
    assert all(fact.geography.name == "Scotland" for fact in facts)
    assert (
        _fact(
            facts, period="2025-04", age_of_youngest_child_bands_and_single_year=0
        ).value
        == 14_451
    )
    assert (
        _fact(
            facts, period="2025-12", age_of_youngest_child_bands_and_single_year=0
        ).value
        == 14_170
    )
    assert (
        _fact(
            facts,
            period="2025-12",
            age_of_youngest_child_bands_and_single_year="No children",
        ).value
        == 378_281
    )
