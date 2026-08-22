"""Deterministic ETL tests for generated administrative source packages."""

import pytest

from chronicle.sources.admin_packages import (
    IRS_PACKAGE_ID,
    PACKAGE_BUILDERS,
    PEP_PACKAGE_ID,
    SNAP_PACKAGE_ID,
    _county_fips,
    build_census_pep_county_package,
    build_irs_soi_county_package,
    build_usda_snap_monthly_package,
    write_packages,
)


def test_generated_admin_source_packages_have_no_drift():
    assert write_packages(list(PACKAGE_BUILDERS), check=True) == []


def test_county_packages_use_one_record_set_with_row_geographies(tmp_path):
    _write_irs_test_source(tmp_path, _THREE_COUNTY_IRS_ROWS)
    _write_pep_test_source(tmp_path, _THREE_COUNTY_PEP_ROWS)

    irs = build_irs_soi_county_package(tmp_path)
    pep = build_census_pep_county_package(tmp_path)

    assert irs["package_id"] == IRS_PACKAGE_ID
    assert pep["package_id"] == PEP_PACKAGE_ID
    assert len(irs["record_sets"]) == 1
    assert len(pep["record_sets"]) == 1
    assert len(irs["record_sets"][0]["measures"]) == 2
    assert len(pep["record_sets"][0]["measures"]) == 1
    assert "artifact_year" not in irs["artifact"]
    assert "artifact_year" not in pep["artifact"]
    assert irs["record_sets"][0]["period"] == "2022"
    assert pep["record_sets"][0]["geography_vintage"] == "2024"
    assert {
        row["geography_id"] for row in irs["record_sets"][0]["rows"]
    } == {
        "0500000US01001",
        "0500000US06037",
        "0500000US11001",
    }
    assert all(
        row["geography_level"] == "county"
        for row in pep["record_sets"][0]["rows"]
    )
    assert all(
        row["geography_vintage"] == "2024"
        for row in pep["record_sets"][0]["rows"]
    )


def test_county_fixture_packages_cannot_masquerade_as_publishers(tmp_path):
    _write_irs_test_source(tmp_path, _THREE_COUNTY_IRS_ROWS)
    _write_pep_test_source(tmp_path, _THREE_COUNTY_PEP_ROWS)

    irs = build_irs_soi_county_package(tmp_path)
    pep = build_census_pep_county_package(tmp_path)

    assert irs["fixture"] is True
    assert pep["fixture"] is True
    assert irs["artifact"]["source_name"] == "test_fixture_irs_soi"
    assert pep["artifact"]["source_name"] == "test_fixture_census_pep"
    assert "TEST FIXTURE" in irs["artifact"]["extraction_method"]
    assert "TEST FIXTURE" in pep["artifact"]["extraction_method"]


def test_snap_generator_emits_only_numeric_publisher_months():
    package = build_usda_snap_monthly_package()

    assert package["package_id"] == SNAP_PACKAGE_ID
    assert package["fixture"] is False
    assert package["artifact"]["artifact_year"] == 2025
    assert package["label"].endswith("through March 2025")
    assert len(package["record_sets"]) == 84
    assert sum(len(record_set["rows"]) for record_set in package["record_sets"]) == 636
    assert {record_set["period"] for record_set in package["record_sets"]} == {
        "2024-10",
        "2024-11",
        "2024-12",
        "2025-01",
        "2025-02",
        "2025-03",
    }
    assert all(
        record_set["period"] not in {
            "2025-04",
            "2025-05",
            "2025-06",
            "2025-07",
            "2025-08",
            "2025-09",
        }
        for record_set in package["record_sets"]
    )


@pytest.mark.parametrize(
    ("state_fips", "county_fips", "expected"),
    (("01", "001", "01001"), ("01", "01001", "01001")),
)
def test_county_fips_accepts_component_and_full_publisher_codes(
    state_fips,
    county_fips,
    expected,
):
    assert _county_fips(state_fips, county_fips) == expected


def test_county_fips_rejects_a_full_code_for_another_state():
    with pytest.raises(ValueError, match="does not match state"):
        _county_fips("01", "06037")


@pytest.mark.parametrize(
    ("state_fips", "county_fips"),
    (
        ("100", "001"),
        ("-1", "001"),
        ("01", "-1"),
        ("1a", "001"),
        ("01", "12a"),
        ("01", "123456"),
        ("", "001"),
        ("01", ""),
    ),
)
def test_county_fips_rejects_malformed_codes(state_fips, county_fips):
    with pytest.raises(ValueError, match="FIPS"):
        _county_fips(state_fips, county_fips)


