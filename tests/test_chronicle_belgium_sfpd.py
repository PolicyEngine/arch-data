"""Direct publisher-artifact tests for Belgium SFPD monthly facts."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

from chronicle.core import validate_facts
from chronicle.source_package import load_source_package, validate_source_package


REPO_ROOT = Path(__file__).resolve().parents[1]
SFPD_PACKAGE = "sfpd-legal-pension-caseload-2025"


@lru_cache
def _sfpd_outputs():
    package = load_source_package(SFPD_PACKAGE)
    cells = tuple(package.build_source_cells(2025))
    facts = tuple(package.build_facts(2025, cells=list(cells)))
    return cells, facts


def test_sfpd_pension_and_grapa_facts_match_publisher_pdf_cells():
    cells, facts = _sfpd_outputs()

    by_concept = {fact.measure.concept: fact.value for fact in facts}
    assert by_concept == {
        "sfpd.employee_or_self_employed_legal_pension_beneficiary_count": 2435457,
        "sfpd.employee_or_self_employed_legal_pension_monthly_expenditure": (
            3759582728.06
        ),
        "sfpd.grapa_beneficiary_count": 117650,
        "sfpd.grapa_monthly_expenditure": 86398449.47,
    }

    cells_by_address = {cell.address: cell.raw_value for cell in cells}
    assert cells_by_address["D881"] == "2.435.457"
    assert cells_by_address["E881"] == 2435457
    assert cells_by_address["D878"] == "3.759.582.728,06"
    assert cells_by_address["E878"] == 3759582728.06
    assert cells_by_address["D1756"] == "117.650"
    assert cells_by_address["E1756"] == 117.65
    assert cells_by_address["D1757"] == "86.398.449,47"
    assert cells_by_address["E1757"] == 86398449.47

    assert {fact.period.type for fact in facts} == {"month"}
    assert {fact.period.value for fact in facts} == {"2025-02"}
    assert {fact.source.source_name for fact in facts} == {
        "sfpd_monthly_social_benefits"
    }
    assert {fact.source.source_file for fact in facts} == {"fr_stat_2502.pdf"}
    assert {fact.source.url for fact in facts} == {
        "https://www.sfpd.fgov.be/files/3432/fr_stat_2502.pdf"
    }
    assert {fact.geography.id for fact in facts} == {"BE"}
    assert {fact.geography.vintage for fact in facts} == {"current"}
    assert {fact.assertion for fact in facts} == {"observation"}
    assert all(fact.source_cell_keys for fact in facts)
    assert validate_facts(facts).valid


def test_sfpd_monthly_statistics_artifact_is_hash_pinned():
    data_dir = REPO_ROOT / "db" / "data" / "sfpd" / "legal_pension_caseload_2025"
    publisher_pdf = data_dir / "fr_stat_2502.pdf"
    package_report = validate_source_package(SFPD_PACKAGE, year=2025)

    assert package_report.valid, package_report.to_dict()
    assert package_report.counts == {
        "record_set_count": 4,
        "row_count": 4,
        "measure_count": 4,
        "source_record_count": 4,
        "source_region_count": 4,
    }
    assert publisher_pdf.stat().st_size == 2319705
    assert hashlib.sha256(publisher_pdf.read_bytes()).hexdigest() == (
        "0d6173e71a0e9c2cd220cd024a5b5fecbb6ca79f8b791cbd2b3368e7f8412106"
    )
    assert not (data_dir / "sfpd_legal_pension_caseload_2025.csv").exists()
