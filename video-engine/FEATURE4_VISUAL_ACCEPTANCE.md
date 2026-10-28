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

- `video-engine/hyperframes/ci-smoke.sh` renders real CPU HyperFrames output in CI. The original 30s/540p fixture validates H.264/AAC output, scene changes, intro brand and known synthetic 480 Hz source-audio mix. A **15s/1080p** synthetic first proof passed 4/4 CI [#40307861324](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40307861324) (15.000s, 3.06MB H.264/AAC, 24fps/yuv420p; renderer ~49 seconds on GitHub CPU). The default acceptance gate now renders the full **30s/1080p** synthetic mode with exact output probe and five distinct scene screenshots; [4/4 GitHub Actions success #40309070130](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40309070130), 30.000s and 5,616,633-byte H.264/AAC MP4. This is NOT genuine AI fashion footage.
- `video-engine/hyperframes/render.mjs` now checks exact requested resolution and fps against the private compiled render configuration. `video-engine/render_adapter.py` independently validates final MP4 before atomic private file publication.
- These are **automated engineering gates only**. Neither synthetic silhouette fixtures nor image-difference statistics detect realistic garment fidelity, true AI motion, product misrepresentation, small text clipping or speech intelligibility.
- Do not show the synthetic render as a real retailer reference or mark this feature ready for a paying retailer.

## Release ownership and blocker boundaries

Feature #4 may change `video-engine/**`, `tests/media/**` and `frontend/src/features/video/**` only. Main, coordinator-owned `docs/**`, shared routes/API, deployment, private storage and subscription ledger remain under coordinator control. No production changes, new billable Azure resources or WineShopPOS modifications. PR #322 stays **draft** until approved real photos/Feature #5 media, human QA and hosted integration tests are available.

## Full-minute CPU proof and pending realistic media gate

A real **60.000-second, 1080×1920, H.264/AAC** synthetic output and six QA frames were verified in [CI #40318231205](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40318231205). This proves format/time feasibility on GitHub CPU, not Azure costs or photoreal human motion. The visual frames show a simple illustrated kurti silhouette, so the owner-level fashion quality gate remains unaccepted.

The coordinator must adopt the additive trusted source-only worker callback contract in [FEATURE4_AZURE_HANDOFF.md](FEATURE4_AZURE_HANDOFF.md), reviewing actual DB claim/lease/media/ledger semantics before any hosted v2 enablement. No cost-bearing resource changes are authorized by this handoff. All commercial filming/music/garment media must remain explicitly licensed and merchant-reviewed.

## New source-only human review enforcement (F4-10)

`feature4_release_gate.py` requires the actual SUCCEEDED Full-HD job proof, immutable authorized Feature3 product + Feature5 motion media IDs, no motion fallback, verified source rights, `synthetic_fixture=False` on both verified DB media rows, and a same-job same-tenant saved human review with checks for model realism, garment fidelity, natural walking, branded logo, approved sale terms, licensed music, speech and mobile text readability. CI unit tests are intentionally synthetic and **do not represent a real owner-approved video**. This must be integrated by the coordinator into the protected release/publish process before calling the feature production ready.

## 2026-10-28 — OWNER QUALITY REJECTION: do not present synthetic illustrated Reel again

**Owner verdict: REJECTED.** The sample previously shared as an edited fashion Reel is not an acceptable Reel or even a showcase placeholder. It is composed of elementary vector-style/faceless illustrated fashion assets, repeated synthetic walking animation, simple visual sequencing and a sine-wave instead of spoken narration. The owner's later explicit rejection overrides any earlier positive engineering or partial visual language. **Discard the sample as product demo/showcase evidence.** It may remain privately in CI as a deterministic regression fixture for split/reorder, offer preservation, SFX/audio mix, codec and timing; a passing MP4 or frame-diversity test is categorically *not* visual-quality acceptance.

- **Marketing/showcase status: FAIL / no artifact approved.** No link to this mocked MP4 should be offered as a professional retail demo.
- **Feature4 commercial quality status: NOT COMPLETE.** No owner-reviewed real footage + product identity + movement + edit rhythm + sound/dialogue + legible offer/CTA + final render.
- **New technical safeguard:** `demo_feature4_edited_reel.py` explicitly returns `visual_quality_status=OWNER_REJECTED`, `showcase_eligible=false`, `commercial_release_eligible=false`; tests assert this and confirm the real `feature4_release_gate` rejects synthetic product and motion even with a nominal successful H264/AAC encoding.
- **Replacement bar:** a genuinely licensed, portrait real-human fashion clip or verified approved provider output (not a repeated still/cartoon), visible textile weave/embroidery and garment fidelity to tenant product; deliberate opening hook, scene-based pacing and editorial rhythm; non-obscuring designed brand/offer typography, human-intelligible voice (when scripted), correctly aligned subtitles and music ducking; real 9:16 Full-HD encoded Reel; explicit owner review on the exact finished MP4. No false claim that generic stock footage is the retailer's real garment/model.
- **Cost restriction:** GPU stays disabled. For interim engineering quality checks, use approved and license-verified **real stock footage** with clearly stated stock provenance, not claim Feature5 generated it. Source/acquisition rights and feature handoffs must be verified before any demo can be called accepted.
- **Product decision:** remove the rejected sample from demo/promotional discussion and any release claim. Keep technical regression tests and existing CI, no new renderer. PR #322 stays draft and unmerged; no WineShopPOS, cloud, or coordinator-owned files changed.
