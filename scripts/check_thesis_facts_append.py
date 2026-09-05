#!/usr/bin/env python3
# Thin shim over the receipt pin recorded in uv.lock. Any receipt upgrade
# requires a fresh byte-equivalence proof at this repo's then-current pin BEFORE
# the bump.
"""Gate every change to the thesis-facts observation ledger at a named commit.

Receipt 0.6 reads rehashed objects from the selected commit and base, checks
ancestry, and materializes the protected bytes privately for its leaf verifier.
The working tree and index are not the verdict's subject. The required full
``--commit`` OID selects that subject; the second output line comes directly
from ``AppendGateVerdict.candidate_commit`` and ``candidate_tree``. Trust anchors
remain the verifier's, and same-user writers remain inside the job's trust
boundary. Branch protection must require an up-to-date branch if a stale GitHub
test merge must be recomputed before merging.

The package reader drops every inherited ``GIT_*`` variable, creates its own
safe.directory-only global configuration, and audits its deny list at selection
and close. That list already refuses includes, hooks, filesystem monitors,
program-valued connection settings, partial clones and fsck weakening settings.
The shim delegates those refusals to the package. It retains its existing
caller policy against ``filter.*``, ``core.sparseCheckout`` and
``core.sparseCheckoutCone``: receipt does not refuse these settings because its
object reads use neither checkout filters nor the sparse index. This remaining
audit is a caller configuration policy, not an exact-checkout precondition.

The shim also retains its frozen process environment, scratch directory and
audit of its own safe.directory-only global configuration and absent system
scope. The public append entry still refuses redirecting variables before the
reader sanitizes them, and the shim's own configuration commands run before
that reader exists. Freezing both these commands and the package call keeps the
same caller guarantee. No checkout, checkout hook, index scan or worktree
registration is needed; scratch cleanup runs on success, refusal and exception.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
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
AppendGateVerdict = _receipt.AppendGateVerdict
reject_non_append_bytes = _receipt.reject_non_append_bytes

# A full object id in either of git's two hash algorithms, spelled the way git
# spells one back. Anything shorter is an abbreviation, which resolves through
# the object database and can therefore mean a different object in a different
# clone; anything else is a name, which the candidate can move.
OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")

# Every environment variable beginning with GIT_ that git(1) documents in its
# ENVIRONMENT VARIABLES section, read from the Git 2.53.0 manual page on the
# machine this was written on (`git help --man git`), plus GIT_REFERENCE_BACKEND,
# which the git on ubuntu-latest documents and this machine's does not. There are 74 of them.
#
# The shim does not drop these names one by one: it drops every variable whose
# name begins with GIT_, which is necessarily a superset of any list. The tuple
# is here so a test can hold the drop to the documentation -- if a future git
# documents a name the prefix rule would miss, that test fails rather than the
# gate quietly inheriting it.
DOCUMENTED_GIT_VARIABLES = (
    "GIT_ADVICE",
    "GIT_ALLOW_PROTOCOL",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_ASKPASS",
    "GIT_ATTR_SOURCE",
    "GIT_AUTHOR_DATE",
    "GIT_AUTHOR_EMAIL",
    "GIT_AUTHOR_NAME",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMITTER_DATE",
    "GIT_COMMITTER_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMIT_GRAPH_PARANOIA",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_SYSTEM",
    "GIT_DEFAULT_HASH",
    "GIT_DEFAULT_REF_FORMAT",
    "GIT_DIFF_OPTS",
    "GIT_DIFF_PATH_COUNTER",
    "GIT_DIFF_PATH_TOTAL",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_EDITOR",
    "GIT_EXEC_PATH",
    "GIT_EXTERNAL_DIFF",
    "GIT_EXTERNAL_DIFF_TRUST_EXIT_CODE",
    "GIT_FLUSH",
    "GIT_GLOB_PATHSPECS",
    "GIT_ICASE_PATHSPECS",
    "GIT_INDEX_FILE",
    "GIT_INDEX_VERSION",
    "GIT_LITERAL_PATHSPECS",
    "GIT_MERGE_VERBOSITY",
    "GIT_NAMESPACE",
    "GIT_NOGLOB_PATHSPECS",
    "GIT_NO_LAZY_FETCH",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_OPTIONAL_LOCKS",
    "GIT_PAGER",
    "GIT_PRINT_SHA1_ELLIPSIS",
    "GIT_PROGRESS_DELAY",
    "GIT_PROTOCOL",
    "GIT_PROTOCOL_FROM_USER",
    "GIT_REDIRECT_STDERR",
    "GIT_REDIRECT_STDIN",
    "GIT_REDIRECT_STDOUT",
    "GIT_REFERENCE_BACKEND",
    "GIT_REFLOG_ACTION",
    "GIT_REF_PARANOIA",
    "GIT_SEQUENCE_EDITOR",
    "GIT_SSH",
    "GIT_SSH_COMMAND",
    "GIT_SSH_VARIANT",
    "GIT_SSL_NO_VERIFY",
    "GIT_TERMINAL_PROMPT",
    "GIT_TRACE",
    "GIT_TRACE2",
    "GIT_TRACE2_EVENT",
    "GIT_TRACE2_PERF",
    "GIT_TRACE_CURL",
    "GIT_TRACE_CURL_NO_DATA",
    "GIT_TRACE_FSMONITOR",
    "GIT_TRACE_PACKET",
    "GIT_TRACE_PACKFILE",
    "GIT_TRACE_PACK_ACCESS",
    "GIT_TRACE_PERFORMANCE",
    "GIT_TRACE_REDACT",
    "GIT_TRACE_REFS",
    "GIT_TRACE_SETUP",
    "GIT_TRACE_SHALLOW",
    "GIT_WORK_TREE",
)

# The three variables the shim sets, and the only ones beginning with GIT_ that
# any git call in a run is allowed to see.
GATE_GIT_VARIABLES = (
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_GLOBAL",
)

# The configuration keys the shim writes into its own global file, and the
# whole of what the global scope is allowed to resolve to.
GATE_CONFIG_KEYS = ("safe.directory",)

# The two ways a run can end without a verdict of "OK", kept apart on purpose.
# "failed" is the gate's verdict about a tree it was given; "refused" is this
# shim declining to call the package because its caller configuration policy
# or frozen environment could not be established.
VERDICT_REFUSAL_PREFIX = "thesis-facts append check failed: "
REFUSAL_PREFIX = "thesis-facts append check refused: "


class ShimRefusal(RuntimeError):
    """The shim's environment or caller configuration policy was not established.

    Distinct from ``AppendError``, which is a refusal from the package verifier.
    """


def _git(
    arguments: list[str],
    *,
    cwd: pathlib.Path,
    env: dict[str, str],
) -> bytes:
    """Run one git command under the frozen environment and return its stdout.

    A non-zero exit is a refusal rather than an exception to interpret: every
    git call the shim makes establishes or audits the frozen configuration. A
    call that did not answer means that audit could not be completed.
    """

    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise ShimRefusal(
            f"git could not be run in {cwd}: {exc.strerror or exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ShimRefusal(
            f"git {' '.join(arguments)} in {cwd} exited "
            f"{completed.returncode}: {detail}"
        )
    return completed.stdout


def _scratch_root() -> pathlib.Path:
    """Create the private directory that holds everything one run writes.

    ``mkdtemp`` creates the directory with mode 0700 and does so atomically, so
    no other user has a moment in which the directory is readable. The mode is
    asserted rather than assumed, because everything the shim writes -- the
    global git configuration and its audit -- lives under it.
    """

    root = pathlib.Path(tempfile.mkdtemp(prefix="thesis-facts-gate-"))
    mode = stat.S_IMODE(os.stat(root).st_mode)
    if mode != 0o700:
        shutil.rmtree(root, ignore_errors=True)
        raise ShimRefusal(
            f"scratch directory {root} was created with mode {mode:04o}, not 0700"
        )
    return root


def _gate_environment(
    clone_root: pathlib.Path,
    scratch_root: pathlib.Path,
) -> dict[str, str]:
    """Drop all inherited GIT_* values and freeze the shim's configuration.

    Receipt constructs the same three-variable environment with its own global
    file. The outer freeze also covers this audit and the append entry's
    redirect-variable refusal, which precedes the package reader.
    """

    config = scratch_root / "gitconfig"
    config.write_bytes(b"")

    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = str(config)

    _git(
        ["config", "-f", str(config), "safe.directory", str(clone_root)],
        cwd=scratch_root,
        env=environment,
    )
    return environment


@contextlib.contextmanager
def _frozen_environment(environment: dict[str, str]) -> Iterator[None]:
    """Make ``environment`` the process environment for the enclosed block.

    The pinned receipt passes an environment to every git child it starts,
    and builds that environment out of ``os.environ`` (see
    ``_gate_environment``). Replacing ``os.environ`` for the duration is
    therefore what puts the gate's own git calls under the same frozen
    environment as the shim's, and the original is restored however the
    block ends.
    """

    saved = dict(os.environ)
    os.environ.clear()
    os.environ.update(environment)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def _config_records(payload: bytes, *, scoped: bool) -> list[tuple[str, str, str]]:
    """Parse ``git config --list -z`` output into scope, key, value triples.

    With ``-z`` git separates records with NUL and separates a record's key
    from its value with a newline; with ``--show-scope`` it emits the scope as
    its own NUL-terminated field before each record. A key declared with no
    value carries no newline, and reads back with an empty value. Git lowercases
    a key's section and variable name and leaves any subsection alone, so the
    keys here are already in the spelling the comparisons below use.
    """

    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    stride = 2 if scoped else 1
    if len(fields) % stride:
        raise ShimRefusal(
            "git config --list returned a partial record; the configuration "
            "could not be audited"
        )
    records: list[tuple[str, str, str]] = []
    for index in range(0, len(fields), stride):
        scope = fields[index].decode("utf-8", "replace") if scoped else ""
        entry = fields[index + stride - 1].decode("utf-8", "replace")
        key, _, value = entry.partition("\n")
        records.append((scope, key, value))
    return records


def _refused_config_key(key: str) -> str | None:
    """Retain only caller configuration refusals absent from receipt's audit."""

    section, _, remainder = key.partition(".")
    section = section.lower()
    variable = remainder.rpartition(".")[2].lower()
    if section == "filter":
        return "names a content filter driver"
    if section == "core" and variable in {"sparsecheckout", "sparsecheckoutcone"}:
        return "enables sparse checkout configuration excluded by caller policy"
    return None


