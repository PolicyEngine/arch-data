#!/usr/bin/env python3
# Thin shim over receipt==0.5.1 (hash-pinned in uv.lock). Any receipt upgrade
# requires a fresh byte-equivalence proof at this repo's then-current pin BEFORE
# the bump.
"""Gate every change to the thesis-facts observation ledger."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import receipt.append_gate as _receipt
from receipt.release_chain import MANIFEST_RE, ReleaseChainError

try:
    from receipt_pins import APPEND_GATE_SPEC
except ModuleNotFoundError as exc:
    if exc.name != "receipt_pins":
        raise
    # The test suite copies the legacy three-script surface into temporary
    # repositories. The editable consumer tree remains the sole pin owner.
    from scripts.receipt_pins import APPEND_GATE_SPEC


CODE_ROOT = pathlib.Path(__file__).resolve().parents[1]
RELEASE_MANIFEST_PREFIX = APPEND_GATE_SPEC.release_manifest_prefix
GENESIS_SUPPORT_FILES = APPEND_GATE_SPEC.genesis_support_files
GATE_SURFACE = APPEND_GATE_SPEC.gate_surface
DATA_SURFACE = APPEND_GATE_SPEC.data_surface
ASSERTION_CONTENT_KEYS = APPEND_GATE_SPEC.assertion_content_keys

AppendError = _receipt.AppendError
AppendGateSpec = _receipt.AppendGateSpec
reject_non_append_bytes = _receipt.reject_non_append_bytes


def expected_assertion_version_id(row: dict[str, Any]) -> str:
    return _receipt.expected_assertion_version_id(row, APPEND_GATE_SPEC)


def effective_current_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _receipt.effective_current_rows(rows, APPEND_GATE_SPEC)


def check_rows(lines: list[str], prefix_count: int) -> None:
    return _receipt.check_rows(lines, prefix_count, APPEND_GATE_SPEC)


def verify_append_gate(
    root: pathlib.Path,
    *,
    base_ref: str | None = None,
    trusted_code_root: pathlib.Path = CODE_ROOT,
    release_anchor_dir: pathlib.Path | None = None,
) -> str:
    return _receipt.verify_append_gate(
        root,
        spec=APPEND_GATE_SPEC,
        base_ref=base_ref,
        trusted_code_root=trusted_code_root,
        release_anchor_dir=release_anchor_dir,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=CODE_ROOT,
        help="candidate worktree root (defaults to the checker's repository)",
    )
    parser.add_argument(
        "--base-ref",
        help="enforce an append-only diff against this git ref",
    )
    parser.add_argument(
        "--release-anchor-dir",
        type=pathlib.Path,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    try:
        summary = verify_append_gate(
            args.root.resolve(),
            base_ref=args.base_ref,
            trusted_code_root=CODE_ROOT.resolve(),
            release_anchor_dir=args.release_anchor_dir,
        )
    except AppendError as exc:
        print(f"thesis-facts append check failed: {exc}", file=sys.stderr)
        return 1
    print(summary)
    return 0


__all__ = [
    "APPEND_GATE_SPEC",
    "ASSERTION_CONTENT_KEYS",
    "AppendError",
    "AppendGateSpec",
    "CODE_ROOT",
    "DATA_SURFACE",
    "GATE_SURFACE",
    "GENESIS_SUPPORT_FILES",
    "MANIFEST_RE",
    "RELEASE_MANIFEST_PREFIX",
    "ReleaseChainError",
    "check_rows",
    "effective_current_rows",
    "expected_assertion_version_id",
    "main",
    "reject_non_append_bytes",
    "verify_append_gate",
]


if __name__ == "__main__":
    raise SystemExit(main())
