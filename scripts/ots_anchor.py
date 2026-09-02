#!/usr/bin/env python3
"""Anchor witnessed release manifests in Bitcoin via OpenTimestamps.

Each supplied release manifest is already witnessed by two RFC 3161
authorities and a pinned producer signature over its exact bytes. This tool
adds an operator-independent witness: an OpenTimestamps proof over those same
exact bytes, committed as ``ots/<stem>.json.ots`` in this repository. Because
manifest ``state.jsonlSha256`` covers the full journal bytes and
``previousManifestSha256`` chains every earlier manifest, a Bitcoin
attestation over one manifest bounds the existence time of the whole journal
state it commits to.

Proofs live in this repository's top-level ``ots/`` directory, never beside
the manifests. The manifests may be supplied from a separate, credential-free
journal checkout with ``--manifests``. OpenTimestamps upgrades rewrite proof
files in place, while the journal's release history is immutable.

Subcommands:

- ``run``: stamp any manifest that lacks a proof, then try to upgrade pending
  proofs to complete Bitcoin attestations. Idempotent; safe on a schedule.
- ``verify``: check every proof against its manifest's current bytes and
  report the state stored in each local proof. Exits nonzero on a digest
  mismatch or a manifest with no proof.
- ``status``: list proofs and whether each is unanchored, pending locally, or
  Bitcoin-complete locally.
- ``guard``: fail if the repository has any change outside ``ots/``.

Requires the ``ots`` CLI (PyPI ``opentimestamps-client``); stamping and
upgrading contact public calendar servers. Verification with ``--no-bitcoin``
checks the file binding and prints manual Bitcoin block-check information.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_DIR = pathlib.Path("releases/manifests")
OTS_DIR = pathlib.Path("ots")
MANIFEST_NAME_RE = re.compile(r"^(\d{4})-([0-9a-f]{16})\.json$")
SUBPROCESS_TIMEOUT = 300

# Full-line patterns observed from opentimestamps-client 0.7.2. Calendar URLs
# and errors are untrusted text, so substring matches are intentionally unsafe.
_MISMATCH_LINE_RE = re.compile(r"^\s*File does not match original!?\s*$", re.MULTILINE)
_VERIFY_PENDING_LINE_RE = re.compile(
    r"^\s*Pending confirmation in Bitcoin blockchain\s*$", re.MULTILINE
)
_VERIFY_MANUAL_LINE_RE = re.compile(
    r"^\s*To verify manually, check that Bitcoin block \d+ "
    r"has merkleroot [0-9a-fA-F]+\s*$",
    re.MULTILINE,
)
_NO_NODE_LINE_RE = re.compile(
    r"^\s*Could not connect to Bitcoin node(?:[.:].*)?\s*$", re.MULTILINE
)
_UPGRADE_PENDING_LINE_RE = re.compile(
    r"^\s*(?:Failed!\s*)?Timestamp not complete\.?\s*$", re.MULTILINE
)
_INFO_BITCOIN_LINE_RE = re.compile(
    r"^\s*verify BitcoinBlockHeaderAttestation\(\d+\)\s*$", re.MULTILINE
)
_INFO_PENDING_LINE_RE = re.compile(
    r"^\s*verify PendingAttestation\([^\r\n]*\)\s*$", re.MULTILINE
)


class AnchorError(RuntimeError):
    """A condition that must stop the anchoring run."""


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_manifests(directory: pathlib.Path) -> list[pathlib.Path]:
    if not directory.is_dir():
        raise AnchorError(f"manifest directory missing: {directory}")
    manifests: list[pathlib.Path] = []
    for candidate in sorted(directory.iterdir()):
        if not MANIFEST_NAME_RE.match(candidate.name):
            continue
        if candidate.is_symlink() or not candidate.is_file():
            raise AnchorError(f"manifest is not a regular file: {candidate}")
        manifests.append(candidate)
    if not manifests:
        raise AnchorError(f"no release manifests found in {directory}")
    return manifests


def check_manifest_name_digest(manifest: pathlib.Path) -> str:
    """Refuse to anchor bytes that contradict the manifest's own filename."""

    match = MANIFEST_NAME_RE.match(manifest.name)
    if match is None:  # discover_manifests already filtered on the pattern
        raise AnchorError(f"unexpected manifest filename: {manifest.name}")
    digest = sha256_file(manifest)
    if digest[:16] != match.group(2):
        raise AnchorError(
            f"manifest {manifest.name} bytes hash to {digest[:16]}..., "
            "which contradicts the filename; refusing to anchor"
        )
    return digest


