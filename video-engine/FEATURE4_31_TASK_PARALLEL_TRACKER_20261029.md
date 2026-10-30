# Feature #4 — 31-work-item concurrent execution tracker (29 October 2026)

PR #322 (DRAFT). Feature4 owner: `feat/feature4-professional-video-studio`. Review against CURRENT HEAD / merged-base CI; no cross-branch direct writes, paid GPU/cloud/PROD, WineShopPOS edits or unreviewed customer media. This is an **honest backlog**, not 31 completed tasks.

## Independent Feature #4 — work may proceed concurrently within owned paths

| # | P | Required deliverable | Current source/evidence | Remaining gate |
|---|---|---|---|---|
| 1 | P0 | Standalone revised native 60s render + caption/visibility/endcard | Runner now calls mandatory v2 visibility and encoded 55s endcard QA, plus FFmpeg subtitles | **NEW native 60s exact-head render still needed** |
| 2 | P0 | Hash-linked final 60s quality receipt | Source now FAILS CLOSED if any caption, v2 visibility or real encoded endcard proof missing; negative tests added | Full updated media+SHA+report chain not rerun |
| 3 | P0 | 15/30/60 actual export regression matrix | Existing 15/30 CI & separate 60s stock artifact | One unified exact-code acceptance record |
| 4 | P0 | Encoded editor action parity after split/reorder/duplicate | Trusted JS/Python compiler tests; synthetic edit MP4 | Encoded visual tests for every supported edit |
| 5 | P0 | Renderer-supported transitions/fades/effects | Existing reviewed HyperFrames subset | Remaining effect/render parity and UI |
| 6 | P0 | Multi-track independent audio levels | Disabled unsupported controls in UI | Implement only matching actual renderer semantics |
| 7 | P0 | Actual audio fades/ducking and final QA | Private audio mastering, AAC, SHA tests | Spoken audio and more real mix profiles |
| 8 | P0 | Accurate timeline frame scrub/playback | Focusable keyboard video region supports 1/10-frame seek without editing draft, new mobile Playwright | Actual visual decoded-preview parity remains |
| 9 | P1 | Deep OpenReel adopted capabilities | Split/trim/reorder/snap/zoom/undo/repeat implemented | Unsupported advanced controls remain disabled |
| 10 | P1 | Mobile touch/keyboard/a11y/browser | New keyboard jog, approved readonly navigation, keyboard conflict avoidance, Playwright tests | Comprehensive manual accessibility/device usability |
| 11 | P0 | Near-black/repeat/motion/overlay detection | Added encoded 53/57.5/59.3s endcard proof (old rack repeated); mutation/forged receipts denied; F4-62 60 scene samples remain | Actual new Full-HD minute and human quality review pending |
| 12 | P0 | Typography/endcard/caption and shot composition | New distinct 55–60s disclaimer storyboard + encoded endcard QA; actual libass reviewer captions | **New native 60s footage + text legibility and human review pending** |
| 13 | P1 | Private input/license/dependency integrity | SHA-pinned source, npm audit, F4-63 mutation guard | Commercial attribution and transitive notices approval |
| 14 | P1 | CPU/RSS/latency budgets 15/30/60 | Prior CPU 30s benchmarks; local 60s five-probe QA took ~25.44s/136844 KiB max RSS | Real revised runner Azure budget |
| 15 | P1 | Worker retry/cancel/race/cleanup tests | Existing feature-owned source tests | Real v2 worker/RLS and hosted concurrency |

## Parallel cross-feature contracts — send handoffs, do not bypass owners

| # | Owner | Expected input | Status |
|---|---|---|---|
| 16 | F2 | Independently approved creative_direction/script/offer revision | Handoff to draft PR #551 |
| 17 | F2 | Licensed audio and actual voiced word-timed captions | Handoff to draft PR #551; test editorial captions are NOT speech |
| 18 | F3 | Tenant-granted original product/model bytes and identity/license | Synthetic test-byte #630 MERGED; actual approved retailer handoff absent |
| 19 | F5 | Approved encoded garment-matched real motion | Draft PR #465 source; GPU OFF, actual inference unavailable |
| 20 | F7 | Human-reviewed semantic trims/captions/cuts | Draft PR #513; only supported contiguous trims compile |
| 21 | F2/F3/F5/F7/F4 | End-to-end real approved integrated media | Mock/stock technical handoffs pass only, no true retailer Reel signoff |

## Coordinator-owned integration/production gates — cannot self-merge

| # | Owner | Expected action | Current blocker |
|---|---|---|---|
| 22 | Coordinator | Runtime-only deterministic Functions ZIP manifest preserving license, rollback, ELF, member guards | PR merged-base Python tests fail ZIP >120 entries; documented in FEATURE4_AZURE_HANDOFF.md |
| 23 | Coordinator | Rebase/reconcile main, 4/4 PR and postmerge 4/4, merge only after review | PR #322 remains draft |
| 24 | Coordinator | V2 JWT/tenant-approved snapshot & RLS | Feature4 HTTP adapter source-only, not live |
| 25 | Coordinator | Atomic lease/outbox/quota/accounting one-charge | Cannot bypass existing jobs/billing |
| 26 | Coordinator | Expiring same-shop private signed output & revocation | Private preview source-only |
| 27 | Coordinator | Queue retry/poison/cancel/cleanup hosted checks | Offline tests not Azure proof |
| 28 | Coordinator | Node22/Chromium/FFmpeg v2 worker package, lease/memory/cold-start | Local runtime preflight only |
| 29 | Coordinator/#249 | Repair/verify Azure HTTP timeout issue | Independent Azure canary required |
| 30 | Coordinator QA | Signed-in DEV 15/30/60 E2E + negative cross-tenant | Not run; no user/customer media in public CI |
| 31 | Retailer owner + coordinator | Exact finished MP4 license/visual/audio approval, canonical project docs and launch | NO commercial release approval |

