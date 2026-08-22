"""Offline ETL coverage for the Eurostat BE/DE/FR pilot packages."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from chronicle.consumer_contract import validate_consumer_fact_contract
from chronicle.core import validate_facts
from chronicle.source_package import (
    SOURCE_PACKAGE_ALIASES,
    load_source_package,
    validate_source_package,
)
from chronicle.sources.cells import validate_source_cells
from chronicle.sources.rows import build_source_row_key, validate_source_rows
from chronicle.suite import build_source_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ONLY_COMMENT = (
    "# EVALUATION-ONLY by class: Ledger ingests everything; "
    "the Populace gate decides use."
)
EUROSTAT_PACKAGES = {
    "eurostat-gov-10a-taxag": ("gov_10a_taxag", 2024, 24, 24),
    "eurostat-spr-exp-func": ("spr_exp_func", 2023, 27, 27),
    "eurostat-ilc-li02": ("ilc_li02", 2024, 3, 3),
    "eurostat-ilc-di01": ("ilc_di01", 2024, 54, 54),
}
EUROSTAT_DATASET_IDS = {values[0] for values in EUROSTAT_PACKAGES.values()}
EXPECTED_QUERY_FILTERS = {
    "gov_10a_taxag": {
        "freq": ["A"],
        "unit": ["MIO_EUR"],
        "sector": ["S13"],
        "na_item": ["D2", "D5", "D51", "D61"],
        "geo": ["BE", "DE", "FR"],
        "time": ["2023", "2024"],
    },
    "spr_exp_func": {
        "freq": ["A"],
        "spdeps": ["SPR"],
        "spfunc": [
            "TOTAL",
            "SICK",
            "DIS",
            "OLD",
            "SRV",
            "FAM",
            "UNE",
            "HOU",
            "EXCL",
        ],
        "unit": ["MIO_EUR"],
        "geo": ["BE", "DE", "FR"],
        "time": ["2023"],
    },
    "ilc_li02": {
        "freq": ["A"],
        "statinfo": ["MED_EI"],
        "unit": ["PC"],
        "rskpovth": ["B_60"],
        "sex": ["T"],
        "age": ["TOTAL"],
        "geo": ["BE", "DE", "FR"],
        "time": ["2024"],
    },
    "ilc_di01": {
        "freq": ["A"],
        "quant_inc": [f"D{index}" for index in range(1, 10)],
        "statinfo": ["TC", "SHARE"],
        "unit": ["EUR"],
        "geo": ["BE", "DE", "FR"],
        "time": ["2024"],
    },
}


@lru_cache
def _package_outputs(alias: str):
    _dataset_id, year, _expected_count, _expected_row_count = EUROSTAT_PACKAGES[alias]
    package = load_source_package(alias)
    rows = package.build_source_rows(year)
    cells = package.build_source_cells(year, source_rows=rows)
    facts = package.build_facts(year, cells=cells, source_rows=rows)
    return package, rows, cells, facts


def test_eurostat_aliases_and_packages_validate_end_to_end():
    assert set(EUROSTAT_PACKAGES) <= set(SOURCE_PACKAGE_ALIASES)

    for alias, (
        _dataset_id,
        year,
        expected_count,
        expected_row_count,
    ) in EUROSTAT_PACKAGES.items():
        package, rows, cells, facts = _package_outputs(alias)
        package_report = validate_source_package(alias, year=year)

        assert package.artifact.parser == "json_stat_2_full_rows"
        assert package_report.valid, package_report.to_dict()
        assert len(rows) == expected_row_count
        assert len(facts) == expected_count
        assert validate_source_rows(rows).valid
        assert validate_source_cells(cells).valid
        assert validate_facts(facts).valid
        contract_report = validate_consumer_fact_contract(facts)
        assert contract_report.valid, contract_report.to_dict()


@pytest.mark.parametrize("alias", EUROSTAT_PACKAGES)
def test_eurostat_packages_pass_full_agent_acceptance(alias, tmp_path):
    _dataset_id, year, expected_count, _expected_row_count = EUROSTAT_PACKAGES[alias]

    report = build_source_suite(alias, tmp_path / alias, year=year)

    assert report.valid, report.to_dict()
    assert report.agent_acceptance.valid, report.agent_acceptance.to_dict()
    assert report.agent_acceptance.counts["fact_count"] == expected_count
    assert report.agent_acceptance.counts["row_semantic_error_count"] == 0


def test_eurostat_facts_preserve_raw_cube_dimensions_and_scaling():
    unit_mapping = {
        "MIO_EUR": ("eur", 1_000_000),
        "PC": ("percent", 1),
        "EUR": ("eur", 1),
    }

    for alias in EUROSTAT_PACKAGES:
        _package, rows, _cells, facts = _package_outputs(alias)
        rows_by_key = {build_source_row_key(row): row for row in rows}

        for fact in facts:
            assert len(fact.source_row_keys) == 1
            source_row = rows_by_key[fact.source_row_keys[0]]
            raw_unit = str(source_row.values["unit"])
            if alias == "eurostat-ilc-di01":
                expected_unit = {
                    "SHARE": "percent",
                    "TC": "eur",
                }[str(source_row.values["statinfo"])]
                scale = 1
            else:
                expected_unit, scale = unit_mapping[raw_unit]

            assert source_row.values["geo"] == fact.geography.id
            assert str(source_row.values["time"]) == str(fact.period.value)
            assert fact.geography.level == "country"
            assert fact.geography.vintage == "current"
            assert fact.measure.unit == expected_unit
            assert fact.value == pytest.approx(source_row.values["value"] * scale)


def test_eurostat_provenance_and_evaluation_only_boundary():
    administrative_aliases = {
        "eurostat-gov-10a-taxag",
        "eurostat-spr-exp-func",
    }
    survey_aliases = {"eurostat-ilc-li02", "eurostat-ilc-di01"}

    for alias in administrative_aliases:
        facts = _package_outputs(alias)[3]
        assert {fact.provenance_class for fact in facts} == {"administrative"}
        assert {fact.survey_instrument for fact in facts} == {None}

    for alias in survey_aliases:
        package, _rows, _cells, facts = _package_outputs(alias)
        package_text = (package.package_path / "source_package.yaml").read_text()
        assert EVALUATION_ONLY_COMMENT in package_text
        assert {fact.provenance_class for fact in facts} == {"survey_aggregate"}
        assert {fact.survey_instrument for fact in facts} == {"EU-SILC"}

    di01_facts = _package_outputs("eurostat-ilc-di01")[3]
    assert Counter(
        (fact.measure.unit, fact.aggregation.method) for fact in di01_facts
    ) == {
        ("percent", "share"): 27,
        ("eur", "quantile"): 27,
    }


def test_eurostat_production_values_match_publisher_bytes():
    # Decoded independently from the raw JSON-stat cube (row-major index over
    # freq/unit/sector/na_item/geo/time): D2 taxes on production and imports,
    # calendar year 2023, MIO_EUR scaled by 1,000,000. Exact equality, not
    # approx: publisher lexemes must survive scaling bit-for-bit.
    _package, rows, _cells, facts = _package_outputs("eurostat-gov-10a-taxag")
    rows_by_key = {build_source_row_key(row): row for row in rows}
    expected = {"BE": 72_825_500_000, "DE": 428_710_000_000, "FR": 446_580_000_000}

    d2_2023 = {
        source_row.values["geo"]: fact
        for fact in facts
        for source_row in (rows_by_key[fact.source_row_keys[0]],)
        if source_row.values["na_item"] == "D2"
        and str(source_row.values["time"]) == "2023"
    }

    assert set(d2_2023) == set(expected)
    for geo, value in expected.items():
        assert d2_2023[geo].value == value
        assert isinstance(d2_2023[geo].value, int)
        assert d2_2023[geo].measure.unit == "eur"
        assert d2_2023[geo].geography.id == geo

    # The decimal-scaling regression case: 16448.06 MIO_EUR must scale to
    # exactly 16,448,060,000 (binary-float multiply emitted ...000.000002).
    _package, spr_rows, _cells, spr_facts = _package_outputs("eurostat-spr-exp-func")
    spr_rows_by_key = {build_source_row_key(row): row for row in spr_rows}
    be_disability = [
        fact
        for fact in spr_facts
        for source_row in (spr_rows_by_key[fact.source_row_keys[0]],)
        if source_row.values["geo"] == "BE" and source_row.values["spfunc"] == "DIS"
    ]
    assert len(be_disability) == 1
    assert be_disability[0].value == 16_448_060_000
    assert isinstance(be_disability[0].value, int)


def test_eurostat_production_surfaces_carry_no_fixture_identity():
    # Fixture identity must be absent everywhere it could reach a fact:
    # package specs (vintage, sheet names, notes), db manifests, and the
    # artifacts themselves. Case-insensitive, marker-word based.
    forbidden = re.compile(r"fixture|sentinel|synthetic", re.IGNORECASE)
    surfaces = sorted(
        list((REPO_ROOT / "packages" / "eurostat").rglob("source_package.yaml"))
        + list((REPO_ROOT / "db" / "data" / "eurostat").rglob("manifest.yaml"))
        + list((REPO_ROOT / "db" / "data" / "eurostat").rglob("*.json"))
    )
    assert len(surfaces) >= 12
    for surface in surfaces:
        match = forbidden.search(surface.read_text())
        assert match is None, f"{surface}: {match.group(0)!r}"


def test_eurostat_artifacts_match_verified_live_dimension_shapes_and_labels():
    expected_shapes = {
        "spr_exp_func": (
            ["freq", "spdeps", "spfunc", "unit", "geo", "time"],
            [1, 1, 9, 1, 3, 1],
        ),
        "ilc_li02": (
            ["freq", "statinfo", "unit", "rskpovth", "sex", "age", "geo", "time"],
            [1, 1, 1, 1, 1, 1, 3, 1],
        ),
        "ilc_di01": (
            ["freq", "quant_inc", "statinfo", "unit", "geo", "time"],
            [1, 9, 2, 1, 3, 1],
        ),
    }

    fixtures = {}
    for dataset_id, (expected_id, expected_size) in expected_shapes.items():
        package_dir = REPO_ROOT / "db" / "data" / "eurostat" / dataset_id
        manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
        filename = next(iter(manifest["files"].values()))["filename"]
        fixture = json.loads((package_dir / filename).read_text())
        fixtures[dataset_id] = fixture

        assert fixture["id"] == expected_id
        assert fixture["size"] == expected_size

    assert fixtures["spr_exp_func"]["dimension"]["spfunc"]["category"]["index"] == {
        "TOTAL": 0,
        "SICK": 1,
        "DIS": 2,
        "OLD": 3,
        "SRV": 4,
        "FAM": 5,
        "UNE": 6,
        "HOU": 7,
        "EXCL": 8,
    }
    assert fixtures["ilc_li02"]["dimension"]["statinfo"]["category"]["label"] == {
        "MED_EI": "Median equivalised income"
    }
    assert fixtures["ilc_li02"]["dimension"]["rskpovth"]["category"]["label"] == {
        "B_60": "Below 60%"
    }
    assert fixtures["ilc_di01"]["dimension"]["statinfo"]["category"]["label"] == {
        "TC": "Top cut-off point",
        "SHARE": "Share of national equivalised income",
    }
    assert (
        "D10" not in fixtures["ilc_di01"]["dimension"]["quant_inc"]["category"]["index"]
    )

    li02_package_text = (
        REPO_ROOT / "packages" / "eurostat" / "ilc_li02" / "source_package.yaml"
    ).read_text()
    assert 'B_60 is "Below 60%"' in li02_package_text
    assert 'A_60 is "Above 60%"' in li02_package_text


def test_eurostat_manifests_pin_real_publisher_artifacts():
    for (
        dataset_id,
        _year,
        _expected_count,
        _expected_row_count,
    ) in EUROSTAT_PACKAGES.values():
        package_dir = REPO_ROOT / "db" / "data" / "eurostat" / dataset_id
        manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
        file_spec = next(iter(manifest["files"].values()))
        artifact_path = package_dir / file_spec["filename"]
        artifact = json.loads(artifact_path.read_text())
        content = artifact_path.read_bytes()
        markers = (
            " ".join(
                str(artifact.get(field) or "") for field in ("label", "source", "note")
            )
            + " "
            + str(manifest.get("source_name", ""))
            + " "
            + str(file_spec.get("source_table", ""))
        )

        assert file_spec["filename"] == f"{dataset_id}.json"
        assert file_spec["sha256"] == hashlib.sha256(content).hexdigest()
        assert file_spec["size_bytes"] == len(content)
        assert file_spec["storage"]["r2"]["uri"].startswith("r2://ledger-raw/")
        assert file_spec["sha256"] in file_spec["storage"]["r2"]["uri"]
        assert artifact["source"] == "ESTAT"
        assert "TEST FIXTURE" not in markers
        assert "sentinel" not in markers.lower()


def test_fetch_manifest_has_exact_filtered_eurostat_requests():
    fetch_manifest = json.loads(
        (REPO_ROOT / "FETCH-MANIFEST-EUROSTAT.json").read_text()
    )
    fetches = fetch_manifest["fetches"]

    assert fetch_manifest["schema_version"] == "ledger.fetch_manifest.v1"
    assert {fetch["dataset_id"] for fetch in fetches} == EUROSTAT_DATASET_IDS
    for fetch in fetches:
        dataset_id = fetch["dataset_id"]
        parsed = urlsplit(fetch["source_url"])
        query = parse_qs(parsed.query)
        package_manifest = yaml.safe_load(
            (
                REPO_ROOT / "db" / "data" / "eurostat" / dataset_id / "manifest.yaml"
            ).read_text()
        )
        artifact_spec = next(iter(package_manifest["files"].values()))

        assert parsed.scheme == "https"
        assert parsed.netloc == "ec.europa.eu"
        assert parsed.path.endswith(f"/data/{dataset_id}")
        assert query.pop("format") == ["JSON"]
        assert query.pop("lang") == ["en"]
        assert query == EXPECTED_QUERY_FILTERS[dataset_id]
        assert fetch["destination"] == (
            f"db/data/eurostat/{dataset_id}/{dataset_id}.json"
        )
        sha = fetch["sha256"]
        dest = REPO_ROOT / fetch["destination"]
        assert re.fullmatch(r"[0-9a-f]{64}", sha)
        assert dest.exists()
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == sha
        assert artifact_spec["sha256"] == sha
        assert artifact_spec["source_url"] == fetch["source_url"]
