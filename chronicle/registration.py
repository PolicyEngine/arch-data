"""Shared source-artifact registration primitives.

This module holds manifest parsing and filename identity rules used at every
artifact boundary.  PR #227 extends the same surface with access-specific
registration; keeping the common functions here lets that stacked work rebase
without inventing parallel helpers.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Mapping
import unicodedata

import yaml


class ArtifactFilenameError(ValueError):
    """Raised when a filename is not a bare name inside a package directory."""


def is_bare_filename(value: Any) -> bool:
    """Whether ``value`` names a file inside a directory, with no path."""
    if value is None:
        return False
    text = str(value).strip()
    if not text or text != str(value) or text in (".", ".."):
        return False
    if "/" in text or "\\" in text or "\x00" in text:
        return False
    return Path(text).name == text


def bare_filename(value: Any, *, what: str = "filename") -> str:
    """Return ``value`` as a bare filename, refusing any other spelling.

    ``./adult.tab``, ``sub/../adult.tab``, ``adult.tab/`` and an absolute path
    all resolve to the same file as ``adult.tab`` once joined under the package
    directory, so the manifest and every guard use one spelling.
    """
    if not is_bare_filename(value):
        raise ArtifactFilenameError(
            f"{what} must be a bare filename inside the package directory, not "
            f"{value!r}; it may not carry a directory, '.', '..', a trailing "
            "slash, surrounding whitespace, or an absolute path."
        )
    return str(value)


def filename_key(value: Any) -> str:
    """Return the case-folded, Unicode-normalized comparison key for a name."""
    return unicodedata.normalize("NFC", Path(str(value)).name).casefold()


_MANIFEST_FILENAME_RE = re.compile(
    r"^manifest(?:_[^/\\]+)?\.ya?ml$",
    re.IGNORECASE,
)


def is_manifest_filename(value: Any) -> bool:
    """Whether ``value`` is a package-manifest filename."""
    return is_bare_filename(value) and bool(_MANIFEST_FILENAME_RE.fullmatch(str(value)))


def package_manifest_paths(package_dir: Path) -> list[Path]:
    """Return every manifest file a package directory keeps, sorted by name."""
    directory = Path(package_dir)
    if not directory.is_dir():
        return []
    manifests = []
    for path in sorted(directory.iterdir()):
        if not is_manifest_filename(path.name):
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"{path} carries a manifest name but is not a regular file; "
                "Chronicle will not register beside it or sweep past it."
            )
        manifests.append(path)
    return manifests


def validate_package_directory(
    manifests: Mapping[str, Mapping[str, Any] | None],
) -> tuple[str, ...]:
    """Return filename-identity collisions across a package's manifests.

    Two manifests may name one physical file only when they record the same
    digest. A differing digest means the same package-local bytes have two
    incompatible identities, so no command may act through either record.
    """
    by_name: dict[str, list[tuple[str, str]]] = {}
    for name, manifest in manifests.items():
        files = manifest.get("files") if isinstance(manifest, Mapping) else None
        if not isinstance(files, Mapping):
            continue
        for entry in files.values():
            if not isinstance(entry, Mapping):
                continue
            filename = entry.get("filename")
            if filename is None:
                continue
            digest = entry.get("sha256")
            digest = digest.strip() if isinstance(digest, str) else ""
            by_name.setdefault(filename_key(filename), []).append((name, digest))

    errors: list[str] = []
    for key, records in by_name.items():
        if len({name for name, _digest in records}) < 2:
            continue
        if len({digest for _name, digest in records}) > 1:
            errors.append(f"filename_collision_across_manifests:{key}")
    return tuple(dict.fromkeys(errors))


def matching_directory_entry(directory: Any, filename: Any) -> Any | None:
    """Return the actual directory entry matching a bare filename's safe key.

    Scanning real entries makes the identity rule the same on case-sensitive
    and case-folding filesystems, including Unicode-normalized aliases.
    """
    if not is_bare_filename(filename) or not directory.is_dir():
        return None
    wanted = filename_key(filename)
    matches = [
        path
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if filename_key(path.name) == wanted
    ]
    if len(matches) > 1:
        names = ", ".join(repr(path.name) for path in matches)
        raise ValueError(
            f"{filename!r} matches more than one physical entry ({names}); "
            "the package holds conflicting spellings of one artifact identity "
            "and must be repaired by hand."
        )
    return matches[0] if matches else None


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


__all__ = [
    "ArtifactFilenameError",
    "StrictManifestLoader",
    "bare_filename",
    "filename_key",
    "is_bare_filename",
    "is_manifest_filename",
    "load_manifest_document",
    "matching_directory_entry",
    "package_manifest_paths",
    "validate_package_directory",
]
