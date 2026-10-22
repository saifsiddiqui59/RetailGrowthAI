# Workstream A — Supabase foundation and handoff

## Verified deployment — 2026-10-22
- Dedicated RetailGrowthAI Supabase project: `jeearzffnjbvghwjjjrf` (Tokyo, `ap-northeast-1`). **Treat as development/pilot only**; a separate PROD Supabase project is still required.
- Three migrations applied successfully using Supabase migration history, then migration file versions synchronized with the remote history:
  - `20261022085124_p1_foundation.sql` — schema, ownership, RLS, API column grants
  - `20261022085132_p1_private_media.sql` — private bucket and tenant-path policies
  - `20261022085503_p1_security_hardening.sql` — indexes and revoke execute on pre-existing `public.rls_auto_enable()`
- Verified **10/10** business tables with RLS, **25** public RLS policies, **4** private-storage policies; bucket `retailgrowth-media` is `public=false`.
- Executed `tests/security/rls_negative.sql` (minus `psql` directives) against the dedicated project through `execute_sql`; completed without SQL assertion errors. Covered positive authorized reads + onboarding, negative cross-tenant read/write/membership escalation/owner forgery, VIEWER cannot edit, deactivated member denied, and anonymous denied. `ROLLBACK` ensured 0 shops / 0 synthetic test users remain.
- Executed `tests/security/storage_negative.sql` through `execute_sql`; completed without SQL assertion errors. Covered authorized media read/upload, wrong-tenant read/upload/asset-path move denial, and VIEWER upload denial. Transaction rolled back; zero fake storage objects remain.
- Post-deployment Supabase **security advisor: 0 lints**. Initial performance advisor detected nine unindexed foreign keys; a follow-up migration created indexes. Expect initial unused-index information notices for an empty database.

## Deployment boundary
Only the RetailGrowthAI project above was modified. **Never** connect or alter WineShopPOS, WineshopPOS_DEV, voice/optical projects. No auth test accounts or user data were persisted. The RetailGrowthAI database is distinct from the later-required PROD project.

For future clean database setup, apply committed `supabase/migrations/*.sql` chronologically via Supabase CLI/MCP. Migration versions in the filenames now match the remote version history. For each new isolated disposable test project, run the `psql` tests after applying migrations with `ON_ERROR_STOP=1` and never against production:
```bash
psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f tests/security/rls_negative.sql
psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f tests/security/storage_negative.sql
node --test tests/security/supabase-client.test.mjs
```
These live SQL tests simulate authenticated database roles/JWT claims directly; they do **not** replace end-to-end Auth/HTTP tests.

## Authentication integration
- `frontend/src/lib/supabase.js` wraps GoTrue Auth v1 and PostgREST endpoints, refreshes expiring access tokens, stores a per-tab session in sessionStorage and passes the user bearer token. Not a privileged client.
- `frontend/src/auth/AuthProvider.jsx` restores/verifies the user session and implements sign-in/up/out and auth state.
- `frontend/src/auth/AccountWorkspace.jsx` provides sign-in, registration, create-shop onboarding and business profile editing, guarded by actual auth state. The existing root `/account` is still the coordinator-owned placeholder until integrated.
- Configure **only** `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in a RetailGrowthAI-specific Vite environment. Never place a secret/service-role key in frontend variables.
- Coordinator must integrate `<AuthProvider><AccountWorkspace /></AuthProvider>` into `frontend/src/App.jsx`. Changes to root app/router or dependency config remain coordinator-owned.

## Permissions and guardrails
- Authenticated users can create a shop for themselves. Trigger transactionally creates OWNER membership and initial business profile.
- OWNER can add/edit/remove existing EDITOR/VIEWER memberships. Clients cannot elevate or modify OWNER seats. No invite-by-email workflow yet.
- Active OWNER/EDITOR may update business profiles, campaign draft/day, brand kit and own-shop media. VIEWER is read-only.
- Cross-shop campaign/day/render/media relationships use composite `(shop_id,id)` foreign keys.
- Backend-managed render/usage/audit rows are client read-only; privileged Azure Functions must authenticate the real user and re-check active shop membership before service-role writes.
- Media object paths are prefixed `<shop UUID>/...` in a private bucket; no externally supplied URL is sufficient authorization.
- Identity roles are read from the database, never mutable JWT `user_metadata`.

## CI and coordinator handoff
- Current three GitHub Actions jobs verify Vite build/fixture test, Python fixture and synthetic FFmpeg. They **do not** run `tests/security/**`; green CI must not be presented as security CI coverage.
- Coordinator to add an isolated security CI job (disposable Supabase local/Auth/Storage database, migrations and SQL tests plus Node test) in coordinator-owned `.github/workflows/**`. Do not turn off failing tests.
- Browser-client Node unit tests `tests/security/supabase-client.test.mjs` remain unverified until executed through Node or CI. Production sign-in and profile editing over HTTPS also remain unverified until coordinator wires the route.
- Coordinator alone updates canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` after integration; this worker does not touch shared docs.
