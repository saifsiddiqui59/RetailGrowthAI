# Feature #4 — Cross-feature Creative Reel Contract (internal, v1)

**Implementation branch:** `feat/feature4-professional-video-studio` • Draft PR #322. This interface is **proposed for coordinator approval** and does **not** change `docs/INTERFACES_V1.md`, the deployed Azure Functions API, existing render jobs, Supabase RLS, migrations or subscription ledger.

## Ownership and trust

1. The **coordinator/orchestrator** authenticates an existing shop and checks membership, quotas, script/offer approval and media rights using the **existing** secure tenant DB, claim-fenced job and private Storage service. It supplies a private JSON request and a **server-generated** media manifest to Feature #4.
2. **Feature #2** supplies an approved script record with an explicit `approved_text` list and final CTA. Feature #4 rejects headlines, prices and offers not **exactly** in that list.
3. **Feature #3** supplies approved product stills and posters. Existing retailer brand kit supplies name, color and logo. **Feature #5** supplies actual video clips, or explicit failure status with optional approved still-image fallback. **Feature #7** supplies an approved final edit plan with timeline version. Feature #4 does not transcribe speech or decide semantic scene timings.
4. **Feature #4** verifies provenance against the server-generated manifest, validates media bytes and contiguous 15/30/60s scenes, compiles an application-owned HyperFrames composition and invokes the pinned producer in a private, bounded local process. It records the unchanged `video_job_id` and `idempotency_key` in lineage. This library **never bills, enqueues, uploads, or returns a user-signed URL**: existing coordinator APIs/queues must do these operations after final acceptance.

## Suggested internal schema

```json
{
  "version": "creative_reel_v1",
  "shop_id": "11111111-1111-4111-8111-111111111111",
  "campaign_id": "22222222-2222-4222-8222-222222222222",
  "video_job_id": "33333333-3333-4333-8333-333333333333",
  "idempotency_key": "logical-request-0001",
  "template": "cinematic",
  "duration_seconds": 30,
  "output": {"format": "mp4", "width": 1080, "height": 1920, "fps": 30},
  "script": {
    "source_feature": "feature2",
    "approved": true,
    "approval_id": "approved-script-v1",
    "approved_text": ["Diwali Fashion", "Luxury Boutique", "New Season Styles", "Diwali Sale", "20% OFF", "Our Kurti Collection", "Visit Our Store"],
    "cta": "Visit Our Store"
  },
  "brand": {"shop_name": "Fixture Clothing Store", "primary_color": "#d4a754", "secondary_color": "#17112f", "logo_asset_id": "store_logo"},
  "allow_image_fallback": false,
  "scenes": [
    {"order": 0, "start_time": 0, "duration": 3, "headline": "Diwali Fashion", "animation_preset": "glow"},
    {"order": 1, "start_time": 3, "duration": 7, "asset_id": "walk_clip", "asset_type": "video", "source_feature": "feature5", "motion_status": "ready", "headline": "Luxury Boutique"},
    {"order": 2, "start_time": 10, "duration": 6, "asset_id": "product_image", "asset_type": "image", "source_feature": "feature3", "headline": "New Season Styles"},
    {"order": 3, "start_time": 16, "duration": 6, "asset_id": "product_image", "asset_type": "image", "source_feature": "feature3", "poster_overlay_asset_id": "sale_poster", "headline": "Diwali Sale", "text_overlay": "20% OFF", "animation_preset": "pop"},
    {"order": 4, "start_time": 22, "duration": 5, "asset_id": "product_image", "asset_type": "image", "source_feature": "feature3", "headline": "Our Kurti Collection"},
    {"order": 5, "start_time": 27, "duration": 3, "asset_id": "sale_poster", "asset_type": "poster", "source_feature": "feature3", "headline": "Visit Our Store"}
  ],
  "music_asset_id": null
}
```

For Feature #7 add `edit_plan: {"source_feature":"feature7","approved":true,"approval_id":"edit-reviewed-00001","timeline_version":"creative_reel_v1"}`; leave the rendered scene objects identical. For sound effects use `sfx_asset_id` and optional `sfx_source`; each must resolve to separately licensed, server-approved, tenant-owned audio. Poster inserts use `poster_overlay_asset_id`. Trimmed clips use `trim_start` (seconds) and default source audio preservation; `mute_source: true` requires explicit approval. The `source_feature` field of the server-created manifest must match the scene: `feature5` permits **video only**, `feature3` permits images/posters, `retailer` permits logo/user media/audio, `stock` permits media/audio. Enforce media rights separately in the existing backend; request JSON assertions alone never confer authorization.

### Failure and fallback behavior

- When Feature #5 fails, the original premium request may name `motion_status:"failed"`, `fallback_image_asset_id:"approved_still"`, `allow_image_fallback:true`. **No fabricated video row is required.**
- The builder emits the approved still-image animation and an immutable lineage event `IMAGE_ANIMATION_NOT_AI_HUMAN_MOTION`; it never claims a generated motion scene, and it never triggers another premium generation.
- Without approved fallback or still-media rights, the request fails closed and the approved campaign is not altered.
- Stable `video_job_id` and `idempotency_key` must use the existing durable claim-fenced ledger/one-charge semantics. Source module has **no usage writes**. Private output is committed without overwriting an existing logical job result. On ambiguous completion, read the authoritative existing ledger rather than issuing a second billable request.

## DEV commands (server operator, not browser)

```sh
python3 video-engine/render_adapter.py --request /trusted/internal-request.json \
  --manifest /trusted/authorized-media-manifest.json --asset-root /trusted/media \
  --output-dir /trusted/private-output --compile-only
# After pinning producer and provisioning a no-egress Node>=22/Chromium/FFmpeg CPU worker:
python3 video-engine/render_adapter.py --request /trusted/internal-request.json \
  --manifest /trusted/authorized-media-manifest.json --asset-root /trusted/media \
  --output-dir /trusted/private-output --timeout 780
```

Compiler writes `index.html`, `render-config.json`, staged authorized assets, and `lineage.json`. CLI render validates H.264, AAC, exact width/height, FPS and ±0.25s duration with ffprobe. No double transcode is performed. A sample synthetic timeline with 6 scenes and generated 8s fixture clip is covered by `tests/media/test_feature4_cross_feature.py` on GitHub Actions.

## Pending release gates

A **real HyperFrames producer run** on Node 22/Chrome and inspected rendered frames; licensed song/SFX provenance (none currently approved), source voice intelligibility, precise volume ducking/transition QA, simultaneous source video clip layering, approved brand-logo visual fidelity, 15/30/60s CPU/RSS and prices, three representative real rendered videos, live worker bound to existing claim/recovery, private signed preview/download, coordinated frontend mounting, tenant live E2E and four current-head CI checks. The locally generated synthetic reference video is a **concept-only visual fixture**, not a render from this module or a generated AI model clip. No Azure deployment/resource creation or issue #249 ingress changes permitted from this feature branch.

Coordinator should update `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md` only after accepting this additive contract.
