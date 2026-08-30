"""Source-faithful Belgian child-benefit participation facts."""

from dataclasses import replace

import pytest

from chronicle.core import validate_facts
from chronicle.source_package import SOURCE_PACKAGE_ALIASES, load_source_package


OPGROEIEN_ALIAS = "opgroeien-groeipakket-basic-caseload-2025-12"
OPGROEIEN_COMPONENT_ALIAS = "opgroeien-groeipakket-caseload-2025"
IRISCARE_ALIAS = "iriscare-child-benefit-caseload-2025-12"
OSTBELGIEN_ALIAS = "ostbelgien-child-benefit-caseload-2025-12"
PARLEMENT_WALLONIE_ALIAS = "parlement-wallonie-child-benefit-partitions-2023-12"


def _facts(alias: str, year: int):
    return tuple(load_source_package(alias).build_facts(year))


def test_belgium_child_benefit_participation_aliases_are_registered():
    assert {
        OPGROEIEN_ALIAS,
        IRISCARE_ALIAS,
        OSTBELGIEN_ALIAS,
        PARLEMENT_WALLONIE_ALIAS,
    } <= set(SOURCE_PACKAGE_ALIASES)


def test_all_opgroeien_packages_use_administrative_scheme_scope():
    opgroeien_aliases = {
        alias
        for alias, path in SOURCE_PACKAGE_ALIASES.items()
        if path.parts[0] == "opgroeien"
    }

    assert opgroeien_aliases == {OPGROEIEN_ALIAS, OPGROEIEN_COMPONENT_ALIAS}
    for alias in opgroeien_aliases:
        facts = _facts(alias, 2025)
        assert {
            (fact.geography.level, fact.geography.id, fact.geography.vintage)
            for fact in facts
        } == {
            (
                "statistical_scope",
                "BE-GROEIPAKKET-SCHEME",
                "GROEIPAKKET_ADMINISTRATIVE_SCOPE_2025",
            )
        }


def test_opgroeien_basic_child_caseload_preserves_dashboard_query_scope():
    facts = _facts(OPGROEIEN_ALIAS, 2025)

    assert len(facts) == 1
    fact = facts[0]
    assert fact.value == 1_629_980
    assert (fact.period.type, fact.period.value) == ("month", "2025-12")
    assert (fact.geography.level, fact.geography.id) == (
        "statistical_scope",
        "BE-GROEIPAKKET-SCHEME",
    )
    assert (fact.entity.name, fact.entity.role) == (
        "person",
        "child_benefit_recipient",
    )
    assert fact.measure.concept == "opgroeien.groeipakket_basic_amount_children"
    assert fact.filters == {
        "groeipakket.component": "basic_amount",
        "publication_status": "provisional",
    }
    assert fact.period_coverage is not None
    assert fact.period_coverage.source_period_label == "2025/12"
    assert validate_facts(facts).valid


def test_iriscare_keeps_children_and_payment_recipients_distinct():
    facts = _facts(IRISCARE_ALIAS, 2025)
    by_concept = {fact.measure.concept: fact for fact in facts}

    assert {concept: fact.value for concept, fact in by_concept.items()} == {
        "iriscare.child_benefit_entitled_children": 304_966,
        "iriscare.child_benefit_payment_recipients": 162_745,
    }
    assert {(fact.entity.name, fact.entity.role) for fact in facts} == {
        ("person", "child_benefit_entitled_child"),
        ("person", "child_benefit_payment_recipient"),
    }
    assert {(fact.period.type, fact.period.value) for fact in facts} == {
        ("month", "2025-12")
    }
    assert {(fact.geography.level, fact.geography.id) for fact in facts} == {
        ("statistical_scope", "BE-IRISCARE-CHILD-BENEFIT-SCHEME")
    }
    assert {fact.filters["publication_status"] for fact in facts} == {"provisional"}
    assert validate_facts(facts).valid


def test_ostbelgien_keeps_children_and_payment_recipients_distinct():
    facts = _facts(OSTBELGIEN_ALIAS, 2025)
    by_concept = {fact.measure.concept: fact for fact in facts}

    assert {concept: fact.value for concept, fact in by_concept.items()} == {
        "ostbelgien.child_benefit_paid_children": 15_533,
        "ostbelgien.child_benefit_payment_recipients": 8_302,
    }
    assert {(fact.entity.name, fact.entity.role) for fact in facts} == {
        ("person", "child_benefit_paid_child"),
        ("person", "child_benefit_payment_recipient"),
    }
    assert {(fact.period.type, fact.period.value) for fact in facts} == {
        ("month", "2025-12")
    }
    assert {(fact.geography.level, fact.geography.id) for fact in facts} == {
        ("statistical_scope", "BE-DG")
    }
    assert validate_facts(facts).valid


