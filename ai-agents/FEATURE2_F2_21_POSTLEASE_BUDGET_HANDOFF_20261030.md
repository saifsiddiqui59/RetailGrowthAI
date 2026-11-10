# Feature #2 — F2-21 CPU reservation post-lease policy fence (2026-10-30)

**Status:** IN PROGRESS — source-only proposed, not integrated DONE. Parent draft PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`; this branch is a scoped stacked review and does not modify canonical task control tables.

## Change and rationale

- After a trusted atomic CPU reservation returns, re-read the authoritative private quota policy before reporting a usable lease. Reject revoked/suspended policy, changed tenant/campaign/provider, paid-provider enablement, changed UTC billing period, or rollback of the budget revision. The worker and durable store **still must** enforce transactionally fenced lease/usage settlement; a denied post-write receipt may have consumed a reservation and must **not** be automatically retried or charged twice.
- Reject forged receipt `paid_api_calls: false` masquerading as integer zero, and any positive optional worker-inference or motion-dispatch authority flags. A reservation is not synthesis or rights approval.
- Deterministic negative tests cover post-reservation suspension, revision rollback, paid-call type confusion and elevated worker/motion flags. No real CPU model inference, model download, paid API, GPU, cloud write, SQL, PROD, WineShopPOS or sample media.

## Evidence and next gates

- Source: `ai-agents/src/ai_agents/feature2_local_voice_workflow.py` — `reserve_budgeted_local_voice_job`.
- Tests: `ai-agents/tests/test_feature2_local_voice_workflow.py` — new post-lease and receipt-denial cases. **Remote targeted/CI results must be inspected; not claimed passing at authoring time.**
- Task: `F2-21` remains **IN PROGRESS**. Coordinator-owned durable transaction, original voice-worker settlement and fresh 4/4 postmerge `main` remain required.
- Shared release dependency: `ISSUE-650` coordinator-owned Functions ZIP 120-member packaging guard; `ISSUE-249` Azure 503 hosted path. Do not bypass these gates or merge failing CI.
- Coordinator must review this stacked PR after parent #551, update `coordination/task_progress.json` and canonical docs only after accepted integration with verified CI. No completion event submitted.
