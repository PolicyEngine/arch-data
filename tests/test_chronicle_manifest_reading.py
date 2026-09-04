"""Manifest reading contracts shared by every consumer on this branch."""

from __future__ import annotations

import pytest
import yaml


def test_strict_loader_keeps_yaml_merge_overrides_and_refuses_explicit_duplicates():
    """A ``<<: *defaults`` merge followed by an explicit override is valid YAML
    (the explicit key wins); only two explicit spellings of one key are a
    duplicate the loader must refuse."""
    from chronicle.registration import load_manifest_document

    merged = load_manifest_document(
        "defaults: &defaults\n"
        "  source_url: https://publisher.test/a\n"
        "  filename: table.csv\n"
        "files:\n"
        "  2024:\n"
        "    <<: *defaults\n"
        "    source_url: https://publisher.test/b\n"
        "    sha256: " + "ab" * 32 + "\n"
    )

    assert merged["files"][2024]["source_url"] == "https://publisher.test/b"
    assert merged["files"][2024]["filename"] == "table.csv"

    with pytest.raises(yaml.YAMLError, match="duplicate key 'source_url'"):
        load_manifest_document(
            "defaults: &defaults\n"
            "  filename: table.csv\n"
            "files:\n"
            "  2024:\n"
            "    <<: *defaults\n"
            "    source_url: https://publisher.test/a\n"
            "    source_url: https://publisher.test/b\n"
        )
