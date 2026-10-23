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
