# RetailGrowthAI Feature #4 — Actual Timeline Studio source adaptation

Checkpoint 2026-10-28. **Source-only, PR #322 draft; no Azure, GPU or public editor deployment.**

## Selected real upstream source

- [MartinDelophy/ai-video-editor](https://github.com/MartinDelophy/ai-video-editor), immutable research commit `e1091feccca3be8832b507eb7e17c9e55eb2233a` (MIT).
- Preserved original MIT LICENSE, © 2026 MartinDelophy, in `frontend/src/features/video/vendor/LICENSE`. This is adapted real upstream editing code, not a claim of full upstream-app deployment.
- Upstream pinned commit's actual [Actions #40501035304](https://github.com/MartinDelophy/ai-video-editor/actions/runs/40501035304) SUCCESS: `npm ci`, ESLint, TypeScript typechecks (host and app), Vite production build. That upstream package does **not** define a standalone `npm test` script. Direct local clone/npm installation and launching the entire original application was **not possible in the available network-restricted runtime**; no fabricated local run.
- Research ownership from [PR #497](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/497): **Feature #2** authors approved `creative_direction_v1`, dialogue, story, camera and exact motion prompts; **Feature #4** assembles, edits and verifies; **Feature #5** validates/inferences motions; **Feature #7** semantically edits existing uploaded footage.

## Original source → Feature #4 source map

| Upstream pinned source | Feature #4 adaptation | Real reused capability |
| --- | --- | --- |
| `src/lib/timeline.js` | `frontend/src/features/video/vendor/timeline.js` | Scene ranges, captions, lanes, reorder, timing, formatting |
| `src/lib/timelineScale.js` | `frontend/src/features/video/vendor/timelineScale.js` | Zoom/ruler ticks, bounded viewport math |
| `src/lib/projectTrackState.js` | `frontend/src/features/video/vendor/projectTrackState.js` | Multi-track visibility/lock helpers |
| `src/lib/editorHistoryCore.ts` | `frontend/src/features/video/vendor/editorHistoryCore.mjs` | Exact upstream push/undo/redo algorithm converted from TS generics to JS |
| `src/lib/timelineCutActions.js` | `frontend/src/features/video/vendor/timelineCut.js` | Original `splitVisualSegmentState` including video sourceStart offsets; unsupported keyframe logic omitted |
| `src/components/TimelineClips.jsx` | `frontend/src/features/video/vendor/TimelineClips.jsx` | Real React caption/audio clip controls and resize handles |
| `src/components/TimelineGain.jsx`, `.css` | `frontend/src/features/video/vendor/TimelineGain.*` | Original audio-gain UI, **disabled** when final renderer cannot reproduce it |
| `src/config/editor.js` | `frontend/src/features/video/vendor/editorConfig.js` | Isolated original timing constants; avoids unrelated upstream host/model dependencies |
| `src/components/ui.jsx` | `frontend/src/features/video/vendor/WaveformStrip.jsx` | Simplified static waveform adapter, not modeled/synthetic speech or AI waveform |

## RetailGrowthAI integration

- `TimelineStudioSurface.jsx` and `.css`: multi-track timeline rendered **inside** existing feature-owned React workspace, edit/seek, HTML drag reorder, mobile earlier/later controls, source video trims, real segment splitting, caption lane, music lane, undo/redo, ruler and playhead. It **does not** import or run upstream's cloud host, local accounts, browser-WebCodecs exporter or paid models.
- `timeline-studio-bridge.mjs`: converts upstream timeline operations into the **exact existing** `rg_video_v2` scene allowlist. Keeps 15/30/60s duration, 1–12 scenes, minimum 0.5s clips, shop-private approved asset IDs, unchanged approved captions/offers/CTA. Clip split reuses same approved image/video, advancing video trim source offset. The existing `feature4_intent_compiler.py` remains authoritative for server approval/rights.
- `creative-direction-adapter.mjs`: proposed frontend read-only `creative_direction_v1` preview bridge, requires Feature2 reviewed shop/campaign/approval/hash, exact approved headline/offer/CTA/media/allowed transitions and no unapproved assets. **UI browser approval flags are NOT authorization.** Feature2 schema and DB snapshot are not coordinator-frozen yet; consumer route remains OFF.
- `feature4_motion_handoff.py`: source-only, bounded F2 approved motion brief → F5 legacy 5s/480p profile request. Preserves rich prompt and choreography data verbatim and derives shop-scoped idempotency. Coordinator must atomically reserve/claim/outbox before invoking callback. **No actual GPU, Wan, billed inference, queue deployment or live media receipt**.
- Final export remains HyperFrames + FFmpeg fallback. No second independent renderer. Upstream `projectRenderPlan.js` intentionally **not** used: its offline path drops requested overlays/captions and would create false preview parity.

## Explicit capabilities not yet claimed

- Upstream full 200KB `Timeline.jsx`, 66KB `PreviewStage.jsx`, 127KB `App.jsx` and many unsupported mask/keyframe/3D effects are **not** imported wholesale. This is a bounded adoption of working upstream components and editing algorithms, **not** the entire original UI; deeper editing parity is still pending.
- Independent subtitle-text editing, per-track gain, arbitrary keyframes, sophisticated source speech alignment and arbitrary motion transforms remain disabled or pending. Only renderer-supported effects are actionable; no silent drop of user-selected effects.
- The Feature2 `creative_direction_v1` shape shown in tests is a **proposed** handoff, not a merged cross-feature contract. A real Feature2 review must be reissued if a director-locked storyboard is changed.
- No actual Wan inference, original retailer kurti or human-model quality approval. Mocked media tests are engineering evidence only, not premium fashion-campaign acceptance.
- No Azure v2 DB/queue/API contract, authenticated hosted E2E, signed output publishing, GPU or PROD delivery without coordinator approval and issue #249 remediation.

## Verification requirements

- Existing `tests/frontend/timeline-studio-adoption.test.mjs`: actual borrowed timeline geometry, caption lanes, zoom, split/trim, history, F2 contract and malicious media denial.
- Existing `frontend/e2e/timeline-studio.spec.mjs`: actual browser interaction with adapter and mobile locked package (Vite-served test fixture, no public test route).
- Existing `tests/media/test_feature4_motion_handoff.py`: mock F2→F5 security, exact prompt fidelity, no double dispatch and no GPU.
- Existing real 30s synthetic 1080×1920 HyperFrames/FFmpeg CI; server snapshot/tenant/rights tests remain mandatory.
- Inspect **exact latest head** four-job CI after every push and report failures separately. Previous runs with cancelled jobs or upstream passes do not prove the latest edited source.
