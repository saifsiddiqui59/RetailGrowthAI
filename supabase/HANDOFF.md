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


## 2026-10-22 — DEV migration and RLS readiness review (branch `feat/p1-dev-migration-readiness`)

### Read-only hosted DEV verification
- Current `main` starting point: `92889707a19f9a42238bced6d527963b677e0e74`; dedicated project `jeearzffnjbvghwjjjrf` is `ACTIVE_HEALTHY` (Tokyo, PostgreSQL 17).
- Remote migration history **still contains ONLY** `20261022085124`, `20261022085132`, `20261022085503`. The durable-planning, render-claim, draft-save, private-upload-registration and new media-integrity migrations are **pending**, in order. Do not assume source files are deployed.
- Remote security advisor returned **zero notices** for the presently deployed three-migration schema. Performance advisor returned **15 INFO-only unused-index notices**; expected in an unused DEV database, not a reason to remove planned foreign-key indexes.
- No migration was applied; no hosted Supabase data, policies, buckets, auth users or service keys were changed.

### Code hardening queued for review
- New `20261022180000_p1_dev_media_integrity.sql` strengthens browser Storage INSERT to canonical `<shop-id>/uploads/<uuid>.png|jpg|webp`, closes browser UPDATE/upsert/rename of Storage objects, prevents user deletion of registered blobs, and revokes browser deletion of `media_assets` registration rows. This removes the two-step bypass where a member first deletes metadata and then replaces previously registered content.
- Verified frontend contract is upload-only with `x-upsert: false` and server-bound registration; generated video files are backend-managed. The single shared private bucket intentionally retains its existing 50 MB ceiling to accommodate generated MP4 outputs.
- Expanded disposable Postgres tests in `tests/security/storage_negative.sql` and `tests/security/upload_registration_negative.sql` to exercise canonical paths, malicious browser MP4 upload, protected update grants/policies and metadata-delete bypass. Direct Storage deletion is not tested with SQL because Supabase requires the Storage API to synchronize object bytes.
- No incompatible HTTP/JSON interface was changed. Any future user media revocation/delete requires a separate audited server-side workflow.

### Approval-gated deployment order and checks
1. Obtain explicit coordinator/user approval, verify backup/recovery plan for **RetailGrowthAI DEV only**, and compare hosted migration history against committed files before applying.
2. Review and apply sequentially: `20261022100400` durable planning, `20261022101800` render claim, `20261022162000` draft save, `20261022173000` private upload registration, `20261022180000` media integrity. Stop on drift/errors; do not apply to other projects.
3. After authorized DEV rollout, run Supabase security/performance advisors, verify RLS and RPC EXECUTE/GRANT, and test a real user-authorized private upload/registration, cross-tenant rejection, registered overwrite/delete denial, and service-only generated MP4 handling.
4. Await isolated Azure Function and Storage queue deployment approval before claiming authenticated campaign/render E2E. Production remains unprovisioned.

Remaining known gaps: a 50 MB multi-purpose bucket allows unregistered objects up to its ceiling; abandoned upload cleanup and quotas require an approved service workflow. User-declared rights remain unverified until human/commercial review. This branch does not deploy or prove hosted browser functionality. Canonical `docs/**` updates are coordinator-owned and should be performed after PR integration.
