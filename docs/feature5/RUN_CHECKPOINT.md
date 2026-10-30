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

## 2026-10-30 integration-first branch reconciliation

- **Action:** reconciled the six commits added to Feature5 consolidated PR #781 after F5-14 branch diverged, using the latest batch tree and the original F5-14 source/test/doc additions. Preserved batch test `test_manifest_reader_does_not_follow_hardlinks_or_changed_descriptor` and updated its mocked stat object for the new ctime identity check; added four additional F5-14 negatives. This is a two-parent Git merge on the existing PR #819 branch, not a merge into main.
- **Source parents:** batch #781 `18cbc016b0a2914c886e75328366d46f85901901`; prior #819 `36fc11a878dd0325df097a6482c1239d58e73e44`.
- **Evidence:** source/tree reconciliation only; targeted Python tests and exact-head CI are **NOT VERIFIED**. New head/CI must be checked after commit. No model weights read, GPU remains OFF.
- **NEXT:** review resulting PR #819 diff/mergeability, run targeted tests and exact-head 4/4; coordinator may then integrate stack into #781 and verify parent chain before main. F5-13 OCI/SBOM remains independently blocked by external evidence.

## 2026-10-30 exact-head CI repair after stack reconciliation

- Reconciled #819 into latest #781 via two-parent merge commit `8e07cdd5830c2539867cca741be5a573285610d3`, with compare **behind 0**; GitHub REST reports mergeable true, unstable until checks.
- Push CI [41090613967](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41090613967) found a **real failure** in Python job: 4 F5-14 regression tests raised `NameError: os not defined`; other Python tests 1214 passed, 12 skipped. This is a failed exact-head run, NOT verified TESTED/PR-ready.
- Fixed top-level `import os` in `tests/ai/test_feature5_shared_model_mount.py`, code commit `55d0d888047471cbbad932ba1e04ed6fddcef5e1`. The prior merge had only a nested import, which the source merge check incorrectly treated as a module import.
- **NEXT:** inspect the new exact-head push run and all four jobs, including the four previously failing F5-14 tests; if green, coordinator reviews five-file #819 and merges into #781. No main merge, GPU or paid inference. Original F5-14 weight hash/mount/license gates remain pending.


## 2026-10-30 integration-first: F5-14 consolidated into Feature5 batch
- **Actual feature-owned integration:** merged stacked PR #819 (F5-14 private manifest inode/symlink/path-swap hardening and CPU regressions) into existing Feature5 batch PR #781, **not into main**. Merge commit: `3eeb7124d9a2e4440dec04be60efc2ff0687e47b`. The batch now contains 47 changed files relative to its Feature5 parent PR #465; do not reopen the duplicate #819 work.
- **Independent pre-merge source verification:** PR #819 exact head `d15e995ff9ebbdbc930116ddf2943b402b9d302f`, Actions run [#41090732742](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41090732742), all **four standard jobs passed**. The Python job log checked out that exact SHA and reported **1218 passed, 12 skipped**. This verifies CPU regression source tests, not model checkpoint readback or skipped native-media acceptance.
- **Batch before integration:** PR #781 exact head `29a75ebba5569e2ba14babfde47efdfeaa1c463e`, Actions run [#41096085256](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41096085256), four standard jobs passed; Python **1215 passed, 13 skipped**. This run predates the #819 merge and is **not** current-head CI.
- **Current batch:** PR #781 is OPEN, targeting Feature5 parent #465, not main. The merge SHA and this checkpoint commit require new exact-head 4/4 CI and independent coordinator review. Do not claim integrated DONE.
- **NEXT integration gate:** inspect latest PR #781 exact-head CI after this checkpoint. Separately require the coordinator-owned FFmpeg workflow to invoke `python3 -m feature5_motion.ci_native_media` with actual FFmpeg/ffprobe/Pillow and **4/4 native CPU tests, zero skipped**. Do not silently count skipped tests as passing.
- **Unresolved release gates:** F5-13 OCI/CUDA image digest/SBOM/license; F5-14 three original checkpoint hashes and trusted mount; Part3 native Wan2.2 tenant/lease/credit/storage; Feature3 licensed worn-SKU first frame; human QA and explicit GPU approval. GPU OFF, no paid model, hosted SQL, PROD or WineShopPOS change.

## 2026-10-30 — F5-17 existing FFmpeg CI bridge executed
- F5-17 original release status **BLOCKED**, but the previously skipped **CPU source acceptance** is independently proven. New cross-owner `tests/media/test_feature5_native_media_ci_bridge.py` on batch #781 head `8783fc172d3b58be9070b5593071dcf60dfb9650` was discovered by original `video-engine/ci.sh` on Actions #41115123091 FFmpeg job #124267216516.
- Actual log: four native CPU/private intake tests separately `... ok`, `Ran 4 tests in 4.267s`, `PASS: 4/4 real ffmpeg/ffprobe private-intake tests, 0 skipped`. No GPU or AI model.
- At this checkpoint, video job success verified; full 4/4 overall exact-head workflow was not yet concluded. Coordinator/media workstream reviews one new tests/media bridge in ready #781, then may integrate to parent #465. Source acceptance is NOT original Wan GPU/render/rights/human review acceptance.
