# Workstream A — Supabase foundation and handoff

## Deployment boundary
**NOT deployed.** No dedicated RetailGrowthAI Supabase DEV/PROD projects currently exist. Migrations apply ONLY after creating separate RetailGrowthAI projects. Never reuse WineShopPOS, WineshopPOS_DEV or the voice/optical databases. Do not paste service-role keys into a browser or repository.

In a disposable *RetailGrowthAI-only* Supabase local stack, apply migrations (in lexical order) with the Supabase CLI, then run \`psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f tests/security/rls_negative.sql\`. The SQL test creates two synthetic Auth users, verifies own-shop access and asserts forbidden cross-shop access, updates, membership escalation and wrong-shop media. The transaction is rolled back to avoid leaving test users. **Do not run this SQL against a production database**. Use the project's CLI migration tooling when available.

## Authentication integration
- Zero dependency REST client: \`frontend/src/lib/supabase.js\` wraps documented GoTrue Auth v1 and PostgREST endpoints, refreshes expiring access tokens, and holds a per-tab session in \`sessionStorage\`.
- \`frontend/src/auth/AuthProvider.jsx\`: session restoration, server user validation, sign-in/up/out and auth hook. Sign-up may require email confirmation. No privileged credentials.
- \`frontend/src/auth/AccountWorkspace.jsx\`: sign-in, registration, create-shop onboarding and business profile editing, guarded by actual auth state. Existing root \`/account\` remains a coordinator-owned placeholder until integrated.
- Add \`VITE_SUPABASE_URL\` and \`VITE_SUPABASE_PUBLISHABLE_KEY\` to a **new RetailGrowthAI** frontend environment (publishable key only). The client refuses to start when unset. Never use a service role or secret key.
- Coordinator must replace the existing Account placeholder in \`frontend/src/App.jsx\` with \`<AuthProvider><AccountWorkspace /></AuthProvider>\` (and provide an account-specific loading/error UX), without altering A's internals. Guard other routes when APIs become live.

## Permissions
- A logged-in user can create a shop they own. Database trigger creates OWNER membership and business profile atomically.
- OWNER can view/add/edit/deactivate/remove EDITOR/VIEWER memberships. OWNER membership cannot be modified through browser grants. Do not allow client creation of OWNER memberships.
- Active OWNER/EDITOR may update business profile, campaign brief/day drafts, brand kit and own-shop media. VIEWER is read-only.
- Campaign/day/render IDs are protected by composite \`(shop_id,id)\` foreign keys, not only filter parameters.
- Backend-managed render/usage/audit rows are read-only to end users. Service-role use is server-side only; Azure Functions must authenticate the user and authorize membership *before* privileged writes.
- Private Storage bucket \`retailgrowth-media\` restricts paths to \`<shop UUID>/...\`; signed/public URLs are not stored in data tables.
- A shop slug is globally unique; a collision may return a 409. No invite-email workflow is implemented (membership management expects an existing Auth user UUID).
- All RLS policies are restrictive by positive membership checks; no JWT \`user_metadata\` authority.

## Tests and coordination gaps
- \`tests/security/rls_negative.sql\` is a real Postgres RLS test, not a mocked assertion. It requires a disposable Supabase database with Auth/Storage schema and privileges; it has **not** been executed against a connected project.
- \`tests/security/supabase-client.test.mjs\` validates browser-client request shapes and session expiry using mocked network. Run \`node --test tests/security/supabase-client.test.mjs\`.
- Existing GitHub Actions jobs do **not** include \`tests/security/**\`. Coordinator should add a Postgres/Supabase security CI job using an isolated disposable database with migrations, plus Node test execution, without touching A's files or weakening checks.
- Generated assets and all actual AI/render jobs remain workstreams B/C/D. Store license information at media ingest; human review gates on promotions remain mandatory.
