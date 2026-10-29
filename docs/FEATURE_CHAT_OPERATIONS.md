# RetailGrowthAI — Batch execution + concise feature-chat status

Effective: 2026-10-29. Canonical policy: `coordination/execution_policy.json`.

## Global feature behavior

1. All existing Feature #2, #3, #4, #5 and #7 work continues; Feature #1 remains **100% development closed**. **Do not restart or duplicate completed tasks.**
2. Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md`, `docs/DEPENDENCY_COORDINATOR.md`, `docs/FEATURE_CHAT_OPERATIONS.md`, `coordination/dependencies.json`, `coordination/feature_tasks.json` and the **source feature ledger/branch** before coding. Verify actual `main`, open/draft PRs, source, issues, CI and ownership. The task inventory is a pinned **snapshot**: its source_status is not automatically integrated completion.
3. **Batch related independent work** into coherent feature-owned changes. Use targeted tests/negative tests during the batch; run existing four-job CI when a batch is ready for review. Never bypass mandatory exact-head PR checks or fresh postmerge main checks. Do not make unrelated tiny commits and rerun full CI merely to announce progress.
4. **Up to 10 independent coding tasks running simultaneously** with distinct branches/worktrees and atomic claims; this is a **limit**, not an assertion that ten sessions are running. The existing GitHub coordinator currently queues issues, not coding agents. No global executor/concurrency enforcement until a reviewed executor is installed.
5. **DONE requires agreed task acceptance, actual supporting tests, accepted integration and a fresh four-job postmerge main pass**. Source-ready is tracked separately from integrated DONE, hosted verification and commercial approval. Preserve genuinely completed source implementation without reopening it for missing external service evidence.
6. Automatically retry **recoverable** network/runner/transient errors at most **two additional times** with bounded backoff and idempotency. Do **not** print intermediate retries to the user; keep true attempt history in CI/issues. NEVER blindly retry uncertain billing/queue ACK/paid inference, permission or security denials, ambiguous writes or nonrecoverable errors. Report the terminal failure and exact reason.
7. Recheck the dependency DAG after successful main CI for merged PRs; the hourly schedule backs this up. In a blocked task record exact ID, owning feature, required output, acceptance and evidence. Continue every independent fixture/source task. Never present test fixtures or generated color bars as real fashion media or AI inference.
8. The coordinator owns `PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md`, `WORK_LOG.md` and verified feature counts **after each integration batch**. Feature leads retain owned branch handoffs and do not edit canonical shared docs by themselves.
9. Issue #650 Azure Functions 120-entry ZIP limit is **coordinator-owned** (PR #665 under review at this checkpoint). Continue unrelated feature source work; don't bypass the same four failing protected packaging tests. Azure #249 503 remains a separate release gate. Reverify issue status regularly.
10. Never automatically start GPU/A100 or billable AI coding calls without separate approval, alter PROD/hosted SQL, touch WineShopPOS, break tenant isolation or bypass security/cost approvals.

## Default user-facing output

Unless the user asks for details, show up to four short status lines, using **only**:

```text
DONE — verified integrated X/Y task IDs.
IN PROGRESS — current batch + next independent work.
FAILED — terminal cause after up to 2 safe internal retries (if any).
BLOCKED — dependency ID / owner / missing approved output (if any).
```

Omit empty categories; **never claim running work just because an issue exists**. A source-complete but unmerged item is not DONE under this policy. Full logs, errors and blockers stay in GitHub even when the user-facing answer is short.

## New ChatGPT conversation per feature

The GitHub workflow cannot itself create or keep alive a ChatGPT Project conversation. Start a new chat inside the same RetailGrowthAI Project and paste this exact starter, changing `<FEATURE>`:

```text
Continue saifsiddiqui59/RetailGrowthAI as Feature #<FEATURE> development lead.
Read AGENTS.md, docs/FEATURE_CHAT_OPERATIONS.md, coordination/execution_policy.json,
coordination/feature_tasks.json, coordination/dependencies.json, docs/PROJECT_STATE.md,
docs/NEXT_TASK.md, docs/DECISIONS.md, docs/WORK_LOG.md, docs/INTERFACES_V1.md,
docs/PARALLEL_WORK.md, docs/CI_AUTOMATION.md and the original numbered feature ledger.
Verify current main, source, all existing branches/draft PRs, issues, artifacts and exact-head CI.
Batch related independent tasks, use targeted tests during batches, run four required CI jobs
at batch boundaries and after coordinator main integration. Don't stop for another feature's
production output if verified fixtures/contracts enable independent work.
Retry transient safe failures internally up to two additional times without intermediate
chat messages. On terminal failures, report the cause; never retry uncertain paid/financial
actions or bypass approvals.
Maximum 10 simultaneously claimed coding tasks globally once an approved executor exists,
each in a separate branch/worktree. Don't claim that the current coordinator runs a coder.
DONE means acceptance + integration + postmerge CI. Keep source-ready/live gates distinct.
Only coordinator changes shared docs and main. GPU OFF; no PROD changes or WineShopPOS.
Send only concise status lines: DONE, IN PROGRESS, FAILED, BLOCKED, with accurate X/Y.
Continue eligible batches without waiting for a new 'continue' message between small commits.
```

Feature task source ledgers pinned in `coordination/feature_tasks.json`:

- #2: 38 tasks, `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md` (draft PR #551).
- #3: 33 packages, `docs/feature3/FEATURE3_33_PACKAGE_STATUS_20261029.md` (main).
- #4: 31 tasks, `video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md` (draft PR #322).
- #5: 22 tasks, `docs/feature5/F5_22_TASK_DEPENDENCIES_20261029.json` (stacked draft PR #465).
- #7: 35 named tracks **A–AI**, `video-engine/feature7/TASKS_20261028.md` (draft PR #513, including narrative tracks Q/R/S and AF–AI).
- #1: source closed; remaining external live integration tracked separately, not reopened.

**Source snapshot counts are not product completion percentages or automatically accepted releases.** To enable actual continuous coding across chat limits, an approved paid coding-agent executor with repository permissions, budget guardrails and atomic task claims must separately be connected. The current safe coordinator remains issue/report-only.
