"""Boundary tests for Chronicle source-data ownership."""

from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_PACKAGE_ROOTS = {"calibration", "micro"}


def test_chronicle_modules_do_not_import_non_chronicle_runtime_packages():
    chronicle_root = Path(__file__).resolve().parents[1] / "chronicle"
    violations: list[str] = []

    for path in sorted(chronicle_root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            imported_roots: list[str] = []
            if isinstance(node, ast.Import):
                imported_roots = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots = [node.module.split(".", 1)[0]]

            for root in imported_roots:
                if root in FORBIDDEN_PACKAGE_ROOTS:
                    relative_path = path.relative_to(chronicle_root.parent)
                    violations.append(f"{relative_path}:{node.lineno}: {root}")

    assert violations == []


def test_repository_does_not_ship_raw_microdata_namespace():
    repo_root = Path(__file__).resolve().parents[1]

    assert not (repo_root / "chronicle" / "microdata").exists()
    assert not (repo_root / "policyengine_chronicle" / "microdata").exists()
    assert not (repo_root / "micro").exists()
    assert not (repo_root / "calibration").exists()
    assert not (repo_root / "storage").exists()


def test_uk_legacy_etl_cleanup_checklist_accounts_for_legacy_series():
    repo_root = Path(__file__).resolve().parents[1]
    checklist = (repo_root / "docs" / "pe-uk-source-checklist.md").read_text()

    required_entries = [
        "`db/etl_obr.py` `gdp`",
        "`db/etl_obr.py` `total_receipts`",
        "`db/etl_obr.py` `total_managed_expenditure`",
        "`db/etl_obr.py` `public_sector_net_borrowing`",
        "`db/etl_obr.py` `public_sector_net_debt`",
        "`db/etl_obr.py` `real_gdp_growth`",
        "`db/etl_obr.py` `unemployment_rate`",
        "`db/etl_obr.py` `cpi_inflation`",
        "`db/etl_obr.py` `rpi_inflation`",
        "`db/etl_obr.py` `bank_rate`",
        "`db/etl_obr.py` `employment`",
        "`db/etl_ons.py` `population_total`",
        "`db/etl_ons.py` `population_age_0_15`",
        "`db/etl_ons.py` `population_age_16_64`",
        "`db/etl_ons.py` `population_age_65_plus`",
        "`db/etl_ons.py` `households_total`",
        "`db/etl_ons.py` `average_household_size`",
        "`db/etl_hmrc.py` `income_tax`",
        "`db/etl_hmrc.py` `national_insurance`",
        "`db/etl_hmrc.py` `capital_gains_tax`",
        "`db/etl_hmrc.py` `inheritance_tax`",
        "`db/etl_hmrc.py` `taxpayers`, `higher_rate_taxpayers`, `additional_rate_taxpayers`",
        "`db/etl_hmrc.py` `total_income`",
        "`db/etl_hmrc.py` `benefits.universal_credit.{recipients,expenditure}`",
        "`db/etl_hmrc.py` `benefits.child_benefit.{recipients,expenditure}`",
        "`db/etl_hmrc.py` `benefits.state_pension.{recipients,expenditure}`",
        "`db/etl_hmrc.py` `benefits.housing_benefit.{recipients,expenditure}`",
        "`db/etl_hmrc.py` `benefits.pension_credit.{recipients,expenditure}`",
    ]

    for entry in required_entries:
        assert entry in checklist

    assert "obr-efo-economy-march-2026" in checklist
    assert "obr-efo-aggregates-march-2026" in checklist
    assert "ons-families-households-2025" in checklist
    assert "2026-2034 remain gaps" in checklist
    assert "Explicit source gap or non-equivalence" in checklist
    assert "assertion" in checklist
    assert "period_type" in checklist
    assert "2023 through 2026" in checklist


def test_retired_uk_legacy_etl_modules_are_not_shipped():
    repo_root = Path(__file__).resolve().parents[1]

    assert not (repo_root / "db" / "etl_obr.py").exists()
    assert not (repo_root / "db" / "etl_ons.py").exists()
    assert not (repo_root / "tests" / "test_etl_obr.py").exists()
    assert not (repo_root / "tests" / "test_etl_ons.py").exists()
    assert not (repo_root / "db" / "etl_hmrc.py").exists()
    assert not (repo_root / "tests" / "test_etl_hmrc.py").exists()


def test_load_cli_no_longer_accepts_retired_uk_legacy_etl_sources():
    cli_source = (Path(__file__).resolve().parents[1] / "db" / "cli.py").read_text()

    assert 'if args.source == "obr"' not in cli_source
    assert 'if args.source == "ons"' not in cli_source
    assert 'if args.source == "hmrc"' not in cli_source
    assert "load_obr_targets" not in cli_source
    assert "load_ons_targets" not in cli_source
    assert "load_hmrc_targets" not in cli_source
    assert '"obr",' not in cli_source
    assert '"ons",' not in cli_source
    assert '"hmrc",' not in cli_source
