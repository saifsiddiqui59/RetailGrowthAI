# Five-stage feature reporting (proposal, 2026-10-30)

Use `python scripts/coordination/feature_progress_report.py` to read the current repository task inventory and reviewed progress receipts. This report is intentionally conservative: a blank receipt log does not erase feature-branch work, but it is not evidence of an accepted integration.

Report these dimensions **separately** for each feature: **source-complete**, **tested**, **PR-ready**, **integrated DONE**, and **blocked**. Source-complete and blocked are *snapshot classifications* from `coordination/feature_tasks.json`. Tested, PR-ready and integrated require per-task explicit reviewed receipts in `coordination/task_progress.json` (fields `task_id`, `stage`, `verified: true`, and nonempty `evidence`). Do not infer PR-ready from existence of a draft PR or infer tested from passing CI on a different head. The integrated counter also requires the task's `integrated_done: true` and acceptance on main with fresh 4/4 CI; coordinator must update that field and receipt together.

**This is a reporting implementation, not a claim of test coverage or a modification to the authoritative tracker.** Existing unmerged branches/PRs can demonstrate real work without contributing to integrated DONE. Coordinator should review PRs and exact-head CI, then write task evidence through a separate authorized PR. This report intentionally shows unverified stages as zero; label them "not verified" in discussions rather than "nothing done."

## Scheduled ChatGPT execution limitation

A scheduled ChatGPT run ends at its execution boundary. It **cannot keep working indefinitely** and follow-up runs do not resume an open tool call. Long instructions, repeated reads and reporting can consume an entire run without code changes. GitHub Actions `task_scheduler.py` is advisory; no automatic coding agent or atomic task claim exists. Scheduling five independent runs does **not** produce continuous parallel workers.

Prefer one bounded, achievable task per run: read current state, make one safe owned code/test change, open or update a PR, record reviewable evidence, then pick another only if execution budget permits. If a run cannot make a code/PR change, record exactly why, not a fabricated completion. Coordinator separately batches code review/merge and main CI. Do not automatically activate GPUs, paid inference, PROD or alter WineShopPOS.


## Durable coding checkpoint protocol for scheduled runs

Each run must prioritize a **small executable code change** rather than an exhaustive review or repeated count. GitHub is the sole durable state across executions. Before starting, inspect the latest main and open feature PR heads to avoid duplication.

1. **Resume**: read the latest feature-owned checkpoint (if present), and the relevant task/contract/CI documents. A checkpoint is guidance, not a lock. Verify its PR branch/head before acting.
2. **Execute**: select one eligible unblocked task with ownership and acceptance criteria; edit owned code and tests; create/update its branch and PR. Do not treat a status-only PR as coding completion.
3. **Checkpoint**: in the *same feature-owned PR* append a concise `docs/featureN/RUN_CHECKPOINT.md` file (or update its existing feature handoff file), with task ID, branch, exact commit SHA if known, PR number, files changed, verification performed with precise command/result, CI run/head status, blockers, and **NEXT actionable task ID**. Use factual "not run/pending" where appropriate. Commit this checkpoint so it survives chat expiration.
4. **Handoff**: after a verified source task or blocker, read the current registry again and pick next independent eligible work during this run if tools/time permit. Never represent scheduler advisory slots as atomic claims.
5. **Restart**: the next scheduled run **first** reads the committed checkpoint and checks PR/source/CI against GitHub. Continue unfinished code rather than regenerating plans. If the prior PR is waiting for CI or coordinator merge, work on another independent task.
6. **Acceptance**: source implementation and tests are reported separately from PR-ready and coordinator-integrated DONE. Do not modify shared completion records as a feature worker; file factual evidence for coordinator review.

Every run must either (a) commit a meaningful owned code/test improvement and a factual checkpoint or (b) record a precise actionable blocker in an owned PR/handoff. Do not claim completed work unless the relevant code and evidence are visible in GitHub. No background continuity is implied; a new scheduled invocation resumes after the prior one stops.
