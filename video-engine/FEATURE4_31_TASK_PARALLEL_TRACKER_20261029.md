# Feature #4 — 31-work-item concurrent execution tracker (29 October 2026)

PR #322 (DRAFT). Feature4 owner: `feat/feature4-professional-video-studio`. Review against CURRENT HEAD / merged-base CI; no cross-branch direct writes, paid GPU/cloud/PROD, WineShopPOS edits or unreviewed customer media. This is an **honest backlog**, not 31 completed tasks.

## Independent Feature #4 — work may proceed concurrently within owned paths

| # | P | Required deliverable | Current source/evidence | Remaining gate |
|---|---|---|---|---|
| 1 | P0 | Standalone revised native 60s render + caption/visibility | Existing runner calls all modules; earlier artifact real 60s | Regenerate exact current-head runner output |
| 2 | P0 | Hash-linked final 60s quality receipt | New `feature4_minute_quality_receipt.py` supports caption and v2 visibility | Full updated original/master/preview/caption/contact chain not rerun |
| 3 | P0 | 15/30/60 actual export regression matrix | Existing 15/30 CI & separate 60s stock artifact | One unified exact-code acceptance record |
| 4 | P0 | Encoded editor action parity after split/reorder/duplicate | Trusted JS/Python compiler tests; synthetic edit MP4 | Encoded visual tests for every supported edit |
| 5 | P0 | Renderer-supported transitions/fades/effects | Existing reviewed HyperFrames subset | Remaining effect/render parity and UI |
| 6 | P0 | Multi-track independent audio levels | Disabled unsupported controls in UI | Implement only matching actual renderer semantics |
| 7 | P0 | Actual audio fades/ducking and final QA | Private audio mastering, AAC, SHA tests | Spoken audio and more real mix profiles |
| 8 | P0 | Accurate timeline frame scrub/playback | OpenReel bridge and mobile test | Frame-exact visual preview parity |
| 9 | P1 | Deep OpenReel adopted capabilities | Split/trim/reorder/snap/zoom/undo/repeat implemented | Unsupported advanced controls remain disabled |
| 10 | P1 | Mobile touch/keyboard/a11y/browser | Playwright mobile and control regressions | Comprehensive manual+browser usability |
| 11 | P0 | Near-black/repeat/motion/overlay detection | F4-62 five decoded samples/scene, v2 validated receipt; local 12 scenes / 60 samples PASS; F4-63 contact source pin | CI + brief-black/full-frame and human editorial QA |
| 12 | P0 | Typography/endcard/caption and shot composition | Stock edit, timed SRT/VTT, libass reviewer, contact sheet | Diverse film material and human professional quality signoff |
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
