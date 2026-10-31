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
- Feature leads may integrate *eligible feature-owned PRs* into main following docs/FEATURE_SELF_MERGE_POLICY_20261031.md. Shared/critical contracts require independent review; no dedicated coordinator schedule.
- The integrating feature lead maintains its scoped handoff and updates canonical docs through a separate reviewed PR when needed.

GitHub Actions automation:
- Read docs/CI_AUTOMATION.md before claiming builds/tests passed.
- Every branch push or PR runs the Part 1 CI jobs; inspect the actual GitHub Actions run and logs after pushing.
- Fix failures only inside your owned branch/files; do not bypass or disable a failing test to obtain green CI.
- Shared .github/workflows/** changes need independent affected-lead or human review; never bypass existing CI/release approvals.

## Feature-chat operating policy (2026-10-29)
Read `docs/FEATURE_CHAT_OPERATIONS.md`, `coordination/execution_policy.json` and `coordination/feature_tasks.json` before continuing Feature #2/#3/#4/#5/#7 work. These add a maximum of 10 independently claimed tasks in distinct worktrees (when an approved executor exists), two silent *safe transient* retries, coherent work batching, targeted tests then full CI at batch boundaries, strict source-vs-integrated DONE evidence, and concise DONE / IN PROGRESS / FAILED / BLOCKED user-facing reporting. The task registry pins 159 existing task IDs, **not** verified production completion. No automatic GPU spending, PROD, protected approval bypass or WineShopPOS changes. The active feature-owned integration policy supersedes historical coordinator-only merge requirements; see docs/FEATURE_SELF_MERGE_POLICY_20261031.md.

## Manual feature task selection (effective 2026-10-31)
Recurring ChatGPT feature schedules and the GitHub advisory task-selection planner have been retired. For user-initiated feature work, inspect latest `main`, the immutable 159-task `coordination/feature_tasks.json`, reviewed `coordination/task_progress.json`, feature-ledgers/checkpoints, branches, open PRs and CI before selecting an eligible unfinished task. Prevent duplicate ownership, preserve bounded safe retries and independent approvals, and verify mandatory CI. No paid GPU/model, PROD, hosted schema or WineShopPOS changes without approval.

## Cross-feature references, DEV testing and task-status receipts (2026-10-29)
- All five feature chats MUST first read `docs/FEATURE_CHAT_SETUP_20261029.md`, `coordination/shared_feature_references.json`, `coordination/feature_test_policy.json`, and `docs/DEV_TEST_LOGIN_PLAYWRIGHT.md`. Exact chat names: `reail feature2`, `retail feature 3`, `retail feature 4`, `retail feature 5`, `retail feature 7`.
- Owner will not review samples for at least 10 hours: **do not create sample Reels, posters, images, videos, screenshots or user-preview requests** until owner explicitly asks; continue source code and deterministic automated fixtures/tests. No production sample claims.
- Use Playwright for DEV UI/login only with isolated, real nonprivileged test accounts **after** Auth Admin provisioning; mocked Playwright is not hosted authentication. An existing owner-controlled approval login must never be placed in Git, automated for approval, elevated or used to bypass permission gates.
- After every batch, update exact task IDs, source/PR/CI proof and status in owned handoff and propose reviewed `coordination/task_progress.json` status events; the integrating feature may propose reviewed shared receipts/docs updates under docs/FEATURE_SELF_MERGE_POLICY_20261031.md. `scripts/coordination/task_status.py` verifies PR merge/accepted scope/fresh main 4/4 before DONE.
- GPU OFF, all paid provider/model calls OFF by default, no PROD or WineShopPOS. Bounded one-off existing GPT-4.1 Mini DEV inference is optional only with a proven usage meter and enforced cost guard; do not start without that guard.


## Feature-owned integration, manual sessions only — effective 2026-10-31
Read `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`: Features #2/#3/#4/#5/#7 each own eligible reviewed PRs, main integration, verification and task receipts. Continue through user-initiated chats; no automatic ChatGPT schedules or hourly GitHub coding planner. Sensitive cross-feature work still requires independent review. GPU/PROD/WineShopPOS remain protected.
