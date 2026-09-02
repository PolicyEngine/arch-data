# PR #229 final report

## Outcome

Implementation and local verification are complete for both requested changes:

- The scheduled job now publishes proof-only commits directly to `main` with a
  bounded, non-force retry path. The bot-branch import, PR creation, and
  auto-merge machinery are gone.
- OpenTimestamps 0.7.2 pending, complete-with-leftover-pending, exact mismatch,
  and unknown outputs are classified according to the captured real contract.
  Unknown output fails closed.

Shell access to GitHub remained DNS-blocked, so the required branch push and
`gh pr edit 229 --body-file` have not succeeded as of this report. An
authenticated connector could read PR #229, but its attempted body update was
cancelled. PR #229 remains open and was not merged.

## Implementation

The workflow now:

1. Logs the three supplied `main` rules/ruleset/protection API queries on a
   best-effort basis at job start.
2. Checks out trusted `main` with full history and a persisted push credential,
   and checks out the journal separately without credentials.
3. Runs `run`, `verify`, and `guard`, stages only `ots/`, and refuses a dirty
   worktree or any committed path outside `ots/`.
4. Runs `git push origin HEAD:main` without force.
5. After a failed push, fetches `main` and uses commit ancestry to distinguish an
   ambiguous success, a non-race rejection, and a retryable remote advance. A
   retry rebases, refreshes the journal checkout, reruns all three commands,
   recommits, and pushes again, with three total attempts.

The proof classifier now reads local `ots info` structure first. Any
`BitcoinBlockHeaderAttestation` makes the local state complete even when
`PendingAttestation` lines remain. Binding then accepts only the complete
captured line structures at exit 1: one or more full calendar-pending lines, or
one or more paired Bitcoin-disabled/manual-verification lines with 64-hex merkle
roots. Only the exact line `File does not match original` is a mismatch.

## Verification

The sandbox does not allow `uv` to initialize its default cache, so the three
requested `uv run` commands used the writable cache location
`UV_CACHE_DIR=/tmp/chronicle-uv-cache`; the command bodies were otherwise
unchanged.

```console
$ uv run pytest -q tests/test_ots_anchor.py
.................                                                        [100%]
17 passed in 3.32s
```

```console
$ uv run ruff check .
All checks passed!
```

```console
$ uv run ruff format --check scripts/ots_anchor.py tests/test_ots_anchor.py
2 files already formatted
```

```console
$ actionlint .github/workflows/ots-anchor.yml
# no output; exit 0 (actionlint 1.7.12)
```

The requested real-proof command could not complete in this sandbox. With the
literal `uvx` invocation, `uvx` cannot write its default cache:

```console
$ python3 scripts/ots_anchor.py status --manifests /tmp/journal/releases/manifests --ots-bin "uvx --from opentimestamps-client==0.7.2 ots"
ots anchor failed: unrecognized ots verify outcome for 0000-307cedbc91de43be.json.ots: error: Failed to initialize cache at `/Users/maxghenis/.cache/uv`
  Caused by: failed to open file `/Users/maxghenis/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
```

The machine already has the exact client in a read-only cached environment, so
the equivalent direct executable was checked:

```console
$ /Users/maxghenis/.cache/uv/archive-v0/SDUkLw8BSnRSiJdUQjAU4/bin/ots --version
v0.7.2
```

Running status with that executable classified all fifteen complete proofs,
then stopped when the first pending proof tried to contact its calendars:

```console
$ python3 scripts/ots_anchor.py status --manifests /tmp/journal/releases/manifests --ots-bin "/Users/maxghenis/.cache/uv/archive-v0/SDUkLw8BSnRSiJdUQjAU4/bin/ots"
ots anchor failed: unrecognized ots verify outcome for 0015-fdcfd0e570214f6b.json.ots: Calendar https://btc.calendar.catallaxy.com: [Errno 8] nodename nor servname provided, or not known
Calendar https://finney.calendar.eternitywall.com: [Errno 8] nodename nor servname provided, or not known
Calendar https://alice.btc.calendar.opentimestamps.org: [Errno 8] nodename nor servname provided, or not known
Calendar https://bob.btc.calendar.opentimestamps.org: [Errno 8] nodename nor servname provided, or not known
0000-307cedbc91de43be.json: bitcoin attestation stored locally
0001-916626696d034b80.json: bitcoin attestation stored locally
0002-a69272175b73c83b.json: bitcoin attestation stored locally
0003-cfae6e9b4524db6d.json: bitcoin attestation stored locally
0004-36322993cf45b6d1.json: bitcoin attestation stored locally
0005-9bcc4ff6b3fad5d2.json: bitcoin attestation stored locally
0006-770683e59da14f45.json: bitcoin attestation stored locally
0007-2b5ed02908832f0c.json: bitcoin attestation stored locally
0008-070e797b855dce92.json: bitcoin attestation stored locally
0009-995768a31dd8fa6d.json: bitcoin attestation stored locally
0010-6ba8c08f34189164.json: bitcoin attestation stored locally
0011-34319583df55ce83.json: bitcoin attestation stored locally
0012-3a5ef7eeee484370.json: bitcoin attestation stored locally
0013-d47323bbaacda2d1.json: bitcoin attestation stored locally
0014-bd12e9e3e79a5529.json: bitcoin attestation stored locally
```

This is the assignment's allowed no-network case. Local `ots info` inspection
with that same 0.7.2 executable reports `bitcoin=15 pending=5`; the 17 hermetic
tests reproduce the supplied pending and complete output verbatim and exercise
binding classification without a network assumption.

## Integrity and review

- All 20 `.ots` proof blobs are byte-identical to starting commit `03b27674`.
- Combined checksum over the sorted per-proof SHA-256 list:
  `420c3f54b47df5c58c58edc7202f580dcbad40193a4264bec20c133b71a375b1`.
- No path under `releases/` or `ledger/` changed.
- All assignment commits end with the required Claude Fable co-author trailer.
- Three independent read-only reviews covered classifier behavior, workflow
  races/permissions, documentation, and proof/restricted-path integrity. The one
  workflow race finding was fixed; final rereview found no remaining issue.

## Delivery attempts

```console
$ git fetch origin
fatal: unable to access 'https://github.com/PolicyEngine/chronicle.git/': Could not resolve host: github.com

$ git push origin ots-anchor-main
fatal: unable to access 'https://github.com/PolicyEngine/chronicle.git/': Could not resolve host: github.com

$ gh pr edit 229 --body-file /tmp/pr229-body.md
error connecting to api.github.com
check your internet connection or https://githubstatus.com
```

The replacement PR body is staged at `/tmp/pr229-body.md`; it replaces “Open
items before merge” with the requested “Publication path” section and includes
the supplied API evidence. No merge command was run.
