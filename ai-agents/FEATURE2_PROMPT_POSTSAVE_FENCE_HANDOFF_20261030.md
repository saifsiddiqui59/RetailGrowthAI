# Feature #2 F2-03 — Prompt Improver post-CAS authorization fence (2026-10-30)

**Original task:** F2-03, Prompt Improver and reviewed script-revision workflow. **State:** IN PROGRESS (source-only, not integrated DONE).

## Source change

- `ai-agents/src/ai_agents/prompt_improver.py::commit_reviewed_prompt_draft` now rechecks the authoritative current editor *after* a private draft CAS receipt, so a role revoked while the callback is in flight cannot receive a false successful result.
- Explicit storage receipt fields may not claim publication, paid motion, a paid provider call, approved review, or skipped fact/media-rights review. Missing optional receipt fields retain compatibility with existing coordinator callbacks; the authoritative record always has nonpublishable DRAFT fields.
- Added eight synthetic-only positive/negative regression cases in `tests/ai/test_prompt_improver.py`, including role revocation after the write and forged elevated storage receipts.
- This does **not** roll back already-written bytes and cannot replace transactional membership/lease fencing in the actual database. No real JWT, retailer, hosted storage, human approval, paid provider, GPU, PROD, deployment or WineShopPOS operation was performed.

## Evidence and acceptance gates

- Dedicated branch: `feat/feature2-prompt-postsave-fence-20261030`, stacked on the existing unified draft [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551). This change must not be merged separately without coordinator review and the selected integration order.
- Targeted test command for a suitable Python environment: `uv run --project ai-agents pytest tests/ai/test_prompt_improver.py -q`. No local execution is asserted; inspect the exact-head GitHub CI run.
- **Dependency:** `F2-03-HOSTED-CAS`, owner **coordinator / Supabase DEV backend**. Required output: a real JWT/RLS-authenticated tenant-private prompt draft endpoint with transactionally fenced membership, original proposal SHA and human signed decision, atomic compare-and-swap and source-current postwrite readback. Acceptance: two isolated real DEV shop-owner accounts, foreign-tenant/role-revocation/replay denial, private DRAFT-only persisted bytes, and exact-head 4/4 PR plus fresh 4/4 postmerge main CI.
- **Shared gate:** [Issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) — coordinator-owned protected Azure Functions ZIP package limit. Do not bypass its release tests.
- Coordinator alone updates `coordination/task_progress.json`, canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md` after accepted integration. No DONE event proposed while this is unmerged.

**Fixture policy:** test callbacks are synthetic. No customer media, real approval, actual AI output or hosted authentication was used.
