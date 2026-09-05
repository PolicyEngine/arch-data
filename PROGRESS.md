bc619d697533e8f37b6520d3d9464b0afdcefffb
receipt 0.6.0 wheel sha256 84dd540bc77f14547bcf5b4654ff22184a404aa280d8b13cda8e179593575734
verify-publish: PUBLISH VERIFIED 2026-09-05 12:51

State: release preconditions verified; implementation not yet changed.

Done:
- Read PLAN-0.6 sections 3.10, 3.4, 3.9 and residual rows 2/14; read merged Chronicle #241, #242 and the existing shim/tests.
- Starting branch shim/receipt-0.6 equals origin/codex/thesis-ledger-facts at the first-line OID.
- receipt v0.6.0 peels to a2228e40fc0bb2d8e525cae61b91ea495eec4112, the reviewed head in receipt #59 and approval comment 5553008482.
- PyPI publication is corroborated by release-smoke-060/pypi.json, verify-publish-060.log (completed success), and hashing the published local wheel against its recorded PyPI digest above. Shell DNS cannot resolve api.github.com or pypi.org; GitHub connector can read PR records.
- Exact local receipt tag diff v0.5.2..v0.6.0 -- src/receipt/append_gate.py confirms commit="HEAD" on both verifiers and AppendGateVerdict(summary, candidate_commit, candidate_tree, base_commit, base_tree, object_format, name_repertoire).

Next:
- Run the byte-equivalence proof at receipt 0.5.2 before changing the pin.
- Migrate the shim to the released wheel, adapt installed-package tests and workflow documentation, then rerun proof and required suites.
- Prepare draft PR and default-branch workflow copy; push if networking permits. Write final report to OUTPUT.md unless another output path is supplied.

Progress policy: committed under the standing order; asked for clarification because the Record paragraph also says untracked.

Done: pre-bump byte-equivalence proof at installed receipt 0.5.2: 18 passed in 29.66s (`uv run --frozen --no-sync -q pytest -q tests/test_receipt_shim_transparency.py`; isolated writable UV_CACHE_DIR, offline). The environment was copied from the 0.5.2 shim worktree; ordinary frozen sync initially lacked cached build dependencies. No shim/pin edits preceded this proof.

State: migration implemented; released-wheel verification running.

Done:
- Kept all three explicit workflow OID arguments and the base-owned help compatibility branches; updated object-read documentation and pipefail on every shell block.
- Strengthened adversarial success/refusal assertions to bind the verdict line; 28 passed, 5 existing strict xfails against installed receipt 0.6.0.
- Prepared the default-branch byte-identical workflow in local branch shim/receipt-0.6-workflow at 2f9f5de5c534d15fc64d70a6f742deb7ccf784ba, based on origin/main 743742c. All four workflow run blocks pass bash -n.
- Provisioned the released local wheel offline and verified ordinary uv sync --frozen succeeds using writable /tmp/chronicle-uv-cache. Lock metadata copies the exact published artifact URLs, sizes and SHA-256s; UV_FROZEN=false uv lock --check --offline succeeds.

Next: finish exact requested suite and released-pin byte proof, include the necessary release-chain shim compatibility change discovered by the proof, then commit and attempt delivery.
