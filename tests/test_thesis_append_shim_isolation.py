"""What the append-gate shim establishes before the gate reaches a verdict.

The gate states its verdict about a clean checkout of one named commit, read
once, with no concurrent writer. The shim is the part that makes that true: it
checks the named commit out itself, under a git environment the candidate
cannot redirect, and refuses rather than reaching a verdict when the checkout is
not exactly that commit.

Every case here is one way a repository could have handed the old shim a
directory that was not the commit it claimed to be, run code during the
checkout, or made the bytes on disk differ from the bytes the commit fixes. Each
runs the shim in a subprocess and asserts what it printed and what it exited
with, so the refusal text and the exit code are the assertions rather than an
internal state.

Some cases need something to happen between the checkout and the assertion --
a writer, a permission change -- which is a window no repository setting can
open on its own, because the shim disables hooks and owns the directory. Those
cases run the shim through a small driver that imports the module and wraps one
function, and each says in its own docstring what it wrapped and why the thing
it simulates has no other construction. Everything else runs the script itself.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SHIM_SCRIPTS = ROOT / "scripts"
SHIM = SHIM_SCRIPTS / "check_thesis_facts_append.py"

RELEASE_FILE_SUFFIXES = (
    ".json",
    ".producer.sig",
    ".freetsa.tsr",
    ".digicert.tsr",
)
LEDGER_RELATIVE = "ledger/official_observations.jsonl"

REFUSED = "thesis-facts append check refused: "
FAILED = "thesis-facts append check failed: "

CANDIDATE_LINE = re.compile(
    r"(?m)^candidate commit (?P<commit>[0-9a-f]{40,64}) "
    r"tree (?P<tree>[0-9a-f]{40,64})$"
)

# A commit id of the right shape that no repository holds.
ABSENT_OBJECT_ID = "0" * 40


def _release_manifests() -> list[pathlib.Path]:
    return sorted((ROOT / "releases" / "manifests").glob("[0-9]" * 4 + "-*.json"))


_HEAD_RELEASE = json.loads(_release_manifests()[-1].read_text(encoding="utf-8"))
NEW_RELEASE_STEM = _release_manifests()[-1].stem
RELEASE_INDEX = int(_HEAD_RELEASE["releaseIndex"])
CANDIDATE_LINE_COUNT = int(_HEAD_RELEASE["state"]["lineCount"])
BASE_LINE_COUNT = int(_HEAD_RELEASE["append"]["previousLineCount"])
APPENDED_ROW_COUNT = int(_HEAD_RELEASE["append"]["appendedRowCount"])
PREFIX_LINE_COUNT = int(
    json.loads((ROOT / "ledger" / "immutable_prefix.json").read_text(encoding="utf-8"))[
        "prefixLineCount"
    ]
)
APPEND_GATE_OK = (
    f"thesis-facts append check OK: {CANDIDATE_LINE_COUNT} rows, "
    f"immutable prefix {PREFIX_LINE_COUNT}, "
    f"+{APPENDED_ROW_COUNT} appended vs base, release {RELEASE_INDEX}"
)


def _git(root: pathlib.Path, *arguments: str) -> str:
    """Run git in a fixture repository, ignoring the machine's own settings."""

    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _copy_custody_tree(destination: pathlib.Path) -> pathlib.Path:
    root = destination / "root"
    shutil.copytree(ROOT / "ledger", root / "ledger")
    shutil.copytree(ROOT / "releases", root / "releases")
    return root


def _initialize(root: pathlib.Path) -> None:
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "shim-isolation@example.invalid")
    _git(root, "config", "user.name", "Shim Isolation")


