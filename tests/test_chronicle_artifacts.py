"""Tests for Chronicle source artifact acquisition and storage metadata."""

from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest
import yaml

from chronicle.cli import main as cli_main
from chronicle.artifacts import (
    AmbiguousManifestError,
    MalformedManifestError,
    RecordedR2LocatorError,
    SourceArtifactManifestError,
    SourceArtifactRevisionError,
    build_artifact_key,
    build_artifact_rows,
    build_derived_r2_key,
    bootstrap_r2_buckets,
    build_r2_key,
    fetch_source_artifact,
    infer_r2_country,
    infer_build_id,
    inventory_source_artifacts,
    publish_derived_artifacts,
    publish_source_artifacts,
)
from chronicle.epoch import Epoch
from chronicle.harness import main as harness_main


def test_build_r2_key_is_content_addressed():
    key = build_r2_key(
        source_id="irs_soi",
        package_id="soi-table-1-2",
        year=2023,
        sha256="abc123",
        filename="23in12ms.xls",
    )

    assert key == "raw/irs_soi/soi-table-1-2/2023/abc123/23in12ms.xls"


def test_build_derived_r2_key_is_build_scoped():
    key = build_derived_r2_key(
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        build_id="ledger.build.v1:abc123",
        artifact_name="reports/build_summary.json",
    )

    assert key == (
        "derived/irs_soi/soi-table-1-1/2023/"
        "ledger.build.v1:abc123/reports/build_summary.json"
    )


def test_build_artifact_key_hashes_one_payload_across_epochs():
    ledger = build_artifact_key(
        build_id="ledger.build.v1:abc123",
        artifact_name="reports/build_summary.json",
        sha256="def456",
    )
    chronicle = build_artifact_key(
        build_id="chronicle.build.v2:abc123",
        artifact_name="reports/build_summary.json",
        sha256="def456",
        epoch=Epoch.CHRONICLE,
    )

    assert ledger.startswith("ledger.build_artifact.v1:")
    assert chronicle.startswith("chronicle.build_artifact.v2:")
    assert ledger.split(":", maxsplit=1)[1] == chronicle.split(":", maxsplit=1)[1]


def test_build_artifact_key_rejects_unknown_build_epoch():
    with pytest.raises(
        ValueError,
        match=(
            "ledger[.]build[.]v1.*chronicle[.]build[.]v2|"
            "chronicle[.]build[.]v2.*ledger[.]build[.]v1"
        ),
    ):
        build_artifact_key(
            build_id="future.build.v9:abc123",
            artifact_name="facts.jsonl",
            sha256="def456",
        )


@pytest.mark.parametrize(
    ("source_id", "package_path", "expected_country"),
    [
        ("ird", "db/data/ird/wff", "nz"),
        ("ons", "db/data/ons/mye", "uk"),
        ("irs_soi", "db/data/irs_soi/table_1_1", None),
        ("irs_soi", "/work/ons/chronicle/db/data/irs_soi/table_1_1", None),
        ("ird", "/work/ons/chronicle/db/data/ird/wff", "nz"),
        ("ird", "/work/packages/ons/chronicle/db/data/ird/wff", "nz"),
        ("ird", "/work/ons/chronicle/packages/ird/wff", "nz"),
        ("ird", "/repo/db/data/ird/packages", "nz"),
        ("ird", "/repo/db/data/ird/packages/manifest.yaml", "nz"),
        ("ird", "/repo/packages/ird/packages/source_package.yaml", "nz"),
        ("irs_soi", "/repo/db/data/irs_soi/packages/manifest.yaml", None),
    ],
)
def test_infer_r2_country_uses_publisher_directory(
    source_id, package_path, expected_country
):
    assert (
        infer_r2_country(source_id=source_id, package_path=package_path)
        == expected_country
    )


def test_country_aware_r2_keys_preserve_legacy_us_layout():
    nz_key = build_r2_key(
        source_id="ird",
        package_id="ird-working-for-families-statistics-sept-2025",
        year=2024,
        sha256="abc123",
        filename="wff.xlsx",
    )
    uk_key = build_derived_r2_key(
        source_id="ons",
        package_id="ons-mye-2024-uk",
        year=2024,
        build_id="ledger.build.v1:abc123",
        artifact_name="facts.jsonl",
    )

    assert nz_key.startswith("raw/nz/ird/")
    assert uk_key.startswith("derived/uk/ons/")


def test_country_aware_r2_prefix_rejects_wrong_country():
    with pytest.raises(ValueError, match="disagrees with publisher country"):
        build_r2_key(
            source_id="ird",
            package_id="wff",
            year=2024,
            sha256="abc123",
            filename="wff.xlsx",
            prefix="raw/uk",
        )


def test_fetch_source_artifact_writes_manifest_and_inventory(tmp_path):
    source = tmp_path / "source.xls"
    content = b"chronicle artifact fixture"
    source.write_bytes(content)
    output_dir = tmp_path / "data" / "irs_soi" / "table_1_2"

    report = fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-2",
        year=2023,
        output_dir=output_dir,
        source_page="https://example.test/source-page",
        table="Publication 1304 Table 1.2",
    )

    expected_sha = hashlib.sha256(content).hexdigest()
    manifest = yaml.safe_load((output_dir / "manifest.yaml").read_text())
    inventory = inventory_source_artifacts(output_dir)

    assert report.valid
    assert report.sha256 == expected_sha
    assert (output_dir / "source.xls").read_bytes() == content
    assert manifest["source_id"] == "irs_soi"
    assert manifest["package_id"] == "soi-table-1-2"
    assert manifest["files"][2023]["sha256"] == expected_sha
    assert manifest["files"][2023]["source_url"] == str(source)
    assert inventory.valid
    assert inventory.counts == {
        "artifact_count": 1,
        "checksum_mismatch_count": 0,
        "manifest_count": 1,
        "missing_count": 0,
        "r2_link_count": 0,
    }


def test_fetch_rejects_wrong_country_before_reading_or_overwriting_cache(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.xlsx"
    source.write_bytes(b"original official artifact")
    output_dir = tmp_path / "db" / "data" / "ird" / "wff"
    fetch_source_artifact(
        str(source),
        source_id="ird",
        package_id="ird-wff",
        year=2024,
        output_dir=output_dir,
    )
    artifact_path = output_dir / source.name
    manifest_path = output_dir / "manifest.yaml"
    original_artifact = artifact_path.read_bytes()
    original_manifest = manifest_path.read_bytes()

    def unexpected_read(_source_url):
        raise AssertionError("A rejected route must not read the source artifact")

    monkeypatch.setattr("chronicle.artifacts._read_artifact", unexpected_read)
    with pytest.raises(ValueError, match="disagrees with publisher country"):
        fetch_source_artifact(
            str(source),
            source_id="ird",
            package_id="ird-wff",
            year=2024,
            output_dir=output_dir,
            r2_prefix="raw/uk",
        )

    assert artifact_path.read_bytes() == original_artifact
    assert manifest_path.read_bytes() == original_manifest


def test_publish_source_artifacts_uploads_manifest_entries(tmp_path):
    output_dir = tmp_path / "data" / "irs_soi" / "table_1_2"
    source = tmp_path / "source.xls"
    source.write_bytes(b"raw artifact")
    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-2",
        year=2023,
        output_dir=output_dir,
    )
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))
    manifest = yaml.safe_load((output_dir / "manifest.yaml").read_text())
    storage = manifest["files"][2023]["storage"]["r2"]

    assert report.valid
    assert report.counts == {
        "artifact_count": 1,
        "failed_count": 0,
        "manifest_count": 1,
        "r2_link_count": 1,
        "skipped_count": 0,
        "uploaded_count": 1,
    }
    assert storage["bucket"] == "ledger-raw"
    assert storage["key"].startswith("raw/irs_soi/soi-table-1-2/2023/")
    assert "ledger-raw/raw/irs_soi/soi-table-1-2/2023/" in log.read_text()


