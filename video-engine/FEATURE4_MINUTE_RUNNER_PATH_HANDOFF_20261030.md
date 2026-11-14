# Feature #4 F4-01 — private native-minute runner path preflight (source-only)

- Parent: draft PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
- Owned changes: `video-engine/feature4_stock_minute_acceptance.sh` and `tests/media/test_feature4_stock_minute_runner.py`.
- Fix: before any output directory creation or stock download, reject private-output paths with `..` traversal, symlinked ancestors, missing parents or unwritable parents. Check FFmpeg/ffprobe/Node 22 before mkdir so missing local tools cannot leave an orphan private output directory. Keep fresh-directory requirement and no-overwrite behavior.
- Deterministic tests: symlinked parent, traversal, missing-parent and missing-FFmpeg negatives; existing Bash syntax and no-argument/existing-directory tests.
- Task ID: **F4-01 — IN PROGRESS, partial safety hardening only**. Native revised 60s HyperFrames encode, 12-scene visibility, caption, endcard, signed source SHA chain and human visual review remain **unverified**. No commercial/retailer/garment/voice approval.
- Verification: targeted tests and exact-head four-job CI **pending** until a verified run is recorded. Do not count integrated DONE. Coordinator must review this stacked PR and later merge/verify 4/4 main before changing `coordination/task_progress.json`.
- Existing unrelated coordinator-owned Python package ZIP member-limit failure: ISSUE-650. Do not weaken or bypass.
- No new user-facing sample, hosted Auth, paid model, GPU, Azure/PROD, Supabase mutation, WineShopPOS, or shared-contract edits.
