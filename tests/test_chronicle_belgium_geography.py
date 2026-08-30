"""Tests for Belgium's publisher-backed NIS crosswalk contract."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from chronicle.jurisdictions.be import (
    NISCodeCrosswalk,
    NISCrosswalkError,
    NISCrosswalkLookupError,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CROSSWALK_PATH = (
    REPO_ROOT
    / "db"
    / "data"
    / "statbel"
    / "nis_2025_commune_crosswalk"
    / "statbel_nis_2025_commune_crosswalk.csv"
)


def test_nis_crosswalk_loads_publisher_rows_and_merged_codes():
    crosswalk = NISCodeCrosswalk.from_csv(CROSSWALK_PATH)

    assert len(crosswalk.rows) == 581
    assert {
        row.source_nis
        for row in crosswalk.rows
        if row.target_nis == "82039" and row.relationship == "merged"
    } == {"82003", "82005"}
    assert (
        crosswalk.translate(
            "11007",
            source_vintage="nis_2019_2024",
            target_vintage="nis_2025",
        ).target_nis
        == "11002"
    )


def test_nis_translation_plan_preserves_many_to_one_identity_rows():
    crosswalk = NISCodeCrosswalk.from_csv(CROSSWALK_PATH)

    plan = crosswalk.translation_plan(
        ["11056", "46003", "46013"],
        source_vintage="nis_2019_2024",
        target_vintage="nis_2025",
    )

    assert [row.source_nis for row in plan] == ["11056", "46003", "46013"]
    assert [row.target_nis for row in plan] == ["46030", "46030", "46030"]


def test_nis_translation_fails_when_crosswalk_has_no_declared_row():
    crosswalk = NISCodeCrosswalk.from_csv(CROSSWALK_PATH)

    with pytest.raises(NISCrosswalkLookupError, match="No NIS crosswalk row"):
        crosswalk.translate(
            "99999",
            source_vintage="nis_2019_2024",
            target_vintage="nis_2025",
        )


def test_nis_crosswalk_reports_truncated_csv_rows_as_contract_errors(tmp_path):
    path = tmp_path / "truncated.csv"
    path.write_text(
        "source_nis,source_name,source_vintage,target_nis,target_name,"
        "target_vintage,effective_date,relationship,source_url\n"
        "11001,Aartselaar,nis_2019_2024,11001,Aartselaar,nis_2025,"
        "2019-01-01,unchanged\n",
        encoding="utf-8",
    )

    with pytest.raises(NISCrosswalkError, match="Invalid.*line 2"):
        NISCodeCrosswalk.from_csv(path)


@pytest.mark.parametrize("conflicting", [False, True])
def test_nis_crosswalk_rejects_every_duplicate_source_key(conflicting):
    row = NISCodeCrosswalk.from_csv(CROSSWALK_PATH).rows[0]
    duplicate = replace(row, target_name="Conflicting name") if conflicting else row

    with pytest.raises(NISCrosswalkError, match="Duplicate NIS crosswalk mapping"):
        NISCodeCrosswalk([row, duplicate])
