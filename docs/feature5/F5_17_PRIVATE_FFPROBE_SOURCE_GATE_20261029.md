# Feature #5 — F5-17 private FFprobe acceptance source hardening (2026-10-29)

Native Wan2.2 image-to-video output has NOT been generated, licensed or inspected on a running GPU. This independent CPU-only patch hardens the existing 704x1280, 24fps, 121-frame, silent H264 local MP4 validator without asserting a real output.

A forged or truncated ffprobe JSON payload cannot declare a valid one-stream video while hiding an extra stream: the entire JSON reply must be <= 50,000 text characters, unique-key decoded, finite and schema-checked. File byte-count, inode, device and nanosecond mtime must remain unchanged between preflight, ffprobe and content SHA256; linked private staged files are denied. Negative tests explicitly re-pin valid-looking probe output despite duplicate stream keys, oversized JSON, nonfinite duration and replaced local bytes during inspection.

Targeted `python -m unittest discover -s tests/ai -p 'test_feature5_wan22_clip_validation.py'` plus mandatory exact-head GitHub four-job CI. F5-17 remains BLOCKED on genuine licensed 704x1280 121-frame Wan2.2 video, current commercial rights, Part3 lease/credit/tenant contracts, operator approved GPU and physical human 11-point QA. The source test is not permission to start inference. No GPU, paid calls, DEV/PROD SQL, customer samples or WineShopPOS.
