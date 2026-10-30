# Feature #5 F5-02 — original director timing type hardening (2026-10-30)

Status: **IN PROGRESS / source-only**. This is not an integrated DONE task.

## Scoped change
- Reject `bool` and `float` in original Feature2 `shot_start_seconds` and `duration_seconds` fields, even when Python numeric equality would accept them as integer 0 or 5.
- Preserve the original Feature2-to-Feature4/5 storyboard receipt as synthetic/offline only, never provider permission.
- Add deterministic negative tests for `False`, `0.0`, `5.0` and second-shot `5.0`. These tests do not invoke any model, GPU, Azure, Supabase or paid service.

## Task-manager handoff for coordinator
- **Task ID:** F5-02
- **Current state:** IN PROGRESS (not DONE)
- **Source evidence:** this branch and its exact-head PR; CI must be checked before accepting this source hardening.
- **Dependency ID:** F2-CREATIVE-SOURCE / F2#551
- **Dependency owner:** Feature2 and coordinator
- **Required output:** reviewed original MIT Creative Director Node exporter integrated into main, with original 15/30/60-second stdout.
- **Acceptance:** execute all three original exporter durations, reject tampered JSON/shot timing, coordinator merge of compatible source and fresh 4/4 main CI. No synthetic fixture counts as live media.
- **Review request:** coordinator may propose an IN PROGRESS receipt in `coordination/task_progress.json` only after reviewing PR/CI. Do not record DONE until integration evidence exists.

No paid GPU/model calls, no hosted DEV or PROD mutation, no user samples and no WineShopPOS edits.