def test_publish_source_artifacts_handles_label_year_entries(tmp_path):
    output_dir = tmp_path / "data" / "ssa" / "ssi_monthly_statistics_2024_12"
    source = tmp_path / "table01.csv"
    source.write_bytes(b"csv artifact")
    fetch_source_artifact(
        str(source),
        source_id="ssa",
        package_id="ssa-ssi-monthly-statistics-2024-12",
        year=2024,
        output_dir=output_dir,
    )
    capture = output_dir / "table01.html"
    capture_bytes = b"<html>capture</html>"
    capture.write_bytes(capture_bytes)
    manifest_path = output_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["files"]["source_capture"] = {
        "filename": capture.name,
        "sha256": hashlib.sha256(capture_bytes).hexdigest(),
        "size_bytes": len(capture_bytes),
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))
    manifest = yaml.safe_load(manifest_path.read_text())
    storage = manifest["files"]["source_capture"]["storage"]["r2"]

    assert report.valid
    assert report.counts["uploaded_count"] == 2
    assert report.counts["failed_count"] == 0
    assert storage["key"] == (
        "raw/ssa/ssa-ssi-monthly-statistics-2024-12/source_capture/"
        f"{hashlib.sha256(capture_bytes).hexdigest()}/table01.html"
    )


def test_publish_source_artifacts_uses_country_for_each_manifest(tmp_path):
    data_root = tmp_path / "ons" / "chronicle" / "db" / "data"
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)
    for publisher, package_id, year in (
        ("ird", "ird-wff", 2024),
        ("ons", "ons-mye", 2024),
        ("irs_soi", "soi-table", 2023),
    ):
        output_dir = data_root / publisher / package_id
        source = tmp_path / f"{publisher}.csv"
        source.write_bytes(publisher.encode())
        fetch_source_artifact(
            str(source),
            source_id=publisher,
            package_id=package_id,
            year=year,
            output_dir=output_dir,
        )

    report = publish_source_artifacts(data_root, wrangler_command=str(wrangler))

    assert report.valid
    commands = log.read_text()
    assert "ledger-raw/raw/nz/ird/ird-wff/2024/" in commands
    assert "ledger-raw/raw/uk/ons/ons-mye/2024/" in commands
    assert "ledger-raw/raw/irs_soi/soi-table/2023/" in commands


def test_publish_source_artifacts_refuses_stale_country_key(tmp_path):
    output_dir = tmp_path / "data" / "ird" / "wff"
    source = tmp_path / "wff.xlsx"
    source.write_bytes(b"official WFF workbook")
    fetch_source_artifact(
        str(source),
        source_id="ird",
        package_id="ird-wff",
        year=2024,
        output_dir=output_dir,
    )
    manifest_path = output_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    artifact = manifest["files"][2024]
    artifact["storage"] = {
        "r2": {
            "provider": "r2",
            "bucket": "ledger-raw",
            "key": (
                f"raw/ird/ird-wff/2024/{artifact['sha256']}/{artifact['filename']}"
            ),
        }
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))

    assert not report.valid
    assert report.entries[0].upload is None
    assert (
        report.entries[0]
        .errors[0]
        .startswith("recorded_r2_key_disagrees_with_country_prefix:")
    )
    assert not log.exists()


def test_publish_source_artifacts_accepts_package_named_packages(tmp_path):
    output_dir = tmp_path / "db" / "data" / "ird" / "packages"
    source = tmp_path / "wff.xlsx"
    source.write_bytes(b"official WFF workbook")
    fetched = fetch_source_artifact(
        str(source),
        source_id="ird",
        package_id="packages",
        year=2024,
        output_dir=output_dir,
    )
    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\necho ok\n")
    wrangler.chmod(0o755)

    published = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))

    assert fetched.valid
    assert published.valid
    assert published.counts["uploaded_count"] == 1
    manifest = yaml.safe_load((output_dir / "manifest.yaml").read_text())
    assert manifest["files"][2024]["storage"]["r2"]["key"].startswith(
        "raw/nz/ird/packages/2024/"
    )


def test_inventory_source_artifacts_catches_checksum_mismatch(tmp_path):
    source = tmp_path / "source.xls"
    source.write_bytes(b"original")
    output_dir = tmp_path / "data"
    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-2",
        year=2023,
        output_dir=output_dir,
    )
    (output_dir / "source.xls").write_bytes(b"changed")

    report = inventory_source_artifacts(output_dir)

    assert not report.valid
    assert report.counts["checksum_mismatch_count"] == 1
    assert report.entries[0].errors == ("checksum_mismatch",)


def test_artifact_cli_commands_emit_json(tmp_path, capsys):
    source = tmp_path / "source.xls"
    source.write_bytes(b"cli artifact")
    output_dir = tmp_path / "artifact-dir"

    exit_code = harness_main(
        [
            "fetch-artifact",
            "--url",
            str(source),
            "--source-id",
            "irs_soi",
            "--package-id",
            "soi-table-cli",
            "--year",
            "2023",
            "--out-dir",
            str(output_dir),
        ]
    )
    fetch_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert fetch_payload["valid"]
    assert (output_dir / "manifest.yaml").exists()

    exit_code = harness_main(
        [
            "inventory-artifacts",
            "--root",
            str(output_dir),
        ]
    )
    inventory_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert inventory_payload["valid"]
    assert inventory_payload["counts"]["artifact_count"] == 1

    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\necho ok\n")
    wrangler.chmod(0o755)
    exit_code = harness_main(
        [
            "publish-raw",
            "--root",
            str(output_dir),
            "--wrangler-command",
            str(wrangler),
        ]
    )
    raw_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert raw_payload["valid"]
    assert raw_payload["counts"]["uploaded_count"] == 1


def test_bootstrap_r2_reports_missing_authentication(tmp_path):
    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\necho 'You are not authenticated.'\n")
    wrangler.chmod(0o755)

    report = bootstrap_r2_buckets(wrangler_command=str(wrangler))

    assert not report.valid
    assert not report.authenticated
    assert "wrangler_not_authenticated" in report.errors[0]


def test_publish_derived_artifacts_uploads_build_directory(tmp_path):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    build_id = "ledger.build.v1:test123"
    (reports / "database.json").write_text(json.dumps({"build_id": build_id}))
    (reports / "build_summary.json").write_text(
        json.dumps({"reports": {"database": {"build_id": build_id}}})
    )
    (suite / "facts.jsonl").write_text("{}\n")
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_derived_artifacts(
        suite,
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        build_artifacts_output=tmp_path / "build_artifacts.jsonl",
        wrangler_command=str(wrangler),
    )

    uploaded_names = {entry.artifact_name for entry in report.entries}
    command_log = log.read_text()
    build_artifact_rows = [
        json.loads(line)
        for line in (tmp_path / "build_artifacts.jsonl").read_text().splitlines()
    ]

    assert report.valid
    assert infer_build_id(suite) == build_id
    assert report.build_id == build_id
    assert report.build_artifacts_path == str(tmp_path / "build_artifacts.jsonl")
    assert uploaded_names == {
        "reports/build_summary.json",
        "reports/database.json",
        "facts.jsonl",
    }
    assert len(build_artifact_rows) == 3
    assert build_artifact_rows[0]["build_id"] == build_id
    assert build_artifact_rows[0]["r2_bucket"] == "ledger-derived"
    assert "ledger-derived/derived/irs_soi/soi-table-1-1/2023/" in command_log
    assert "reports/build_summary.json" in command_log


