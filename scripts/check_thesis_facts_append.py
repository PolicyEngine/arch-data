#!/usr/bin/env python3
# Thin shim over the receipt pin recorded in uv.lock. Any receipt upgrade
# requires a fresh byte-equivalence proof at this repo's then-current pin BEFORE
# the bump.
"""Gate every change to the thesis-facts observation ledger.

The gate this shim calls states its verdict about one thing: a clean checkout
of one named commit, read once, with no concurrent writer. Findings whose
precondition is a writer to the working tree or the index during the run, or an
index, a working tree and a commit that disagree with one another, are waived
against that stated contract. A waiver like that is only honest if the program
that calls the gate actually establishes the precondition, and establishing it
is what this shim does.

Every run names the commit to judge as an argument. The shim checks that commit
out into a private directory of its own under a git environment the candidate
cannot redirect, asserts that the directory really is that commit and nothing
else, runs the gate over that directory, and removes the directory and its
registration afterwards whatever happened in between.

What that excludes:

* an index, a working tree and a commit that diverge from one another, because
  the checkout is made from the commit and is then required to be clean, with
  no untracked and no ignored file, and with every protected path's bytes equal
  to the bytes of the blob the commit names;
* a checkout the candidate prepared, because the shim makes its own rather than
  reading the one the job happens to be sitting in;
* a ref the candidate can move, because the commit is given as a full object
  id and a symbolic name is refused before any git command runs;
* a git environment the candidate can redirect, because every ``GIT_*``
  variable is dropped from the environment the git calls inherit, the system
  configuration is switched off, the global configuration is a file this shim
  writes, and the repository's own configuration is read and refused if it
  names a hook path, a filesystem monitor, a content filter or an include.

What it does not exclude: the window between the assertions and the gate's own
reads. A process that can write into the private checkout during that window
runs as the job's own user, which is the trust level of the job's own code, and
this shim claims nothing about it.

A package user who calls ``verify_append_gate`` against some other directory is
outside the contract the gate states, and outside everything the shim
establishes here.
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
    from receipt_pins import APPEND_GATE_SPEC, LEDGER_SPEC
except ModuleNotFoundError as exc:
    if exc.name != "receipt_pins":
        raise
    # The test suite copies the legacy three-script surface into temporary
    # repositories. The editable consumer tree remains the sole pin owner.
    from scripts.receipt_pins import APPEND_GATE_SPEC, LEDGER_SPEC


CODE_ROOT = pathlib.Path(__file__).resolve().parents[1]
RELEASE_MANIFEST_PREFIX = APPEND_GATE_SPEC.release_manifest_prefix
GENESIS_SUPPORT_FILES = APPEND_GATE_SPEC.genesis_support_files
GATE_SURFACE = APPEND_GATE_SPEC.gate_surface
DATA_SURFACE = APPEND_GATE_SPEC.data_surface
ASSERTION_CONTENT_KEYS = APPEND_GATE_SPEC.assertion_content_keys

AppendError = _receipt.AppendError
AppendGateSpec = _receipt.AppendGateSpec
reject_non_append_bytes = _receipt.reject_non_append_bytes

# A full object id in either of git's two hash algorithms, spelled the way git
# spells one back. Anything shorter is an abbreviation, which resolves through
# the object database and can therefore mean a different object in a different
# clone; anything else is a name, which the candidate can move.
OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")

# Every environment variable beginning with GIT_ that git(1) documents in its
# ENVIRONMENT VARIABLES section, read from the Git 2.53.0 manual page on the
# machine this was written on (`git help --man git`). There are 73 of them.
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
GATE_CONFIG_KEYS = ("safe.directory", "core.hookspath")

# Tree modes a protected path is allowed to have. Every other mode -- a symlink
# at 120000, a gitlink at 160000, a subtree at 040000 -- means the path is not
# a file whose bytes this commit fixes, so no comparison below is about it.
PROTECTED_TREE_MODES = ("100644", "100755")

# The five settings receipt spells on every one of its own working-tree reads,
# spelled on the shim's two scans for the same reason: a read that gains a
# cache in a later git is a read this program would otherwise silently begin
# to trust (peer review, round 1). ``core.fsmonitor`` is also refused by the
# configuration audit.
SCAN_SETTINGS = (
    "-c",
    "core.untrackedCache=false",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.trustctime=true",
    "-c",
    "core.checkStat=default",
    "-c",
    "feature.manyFiles=false",
)

# The two ways a run can end without a verdict of "OK", kept apart on purpose.
# "failed" is the gate's verdict about a tree it was given; "refused" is this
# shim declining to give it one, because the precondition the verdict would be
# stated against could not be established.
VERDICT_REFUSAL_PREFIX = "thesis-facts append check failed: "
REFUSAL_PREFIX = "thesis-facts append check refused: "


class ShimRefusal(RuntimeError):
    """The shim will not hand the gate a tree it cannot vouch for.

    Distinct from ``AppendError``, which is the gate's verdict about a tree it
    was handed. A ``ShimRefusal`` says that no verdict was reached, because the
    precondition the verdict would be stated against could not be established.
    """


def _git(
    arguments: list[str],
    *,
    cwd: pathlib.Path,
    env: dict[str, str],
) -> bytes:
    """Run one git command under the frozen environment and return its stdout.

    A non-zero exit is a refusal rather than an exception to interpret: every
    git call the shim makes is part of establishing the precondition, so a call
    that did not answer means the precondition was not established.
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
    global git configuration whose contents decide whether hooks run, the empty
    hook directory itself, and the checkout the gate reads -- lives under it.
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
    """Build the only environment any git in this run is allowed to see.

    The returned mapping is the caller's environment with every variable whose
    name begins with ``GIT_`` removed, and exactly three put back:

    * ``GIT_NO_REPLACE_OBJECTS=1``, so a replace ref committed into the
      repository cannot substitute one object for another underneath a read;
    * ``GIT_CONFIG_NOSYSTEM=1``, so the machine's system configuration -- which
      is not part of what this run is judging -- contributes nothing;
    * ``GIT_CONFIG_GLOBAL``, naming a file this function writes under
      ``scratch_root``. It holds ``safe.directory`` for the clone and
      ``core.hooksPath`` pointing at an empty directory created here, so no
      hook in the repository runs during the checkout. Both are written with
      ``git config -f``, so git does its own quoting of the paths.

    Dropping by prefix rather than by name is deliberate: it is a superset of
    any documented list, and ``DOCUMENTED_GIT_VARIABLES`` exists only so a test
    can check the documentation has not outgrown the rule.

    The environment is used two ways, and both are needed. The shim's own git
    calls receive it as ``env=``. The gate builds the environment for its own
    git calls out of ``os.environ`` -- on the pinned receipt,
    ``release_chain._git_environment`` returns ``os.environ`` with
    ``GIT_NO_REPLACE_OBJECTS`` set and four pathspec variables removed, and its
    docstring says in as many words that it is still not a sanitizer: the five
    redirecting variables are refused at the package's public verifier entries
    rather than dropped there, and everything else in the ambient environment
    is carried through. So ``main`` replaces ``os.environ``
    with this mapping for exactly the duration of the gate call (see
    ``_frozen_environment``); that is the control the package asks its callers
    for. Running the gate in a child process with ``env=`` would work equally
    well for the environment, but would put a process boundary between the
    gate's exception text and this program's stderr, and that text is what the
    byte-equivalence proof compares.

    ``safe.directory`` names the clone. If the clone were owned by another user
    the linked worktree's own path would not be covered, and git would refuse
    the checkout; that is a refusal, not a pass, so it fails closed.
    """

    hooks = scratch_root / "hooks"
    hooks.mkdir(mode=0o700)
    config = scratch_root / "gitconfig"
    config.write_bytes(b"")

    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = str(config)

    for key, value in (
        ("safe.directory", str(clone_root)),
        ("core.hooksPath", str(hooks)),
    ):
        _git(
            ["config", "-f", str(config), key, value],
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
    """Name the reason this configuration key may not stand, or return None.

    Four kinds of key decide what a checkout does rather than what it holds,
    and each of them is a way for a repository to run code or rewrite bytes
    during a read the gate is about to make:

    * ``core.hooksPath`` moves the hook directory, which would defeat the empty
      one the shim points git at;
    * ``core.fsmonitor`` names a program git runs to learn what changed;
    * any ``filter.*`` driver names programs git runs on a file's contents on
      the way in and on the way out;
    * any ``include`` or ``includeIf`` pulls in a file whose contents this
      audit has not read, and could set any of the above;
    * ``core.sparseCheckout`` (and ``core.sparseCheckoutCone``) makes a
      checkout materialise only the paths a patterns file in the shared git
      directory selects, marking the rest skip-worktree so ``git status``
      stays clean over a working tree that is a strict subset of the commit
      (peer review of this pull request, round 1).

    Git compares a key's section and variable case-insensitively and its
    subsection case-sensitively, which is what the folding here reproduces.
    """

    section, _, remainder = key.partition(".")
    section = section.lower()
    variable = remainder.rpartition(".")[2].lower()
    if section == "filter":
        return "names a content filter driver"
    if section.startswith("include"):
        return "pulls in configuration this audit has not read"
    if section == "core" and variable == "hookspath":
        return "moves the hook directory"
    if section == "core" and variable == "fsmonitor":
        return "names a filesystem monitor program"
    if section == "core" and variable in {"sparsecheckout", "sparsecheckoutcone"}:
        return "makes a checkout materialise a subset of the commit"
    return None


def _audit_repository_config(
    clone_root: pathlib.Path,
    env: dict[str, str],
) -> None:
    """Refuse a clone whose configuration would change what a checkout does.

    Reads the configuration git will actually use, with ``--no-includes`` so an
    include is visible as the key it is rather than as its effects, and with
    ``--show-scope`` so each entry is attributable. Entries in the repository's
    own scopes -- ``local`` and ``worktree``, both of which the candidate
    commits or the candidate's clone carries -- are refused when they name a
    hook path, a filesystem monitor, a content filter or an include, because
    each of those takes precedence over the global file the shim wrote.

    The global scope must then resolve to exactly the file the shim wrote and
    nothing else, and no ``system`` entry may appear at all -- one cannot,
    under ``GIT_CONFIG_NOSYSTEM``, so an entry claiming that scope means the
    environment did not reach git.
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
    hooks = pathlib.Path(
        next(value for key, value in written if key == "core.hookspath")
    )
    if not hooks.is_dir() or any(hooks.iterdir()):
        raise ShimRefusal(
            f"the hook directory {hooks} the shim points git at is not an "
            "existing empty directory"
        )

    globals_in_effect = [
        (key, value) for scope, key, value in resolved if scope == "global"
    ]
    if globals_in_effect != written:
        raise ShimRefusal(
            "the global configuration git resolved is not the file the shim "
            f"wrote: {globals_in_effect} against {written}"
        )


def _isolated_checkout(
    clone_root: pathlib.Path,
    scratch_root: pathlib.Path,
    oid: str,
    env: dict[str, str],
) -> pathlib.Path:
    """Check the named commit out into a directory this run owns.

    The checkout is a linked worktree of the clone, detached at the object id.
    It shares the clone's object database, so a base commit named with
    ``--base-ref`` resolves inside it, and it is a directory nothing else in
    the job has a name for.

    The object id is re-checked here even though the argument parser already
    refused anything else, because this function is the last place before a
    name reaches git and a caller that bypassed the parser must not get a
    symbolic name resolved on its behalf.
    """

    if not OBJECT_ID.fullmatch(oid):
        raise ShimRefusal(
            f"{oid!r} is not a full object id, so it will not be checked out"
        )
    checkout = scratch_root / "checkout"
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(clone_root),
                "worktree",
                "add",
                "--detach",
                str(checkout),
                oid,
            ],
            env=env,
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise ShimRefusal(
            f"git could not be run to check {oid} out: {exc.strerror or exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ShimRefusal(
            f"cannot check {oid} out in isolation from {clone_root}: {detail}"
        )
    return checkout


def _tree_entries(
    checkout: pathlib.Path,
    oid: str,
    pathspec: str,
    env: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    """List the commit's blob entries under one pathspec as mode, type, id, path.

    ``-z`` is what makes this a parse rather than a guess: git quotes unusual
    path names in its default output and emits them raw under ``-z``.
    """

    payload = _git(
        ["ls-tree", "-r", "-z", oid, "--", pathspec],
        cwd=checkout,
        env=env,
    )
    entries: list[tuple[str, str, str, str]] = []
    for record in payload.split(b"\0"):
        if not record:
            continue
        metadata, _, raw_path = record.partition(b"\t")
        mode, kind, blob = metadata.decode("utf-8", "replace").split(" ")
        entries.append((mode, kind, blob, os.fsdecode(raw_path)))
    return entries


def _protected_entries(
    checkout: pathlib.Path,
    oid: str,
    env: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    """Every entry of the commit whose bytes the gate's verdict is about.

    The two state files the chain specification names, plus everything under
    the release root, which is where the manifests, the producer signatures,
    the RFC 3161 receipts and the trust anchors live, plus everything else
    under the state files' directory, so the byte comparison covers the whole
    of the gate's data surface (``ledger/**`` and ``releases/manifests/**``)
    and not only the paths the gate reads (peer review, round 1). The prefixes
    are the chain specification's, not the data-surface globs themselves;
    ``test_the_byte_comparison_covers_the_whole_data_surface`` holds the two
    together, so a widened data surface cannot outgrow this comparison
    unnoticed. A commit that carries no
    entry at one of the two state paths is refused here: the gate would refuse
    it too, but this says which of the two is missing and says it before any
    file is read.
    """

    chain = LEDGER_SPEC
    entries: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for relative in (chain.state_relative, chain.prefix_relative):
        found = _tree_entries(checkout, oid, str(relative), env)
        if not found:
            raise ShimRefusal(f"commit {oid} carries no entry at {relative}")
        for entry in found:
            if entry[3] not in seen:
                seen.add(entry[3])
                entries.append(entry)
    for prefix in (chain.release_root_relative, chain.state_relative.parent):
        for entry in _tree_entries(checkout, oid, f"{prefix}/", env):
            if entry[3] not in seen:
                seen.add(entry[3])
                entries.append(entry)
    return entries


def _hash_working_files(
    checkout: pathlib.Path,
    paths: list[str],
    env: dict[str, str],
) -> list[str]:
    """Hash each path's bytes on disk, with no attribute conversion applied.

    ``--no-filters`` is the whole point of this call. Without it git applies
    whatever the commit's own ``.gitattributes`` asks for -- an end-of-line
    conversion, a clean filter -- and the result is by construction the blob id
    the commit names, whatever the file on disk actually holds. With it the
    answer is a hash of the bytes the gate is about to read.
    """

    hashes: list[str] = []
    for start in range(0, len(paths), 500):
        chunk = paths[start : start + 500]
        payload = _git(
            ["hash-object", "--no-filters", "--", *chunk],
            cwd=checkout,
            env=env,
        )
        lines = payload.decode("utf-8", "replace").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        if len(lines) != len(chunk):
            raise ShimRefusal(
                f"git hash-object answered for {len(lines)} of "
                f"{len(chunk)} protected paths"
            )
        hashes.extend(lines)
    return hashes


def _assert_exact_checkout(
    checkout: pathlib.Path,
    oid: str,
    env: dict[str, str],
) -> tuple[str, str]:
    """Require the checkout to be that commit and nothing besides.

    Four things are asserted about the directory as a whole: its ``HEAD`` is
    the named commit; ``git status`` reports nothing, with untracked files
    forced on from the command line so a repository setting cannot hide one and
    with submodules included; and ``git ls-files`` reports no ignored file, so
    a ``.gitignore`` the commit carries cannot conceal one either.

    Then four things are asserted about every protected path the commit names.
    Its tree mode must be a regular file's, so a symlink, a gitlink or a
    subtree standing where a file should be is refused rather than followed.
    ``os.lstat`` must agree that the path on disk is a regular file, without
    following anything. The bytes on disk must hash to the blob id the commit
    names, computed with no attribute conversion. And the owner-execute bit on
    disk must be the one the tree mode states.

    The structural three are checked for every entry in tree order first and
    the byte comparison for every entry after them, so the two passes each name
    the first path that failed them.

    Returns the commit and its tree, for the line ``main`` prints after the
    verdict.
    """

    head = (
        _git(["rev-parse", "HEAD"], cwd=checkout, env=env)
        .decode("utf-8", "replace")
        .strip()
    )
    if head != oid:
        raise ShimRefusal(
            f"the isolated checkout is at {head}, not the named commit {oid}"
        )

    status = _git(
        [
            *SCAN_SETTINGS,
            "-c",
            "status.showUntrackedFiles=all",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ],
        cwd=checkout,
        env=env,
    ).decode("utf-8", "replace")
    if status.strip():
        first = status.strip().splitlines()[0]
        raise ShimRefusal(f"the isolated checkout of {oid} is not clean: {first}")

    ignored = _git(
        [*SCAN_SETTINGS, "ls-files", "--others", "--ignored", "--exclude-standard"],
        cwd=checkout,
        env=env,
    ).decode("utf-8", "replace")
    if ignored.strip():
        first = ignored.strip().splitlines()[0]
        raise ShimRefusal(
            f"the isolated checkout of {oid} carries an ignored file: {first}"
        )
    # The checkout must be the whole commit, not a selection of it: a sparse
    # checkout leaves the omitted entries in the index marked skip-worktree,
    # which a clean ``status`` does not reveal (peer review, round 1). Every
    # index entry must be an ordinary tracked file, and there must be exactly
    # as many of them as the commit has entries.
    tagged = _git(
        [*SCAN_SETTINGS, "ls-files", "-v", "-z"],
        cwd=checkout,
        env=env,
    )
    index_entries = 0
    for record in tagged.split(b"\0"):
        if not record:
            continue
        index_entries += 1
        tag = record[:1]
        if tag != b"H":
            path = os.fsdecode(record[2:])
            reason = {
                b"S": "skip-worktree",
                b"h": "assume-unchanged",
                b"M": "unmerged",
            }.get(tag, f"tagged {tag.decode('ascii', 'replace')!r}")
            raise ShimRefusal(
                f"the isolated checkout of {oid} has an index entry that is "
                f"not an ordinary tracked file ({reason}): {path}"
            )
    tree_entries = sum(
        1
        for record in _git(["ls-tree", "-r", "-z", oid], cwd=checkout, env=env).split(
            b"\0"
        )
        if record
    )
    if index_entries != tree_entries:
        raise ShimRefusal(
            f"the isolated checkout of {oid} indexes {index_entries} entries "
            f"where the commit has {tree_entries}"
        )

    entries = _protected_entries(checkout, oid, env)
    for mode, _kind, _blob, relative in entries:
        if mode not in PROTECTED_TREE_MODES:
            raise ShimRefusal(
                f"commit {oid} carries the protected path {relative} with "
                f"tree mode {mode}; a protected path must be a regular file "
                f"({' or '.join(PROTECTED_TREE_MODES)})"
            )
        target = checkout / relative
        try:
            info = os.lstat(target)
        except OSError as exc:
            raise ShimRefusal(
                f"the protected path {relative} cannot be inspected in the "
                f"isolated checkout of {oid}: {exc.strerror}"
            ) from exc
        if not stat.S_ISREG(info.st_mode):
            raise ShimRefusal(
                f"the protected path {relative} is not a regular file in the "
                f"isolated checkout of {oid}"
            )
        executable = bool(info.st_mode & stat.S_IXUSR)
        if executable != (mode == "100755"):
            raise ShimRefusal(
                f"the protected path {relative} is "
                f"{'executable' if executable else 'not executable'} in the "
                f"isolated checkout of {oid}, against tree mode {mode}"
            )

    hashes = _hash_working_files(checkout, [entry[3] for entry in entries], env)
    for (_mode, _kind, blob, relative), found in zip(entries, hashes, strict=True):
        if found != blob:
            raise ShimRefusal(
                f"the protected path {relative} holds bytes hashing to "
                f"{found} in the isolated checkout of {oid}, against the "
                f"{blob} the commit names"
            )

    tree = _git(["rev-parse", "HEAD^{tree}"], cwd=checkout, env=env)
    return head, tree.decode("utf-8", "replace").strip()


def _worktree_removed(
    clone_root: pathlib.Path,
    checkout: pathlib.Path,
    env: dict[str, str],
) -> bool:
    """Try once to deregister this checkout, and report whether git did."""

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(clone_root),
                "worktree",
                "remove",
                "--force",
                str(checkout),
            ],
            env=env,
            check=False,
            capture_output=True,
        )
    except OSError:
        # Cleanup runs in a finally, so it never raises over whatever brought
        # the run here; a failure to remove is reported at the end instead.
        return False
    return completed.returncode == 0


def _remove_checkout(
    clone_root: pathlib.Path,
    scratch_root: pathlib.Path,
    checkout: pathlib.Path | None,
    env: dict[str, str] | None,
) -> None:
    """Remove this run's checkout and everything else it wrote.

    Named by path, so it removes this checkout and no other. ``git worktree
    prune`` is never used and must never be: it deregisters every prunable
    worktree of the repository, including registrations that belong to
    somebody else's work in the same clone.

    An add that failed part-way leaves no registration -- git validates the
    commit before it writes one -- so the ordinary case after a failure is that
    there is nothing to deregister and only the directory to delete. The order
    here handles both: deregister, delete the directory tree, and if the first
    attempt failed try once more, because git accepts the path of a
    registration whose directory has already gone. Only if that also fails does
    anything get printed, and then it names the directory and the command that
    clears it.
    """

    removed = True
    if checkout is not None and env is not None:
        removed = _worktree_removed(clone_root, checkout, env)
    shutil.rmtree(scratch_root, ignore_errors=True)
    if not removed and checkout is not None and env is not None:
        removed = _worktree_removed(clone_root, checkout, env)
    if not removed:
        print(
            "thesis-facts append check warning: the isolated checkout "
            f"registration at {checkout} could not be removed; clear it with "
            f"git -C {clone_root} worktree remove --force {checkout}",
            file=sys.stderr,
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
            "clone in which --commit is resolved and checked out "
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

    scratch_root: pathlib.Path | None = None
    environment: dict[str, str] | None = None
    checkout: pathlib.Path | None = None
    try:
        scratch_root = _scratch_root()
        try:
            environment = _gate_environment(clone_root, scratch_root)
            _audit_repository_config(clone_root, environment)
            checkout = _isolated_checkout(
                clone_root,
                scratch_root,
                args.commit,
                environment,
            )
            commit, tree = _assert_exact_checkout(
                checkout,
                args.commit,
                environment,
            )
            with _frozen_environment(environment):
                summary = verify_append_gate(
                    checkout,
                    base_ref=args.base_ref,
                    trusted_code_root=CODE_ROOT.resolve(),
                    release_anchor_dir=args.release_anchor_dir,
                )
        finally:
            _remove_checkout(clone_root, scratch_root, checkout, environment)
    except ShimRefusal as exc:
        print(f"{REFUSAL_PREFIX}{exc}", file=sys.stderr)
        return 1
    except AppendError as exc:
        print(f"{VERDICT_REFUSAL_PREFIX}{exc}", file=sys.stderr)
        return 1
    print(summary)
    print(f"candidate commit {commit} tree {tree}")
    return 0


__all__ = [
    "APPEND_GATE_SPEC",
    "ASSERTION_CONTENT_KEYS",
    "AppendError",
    "AppendGateSpec",
    "CODE_ROOT",
    "DATA_SURFACE",
    "DOCUMENTED_GIT_VARIABLES",
    "GATE_CONFIG_KEYS",
    "GATE_GIT_VARIABLES",
    "GATE_SURFACE",
    "GENESIS_SUPPORT_FILES",
    "MANIFEST_RE",
    "OBJECT_ID",
    "PROTECTED_TREE_MODES",
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
