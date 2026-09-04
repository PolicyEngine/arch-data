"""Shared source-artifact registration primitives.

This module holds manifest parsing and filename identity rules used at every
artifact boundary.  PR #227 extends the same surface with access-specific
registration; keeping the common functions here lets that stacked work rebase
without inventing parallel helpers.
"""

from __future__ import annotations

from typing import Any

import yaml


class StrictManifestLoader(yaml.SafeLoader):
    """A YAML loader that refuses a mapping with duplicate keys.

    PyYAML keeps the last of two equal keys, so ``files:`` recorded twice, or
    a vintage recorded as ``2023`` and again as ``2_023`` (the same integer),
    would read as one entry and the shadowed entry would be dropped by the
    next write. A manifest is the record the byte boundary is decided from,
    so a document the loader cannot represent faithfully is malformed.
    """

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )
        self.flatten_mapping(node)
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found unhashable key ({exc})",
                    key_node.start_mark,
                ) from exc
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_manifest_document(text: str) -> Any:
    """Parse a manifest document, refusing duplicate keys.

    Raises :class:`yaml.YAMLError` (a ``ConstructorError`` naming the
    duplicate key) for a document YAML would otherwise silently collapse.
    """
    return yaml.load(text, Loader=StrictManifestLoader)  # noqa: S506


__all__ = ["StrictManifestLoader", "load_manifest_document"]
