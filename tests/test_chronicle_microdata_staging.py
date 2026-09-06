"""Public microdata staging stays outside repositories and package trees."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest
import yaml

from chronicle.artifacts import (
    ArtifactCommandResult,
    microdata_staging_path,
    publish_source_artifacts,
)
from chronicle.registration import ManifestAccessError
from tests.test_chronicle_microdata_registration import (
    PUBLIC_BYTES,
    PUBLIC_SHA,
    _fetch_release,
    _record_uploads,
    _serve,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(
    params=[
        "output-directory",
        "nested-output-directory",
        "repository-directory",
        "repository-data-directory",
        "another-package-directory",
        "another-package-yml",
        "another-named-package",
        "another-git-checkout",
        "another-git-worktree",
        "bare-git-repository",
        "symlink-component",
        "symlink-before-parent-component",
        "symlink-identity-component",
        "symlink-filename-component",
    ],
)
def unsafe_microdata_staging(tmp_path, request):
    destination = request.param
    output = tmp_path / "package"
    staging = tmp_path / "staging"
    if destination == "output-directory":
        staging = output
    elif destination == "nested-output-directory":
        staging = output / "nested" / "staging"
    elif destination == "repository-directory":
        staging = REPO_ROOT / ".chronicle-test-staging-refusal" / "nested"
    elif destination == "repository-data-directory":
        staging = REPO_ROOT / "db" / "data" / ".chronicle-test-staging-refusal"
    elif destination in {
        "another-package-directory",
        "another-package-yml",
        "another-named-package",
    }:
        package = tmp_path / "another-package"
        package.mkdir()
        manifest_name = {
            "another-package-directory": "manifest.yaml",
            "another-package-yml": "Manifest.yml",
            "another-named-package": "manifest_public.YAML",
        }[destination]
        (package / manifest_name).write_text(
            yaml.safe_dump({"kind": "publisher_table", "files": {}})
        )
        staging = package / "nested" / "staging"
    elif destination in {
        "another-git-checkout",
        "another-git-worktree",
        "bare-git-repository",
    }:
        repository = tmp_path / "another-repository"
        repository.mkdir()
        if destination == "another-git-checkout":
            (repository / ".git").mkdir()
        elif destination == "another-git-worktree":
            (repository / ".git").write_text("gitdir: /elsewhere/worktrees/example\n")
        else:
            (repository / "HEAD").write_text("ref: refs/heads/main\n")
            (repository / "objects").mkdir()
            (repository / "refs").mkdir()
        staging = repository / "nested" / "staging"
    else:
        outside = tmp_path / "outside" / "child"
        outside.mkdir(parents=True)
        if destination == "symlink-identity-component":
            staging.mkdir()
            (staging / "census_acs").symlink_to(outside, target_is_directory=True)
        elif destination == "symlink-filename-component":
            identity = (
                staging
                / "census_acs"
                / "census-acs-pums-2022-1yr"
                / "2022"
                / PUBLIC_SHA
            )
            identity.mkdir(parents=True)
            (identity / "csv_hus.zip").symlink_to(outside / "missing.zip")
        else:
            alias = tmp_path / "alias"
            alias.symlink_to(outside, target_is_directory=True)
            staging = (
                alias / ".." / "staging"
                if destination == "symlink-before-parent-component"
                else alias / "staging"
            )

    return output, staging


def test_fetch_refuses_unsafe_microdata_staging_before_publisher_read(
    monkeypatch, unsafe_microdata_staging
):
    output, staging = unsafe_microdata_staging
    effects = []
    monkeypatch.setattr(
        "chronicle.artifacts._registration_lock",
        lambda path: effects.append(("lock", path)) or nullcontext(),
    )
    monkeypatch.setattr(
        "chronicle.artifacts._read_artifact",
        lambda url: (
            effects.append(("publisher_read", url)) or (PUBLIC_BYTES, "csv_hus.zip")
        ),
    )
    # Record every mutation instead of putting release bytes anywhere, even
    # while this regression runs against the vulnerable implementation.
    monkeypatch.setattr(
        Path, "mkdir", lambda path, **kwargs: effects.append(("mkdir", path))
    )
    monkeypatch.setattr(
        Path,
        "write_bytes",
        lambda path, content: effects.append(("write_bytes", path)),
    )
    monkeypatch.setattr(
        "chronicle.artifacts._upsert_manifest",
        lambda path, **kwargs: effects.append(("manifest_write", path)),
    )
    monkeypatch.setattr(
        "chronicle.artifacts._upload_r2_object",
        lambda location, path, **kwargs: (
            effects.append(("upload", path))
            or ArtifactCommandResult(
                command=("stub",), returncode=0, stdout="", stderr=""
            )
        ),
    )

    with pytest.raises(ManifestAccessError, match="[Ss]taging"):
        _fetch_release(output, staging_dir=staging, upload_r2=True)

    assert effects == []


def test_publish_refuses_unsafe_microdata_staging_before_read_or_upload(
    tmp_path, monkeypatch, unsafe_microdata_staging
):
    output, staging = unsafe_microdata_staging
    _serve(monkeypatch, PUBLIC_BYTES)
    _fetch_release(output, staging_dir=tmp_path / "safe-staging")
    manifest_path = output / "manifest.yaml"
    before = manifest_path.read_bytes()
    staged = microdata_staging_path(
        staging_dir=staging,
        source_id="census_acs",
        package_id="census-acs-pums-2022-1yr",
        year=2022,
        sha256=PUBLIC_SHA,
        filename="csv_hus.zip",
    )
    effects = []
    original_is_file = Path.is_file
    original_read_bytes = Path.read_bytes
    # Simulate existing staged bytes without writing into any unsafe tree.
    monkeypatch.setattr(
        Path, "is_file", lambda path: path == staged or original_is_file(path)
    )

    def read_bytes(path):
        if path == staged:
            effects.append(("artifact_read", path))
            return PUBLIC_BYTES
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(
        "chronicle.artifacts._registration_lock",
        lambda path: effects.append(("lock", path)) or nullcontext(),
    )
    monkeypatch.setattr(
        "chronicle.artifacts._upload_r2_object",
        lambda location, path, **kwargs: (
            effects.append(("upload", path))
            or ArtifactCommandResult(
                command=("stub",), returncode=0, stdout="", stderr=""
            )
        ),
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda path, content, **kwargs: effects.append(("manifest_write", path)),
    )

    report = publish_source_artifacts(output, staging_dir=staging)

    assert effects == [], report
    assert not report.valid
    assert any(
        ("staging" in error.lower() or "artifact_path_is_symlink" in error)
        for error in (
            *report.errors,
            *(e for entry in report.entries for e in entry.errors),
        )
    )
    assert manifest_path.read_bytes() == before


@pytest.mark.parametrize("spelling", ["absolute", "relative", "parent-component"])
def test_fetch_accepts_external_microdata_staging(tmp_path, monkeypatch, spelling):
    output = tmp_path / "package"
    external = tmp_path / "package-external"
    staging = external
    if spelling == "relative":
        monkeypatch.chdir(tmp_path)
        staging = Path("package-external")
    elif spelling == "parent-component":
        (tmp_path / "existing").mkdir()
        staging = tmp_path / "existing" / ".." / "package-external"
    _serve(monkeypatch, PUBLIC_BYTES)
    uploads = _record_uploads(monkeypatch)

    report = _fetch_release(output, staging_dir=staging, upload_r2=True)

    assert report.valid
    staged = Path(report.local_path)
    assert staged.is_relative_to(external)
    assert staged.read_bytes() == PUBLIC_BYTES
    assert uploads == [(report.r2_location.uri, str(staged))]
    assert sorted(path.name for path in output.iterdir()) == ["manifest.yaml"]
