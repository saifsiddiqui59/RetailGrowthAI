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
| [7626927](https://www.pexels.com/video/woman-wearing-black-dress-7626927/) | Mikhail Nilov | 10–15s portrait studio outfit motion |

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
privately staged `8151871.mp4`, `8249911.mp4`, `7626927.mp4`.
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

## F4-37 — Fixed-keyframe full-HD source normalization

Actual F4-36 [PR CI #40759676430](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40759676430) 4/4 SUCCESS created verified real stock `feature4-stock-real-footage-15s.mp4`, but Chromium/HyperFrames warned about **3.03–3.04s sparse source keyframe intervals**. This is a real seek/freeze hazard; encoded MP4 PASS alone is insufficient to waive it. F4-37 now has a bounded CPU-only **immutable input-staging normalization**: each allowed stock source is probed, cropped to 9:16 Full-HD, FPS normalized to 24, re-encoded H264 with a 24-frame (1s) fixed GOP and source audio stripped for the intentionally muted timeline. It processes the first 5.25s only, never overwrites original downloaded files, preserves original + staged SHA-256 evidence and uses the same trusted HyperFrames compiler/producer. Negative tests reject overwrite and invalid clips; a real FFprobe keyframe test checks spacing <=1.1s. These changes do **not** imply a true garment match, professional edit quality, spoken narration or release approval. CI exact new-head required. GPU remains OFF; prior F4-36 sample artifact is a provisional owner-review candidate, superseded if the new sample renders.

## F4-38 — stronger real runway-style closing frame
The first F4-36 extracted MP4 was inspected frame-by-frame and the 8531898 clip's closing 5s lacked focus. This improves shot quality by replacing it with the Pexels-verified **vertical 1080×1920** 12s/25fps studio fashion clip [7626927](https://www.pexels.com/video/woman-wearing-black-dress-7626927/) by Mikhail Nilov. The exact 7626927 HD download URL is the Pexels site's official redirect, not an invented mirror. The intrusive multi-line `RetailGrowthAI editing concept` header is shortened to `FASHION EDIT`. Existing source normalized FFmpeg 1s GOP, original license/provenance checks, rights fail-closed, exact 15s no-endorsement CTA remain. This does NOT verify retailer's actual garment or professional human approval. Exact source CI must re-verify.

## F4-39 — Face-safe final edit: no CTA over human footage

The exact F4-38 [15s real-person stock export](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40761959879/artifacts/12847809476) was manually inspected via ten decoded frames at 0.75–13.8 seconds. Although the third scene is now crisp portrait video and F4-37 input clips have fixed 1-second keyframes, the reviewed CTA banner in the last three seconds covered the black-dress model's forehead and face. **A successful encode is not sufficient visual acceptance.** F4-39 moves the disclaimer to an isolated editorial endcard from 13–15s, with the real-human final shot visible untouched from 10–13s. CTA and last-scene headline match exactly so the existing trusted compositor deliberately does not create the giant timed root banner. The text states `STOCK FASHION EDIT - NOT A RETAILER AD`, not fictitious model endorsement or an unverified garment sale. Test checks exact four scene segments, video-only shot count 3, text and absent root CTA. No HyperFrames fork/new renderer, no GPU and no change to the generic renderer. Exact new-head CI and playback visual review required; final client commercial acceptance still pending.
