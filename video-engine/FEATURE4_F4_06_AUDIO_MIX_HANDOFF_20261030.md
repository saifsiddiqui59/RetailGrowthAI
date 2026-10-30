# Feature #4 F4-06 — truthful read-only audio mix (2026-10-30)

**Task ID:** F4-06. **Status:** SOURCE IN PROGRESS, not integrated DONE.
**Parent:** draft PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
**Scope:** Feature4-only UI/read-only audio parity, offline unit tests. No model inference, FFmpeg render, cloud, PROD, schema or shared-doc changes.

## Source change and acceptance slice

- `audio-mix-display.mjs` exposes fixed HyperFrames levels **only when determinable**: 55% licensed music on still/silent-only scenes, 12% bed under approved full-Reel narration, 100% narration, 25% scene SFX (2s maximum). These are **renderer settings**, not actual measured acoustic loudness.
- When any approved unmuted source video is present without narration, browser metadata cannot prove whether the renderer will duck music; the UI **omits** the numeric gain widget and labels the level unverified pending trusted source-audio probe. No fabricated 100% default or editable gain.
- `TimelineAudioClip` adds optional `hideGain` only for that case. All other upstream behavior stays unchanged.
- Offline Node tests cover fixed/unknown levels, source mute, tenant/rights denial, absent tracks and SFX limits. This does not grant rights, approve real audio, perform source audio probing or implement arbitrary independent multitrack gain controls.

## Remaining F4-06 acceptance / blockers

- **Owner:** Feature4 + coordinator for any shared contract change.
- **Required output:** approved versioned audio-mix schema and actual renderer support for independent track gain controls, with exact encoded AAC parity and rights-scoped source proof.
- **Acceptance:** one-to-one saved/approved draft → trusted renderer gain → decoded AAC technical tests, no stale tenant/approval edits, passing exact-head PR 4/4 and fresh postmerge main 4/4.
- **Dependency:** F2-APPROVED-VOICE for genuine reviewed narration; current fixed-gain fixtures are not spoken audio.
- This branch must remain stacked on #322 and **must not merge directly to main**. Existing #322 merged-base CI ZIP >120 issue belongs to coordinator ISSUE-650. No user-facing media sample.

## Verification receipt

- GitHub branch commits: `49f4209e46aabeb1bd57e218fc1884b7ef1220d9`, `f3dbe9089fa6ab76b1b8af7fcefd35f8a4749da3`, `e99a131529631afd964310697ae6b09758f75518`, `615d22e33a7d2a903d12cb14ae6ddd576d0c242e`.
- **CI:** inspect exact final branch SHA after push; do not infer success from parent branch runs. Full F4-06 task remains IN PROGRESS pending actual renderer gain control/approved contract and integration.
- Proposed coordinator status receipt: `F4-06` source-progress only, no `integrated_done` event; coordinator owns `coordination/task_progress.json` and canonical docs.
