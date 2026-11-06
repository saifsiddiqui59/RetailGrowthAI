# Feature #7 — Real Pexels stock editing acceptance using selected AutoBroll code

## Verified source selections and independent licensing

**Real Pexels footage (downloaded and decoded in GitHub media tests):**
- Video: [Clothes Hanging on a Rack, video #8581174](https://www.pexels.com/video/clothes-hanging-on-a-rack-8581174/), RDNE Stock project. Public page reports original 1080x1920, 10s, 30fps, clothing-rack fashion stock video. The page's real **Free download** redirects to `https://videos.pexels.com/video-files/8581174/8581174-hd_1080_1920_30fps.mp4`. Exact direct download is a public Pexels server link, not fabricated from filename heuristics.
- Image: [Assorted Colorful Clothes Hanging on Rack in Store, photo #5490963](https://www.pexels.com/photo/assorted-colorful-clothes-hanging-on-rack-in-store-5490963/), Rachel Claire. Public page reports original 5472x3648. The download action leads to `https://images.pexels.com/photos/5490963/pexels-photo-5490963.jpeg?cs=srgb&dl=pexels-rachel-claire-5490963.jpg&fm=jpg`.
- License: [Pexels License](https://www.pexels.com/license/). It allows modifying photos and videos, including commercial use, without attribution. **No implied person/brand endorsement; third-party trademarks/model releases or identifiable individuals remain separately restricted.** No public test media shall be asserted as legally authorized original tenant-uploaded fashion product or product-garment-specific try-on.
- This public fixture consists primarily of clothing/display imagery, reducing person/identity endorsement questions. No actual retailer inventory, discounts or advertisements are represented as factual, and the demo overlays are purely fictional.

## Chosen open-source engine, not reinvented

Feature #7 already adapted the **MIT-licensed** `andriidrok1/autobroll` project into `autobroll_semantics.mjs`, pinned upstream tree `4aef3afb099c866bd2977c184f9912ba57318f77` and vendored intact `AUTOBROLL_MIT_LICENSE.txt` (copyright 2026 Andrii Drok).

The new `pexels_autobroll_fixture.mjs` does **not** implement a new caption algorithm/editor: it directly calls the existing imported AutoBroll `buildCaptions` and `speechRuns` under a strictly bounded stock-media test fixture, while requiring `source_relative_speech_runs=[]` for footage without verified spoken voice. Promotional text overlays are explicitly **not** inferred audio transcripts. No Gemini, Pexels API key, new language model, Remotion download, GPU or paid service was started.

The selected professional editing project `MartinDelophy/ai-video-editor` remains Feature #4's editor responsibility, pinned there as `e1091feccca3be8832b507eb7e17c9e55eb2233a`. This feature branch **does not create a second professional editor** or modify that upstream editor's UI. Actual F4-specific production overlay/render paths, including caption tracks, B-roll and multi-cut precision, remain F4 integration work.

## Actual editing acceptance performed in CI

`tests/media/test_feature7_pexels_autobroll.py` runs two independent groups:

1. Offline deterministic tests require the existing AutoBroll MIT planner, assert text/word grouping, correct stock-video/photo provenance, no fabricated speech, no upstream-editor replacement, fail-closed timing/tenant ids.
2. GitHub CI **downloads both exact actual Pexels assets** over HTTPS, allowlists final CDN host, checks JPEG/MP4 magic bytes and bounded download sizes, decodes their real streams using `ffprobe`, hashes immutable source bytes. The test scales and crops the Pexels photograph into a private 360x640 still and uses FFmpeg test commands (not a new app/editor) to produce a ~6.5s **360x640** vertical reel with moving Pexels footage, the genuine Pexels boutique photo as B-roll, a crossfade, the AutoBroll-planned fictional text overlay and **synthetic AAC test tone**. It validates H.264 video, AAC audio, real image/video scene differences, duration/dimensions and unchanged original file hashes, then removes every original, still and temporary edited MP4.

The audio is **synthetic test-only**, not licensed music, recorded user speech or real WhisperX output. This proves actual stock video+image editing mechanics and source-frame integrity; it is **not yet a production video download or the F4 renderer integrated in RetailGrowthAI**.

Run the same exact real Pexels sample manually from repo root with Node, Python, FFmpeg/ffprobe:

```bash
RETAIL_F7_PEXELS_WEB_TEST=1 python3 -m unittest discover -s tests/media -p 'test_feature7_pexels_autobroll.py' -v
```

Test media stays only in a temporary directory and is deleted after checks. The same test runs automatically when `CI=true`; no optional API key and **no paid GPU** needed.

## Ownership and unmet product gates

Feature #7 worker may edit only `video-engine/feature7/**` and `tests/media/test_feature7*.py`. F4 editor integration and final production rendering belong to Feature #4; hosted upload/JWT/RLS/private storage/Postgres approval/lease, and shared docs/CI changes belong to the coordinator. Source test images are not automatically customer-license evidence, nor authorization to publish a real model's likeness. Hosted two-tenant DEV E2E and real licensed CPU WhisperX ASR quality are still unverified.

**No modification to WineShopPOS, main, shared schema, CI workflow, Azure services or PROD; no GPU started.**


## 2026-10-28 — Verified real 1080x1920 Pexels export (supersedes earlier 360x640-only acceptance)

**New working CPU-only Full HD sample preset:** `pexels_fullhd_export.py` uses the **existing** MIT AutoBroll `buildPexelsOfflineEditFixture()` source-aligned caption planner and the shared FFmpeg H264/AAC codec stack. The script is an offline **stock-demo export preset**, not a separate SaaS editor or alternative to Feature #4's chosen `MartinDelophy/ai-video-editor`. It processes real, previously verified Pexels video #8581174 and original photo #5490963, preserves source SHA, applies video and photo grading, B-roll zoom/pan, text overlays and 0.5s crossfade, and outputs **1080x1920 pixels, 30fps, 15s, H264 High yuv420p CRF20, AAC stereo 48 kHz, faststart**. CPU only; no proprietary model, GPU or paid inference.

**Working real-world acceptance:** `test_feature7_pexels_autobroll.py` adds exact original Pexels Full HD export and corrupt media / duplicate write negative tests. It verifies the actual FFprobe dimensions, frame rate, pixel format, audio codec/sample rate, duration, decoded distinct video/photo frames, source integrity and fail-closed output name. Original source Pexels assets are online-retrieved solely in CI/explicit opt-in, capped and discarded after testing. GitHub media CI [#40760554613](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40760554613) **264 media tests PASS**, real 1080p rendered output; a genuine first attempt at `873c894` failed on a Python stat descriptor method misuse and was corrected, not bypassed.

**Playable output now retained as a short-lived public CI artifact:** The existing `ffmpeg-smoke` GitHub upload-artifact action automatically attaches `ci-artifacts/feature7-pexels-fullhd-1080x1920-demo.mp4` and `feature7-pexels-fullhd-proof.json`; **no GitHub workflow or shared CI change required**. Example verified real artifact [from #40760554613](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40760554613/artifacts/12846938704), retained until approximately 2026-10-31; subsequent exact-head runs have their own artifact IDs. This is a downloadable **genuine Full HD stock sample**, not just render logs.

Run with already legally downloaded public Pexels stock assets (Node+FFmpeg/ffprobe+Python required):
```bash
python3 video-engine/feature7/pexels_fullhd_export.py \
  --video /absolute/path/pexels_8581174.mp4 \
  --photo /absolute/path/pexels_5490963.jpg \
  --output /absolute/private/path/fashion_demo_fullhd.mp4
```

**Production distinction:** The demo emits silent **AAC placeholder audio** rather than falsely claim a music license, spoken presenter, voice transcription or customer approval. It is real Full HD media suitable for reviewing framing/text/transition/encoding, but **NOT** a signed customer-ready production advertisement: active authenticated shop ownership, registered private media, real licensed/approved soundtrack, human editorial approval, F4 renderer integration, 15/30/60s campaign lengths and hosted downloadable tenant output still require their respective API/DB/F4 team owners. Do not claim Pexels stock conveys ownership of an actual retailer's product/garment or person endorsement. GPU remains OFF. No WineShopPOS, cloud or shared contracts changed.

### 2026-10-28 — 15-second campaign-compatible Full HD refinement
The latest Full HD stock demo uses **9 seconds of the original Pexels clothing video plus 6.5 seconds of the real photo**, with a 0.5-second overlap crossfade, for **15.0 seconds at 1080×1920, 30 fps, H.264 High/yuv420p, AAC 48kHz**. This replaces the earlier 10-second-only export preset; that earlier successful GitHub artifact remains a separate historical test. The same bounded Pexels downloaded bytes, original MIT AutoBroll plan, no GPU, integrity checks and existing CI attachment apply. The Pexels footage itself is 10 seconds long; no claimed retailer ownership, face endorsement, human speech or music rights. Actual final length and video/audio streams must pass the latest exact-commit CI before marking the new 15s sample verified.
