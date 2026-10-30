# Feature5 F5-17 — Real FFmpeg full private intake: fail-on-skip CI entrypoint

Date: 2026-10-30. This file describes a *source-ready* task that still needs coordinator CI wiring. No GPU/paid inference, original licensed media, hosted SQL, customer visuals or WineShopPOS.

## Why existing CI green is insufficient

Exact-head PR #781 source `96075e45722c90c17a5b43f582736fbfceaaeb1d` passed 4/4 run #41061807851, but Python's tests reported **1209 passed / 12 skipped**, compared with **1209 passed / 9 skipped** previously. The three new real-FFmpeg tests did not execute because the Python/uv runner lacks `ffmpeg` and `ffprobe`. A passing *generic* FFmpeg smoke job does not exercise the new Feature5 private intake path.

## New in Feature5-owned paths

- `feature5_motion/ci_native_media.py` is a fail-closed runner for the **three** `tests/ai/test_feature5_wan22_real_cpu_private_intake.py` tests: native moving CPU 121-frame H.264 -> real staged private intake/ffprobe/5-frame screening/pending-only receipt; frozen static video denied; real AAC stowaway denied. Requires genuine executables `ffmpeg` and `ffprobe`, Pillow, exactly the three named acceptance tests, and **zero skips/errors/failures/xpasses/xfails**. Does not mask missing tools with skips.
- `tests/ai/test_feature5_ci_native_media.py` provides four small offline gate-unit tests, including negative cases for missing tools and any skipped or incomplete suite. They are **mocked gate tests**, not actual decoded-video acceptance.
- **Local independent CPU smoke execution** in current worker environment: genuine FFmpeg `testsrc2` and `color` native 704x1280/24fps/121 frames produced real 5.041667-second H.264 clips, with 5 independently extracted PIL RGB frames. Moving luma differences `[3.867, 4.516, 8.375, 8.588]` (nonstatic); static `[0,0,0,0]` (frozen). An added AAC stream was independently identified by ffprobe. Those local checks **did not import the complete Feature5 private-intake module**. The runner is explicitly prepared to test that exact path in the existing FFmpeg CI environment.

## Required coordinator action (owned .github workflow)

In the existing `FFmpeg codecs + renderer tests` job of `.github/workflows/frontend-bootstrap.yml`, **after** FFmpeg/ffprobe and Pillow installation and **before** job completion, add exactly:

```bash
python3 -m feature5_motion.ci_native_media
```

No new workflow/job/provider, no new sample video uploads or approval bypass is needed. This command fails on missing tools, skips, changed tests and actual decoder/private-intake errors. Verify its log prints `PASS: 3/3 actual FFmpeg/ffprobe private-intake tests; 0 skipped` and independently confirm **all four jobs green on the updated exact PR head**. These three real decoded-video checks are required, not the Python mocked gate tests or previous FFmpeg smoke. Coordinator owns global CI workflow files, so Feature5 worker **did not edit .github/workflows/**.

This only advances **F5-17 source testing**. Genuine commercially licensed Wan2.2 5s model output, approved private input/licence rights, durable native Part3 claims, operator budget and signed human fashion QA are still missing. F5-17 remains BLOCKED, not released. Original ledger remains **0 integrated DONE / 3 IN PROGRESS / 19 BLOCKED / 22 total**. PR #781 remains source-review-ready; coordinator owns its integration into #465, remaining stack and eventual main with fresh CI.
