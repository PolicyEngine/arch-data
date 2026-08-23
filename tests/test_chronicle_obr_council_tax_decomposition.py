"""OBR EFO March 2026 Table 4.1 council tax block, carried in full.

Row 19 'Total net council tax receipts' (concept obr.council_tax_total) equals
row 15 'Total council tax receipts' (England + Scotland + Wales) plus NI
domestic rates, the council tax accruals adjustment and, from 2028-29, the
high-value council tax surcharge. The decomposition rows let a consumer bind a
household council tax liability to the GB cash-receipts total instead of the
UK total that carries components with no household counterpart.
"""

from __future__ import annotations

import pytest

from chronicle.source_package import load_source_package

RECEIPTS_GB = "obr.council_tax_receipts_england_scotland_wales"
ACCRUALS = "obr.council_tax_accruals_adjustment"
SURCHARGE = "obr.council_tax_high_value_surcharge"


def _by_concept_period(facts):
    table = {}
    for fact in facts:
        table[(fact.measure.concept, fact.period.value)] = fact
    return table


def test_obr_table_4_1_council_tax_decomposition_rows():
    package = load_source_package("obr-efo-expenditure-march-2026")
    facts = package.build_facts(2026)
    table = _by_concept_period(facts)

    receipts_years = {period for concept, period in table if concept == RECEIPTS_GB}
    accruals_years = {period for concept, period in table if concept == ACCRUALS}
    surcharge_years = {period for concept, period in table if concept == SURCHARGE}
    assert receipts_years == set(range(2024, 2031))
    assert accruals_years == set(range(2024, 2031))
    # The publisher prints the surcharge from 2028-29 only; blank cells emit no facts.
    assert surcharge_years == {2028, 2029, 2030}

    # FY2025-26: GBP 49.569bn GB receipts, GBP 0.862bn accruals adjustment.
    assert table[(RECEIPTS_GB, 2025)].value == pytest.approx(49_569_234_862.02, abs=0.01)
    assert table[(ACCRUALS, 2025)].value == pytest.approx(861_928_964.29, abs=0.01)
    assert table[(SURCHARGE, 2028)].value == 454_292_600
    assert table[(RECEIPTS_GB, 2024)].assertion == "observation"
    assert table[(RECEIPTS_GB, 2025)].assertion == "source_projection"
    assert {table[(RECEIPTS_GB, y)].geography.id for y in range(2024, 2031)} == {
        "K02000001"
    }

    for year in range(2024, 2031):
        nations = sum(
            table[(concept, year)].value
            for concept in (
                "obr.council_tax_england",
                "obr.council_tax_scotland",
                "obr.council_tax_wales",
            )
        )
        # Row 15 is the sum of the three nation rows.
        assert table[(RECEIPTS_GB, year)].value == pytest.approx(nations, rel=1e-9)
        # Row 19 is row 15 + NI domestic rates + accruals (+ surcharge from 2028-29).
        components = (
            table[(RECEIPTS_GB, year)].value
            + table[("obr.domestic_rates", year)].value
            + table[(ACCRUALS, year)].value
            + (table[(SURCHARGE, year)].value if (SURCHARGE, year) in table else 0)
        )
        assert table[("obr.council_tax_total", year)].value == pytest.approx(
            components, rel=1e-9
        )
    assert len(facts) == 150