## Evidence and immediate next work

- Owned source changes: `3cb13517`, `d1c7021e`, `80b54465`, `52bd614b`, `3bd94dd6`, `b6acbcc3`; F4 docs and shared-owner handoffs.
- Earlier 60s original Pexels source artifact was independently decoded in 60 interior samples (5 per each of 12 provenance-derived scenes); none almost all black, minimum sampled mean luma 34.69. 25.44s wall and 136844 KiB peak Python-process RSS. This is **not** the updated standalone current-head runner and not a commercial acceptance or video quality guarantee.
- PR merge-base Python/uv failure reproduced in logs at `scripts/deploy/package.py:134`; do not increase member cap or disable tests to make PR green.
- F2/F5/F7 PRs #551/#465/#513 and F3 merged PR #630 received direct source/rights/approval handoffs.
- Latest branch/PR CI runs require observation at the actual terminal commit; logs, not assumptions, determine status. Coordinator alone updates `docs/{PROJECT_STATE,NEXT_TASK,DECISIONS,WORK_LOG}.md` after integration.


## 2026-10-29 afternoon continued independent sprint — source checkpoints, no false closure

- CI on preceding exact branch head `50e700966f`: push [#40869461422](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40869461422) **4/4 SUCCESS**. Pull-request merged-base [#40869468107](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40869468107) **3/4**, with coordinator-owned Python ZIP >120 member count failure. PR remains draft and unmerged; latest main has advanced since baseline.
- F4-65: final `feature4_minute_quality_receipt.py` cannot issue `NATIVE_60S_TECHNICAL_EVIDENCE_ONLY` if any actual private captioned MP4/SRT/VTT/burn report, v2 scene visibility proof, or 55–60s encoded endcard QA proof is absent. Tests assert incomplete chains are rejected **before** media scanning and retain real garbage-media, oversized source and symlink negatives.
- F4-66: new `feature4_endcard_qa.py` performs actual FFmpeg 53/57.5/59.3s source-frame comparison and binds SHA/timestamps to final accepted receipt. Unit tests physically encode synthetic 60s red/blue and red/red H264/AAC scenes and reject old held shot, wrong 58s start, source mutation, forged approval. Local FFmpeg sanity red/blue change 46.83, internal stability 0.0; archived rack hold at 52.5→57.5 changed only 16.397. **Updated 60s HyperFrames media pipeline not yet rerun; do not claim visual acceptance.**
- F4-67: TimelineStudio video-track keyboard focus and preview-only frame jogging, one or ten frames, including approved direction but never editing assets/rights/copy; Playwright mobile negatives. Source+docs pushed to F4 branch, exact-head CI must be inspected. No WineShopPOS, GPUs, paid APIs, production cloud, coordinator-owned workflows/contracts or shared docs changed.

## 2026-10-29 — MVP-first Batch 1 / 30-second encoded edit parity

- **Implemented, source+local archive evidence:** The existing exact Timeline Studio JS split/reorder `[0,4,14,20]` → trusted Python compiler → 30s 540p HyperFrames **encoded mock** now runs `feature4_edited_export_qa.py` in the same existing media CI job; no second render. It verifies 30s H264/AAC, hashes source before/after four actual FFmpeg decoded scenes (2/7/16/24s), rejects gross swapped/missing shots and identical second video replay, and emits fail-closed technical-only report. Importantly this is a **synthetic owner-rejected technical fixture**, not garment/product visual quality or exact-frame inpoint proof.
- **Actual archived prior 30s edited MP4**, SHA-256 `1c69ede47eac07a2dba118ceca59beca118f337d67e801b7eecc4bbe94b57153`, 30.000s/540x960, passed the same local four-frame decoder/proof: video-pair delta 3.53; photo-pair 19.017; minimum video/photo 21.095. Four focused negative/positive Python tests pass locally, covering forged order, false replay, source mutation, wrong duration, and symlinks.
- **Status against 31 tasks**: progress on **#4**, with the 30s split/reorder encoded mock *technical regression slice* complete locally; duplication encoded pixels and real customer 30s footage remain open, so DO NOT relabel the full #4 (or MVP) as commercially complete. First run exact-head branch 4/4 and merged-base PR CI; shared ZIP issue #22 remains coordinator-owned. This batch touches only Feature4-owned CI harness, source, tests and docs. No GPU, cloud, WineShopPOS or production change.

## 2026-10-30 — F4-13/F4-15 source-only race and storage-key hardening (stacked draft PR #792)

- Branch `feat/feature4-pre-render-lease-guard-20261030` starts at existing F4 draft PR #322 head `e32a8da61`, not current main; no unrelated coordinator-owned files touched.
- F4-15: after all private downloads and before CPU/Chromium rendering, recheck both current lease and active rights. A stale or revoked claim now returns `STALE` without running the renderer, uploading output, finalizing the job or settling usage. Negative test revokes each gate during media staging.
- F4-13: reject tenant storage keys ending in a slash, containing dot-only path components, or containing ASCII control characters; tests reject these before any download. This does not claim an external retailer rights review.
- **Status:** source patch and deterministic regression tests proposed in draft PR #792. Exact-head CI, coordinator acceptance, existing draft #322 integration, fresh postmerge main 4/4, and live lease/rights checks remain open. These two broad numbered tasks are **NOT DONE**. No GPU, paid model, DEV/PROD deployment, media sample or WineShopPOS edit.
