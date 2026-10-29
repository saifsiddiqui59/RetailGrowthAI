# RetailGrowthAI — Shared feature-chat startup (29 Oct 2026)

The following are the user's exact new-chat names inside the **existing RetailGrowthAI ChatGPT Project**:

| Name | Feature | Pinned tasks | Existing lead PR |
|---|---:|---:|---|
| `reail feature2` | #2 Creative Director | 38 | #551 |
| `retail feature 3` | #3 Poster Studio | 33 | coordinator-managed main |
| `retail feature 4` | #4 Video Studio | 31 | #322 |
| `retail feature 5` | #5 Wan Motion | 22 | #465 |
| `retail feature 7` | #7 Editing | 35 | #513 |

All five use **the same prompt** below; replace the feature number/chat name only. Chat creation requires a user-initiated new ChatGPT conversation; GitHub Actions doesn't create chats.

> Act as the development lead for **<CHAT_NAME>**, Feature #<NUMBER>, in `saifsiddiqui59/RetailGrowthAI`.
>
> Read `AGENTS.md`, `docs/FEATURE_CHAT_SETUP_20261029.md`, `docs/FEATURE_CHAT_OPERATIONS.md`, `docs/SCHEDULER_RUNBOOK.md`, `coordination/feature_tasks.json`, `coordination/shared_feature_references.json`, `coordination/dependencies.json`, `coordination/task_progress.json`, `coordination/feature_test_policy.json`, `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md`, `docs/INTERFACES_V1.md`, `docs/PARALLEL_WORK.md`, and your actual feature ledger.
>
> Verify latest main/PRs/CI/ownership; continue existing independent source work without restarting completed tasks. Respect the **global maximum of 10** atomic, nonconflicting worktrees ONLY if real coding workers are connected. Work in coherent batches; targeted tests during development, mandatory four-job CI at batch boundaries. Keep all cross-feature input IDs and handoffs current with `coordination/shared_feature_references.json`; never treat a fixture as a reviewed production output.
>
> When a recoverable issue occurs, diagnose/fix and retry up to 2 more times. After 3 unsuccessful safe attempts, defer it and continue other eligible tasks; once all first-pass work is attempted, give deferred failures 2 more fix/retries. After 5 failures total, mark terminal FAILED. No blind payment/security/unknown-ACK retries.
>
> I will **not review samples for the next 10 hours**. Do not generate user-facing demo/sample images, Reels, videos, screenshots or review requests during that period; continue source implementation and automated regression tests. Do not create samples afterward without my explicit request. Internal deterministic test fixtures may be used, clearly labeled as fixtures.
>
> For UI and login coverage use Playwright with existing DEV-only accounts. Follow `docs/DEV_TEST_LOGIN_PLAYWRIGHT.md`. Two nonprivileged test logins are proposed but **not yet created** until the supported Auth Admin provisioning is run; never report login as verified before real authentication succeeds. Existing approval user is for owner-controlled manual approval only; never store their password, simulate approval or bypass permissions.
>
> Cost policy: GPU OFF; no paid inference, provisioning, Azure resource upgrades, production deployments, or other billable operations. Use CPU/mock tests first. GPT-4.1 Mini may be used for a **single explicitly bounded, metered test** only if the deployed model is already available and a strict usage limit has been enforced; do not automatically run the model or another paid fallback.
>
> After **each task batch**, update the task's original ID, source evidence, CI run, PR and next state in your feature-owned ledger/handoff and proposed coordinator task-status event. The coordinator reviews and integrates `coordination/task_progress.json`, which the GitHub reporting workflow verifies. DONE requires acceptance, main merge and fresh 4/4 CI, not mock success.
>
> To me, respond only in short lines: **DONE — X/Y verified; IN PROGRESS — task IDs; FAILED — terminal root cause; BLOCKED — exact dependency ID/owner/output.** Omit empty lines, hide intermediate retry narration, and continue eligible work without waiting for my next message.

## Shared feature references

The machine-readable map `coordination/shared_feature_references.json` is authoritative for **producers, consumers, source PRs, required outputs, fixture-level contracts, live/rights gates and issues #249/#650**. Owner feature IDs remain in `coordination/feature_tasks.json`, while independent cross-feature readiness is checked through `coordination/dependencies.json`. Do not duplicate PR work or turn file handoffs into claimed production release.

## After task completion

Feature lead documents verified source result and submits to coordinator. Coordinator evaluates actual PR integration and full CI, records an evidence-backed event in `coordination/task_progress.json`, and the scheduled workflow refreshes `task-status.json/.md` in Actions artifacts. **Neither chat text nor an advisory scheduler candidate automatically means the task ran.**

## Required startup behavior for all five named chats
At **every** manual or scheduled ChatGPT execution, read `coordination/chat_worker_control.json` and `docs/CHAT_TASK_CONTROL.md` in addition to the files above. Treat their `entrypoint_instruction` and `on_task_resolution_instruction` as the active control manager: perform a real eligible coding task, document evidence, and immediately select the next one without user intervention within the same run. Do not end after a single PR/commit or status count when other independent safe tasks can be addressed. Global ten-claim limit is conditional on real atomic claims; do not pretend ten parallel workers exist. A chat turn cannot keep itself alive after it ends; the next user or automation trigger will reread the current backlog. The scheduler is separate and remains advisory.
