# Feature #4 — 2026-10-28 stock video candidate (NOT approved commercial Reel)

The owner explicitly rejected the older illustrated fake-fashion Reel, which stays
only in deterministic regression CI. This is a **separate** candidate using **real
human-shot Pexels video footage** and the existing authorized `professional.py`
HyperFrames compiler — not a competing renderer, not a Feature #5 AI generation,
and not proof that a retailer's garment is shown.

Sources verified at public Pexels pages 2026-10-28:

| Source | Creator | Use |
| --- | --- | --- |
| [8151871](https://www.pexels.com/video/a-fashionable-woman-modeling-while-walking-8151871/) | RDNE Stock project | 0–5s fashion hook |
| [8249911](https://www.pexels.com/video/woman-walking-while-looks-at-camera-8249911/) | RDNE Stock project | 5–10s rose-pattern fabric |
| [8531898](https://www.pexels.com/video/a-woman-in-a-dress-walking-at-a-park-8531898/) | KoolShooters | 10–15s sunlit outdoor movement |

The [Pexels License](https://www.pexels.com/license/) allows editing and commercial
video usage, **but forbids suggesting model/brand endorsement**. The concept's
approved copy is fictional: no discount, trademark, real retailer garment claim
or implicit model endorsement. These source pages are evidence of the platform
license, **not warranties that subjects consented to a specific new endorsement**.
Every downloaded asset is SHA-256 recorded, ffprobed, and sized under a hard cap.

## Reproducible private staging and render

With a Node 22 / HyperFrames npm ci installation and FFmpeg available:

```bash
python3 video-engine/feature4_stock_showcase.py --download \
 --project /tmp/rgai-stock-composition \
 --provenance ci-artifacts/feature4-stock-provenance.json
node video-engine/hyperframes/render.mjs \
 /tmp/rgai-stock-composition ci-artifacts/feature4-stock-real-footage-15s.mp4
ffprobe -v error -show_format -show_streams \
 ci-artifacts/feature4-stock-real-footage-15s.mp4
```

For **no-network** source tests, supply `--source-dir` with actual downloaded,
privately staged `8151871.mp4`, `8249911.mp4`, `8531898.mp4`.
Running `tests/media/test_feature4_stock_showcase.py` uses local patterns
exclusively and *never* labels them genuine fashion footage.

The Pexels downloader never accepts an arbitrary URL, never accepts a browser
media grant, redirects only to HTTPS `videos.pexels.com`, caps file size and
time, fails on bad source code/streams and preserves exact provenance.

**Commercial/visual release = BLOCKED until real owner QA.**
`showcase_eligible=false`, `commercial_release_eligible=false`,
`retailer_garment_identity_verified=false`, `real_spoken_voiceover=false`.
There is no claim of commercial third-party endorsement, word-level spoken sync,
Feature5 natural AI motion, or coordinator JWT/RLS/outbox/quota/lease/hosted
approval. GPU OFF. This concept must not displace the approved-tenant media gate.

The isolated GitHub PR's existing FFmpeg CI artifact contains the MP4 **only if**
the exact-source download and CPU render actually completed. CI must print an
honest failure if the external source is unreachable. No release/deploy or
WineShopPOS file modified.
