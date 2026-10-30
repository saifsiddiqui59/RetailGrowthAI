# Feature #7 — Integration-first run checkpoint (2026-10-30)

## Completed integration work
- **Batch PR:** #513 (draft), branch `feat/feature7-uploaded-footage-semantics-20261028`. Feature-owned branch only; no merge to main.
- **Source PR reconciled:** #847, F7-L bounded offline CPU worker hard timeout. Existing source copied into the batch without rewriting its implementation.
- **Integrated code:** `video-engine/feature7/offline_whisperx_cpu.mjs`, source commit `ac80bda802a4b52235258b7dbf4610377f208e0c`.
- **Integrated regression:** `tests/media/test_feature7_offline_worker_timeout.py`, test commit `f64d3e0cef5c1be2643ddc6b591cc8c8ddd66837`. Cases: successful subprocess, nonzero exit, SIGTERM-resistant hang killed by deadline, invalid timeout.
- **Original source PR head:** #847 `2edb642002600131127318d5c64f24dc8496b82e`. Its PR remains stacked/open; coordinator should mark it superseded only after confirming accepted source in #513.
- **Pre-integration parent SHA:** `7ca3b6bc9c12ae5fbdfd7ad84e62920c5822ce4d`. Its GitHub Actions Part 1 CI run [#41090018122](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41090018122) completed 4/4 success. **This is stale evidence for the new source/test commits.**
- **New exact-head CI:** NOT YET VERIFIED as of this checkpoint. Required: 4/4 Part 1 CI on the current PR #513 head; inspect workflow run and jobs before declaring tested/PR-ready. No local repository suite was executed during this integration run.
- **Mergeability:** #513 was reported mergeable and draft before edits; recheck after CI. Coordinator alone reviews/merges into main, followed by fresh main 4/4.
- **Source snapshot (central unchanged):** source-complete 8/35, blocked 8/35, integrated 0/35. Tested and PR-ready task counts remain unverified; green historical CI is not current-head acceptance.
- **External acceptance blockers:** F7-L genuine licensed offline WhisperX weights, human reference speech and CPU accuracy benchmark; F7-H/K hosted tenant JWT/RLS and signed private intake; F7-J Feature4 reviewed editor/renderer execution. None is claimed complete by this offline subprocess fix.
- **NEXT integration candidate:** F7-G stacked PR #846 (music ducking speech-cue validation). Check its base/parent diff, exact head and overlapping files before copying; then #840 review receipt time validation. Do not open another micro-PR or duplicate work already in #513.
- **Safety:** GPU OFF; no paid inference, hosted SQL, PROD, WineShopPOS, or samples.

## Second compatible source integration — F7-G
- **Source PR:** #846, original child head `2e2106945cafa05ca38402d6b163d64a46e0195c` (draft, stacked). This branch was compared with the current parent since its base `0166d719be7e13cf8d5280217c97f9dcf9a050f7`; parent had no changes to either imported path.
- **Files imported:** `video-engine/feature7/speech_music_handoff.mjs` (commit `5e1577ffbe0c6edd62b38190af9ce3172f493158`); `tests/media/test_feature7_music_ducking.py` (commit `2b942874bbf84c2d30848bdd1ed02879d28287ca`). These are existing speech-cue Unicode/clock validation changes and their offline regressions, not newly authored functionality.
- **Verification:** GitHub exact-current-head 4/4 CI must be rechecked after this checkpoint commit; the earlier successful #41090018122 applied to the old parent SHA only. No claim that this combined head has passed yet.
- **Merge gate:** PR #513 returned `mergeable=false` immediately after the first integration; determine whether this is a transient GitHub calculation or a real main conflict before requesting coordinator merge. Never force-merge or edit main.
- **NEXT:** F7-G PR #840 (review receipt time bounds), compare base-to-parent paths first. If conflict, stop copying and prepare exact conflict evidence for coordinator. Then review #825 and #847/#846 source presence before closing any child PR.

## Third compatible source integration — F7-G / F7-F review receipt
- **Source PR:** #840, original child head `1791c3dce9620be48b461b6873fe48748e77f613` (draft). Compared the parent since #840 base `0166d719be7e13cf8d5280217c97f9dcf9a050f7`; neither review path was modified by parent.
- **Files integrated:** `video-engine/feature7/review_fence.mjs` commit `112d0e77a485ab0f5aaf4a5ebb8ddabb43607c25`, and `tests/media/test_feature7_review_fence.py` commit `e83eec422e9bc0825cdd9c7ae797b0ea02ccacfa`. Imported existing overflow/invalid signed receipt negative checks.
- **Parent mergeability:** GitHub recomputed #513 as `mergeable=true` after earlier transient `false`; do not treat that alone as accepted review or green CI.
- **Current exact-head CI:** unverified; previous run #41090018122 was 4/4 on `7ca3b6b...`, before all three integrations. Inspect latest head, CI job results and any conflicts before coordinator merge. This checkpoint is the last write in this run.
- **NEXT:** investigate PR #513 exact-head four-job CI and targeted F7-L/F7-G tests; then compare #825 (caption cue validation) for compatible integration. PRs #847, #846 and #840 should remain open until coordinator confirms their source is accepted in #513.

## Fourth compatible source integration — F7-G caption projection (2026-10-30)
- Source PR #825 (stacked), source branch `feat/feature7-caption-projection-validation-20261030` head `5fb4c258d4bc59531d417ab867243e8cb54613a4`.
- Source file `video-engine/feature7/transcript_adapter.mjs` imported unchanged from source blob `03746f42c4cdcec58ef690e695f631b2e9c237a8` at commit `13cb7d8112bd12865a15b8afd51bfa381333727f`.
- Test file `tests/media/test_feature7_caption_projection.py` imported unchanged from source blob `fc260b1d0f7ca3c410d4dd659c20655a0ddb45e0` at commit `061f97f1a0185fa0e85fba381f8e1387e00b9257`.
- Exact code-head verification: GitHub compare `2184fdc...061f97f` shows exactly these two paths, +116/-8 lines. Parent #513 remained mergeable=true against main at code head `061f97f`.
- Prior parent head `2184fdcea47c976b1d2505a02abc01f29d0b8a44` had Part 1 CI run `41098097292` with all four jobs successful (FFmpeg, Python/uv, Supabase, Frontend). This is **not** evidence for the new code or this checkpoint.
- New code head `061f97f` had **no PR-triggered workflow runs returned** at inspection. No local test suite executed in this run. Current checkpoint commit changes head again; require fresh exact-head 4/4 CI and coordinator review before PR-ready or accepted integration.
- Child PR #825 remains open until coordinator verifies this integration; no source PRs closed, no main merge. Hosted signed tenant rights/ASR/Feature4 live approval remain blocked separately.
- NEXT: inspect #513 exact-head four-job CI and run targeted caption projection regression if runner permits. If CI awaits, compare source PR #806 (F7-AC CPU readiness policy) against current parent for a conflict-free existing-source integration. Do not duplicate code or open micro-PRs.
- Snapshot remains source-complete 8/35, blocked 8/35, integrated DONE 0/35; tested and PR-ready task counts unverified on new head. GPU OFF, no paid inference, PROD, SQL, WineShopPOS or samples.

## Fifth compatible source integration — F7-AC CPU readiness (2026-10-30)
- Source stacked PR #806 `feat/feature7-cpu-policy-failclosed-20261030` at `83a7e935824e67b484bf0f9895821cdb1adc972d`; source changes compared against parent base `332eab48020bb9bad6aa105332cf5f162c76b793`.
- Imported unchanged code `video-engine/feature7/cpu_readiness.mjs` from blob `baf20790fbf4a8638e5440f321b1c840fdf1e3f3` at commit `58c907e8e3b467c618c0aa62723b6f75e4f6ecc0`.
- Imported unchanged regression `tests/media/test_feature7_cpu_readiness.py` from blob `81fb14ef6d4e593dc7b74769ed0929f80bfafe52` at commit `f51507c5a5424a7e04d8b8942d2ae61fb775d9f7`.
- Parent had not modified either source/test path since #806 base; only feature-owned TASKS ledger overlapped and was intentionally NOT overwritten. Existing ledger source remains authoritative pending coordinator review.
- GitHub compare from prior checkpoint `89eb2a8` to code head `f51507c` showed only the two imported files (+48/-6 lines). PR #513 mergeable=true at code head, against main.
- **Verification boundary:** No local targeted suite was executed. No PR-triggered workflow runs returned on code head `f51507c` at inspection. Earlier 4/4 green CI run `41098097292` applies ONLY to stale pre-integration parent head `2184fdc`; it cannot certify these imports. Current checkpoint commit changes the head again; require exact-head 4/4 and coordinator review.
- NEXT: check new PR #513 exact-head Part 1 CI, run targeted caption projection and CPU readiness tests if possible; diagnose any failure before integration. If pending, inspect source PR #800 for nonoverlapping private-intake rights safety and compare with parent. Do not merge main or close child #806/#825 until accepted.
- Snapshot: source-complete 8/35; blocked 8/35; integrated DONE 0/35; tested and PR-ready not yet verified on current combined head. No GPU, paid inference, PROD, SQL, WineShopPOS or samples.
