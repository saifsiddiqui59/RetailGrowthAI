# RetailGrowthAI standalone 30-second Reel renderer (Workstream C)

Offline renderer matching INTERFACES_V1.md. Accepts an existing campaign's day, with 2-8 contiguous storyboard frames spanning exactly 30s, a separate server-authorized asset ID manifest, and a server-controlled local media root. Never use browser-provided file paths or unauthenticated IDs.

Example, with real merchant-authorized assets staged inside /tmp/retail-assets (manifest paths are RELATIVE to that folder):

    python3 video-engine/render.py --campaign campaign.json --manifest /tmp/retail-assets/manifest.json --asset-root /tmp/retail-assets --day-index 1 --output /tmp/retail-reel.mp4

The output defaults to 1080x1920, 24 fps H.264/yuv420p with AAC audio and exactly 30 seconds. Transitions are half-second crossfades at storyboard boundaries. Title overlays come from each storyboard segment; CTA comes from reel.cta. Only supply --offer-text if validated against a human-approved offer from the campaign brief. This renderer never invents discounts. When music_asset_id is null, a silent AAC track is generated; otherwise only a commercial-use licensed music asset is accepted.

Manifest example:

    {
      "shop_id": "shop-uuid",
      "assets": {
        "image-asset-uuid": {
          "kind": "image", "path": "product.jpg",
          "rights": {
            "license": "owned",
            "commercial_use": true,
            "source": "merchant upload",
            "evidence": "recorded merchant rights attestation ID"
          }
        },
        "music-asset-uuid": {
          "kind": "audio", "path": "music.wav",
          "rights": {
            "license": "commercial",
            "commercial_use": true,
            "source": "licensed stock music library",
            "evidence": "verified license record permitting social advertising"
          }
        }
      }
    }

Asset IDs in the shared frontend fixture are SYNTHETIC, not uploaded images. A trusted orchestration layer must authorize each ID against the authenticated shop, check license provenance and intended channels, and create this manifest. The local manifest's declared rights are validation metadata, not independent proof of a license. Deny unverified or expired licenses at the API boundary; never fetch URLs or execute supplied FFmpeg expressions. Synthetic_test assets are blocked unless --allow-test-media is explicitly passed, which is only for isolated CI.

Run offline test harness from repo root or any directory:

    bash video-engine/ci.sh

It generates three different synthetic color-card JPGs and a synthetic 440Hz TEST TONE (not production music). No downloaded images or third-party music are bundled. It copies the existing v1 campaign fixture into a temporary file to attach the test audio ID, verifies 14 validation tests, renders a real 1080x1920 30s MP4 with an explicit offer string, checks ffprobe streams/duration and samples actual video colors/crossfade/audio signal. Synthetic MP4 stored in ci-artifacts for the existing workflow's 3-day artifact retention; do not commit MP4 or treat a color-card render as visual QA of real stock media.

Runtime requirements: Python 3.10+, FFmpeg/ffprobe with libx264, AAC encoder and drawtext enabled; DejaVu Sans fontconfig font. No pip packages, Azure credentials or cloud account required. Encoder runtime and quality require later benchmarking with real, authorized imagery and approved music. Async API queue, tenant authorization, signed downloads, retries and output upload are coordinator/B integration work, NOT implemented in this module.