def _commit(root: pathlib.Path, message: str, index_mutation=None) -> str:
    """Commit the working tree, and any entry only the index can carry.

    ``index_mutation`` runs between the add and the commit, because an entry
    with no file behind it -- a gitlink, say -- would be staged for deletion by
    the add if it were written first.
    """

    _git(root, "add", "-A")
    if index_mutation is not None:
        index_mutation(root)
    _git(root, "commit", "--quiet", "--allow-empty", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _release_file(root: pathlib.Path, suffix: str) -> pathlib.Path:
    return root / "releases" / "manifests" / f"{NEW_RELEASE_STEM}{suffix}"


def _replay_latest_release(
    destination: pathlib.Path,
    *,
    prepare=None,
    mutate=None,
    mutate_index=None,
) -> tuple[pathlib.Path, str, str]:
    """Build the prior release as base and the witnessed append as candidate.

    ``prepare`` runs before the base commit, so whatever it writes is in both
    commits and is therefore not part of the diff the gate judges. ``mutate``
    runs after the release files are restored and before the candidate commit,
    so whatever it writes is part of the candidate and of nothing else.
    ``mutate_index`` does the same for an entry that exists only in the index.
    """

    root = _copy_custody_tree(destination)
    ledger = root / LEDGER_RELATIVE
    full_ledger = ledger.read_bytes()
    rows = full_ledger.splitlines(keepends=True)
    assert len(rows) == CANDIDATE_LINE_COUNT
    ledger.write_bytes(b"".join(rows[:BASE_LINE_COUNT]))
    for suffix in RELEASE_FILE_SUFFIXES:
        _release_file(root, suffix).unlink()

    _initialize(root)
    if prepare is not None:
        prepare(root)
    base = _commit(root, "release base")

    ledger.write_bytes(full_ledger)
    for suffix in RELEASE_FILE_SUFFIXES:
        shutil.copyfile(_release_file(ROOT, suffix), _release_file(root, suffix))
    if mutate is not None:
        mutate(root)
    return root, base, _commit(root, "witnessed append", mutate_index)


def _replay_current_state(destination: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Commit the repository's present custody tree as the base to diff against.

    Used by the cases that ask what the gate says about a change made on top of
    the state as it stands, rather than about the last witnessed release.
    """

    root = _copy_custody_tree(destination)
    _initialize(root)
    return root, _commit(root, "current state")


DRIVER = """\
import subprocess
import sys

sys.path.insert(0, {scripts!r})

import check_thesis_facts_append as shim  # noqa: E402

{injection}

raise SystemExit(shim.main())
"""


def _run_shim(
    clone: pathlib.Path,
    *,
    commit: str,
    base_ref: str | None = None,
    temporary_root: pathlib.Path,
    injection: str | None = None,
    workspace: pathlib.Path | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the shim over ``clone`` with its scratch directories under our eye.

    ``temporary_root`` becomes the child's ``TMPDIR``, so the private directory
    the shim creates lands somewhere a test can look at afterwards and assert
    that nothing was left behind.
    """

    temporary_root.mkdir(parents=True, exist_ok=True)
    if injection is None:
        script = SHIM
    else:
        assert workspace is not None
        workspace.mkdir(parents=True, exist_ok=True)
        script = workspace / "driver.py"
        script.write_text(
            DRIVER.format(scripts=str(SHIM_SCRIPTS), injection=injection),
            encoding="utf-8",
        )

    child = os.environ.copy() if environment is None else dict(environment)
    child["TMPDIR"] = str(temporary_root)
    command = [
        sys.executable,
        str(script),
        "--root",
        str(clone),
        "--commit",
        commit,
    ]
    if base_ref is not None:
        command.extend(["--base-ref", base_ref])
    return subprocess.run(
        command,
        cwd=clone,
        env=child,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_nothing_left_behind(
    clone: pathlib.Path, temporary_root: pathlib.Path
) -> None:
    """No scratch directory survives, and no registration names one."""

    leftovers = sorted(temporary_root.glob("thesis-facts-gate-*"))
    assert leftovers == [], leftovers
    listing = _git(clone, "worktree", "list", "--porcelain")
    assert "thesis-facts-gate-" not in listing, listing


def test_a_checkout_of_another_commit_is_refused(tmp_path):
    """HEAD must be the commit that was named, not one near it.

    The writer simulated here is a checkout that answered for a different
    commit. There is no repository setting that produces it -- the shim passes
    the object id to `git worktree add` itself -- so the driver wraps
    `_isolated_checkout` and has it check out the candidate's parent, which is
    the closest thing to a checkout that looks right and is not.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    parent = _git(clone, "rev-parse", f"{candidate}^")
    injection = """\
_real_checkout = shim._isolated_checkout


def _checkout_the_parent(clone_root, scratch_root, oid, env):
    parent = subprocess.run(
        ["git", "-C", str(clone_root), "rev-parse", oid + "^"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return _real_checkout(clone_root, scratch_root, parent, env)


shim._isolated_checkout = _checkout_the_parent
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert REFUSED in completed.stderr
    assert (
        f"the isolated checkout is at {parent}, not the named commit "
        f"{candidate}" in completed.stderr
    )
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_a_modified_tracked_file_in_the_checkout_is_refused(tmp_path):
    """A tracked file written after the checkout is refused.

    A `post-checkout` hook is the realistic writer, and the shim disables hooks
    by construction, which is proved separately. So the writer here is the
    driver: it wraps `_isolated_checkout` and appends a byte to the ledger in
    the directory the real function returned, which is exactly what a hook
    would have had the opportunity to do.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    injection = """\
_real_checkout = shim._isolated_checkout


def _write_into_the_checkout(clone_root, scratch_root, oid, env):
    checkout = _real_checkout(clone_root, scratch_root, oid, env)
    ledger = checkout / "ledger" / "official_observations.jsonl"
    ledger.write_bytes(ledger.read_bytes() + b"{}\\n")
    return checkout


shim._isolated_checkout = _write_into_the_checkout
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert f"{REFUSED}the isolated checkout of {candidate} is not clean" in (
        completed.stderr
    )
    assert LEDGER_RELATIVE in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_an_untracked_file_is_refused_though_the_clone_hides_untracked_files(
    tmp_path,
):
    """`status.showUntrackedFiles=no` in the clone does not hide the file.

    The setting is the repository's, and it is the kind of setting the shim
    deliberately does not refuse in the configuration audit, because it changes
    what a report says rather than what a checkout does. It is answered
    instead: the shim forces `status.showUntrackedFiles=all` on the command
    line, where it outranks any configured value, and passes
    `--untracked-files=all` as well.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    _git(clone, "config", "status.showUntrackedFiles", "no")
    injection = """\
_real_checkout = shim._isolated_checkout


def _leave_an_untracked_file(clone_root, scratch_root, oid, env):
    checkout = _real_checkout(clone_root, scratch_root, oid, env)
    (checkout / "unexpected.txt").write_text("left behind\\n", encoding="utf-8")
    return checkout


shim._isolated_checkout = _leave_an_untracked_file
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert f"{REFUSED}the isolated checkout of {candidate} is not clean" in (
        completed.stderr
    )
    assert "?? unexpected.txt" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_an_ignored_file_is_refused(tmp_path):
    """A file the commit's own .gitignore hides is still a file in the tree.

    `git status` says nothing about an ignored file however untracked files are
    configured, so the clean-tree assertion cannot see one. The separate
    `ls-files --others --ignored` is what does.
    """

    def _ignore_a_directory(root: pathlib.Path) -> None:
        (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

    clone, base, candidate = _replay_latest_release(
        tmp_path, prepare=_ignore_a_directory
    )
    injection = """\
_real_checkout = shim._isolated_checkout


def _leave_an_ignored_file(clone_root, scratch_root, oid, env):
    checkout = _real_checkout(clone_root, scratch_root, oid, env)
    hidden = checkout / "workspace"
    hidden.mkdir()
    (hidden / "smuggled.txt").write_text("ignored\\n", encoding="utf-8")
    return checkout


shim._isolated_checkout = _leave_an_ignored_file
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert f"{REFUSED}the isolated checkout of {candidate} carries an ignored " in (
        completed.stderr
    )
    assert "workspace/smuggled.txt" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_an_attribute_that_rewrites_the_checkout_bytes_is_refused(tmp_path):
    """Committed attributes cannot make the gate read bytes the commit fixes.

    A `text eol=crlf` attribute over an LF blob is the whole attack in one
    line: the checkout writes CRLF, `git status` stays clean because git
    normalises on the way back in, and a content hash taken the ordinary way
    reproduces the blob id by construction whatever is on disk. Hashing with
    `--no-filters` is what makes the comparison a comparison, and this is the
    case that fails without it.

    A `filter.*` driver would do the same thing with a program instead of a
    conversion; the configuration audit refuses that one earlier, and its own
    case is below.
    """

    def _convert_the_ledger_to_crlf(root: pathlib.Path) -> None:
        (root / ".gitattributes").write_text(
            f"{LEDGER_RELATIVE} text eol=crlf\n", encoding="utf-8"
        )

    clone, base, candidate = _replay_latest_release(
        tmp_path, prepare=_convert_the_ledger_to_crlf
    )
    blob = _git(clone, "rev-parse", f"{candidate}:{LEDGER_RELATIVE}")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert f"{REFUSED}the protected path {LEDGER_RELATIVE} holds bytes hashing" in (
        completed.stderr
    )
    assert f"against the {blob} the commit names" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_an_execute_bit_that_disagrees_with_the_tree_mode_is_refused(tmp_path):
    """The owner-execute bit on disk must be the one the commit states.

    `core.fileMode=false` tells git to stop comparing the bit, so `git status`
    reports a clean tree while the file's permissions are not the ones the
    commit records. That is why this is a separate assertion and not something
    the clean-tree check already covers: under that setting the clean-tree check
    cannot see it. The clearing of the bit itself is done by the driver, because
    with the setting in place nothing in the repository has to do it for the
    tree to still look clean.
    """

    clone, base, candidate = _replay_latest_release(
        tmp_path,
        prepare=lambda root: (root / LEDGER_RELATIVE).chmod(0o755),
    )
    assert _git(clone, "ls-tree", candidate, "--", LEDGER_RELATIVE).startswith("100755")
    _git(clone, "config", "core.fileMode", "false")
    injection = """\
_real_checkout = shim._isolated_checkout


def _clear_the_execute_bit(clone_root, scratch_root, oid, env):
    checkout = _real_checkout(clone_root, scratch_root, oid, env)
    (checkout / "ledger" / "official_observations.jsonl").chmod(0o644)
    return checkout


shim._isolated_checkout = _clear_the_execute_bit
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert (
        f"{REFUSED}the protected path {LEDGER_RELATIVE} is not executable"
        in completed.stderr
    )
    assert "against tree mode 100755" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def _commit_a_symlink_under_releases(root: pathlib.Path) -> None:
    link = root / "releases" / "manifests" / "0000-shortcut.json"
    link.symlink_to(pathlib.Path("..") / ".." / "ledger" / "immutable_prefix.json")


def _stage_a_gitlink_under_releases(root: pathlib.Path) -> None:
    """Record a submodule boundary under the release root, in the index only.

    A gitlink names a commit in another repository. Whatever a checkout puts at
    that path belongs to that repository and is no part of this commit, so
    nothing under it can be compared against anything this commit fixes.
    """

    head = _git(root, "rev-parse", "HEAD")
    _git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{head},releases/manifests/0000-elsewhere",
    )


@pytest.mark.parametrize(
    ("case", "mutate", "mutate_index", "path", "mode"),
    [
        (
            "symlink",
            _commit_a_symlink_under_releases,
            None,
            "releases/manifests/0000-shortcut.json",
            "120000",
        ),
        (
            "gitlink",
            None,
            _stage_a_gitlink_under_releases,
            "releases/manifests/0000-elsewhere",
            "160000",
        ),
    ],
)
def test_a_protected_path_that_is_not_a_file_is_refused(
    tmp_path, case, mutate, mutate_index, path, mode
):
    """A link and a submodule boundary are both refused on their tree mode.

    Neither is a path whose bytes this commit fixes: a link is a name for
    somewhere else, and a gitlink is a name for another repository whose
    contents this commit does not carry. They are refused rather than followed.

    The refusal is the shim's and not the gate's -- the message says "refused"
    and not "failed" -- so the mode was read before any verdict was reached
    about what the tree holds.
    """

    clone, base, candidate = _replay_latest_release(
        tmp_path / case, mutate=mutate, mutate_index=mutate_index
    )

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert FAILED not in completed.stderr
    assert REFUSED in completed.stderr
    assert path in completed.stderr
    assert f"tree mode {mode}" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_a_symlink_materialised_as_a_file_is_still_refused(tmp_path):
    """`core.symlinks=false` turns the link into a regular file, and it is
    still refused.

    Under that setting git writes the link's target text into an ordinary file,
    which passes every test that asks what the thing on disk is. The tree mode
    is what says the commit does not fix that file's bytes, and the tree mode is
    what the refusal names.
    """

    clone, base, candidate = _replay_latest_release(
        tmp_path, mutate=_commit_a_symlink_under_releases
    )
    _git(clone, "config", "core.symlinks", "false")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert REFUSED in completed.stderr
    assert "tree mode 120000" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_a_checkout_that_never_happened_leaves_no_registration(tmp_path):
    """An object id nothing holds fails the add, and leaves nothing behind.

    git validates the commit before it writes a registration, so the ordinary
    outcome is that there is nothing to deregister and only a directory to
    delete. The assertion is that both are true afterwards, which is what the
    `finally` is for.
    """

    clone, _base, _candidate = _replay_latest_release(tmp_path)
    before = _git(clone, "worktree", "list", "--porcelain")

    completed = _run_shim(
        clone,
        commit=ABSENT_OBJECT_ID,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert f"{REFUSED}cannot check {ABSENT_OBJECT_ID} out in isolation" in (
        completed.stderr
    )
    assert _git(clone, "worktree", "list", "--porcelain") == before
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


# Braces are everywhere in this one, so the recording path is spliced in by
# name rather than by str.format.
ENVIRONMENT_SPY = """\
import json
import os
import pathlib
import sys as _sys

RECORDING = __RECORDING__

import receipt.append_gate as gate  # noqa: E402

_real_run = subprocess.run
_records = []


def _spy(*args, **kwargs):
    argv = args[0] if args else kwargs.get("args")
    given = kwargs.get("env")
    # A call that passes no environment gets the process's, so what the child
    # actually receives is os.environ at the moment of the call either way.
    effective = dict(given) if given is not None else dict(os.environ)
    _records.append(
        {
            "argv": [str(item) for item in argv],
            "caller": _sys._getframe(1).f_globals.get("__name__", "?"),
            "explicit": given is not None,
            "git": {
                name: value
                for name, value in effective.items()
                if name.startswith("GIT_")
            },
        }
    )
    return _real_run(*args, **kwargs)


subprocess.run = _spy
gate.subprocess.run = _spy


def _record_and_exit(code):
    pathlib.Path(RECORDING).write_text(json.dumps(_records), encoding="utf-8")
    return code


_real_main = shim.main
shim.main = lambda: _record_and_exit(_real_main())
"""


def test_no_inherited_git_variable_reaches_any_child(tmp_path):
    """Every git the run starts sees exactly three GIT_ variables.

    The caller's environment is loaded with every GIT_ name git(1) documents,
    plus GIT_CONFIG_COUNT, which git-config(1) documents and git(1) does not --
    the shim drops by prefix rather than by list, so a name outside the list is
    dropped too.

    Both halves of the run are checked, told apart by which module made the
    call. The shim passes its environment explicitly. The gate builds its own
    from ``os.environ`` and says in as many words that it is not a sanitizer and
    that a caller which does not control the environment it invokes the package
    in has a problem outside that function's scope. Controlling ``os.environ``
    for the duration of the gate call is how the shim answers that, and this is
    the test that it works: whichever module made the call, and whether or not
    an environment was passed, what the child receives carries exactly the three
    variables and none of the hostile values.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    recording = tmp_path / "subprocess-environments.json"

    module = SHIM.read_text(encoding="utf-8")
    documented = re.search(r"There are (\d+) of them\.", module)
    assert documented is not None, "the tuple's comment no longer gives a count"

    hostile = os.environ.copy()
    for name in _documented_git_variables():
        hostile[name] = f"hostile-{name}"
    hostile["GIT_CONFIG_COUNT"] = "1"
    hostile["GIT_CONFIG_KEY_0"] = "core.hooksPath"
    hostile["GIT_CONFIG_VALUE_0"] = str(tmp_path / "hostile-hooks")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=ENVIRONMENT_SPY.replace("__RECORDING__", repr(str(recording))),
        workspace=tmp_path / "driver",
        environment=hostile,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    records = json.loads(recording.read_text(encoding="utf-8"))
    git_calls = [record for record in records if record["argv"][0] == "git"]
    assert git_calls, records

    by_shim = [
        record
        for record in git_calls
        if record["caller"] == "check_thesis_facts_append"
    ]
    by_gate = [
        record for record in git_calls if record["caller"].startswith("receipt.")
    ]
    assert by_shim, [record["caller"] for record in git_calls]
    assert by_gate, [record["caller"] for record in git_calls]

    for record in git_calls:
        assert set(record["git"]) == {
            "GIT_NO_REPLACE_OBJECTS",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
        }, record
        assert record["git"]["GIT_NO_REPLACE_OBJECTS"] == "1"
        assert record["git"]["GIT_CONFIG_NOSYSTEM"] == "1"
        assert not record["git"]["GIT_CONFIG_GLOBAL"].startswith("hostile-")


def _documented_git_variables() -> tuple[str, ...]:
    sys.path.insert(0, str(SHIM_SCRIPTS))
    from check_thesis_facts_append import DOCUMENTED_GIT_VARIABLES

    return DOCUMENTED_GIT_VARIABLES


def test_the_documented_variable_list_is_not_narrower_than_the_drop():
    """The prefix rule covers every name the tuple records, and the count holds.

    The shim drops by prefix, so this is a check on the documentation rather
    than on the code: if a future git documents a GIT_ variable the prefix rule
    would miss, there is no such name and this says so; if the tuple and the
    comment beside it disagree about how many names it holds, that is a stale
    comment and this says that too.
    """

    documented = _documented_git_variables()
    assert len(set(documented)) == len(documented)
    assert sorted(documented) == list(documented)
    for name in documented:
        assert name.startswith("GIT_"), name

    module = SHIM.read_text(encoding="utf-8")
    stated = re.search(r"There are (\d+) of them\.", module)
    assert stated is not None
    assert int(stated.group(1)) == len(documented)


def test_a_post_checkout_hook_in_the_clone_does_not_run(tmp_path):
    """`git worktree add` runs post-checkout, and here it does not.

    The hook is a real one, installed where git looks by default. It is not
    reached because the shim points `core.hooksPath` at an empty directory it
    made, from a global configuration file the repository's own configuration
    is separately checked for not overriding.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    marker = tmp_path / "the-hook-ran"
    hook = clone / ".git" / "hooks" / "post-checkout"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(
        f"#!/bin/sh\nprintf 'ran' > {marker}\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not marker.exists()
    assert APPEND_GATE_OK in completed.stdout
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_an_unrelated_prunable_worktree_keeps_its_registration(tmp_path):
    """Cleanup removes this run's checkout by name and nothing else.

    `git worktree prune` would have removed the other registration too -- the
    second half of this test shows that it does -- which is why the shim never
    calls it. A worktree whose directory has gone is prunable, and a repository
    in which other work is going on can hold several at any moment.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    other = tmp_path / "somebody-elses-worktree"
    _git(clone, "worktree", "add", "--detach", str(other), base)
    shutil.rmtree(other)
    assert str(other) in _git(clone, "worktree", "list", "--porcelain")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert str(other) in _git(clone, "worktree", "list", "--porcelain")
    _assert_nothing_left_behind(clone, tmp_path / "tmp")

    _git(clone, "worktree", "prune")
    assert str(other) not in _git(clone, "worktree", "list", "--porcelain")


@pytest.mark.parametrize(
    ("key", "value", "reported"),
    [
        ("filter.smuggle.clean", "cat", "filter.smuggle.clean"),
        ("core.hooksPath", "hooks", "core.hookspath"),
        ("core.fsmonitor", "true", "core.fsmonitor"),
        ("include.path", "extra-config", "include.path"),
    ],
)
def test_a_clone_that_redirects_the_checkout_is_refused_before_it_happens(
    tmp_path, key, value, reported
):
    """Four repository settings decide what a checkout does, and all are refused.

    Each of them outranks the global file the shim wrote: a hook path moves the
    directory the shim emptied, a filesystem monitor and a content filter each
    name a program git runs, and an include pulls in a file this audit has not
    read and which could set any of the other three. The audit runs before the
    checkout, so nothing has been created when the refusal is made.
    """

    clone, _base, candidate = _replay_latest_release(tmp_path)
    _git(clone, "config", key, value)
    before = _git(clone, "worktree", "list", "--porcelain")

    completed = _run_shim(
        clone,
        commit=candidate,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert REFUSED in completed.stderr
    assert f"sets {reported} in its local configuration" in completed.stderr
    assert _git(clone, "worktree", "list", "--porcelain") == before
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


@pytest.mark.parametrize(
    "spelling",
    ["HEAD", "main", "codex/thesis-ledger-facts", "3a5ef7e", "A" * 40, ""],
)
def test_a_commit_that_is_not_a_full_object_id_is_refused_by_the_parser(
    tmp_path, spelling
):
    """A name the candidate can move, or an id short enough to be ambiguous.

    The parser refuses these, so the refusal costs nothing -- no directory is
    made, no git command runs -- and it is argparse's own exit status 2 rather
    than the gate's 1, because it is a usage error and not a verdict.
    """

    completed = subprocess.run(
        [
            sys.executable,
            str(SHIM),
            "--root",
            str(tmp_path),
            "--commit",
            spelling,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert "argument --commit" in completed.stderr
    assert "a full object id is required" in completed.stderr


def test_an_exception_after_the_checkout_still_removes_everything(tmp_path):
    """The cleanup is in a `finally`, so it does not need the run to succeed.

    The gate is replaced by something that raises, which stands for every way
    the run can end that is neither a verdict nor a refusal.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    injection = """\
def _explode(*args, **kwargs):
    raise RuntimeError("the gate did not get to finish")


shim.verify_append_gate = _explode
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode != 0
    assert "RuntimeError: the gate did not get to finish" in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_the_witnessed_release_passes_and_names_its_commit(tmp_path):
    """The accepting case, end to end, over a committed replay of the last
    release.

    stdout is the gate's own summary line and then one line the shim adds,
    naming the commit it checked out and that commit's tree.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    tree = _git(clone, "rev-parse", f"{candidate}^{{tree}}")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert completed.stdout == (
        f"{APPEND_GATE_OK}\ncandidate commit {candidate} tree {tree}\n"
    )
    match = CANDIDATE_LINE.search(completed.stdout)
    assert match is not None
    assert match.group("commit") == candidate
    assert match.group("tree") == tree
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def _rewrite_the_first_unfrozen_row(root: pathlib.Path) -> None:
    ledger = root / LEDGER_RELATIVE
    rows = ledger.read_bytes().splitlines(keepends=True)
    rows[PREFIX_LINE_COUNT] = b" " + rows[PREFIX_LINE_COUNT]
    ledger.write_bytes(b"".join(rows))


def _drop_the_last_row(root: pathlib.Path) -> None:
    ledger = root / LEDGER_RELATIVE
    rows = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(b"".join(rows[:-1]))


@pytest.mark.parametrize(
    ("case", "mutation", "marker"),
    [
        (
            "rewrite",
            _rewrite_the_first_unfrozen_row,
            f"change rewrites existing line {PREFIX_LINE_COUNT + 1}",
        ),
        (
            "truncate",
            _drop_the_last_row,
            (
                f"change truncates the ledger: {CANDIDATE_LINE_COUNT} -> "
                f"{CANDIDATE_LINE_COUNT - 1} rows"
            ),
        ),
    ],
)
def test_the_append_only_diff_is_still_enforced_end_to_end(
    tmp_path, case, mutation, marker
):
    """A rewritten historical line and a truncated ledger, through the shim.

    These two outcomes used to be asserted by calling the gate's append-only
    check directly with a list of lines. They are asserted here the way the
    gate is actually used: two commits in a repository, the second judged
    against the first, with the refusal read off the process's stderr. The
    refusal is the gate's, spelled "failed", which is also how these cases say
    that the shim handed the gate a tree rather than refusing it one.
    """

    clone, base = _replay_current_state(tmp_path / case)
    mutation(clone)
    candidate = _commit(clone, f"candidate: {case}")

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert completed.stdout == ""
    assert f"{FAILED}" in completed.stderr
    assert marker in completed.stderr
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_a_true_append_is_accepted_end_to_end(tmp_path):
    """And the third outcome: a real append is accepted.

    The append the old unit test accepted was any whole line added to the end.
    End to end an append also has to carry its witnessed release, so what is
    accepted here is the last real release of this ledger, replayed against the
    one before it.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)

    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"+{APPENDED_ROW_COUNT} appended vs base" in completed.stdout
    _assert_nothing_left_behind(clone, tmp_path / "tmp")


def test_the_scratch_directory_is_private_to_the_run(tmp_path):
    """The private directory is created 0700, and the shim asserts that it was.

    Everything the run writes lives under it: the global configuration file
    whose contents decide whether hooks run, the empty hook directory itself,
    and the checkout the gate reads. The assertion here is on the other side of
    the same fact -- that the shim records the mode it requires and would refuse
    a directory that did not have it.
    """

    clone, base, candidate = _replay_latest_release(tmp_path)
    observed = tmp_path / "observed-mode.txt"
    injection = f"""\
import pathlib
import stat

_real_scratch = shim._scratch_root


def _record_the_mode():
    root = _real_scratch()
    pathlib.Path({str(observed)!r}).write_text(
        oct(stat.S_IMODE(root.stat().st_mode)), encoding="utf-8"
    )
    return root


shim._scratch_root = _record_the_mode
"""
    completed = _run_shim(
        clone,
        commit=candidate,
        base_ref=base,
        temporary_root=tmp_path / "tmp",
        injection=injection,
        workspace=tmp_path / "driver",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert observed.read_text(encoding="utf-8") == oct(stat.S_IRWXU)
    _assert_nothing_left_behind(clone, tmp_path / "tmp")
