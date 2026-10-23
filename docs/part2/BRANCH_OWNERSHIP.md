# Workstreams / parallel ownership

Each `feat/p2-*` branch starts from the integration baseline and targets **`feat/part2-integration`**, never `main`. Worktrees may execute in parallel, but this GitHub-based session performs sequential independent tool actions; no concurrency of code implementation is claimed.

| Workstream | Branch | Exclusive scope |
|---|---|---|
| Provider adapters + media restrictions | `feat/p2-provider-adapters` | `azure-functions/campaign-api/social_providers.py`, provider API tests |
| Tenant schema + credential storage | `feat/p2-data-security` | `supabase/part2/pending/**`, corresponding tests |
| OAuth encryption, scheduler, retry/reconcile primitives | `feat/p2-publishing-runtime` | `social_oauth.py`, `social_scheduling.py`, future `social_runtime.py` and owned API tests |
| Read-only frontend and safe schedule/approval UX | `feat/p2-social-ui` | `frontend/src/features/social/**`, `tests/frontend/social*;` root React route and package test command only |
| Part 2 handoffs and API decisions | `feat/p2-documentation` | `docs/part2/**` only |
| Follow-on integration paths | new `feat/p2-oauth-api`, `feat/p2-dispatch-worker`, `feat/p2-publishing-quota`, `feat/p2-security-e2e` | Narrow paths allocated before each start; changes to P1 contract require Coordinator boundary review |

Avoid changing `.github/workflows/**`, shared `docs/INTERFACES_V1.md`, existing P1 migrations, WineShopPOS and GenAI Galaxy. Internal PR review and squash merge are Part 2 Lead responsibilities.

## Additional completed isolated tasks (2026-10-23)
- `feat/p2-approval-media-gates` #118 — owns `social_publish_policy.py` + `test_social_publish_policy.py`; internally merged with 4/4.
- `feat/p2-social-read-api` #119 — owns `social_read_api.py` + `test_social_read_api.py` and additive `function_app.py` route; internally merged 4/4, feature flag OFF.
- `feat/p2-dispatch-fencing` #123 — owns `social_dispatch.py` + `test_social_dispatch.py`; internally merged with 4/4.
- `feat/p2-final-handoff-docs` — owns `docs/part2/**` only; documents exact sources/CI/remaining tasks and moves through its own internal PR.
- Integration maintenance: actual `main` two-parent merge `55470665` to reconcile P1 dashboard and P2 social route. This is part-owned integration and is not a final PR to `main`.

## OAuth follow-on workstreams — 2026-10-23
- `feat/p2-oauth-lifecycle` PR #131 — `social_oauth_lifecycle.py`, scoped unit tests, 4/4 merged.
- `feat/p2-oauth-repository` PR #133 — `social_oauth_repository.py`, mock backend RPC transport tests, 4/4 merged.
- `feat/p2-oauth-db-atomic` PR #132 — staged `supabase/part2/pending/**` P2 OAuth SQL, `tests/security/part2_social_negative.sql`, narrow conditional disposable Supabase CI invocation; 4/4 merged, **NOT hosted**.
- `feat/p2-oauth-handoff-docs` — Part 2-only architecture/next task/decision handoff.
