"""Public microdata staging stays outside repositories and package trees."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest
import yaml

from chronicle.artifacts import ArtifactCommandResult
from chronicle.registration import ManifestAccessError
from tests.test_chronicle_microdata_registration import PUBLIC_BYTES, _fetch_release


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "destination",
    [
        "output-directory",
        "nested-output-directory",
        "repository-directory",
        "another-package-directory",
        "symlink-component",
        "symlink-before-parent-component",
        "symlink-identity-component",
    ],
)
def test_fetch_refuses_unsafe_microdata_staging_before_publisher_read(
    tmp_path, monkeypatch, destination
):
    output = tmp_path / "package"
    staging = tmp_path / "staging"
    if destination == "output-directory":
        staging = output
    elif destination == "nested-output-directory":
        staging = output / "nested" / "staging"
    elif destination == "repository-directory":
        staging = REPO_ROOT / ".chronicle-test-staging-refusal" / "nested"
    elif destination == "another-package-directory":
        package = tmp_path / "another-package"
        package.mkdir()
        (package / "manifest.yaml").write_text(
            yaml.safe_dump({"kind": "publisher_table", "files": {}})
        )
        staging = package / "nested" / "staging"
    else:
        outside = tmp_path / "outside" / "child"
        outside.mkdir(parents=True)
        if destination == "symlink-identity-component":
            staging.mkdir()
            (staging / "census_acs").symlink_to(outside, target_is_directory=True)
        else:
            alias = tmp_path / "alias"
            alias.symlink_to(outside, target_is_directory=True)
            staging = (
                alias / ".." / "staging"
                if destination == "symlink-before-parent-component"
                else alias / "staging"
            )

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