@pytest.mark.parametrize("write_build_artifacts", [False, True])
def test_publish_derived_artifacts_rejects_unknown_build_before_side_effects(
    tmp_path,
    write_build_artifacts,
):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    (reports / "database.json").write_text(
        json.dumps({"build_id": "future.build.v9:invalid"})
    )
    (suite / "facts.jsonl").write_text("{}\n")
    upload_log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {upload_log}\necho ok\n")
    wrangler.chmod(0o755)
    build_artifacts_path = tmp_path / "build_artifacts.jsonl"
    build_artifacts_path.write_text("sentinel\n")

    report = publish_derived_artifacts(
        suite,
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        build_artifacts_output=(
            build_artifacts_path if write_build_artifacts else None
        ),
        wrangler_command=str(wrangler),
    )

    assert report.errors == ("malformed_build_id",)
    assert report.entries == ()
    assert not upload_log.exists()
    assert build_artifacts_path.read_text() == "sentinel\n"


def test_build_artifact_rows_skips_failed_uploads(tmp_path):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    (reports / "database.json").write_text(
        json.dumps({"build_id": "ledger.build.v1:failed-row"})
    )
    (suite / "facts.jsonl").write_text("{}\n")
    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\nexit 1\n")
    wrangler.chmod(0o755)

    report = publish_derived_artifacts(
        suite,
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        wrangler_command=str(wrangler),
    )

    assert not report.valid
    assert build_artifact_rows(report) == ()


def test_publish_derived_cli_emits_json(tmp_path, capsys):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    (reports / "database.json").write_text(
        json.dumps({"build_id": "ledger.build.v1:cli"})
    )
    (suite / "ledger.db").write_bytes(b"db")
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    exit_code = harness_main(
        [
            "publish-derived",
            "--dir",
            str(suite),
            "--source-id",
            "irs_soi",
            "--package-id",
            "soi-table-1-1",
            "--year",
            "2023",
            "--wrangler-command",
            str(wrangler),
            "--build-artifacts-out",
            str(tmp_path / "build_artifacts.jsonl"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["valid"]
    assert payload["build_id"] == "ledger.build.v1:cli"
    assert payload["counts"]["artifact_count"] == 2
    assert (tmp_path / "build_artifacts.jsonl").exists()


def test_top_level_cli_dispatches_publish_derived(tmp_path, capsys, monkeypatch):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    (reports / "database.json").write_text(
        json.dumps({"build_id": "ledger.build.v1:top-cli"})
    )
    (suite / "facts.jsonl").write_text("{}\n")
    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\necho ok\n")
    wrangler.chmod(0o755)
    monkeypatch.setattr(
        "sys.argv",
        [
            "chronicle",
            "publish-derived",
            "--dir",
            str(suite),
            "--source-id",
            "irs_soi",
            "--package-id",
            "soi-table-1-1",
            "--year",
            "2023",
            "--wrangler-command",
            str(wrangler),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli_main()
    payload = json.loads(capsys.readouterr().out)

    assert exc.value.code == 0
    assert payload["valid"]


def _sqlite_build(path, build_id):
    """Write a minimal build database carrying one ledger_builds row."""
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE ledger_builds (build_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO ledger_builds VALUES (?)", (build_id,))


@pytest.mark.parametrize("db_name", ["chronicle.db", "ledger.db"])
def test_infer_build_id_reads_new_and_legacy_database_names(tmp_path, db_name):
    suite = tmp_path / "suite"
    suite.mkdir()
    _sqlite_build(suite / db_name, "ledger.build.v1:from-db")

    assert infer_build_id(suite) == "ledger.build.v1:from-db"


def test_infer_build_id_prefers_the_chronicle_database(tmp_path):
    suite = tmp_path / "suite"
    suite.mkdir()
    _sqlite_build(suite / "chronicle.db", "ledger.build.v1:chronicle")
    _sqlite_build(suite / "ledger.db", "ledger.build.v1:legacy")

    assert infer_build_id(suite) == "ledger.build.v1:chronicle"


@pytest.mark.parametrize("db_name", ["chronicle.db", "ledger.db"])
def test_publish_derived_classifies_both_database_names(tmp_path, db_name):
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    build_id = "ledger.build.v1:kind"
    (reports / "database.json").write_text(json.dumps({"build_id": build_id}))
    (suite / db_name).write_bytes(b"db")
    wrangler = tmp_path / "wrangler"
    wrangler.write_text("#!/bin/sh\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_derived_artifacts(
        suite,
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        wrangler_command=str(wrangler),
    )
    rows = {row["artifact_name"]: row for row in build_artifact_rows(report)}

    assert rows[db_name]["artifact_kind"] == "sqlite_database"


def test_publish_derived_uses_the_configured_bucket(tmp_path, monkeypatch):
    monkeypatch.setenv("CHRONICLE_R2_DERIVED_BUCKET", "chronicle-derived")
    suite = tmp_path / "suite"
    reports = suite / "reports"
    reports.mkdir(parents=True)
    (reports / "database.json").write_text(
        json.dumps({"build_id": "ledger.build.v1:bucket"})
    )
    (suite / "facts.jsonl").write_text("{}\n")
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    report = publish_derived_artifacts(
        suite,
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        wrangler_command=str(wrangler),
    )

    assert report.valid
    assert report.entries[0].r2_location.bucket == "chronicle-derived"
    assert "chronicle-derived/derived/irs_soi/" in log.read_text()


def test_publish_raw_skips_an_object_already_held_by_a_preserved_bucket(
    tmp_path, monkeypatch
):
    """A recorded storage.r2 bucket is preserved history, not a publish target.

    Archived witness records pin raw R2 URLs by hash, so backfilling the same
    bytes into a renamed bucket must not rewrite the manifest. The entry is
    already published, so the sweep reports it skipped and stays green: after
    the bucket-default flip every entry published before it takes this path.
    """
    monkeypatch.setenv("CHRONICLE_R2_RAW_BUCKET", "chronicle-raw")
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-1-1"
    source = tmp_path / "soi.xlsx"
    source.write_bytes(b"official SOI workbook")
    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        output_dir=output_dir,
    )
    manifest_path = output_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    artifact = manifest["files"][2023]
    recorded_key = (
        f"raw/irs_soi/soi-table-1-1/2023/{artifact['sha256']}/{artifact['filename']}"
    )
    artifact["storage"] = {
        "r2": {
            "provider": "r2",
            "bucket": "ledger-raw",
            "key": recorded_key,
            "uri": f"r2://ledger-raw/{recorded_key}",
        }
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)

    before = manifest_path.read_bytes()
    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))
    entry = report.entries[0]

    assert report.valid
    assert entry.errors == ()
    assert entry.upload is None
    assert entry.skipped == (
        "recorded_r2_bucket_is_preserved_history:"
        "recorded=ledger-raw:requested=chronicle-raw"
    )
    assert entry.r2_location is not None
    assert entry.r2_location.bucket == "ledger-raw"
    assert entry.r2_location.key == recorded_key
    assert entry.to_dict()["skipped"] == entry.skipped
    assert report.counts["skipped_count"] == 1
    assert report.counts["uploaded_count"] == 0
    assert report.counts["failed_count"] == 0
    assert not log.exists()
    assert manifest_path.read_bytes() == before


def test_fetch_artifact_keeps_an_already_recorded_bucket(tmp_path, monkeypatch):
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-1-1"
    source = tmp_path / "soi.xlsx"
    source.write_bytes(b"official SOI workbook")
    log = tmp_path / "wrangler.log"
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)
    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        output_dir=output_dir,
        upload_r2=True,
        wrangler_command=str(wrangler),
    )
    manifest_path = output_dir / "manifest.yaml"
    first = yaml.safe_load(manifest_path.read_text())
    assert first["files"][2023]["storage"]["r2"]["bucket"] == "ledger-raw"

    monkeypatch.setenv("CHRONICLE_R2_RAW_BUCKET", "chronicle-raw")
    report = fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table-1-1",
        year=2023,
        output_dir=output_dir,
        upload_r2=True,
        wrangler_command=str(wrangler),
    )
    second = yaml.safe_load(manifest_path.read_text())

    # The backfill copy really is uploaded to the new bucket, but the manifest
    # keeps recording where the bytes were first published.
    assert report.r2_location.bucket == "chronicle-raw"
    assert "chronicle-raw" in log.read_text()
    assert (
        second["files"][2023]["storage"]["r2"] == first["files"][2023]["storage"]["r2"]
    )