_THREE_COUNTY_IRS_ROWS = (
    "01,AL,01001,Autauga County,25750,1795342\n"
    "06,CA,06037,Los Angeles County,4238450,457528383\n"
    "11,DC,11001,District of Columbia,10,20\n"
)
_THREE_COUNTY_PEP_ROWS = (
    "050,01,001,Alabama,Autauga County,61464\n"
    "050,06,037,California,Los Angeles County,9757179\n"
    "050,11,001,District of Columbia,District of Columbia,702250\n"
)


def _write_irs_test_source(root, rows, *, fixture=True):
    data_dir = root / "db/data/irs_soi/county_2022"
    data_dir.mkdir(parents=True)
    fixture_line = "    fixture: true\n" if fixture else ""
    (data_dir / "manifest.yaml").write_text(
        "files:\n"
        "  2022:\n"
        "    filename: 22incyallnoagi.csv\n"
        "    fetched_at: '2026-07-22T00:00:00+00:00'\n"
        f"{fixture_line}"
    )
    (data_dir / "22incyallnoagi.csv").write_text(
        "STATEFIPS,STATE,COUNTYFIPS,COUNTYNAME,N1,A00100\n" + rows
    )


def _write_pep_test_source(root, rows, *, fixture=True):
    data_dir = root / "db/data/census/pep_county_2024"
    data_dir.mkdir(parents=True)
    fixture_line = "    fixture: true\n" if fixture else ""
    (data_dir / "manifest.yaml").write_text(
        "files:\n"
        "  2024:\n"
        "    filename: co-est2024-alldata.csv\n"
        "    fetched_at: '2026-07-22T00:00:00+00:00'\n"
        f"{fixture_line}"
    )
    (data_dir / "co-est2024-alldata.csv").write_text(
        "SUMLEV,STATE,COUNTY,STNAME,CTYNAME,POPESTIMATE2024\n" + rows
    )


def test_irs_generator_rejects_a_source_without_county_rows(tmp_path):
    _write_irs_test_source(tmp_path, "01,AL,01000,Alabama,1,2\n")

    with pytest.raises(ValueError, match="no eligible county rows"):
        build_irs_soi_county_package(tmp_path)


def test_removing_the_fixture_marker_cannot_promote_a_small_source(tmp_path):
    # The masquerade attack: strip `fixture: true` from a tiny synthetic
    # source and hope it builds as publisher data. The inventory guard
    # must refuse anything outside a plausible national county count.
    _write_irs_test_source(tmp_path, _THREE_COUNTY_IRS_ROWS, fixture=False)

    with pytest.raises(ValueError, match="Implausible IRS SOI county inventory"):
        build_irs_soi_county_package(tmp_path)


@pytest.mark.parametrize(
    ("rows", "error"),
    (
        (
            "01,AL,001,Autauga County,1,2\n"
            "01,AL,01001,Autauga County duplicate,3,4\n",
            "Duplicate IRS county FIPS row",
        ),
        ("01,AL,01001,Autauga County,**,2\n", "Expected numeric N1"),
        ("01,AL,01999,Other areas,1,2\n", "Reserved IRS aggregate FIPS row"),
    ),
)
def test_irs_generator_rejects_ambiguous_or_non_numeric_rows(tmp_path, rows, error):
    _write_irs_test_source(tmp_path, rows)

    with pytest.raises(ValueError, match=error):
        build_irs_soi_county_package(tmp_path)


def test_nonfixture_county_packages_activate_only_their_fixed_years(tmp_path):
    irs_rows = "".join(
        f"{state:02},S{state:02},{state:02}{county:03},County {state}-{county},1,2\n"
        for state in range(1, 51)
        for county in range(1, 61)
    )
    _write_irs_test_source(tmp_path, irs_rows, fixture=False)

    _write_pep_test_source(
        tmp_path,
        "".join(
            f"050,{state:02},{county:03},S{state:02},County {state}-{county},1\n"
            for state in range(1, 51)
            for county in range(1, 61)
        ),
        fixture=False,
    )

    irs = build_irs_soi_county_package(tmp_path)
    pep = build_census_pep_county_package(tmp_path)

    assert irs["artifact"]["artifact_year"] == 2022
    assert irs["record_sets"][0]["period"] == "2022"
    assert irs["artifact"]["vintage"] == "tax_year_2022"
    assert irs["record_sets"][0]["geography_vintage"] == "2022"
    assert all(
        row["geography_vintage"] == "2022"
        for row in irs["record_sets"][0]["rows"]
    )
    assert pep["artifact"]["artifact_year"] == 2024
    assert pep["record_sets"][0]["period"] == 2024
    assert pep["record_sets"][0]["geography_vintage"] == "2024"
