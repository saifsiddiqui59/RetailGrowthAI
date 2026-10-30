# Feature #7 durable run checkpoint — 2026-10-30 (CPU worker)

- **Task:** F7-L (GPU-OFF CPU speech worker safety), bounded subprocess failure/timeout regression. Incremental source-only change, NOT full F7-L acceptance.
- **Branch:** `feat/feature7-cpu-worker-hard-timeout-20261030`, stacked on `feat/feature7-uploaded-footage-semantics-20261028` / parent draft PR #513.
- **Draft PR:** [#847](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/847).
- **Code commit:** `38dfdbc03eb70831a7627344a927ff54f9ed983f`; **test commit:** `7e97ff533616859bf1ef15104326007b8b21b5a5`. Inspect GitHub for the latest PR head after this checkpoint commit.
- **Changed files:** `video-engine/feature7/offline_whisperx_cpu.mjs` exports `runBoundedOfflineCommand` with validated timeout and SIGKILL for hung FFmpeg/WhisperX processes; `tests/media/test_feature7_offline_worker_timeout.py` checks success, nonzero exit, SIGTERM-ignoring hang and invalid timeout. No actual model/media samples.
- **Verification:** Isolated local Node v22 `spawnSync` behavior smoke: exit 0, exit 7 and `ETIMEDOUT` after ~303ms with SIGKILL. This was NOT the committed repository module/test suite. Full targeted tests not run. GitHub connector showed no workflow runs or combined statuses for pre-checkpoint commit `7e97ff533616859bf1ef15104326007b8b21b5a5`. **Exact-final-head 4/4 CI unverified**, recheck after checkpoint.
- **Status:** SOURCE CHANGE COMMITTED / TEST FILE COMMITTED / REPO TEST EXECUTION UNVERIFIED / DRAFT / NOT INTEGRATED. Central task registry unchanged.
- **Blocked acceptance:** F7-L genuine reviewed WhisperX/aligner weights, approved human speech, no-egress CPU accuracy benchmark (Feature7/operator); F7-H/K authenticated private video upload, JWT/RLS and hosted signed E2E (coordinator); F7-J reviewed Feature4 render execution (Feature4). These do not block this source regression.
- **NEXT eligible:** F7-F source-only Feature4 review-envelope contract/negative tests, after checking recent PRs. Do not duplicate F7-04 PR #756 or F7-G PRs #825/#840/#846.
- **Safety:** GPU OFF; no paid AI/model, PROD, cloud/SQL mutation, samples or WineShopPOS.
