# Obsolete 2026-10-29 coordinator-control draft #696 exact patches — 2026-11-19

Original PR [#696](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/696) at exact head `dfa0e58c01f4f961180682f6bedd85c9d308d0e4` (12 changed paths) is a DRAFT against a now-obsolete coordinator-only scheduling workflow. Active five independent feature owners and current saifsiddiqui59/RetailGrowthAI permissions are governed by unchanged `AGENTS.md` and `docs/FEATURE_SELF_MERGE_POLICY_20261031.md` on main. Do not merge the old draft's rewrites to `AGENTS.md`, pinned `coordination/feature_tasks.json`, `coordination/execution_policy.json`, or canonical documents.

More recent [#964](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/964) proposes a CAS claim/lease queue, with added global ten-active-PR guard and exact head CI 4/4, but is still awaiting independent coordination/shared-policy review. This archive does NOT merge #964 or create a worker pool, and advisory slots remain noncoding.

## Full original PR #696 GitHub changed-file patch hunks
### AGENTS.md
~~~~diff
@@ -56,3 +56,13 @@ Read `docs/SCHEDULER_RUNBOOK.md` before feature work. The shared coordinator's e
 - Use Playwright for DEV UI/login only with isolated, real nonprivileged test accounts **after** Auth Admin provisioning; mocked Playwright is not hosted authentication. An existing owner-controlled approval login must never be placed in Git, automated for approval, elevated or used to bypass permission gates.
 - After every batch, update exact task IDs, source/PR/CI proof and status in owned handoff and propose reviewed `coordination/task_progress.json` status events; only coordinator integrates shared status and canonical docs. `scripts/coordination/task_status.py` verifies PR merge/accepted scope/fresh main 4/4 before DONE.
 - GPU OFF, all paid provider/model calls OFF by default, no PROD or WineShopPOS. Bounded one-off existing GPT-4.1 Mini DEV inference is optional only with a proven usage meter and enforced cost guard; do not start without that guard.
+
+## Mandatory chat control-manager loop (2026-10-29)
+On **every** Feature #2/#3/#4/#5/#7 ChatGPT turn (including scheduled chat runs), read `coordination/chat_worker_control.json` and `docs/CHAT_TASK_CONTROL.md` before reporting. The central task inventory `coordination/feature_tasks.json` points to the control file. **Work, then continue to the next independent eligible task within this same chat execution** after each DONE/BLOCKED/FAILED/DEFERRED task; do not stop after creating a PR, pushing one commit or reading task counts. Recheck task evidence and owned work before each new assignment. Consider up to 10 nonconflicting tasks in a coherent batch, but **10 simultaneous tasks is a global maximum requiring real atomic claims and distinct worktrees**; without an enforceable claim store, work sequentially and never claim ten workers are running. Do not wait for an external coding executor; this chat can use its connected GitHub tools to perform feasible owned work. Chat cannot automatically continue beyond a finished turn: the next trigger must start the next execution. All existing source-vs-DONE, approvals, cost, safety and coordinator-only merge rules continue to apply.
+
+## Strict user-visible counts-only rule (all active feature chats)
+STRICT COUNTS-ONLY OUTPUT (overrides any earlier DONE / IN PROGRESS / FAILED / BLOCKED instructions): Do all tool calls and development silently. Do not send startup narration, commentary, progress reports, warnings, lists, code, links, summaries or reasons in the chat. After execution, output exactly one line: 'Feature #N: X/Y completed' for the appropriate feature, using verified central task counts. When counts cannot be verified output exactly 'Feature #N: completion count not verified'. Never display other text unless the user explicitly requests an explanation. Do not suppress internal GitHub task evidence or error logging.
+
+
+## Feature-chat response format
+After completing the available task work, reply with only a single verified count line: `Feature #N: X/Y completed`. If the central count is not verifiable, reply only `Feature #N: completion count not verified`. Do not include unsolicited task lists or commentary; keep development logs and task evidence in GitHub.
~~~~

### coordination/chat_worker_control.json
~~~~diff
@@ -0,0 +1,80 @@
+{
+  "schema_version": 1,
+  "purpose": "ChatGPT task-control instructions, not a background coding executor or a GitHub Actions trigger",
+  "active_features": [
+    "2",
+    "3",
+    "4",
+    "5",
+    "7"
+  ],
+  "read_at_start_of_every_chat_execution": [
+    "AGENTS.md",
+    "docs/CHAT_TASK_CONTROL.md",
+    "docs/FEATURE_CHAT_OPERATIONS.md",
+    "coordination/feature_tasks.json",
+    "coordination/task_progress.json",
+    "coordination/shared_feature_references.json",
+    "coordination/dependencies.json",
+    "coordination/execution_policy.json",
+    "docs/PROJECT_STATE.md",
+    "docs/NEXT_TASK.md",
+    "docs/DECISIONS.md",
+    "docs/WORK_LOG.md"
+  ],
+  "entrypoint_instruction": "You are the coding worker for the requested feature in THIS chat execution. Before answering, read the control files and current GitHub evidence. Select and actually attempt the next eligible owned pending task. Do not respond with a count before attempting feasible development work.",
+  "on_task_resolution_instruction": "Immediately reread live task ownership, dependency, PR/CI evidence and task progress. Then select the next independent eligible pending task and continue work within this same execution. Repeat after DONE, BLOCKED, FAILED or DEFERRED, including while unrelated CI is pending. Do not request another user 'continue' message between tasks.",
+  "end_of_execution_instruction": "Stop only if no safe eligible tasks remain or the current chat/tool execution reaches its limit. At the next user or scheduled trigger reread the control table and resume. Do not claim the chat runs continuously between triggers.",
+  "planning": {
+    "preferred_independent_tasks_per_batch": 10,
+    "maximum_global_simultaneous_claims": 10,
+    "requires_atomic_global_claims_for_parallel_execution": true,
+    "requires_distinct_nonoverlapping_owned_branches_and_worktrees": true,
+    "without_atomic_claim_store": "Do not claim concurrent execution or reserve ten tasks; process independent eligible items sequentially or as a nonconflicting coding batch, one actual task at a time.",
+    "existing_scheduler_candidates_are_not_active_claims": true
+  },
+  "pick_next_task": {
+    "registry": "coordination/feature_tasks.json",
+    "reviewed_status_events": "coordination/task_progress.json",
+    "dependency_registry": "coordination/dependencies.json",
+    "cross_feature_reference_registry": "coordination/shared_feature_references.json",
+    "verify_branch_pr_and_exact_head_ci": true,
+    "skip_source_complete_and_verified_integrated": true,
+    "skip_other_owner_and_conflicting_active_work": true,
+    "skip_external_approval_gates_but_continue_unrelated_items": true,
+    "never_assume_source_snapshot_means_verified_done": true
+  },
+  "repair": {
+    "first_pass_total_attempts": 3,
+    "deferred_second_pass_additional_attempts": 2,
+    "maximum_total_safe_attempts": 5,
+    "diagnose_and_fix_before_retry": true,
+    "unsafe_errors_never_auto_retry": [
+      "unknown_billing_ack",
+      "paid_provider_submission",
+      "non_idempotent_write",
+      "approval_missing",
+      "tenant_security_denial",
+      "license_denied",
+      "unknown_classification"
+    ]
+  },
+  "evidence": {
+    "task_acceptance_required": true,
+    "source_tests_do_not_equal_integrated_done": true,
+    "integrated_done_requires_reviewed_main_merge_and_fresh_four_job_ci": true,
+    "update_owned_handoff_and_propose_reviewed_task_progress_event": true,
+    "canonical_docs_and_main_merges_coordinator_owned": true,
+    "do_not_fabricate_claims_test_results_or_completion_counts": true
+  },
+  "safety": {
+    "GPU_off": true,
+    "paid_models_off_by_default": true,
+    "no_prod_or_unapproved_hosted_migrations": true,
+    "do_not_modify_WineShopPOS": true,
+    "no_unrequested_samples": true
+  },
+  "user_output": "After finishing task work, respond with one line only: Feature #N: X/Y completed, where X/Y comes from verified centralized status. If unavailable, respond only: Feature #N: completion count not verified. Do not include progress narration or task lists unless requested. Preserve internal logs and evidence in GitHub.",
+  "suppress_interim_user_messages": true,
+  "report_only_after_attempting_work": true
+}
~~~~

### coordination/execution_policy.json
~~~~diff
@@ -99,6 +99,16 @@
     "never_merge_failing_required_ci": true,
     "do_not_promote_ledger_snapshot_to_verified_task_state_without_evidence": true
   },
+  "chat_worker_control": {
+    "path": "coordination/chat_worker_control.json",
+    "read_on_each_chat_execution": true,
+    "continue_after_each_task_within_current_execution": true,
+    "prefer_up_to_ten_independent_tasks_per_batch": true,
+    "maximum_parallel_claims_global": 10,
+    "parallel_requires_atomic_claims": true,
+    "no_continuous_chat_between_triggers": true,
+    "do_not_replace_advisory_scheduler_with_fake_executor": true
+  },
   "scheduler": {
     "mode": "advisory_until_authorized_executor_connected",
     "cron": "17 * * * *",
~~~~

### coordination/feature_tasks.json
~~~~diff
@@ -1,5 +1,6 @@
 {
   "schema_version": 1,
+  "chat_execution_control": "coordination/chat_worker_control.json",
   "generated_from_verified_sources": "2026-10-29",
   "description": "All 159 explicitly numbered active feature tasks, preserving owner ledger evidence without falsely treating source completion as production/integrated DONE. Additional 16 typed handoffs remain in coordination/dependencies.json.",
   "source_ledgers": [
~~~~

### docs/CHAT_TASK_CONTROL.md
~~~~diff
@@ -0,0 +1,32 @@
+# Chat-controlled backlog pickup (not the scheduled trigger)
+
+This is the **control-manager instruction** for every RetailGrowthAI Feature #2/#3/#4/#5/#7 ChatGPT execution. The machine-readable rule is `coordination/chat_worker_control.json`, referenced from the task inventory and `AGENTS.md`. It is distinct from the read-only GitHub Actions advisory scheduler. **It does not launch or keep ChatGPT running between turns.**
+
+## At the start of EVERY feature chat / scheduled run
+
+1. Read `AGENTS.md`, `coordination/chat_worker_control.json`, `coordination/feature_tasks.json`, `coordination/task_progress.json`, `coordination/dependencies.json`, `coordination/shared_feature_references.json`, `coordination/execution_policy.json`, this page, the feature's original ledger and the normal project handoff documents.
+2. Verify latest `main`, existing feature branch, open/draft PRs, required four CI jobs and task-owner paths. Never reimplement source-complete work, claim mock fixtures are real outputs, or override coordinator integration ownership.
+3. **Do real work before reporting a count.** Select the highest-priority independent unblocked owned task with a concrete achievable deliverable. Implement source/test changes, verify what can actually be verified, and update the feature handoff. If a task is approval- or dependency-blocked, record exact ID/owner/missing output/acceptance criteria and select another independent task.
+
+## On EVERY resolved task: continue in the same chat run
+
+**CONTINUE WITH THE NEXT TASK WITHOUT ASKING THE USER.** After completing, deferring, blocking or failing an assignment, reread the *current* registry, reviewed evidence and dependency status; select the next safe eligible task and repeat. A PR created, commit pushed, CI pending or single task closed is **not** the end condition. While waiting for CI, move to independent nonconflicting work. Do not spin on one blocked task. Process related work in coherent batches, with targeted checks during implementation and four mandatory checks at PR/integration boundaries.
+
+### Parallel work is conditional, not fictional
+
+The **global cap is ten actually claimed, independently owned coding tasks across all features**, NOT ten running tasks per feature. Parallel execution requires a real atomic claim store/lease and separate nonconflicting branches/worktrees; neither the task registry nor the advisory planner provides those leases. Without them, a chat may *consider up to ten independent tasks in a batch*, but must execute its actual owned work sequentially or in nonconflicting verifiable batches. Never state that ten workers are running merely because ten candidates were selected. Other feature chats may be editing simultaneously: reverify remote PRs and ownership before every change.
+
+For recoverable failures: diagnose and **fix the code** before retry #2 and #3; defer after attempt #3, work through all eligible first-pass tasks, then revisit safe deferred failures for at most two more repaired attempts (#4/#5). Do not blindly retry unknown payments/queues, permission or license denials or security failures.
+
+### When to stop
+
+Only stop when no safe independent tasks remain **or the current ChatGPT execution/tool limit is reached**. You cannot keep a normal chat alive or self-launch a new turn after it ends. At the next user or automation trigger, reread the current registry and immediately continue from the next eligible task. The two-hour ChatGPT automations are **triggers**, not control-table code and not permanent workers.
+
+On completion provide **only** `Feature #N: X/Y completed` if X is independently verified as accepted integrated DONE; otherwise say `Feature #N: completion count not verified`. Keep actual work evidence in PRs and owned handoffs. Only the coordinator edits canonical project docs, shared task status and `main`. GPU OFF; paid models, PROD and unapproved migrations OFF; never touch WineShopPOS.
+
+## Strict user-visible counts-only rule (all active feature chats)
+STRICT COUNTS-ONLY OUTPUT (overrides any earlier DONE / IN PROGRESS / FAILED / BLOCKED instructions): Do all tool calls and development silently. Do not send startup narration, commentary, progress reports, warnings, lists, code, links, summaries or reasons in the chat. After execution, output exactly one line: 'Feature #N: X/Y completed' for the appropriate feature, using verified central task counts. When counts cannot be verified output exactly 'Feature #N: completion count not verified'. Never display other text unless the user explicitly requests an explanation. Do not suppress internal GitHub task evidence or error logging.
+
+
+## Feature-chat response format
+After completing the available task work, reply with only a single verified count line: `Feature #N: X/Y completed`. If the central count is not verifiable, reply only `Feature #N: completion count not verified`. Do not include unsolicited task lists or commentary; keep development logs and task evidence in GitHub.
~~~~

### docs/DECISIONS.md
~~~~diff
@@ -1015,3 +1015,7 @@
 - No user-facing media demos/samples or review requests while owner is unavailable for at least 10 hours; deterministic test fixtures/CPU regressions are still allowed. No paid GPU, nonessential provider APIs, new compute or PROD. GPT-4.1 Mini may be used only for explicit small, metered, one-off existing DEV tests; automatic model calls remain OFF.
 - Auth test accounts must be created through supported DEV Auth Admin, with credentials from a trusted local secret store, never direct inserts to auth.users or committed passwords. Existing approval account is reserved for human-controlled authorization, not automated rights or payment approval.
 - Original numbered task status is recorded in reviewed append-only `coordination/task_progress.json` events, then GitHub Actions verifies PR merge and independent postmerge main 4/4 for DONE. The status artifact is not self-reported fixture success.
+
+
+## 2026-10-29 — Chat control-manager pickup instead of an external paid executor
+Use `coordination/chat_worker_control.json`, linked from the central task inventory and `AGENTS.md`, as the instruction source for Feature #2/#3/#4/#5/#7 ChatGPT runs. Separate **triggering** (user turn or existing two-hour ChatGPT automation) from **within-run task selection** (read current registry, perform an eligible owned task, update verified evidence, select the next). The up-to-ten cap is global and requires atomic exclusive claims and nonoverlapping worktrees for real parallel workers; absent that infrastructure, use safe sequential/coherent batches and never overstate concurrency. No new paid coding executor, live model, GPU, PROD or WineShopPOS actions; no guarantee of continuous running beyond a chat execution. Coordinator alone integrates to main after required CI.
~~~~

### docs/FEATURE_CHAT_OPERATIONS.md
~~~~diff
@@ -71,3 +71,13 @@ Read `docs/SCHEDULER_RUNBOOK.md`; `coordination/execution_policy.json` is the ca
 Read `docs/FEATURE_CHAT_SETUP_20261029.md` and `coordination/shared_feature_references.json`. Respect the exact project chat names, all documented feature input producer/consumer references and dependency IDs. During the owner's next 10 hours away, DO NOT create user-facing demos, sample video/reels, generated images or review requests; continue code, isolated CPU contracts and tests, and only produce requested samples after explicit owner confirmation.
 For optional signed UI checks, use Playwright against DEV with separate role-scoped test logins **only once actually provisioned**; never store approval-password secrets, automatically approve or claim mock sign-in is live. See `docs/DEV_TEST_LOGIN_PLAYWRIGHT.md`. GPU OFF and other paid models disabled; GPT-4.1 Mini is permitted only for one-off narrowly budgeted tests with enforced metering, and never as an autonomous coding agent.
 Every task/batch: update the original feature ledger with exact ID, PR/CI/acceptance and next status; send coordinator a reviewable `coordination/task_progress.json` event. The trusted scheduled report validates real GitHub evidence, emits task-manager status and refuses false DONE. Chat answers remain DONE / IN PROGRESS / FAILED / BLOCKED only.
+
+## Chat-controlled continuation (per task, not scheduler-only)
+The active control manager is `coordination/chat_worker_control.json`, referenced by `coordination/feature_tasks.json` and explained in `docs/CHAT_TASK_CONTROL.md`. Every feature chat must read this at **startup and after each resolved assignment**. Within the **same** run, immediately select and perform the next independent eligible task; no new user 'continue' message is required between tasks. Do source/test work before merely reporting the X/Y count. The control manager does not create new ChatGPT turns. Consider up to ten safely independent tasks per coherent batch; claim actual parallel work only if global atomic claims, worktree isolation and nonoverlapping ownership can be verified. Otherwise continue sequentially. Continue past unrelated CI/dependency blockers, but never bypass protected review, merged-main acceptance, cost gates, safety or the chat execution boundary.
+
+## Strict user-visible counts-only rule (all active feature chats)
+STRICT COUNTS-ONLY OUTPUT (overrides any earlier DONE / IN PROGRESS / FAILED / BLOCKED instructions): Do all tool calls and development silently. Do not send startup narration, commentary, progress reports, warnings, lists, code, links, summaries or reasons in the chat. After execution, output exactly one line: 'Feature #N: X/Y completed' for the appropriate feature, using verified central task counts. When counts cannot be verified output exactly 'Feature #N: completion count not verified'. Never display other text unless the user explicitly requests an explanation. Do not suppress internal GitHub task evidence or error logging.
+
+
+## Feature-chat response format
+After completing the available task work, reply with only a single verified count line: `Feature #N: X/Y completed`. If the central count is not verifiable, reply only `Feature #N: completion count not verified`. Do not include unsolicited task lists or commentary; keep development logs and task evidence in GitHub.
~~~~

### docs/FEATURE_CHAT_SETUP_20261029.md
~~~~diff
@@ -37,3 +37,6 @@ The machine-readable map `coordination/shared_feature_references.json` is author
 ## After task completion
 
 Feature lead documents verified source result and submits to coordinator. Coordinator evaluates actual PR integration and full CI, records an evidence-backed event in `coordination/task_progress.json`, and the scheduled workflow refreshes `task-status.json/.md` in Actions artifacts. **Neither chat text nor an advisory scheduler candidate automatically means the task ran.**
+
+## Required startup behavior for all five named chats
+At **every** manual or scheduled ChatGPT execution, read `coordination/chat_worker_control.json` and `docs/CHAT_TASK_CONTROL.md` in addition to the files above. Treat their `entrypoint_instruction` and `on_task_resolution_instruction` as the active control manager: perform a real eligible coding task, document evidence, and immediately select the next one without user intervention within the same run. Do not end after a single PR/commit or status count when other independent safe tasks can be addressed. Global ten-claim limit is conditional on real atomic claims; do not pretend ten parallel workers exist. A chat turn cannot keep itself alive after it ends; the next user or automation trigger will reread the current backlog. The scheduler is separate and remains advisory.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1346,3 +1346,9 @@ Detailed handoff: `docs/feature3/PRE_GPU_READINESS_20261028.md`. No WineShopPOS
 2. Verify new task-progress acceptance contract rejects fake DONE, requires merged PR, coordinator-reviewed evidence and four successful main CI jobs; the live coordinator report must produce `task-status.json/.md`, not mark 159 tasks done.
 3. For DEV test logins, operator must supply trusted Supabase **Auth Admin** access and two unique strong secrets to run safe script, then verify signed login and separate role/RLS assignment. No direct auth.users SQL, approval-account password change, or automated approval. If unsupported, leave two accounts BLOCKED and do not assert hosted UI success.
 4. Continue independent source and Playwright mock tests without generating review samples during owner absence. No paid GPU/FLUX/Wan or AI coding calls. GPT-4.1 Mini optional one-off test only after metered hard cap. Merge after full exact-head and postmerge CI.
+
+
+## 2026-10-29 — Chat backlog pickup control next steps
+- Review coordinator PR from `chore/chat-backlog-pickup-control-20261029` for `coordination/chat_worker_control.json`, `docs/CHAT_TASK_CONTROL.md` and startup instructions on each feature chat.
+- Verify exact-head mandatory CI, have coordinator merge only after checks, then verify fresh main 4/4. This is a chat instruction/control-manager change; **not** a new background coding executor.
+- On every subsequent ChatGPT feature trigger, read the control file and immediately attempt the next safe independent owned task; after finishing/defer/block, pick another within the same run. Without atomic claim backend, process sequentially; never claim ten active parallel tasks merely from the advisory schedule. Retain cost and safety approvals.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1355,3 +1355,7 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 ## 2026-10-29 — Shared references, DEV test-account setup and task-status reporter (integration proposal)
 - Verified pre-existing owner-controlled approval email appears in existing RetailGrowthAI Supabase DEV Auth (read-only only); no credentials disclosed or changed. Two nonprivileged test auth identities proposed, but **NOT CREATED**, because connected Supabase management tools have no Auth Admin createUser and secret was not available. Prepared DEV-only fail-closed admin API provisioning script and Playwright guidance, no SQL direct auth user writes, no shop role grant, no PROD.
 - Added five exact named chat mappings, verified cross-feature producer/consumer dependency contract, 10-hour no-sample/no-review rule, GPU/paid-model prohibition with GPT-4.1 Mini strictly optional bounded test, and evidence-based `task_progress.json` status updates. GitHub Actions will publish fresh task-manager status reports; only externally verified merged PR + fresh main 4/4 and reviewer evidence can be marked DONE. Candidate coding scheduler remains advisory; no worker started. All changes require PR/main CI acceptance, no WineShopPOS.
+
+
+## 2026-10-29 — Chat control-manager continuation proposal (branch-only)
+The coordinator branch `chore/chat-backlog-pickup-control-20261029` introduces `coordination/chat_worker_control.json` and `docs/CHAT_TASK_CONTROL.md`, wired into the shared task registry and `AGENTS.md`. Every active feature ChatGPT execution is instructed to read the registry, attempt actual eligible owned work and select the next task in the same run instead of stopping after a PR/count. Up to ten **global** actual parallel tasks require atomic claims and distinct nonconflicting worktrees; without a claim service, chats work sequentially/coherently and do not claim ten workers. The existing GitHub Actions scheduler remains advisory. This source/docs proposal does **not** create continuous ChatGPT sessions, trigger an execution, integrate a feature, approve paid models, change DEV/PROD, or affect WineShopPOS. PR/main CI and coordinator merge still required.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -772,3 +772,6 @@ Use scripts/checkpoint.sh after completing a task.
 ## 2026-10-29 — Consolidated handoffs, signed test-login preparation and task-status reports
 - Read latest canonical docs, Supabase DEV Auth read-only evidence and 16 handoff/159 task registries. Verified existing owner approval email exists without changing credentials. Connected Supabase tool lacks supported Auth Admin mutation; created test account provisioning script but did not run it and did not create two new Auth users.
 - Added five exact feature chat names, cross-feature map, 10-hour no-user-visible-samples directive, Playwright/DEV test-auth protocol, zero paid GPU/model by default and strictly bounded optional existing GPT-4.1 Mini test rules. Added reviewed task-status event ledger, fail-closed PR/main CI DONE verifier, tests and coordinator task-status artifact. No costly cloud/model, PROD/WineShopPOS or rights/permission changes. Exact-head CI and main integration pending independent verification.
+
+
+- 2026-10-29: On coordinator branch `chore/chat-backlog-pickup-control-20261029`, authored chat-only backlog pickup instructions in `coordination/chat_worker_control.json` and `docs/CHAT_TASK_CONTROL.md`; linked from task inventory, execution policy, AGENTS, and feature startup/runbook. Added offline contract checks. The next-task loop is an **instruction within an active ChatGPT turn**, not automatic new turns or ten real coding workers; global claims remain unimplemented and the Actions scheduler remains advisory. Awaiting PR/CI/review, no main merge, cloud operation, GPU spending or WineShopPOS changes.
~~~~

### tests/contracts/test_chat_worker_control.py
~~~~diff
@@ -0,0 +1,42 @@
+"""Contract checks for the chat-controlled, bounded next-task loop (not an executor)."""
+import json
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+def load(path):
+    return json.loads((ROOT / path).read_text(encoding="utf-8"))
+
+def test_chat_control_is_wired_into_authoritative_inventory_and_policy():
+    control = load("coordination/chat_worker_control.json")
+    registry = load("coordination/feature_tasks.json")
+    policy = load("coordination/execution_policy.json")
+    assert control["schema_version"] == 1
+    assert registry["chat_execution_control"] == "coordination/chat_worker_control.json"
+    assert policy["chat_worker_control"]["path"] == registry["chat_execution_control"]
+    assert set(control["active_features"]) == set(policy["scope"]["active_features"])
+    assert control["planning"]["maximum_global_simultaneous_claims"] == policy["concurrency"]["max_running_independent_coding_tasks"] == 10
+
+def test_no_fake_parallel_workers_or_unbounded_chat_execution():
+    control = load("coordination/chat_worker_control.json")
+    assert control["planning"]["requires_atomic_global_claims_for_parallel_execution"] is True
+    assert control["planning"]["existing_scheduler_candidates_are_not_active_claims"] is True
+    assert "Do not claim concurrent execution" in control["planning"]["without_atomic_claim_store"]
+    assert "Do not claim" in control["end_of_execution_instruction"]
+    assert "Immediately reread" in control["on_task_resolution_instruction"]
+    assert "actually attempt" in control["entrypoint_instruction"]
+    assert control["repair"]["maximum_total_safe_attempts"] == 5
+    assert control["repair"]["first_pass_total_attempts"] + control["repair"]["deferred_second_pass_additional_attempts"] == 5
+
+def test_cost_security_and_done_gates_stay_closed():
+    control = load("coordination/chat_worker_control.json")
+    assert all(control["safety"].values())
+    assert all(control["evidence"].values())
+    assert "paid_provider_submission" in control["repair"]["unsafe_errors_never_auto_retry"]
+    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
+    assert "coordination/chat_worker_control.json" in text
+    assert "docs/CHAT_TASK_CONTROL.md" in text
+
+def test_single_line_verified_task_count():
+    control = load("coordination/chat_worker_control.json")
+    assert "one line only" in control["user_output"]
+    assert "completion count not verified" in control["user_output"]
~~~~

## Outstanding
Current coordination queue review remains open in #964. Original 159 task registry immutable; no original task marked DONE from a draft retirement. No GPU, cloud, paid model, PROD or WineShopPOS.