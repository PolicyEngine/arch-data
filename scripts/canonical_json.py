#!/usr/bin/env python3
# Thin shim over the receipt pin recorded in uv.lock. Any receipt upgrade
# requires a fresh byte-equivalence proof at this repo's then-current pin BEFORE
# the bump.
"""Canonical JSON compatibility surface backed by receipt."""

from receipt.canonical import (
    canonical_bytes,
    canonical_sha256,
    canonical_stringify,
    main,
    utf16_sort_key,
)

__all__ = [
    "canonical_bytes",
    "canonical_sha256",
    "canonical_stringify",
    "main",
    "utf16_sort_key",
]


if __name__ == "__main__":
    raise SystemExit(main())
