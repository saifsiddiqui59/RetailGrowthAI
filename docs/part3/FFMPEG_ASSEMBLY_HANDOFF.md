# Part 3: Optional AI clip -> 30-second FFmpeg assembly (source only)

Branch `feat/p3-ffmpeg-ai-assembly`, targeting `feat/part3-integration`.

## Delivered source boundary
- `video-engine/premium_compose.py` is an **additive** 30-second MP4 assembler; existing default `video-engine/render.py` and Part 1 free FFmpeg rendering remain unchanged. `select_render_mode` defaults to `ffmpeg` unless a separate authorized + enabled + all-clips-ready premium decision is explicitly provided.
- Accepts **only tenant-scoped private and independently reviewed provider output receipts**, not browser URLs or user input paths; 2–8 clips, each 2–15 seconds, exact total 30 seconds.
- Requires recorded commercial-use evidence and server-managed paths; re-probes imported MP4 H.264 codec, duration, portrait dimensions and bounded bytes before encoding. Audio sources require separately licensed rights evidence. Uses silent AAC if no music, never bundles unlicensed stock audio.
- Uses the existing FFmpeg/ffprobe toolchain and `verify_reel` contract. One H.264 yuv420p video + AAC audio output at 30 seconds. Uses a no-shell bounded FFmpeg process with safe error text and a temporary output before success atomic move.
- Supports only clip stitching/hard cuts (no branded overlay or dissolve yet); premium 30-second user workflow is **not live**. This source is not called by any registered Azure API/worker and cannot charge a provider. Paid Wan API remains OFF.

## Preconditions before activating
- All `clip receipts` must be fetched from the existing service-role/tenant-scoped authorized store by job ID; never trust a client-provided manifest.
- Provider result URLs must first be imported through `premium_private_import`, and clip provenance/billing/tenant/rights must be verified server-side.
- Reserve a strict total premium spend budget and concurrency before any paid provider task. A 30-second composition may require multiple billable 15s clips; do not bill the customer twice for fallback or duplicate renders.
- A failed/absent premium clip must not silently incur another paid provider POST. UI should explicitly offer the already-working standard FFmpeg renderer as the default fallback. Do not automatically refund a task that may have been charged.
- Branded overlays, CTA, text claim approval, optional fade transitions and mixed stock/AI timelines need review before launch; the minimal pure AI assembly does not implement those capabilities.
- Production output still requires authenticated private upload, DB CAS finalization, signed tenant-only download, exact per-shop usage and hosted FFmpeg benchmark.

## Mocked/offline testing
`tests/media/test_premium_clip_compose.py` checks FFmpeg command generation with mocks, free-first selection, cross-tenant/rights/path/duration/codec denial, safe default silence and licensed audio. Real full-resolution output/video quality and hosted tests are **not claimed**. Existing Part 1 FFmpeg CI remains the original quality gate.

No WAN API calls, paid clouds, schema changes, releases, Part 2 or unrelated repositories affected.
