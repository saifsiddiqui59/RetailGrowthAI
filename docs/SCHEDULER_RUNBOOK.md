# RetailGrowthAI — Bounded 10-slot scheduler and two-pass repair queue

## Current implementation vs future execution

The coordinator runs on GitHub Actions at **17 minutes past each hour**, after a successful `RetailGrowthAI Part 1 CI` workflow run for `main`, and on selected `main` changes/manual dispatch. The action computes verified 16-node cross-feature handoffs, reports the pinned 159 original feature tasks and plans **up to 10 candidate coding slots**. Its schedule does not create ChatGPT conversations, hire an agent, run 10 worktrees, execute repairs, deploy or spend money. A separately authorized coding executor is **not connected yet**. `scheduler-plan.json` always says `advisory_not_started: true`.

The scheduler policy is `coordination/execution_policy.json`, implementation is `scripts/coordination/task_scheduler.py`, and trusted future worker-receipt ledger starts empty at `coordination/scheduler_events.json`. The event ledger must be changed through reviewed GitHub PRs or by a future authenticated and atomic claim/receipt service; NEVER let an untrusted PR user post authoritative completion. Full receipts/logs remain visible in Actions and GitHub even when new feature chats hide intermediate retry messages.

## Requested sequence, implemented as a bounded state machine

- Select independently actionable source tasks; respect exact dependency IDs and existing feature ownership. Do **not** reopen source-complete tasks or create duplicate assignments for open drafts. A candidate is not a claim or a running task.
- **First pass:** initial attempt #1. If a recoverable issue occurs, have the approved coding worker inspect the error, modify the owned source to fix the root cause, and run targeted tests before additional attempts **#2 and #3**. Record each actual attempt with classified diagnostic and evidence; don't repeat the same known-bad code.
- If still failing after #3, **defer the task** while continuing all remaining eligible first-pass tasks. A blocked external dependency does not delay progress on unrelated tasks.
- Once all currently eligible first-pass tasks are attempted/accepted/deferred, perform a **second pass** on deferred safely retryable failures, attempts **#4 and #5**, with a fresh diagnosis/fix on each attempt.
- If #5 fails, park the task as **FAILED for human triage** and move to the next. Future main changes, new permissions or newly satisfied dependencies may justify a new reviewed task version, but cannot silently reset the five-attempt budget or create a retry loop.
- Unsafe/non-idempotent or ambiguous failures (paid model submission, unknown queue acknowledgment, tenant/rights denial, approval missing, security failure) are not automatically retried even once. They become BLOCKED or FAILED with owner/dependency and required acceptance proof.
- Passing targeted tests is **AWAITING INTEGRATION**, never DONE. Only verified acceptance, reviewed PR merge to current `main`, fresh 4/4 CI and any independently required live quality/rights gates permit a completed development or release claim.

## Concurrency & ownership

The **maximum is 10** separate claimed coding tasks globally, not 10 per feature chat. A future executor must maintain an atomic global claim store/lease, verify distinct worktrees and branches and deny overlapping write paths; the current scheduler produces advisory slots and does not enforce live leases. Don't dispatch multiple tasks changing common shared files until ownership is reconciled. Use a coherent batch to avoid repeating full CI for each tiny fix. Keep issue #650 packaging and #249 HTTP reliability with their owners.

## Run and inspect

```bash
python scripts/coordination/task_scheduler.py --validate-only
python -m pytest -q tests/contracts/test_task_scheduler.py
python scripts/coordination/resolve_dependencies.py --report-dir coordination-reports
python scripts/coordination/task_scheduler.py --dependency-report coordination-reports/status.json --output-dir coordination-reports
```

Review `coordination-reports/scheduler-plan.json` and `coordination-reports/scheduler-plan.md` in the workflow artifact. Manually run the existing Actions **RetailGrowthAI dependency coordinator** workflow to produce an updated report; this is still not coding-agent automation. The empty event file proves no executor attempt has been made. Do **not** populate fabricated test receipts into the production event ledger.

## Chat instructions

Open a new chat in the RetailGrowthAI ChatGPT Project **for each feature** (Feature #2, #3, #4, #5 and #7). ChatGPT cannot independently open new chats or guarantee 10 continuous concurrent coding sessions. Give each chat the **same** starter with its correct feature ID:

> Continue `saifsiddiqui59/RetailGrowthAI` as Feature #N lead. First read `AGENTS.md`, `docs/FEATURE_CHAT_OPERATIONS.md`, `docs/SCHEDULER_RUNBOOK.md`, `coordination/feature_tasks.json`, `coordination/dependencies.json`, `coordination/execution_policy.json`, `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` and the original feature ledger. Verify latest main, branches, PRs and CI. Batch independent tasks using existing owned branches, don't duplicate source-complete work. Respect a **global maximum of 10** independently claimed worktrees only when a real coding executor is connected; don't pretend issues are live agents. For each recoverable test/build failure diagnose, **fix the code** and retry at most twice. After three unsuccessful attempts defer it and work on other independent tasks. After all eligible first-pass work, revisit deferred failures for at most two further fix/retries, then terminal FAILED. Never retry ambiguous paid or unsafe operations. Keep logs in GitHub, suppress intermediate retry narration, and report only **DONE / IN PROGRESS / FAILED / BLOCKED** in short lines with accurate verified feature counts. DONE needs acceptance + main integration + fresh 4/4 CI. Only coordinator edits shared docs; keep paid GPU OFF, no PROD or WineShopPOS changes.

## Release permissions

No paid AI Foundry coding agent has been connected or authorized here. Do not assume any Azure model rates, spend quotas or billing consent from this scheduler change. The GPU and DEV/PROD deployment gates remain separate and protected.