def proof_path(root: pathlib.Path, manifest: pathlib.Path) -> pathlib.Path:
    return root / OTS_DIR / f"{manifest.name}.ots"


def ensure_ots_directory(root: pathlib.Path) -> pathlib.Path:
    directory = root / OTS_DIR
    if directory.is_symlink():
        raise AnchorError(f"proof directory must not be a symlink: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.is_dir():
        raise AnchorError(f"proof path is not a directory: {directory}")
    return directory


def check_proof_destination(proof: pathlib.Path) -> None:
    """Reject proof paths that could redirect writes outside ``ots/``."""

    if proof.is_symlink():
        raise AnchorError(f"proof path must not be a symlink: {proof}")
    if proof.exists() and not proof.is_file():
        raise AnchorError(f"proof path is not a regular file: {proof}")


def _run_ots(
    ots_bin: list[str], arguments: list[str], *, timeout: int = SUBPROCESS_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    command = [*ots_bin, *arguments]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AnchorError(
            f"ots binary not found ({command[0]!r}); install "
            "opentimestamps-client or pass --ots-bin"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AnchorError(f"ots timed out: {' '.join(command)}") from exc


def stamp_manifest(
    root: pathlib.Path, manifest: pathlib.Path, ots_bin: list[str]
) -> pathlib.Path:
    """Stamp a temporary copy, installing output only in a real ``ots/``."""

    directory = ensure_ots_directory(root)
    destination = proof_path(root, manifest)
    check_proof_destination(destination)
    if destination.exists():
        raise AnchorError(f"refusing to replace existing proof: {destination}")

    # Keeping the temporary directory beneath ots/ makes os.replace atomic and
    # guarantees that even the client's temporary output cannot reach releases/.
    with tempfile.TemporaryDirectory(prefix=".ots-anchor-", dir=directory) as name:
        working_copy = pathlib.Path(name) / manifest.name
        shutil.copyfile(manifest, working_copy)
        completed = _run_ots(ots_bin, ["stamp", str(working_copy)])
        produced = working_copy.with_name(working_copy.name + ".ots")
        if completed.returncode != 0 or produced.is_symlink() or not produced.is_file():
            raise AnchorError(
                f"ots stamp failed for {manifest.name}: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        check_proof_destination(destination)
        os.replace(produced, destination)
    return destination


def local_proof_state(proof: pathlib.Path, ots_bin: list[str]) -> str:
    """Return the attestation state serialized in the local proof itself."""

    check_proof_destination(proof)
    if not proof.is_file():
        raise AnchorError(f"proof file missing: {proof}")
    completed = _run_ots(ots_bin, ["info", str(proof)])
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        raise AnchorError(f"ots info failed for {proof.name}: {output.strip()}")
    if _INFO_BITCOIN_LINE_RE.search(output):
        return "bitcoin"
    if _INFO_PENDING_LINE_RE.search(output):
        return "pending"
    raise AnchorError(
        f"proof {proof.name} lists neither a Bitcoin nor a pending "
        "attestation; refusing to guess"
    )


def proof_is_complete(proof: pathlib.Path, ots_bin: list[str]) -> bool:
    """True only when the committed proof file carries a Bitcoin attestation."""

    return local_proof_state(proof, ots_bin) == "bitcoin"


def _restore_upgrade_backup(proof: pathlib.Path, backup: pathlib.Path) -> None:
    """Restore the client's backup after an interrupted or invalid upgrade."""

    if not backup.exists() and not backup.is_symlink():
        return
    if backup.is_symlink() or not backup.is_file():
        raise AnchorError(f"unsafe OpenTimestamps backup path: {backup}")
    if proof.is_symlink():
        proof.unlink()
    elif proof.exists():
        if not proof.is_file():
            raise AnchorError(f"cannot restore proof over non-file: {proof}")
        proof.unlink()
    os.replace(backup, proof)


def upgrade_proof(
    manifest: pathlib.Path, proof: pathlib.Path, ots_bin: list[str]
) -> bool:
    """Upgrade a pending proof and validate its replacement before cleanup.

    Returns whether the validated local replacement contains a Bitcoin block
    attestation. A normal still-pending response restores the original proof.
    """

    check_proof_destination(proof)
    if not proof.is_file():
        raise AnchorError(f"proof file missing: {proof}")
    backup = proof.with_name(proof.name + ".bak")
    if backup.exists() or backup.is_symlink():
        raise AnchorError(f"refusing to overwrite existing backup: {backup}")

    completed = _run_ots(ots_bin, ["upgrade", str(proof)])
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        _restore_upgrade_backup(proof, backup)
        if _UPGRADE_PENDING_LINE_RE.search(output):
            return False
        raise AnchorError(f"ots upgrade failed for {proof.name}: {output.strip()}")

    try:
        check_proof_destination(proof)
        if not proof.is_file():
            raise AnchorError(f"ots upgrade removed proof: {proof.name}")
        state = classify_proof(manifest, proof, ots_bin)
        if state == "mismatch":
            raise AnchorError(
                f"upgraded proof {proof.name} does not match manifest bytes"
            )
    except (AnchorError, OSError):
        _restore_upgrade_backup(proof, backup)
        raise

    if backup.exists() or backup.is_symlink():
        if backup.is_symlink() or not backup.is_file():
            _restore_upgrade_backup(proof, backup)
            raise AnchorError(f"unsafe OpenTimestamps backup path: {backup}")
        backup.unlink()
    return state == "bitcoin"


def verify_proof_binding(
    manifest: pathlib.Path, proof: pathlib.Path, ots_bin: list[str]
) -> bool:
    """Return false only when ``ots`` proves the file digest is mismatched."""

    completed = _run_ots(
        ots_bin, ["--no-bitcoin", "verify", "-f", str(manifest), str(proof)]
    )
    output = completed.stdout + completed.stderr
    if _MISMATCH_LINE_RE.search(output):
        return False
    if completed.returncode == 0:
        return True
    if (
        _VERIFY_PENDING_LINE_RE.search(output)
        or _VERIFY_MANUAL_LINE_RE.search(output)
        or _NO_NODE_LINE_RE.search(output)
    ):
        return True
    raise AnchorError(
        f"unrecognized ots verify outcome for {proof.name}: {output.strip()}"
    )


def classify_proof(
    manifest: pathlib.Path, proof: pathlib.Path, ots_bin: list[str]
) -> str:
    """Classify a locally stored proof after checking its exact-file binding."""

    if not verify_proof_binding(manifest, proof, ots_bin):
        return "mismatch"
    return local_proof_state(proof, ots_bin)


def command_run(
    root: pathlib.Path, manifest_dir: pathlib.Path, ots_bin: list[str]
) -> int:
    manifests = discover_manifests(manifest_dir)
    ensure_ots_directory(root)
    stamped: list[str] = []
    upgraded: list[str] = []
    pending: list[str] = []
    for manifest in manifests:
        check_manifest_name_digest(manifest)
        proof = proof_path(root, manifest)
        check_proof_destination(proof)
        if not proof.exists():
            stamp_manifest(root, manifest, ots_bin)
            state = classify_proof(manifest, proof, ots_bin)
            if state == "mismatch":
                raise AnchorError(
                    f"new proof {proof.name} does not match manifest bytes"
                )
            stamped.append(manifest.name)
            if state == "pending":
                pending.append(manifest.name)
            continue

        # Binding is checked before completeness, including for a proof whose
        # local structure already contains a Bitcoin attestation.
        state = classify_proof(manifest, proof, ots_bin)
        if state == "mismatch":
            raise AnchorError(
                f"proof {proof.name} does not match manifest bytes; refusing to skip"
            )
        if proof_is_complete(proof, ots_bin):
            continue
        if upgrade_proof(manifest, proof, ots_bin):
            upgraded.append(manifest.name)
        else:
            pending.append(manifest.name)
    print(
        f"ots anchor run: {len(manifests)} manifests, "
        f"stamped {len(stamped)}, upgraded {len(upgraded)}, "
        f"still pending {len(pending)}"
    )
    for name in stamped:
        print(f"  stamped {name}")
    for name in upgraded:
        print(f"  upgraded {name}")
    return 0


def command_verify(
    root: pathlib.Path,
    manifest_dir: pathlib.Path,
    ots_bin: list[str],
    *,
    require_bitcoin: bool,
) -> int:
    manifests = discover_manifests(manifest_dir)
    failures: list[str] = []
    pending_count = 0
    bitcoin_count = 0
    for manifest in manifests:
        check_manifest_name_digest(manifest)
        proof = proof_path(root, manifest)
        check_proof_destination(proof)
        if not proof.exists():
            failures.append(f"{manifest.name}: no OpenTimestamps proof")
            continue
        state = classify_proof(manifest, proof, ots_bin)
        if state == "mismatch":
            failures.append(f"{manifest.name}: proof does not match manifest bytes")
        elif state == "pending":
            pending_count += 1
            if require_bitcoin:
                failures.append(f"{manifest.name}: attestation not yet in local proof")
        else:
            bitcoin_count += 1
    print(
        f"ots anchor verify: {len(manifests)} manifests, "
        f"{bitcoin_count} locally Bitcoin-complete, {pending_count} pending locally"
    )
    for failure in failures:
        print(f"  FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print("every release manifest has an OpenTimestamps proof bound to its exact bytes")
    return 0


def command_status(
    root: pathlib.Path, manifest_dir: pathlib.Path, ots_bin: list[str]
) -> int:
    manifests = discover_manifests(manifest_dir)
    for manifest in manifests:
        check_manifest_name_digest(manifest)
        proof = proof_path(root, manifest)
        check_proof_destination(proof)
        if not proof.exists():
            print(f"{manifest.name}: unanchored")
            continue
        state = classify_proof(manifest, proof, ots_bin)
        label = {
            "bitcoin": "bitcoin attestation stored locally",
            "pending": "pending local proof",
            "mismatch": "MISMATCH",
        }[state]
        print(f"{manifest.name}: {label}")
    return 0


def git_changed_paths(root: pathlib.Path) -> list[str]:
    """Return both sides of every porcelain-v1 change record."""

    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AnchorError(f"git status failed: {completed.stderr.strip()}")
    fields = completed.stdout.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        if not record:
            index += 1
            continue
        if len(record) < 4 or record[2] != " ":
            raise AnchorError(f"unrecognized git status record: {record!r}")
        status = record[:2]
        paths.append(record[3:])
        if "R" in status or "C" in status:
            index += 1
            if index >= len(fields) or not fields[index]:
                raise AnchorError("git status omitted a rename/copy source path")
            paths.append(fields[index])
        index += 1
    return paths


def assert_only_ots_changes(root: pathlib.Path) -> int:
    paths = git_changed_paths(root)
    outside = sorted(
        changed for changed in paths if not changed.startswith(f"{OTS_DIR.as_posix()}/")
    )
    if outside:
        details = ", ".join(outside)
        raise AnchorError(f"refusing changes outside ots/: {details}")
    return len(paths)


def command_guard(root: pathlib.Path) -> int:
    changed_count = assert_only_ots_changes(root)
    print(f"ots publication guard: {changed_count} changed path(s), all under ots/")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="anchor witnessed release manifests via OpenTimestamps"
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root",
        type=pathlib.Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    common.add_argument(
        "--manifests",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST_DIR,
        help=(
            "manifest directory, absolute or relative to --root (default: %(default)s)"
        ),
    )
    common.add_argument(
        "--ots-bin",
        default="ots",
        help="ots invocation, shell-split (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "run", parents=[common], help="stamp missing proofs, upgrade pending"
    )
    verify_parser = subparsers.add_parser(
        "verify",
        parents=[common],
        help="check every proof against current manifest bytes",
    )
    verify_parser.add_argument(
        "--require-bitcoin",
        action="store_true",
        help="fail while any local proof still lacks a Bitcoin attestation",
    )
    subparsers.add_parser(
        "status", parents=[common], help="list proofs and their local state"
    )
    subparsers.add_parser(
        "guard", parents=[common], help="fail on repository changes outside ots/"
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    manifest_dir = args.manifests
    if not manifest_dir.is_absolute():
        manifest_dir = root / manifest_dir
    manifest_dir = manifest_dir.resolve()
    ots_bin = shlex.split(args.ots_bin)
    try:
        if not ots_bin:
            raise AnchorError("--ots-bin cannot be empty")
        if args.command == "run":
            return command_run(root, manifest_dir, ots_bin)
        if args.command == "verify":
            return command_verify(
                root,
                manifest_dir,
                ots_bin,
                require_bitcoin=args.require_bitcoin,
            )
        if args.command == "status":
            return command_status(root, manifest_dir, ots_bin)
        return command_guard(root)
    except (AnchorError, OSError) as exc:
        print(f"ots anchor failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
