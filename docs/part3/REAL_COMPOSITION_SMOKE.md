# Real offline Part 3 synthetic 30-second media smoke

This milestone is **not a paid Wan run**, customer-ready media or hosted deployment.

`tests/media/test_premium_compose_real.py` invokes the actual system FFmpeg binary to encode two distinct **synthetic** 15-second 720x1280 H.264 MP4 clips (red/blue) and generates a self-owned 440Hz PCM WAV test tone. It passes these as already-verified importer-style receipts into the Part 3-only `video-engine/premium_compose.py` function and independently invokes ffprobe on the assembled output to require exactly 30 seconds, H.264 video and AAC audio. It decodes frame pixels at 5s and 25s to prove both source clips were included in the correct order.

All inputs are created in temporary storage and automatically deleted; the test never contacts Alibaba or other services, never activates paid video, and cannot reuse any production/customer assets. The fixture calls itself “synthetic” and MUST NOT be represented as a legitimate vendor-generated Wan video or production-licensed marketing soundtrack.

This is invoked by existing `video-engine/ci.sh` via its standard `python3 -m unittest discover -s tests/media -p 'test_*.py' -v` command, within the existing FFmpeg CI gate. Ensure both the dedicated Part 3 CI 2/2 and repository CI 4/4 succeed before merging.

The user-ready premium feature still requires: approved vendor, actual paid provider smoke (separate owner approval), durable backend/outbox/worker/lease/credit migration, authenticated API and signed downloads, media licensing/customer consent, mixed stock+AI branding/CTA, failure/UNKNOWN reconciliation and safe app activation.
