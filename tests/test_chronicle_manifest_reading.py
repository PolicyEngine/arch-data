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


def test_strict_loader_does_not_mutate_anchored_entries_when_merged_later():
    """Constructing a later merge of an anchored entry must not turn that
    entry's inherited keys into 'explicit' ones: PyYAML constructs lazily and
    flattens merged nodes in place."""
    from chronicle.registration import load_manifest_document

    document = load_manifest_document(
        "defaults: &d\n"
        "  source_url: old\n"
        "files:\n"
        "  2024: &e\n"
        "    <<: *d\n"
        "    source_url: new\n"
        "latest:\n"
        "  <<: *e\n"
    )

    assert document["files"][2024]["source_url"] == "new"
    assert document["latest"]["source_url"] == "new"


def test_strict_loader_validates_duplicate_keys_inside_inline_merges():
    """A mapping reached through ``<<`` is still a mapping the document
    spells out; duplicate keys inside it must be refused, not collapsed."""
    from chronicle.registration import load_manifest_document

    with pytest.raises(yaml.YAMLError, match="duplicate key 'files'"):
        load_manifest_document(
            "<<: {files: {2023: {filename: old.csv}}, files: {2024: {filename: new.csv}}}\n"
        )