def _audit_repository_config(
    clone_root: pathlib.Path,
    env: dict[str, str],
) -> None:
    """Audit the shim's frozen configuration and remaining caller policy.

    --no-includes exposes include keys without evaluating them; receipt refuses
    those keys itself. Local/worktree filter and sparse settings remain caller
    refusals. The global scope must equal the file the shim wrote and no system
    scope may appear under GIT_CONFIG_NOSYSTEM.
    """

    _git(["rev-parse", "--git-dir"], cwd=clone_root, env=env)

    resolved = _config_records(
        _git(
            ["config", "--list", "--show-scope", "--no-includes", "-z"],
            cwd=clone_root,
            env=env,
        ),
        scoped=True,
    )
    for scope, key, _value in resolved:
        if scope not in ("local", "worktree"):
            continue
        reason = _refused_config_key(key)
        if reason is not None:
            raise ShimRefusal(
                f"the clone at {clone_root} sets {key} in its {scope} "
                f"configuration, which {reason}"
            )

    system = sorted({key for scope, key, _ in resolved if scope == "system"})
    if system:
        raise ShimRefusal(
            "git read system configuration despite GIT_CONFIG_NOSYSTEM, "
            f"which means the frozen environment did not reach it: {system}"
        )

    config_file = pathlib.Path(env["GIT_CONFIG_GLOBAL"])
    written = [
        (key, value)
        for _scope, key, value in _config_records(
            _git(
                ["config", "-f", str(config_file), "--list", "--no-includes", "-z"],
                cwd=config_file.parent,
                env=env,
            ),
            scoped=False,
        )
    ]
    if sorted({key for key, _ in written}) != sorted(GATE_CONFIG_KEYS):
        raise ShimRefusal(
            f"the shim's global configuration at {config_file} holds "
            f"{sorted({key for key, _ in written})}, not "
            f"{sorted(GATE_CONFIG_KEYS)}"
        )
    globals_in_effect = [
        (key, value) for scope, key, value in resolved if scope == "global"
    ]
    if globals_in_effect != written:
        raise ShimRefusal(
            "the global configuration git resolved is not the file the shim "
            f"wrote: {globals_in_effect} against {written}"
        )


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
    commit: str,
    base_ref: str | None = None,
    trusted_code_root: pathlib.Path = CODE_ROOT,
    release_anchor_dir: pathlib.Path | None = None,
) -> AppendGateVerdict:
    return _receipt.verify_append_gate_verdict(
        root,
        spec=APPEND_GATE_SPEC,
        commit=commit,
        base_ref=base_ref,
        trusted_code_root=trusted_code_root,
        release_anchor_dir=release_anchor_dir,
    )


