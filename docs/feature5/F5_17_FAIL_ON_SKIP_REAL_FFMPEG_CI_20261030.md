# Feature5 F5-17 — Real FFmpeg full private intake: fail-on-skip CI entrypoint

Date: 2026-10-30. This file describes a *source-ready* task that still needs coordinator CI wiring. No GPU/paid inference, original licensed media, hosted SQL, customer visuals or WineShopPOS.

## Why existing CI green is insufficient

Earlier PR #781 source `96075e45722c90c17a5b43f582736fbfceaaeb1d` passed standard 4/4 run #41061807851, but Python's tests reported **1209 passed / 12 skipped**, compared with **1209 passed / 9 skipped** previously. At that historical run, three real-FFmpeg tests did not execute because the Python/uv runner lacks `ffmpeg` and `ffprobe`. A passing *generic* FFmpeg smoke job does not exercise the new Feature5 private intake path.

## New in Feature5-owned paths

- `feature5_motion/ci_native_media.py` is a fail-closed runner for the **four** `tests/ai/test_feature5_wan22_real_cpu_private_intake.py` tests: native moving CPU 121-frame H.264 -> real staged private intake/ffprobe/5-frame screening/pending-only receipt; frozen static video denied; single brief flash within an otherwise frozen native clip denied; real AAC stowaway denied. Requires genuine executables `ffmpeg` and `ffprobe`, Pillow, exactly the four named acceptance tests, and **zero skips/errors/failures/xpasses/xfails**. Does not mask missing tools with skips.
- `tests/ai/test_feature5_ci_native_media.py` provides four small offline gate-unit tests, including negative cases for missing tools and any skipped or incomplete suite. They are **mocked gate tests**, not actual decoded-video acceptance.
- **Local independent CPU smoke execution** in current worker environment: genuine FFmpeg `testsrc2` and `color` native 704x1280/24fps/121 frames produced real 5.041667-second H.264 clips, with 5 independently extracted PIL RGB frames. Moving luma differences `[3.867, 4.516, 8.375, 8.588]` (nonstatic); static `[0,0,0,0]` (frozen). An added AAC stream was independently identified by ffprobe. Those local checks **did not import the complete Feature5 private-intake module**. In a separate real-FFmpeg follow-up, an original 121-frame synthetic white flash over a static navy frame at 2.35–2.65 seconds produced the five-sample adjacent luma differences **[0.0, 239.0, 239.0, 0.0]**: only two active intervals, so the now-stricter source rule rejects it. This is a decoder/algorithm check, not a genuine Wan clip or a full integrated intake run. The runner is explicitly prepared to test that exact path in the existing FFmpeg CI environment.

## 2026-10-30 — Existing FFmpeg CI discovery bridge (coordinator review required)

The existing `video-engine/ci.sh` already invokes `python3 -m unittest discover -s "$ROOT/tests/media" -p 'test_*.py' -v` **after the FFmpeg job installs FFmpeg, ffprobe and Pillow**. To avoid creating a new workflow, changing the coordinator-owned `.github/workflows/**`, or continuing to accept 4 skipped real media tests, added a **new file only** at `tests/media/test_feature5_native_media_ci_bridge.py`. Its single named outer unittest invokes the existing Feature5-owned fail-on-skip runner `run_cpu_media_suite()`, reports all four nested media test names to CI logs, and fails the existing FFmpeg job unless exactly **4/4 real CPU tests actually pass, zero skipped**.

This is a **cross-workstream tests/media addition**, not a change to existing video-engine source or workflow. The coordinator / media workstream owner must review it on PR #781 before integration; no other worker's media tests are altered. If the owner prefers an explicit workflow step, replacing the bridge with `python3 -m feature5_motion.ci_native_media` in the existing FFmpeg job is equivalent, but **do not run both** and waste CI time. Neither route creates hosted output or grants commercial use.

**Execution evidence gate:** an exact-head 4/4 standard CI conclusion is insufficient by itself. The FFmpeg job log must additionally name `test_four_real_cpu_ffmpeg_private_intake_cases_not_skipped`, print the **four nested real tests passing**, and show zero skip on that nested suite. Until these logs are checked, the integration status is SOURCE-ONLY. All moving, frozen, brief-flash, and added-audio cases use disposable synthetic CPU signals, never Wan2.2 AI output. F5-17 remains BLOCKED for real model rights, budget, original model provenance and signed human QA.

## Historical alternative: coordinator-owned explicit workflow step


In the existing `FFmpeg codecs + renderer tests` job of `.github/workflows/frontend-bootstrap.yml`, **after** FFmpeg/ffprobe and Pillow installation and **before** job completion, add exactly:

```bash
python3 -m feature5_motion.ci_native_media
```

No new workflow/job/provider, no new sample video uploads or approval bypass is needed. This command fails on missing tools, skips, changed tests and actual decoder/private-intake errors. Verify its log prints `PASS: 4/4 actual FFmpeg/ffprobe private-intake tests; 0 skipped` and independently confirm **all four jobs green on the updated exact PR head**. These four real decoded-video checks are required, not the Python mocked gate tests or previous FFmpeg smoke. Coordinator owns global CI workflow files, so Feature5 worker **did not edit .github/workflows/**.

This only advances **F5-17 source testing**. Genuine commercially licensed Wan2.2 5s model output, approved private input/licence rights, durable native Part3 claims, operator budget and signed human fashion QA are still missing. F5-17 remains BLOCKED, not released. Original ledger remains **0 integrated DONE / 3 IN PROGRESS / 19 BLOCKED / 22 total**. PR #781 remains source-review-ready; coordinator owns its integration into #465, remaining stack and eventual main with fresh CI.
