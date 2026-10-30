# Feature #7 — Stage-based progress reporting (2026-10-30)

## Why these counts are separate

Showing only `integrated_done` (0/35) conceals working, tested source already present
in a draft PR. These are **five independent evidence-backed indicators**, not
mutually exclusive additions to 100%. Do not sum stage counts or translate
them to product release completion. Production/customer acceptance remains distinct.

**Source snapshot:** `coordination/feature_tasks.json` from coordinator `main`,
35 stable IDs F7-A..F7-AI. **Source code and test evidence:** draft
[PR #513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513)
head `a394f2f406422a5969b783d2d719a27fd2d510ab`.
Exact-head [push #41054432688](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41054432688)
and [PR #41054442704](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41054442704)
both passed four jobs. Media job: **391 tests executed, 12 explicit skips**.

| Stage | F7 snapshot | Evidence boundary |
| --- | --- | --- |
| **Source-complete** | **8/35** | Registry's eight `source_complete` entries; source-only, not merged or deployed |
| **Tested** | **8/35 source-complete tracks** | Exact-head media CI `ok` on the individual tests mapped below; no hosted/real-model quality signoff |
| **PR-ready** | **0/35** | PR #513 is still **DRAFT**, so branch green CI alone cannot assert reviewer/merge readiness |
| **Integrated** | **0/35** | No coordinator-accepted task integration plus fresh main 4/4 evidence in canonical ledger |
| **Blocked** | **8/35** | Registry `blocked` snapshot entries; additional external dependencies also constrain in-progress work |
| **In progress** | **19/35** | Registry `in_progress`; source/test coverage within these tasks is not treated as full task acceptance |

**The source-state counts 8 + 19 + 8 = 35** partition the pinned registry,
but the five user-requested stage counters are **overlapping dimensions**:
the eight tested source-complete tracks are already included in source-complete.
The PR-ready and integrated counters are approval/merge gates, not source quality.

## Audited source-complete → tested mapping

The following named tests actually reported `ok` in the media CI logs of
run #41054442704. No test here invoked an approved paid GPU or a live ASR model.

| Pinned F7 task | Evidence-bearing test | Meaning |
| --- | --- | --- |
| `F7-A` | `test_feature7_pipeline::test_real_mp4_probe_and_original_aac_verified` | Integrity and ffprobe of local private synthetic source |
| `F7-B` | `test_feature7_pipeline::test_real_non_destructive_silence_detection` | FFmpeg activity detection, not speech/VAD |
| `F7-C` | `test_feature7_pipeline::test_whisperx_supplied_json_and_caption_trim_projection` | Supplied WhisperX-shaped timings, not real model inference |
| `F7-D` | `test_feature7_semantic::test_review_only_output_speech_captions_broll_and_audio_preserved` | Advisory edit plan; not final renderer |
| `F7-E` | `test_feature7_pipeline::test_integrated_private_review_builds_feature4_compatible_advisory` | Local review-only source pipeline; no backend approval |
| `F7-AF` | `test_feature7_private_snapshot::test_real_media_byte_identical_in_private_snapshot` | Local byte-preserving staged original |
| `F7-AG` | `test_feature7_speech_quality::test_exact_words_and_cue_timing_pass_but_are_not_model_proof` | Deterministic reference WER/clock, not true ASR |
| `F7-AH` | `test_feature7_public_cc0::test_real_internet_voice_video_clip_and_review` | Existing rights-limited CC0 test fixture, not retailer asset |

The older source registry is a fixed **snapshot**; new source commits on tracks
still marked `in_progress` do not automatically qualify them as `source_complete`.
A reviewer must evaluate the exact task acceptance, and the coordinator must
update the authoritative stage evidence. Passing an entire suite without
a verified task-to-test mapping is **not** reason to mark all 35 tested.

## Reusable coordinator-owned reporting change — Feature2/3/4/5/7

Request to the coordinator (do **not** let the F7 worker change the central
reporter, task registry, scheduler or `main`):

1. Extend the **rendered task-status output**, without changing the original
   159 task IDs, with fields `source_complete`, `tested`,
   `pr_ready`, `integrated`, `blocked`, plus `in_progress`
   and a `total`. Preserve the raw five original statuses and any
   prior event ledger rather than silently reclassifying them.
2. **Source-complete** is supported by reviewed feature-ledger source
   acceptance. Do not conflate `source_integrated` with `integrated_done`.
   **Tested** requires specific runnable test identifier(s) and an independently
   verified run/job conclusion for the tested source revision. Record whether
   validation is fixture-only, licensed-stock, real speech, hosted DEV, or PROD.
   Expired/superseded head evidence is labelled historical, never latest head.
3. **PR-ready** requires the exact-current-head required checks, reviewed
   acceptance and a nondraft PR or an explicitly accepted equivalent gate.
   Green CI on an open draft alone is `CI_PASS`, **not** PR-ready.
4. **Integrated** still requires coordinator-accepted scope, merged PR and a
   fresh four-job **postmerge main** run. Keep the trusted
   `coordination/task_progress.json` verification; do not create fake
   `DONE` events or treat draft source as merged.
5. **Blocked** uses exact dependency IDs, the owner, missing approved output
   and acceptance criteria; do not count source-only tests as satisfying
   human rights, TTS/ASR, JWT/RLS, durable storage or renderer gates.
6. Show **source stage and delivery gate separately**. A task can be source
   complete and tested but still blocked for live integration; overlapping
   counters must be clearly labelled, not added together. Publish both
   per-feature and overall views with IDs and run links.
7. Feature #5's denominator is **22**; this thread owns Feature #7's
   **35**. Audit its own 22 source statuses/evidence before reporting its
   tested/PR-ready counts. Do not substitute F7 counts for F5.

No workflow bypass, artificial test successes, automatic paid GPU/model,
PROD or WineShopPOS changes are authorized by this reporting proposal.