# ---------------------------------------------------------------------------
# Publisher revisions
#
# A raw R2 key is content-addressed, so a recorded storage.r2 block is a claim
# about specific bytes. On 2026-09-02 the IRS re-published 22in05ira.xlsx and
# 22in06ira.xlsx under their existing URLs (PolicyEngine/chronicle#225): a
# repeated fetch must never pair those new bytes with the old object's URI.
# ---------------------------------------------------------------------------

REPUBLISHED_URL = "https://www.irs.gov/pub/irs-soi/22in05ira.xlsx"
REPUBLISHED_FILENAME = "22in05ira.xlsx"
FIRST_PUBLICATION = b"IRA table 5, first publication"
SECOND_PUBLICATION = b"IRA table 5, silently re-published with revised rows"


def _wrangler_stub(tmp_path, log):
    wrangler = tmp_path / "wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\necho ok\n")
    wrangler.chmod(0o755)
    return wrangler


def _serve(monkeypatch, content):
    """Serve ``content`` from the publisher URL, without touching the network."""

    def _fake_read_artifact(source_url):
        assert source_url == REPUBLISHED_URL
        return content, REPUBLISHED_FILENAME

    monkeypatch.setattr("chronicle.artifacts._read_artifact", _fake_read_artifact)


def _fetch_republished(output_dir, wrangler, *, upload_r2=True, **kwargs):
    return fetch_source_artifact(
        REPUBLISHED_URL,
        source_id="irs_soi",
        package_id="soi-table-5",
        year=2022,
        output_dir=output_dir,
        upload_r2=upload_r2,
        wrangler_command=str(wrangler),
        **kwargs,
    )


def test_repeated_fetch_of_identical_bytes_preserves_the_recorded_block(
    tmp_path, monkeypatch
):
    """Same bytes: the recorded block survives whatever bucket is configured."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    _fetch_republished(output_dir, wrangler)
    first = yaml.safe_load(manifest_path.read_text())["files"][2022]

    monkeypatch.setenv("CHRONICLE_R2_RAW_BUCKET", "chronicle-raw")
    report = _fetch_republished(output_dir, wrangler)
    second = yaml.safe_load(manifest_path.read_text())["files"][2022]

    assert report.valid
    # The backfill copy really goes to the renamed bucket, but the manifest
    # keeps recording where these bytes were first published.
    assert report.r2_location.bucket == "chronicle-raw"
    assert "chronicle-raw" in log.read_text()
    assert second["storage"] == first["storage"]
    # Field order too, so the block is byte-for-byte identical once dumped.
    assert list(second["storage"]["r2"].items()) == list(first["storage"]["r2"].items())
    assert second["storage"]["r2"]["bucket"] == "ledger-raw"
    assert "previous_r2" not in second["storage"]
    assert second["sha256"] == first["sha256"]


@pytest.mark.parametrize(
    ("upload_r2", "configured_bucket"),
    [
        pytest.param(True, None, id="reuploaded"),
        # The two routes that reached a manifest in the wild: a fetch that only
        # registers the bytes, and a fetch once the bucket default has moved.
        # Both preserved the recorded block while rewriting sha256/size_bytes.
        pytest.param(False, None, id="registered-without-upload"),
        pytest.param(True, "chronicle-raw", id="after-the-bucket-rename"),
    ],
)
def test_repeated_fetch_of_different_bytes_is_refused(
    tmp_path, monkeypatch, upload_r2, configured_bucket
):
    """A publisher revision must not inherit the recorded object's provenance."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    artifact_path = output_dir / REPUBLISHED_FILENAME
    _serve(monkeypatch, FIRST_PUBLICATION)
    first_report = _fetch_republished(output_dir, wrangler)
    manifest_before = manifest_path.read_bytes()
    uploads_before = log.read_text()

    if configured_bucket:
        monkeypatch.setenv("CHRONICLE_R2_RAW_BUCKET", configured_bucket)
    _serve(monkeypatch, SECOND_PUBLICATION)
    with pytest.raises(SourceArtifactRevisionError) as raised:
        _fetch_republished(output_dir, wrangler, upload_r2=upload_r2)

    message = str(raised.value)
    assert first_report.sha256 in message
    assert hashlib.sha256(SECOND_PUBLICATION).hexdigest() in message
    assert f"size_bytes={len(FIRST_PUBLICATION)}" in message
    assert f"size_bytes={len(SECOND_PUBLICATION)}" in message
    assert "release revision" in message
    assert "--record-revision" in message
    # Nothing was overwritten, copied or uploaded on the way to the refusal.
    assert manifest_path.read_bytes() == manifest_before
    assert artifact_path.read_bytes() == FIRST_PUBLICATION
    assert log.read_text() == uploads_before


def test_record_revision_writes_a_new_key_and_keeps_the_previous_object(
    tmp_path, monkeypatch
):
    """The opt-in records the new bytes' own key under the configured bucket."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    first_report = _fetch_republished(output_dir, wrangler)
    superseded = yaml.safe_load(manifest_path.read_text())["files"][2022]

    monkeypatch.setenv("CHRONICLE_R2_RAW_BUCKET", "chronicle-raw")
    _serve(monkeypatch, SECOND_PUBLICATION)
    report = _fetch_republished(output_dir, wrangler, record_revision=True)
    revised = yaml.safe_load(manifest_path.read_text())["files"][2022]
    revised_sha256 = hashlib.sha256(SECOND_PUBLICATION).hexdigest()

    assert report.valid
    # storage.r2 names the object that holds the entry's current bytes...
    assert revised["sha256"] == revised_sha256
    assert revised["size_bytes"] == len(SECOND_PUBLICATION)
    assert revised["storage"]["r2"]["bucket"] == "chronicle-raw"
    assert revised["storage"]["r2"]["key"] == (
        f"raw/irs_soi/soi-table-5/2022/{revised_sha256}/{REPUBLISHED_FILENAME}"
    )
    assert revised["storage"]["r2"]["uri"] == (
        f"r2://chronicle-raw/{revised['storage']['r2']['key']}"
    )
    # ...and never the superseded key, which stays addressable as history.
    previous = revised["storage"]["previous_r2"]
    assert [entry["uri"] for entry in previous] == [superseded["storage"]["r2"]["uri"]]
    assert previous[0]["bucket"] == "ledger-raw"
    assert previous[0]["sha256"] == first_report.sha256
    assert previous[0]["size_bytes"] == len(FIRST_PUBLICATION)
    assert previous[0]["fetched_at"] == superseded["fetched_at"]
    assert previous[0]["superseded_at"] == revised["fetched_at"]
    assert (output_dir / REPUBLISHED_FILENAME).read_bytes() == SECOND_PUBLICATION
    assert f"chronicle-raw/{revised['storage']['r2']['key']}" in log.read_text()


def test_a_revised_manifest_still_reads_as_one_r2_linked_artifact(
    tmp_path, monkeypatch
):
    """storage.previous_r2 is a sibling key, so every storage.r2 reader is intact."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    wrangler = _wrangler_stub(tmp_path, tmp_path / "wrangler.log")
    _serve(monkeypatch, FIRST_PUBLICATION)
    _fetch_republished(output_dir, wrangler)
    _serve(monkeypatch, SECOND_PUBLICATION)
    _fetch_republished(output_dir, wrangler, record_revision=True)

    inventory = inventory_source_artifacts(output_dir)

    assert inventory.valid
    assert inventory.counts["r2_link_count"] == 1
    assert inventory.counts["checksum_mismatch_count"] == 0
    assert inventory.entries[0].r2["bucket"] == "ledger-raw"
    assert inventory.entries[0].sha256_actual == (
        hashlib.sha256(SECOND_PUBLICATION).hexdigest()
    )


