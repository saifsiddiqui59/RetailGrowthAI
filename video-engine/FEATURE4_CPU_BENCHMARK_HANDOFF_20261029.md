# Feature #4 F4-14 — offline CPU budget/output evidence handoff (2026-10-29)

**Status:** IN PROGRESS, never integrated DONE without coordinator-reviewed merge into `main` and fresh four-job main CI. Branch `feat/feature4-cpu-benchmark-proof-20261029` is isolated from F4-04 duplicate parity and F4-13/F4-15 worker staging integrity.

## Source-only change

The existing mandatory 30-second Full-HD synthetic HyperFrames `benchmark_render.py` now binds its **actual encoded file bytes** to the CPU/RSS/wall-clock JSON report through a SHA-256 of a stable no-follow, regular-file descriptor, validates local file identity after hashing, and refuses existing target or report paths rather than silently overwriting another task's evidence. No extra render or paid inference is added. Tests verify full SHA, symlink/missing/truncated file denials and existing destination refusal without launching browser/render processes.

This is an improvement of the existing *local sampled lower-bound* CPU/RSS evidence: it does not create or certify a 15/30/60 cross-profile budget matrix, Azure cold start, Azure cost, cloud memory, human visual quality, or permitted commercial media. Benchmarks still explicitly set `azure_runtime_memory_verified=false` and `commercial_visual_quality_accepted=false`.

## Acceptance and dependencies

Run targeted `python3 -m unittest tests.media.test_feature4_hyperframes_benchmark -v` and standard four-job CI at branch boundary. Coordinator may merge source after separate review; fresh main 4/4 required to mark accepted slice. F4-14 remains IN PROGRESS until genuine 15/30/60 comparable measured envelope is approved; F4-22 ISSUE-650 packaging, F4-29 ISSUE-249 reliability and F4-30 signed DEV E2E remain coordinator/external tasks.

No GPU, Azure/PROD, hosted SQL, customer media or WineShopPOS.