def test_walloon_response_preserves_published_partitions_without_total_fact():
    facts = _facts(PARLEMENT_WALLONIE_ALIAS, 2023)
    by_measure_and_group = {
        (
            fact.measure.concept,
            fact.filters["parlement_wallonie.household_type"],
            fact.filters["parlement_wallonie.social_supplement_status"],
        ): fact.value
        for fact in facts
    }

    assert by_measure_and_group == {
        (
            "parlement_wallonie.child_benefit_recipient_children_by_household_group",
            "single_parent",
            "with_social_supplement",
        ): 149_169,
        (
            "parlement_wallonie.child_benefit_recipient_children_by_household_group",
            "single_parent",
            "without_social_supplement",
        ): 38_385,
        (
            "parlement_wallonie.child_benefit_recipient_children_by_household_group",
            "other_household",
            "with_social_supplement",
        ): 177_229,
        (
            "parlement_wallonie.child_benefit_recipient_children_by_household_group",
            "other_household",
            "without_social_supplement",
        ): 545_442,
        (
            "parlement_wallonie.child_benefit_recipient_households_by_household_group",
            "single_parent",
            "with_social_supplement",
        ): 89_575,
        (
            "parlement_wallonie.child_benefit_recipient_households_by_household_group",
            "single_parent",
            "without_social_supplement",
        ): 24_535,
        (
            "parlement_wallonie.child_benefit_recipient_households_by_household_group",
            "other_household",
            "with_social_supplement",
        ): 90_308,
        (
            "parlement_wallonie.child_benefit_recipient_households_by_household_group",
            "other_household",
            "without_social_supplement",
        ): 308_949,
    }

    assert not any(
        fact.measure.concept.endswith("_total")
        or fact.filters.get("parlement_wallonie.household_type") == "all"
        for fact in facts
    )
    assert {(fact.period.type, fact.period.value) for fact in facts} == {
        ("month", "2023-12")
    }
    assert {(fact.geography.level, fact.geography.id) for fact in facts} == {
        ("statistical_scope", "BE-WALLOON-FRENCH")
    }
    assert validate_facts(facts).valid


@pytest.mark.parametrize(
    ("alias", "year", "record_id", "required_addresses"),
    [
        (
            OPGROEIEN_ALIAS,
            2025,
            "opgroeien.groeipakket.month2025_12.basic_amount.children."
            "basic_amount_children.children",
            {"C2", "D2", "E2", "F2", "G2", "H2", "I2", "J2", "L2"},
        ),
        (
            IRISCARE_ALIAS,
            2025,
            "iriscare.child_benefit.month2025_12.payment_recipients."
            "payment_recipients.payment_recipients",
            {"C3", "D3", "E3", "F3", "G3", "H3", "J3"},
        ),
        (
            OSTBELGIEN_ALIAS,
            2025,
            "ostbelgien.child_benefit.month2025_12.payment_recipients."
            "payment_recipients.payment_recipients",
            {"C3", "D3", "E3", "F3", "H3"},
        ),
        (
            PARLEMENT_WALLONIE_ALIAS,
            2023,
            "parlement_wallonie.child_benefit.month2023_12.children."
            "single_parent_with_social_supplement.children",
            {"C2", "D2", "E2", "F2", "G2", "I2", "J2", "K2", "L2"},
        ),
    ],
)
def test_participation_source_evidence_is_in_record_lineage(
    alias,
    year,
    record_id,
    required_addresses,
):
    records = load_source_package(alias).build_source_records(year)
    record = {item.source_record_id: item for item in records}[record_id]

    assert required_addresses <= set(record.source_cell_addresses)


@pytest.mark.parametrize(
    ("alias", "year", "address", "replacement", "guard_label"),
    [
        (
            OPGROEIEN_ALIAS,
            2025,
            "H2",
            "Groeipakket=changed",
            "Dashboard Groeipakket filter",
        ),
        (
            IRISCARE_ALIAS,
            2025,
            "E3",
            "Households",
            "Dashboard measure view",
        ),
        (
            OSTBELGIEN_ALIAS,
            2025,
            "E3",
            "changed source description",
            "Source description",
        ),
        (
            PARLEMENT_WALLONIE_ALIAS,
            2023,
            "K2",
            "changed-pdf-digest",
            "Verbatim PDF SHA-256",
        ),
    ],
)
def test_participation_source_guard_drift_refuses_resolution(
    alias,
    year,
    address,
    replacement,
    guard_label,
):
    package = load_source_package(alias)
    cells = package.build_source_cells(year)
    mutated = tuple(
        replace(cell, raw_value=replacement, display_value=replacement)
        if cell.address == address
        else cell
        for cell in cells
    )

    with pytest.raises(ValueError, match=guard_label):
        package.build_source_records(year, cells=mutated)
