# RetailGrowthAI - AI Development Instructions

Before starting any development task, read:

1. docs/PROJECT_STATE.md
2. docs/NEXT_TASK.md
3. docs/DECISIONS.md
4. docs/WORK_LOG.md
5. docs/ARCHITECTURE.md
6. docs/INTERFACES_V1.md
7. docs/PARALLEL_WORK.md

Rules:
- Continue existing work; do not restart completed tasks.
- Reuse suitable WineShopPOS components.
- Never modify WineShopPOS production resources.
- Keep RetailGrowthAI DEV and PROD isolated.
- Use Git Bash in VS Code.
- Use npm for JavaScript and uv for Python.
- Prefer low-cost Azure and Supabase architecture.
- Do not implement Postiz or Razorpay.
- Implement platform integrations in Part 2.
- Implement Wan video integration in Part 3.
- Test security and tenant isolation throughout.

After each completed development task:
- Update PROJECT_STATE.md.
- Update NEXT_TASK.md.
- Append a summary to WORK_LOG.md.
- Document any new architecture decision.
- Run appropriate tests.
- Commit and push using scripts/checkpoint.sh.
- Record blockers and unverified work honestly.

Parallel development rules:
- Work on the allocated feature branch and path ownership from docs/PARALLEL_WORK.md.
- Never make incompatible API/schema changes without the coordinator changing docs/INTERFACES_V1.md.
- Only the coordinator integrates to main and edits shared contracts; worker chats send branch PRs.
- The coordinator must update all project documentation after integration.

GitHub Actions automation:
- Read docs/CI_AUTOMATION.md before claiming builds/tests passed.
- Every branch push or PR runs the Part 1 CI jobs; inspect the actual GitHub Actions run and logs after pushing.
- Fix failures only inside your owned branch/files; do not bypass or disable a failing test to obtain green CI.
- The coordinator owns .github/workflows/**; worker chats must propose CI changes rather than modify it directly.

## Feature-chat operating policy (2026-10-29)
Read `docs/FEATURE_CHAT_OPERATIONS.md`, `coordination/execution_policy.json` and `coordination/feature_tasks.json` before continuing Feature #2/#3/#4/#5/#7 work. These add a maximum of 10 independently claimed tasks in distinct worktrees (when an approved executor exists), two silent *safe transient* retries, coherent work batching, targeted tests then full CI at batch boundaries, strict source-vs-integrated DONE evidence, and concise DONE / IN PROGRESS / FAILED / BLOCKED user-facing reporting. The task registry pins 159 existing task IDs, **not** verified production completion. No automatic GPU spending, PROD, protected approval bypass or WineShopPOS changes. Only the coordinator integrates to main and updates shared documents.

## Two-pass coding scheduler rule (2026-10-29)
Read `docs/SCHEDULER_RUNBOOK.md` before feature work. The shared coordinator's existing hourly Actions workflow now plans up to TEN advisory task slots (not actual agent processes). Future authorized workers must atomically claim separate nonconflicting branches/worktrees. For a recoverable failure diagnose the cause and **fix the owned code**, then retry up to **2** times (3 initial-pass attempts); defer it, work through remaining eligible tasks, then revisit safely failed tasks for up to **2** more fix/retries (5 total). Stop and report terminal failure after attempt 5; no infinite loop or repeated stale test. Never silently retry uncertain billing, queue ACK, rights/security denial or unapproved spend. Keep detailed attempts in GitHub, suppress interim retry chat output and use DONE / IN PROGRESS / FAILED / BLOCKED only. Only accepted integration with fresh main 4/4 is DONE. No automatic paid AI coder, GPU, PROD, SQL or WineShopPOS.

## Cross-feature references, DEV testing and task-status receipts (2026-10-29)
- All five feature chats MUST first read `docs/FEATURE_CHAT_SETUP_20261029.md`, `coordination/shared_feature_references.json`, `coordination/feature_test_policy.json`, and `docs/DEV_TEST_LOGIN_PLAYWRIGHT.md`. Exact chat names: `reail feature2`, `retail feature 3`, `retail feature 4`, `retail feature 5`, `retail feature 7`.
- Owner will not review samples for at least 10 hours: **do not create sample Reels, posters, images, videos, screenshots or user-preview requests** until owner explicitly asks; continue source code and deterministic automated fixtures/tests. No production sample claims.
- Use Playwright for DEV UI/login only with isolated, real nonprivileged test accounts **after** Auth Admin provisioning; mocked Playwright is not hosted authentication. An existing owner-controlled approval login must never be placed in Git, automated for approval, elevated or used to bypass permission gates.
- After every batch, update exact task IDs, source/PR/CI proof and status in owned handoff and propose reviewed `coordination/task_progress.json` status events; only coordinator integrates shared status and canonical docs. `scripts/coordination/task_status.py` verifies PR merge/accepted scope/fresh main 4/4 before DONE.
- GPU OFF, all paid provider/model calls OFF by default, no PROD or WineShopPOS. Bounded one-off existing GPT-4.1 Mini DEV inference is optional only with a proven usage meter and enforced cost guard; do not start without that guard.