def test_publish_raw_refuses_a_file_the_recorded_object_does_not_hold(
    tmp_path, monkeypatch
):
    """Recorded sha256 != local sha256 is a revision, not a backfill."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    first_report = _fetch_republished(output_dir, wrangler)

    # Reproduce the state a pre-fix fetch left behind: new bytes on disk, the
    # entry's own hash rewritten, the recorded key still addressing the old
    # bytes.
    revised_sha256 = hashlib.sha256(SECOND_PUBLICATION).hexdigest()
    (output_dir / REPUBLISHED_FILENAME).write_bytes(SECOND_PUBLICATION)
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["files"][2022]["sha256"] = revised_sha256
    manifest["files"][2022]["size_bytes"] = len(SECOND_PUBLICATION)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    manifest_before = manifest_path.read_bytes()
    uploads_before = log.read_text()

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))

    assert not report.valid
    assert report.entries[0].upload is None
    assert report.entries[0].r2_location is None
    assert report.entries[0].errors == (
        "recorded_r2_identity_mismatch:"
        f"recorded_sha256={first_report.sha256}:"
        f"recorded_filename={REPUBLISHED_FILENAME}:"
        f"local_sha256={revised_sha256}:"
        f"local_filename={REPUBLISHED_FILENAME}",
    )
    assert log.read_text() == uploads_before
    assert manifest_path.read_bytes() == manifest_before


def test_publish_raw_uploads_a_registered_revision_and_keeps_its_history(
    tmp_path, monkeypatch
):
    """Once the revision is registered, publishing it is ordinary work."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    first_report = _fetch_republished(output_dir, wrangler)
    _serve(monkeypatch, SECOND_PUBLICATION)
    _fetch_republished(output_dir, wrangler, record_revision=True)
    revised_sha256 = hashlib.sha256(SECOND_PUBLICATION).hexdigest()

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))
    published = yaml.safe_load(manifest_path.read_text())["files"][2022]

    assert report.valid
    assert published["storage"]["r2"]["key"].endswith(
        f"/{revised_sha256}/{REPUBLISHED_FILENAME}"
    )
    assert [entry["sha256"] for entry in published["storage"]["previous_r2"]] == [
        first_report.sha256
    ]


def test_fetch_artifact_cli_refuses_a_revision_then_records_it_on_request(
    tmp_path, monkeypatch, capsys
):
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    wrangler = _wrangler_stub(tmp_path, tmp_path / "wrangler.log")
    argv = [
        "fetch-artifact",
        "--url",
        REPUBLISHED_URL,
        "--source-id",
        "irs_soi",
        "--package-id",
        "soi-table-5",
        "--year",
        "2022",
        "--out-dir",
        str(output_dir),
        "--upload-r2",
        "--wrangler-command",
        str(wrangler),
    ]
    _serve(monkeypatch, FIRST_PUBLICATION)
    assert harness_main(argv) == 0
    capsys.readouterr()

    _serve(monkeypatch, SECOND_PUBLICATION)
    refused = harness_main(argv)
    refusal = capsys.readouterr()

    assert refused == 1
    assert "--record-revision" in refusal.err
    assert refusal.out == ""

    assert harness_main([*argv, "--record-revision"]) == 0
    recorded = json.loads(capsys.readouterr().out)

    assert recorded["sha256"] == hashlib.sha256(SECOND_PUBLICATION).hexdigest()
    assert recorded["r2_location"]["key"].endswith(
        f"/{recorded['sha256']}/{REPUBLISHED_FILENAME}"
    )


def test_record_revision_without_an_upload_records_no_current_object(
    tmp_path, monkeypatch
):
    """An offline revision keeps history without claiming the new bytes exist.

    Registering a revision without ``--upload-r2`` leaves the entry with no
    ``storage.r2`` at all rather than a pointer to bytes R2 does not hold. The
    superseded object stays addressable, and a later publish-raw completes the
    registration.
    """
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    first_report = _fetch_republished(output_dir, wrangler)

    _serve(monkeypatch, SECOND_PUBLICATION)
    _fetch_republished(output_dir, wrangler, upload_r2=False, record_revision=True)
    registered = yaml.safe_load(manifest_path.read_text())["files"][2022]

    assert "r2" not in registered["storage"]
    assert [entry["sha256"] for entry in registered["storage"]["previous_r2"]] == [
        first_report.sha256
    ]

    report = publish_source_artifacts(output_dir, wrangler_command=str(wrangler))
    published = yaml.safe_load(manifest_path.read_text())["files"][2022]
    revised_sha256 = hashlib.sha256(SECOND_PUBLICATION).hexdigest()

    assert report.valid
    assert published["storage"]["r2"]["key"].endswith(
        f"/{revised_sha256}/{REPUBLISHED_FILENAME}"
    )
    assert [entry["sha256"] for entry in published["storage"]["previous_r2"]] == [
        first_report.sha256
    ]


