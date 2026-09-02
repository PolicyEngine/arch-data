# Bitcoin checkpoints for the witnessed journal

This directory contains [OpenTimestamps](https://opentimestamps.org) proofs for
release manifests on the `codex/thesis-ledger-facts` journal branch. For a stem
`<stem>`, `ots/<stem>.json.ots` commits to the exact bytes of
`releases/manifests/<stem>.json` in a journal checkout. Those are the same bytes
witnessed by the release's two RFC 3161 authorities and signed by its pinned
producer key.

## What a proof establishes

A proof with a Bitcoin block attestation establishes that the manifest bytes
existed no later than that block. Each manifest commits to the full journal
bytes (`state.jsonlSha256` and `state.lineCount`), the immutable prefix, and the
previous manifest. An attestation therefore bounds the existence time of that
journal state and the manifest chain it incorporates without trusting this
repository's Git history as the only checkpoint.

The proof does not establish that the manifest's claims are true, that GitHub
accepted a proposal at a particular time, or that no parallel fork exists. A
rewritten history can acquire new anchors, but Bitcoin exposes the later time at
which those replacement bytes first existed; it cannot be backdated.

The 15 proofs initially carried here bind releases 0000–0014 and were first
stamped on 2026-08-19. The daily workflow stamps later manifests after they
appear and upgrades locally pending proof files when calendar attestations can
be folded into the serialized proof.

## Verify

Check a proof against a real checkout of the journal branch:

```console
ots --no-bitcoin verify \
  -f <journal-checkout>/releases/manifests/<stem>.json \
  ots/<stem>.json.ots
```

The workflow pins the client as
`uvx --from opentimestamps-client==0.7.2 ots`; use that invocation in place of
`ots` for the same reproducible client version. `--no-bitcoin` verifies that the
proof commits to the manifest's exact bytes and, when available, prints a block
height and merkle root for manual checking against a Bitcoin source you trust.

To sweep every manifest in a journal checkout against this proof tree:

```console
python3 scripts/ots_anchor.py verify \
  --manifests <journal-checkout>/releases/manifests \
  --ots-bin "uvx --from opentimestamps-client==0.7.2 ots"
```

This is strict: a mismatched or missing proof fails. Add `--require-bitcoin` to
also fail while any committed proof file still contains only pending calendar
attestations. `status` distinguishes that local serialized state from an
attestation a calendar may resolve in memory during verification.

## Why proofs and automation live on `main`

The journal's `releases/` history is immutable, and its append gate admits only
complete release bundles. OpenTimestamps proofs are operational artifacts:
stamping creates them after a release exists, and upgrading rewrites them as
calendar transactions confirm. They therefore cannot live under `releases/`.

Keeping the proof tree, anchoring script, tests, and scheduled workflow together
on protected `main` also establishes the privilege boundary. The workflow runs
`main`'s trusted script against a separate, shallow journal checkout that has no
persisted credential. It verifies the entire manifest/proof tree and rejects
any worktree change outside `ots/` before publication. It never pushes to the
journal branch.
