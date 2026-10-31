# F4-41 — private download-friendly 540p preview

Owner reported inability to download the 30s original full-HD sample. The
verified F4-40 1080x1920/24fps H264/AAC GitHub MP4 was 19,888,931 bytes;
manually derived 540x960 30s H264/AAC copy was 1,351,663 bytes (2026-10-28).

**Product reuse:** \`video-engine/feature4_private_preview.py\` is a CPU-only,
FFmpeg-backed preview helper for **already authorized** 15/30/60s MP4s.
It requires an existing safe local input and private output directory, validates
source codecs, 9:16 resolution and expected duration, refuses symlinks and
overwrite, bounds output to 8 MiB, copies no external URLs, writes an atomic
temporary MP4 and returns input/output SHA-256 plus measured size, format and
explicit \`signed_download_ready=false\`. Original is not edited. Preserves AAC
sound and provides faststart for normal mobile download/playback.

\`\`\`sh
python3 video-engine/feature4_private_preview.py \
  --source /private/authorized-original.mp4 --duration 30 \
  --output /private/authorized-preview.mp4 \
  --report /private/reviewer-preview-proof.json
\`\`\`

Scope: F4-only helper, **not** a public web path, an auth layer, a production
Supabase registration, a signed download, or an Azure deployment. No API/schema
or cloud configuration was changed. Feature4 queue worker must only run after
tenant JWT/RLS approval + claim/lease checks and use existing private bucket.
Coordinator must implement same-shop private preview registration + expiry,
grant/revocation, and tenant signed download before a customer sees one.
Do not put private customer previews into public GitHub CI artifacts.

Only the explicitly consent-free Pexels stock concept generated in F4-40 is
rendered to a download-friendly 540p **CI sample** on Feature4 draft PR branch.
Its commercial_release_eligible=false and garment fidelity flags remain.
No GPU, paid compute, third-party artist music, real retailers or WineShopPOS.
CI test \`tests/media/test_feature4_private_preview.py\` performs actual
FFmpeg encode, source immutability, codec/duration/size verification and
negative tests for unsafe files, wrong aspect and wrong duration.


## F4-43 — audio-only perceptual loudness mastering
The owner-reported stock Reel had quiet original synthesized audio (measured
approximately -29.1 dB mean). A separate FFmpeg loudnorm transcode of **only**
the AAC audio improved mean volume to approximately -17.5 dB on the 30s sample;
the SHA-256 streamhash of H264 video packets remained byte-for-byte identical.
New \`video-engine/feature4_audio_master.py\` performs this step after an
already-authorized private render and BEFORE generating the compact preview,
without rewriting or deleting the Full-HD original. It enforces source 9:16
H264/AAC, expected 15/30/60s duration, bounded output, loudness measurement,
audio level sanity, immutable H264 packet hash, atomic no-overwrite, and
source/output SHA-256 provenance. Source-only, no public/signed URL, no
rights grant, no voice recognition, no music recommendations.

PR-only Pexels QA outputs mastered Full-HD + small 540p mobile MP4 in the
existing short-retention CI artifact. Actual offline unit tests exercise
a low-volume synthetic soundtrack, verify gain and exactly preserved H264
packet hash, and reject malicious/invalid source paths and bad durations.
Commercial acceptance, actual AI speech, licensed third-party songs,
real retailer garment fidelity and hosted JWT/RLS/private signing still pending.
