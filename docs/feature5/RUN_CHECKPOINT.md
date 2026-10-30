# Feature #5 scheduled-run checkpoint — 2026-10-30

## Current task
- **F5-14** — read-only mounted Wan checkpoint files / private manifest source preflight.
- **State:** source hardening proposed on stacked draft [PR #819](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/819), not integrated, not production verified.
- **Parent:** Feature5 consolidated draft [PR #781](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/781). Coordinator must reconcile stacked PRs; do not merge out of order.

## Changes in this run
- `feature5_motion/shared_model_mount.py`: fail closed when O_NONBLOCK is unavailable and recheck the original manifest pathname's inode after descriptor read. The original descriptor remaining valid does not prove that its path was not replaced.
- `tests/ai/test_feature5_shared_model_mount.py`: deterministic CPU-only test replacing the original path after the first successful descriptor read; preflight must reject the changed path.
- Source commits: `3d85700dbd92329c577add57f61deb8d5be4d3ff` and `a1ffbc0076cdc0c7e9c781b0bac61550c5b3cbb0`.
- **Verification:** test source added; local Python unittest execution NOT RUN in this GitHub connector run. Exact-head CI pending inspection; do not claim TESTED or PR-READY from source alone.
- **No Azure Files bytes inspected:** actual three Wan checkpoint SHA-256 hashes, private mounted Azure Files identity, CUDA/OCI licenses and GPU runtime remain unverified.
- No GPU inference, Azure mutations, PROD, paid model, SQL, external samples or WineShopPOS changes.

## Next safe tasks
1. Recheck [PR #819](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/819) exact-head CI; run `python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py'` in authorized CI/local test runner and fix any failure.
2. **F5-13** — independently review pinned OCI/CUDA dependency license, image digest and SBOM source evidence, CPU-only; do not claim image build until independently verified.
3. **F5-02** — review existing [PR #804](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/804) and its latest source/CI before choosing additional independent work; avoid duplicate code.
4. Coordinator: reconcile stacked Feature5 drafts, exact-head 4/4 CI, fresh main 4/4 and reviewed task receipts. Until then F5-14 is IN PROGRESS.

## Reporting
Central `coordination/feature_tasks.json` snapshot: F5 total 22, source-complete 0, blocked 19, in-progress 3. `coordination/task_progress.json` currently has no verified events. This does not imply zero code exists. TESTED, PR-READY and integrated DONE are not verified.

## Post-checkpoint verification receipt
- Latest checked PR #819 head: `9a646abb376a19ab4864b12a1466fbb4bd4bce38` (checkpoint commit before this receipt).
- GitHub PR-triggered workflow runs for that head: **none returned**; combined commit statuses: **none returned**. This is **not** passing CI.
- GitHub PR metadata currently reports `mergeable=false` against moving parent branch `feat/feature5-batched-gpuoff-hardening-20261030`. Coordinator must reconcile/rebase safely before merging; do not assume a clean stack.
- Local targeted tests were not executed because this environment cannot resolve github.com for a local checkout. Existing tests are proposed, not independently verified.

## 2026-10-30 follow-up F5-14 source change
- Added static parent-directory no-symlink validation before and after reading the private manifest in `feature5_motion/shared_model_mount.py`, commit `b84489e803100c2e249c4db8a3c4ce9be5e63740`.
- This denies symlinked ancestors but is NOT an atomic trusted mount attestation; original checkpoint bytes and Azure mount remain unverified.
- Test file write failed due GitHub connector internal error; targeted tests and exact-head CI **NOT RUN**. Next run must add negative regression and verify source CI before claiming tested or PR-ready.
- Next task: F5-14 regression and exact-head CI; then F5-13 OCI evidence. GPU OFF.

## 2026-10-30 follow-up — regression committed
- F5-14 parent-symlink negative test now committed: `tests/ai/test_feature5_parent_guard_20261030.py`, commit `e6189df9f0f1cf8fafd84e4df58cce487206958a`; earlier test write connector failures were transient and resolved by a small create-then-update.
- Source guard: `feature5_motion/shared_model_mount.py` commit `b84489e803100c2e249c4db8a3c4ce9be5e63740`.
- **Verification:** no local repository checkout (network DNS unavailable), so `python -m unittest discover -s tests/ai -p 'test_feature5_parent_guard_20261030.py'` NOT RUN. GitHub PR-run/status API returned no checks on the observed intermediate head; new exact-head 4/4 CI must be inspected before TESTED/PR-ready claims.
- **Next:** F5-14 exact-head CI and merge conflict reconciliation by coordinator; independently eligible F5-13 OCI/SBOM source review if CI pending. No actual mounted checkpoint readback, Azure deployment or GPU inference.

## 2026-10-30 F5-14 same-size rewrite / restored-mtime guard

- **Source:** `feature5_motion/shared_model_mount.py` now compares `st_ctime_ns` alongside device, inode, size, mtime and link count before and after the bounded descriptor read. This detects in-place writes followed by restoration of the old mtime that the previous identity tuple could miss. Source commit `d1193f49e70cd3c720d847f4b6ec076bbbc150bd`.
- **Regression:** `tests/ai/test_feature5_shared_model_mount.py` now rewrites the manifest in-place after `os.read`, preserves byte count and restores the old mtime, and expects `PreflightError`. Test commit `112bc2a4f07acdd379ea2caade8357aa5c8c37f8`.
- **Verification:** GitHub PR-triggered workflow lookup on exact code/test head `112bc2a4f07acdd379ea2caade8357aa5c8c37f8` returned **zero runs**; local repository tests **NOT RUN** (no local checkout). This is **not** TESTED or PR-ready. Suggested command: `python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py'`.
- **PR:** stacked draft [#819](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/819), `mergeable=false` against parent Feature5 batch PR #781; coordinator owns stack reconciliation, CI and merge. New checkpoint commit itself requires a fresh exact-head check.
- **Limits:** ctime identity is defense in depth, not cryptographic provenance or an atomic mount attestation. Actual 3 original Wan checkpoint SHA-256 reads, OCI/CUDA review, hosted mount and real inference remain unverified. GPU OFF; no paid services or PROD changes.
- **NEXT:** F5-14 targeted test + exact-head 4/4 CI after stack reconciliation; meanwhile F5-13 independent OCI digest/license/SBOM review (no image build or GPU), or F5-02 original exporter review after verifying PR #804 to avoid duplicate work.