def _object_id_argument(value: str) -> str:
    if not OBJECT_ID.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not an object id: a full object id is required "
            "(40 or 64 lowercase hexadecimal characters). A symbolic ref such "
            "as a branch name, a tag or HEAD is not accepted, because the "
            "candidate can move one; an abbreviated id is not accepted, "
            "because it can name a different object in a different clone"
        )
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=CODE_ROOT,
        help=(
            "repository whose objects --commit selects "
            "(defaults to the checker's repository)"
        ),
    )
    parser.add_argument(
        "--commit",
        required=True,
        type=_object_id_argument,
        help="full object id of the commit to judge",
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
    clone_root = args.root.resolve()
    if not clone_root.is_dir():
        print(
            f"{REFUSAL_PREFIX}--root {clone_root} is not a directory",
            file=sys.stderr,
        )
        return 1

    try:
        scratch_root = _scratch_root()
        try:
            environment = _gate_environment(clone_root, scratch_root)
            _audit_repository_config(clone_root, environment)
            with _frozen_environment(environment):
                verdict = verify_append_gate(
                    clone_root,
                    commit=args.commit,
                    base_ref=args.base_ref,
                    trusted_code_root=CODE_ROOT.resolve(),
                    release_anchor_dir=args.release_anchor_dir,
                )
        finally:
            shutil.rmtree(scratch_root)
    except ShimRefusal as exc:
        print(f"{REFUSAL_PREFIX}{exc}", file=sys.stderr)
        return 1
    except AppendError as exc:
        print(f"{VERDICT_REFUSAL_PREFIX}{exc}", file=sys.stderr)
        return 1
    print(verdict.summary)
    print(f"candidate commit {verdict.candidate_commit} tree {verdict.candidate_tree}")
    return 0


__all__ = [
    "APPEND_GATE_SPEC",
    "ASSERTION_CONTENT_KEYS",
    "AppendError",
    "AppendGateSpec",
    "AppendGateVerdict",
    "CODE_ROOT",
    "DATA_SURFACE",
    "DOCUMENTED_GIT_VARIABLES",
    "GATE_CONFIG_KEYS",
    "GATE_GIT_VARIABLES",
    "GATE_SURFACE",
    "GENESIS_SUPPORT_FILES",
    "MANIFEST_RE",
    "OBJECT_ID",
    "RELEASE_MANIFEST_PREFIX",
    "ReleaseChainError",
    "ShimRefusal",
    "check_rows",
    "effective_current_rows",
    "expected_assertion_version_id",
    "main",
    "reject_non_append_bytes",
    "verify_append_gate",
]


if __name__ == "__main__":
    raise SystemExit(main())
