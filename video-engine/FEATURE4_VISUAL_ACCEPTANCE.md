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

## F4-29 — CPU freeze-screen diagnostics (source-only, commercial quality still FAIL)
`feature4_motion_diagnostics.py` now probes an already staged **local** MP4/MOV with ffprobe/FFmpeg and samples 6 decoded grayscale frames under strict time/size bounds. It records frame deltas and flags clearly frozen/repeated-still clips as `FAILED_FROZEN_OR_LOW_MOTION`; no external URL, raw user HTML, GPU or stock licensing bypass. Tests compare a frozen 3-second clip with a changing 3-second synthetic test source. **A positive motion score DOES NOT mean there is a photoreal human model, that the retailer's garment is identical, that footage has rights, or that any customer would accept the Reel.** The owner-rejected illustrated mock must remain unapproved even if it passes this low-level motion heuristic. Source/CI exact-head acceptance required.

## F4-30 — Rejected-result UI safeguard
A successful `SUCCEEDED` codec/MP4 job does **not** override the exact reviewer-owned `OWNER_REJECTED` visual-quality state. The Feature4 workspace now hides a marked rejected signed preview/download and displays a clear rejection alert. This is a UI defense against presenting the discarded illustrated mock as a finished Reel, **not an authorization layer or a substitute for the trusted coordinator's saved review/release gate**. The new browser test injects an explicitly owner-rejected same-shop successful job and checks no MP4 preview/download is presented. No schema, cloud or billing change. Exact-head CI required.

## F4-31 — Encoded subtitle visibility gate (source commit; CI pending)
The accepted Feature2 timecode/voice track already passed 4/4 PR CI #40732044387, but that only checked authored HTML. The existing Full-HD CI fixture now adds a clearly **test-only** 0.9–1.8s caption `SUBTITLE CHECK 873` to the same sine-wave (NOT spoken) narration. The existing 30s/1080×1920 H264/AAC render extracts PNG frames 0.6s/1.2s/2.2s from the same intro shot, and `check_feature4_output.py` fail-closes if pixels do not change strongly while the caption is scheduled versus the control period. This proves *encoded temporal overlay presence* without OCR or new paid renders; it does NOT certify actual speech alignment, typography taste, caption legibility at phone size, or commercial acceptance. The owner-rejected illustrated test fixture stays **showcase_eligible=false** and never becomes a replacement sample. Exact current-head CI needed.

