# Chat-controlled backlog pickup (not the scheduled trigger)

This is the **control-manager instruction** for every RetailGrowthAI Feature #2/#3/#4/#5/#7 ChatGPT execution. The machine-readable rule is `coordination/chat_worker_control.json`, referenced from the task inventory and `AGENTS.md`. It is distinct from the read-only GitHub Actions advisory scheduler. **It does not launch or keep ChatGPT running between turns.**

## At the start of EVERY feature chat / scheduled run

1. Read `AGENTS.md`, `coordination/chat_worker_control.json`, `coordination/feature_tasks.json`, `coordination/task_progress.json`, `coordination/dependencies.json`, `coordination/shared_feature_references.json`, `coordination/execution_policy.json`, this page, the feature's original ledger and the normal project handoff documents.
2. Verify latest `main`, existing feature branch, open/draft PRs, required four CI jobs and task-owner paths. Never reimplement source-complete work, claim mock fixtures are real outputs, or override coordinator integration ownership.
3. **Do real work before reporting a count.** Select the highest-priority independent unblocked owned task with a concrete achievable deliverable. Implement source/test changes, verify what can actually be verified, and update the feature handoff. If a task is approval- or dependency-blocked, record exact ID/owner/missing output/acceptance criteria and select another independent task.

## On EVERY resolved task: continue in the same chat run

**CONTINUE WITH THE NEXT TASK WITHOUT ASKING THE USER.** After completing, deferring, blocking or failing an assignment, reread the *current* registry, reviewed evidence and dependency status; select the next safe eligible task and repeat. A PR created, commit pushed, CI pending or single task closed is **not** the end condition. While waiting for CI, move to independent nonconflicting work. Do not spin on one blocked task. Process related work in coherent batches, with targeted checks during implementation and four mandatory checks at PR/integration boundaries.

### Parallel work is conditional, not fictional

The **global cap is ten actually claimed, independently owned coding tasks across all features**, NOT ten running tasks per feature. Parallel execution requires a real atomic claim store/lease and separate nonconflicting branches/worktrees; neither the task registry nor the advisory planner provides those leases. Without them, a chat may *consider up to ten independent tasks in a batch*, but must execute its actual owned work sequentially or in nonconflicting verifiable batches. Never state that ten workers are running merely because ten candidates were selected. Other feature chats may be editing simultaneously: reverify remote PRs and ownership before every change.

For recoverable failures: diagnose and **fix the code** before retry #2 and #3; defer after attempt #3, work through all eligible first-pass tasks, then revisit safe deferred failures for at most two more repaired attempts (#4/#5). Do not blindly retry unknown payments/queues, permission or license denials or security failures.

### When to stop

Only stop when no safe independent tasks remain **or the current ChatGPT execution/tool limit is reached**. You cannot keep a normal chat alive or self-launch a new turn after it ends. At the next user or automation trigger, reread the current registry and immediately continue from the next eligible task. The two-hour ChatGPT automations are **triggers**, not control-table code and not permanent workers.

On completion provide **only** `Feature #N: X/Y completed` if X is independently verified as accepted integrated DONE; otherwise say `Feature #N: completion count not verified`. Keep actual work evidence in PRs and owned handoffs. Only the coordinator edits canonical project docs, shared task status and `main`. GPU OFF; paid models, PROD and unapproved migrations OFF; never touch WineShopPOS.
