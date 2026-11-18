# F5-02 original Creative Director PR source drift review — 2026-10-31

## Verified GitHub source comparison

- Old original Feature2 draft #551 head: `f38bf815cad7d77b7cadd9aa8bff55759e86947c`.
- New original Feature2 draft #551 head: `d80d6b50705323290c4b214bf2f006eacef1ef33`.
- GitHub comparison: **13 commits ahead, 0 behind**, affecting only `docs/issue650/COORDINATOR_RUNTIME_MANIFEST.md`, `scripts/deploy/package.py`, and `tests/infra/test_functions_runtime_manifest.py`.
- Fetched original `ai-agents/creative-director/export-feature4-feature5-fixture.js` at BOTH exact refs; **byte-for-byte equal** (7200 source characters). No Creative Director original exporter modification in this delta.
- Existing Feature5 branch CI #41179203232 correctly **failed**, not skipped, when strict test fetched current `refs/pull/551/head` and found the old expected immutable head. This deliberate failure confirms drift detection.

## Safe response, not a shortcut

Advanced only the `PINNED_F2_HEAD` literal inside Feature5 `feature5_motion/f2_branch_export_probe.py` to the newly reviewed exact upstream revision. Retained independent read-only detached Git fetch, fully clean tracked/untracked worktree verification, unchanged original Node 15/30/60 seconds stdout, seven independently tampered negative packets and no GPU/network/cloud credentials in the Node environment. **New exact-head CI must pass** before calling this change verified.

This means **F5-02 remains IN PROGRESS**: Feature2 #551 is still draft on `main`, original 15/30/60 source has not been coordinator-merged into production, and no signed rights, model output or publication authorization exists. The source of the change is a code-verified repository comparison, not an assertion of original legal/production approval.

GPU OFF. No paid inference/OCI build/Azure/hosted SQL, PROD, customer media or WineShopPOS.
