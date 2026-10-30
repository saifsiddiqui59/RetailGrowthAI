# Five-stage feature reporting (proposal, 2026-10-30)

Use `python scripts/coordination/feature_progress_report.py` to read the current repository task inventory and reviewed progress receipts. This report is intentionally conservative: a blank receipt log does not erase feature-branch work, but it is not evidence of an accepted integration.

Report these dimensions **separately** for each feature: **source-complete**, **tested**, **PR-ready**, **integrated DONE**, and **blocked**. Source-complete and blocked are *snapshot classifications* from `coordination/feature_tasks.json`. Tested, PR-ready and integrated require per-task explicit reviewed receipts in `coordination/task_progress.json` (fields `task_id`, `stage`, `verified: true`, and nonempty `evidence`). Do not infer PR-ready from existence of a draft PR or infer tested from passing CI on a different head. The integrated counter also requires the task's `integrated_done: true` and acceptance on main with fresh 4/4 CI; coordinator must update that field and receipt together.

**This is a reporting implementation, not a claim of test coverage or a modification to the authoritative tracker.** Existing unmerged branches/PRs can demonstrate real work without contributing to integrated DONE. Coordinator should review PRs and exact-head CI, then write task evidence through a separate authorized PR. This report intentionally shows unverified stages as zero; label them "not verified" in discussions rather than "nothing done."

## Scheduled ChatGPT execution limitation

A scheduled ChatGPT run ends at its execution boundary. It **cannot keep working indefinitely** and follow-up runs do not resume an open tool call. Long instructions, repeated reads and reporting can consume an entire run without code changes. GitHub Actions `task_scheduler.py` is advisory; no automatic coding agent or atomic task claim exists. Scheduling five independent runs does **not** produce continuous parallel workers.

Prefer one bounded, achievable task per run: read current state, make one safe owned code/test change, open or update a PR, record reviewable evidence, then pick another only if execution budget permits. If a run cannot make a code/PR change, record exactly why, not a fabricated completion. Coordinator separately batches code review/merge and main CI. Do not automatically activate GPUs, paid inference, PROD or alter WineShopPOS.
