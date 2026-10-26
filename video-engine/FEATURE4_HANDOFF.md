# RetailGrowthAI Feature #4 — Coordinator handoff (2026-10-26)

## Branch scope and current verified boundary

Branch: feat/feature4-professional-video-studio (based on main 140a9f8617). This is a first **implementation increment**, not Feature #4 completion or approval to change the shared API. PR #318 is an **unmerged draft architecture**.

Added:
- video-engine/professional.py: strict rg_video_v2 compiler producing a private HyperFrames HTML project from tenant-bound, trusted, staged, rights-approved media IDs. Supports text, image, poster, media and beat-grid synchronized modes as a **source contract** (15/30/60 seconds, 540/1080 portrait, 24/30 FPS), three styled templates, approved offer/title/CTA escaping, finite contiguous scenes, trim ranges, an authorized music ID, no raw customer HTML/CSS/JS/remote media.
- video-engine/audio_catalog.py and empty audio_catalog.json: operator-curated fail-closed rights/territory/platform/usage/expiry guard; no commercial music or SFX approved or bundled. This is a local policy gate, not a claim of third-party license review.
- video-engine/beat_grid.py: bounded CPU-only onset estimates for trusted PCM16 WAV (source must already pass backend audio authorization and FFmpeg normalization). This is approximate transient detection, not source-aware voice ducking or a professional rhythmic transcription.
- video-engine/hyperframes/: pinned versioned Node producer adapter with local MP4 render and ffprobe checks; no hosted API, no provisioning and no activation in Azure.
- frontend/src/features/video/{video-model.mjs, VideoStudio.jsx, VideoStudio.css}: isolated responsive video-specific draft editor, mode/template/media/music selectors, scene reordering, mobile storyboard mock, guarded render callback and signed output slot (not mounted into shared routes).
- tests/frontend/video-model.test.mjs: React-independent video plan controls and authorization-flag tests under existing frontend tests.
- tests/media/test_feature4_audio_catalog.py and test_feature4_beat_grid.py: offline rights restrictions and synthetic percussion timing.
- tests/media/test_feature4_professional.py: compiler authorization, modes, source-audio behavior and injection regressions under existing FFmpeg CI job.
- Legacy video-engine/render.py, queue/outbox, DB/Auth, React root app and Part 2/3 source all deliberately unchanged.

### Versioned proposed contract (coordinator approval required before live API integration)

```json
{
  "version": "rg_video_v2",
  "shop_id": "11111111-1111-4111-8111-111111111111",
  "mode": "image",
  "template": "cinematic",
  "duration_seconds": 15,
  "output": {"width": 1080, "height": 1920, "fps": 30},
  "scenes": [
    {"start": 0, "duration": 15, "asset_id": "approved_product_1", "headline": "THE NEW COLLECTION"}
  ],
  "cta": "Visit our store",
  "music_asset_id": null
}
```

Trusted backend creates separate server-staged manifest (shop_id and asset ID -> kind, relative file path, rights). A caller-supplied manifest is **not an authorization mechanism**. Server must resolve current tenant, verified rights, approved claims, idempotent job, quota and signed private output via existing services. For Feature #7 use this same v2 plan as a final renderer instruction: it supplies already approved timed inserts, while Feature #7 performs transcription/semantic timing independently. No alteration to docs/INTERFACES_V1.md in this worker branch.

### Offline usage (no cloud, when ffprobe installed)

```sh
python3 video-engine/professional.py --plan /trusted/plan.json --manifest /trusted/manifest.json --asset-root /trusted/assets --output-dir /tmp/new-empty-project
cd video-engine/hyperframes
npm install --ignore-scripts
node render.mjs /tmp/new-empty-project /tmp/validated-private-output.mp4
```

Producer integration follows current @hyperframes/producer 0.8.x JavaScript createRenderJob + executeRenderJob API. This **has not yet been exercised** in CI. Browser rendering may need template/time/clip/audio adjustments after actual output inspection. The CPU job must restrict network egress, process time, memory, concurrency, local scratch and private upload. Never execute arbitrary HTML or service secrets in the browser.

## Explicit pending work (not claimed complete)

1. Run a real pinned HyperFrames/Chromium CPU MP4 on authorized original clothing fixtures. Verify frame screenshots, animated products/crops, scene timing, H.264/AAC, source video speech/audio mix, typography safe zones and 15/30/60 outputs. Perform repeatable wall-clock RSS/CPU/cost comparisons against existing FFmpeg and Feature #5 premium clips; current numbers are unknown.
2. Improve three templates visually and verify real rendering behavior, not just HTML source/CSS. Improve true fade/audio duck automation and sound effects; source-only PCM16 beat-onset detection now exists, but real source-licensed mix, automatic binding to video plan and quality-checked beat sync remain outstanding.
3. Curate and individually audit license evidence for Mixkit/Pixabay assets including SaaS redistribution; currently there is **no third-party music bundled or cleared**. Audio requires a preapproved manifest.
4. Coordinator-approved v2 transport, central quotas/claim-fenced worker/private storage/subscription usage and Azure Container Apps Jobs cost gate. **Do not change shared APIs, migrations, Functions ingress or #249 settings without review.**
5. Feature #1 layout review, video-specific React editor, live status/preview/history/private signed download, review/save/approval, signed-in browser E2E, invalid media, job idempotency/timeouts/retries and tenant negative integration.
6. Three actual reviewable MP4 sample artifacts, four inspected green CI checks on the final PR, hosted DEV acceptance under separate approval. No hosted run, resource change, public API, production or WineShopPOS modifications here.

## License and references

HyperFrames upstream https://github.com/heygen-com/hyperframes LICENSE is Apache-2.0 (HeyGen 2026). Pin producer 0.8.185; verify its published package and transitive notices before deployment. FFmpeg remains the existing fallback. MoneyPrinterTurbo is only a reference; no code was copied. No Mixkit/Pixabay track was downloaded or granted rights by this PR.

## Coordinator document policy

AGENTS.md and docs/PARALLEL_WORK.md reserve docs/PROJECT_STATE.md, docs/NEXT_TASK.md, docs/DECISIONS.md, docs/WORK_LOG.md and docs/INTERFACES_V1.md to coordinator. Please update these upon accepting/integrating this branch; this feature-owned handoff avoids competing updates to shared tracking.
