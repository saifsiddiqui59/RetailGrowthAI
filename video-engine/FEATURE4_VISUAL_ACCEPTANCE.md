# Feature #4 professional Reel acceptance — OWNER NOT ACCEPTED (2026-10-26)

The owner rejected the original 30-second synthetic animation as basic. A technical render succeeding is **not** equivalent to a premium, publishable fashion advertisement. This document is the Feature #4 team handoff to the existing coordinator; it is not a new shared API.

## Low-cost production sequence (reuse existing infrastructure)

1. **Feature #2**: approved shop-specific copy, explicit promotion/terms and CTA. Never invent a discount. The current internal `creative_reel_v1` compiler enforces literal approved marketing claims.
2. **Feature #3**: a retailer-approved original kurti photograph, higher-quality poster background, verified logo and rights/provenance. Product color, fabric, embroidery, length and silhouette must match the actual uploaded item; human review is mandatory.
3. **Feature #5**: an actual approved video clip of an AI fashion model wearing THAT kurti, walking in a believable boutique. Video must preserve garment identity and not exhibit changing limbs or fabric, model flicker, distorted hands or copied stock shots falsely labeled as bespoke generation. Rendering a panning still is **not** proof of realistic AI motion.
4. **Feature #7** (optional): approved speech-aware editing timings. Feature #4 should not fabricate a transcript or claim beat-sync is semantic editing. Preserve intelligible voice and duck music during spoken promos.
5. **Feature #4**: combine approved inputs in the existing application-owned HyperFrames timeline with FFmpeg-compatible H.264/AAC export. No replacement of Supabase tenant isolation, Azure Functions worker, queues, FFmpeg or existing charge ledger.

## Visual/functional acceptance checklist

- [ ] Real approved human-model walking clip visibly moves, with consistent anatomy, garment texture and advertised product.
- [ ] Opening shop identity readable within three seconds, using actual logo—not test shop text.
- [ ] Narration/source-video audio intelligible, with musical bed never masking important speech.
- [ ] Product reveal uses source image at native useful sharpness; no deceptively pixelated 128px still upscaled to 1080p.
- [ ] Exact approved `Diwali Sale — 20% OFF` is readable on screen. The offer, product, poster and CTA do not cover or contradict each other.
- [ ] Fashion-quality art direction: meaningful camera/motion, intentional pace, balanced spacing, consistent palette, restrained motion, no generic card-slideshow impression.
- [ ] Intro, motion, product, discount and closing CTA reviewed at 9:16 mobile display size as well as desktop.
- [ ] Real H.264/AAC MP4 verified at exactly **1080×1920**, **24/30 fps**, correct duration (15/30/60 seconds), `yuv420p` compatibility, sensible file size and deterministic retry.
- [ ] 30-second AND 60-second actual real-media exports, cold start and Azure DEV render costs/timing measured against worker limits (15s synthetic full HD is an intermediate gate only).
- [ ] Existing signed private output, JWT/membership, media license, quota/ledger single-charge, retry and tenant isolation checks pass end-to-end on DEV.
- [ ] Owner watches and expressly approves the real-media result.

## Automated evidence (what the tests can and cannot prove)

- `video-engine/hyperframes/ci-smoke.sh` renders real CPU HyperFrames output in CI. The original 30s/540p fixture validates H.264/AAC output, scene changes, intro brand and known synthetic 480 Hz source-audio mix. Added **15s/1080p** original synthetic stress fixture validates actual encoded resolution, fps, pixel format and five separate scenes, and extracts high-resolution review frames.
- `video-engine/hyperframes/render.mjs` now checks exact requested resolution and fps against the private compiled render configuration. `video-engine/render_adapter.py` independently validates final MP4 before atomic private file publication.
- These are **automated engineering gates only**. Neither synthetic silhouette fixtures nor image-difference statistics detect realistic garment fidelity, true AI motion, product misrepresentation, small text clipping or speech intelligibility.
- Do not show the synthetic render as a real retailer reference or mark this feature ready for a paying retailer.

## Release ownership and blocker boundaries

Feature #4 may change `video-engine/**`, `tests/media/**` and `frontend/src/features/video/**` only. Main, coordinator-owned `docs/**`, shared routes/API, deployment, private storage and subscription ledger remain under coordinator control. No production changes, new billable Azure resources or WineShopPOS modifications. PR #322 stays **draft** until approved real photos/Feature #5 media, human QA and hosted integration tests are available.