## F4-31 verified — real encoded Full-HD timecoded subtitle proof (2026-10-28)
**Exact source SHA:** `c2c0786710939c27cd167d564aa57f05899f22ba`. [Branch CI #40746342531](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40746342531) and [PR CI #40746345804](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40746345804) each **4/4 SUCCESS** (Python, React/browser, isolated Supabase, real FFmpeg/HyperFrames). The branch job passed **145 media tests**; independent PR job passed **320 media tests**. Both actually encoded the existing 30s/1080×1920/24fps H264/AAC synthetic test Reel with approved timecoded subtitle test cue, decoded 0.6/1.2/2.2s PNG frames, and measured **caption-window pixel difference 16.82 versus same-shot caption-off baseline 0.19** in the fixed subtitle region; the check would fail if caption appears only in HTML or at the wrong time. Existing original narration 863Hz test tone survived AAC and edited 30s/540p real JS→Python→HyperFrames MP4 also passed. The demonstration media is **OWNER_REJECTED, showcase_eligible=false, commercial_fashion_realism_accepted=false, spoken_word_qa_accepted=false, caption_semantic_alignment_accepted=false**. This proves *temporal overlay encoding only*, not realistic human/garment footage, actual speech alignment, visual aesthetics, producer rights, or production deploy. Keep draft PR / no paid GPU.


## F4-47 — encoded actual stock-human-motion verification
Added a fail-closed moving-pixel gate to the 30s real Pexels QA render
(`video-engine/feature4_encoded_motion_qa.py`). The verifier checks the
already fully encoded, probed 9:16 H264/AAC MP4, decodes *two actual frames*
per fixed reviewed actor-motion interval at 0–5, 10–15 and 20–25 seconds,
and computes normalized per-pixel grayscale differences. A static/frozen
'video' cannot pass the same contract. Source SHA-256 and per-scene values
are written to a noncommercial QA report in the PR CI artifact. Offline tests
use genuinely encoded synthetic moving and nonmoving videos, and reject
forged timestamps or invalid duration. This check proves *pixel motion*,
not person/garment identity, real AI inference, image attribution,
voice semantics or owner-level commercial visual quality. DO NOT promote
the owner-rejected illustrated fixture or generic Pexels stock to an ad.


## F4-51: Exact-artifact cross-feature QA and real browser beat navigation (2026-10-29)
Feature4-only `feature4_quality_receipt.py` verifies a real FFmpeg-produced
original, AAC-only mastered Full-HD video and compact reviewer MP4 are
exactly SHA-256 chained to their existing provenance, moving-pixel QA,
master/preview reports and editorial-only subtitle receipts. Each feature
(#2, #3, #4, #5, #7) gets its own explicit status and evidence summary,
with release blockers and `commercial_release_eligible=false` hard-coded.
The report rejects silent model/garment/voice approval upgrades and forged
SHA chains. A local immutable QA artifact is not a multi-tenant API or a signed
download. No user assets are uploaded to GitHub, only permitted Pexels stock QA.

The Playwright suite now mounts the actual React OpenReel timeline with a
same-shop, 15s measured-music stub and asserts four visible beat markers,
a precise 3.5s -> 24fps frame seek and mobile body overflow safety; a separate
cross-shop media stub proves the beat lane stays hidden. This is NOT evidence
that internet music rights, ASR or commercial scene fidelity are approved.
The old 'beat detection pending' UI copy is clarified to distinguish already
implemented offline WAV onset detection from unapproved cloud/signed music
operations. No new render engine, service, GPU, schema or WineShopPOS edits.


## F4-53 — actual encoded Pexels reel visual reviewer sheet
Added `feature4_review_contact_sheet.py`: source-only CPU/FFmpeg and Pillow
generator of a 12-frame 3×4 contact sheet from a *real verified* 15/30/60s
H264/AAC output (including an explicit stock-not-ad banner and frame
timestamps). The output is a private new JPEG and never overwrites an
existing review; source and output SHA-256, frame timestamps and
`owner_visual_approval=false` are returned. Unit tests verify physical
frame decoding (not HTML-only) with synthetic video. The PR media CI
exports this for the actual 30s Pexels garment concept only: do not upload
customer footage to public GitHub CI artifacts. This does not assert
human/model identity, transcript semantic alignment, licensing, fashion
commercial taste or owner-approved production readiness.


### F4-54 — source-frame repeated-shot warning
F4-53 contact-sheet QA now compares luma thumbnails of **decoded source
frames**, ignoring the timestamp band, across widely separated timestamps.
Near-identical actor/photo frames in distant parts of a video are recorded
in `possible_repeated_shot_pairs` and `repetition_warning` instead of
claiming the 60s stock-concat sample is professionally varied. A genuine
still-video fixture with repeated frames must trigger this warning.
This is a heuristic for visual review, NOT automated acceptance or identity
proof; `visual_diversity_accepted=false` always remains until owner review.


## F4-62 — five-point actual scene visibility, immutable media proof (2026-10-29)

Previous proof sampled only 30% and 70% of each scene. A black/blank encoded
interval between those two frames could pass; the old receipt also did not
recompute sampled near-black metrics or require exact sample time positions.
The Feature4-owned `feature4_scene_visibility.py` now decodes **five frames
at 15%, 30%, 50%, 70%, 85% per scene** from the actual encoded H264/AAC video,
rejects a nearly entirely black frame at any sampled point, and hashes the
source before and after decoding to reject mutation while producing proof.
The linked 60s proof has schema `feature4_scene_visibility_v2` and a fixed
sample schedule; `feature4_minute_quality_receipt.py` fails closed on a
missing, shifted, legacy or forged-black probe. Offline FFmpeg regression makes
an actual 1.5s black interval in the *middle* of the first 5s shot, which the
old 30%/70% checks missed; a positive colored scene remains accepted as purely
technical evidence. The standalone minute runner already invokes both helpers.

**Limitations:** 5 samples/scene are not exhaustive frame-by-frame monitoring,
face/product identification, sound or dialogue review, real spoken subtitle
alignment, absence of overlays, verified third-party approval or human visual
acceptance. A brief black flash could still occur between samples. The 60s
provenance/QA receipt must be regenerated with v2, **not** relabeled from old
receipts. No GPU, paid service, shared file, hosting, customer data or media
publishing was added. Source commits `3cb13517`, `d1c7021e`,
`80b54465`, `52bd614b`; exact-head CI must pass before marking verified.
