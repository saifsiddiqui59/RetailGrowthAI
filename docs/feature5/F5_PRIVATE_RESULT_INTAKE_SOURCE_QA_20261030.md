# Feature #5 — Private result intake isolation and revoked-lease tests (2026-10-30)

Original task **F5-17** is still **BLOCKED** on genuine authorized Wan2.2 704x1280 24fps 121-frame output and approved actual fashion media. This batch adds source-only tests and a production fail-closed ownership rule without enabling inference or changing Part3.

## Changed paths
- `feature5_motion/wan22_private_result_intake.py`: Linux worker-owned 0700 private root, Comfy output subdirectory and 0600 regular MP4 must have the current effective UID; POSIX ownership is independently checked after existing link/mode enforcement. A root-like or wrongly configured privileged worker cannot accept another user's Comfy attempt bytes.
- `tests/ai/test_feature5_wan22_private_result_intake.py`: six CPU-only deterministic test paths using the actual Feature5 `synthetic_package`, current source finder, current receipt assembler and small **fake** MP4 bytes. Tests allow exactly one native numbered output, deny unexpected files/directories, loose perms, symlink/hardlink, bad counter and foreign POSIX ownership, require two independent fenced scope calls, verify receipt digest remains **PENDING/not approved**, reject lease revocation after mocked video screening and reject clip byte changes after inspection.

## Acceptance and boundaries
Run targeted `python -m unittest discover -s tests/ai -p 'test_feature5_wan22_private_result_intake.py'` and existing `test_feature5_wan22_clip_validation.py`/`test_feature5_wan22_frame_screening.py`; inspect the current head's full four-job GitHub Actions run. Existing F5 `#781` can remain a single coordinator review batch; do not create or merge another sibling PR for this small source addition.

The test doubles substitute ONLY for external ffprobe/FFmpeg on synthetic bytes; **not** an output of Wan, rights-verified retailer imagery, a real cloud lease, commercial license, live tenant isolation or publishing approval. Never auto-mark task DONE from passing CI. Coordinator owns integration, canonical task status and fresh post-merge main CI.

**Global status unchanged:** 0 DONE, 3 IN PROGRESS, 19 BLOCKED / 22 Feature5 tasks. F2 #551, Part3 #125, Feature4 #322 stay draft. No GPU/A100, model download, paid inference, hosted SQL/PROD, real sample Reel, billing retries or WineShopPOS.
