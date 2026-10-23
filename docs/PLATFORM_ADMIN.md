# RetailGrowthAI Platform Super Admin — single-login authorization

## What is implemented

- **One RetailGrowthAI Supabase Auth session**. A person can simultaneously have
  an ordinary shop OWNER/EDITOR/VIEWER membership and a separately verified
  global Platform Super Admin grant. No second sign-in, root password,
  account metadata flag, browser role switch or shared WineShopPOS identity.
- `/platform-admin` displays aggregated retailer/production usage and a
  paginated cross-retailer account directory through explicitly guarded RPCs.
- Platform root may manually set a paid plan and status for an existing shop
  after acknowledging an audited, reasoned quota period reset. This is not
  payment collection, auto-renewal or a new TRIAL.
- Shop RLS remains unchanged: platform-level RPCs require fresh membership
  verification for every invocation; the root's ordinary tenant API calls
  do **not** gain access to other shops.

## Production/DEV activation gates

1. Review `supabase/migrations/20261023181000_p1_platform_admin.sql`,
   require all 4 GitHub PR/main CI jobs, and make a separate approved
   **RetailGrowthAI DEV-only** migration application via verified migration
   history. Do not use WineShopPOS or a production database.
2. Identify the **existing, confirmed RetailGrowthAI login** to promote,
   using the Supabase Auth user UUID in the dedicated RetailGrowthAI project.
   There is **no seeded root user**; do not choose an email by guesswork or
   auto-promote the first account. Only authorized operators use the trusted
   Supabase SQL Editor (postgres), never frontend/client RPCs.
3. Verify the exact UUID and email in the trusted editor (read-only):

    select id, email, email_confirmed_at from auth.users where id = '<verified-user-uuid>'::uuid;

   With an approved identity, grant only that user:

    insert into retail_private.platform_admins (user_id, active)
    values ('<verified-user-uuid>'::uuid, true)
    on conflict (user_id) do update set active = true;

   This is an administrator-only operation, not a website signup flow.
4. Build/deploy only the approved existing RetailGrowthAI DEV Static Web App.
   Do not expose a `service_role` key, auth user list, or admin secrets
   in frontend environment variables. Normal account login is unchanged.
5. Exercise real DEV login tests below **without disclosing passwords/JWTs**.

## Live DEV login checklist (separate from automated mocks)

- Approved root: normal `/account` password login succeeds; Platform Control
  appears in the top-right account menu and sidebar; aggregate summary and
  retailer directory render; only explicitly approved changes are applied.
- Shop OWNER: login succeeds, `/subscription` accessible for own shop;
  `/platform-admin` denied, platform RPC calls return 42501/403.
- EDITOR and VIEWER: login succeeds, campaign permissions remain shop-scoped;
  global admin page and RPCs denied; VIEWER cannot use edit privileges.
- Invalid password: no session and zero platform RPCs after a denied login.
- Revoked root: set `active=false` in the trusted editor and verify the next
  platform API operation fails (without relying on client navigation state).
- Check audit in trusted database context, no raw customer passwords:

    select actor_id,shop_id,action,new_plan,new_status,happened_at
    from retail_private.platform_admin_audit order by happened_at desc limit 20;

## Privilege revocation

    update retail_private.platform_admins set active=false
    where user_id='<verified-user-uuid>'::uuid;

Revocation is checked on every RPC regardless of stale browser role UI.
Never grant `service_role` to the browser or alter existing tenant RLS.
Do not run hosted role changes using a mock/test email or hard-coded UUID.

## Test evidence boundaries

`tests/security/platform_admin_negative.sql` runs only in disposable local
Postgres and tests root grant, OWNER/VIEWER denial, authorization on reads
and writes, no ordinary RLS bypass, audit, and revocation.
`frontend/e2e/platform-admin.spec.mjs` exercises mock HTTP login for ROOT,
OWNER, EDITOR, VIEWER and invalid credentials. Neither proves a real hosted
admin has been promoted. The live owner/root login must be verified after
DEV migration and identity selection; never claim production root readiness
from source-only tests.

## 2026-10-23 — DEV activation update and safe login-first entry

- The project has only ONE public website and ONE Supabase Auth session. A guest visiting `/` sees a login page; a server-verified root logging in there goes to the protected provider monitoring dashboard, and an ordinary OWNER/EDITOR/VIEWER goes to the tenant dashboard. `/platform-admin` is an internal protected route, NOT a second site or login.
- The reviewed database migration has been applied to RetailGrowthAI DEV via the connected Supabase project. The provider assigned actual migration history version **20261023165300** to `p1_platform_admin`; the source filename and migration preflight were reconciled to that version to avoid replay. At inspection the hosted Auth project had **zero users** and **zero root grants**.
- A real root user cannot be safely provisioned as an anonymous/example.invalid test account. The owner should sign up using a controlled reachable email through the ordinary RetailGrowthAI signup form (or operator-managed Supabase Auth Admin `createUser` invitation), confirm ownership, and then have a trusted operator match the exact Auth UUID and apply the grant. Do not add users via SQL inserts to `auth.users`, embed privileged role in JWT `user_metadata`, use a static password, or expose service keys. A temporary test admin must still have a real controllable email and be revocable.
- The monitoring warning center shows conditions derived from true privileged RPC counts and explicit visibility gaps for payments, Azure latency/cost and social platform health. A blank or unverified source never implies zero failure or zero spend.