def test_a_recorded_block_that_only_carries_a_uri_is_still_recognized(
    tmp_path, monkeypatch
):
    """Identity reads the URI when a hand-written block records no key."""
    output_dir = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    wrangler = _wrangler_stub(tmp_path, tmp_path / "wrangler.log")
    manifest_path = output_dir / "manifest.yaml"
    _serve(monkeypatch, FIRST_PUBLICATION)
    _fetch_republished(output_dir, wrangler)
    manifest = yaml.safe_load(manifest_path.read_text())
    recorded = manifest["files"][2022]["storage"]["r2"]
    manifest["files"][2022]["storage"]["r2"] = {
        "provider": recorded["provider"],
        "bucket": recorded["bucket"],
        "uri": recorded["uri"],
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    uri_only = manifest["files"][2022]["storage"]["r2"]

    report = _fetch_republished(output_dir, wrangler)
    preserved = yaml.safe_load(manifest_path.read_text())["files"][2022]

    assert report.valid
    assert preserved["storage"]["r2"] == uri_only

    _serve(monkeypatch, SECOND_PUBLICATION)
    with pytest.raises(SourceArtifactRevisionError):
        _fetch_republished(output_dir, wrangler)


# ---------------------------------------------------------------------------
# Manifest addressing, entry identity, and recorded locators
#
# Everything below concerns the state a fetch reads before it writes: which
# manifest it reads, what that manifest's entry says its vintage holds, and
# whether the recorded R2 block names one object or two.
# ---------------------------------------------------------------------------

TRADITIONAL_MANIFEST = "manifest_traditional_source_package.yaml"
ROTH_MANIFEST = "manifest_roth_source_package.yaml"


def _publish(tmp_path, name, content):
    """Write bytes a fetch can read as a local publisher path."""
    path = tmp_path / "publisher" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _fetch_local(output_dir, source_path, *, package_id="soi-table-5", **kwargs):
    return fetch_source_artifact(
        str(source_path),
        source_id="irs_soi",
        package_id=package_id,
        year=2022,
        output_dir=output_dir,
        **kwargs,
    )


def _entry(manifest_path):
    return yaml.safe_load(manifest_path.read_text())["files"][2022]


def test_fetch_artifact_writes_the_manifest_it_was_given(tmp_path):
    """One publisher directory, two source packages, two manifests.

    db/data/irs_soi/ira_contributions keeps the traditional and Roth IRA
    packages side by side. A fetch that always wrote manifest.yaml would write
    a third manifest neither package reads.
    """
    package = tmp_path / "db" / "data" / "irs_soi" / "ira_contributions"
    traditional = _publish(tmp_path, "22in05ira.xlsx", b"traditional IRA table")
    roth = _publish(tmp_path, "22in06ira.xlsx", b"roth IRA table")

    _fetch_local(
        package,
        traditional,
        package_id="soi-ira-traditional-contributions-2022",
        manifest_filename=TRADITIONAL_MANIFEST,
    )
    _fetch_local(
        package,
        roth,
        package_id="soi-ira-roth-contributions-2022",
        manifest_filename=ROTH_MANIFEST,
    )

    assert sorted(path.name for path in package.glob("manifest*.yaml")) == [
        ROTH_MANIFEST,
        TRADITIONAL_MANIFEST,
    ]
    assert not (package / "manifest.yaml").exists()
    assert _entry(package / TRADITIONAL_MANIFEST)["filename"] == "22in05ira.xlsx"
    assert _entry(package / ROTH_MANIFEST)["filename"] == "22in06ira.xlsx"
    assert _entry(package / TRADITIONAL_MANIFEST)["sha256"] == (
        hashlib.sha256(b"traditional IRA table").hexdigest()
    )


def test_a_revision_is_refused_in_the_manifest_that_records_it(tmp_path):
    """The IRA revision workflow the docs cite, on a two-manifest package."""
    package = tmp_path / "db" / "data" / "irs_soi" / "ira_contributions"
    traditional = _publish(tmp_path, "22in05ira.xlsx", b"traditional IRA table")
    _fetch_local(
        package,
        traditional,
        package_id="soi-ira-traditional-contributions-2022",
        manifest_filename=TRADITIONAL_MANIFEST,
    )
    recorded = (package / TRADITIONAL_MANIFEST).read_bytes()

    # The IRS re-publishes under the same URL and vintage.
    traditional.write_bytes(b"traditional IRA table, revised rows")

    with pytest.raises(SourceArtifactRevisionError) as raised:
        _fetch_local(
            package,
            traditional,
            package_id="soi-ira-traditional-contributions-2022",
            manifest_filename=TRADITIONAL_MANIFEST,
        )

    assert TRADITIONAL_MANIFEST in str(raised.value)
    assert (package / TRADITIONAL_MANIFEST).read_bytes() == recorded
    assert (package / "22in05ira.xlsx").read_bytes() == b"traditional IRA table"

    # Without the flag the same fetch would address a manifest.yaml that no
    # package reads and that protects nothing: the #225 path. It is refused,
    # naming the manifests the directory keeps, and nothing is written.
    with pytest.raises(AmbiguousManifestError) as stray:
        _fetch_local(
            package,
            traditional,
            package_id="soi-ira-traditional-contributions-2022",
        )

    assert TRADITIONAL_MANIFEST in str(stray.value)
    assert "--manifest" in str(stray.value)
    assert not (package / "manifest.yaml").exists()
    assert (package / TRADITIONAL_MANIFEST).read_bytes() == recorded
    assert (package / "22in05ira.xlsx").read_bytes() == b"traditional IRA table"


def test_fetch_artifact_cli_refuses_a_stray_default_manifest(tmp_path, capsys):
    package = tmp_path / "db" / "data" / "irs_soi" / "ira_contributions"
    traditional = _publish(tmp_path, "22in05ira.xlsx", b"traditional IRA table")
    _fetch_local(
        package,
        traditional,
        package_id="soi-ira-traditional-contributions-2022",
        manifest_filename=TRADITIONAL_MANIFEST,
    )
    argv = [
        "fetch-artifact",
        "--url",
        str(traditional),
        "--source-id",
        "irs_soi",
        "--package-id",
        "soi-ira-traditional-contributions-2022",
        "--year",
        "2022",
        "--out-dir",
        str(package),
    ]

    assert harness_main(argv) == 1

    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert TRADITIONAL_MANIFEST in err
    assert not (package / "manifest.yaml").exists()


def test_a_same_bytes_rename_is_refused_by_name_not_as_a_revision(tmp_path):
    """Identical bytes under another filename are neither a revision nor a
    re-fetch: the entry's filename must keep agreeing with its recorded key."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    source = _publish(tmp_path, "22in05ira.xlsx", b"IRA table 5")
    _fetch_local(package, source, filename="table-5.xlsx", upload_r2=False)
    recorded = (package / "manifest.yaml").read_bytes()

    for record_revision in (False, True):
        with pytest.raises(SourceArtifactRevisionError) as raised:
            _fetch_local(
                package, source, upload_r2=False, record_revision=record_revision
            )
        message = str(raised.value)
        assert "rename is not a release revision" in message
        assert "filename=table-5.xlsx" in message
        assert "names them 22in05ira.xlsx" in message
        assert "--filename table-5.xlsx" in message

    assert (package / "manifest.yaml").read_bytes() == recorded
    assert not (package / "22in05ira.xlsx").exists()
    assert (package / "table-5.xlsx").read_bytes() == b"IRA table 5"


@pytest.mark.parametrize(
    "manifest_filename",
    ["../manifest.yaml", "nested/manifest.yaml", "", "   ", ".", ".."],
)
def test_a_manifest_name_must_stay_inside_the_package(tmp_path, manifest_filename):
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    source = _publish(tmp_path, "table.xlsx", b"table")

    with pytest.raises(ValueError, match="inside the package directory"):
        _fetch_local(package, source, manifest_filename=manifest_filename)

    assert not package.exists()


def test_fetch_artifact_cli_reports_a_manifest_name_outside_the_package(
    tmp_path, capsys
):
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    source = _publish(tmp_path, "table.xlsx", b"table")
    argv = [
        "fetch-artifact",
        "--url",
        str(source),
        "--source-id",
        "irs_soi",
        "--package-id",
        "soi-table-5",
        "--year",
        "2022",
        "--out-dir",
        str(package),
        "--manifest",
        "../manifest.yaml",
    ]

    assert harness_main(argv) == 1

    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert "inside the package directory" in err
    assert not package.exists()
    assert not (tmp_path / "db" / "data" / "irs_soi" / "manifest.yaml").exists()


def test_fetch_artifact_cli_targets_the_named_manifest(tmp_path, capsys):
    package = tmp_path / "db" / "data" / "irs_soi" / "ira_contributions"
    traditional = _publish(tmp_path, "22in05ira.xlsx", b"traditional IRA table")
    argv = [
        "fetch-artifact",
        "--url",
        str(traditional),
        "--source-id",
        "irs_soi",
        "--package-id",
        "soi-ira-traditional-contributions-2022",
        "--year",
        "2022",
        "--out-dir",
        str(package),
        "--manifest",
        TRADITIONAL_MANIFEST,
    ]

    assert harness_main(argv) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["manifest_path"].endswith(TRADITIONAL_MANIFEST)
    assert not (package / "manifest.yaml").exists()

    traditional.write_bytes(b"traditional IRA table, revised rows")

    assert harness_main(argv) == 1
    assert TRADITIONAL_MANIFEST in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Identity without a recorded R2 object
# ---------------------------------------------------------------------------


def _failing_wrangler(tmp_path, log):
    wrangler = tmp_path / "failing-wrangler"
    wrangler.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\nexit 1\n")
    wrangler.chmod(0o755)
    return wrangler


def test_a_registered_entry_is_protected_before_it_is_ever_published(tmp_path):
    """No storage.r2 yet is not no identity: the entry declares its bytes."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    source = _publish(tmp_path, "22in05ira.xlsx", b"IRA table 5, first publication")
    first = _fetch_local(package, source, upload_r2=False)
    recorded = (package / "manifest.yaml").read_bytes()

    assert "storage" not in _entry(package / "manifest.yaml")

    # Same bytes: an ordinary repeated fetch, not a revision.
    assert _fetch_local(package, source, upload_r2=False).sha256 == first.sha256

    source.write_bytes(b"IRA table 5, silently re-published")
    with pytest.raises(SourceArtifactRevisionError) as raised:
        _fetch_local(package, source, upload_r2=False)

    message = str(raised.value)
    assert first.sha256 in message
    assert hashlib.sha256(b"IRA table 5, silently re-published").hexdigest() in message
    assert "size_bytes=30" in message
    assert "--record-revision" in message
    assert (package / "manifest.yaml").read_bytes() == recorded
    assert (package / "22in05ira.xlsx").read_bytes() == (
        b"IRA table 5, first publication"
    )


def test_a_failed_upload_does_not_disable_revision_protection(tmp_path):
    """The state #225 hit: bytes registered, upload failed, no storage.r2."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    log = tmp_path / "wrangler.log"
    wrangler = _failing_wrangler(tmp_path, log)
    source = _publish(tmp_path, "22in05ira.xlsx", b"IRA table 5, first publication")

    report = _fetch_local(
        package, source, upload_r2=True, wrangler_command=str(wrangler)
    )
    recorded = (package / "manifest.yaml").read_bytes()

    assert report.errors == ("r2_upload_failed",)
    assert "storage" not in _entry(package / "manifest.yaml")

    source.write_bytes(b"IRA table 5, silently re-published")
    with pytest.raises(SourceArtifactRevisionError):
        _fetch_local(package, source, upload_r2=True, wrangler_command=str(wrangler))

    assert (package / "manifest.yaml").read_bytes() == recorded


def test_record_revision_over_an_unpublished_entry_supersedes_nothing(tmp_path):
    """There is no object to keep, so the entry gets no previous_r2 key."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    source = _publish(tmp_path, "22in05ira.xlsx", b"IRA table 5, first publication")
    _fetch_local(package, source, upload_r2=False)

    source.write_bytes(b"IRA table 5, silently re-published")
    report = _fetch_local(package, source, upload_r2=False, record_revision=True)
    revised = _entry(package / "manifest.yaml")

    assert report.valid
    assert revised["sha256"] == (
        hashlib.sha256(b"IRA table 5, silently re-published").hexdigest()
    )
    assert "storage" not in revised


# ---------------------------------------------------------------------------
# Recorded locator cross-checks
# ---------------------------------------------------------------------------


def _recorded_package(tmp_path, content=b"IRA table 5, first publication"):
    """A package whose entry records a published, content-addressed object."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    wrangler = _wrangler_stub(tmp_path, tmp_path / "wrangler.log")
    source = _publish(tmp_path, "22in05ira.xlsx", content)
    report = _fetch_local(
        package, source, upload_r2=True, wrangler_command=str(wrangler)
    )
    return package, source, report


def _rewrite_recorded_r2(package, mutate, manifest="manifest.yaml"):
    manifest_path = package / manifest
    payload = yaml.safe_load(manifest_path.read_text())
    mutate(payload["files"][2022]["storage"])
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return manifest_path


def _other_sha256():
    return hashlib.sha256(b"some other object entirely").hexdigest()


def _contradict_key(storage):
    key = storage["r2"]["key"]
    storage["r2"]["key"] = key.replace(key.split("/")[-2], _other_sha256())


def _contradict_bucket(storage):
    storage["r2"]["bucket"] = "some-other-bucket"


def _contradict_provider(storage):
    storage["r2"]["provider"] = "s3"


def _mangle_uri(storage):
    storage["r2"]["uri"] = "r2:/ledger-raw-missing-a-slash"


def _drop_the_locator(storage):
    storage["r2"] = {"provider": "r2", "bucket": "ledger-raw"}


def _flatten_the_key(storage):
    storage["r2"]["key"] = "raw/irs_soi/22in05ira.xlsx"
    storage["r2"]["uri"] = f"r2://ledger-raw/{storage['r2']['key']}"


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(_contradict_key, "contradicts uri", id="key-vs-uri"),
        pytest.param(_contradict_bucket, "contradicts uri", id="bucket-vs-uri"),
        pytest.param(_contradict_provider, "contradicts uri", id="provider-vs-uri"),
        pytest.param(_mangle_uri, "is not provider://bucket/key", id="uri-shape"),
        pytest.param(_drop_the_locator, "records no key", id="no-locator"),
        pytest.param(
            _flatten_the_key, "is not content-addressed", id="not-content-addressed"
        ),
    ],
)
def test_a_recorded_block_that_names_two_objects_is_refused(tmp_path, mutate, expected):
    """A contradictory locator is an error, never a silently preserved block.

    The key-vs-uri case is the one that used to pass: identity was read from
    the key alone, so a block whose uri named different bytes was carried
    forward verbatim, and the manifest kept publishing a URI for an object it
    no longer described.
    """
    package, source, _ = _recorded_package(tmp_path)
    manifest_path = _rewrite_recorded_r2(package, mutate)
    recorded = manifest_path.read_bytes()

    # Identical bytes: the fetch would otherwise preserve the recorded block.
    with pytest.raises(RecordedR2LocatorError) as raised:
        _fetch_local(package, source, upload_r2=False)

    assert expected in str(raised.value)
    assert manifest_path.read_bytes() == recorded


def test_a_malformed_storage_block_is_not_treated_as_absent(tmp_path):
    package, source, _ = _recorded_package(tmp_path)
    manifest_path = _rewrite_recorded_r2(
        package, lambda storage: storage.update({"r2": ["r2://ledger-raw/raw/key"]})
    )
    recorded = manifest_path.read_bytes()

    with pytest.raises(MalformedManifestError, match="must be a mapping"):
        _fetch_local(package, source, upload_r2=False)

    assert manifest_path.read_bytes() == recorded


def test_publish_raw_refuses_a_contradictory_recorded_block(tmp_path):
    """Nothing is uploaded under a block that does not name one object."""
    package, _, _ = _recorded_package(tmp_path)
    log = tmp_path / "publish.log"
    wrangler = _wrangler_stub(tmp_path, log)
    manifest_path = _rewrite_recorded_r2(package, _contradict_key)
    recorded = manifest_path.read_bytes()

    report = publish_source_artifacts(package, wrangler_command=str(wrangler))

    assert not report.valid
    assert report.entries[0].upload is None
    assert report.entries[0].errors[0].startswith("recorded_r2_locator_invalid:")
    assert "contradicts uri" in report.entries[0].errors[0]
    assert not log.exists()
    assert manifest_path.read_bytes() == recorded


# ---------------------------------------------------------------------------
# Malformed manifests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "document",
    [
        pytest.param("- one entry\n- another\n", id="list"),
        pytest.param("a bare scalar\n", id="scalar"),
        pytest.param("files: [\n", id="unparseable"),
    ],
)
def test_a_malformed_manifest_is_refused_before_anything_is_fetched(tmp_path, document):
    """Not an absent manifest: refusing it protects what it still records.

    The publisher path does not exist, so reaching the fetch at all would raise
    FileNotFoundError instead. Getting MalformedManifestError is what says the
    manifest was read and refused first.
    """
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    package.mkdir(parents=True)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(document)

    with pytest.raises(MalformedManifestError):
        _fetch_local(package, tmp_path / "publisher" / "never-read.xlsx")

    assert manifest_path.read_text() == document
    assert list(package.iterdir()) == [manifest_path]


@pytest.mark.parametrize(
    "document",
    [
        "files:\n- not a mapping\n",
        "files: 3\n",
        "source_id: irs_soi\nfiles: text\n",
    ],
)
def test_a_non_mapping_files_block_is_refused_before_anything_is_fetched(
    tmp_path, document
):
    """The same document inventory-artifacts and publish-raw report as
    'files must be a mapping'; a fetch must not overwrite the artifact first."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    package.mkdir(parents=True)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(document)

    with pytest.raises(MalformedManifestError, match="files must be a mapping"):
        _fetch_local(package, tmp_path / "publisher" / "never-read.xlsx")

    assert manifest_path.read_text() == document
    assert list(package.iterdir()) == [manifest_path]


@pytest.mark.parametrize(
    "document",
    [
        "",
        "\n",
        "{}\n",
        "# only a comment\n",
        "files:\n",
        "source_id: irs_soi\nfiles:\n",
    ],
)
def test_an_empty_manifest_still_reads_as_absent(tmp_path, document):
    """Including a bare ``files:`` line, which parses as an explicit null: the
    fetch records into a fresh mapping rather than failing after the write."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    package.mkdir(parents=True)
    (package / "manifest.yaml").write_text(document)
    source = _publish(tmp_path, "22in05ira.xlsx", b"IRA table 5")

    report = _fetch_local(package, source, upload_r2=False)

    assert report.valid
    assert _entry(package / "manifest.yaml")["filename"] == "22in05ira.xlsx"


def test_a_malformed_manifest_is_reported_by_inventory_and_publish(tmp_path):
    """Neither sweep may crash on, or silently skip, a document it cannot read."""
    package = tmp_path / "db" / "data" / "irs_soi" / "soi-table-5"
    package.mkdir(parents=True)
    (package / "manifest.yaml").write_text("- not a mapping\n")

    inventory = inventory_source_artifacts(package)
    published = publish_source_artifacts(package)

    assert not inventory.valid
    assert inventory.entries == ()
    assert "must be a YAML mapping" in inventory.errors[0]
    assert not published.valid
    assert published.entries == ()
    assert "must be a YAML mapping" in published.errors[0]


# ---------------------------------------------------------------------------
# Sol gate round 3: fetch preflight and in-place manifest updates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    (
        "mismatched_field",
        "declared_source_id",
        "declared_package_id",
        "source_id",
        "package_id",
    ),
    [
        pytest.param(
            "source_id",
            "other_source",
            "requested-package",
            "requested_source",
            "requested-package",
            id="source-id",
        ),
        pytest.param(
            "package_id",
            "usda_snap",
            "usda-snap-fy69-to-current",
            "usda_snap",
            "usda-snap-fy2025-monthly-state-caseloads",
            id="package-id",
        ),
    ],
)
def test_fetch_refuses_a_selected_manifest_for_another_package_before_io(
    tmp_path,
    monkeypatch,
    mismatched_field,
    declared_source_id,
    declared_package_id,
    source_id,
    package_id,
):
    package = tmp_path / "db" / "data" / "usda_snap" / "fy69_to_current"
    package.mkdir(parents=True)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "source_id": declared_source_id,
                "package_id": declared_package_id,
                "files": {},
            },
            sort_keys=False,
        )
    )
    before = manifest_path.read_bytes()

    def unexpected_read(_source_url):
        raise AssertionError("a mismatched manifest must be refused before I/O")

    monkeypatch.setattr("chronicle.artifacts._read_artifact", unexpected_read)

    with pytest.raises(SourceArtifactManifestError) as raised:
        fetch_source_artifact(
            "https://example.test/snap-zip-fy69tocurrent-6.zip",
            source_id=source_id,
            package_id=package_id,
            year=2025,
            output_dir=package,
        )

    message = str(raised.value)
    declared = {
        "source_id": declared_source_id,
        "package_id": declared_package_id,
    }[mismatched_field]
    requested = {"source_id": source_id, "package_id": package_id}[mismatched_field]
    assert f"{mismatched_field}={declared!r}" in message
    assert f"{mismatched_field}={requested!r}" in message
    assert manifest_path.read_bytes() == before
    assert list(package.iterdir()) == [manifest_path]


def test_fetch_uses_a_quoted_year_key_for_revision_protection(tmp_path):
    package = tmp_path / "db" / "data" / "irs_soi" / "table"
    package.mkdir(parents=True)
    artifact_path = package / "table.xlsx"
    original = b"original publisher bytes"
    revised = b"silently revised publisher bytes"
    artifact_path.write_bytes(original)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "source_id": "irs_soi",
                "package_id": "soi-table",
                "files": {
                    "2024": {
                        "filename": artifact_path.name,
                        "source_url": "https://example.test/table.xlsx",
                        "sha256": hashlib.sha256(original).hexdigest(),
                        "size_bytes": len(original),
                    }
                },
            },
            sort_keys=False,
        )
    )
    source = _publish(tmp_path, artifact_path.name, revised)
    before = manifest_path.read_bytes()

    with pytest.raises(SourceArtifactRevisionError):
        fetch_source_artifact(
            str(source),
            source_id="irs_soi",
            package_id="soi-table",
            year=2024,
            output_dir=package,
        )

    assert manifest_path.read_bytes() == before
    assert artifact_path.read_bytes() == original


def test_fetch_refuses_both_spellings_of_one_year_before_io(tmp_path, monkeypatch):
    package = tmp_path / "db" / "data" / "irs_soi" / "table"
    package.mkdir(parents=True)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "source_id": "irs_soi",
                "package_id": "soi-table",
                "files": {
                    2024: {"filename": "numeric.xlsx"},
                    "2024": {"filename": "quoted.xlsx"},
                },
            },
            sort_keys=False,
        )
    )
    before = manifest_path.read_bytes()

    def unexpected_read(_source_url):
        raise AssertionError("ambiguous year keys must be refused before I/O")

    monkeypatch.setattr("chronicle.artifacts._read_artifact", unexpected_read)

    with pytest.raises(MalformedManifestError, match="both keys"):
        fetch_source_artifact(
            "https://example.test/table.xlsx",
            source_id="irs_soi",
            package_id="soi-table",
            year=2024,
            output_dir=package,
        )

    assert manifest_path.read_bytes() == before
    assert list(package.iterdir()) == [manifest_path]


@pytest.mark.parametrize(
    "file_spec",
    [
        pytest.param([], id="list"),
        pytest.param("not a mapping", id="string"),
        pytest.param(0, id="zero"),
        pytest.param(False, id="false"),
        pytest.param(None, id="null"),
    ],
)
def test_fetch_refuses_a_non_mapping_year_entry_before_io(
    tmp_path, monkeypatch, file_spec
):
    package = tmp_path / "db" / "data" / "irs_soi" / "table"
    package.mkdir(parents=True)
    manifest_path = package / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "source_id": "irs_soi",
                "package_id": "soi-table",
                "files": {2024: file_spec},
            },
            sort_keys=False,
        )
    )
    before = manifest_path.read_bytes()

    def unexpected_read(_source_url):
        raise AssertionError("a malformed year entry must be refused before I/O")

    monkeypatch.setattr("chronicle.artifacts._read_artifact", unexpected_read)

    with pytest.raises(MalformedManifestError, match="entry 2024.*mapping"):
        fetch_source_artifact(
            "https://example.test/table.xlsx",
            source_id="irs_soi",
            package_id="soi-table",
            year=2024,
            output_dir=package,
        )

    assert manifest_path.read_bytes() == before
    assert list(package.iterdir()) == [manifest_path]


@pytest.mark.parametrize("revision", [False, True], ids=["refetch", "revision"])
def test_fetch_carries_forward_fields_it_does_not_own(tmp_path, revision):
    package = tmp_path / "db" / "data" / "irs_soi" / "table"
    source = _publish(tmp_path, "table.xlsx", b"original publisher bytes")
    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table",
        year=2024,
        output_dir=package,
    )
    manifest_path = package / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    metadata = {
        "source_table": "Publisher table 7",
        "notes": "Keep this review note.",
        "source_urls": ["https://example.test/landing-page"],
        "archive_member": "table.csv",
        "year": 2024,
    }
    manifest["files"][2024].update(metadata)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    if revision:
        source.write_bytes(b"publisher revision")

    fetch_source_artifact(
        str(source),
        source_id="irs_soi",
        package_id="soi-table",
        year=2024,
        output_dir=package,
        record_revision=revision,
    )

    updated = yaml.safe_load(manifest_path.read_text())["files"][2024]
    for field, value in metadata.items():
        assert updated.get(field) == value
