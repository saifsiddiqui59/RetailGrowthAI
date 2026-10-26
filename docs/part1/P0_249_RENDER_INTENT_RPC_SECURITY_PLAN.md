# P0 #249 — Remaining Reel request RPC: verified DEV database permissions and safe contract

Verified against **RetailGrowthAI DEV only**, Supabase project `jeearzffnjbvghwjjjrf`, using read-only catalog SQL on 2026-10-26. No table rows, credentials or personal content were queried or changed.

## What the live database proves

- `has_table_privilege('authenticated','public.render_jobs','INSERT') = false`; `SELECT = true`; render_jobs RLS is enabled.
- Current `render_jobs` published policy covers **SELECT** for members who have active `OWNER/EDITOR/VIEWER` membership; there is **no general authenticated INSERT policy**. This is intentional safety isolation. Do **not** GRANT authenticated INSERT broadly just to make Node work.
- Existing `render_jobs` triggers:
  - `subscription_reserve_render` — BEFORE INSERT, `retail_private.reserve_subscription_unit()`
  - `render_job_outbox` — AFTER INSERT, `retail_private.enqueue_new_job()`
- Existing `campaigns` triggers `subscription_reserve_campaign` and `campaign_job_outbox` work analogously.
- No user-executable `request_reel_render_job` or similar render-creation RPC exists. `public.claim_render_job`, `complete_render_claim`, `fail_render_claim` and worker outbox RPCs are **not executable** by authenticated users. `public.request_poster_job(p_poster_id uuid)` is an **authenticated-executable SECURITY DEFINER** function for the **separate poster workflow**, not a Reel renderer.
- The current Python `RenderAPI.create` performs business-level rights checks then relies on worker-only `AdminStore.valid_media/find_render_job/insert_render_job` and their privileged credentials. It hashes `[user_id,campaign_id,day_id,reel]` using sorted-key, compact Python JSON + SHA-256 for stable deduplication, then inserts a render job. A new independently computed Node/SQL hash must **not** silently diverge and double-charge.

## Narrowest safe missing contract

Create a reviewed **one-function, caller-authorized render-intent RPC** instead of giving the Free SWA HTTP layer service keys or direct `render_jobs` INSERT:

- Inputs: only canonical `campaign_id` and `day_id`. Do not accept `shop_id`, `user_id`, object paths, price/usage values or a trusted client-supplied idempotency digest.
- Resolve caller through `auth.uid()`, prove non-anonymous authenticated JWT, find the DRAFT campaign and its matching DRAFT/non-REJECTED day, verify current active OWNER/EDITOR in the campaign's shop **inside the transaction**; do not rely only on browser claims.
- Read the stored immutable-for-request Reel storyboard and music ID; validate the 30-second, 9:16 v1 contract and every actual media source/music ownership and **reviewed license evidence** inside the transaction. No user-supplied URLs.
- Reuse or version-reconcile **exact existing Python idempotency key format** before writes, including records created before any future Node deployment. Lock/unique-key strategy must handle two identical simultaneous requests and a lost HTTP acknowledgement without extra usage reservations.
- Insert exactly one `render_jobs` row via strictly scoped privileged operation only after validation; the already-existing BEFORE/AFTER triggers must provide **one** quota reservation and **one** durable `job_outbox` entry, in the **same transaction**. Never enqueue directly from the HTTP handler.
- Return only `job_id` and `status`, with an equivalent 202 (QUEUED/RUNNING) or 200 (already completed) mapping. Fail before insert on inactive subscription, missing rights, cross-shop ID, insufficient quota, outbox failure or invalid media.
- Keep `retail_private` worker functions and service-role secrets inaccessible to anonymous/authenticated users. If a privileged SQL function is required, treat it as a high-risk **SECURITY DEFINER** surface: fix its search_path, schema-qualify ALL objects, explicit `auth.uid()`/role/tenant/rights assertions, revoke EXECUTE from PUBLIC/anon and grant only the reviewed authenticated entrypoint. Supabase security guidance warns that SECURITY DEFINER bypasses RLS; verify its function owner and restrict by code/tests, not only by RLS.

## Mandatory gates before deploying a migration

1. Use an actual `supabase migration new` generated version in a *dedicated coordinator-owned migration branch*, following latest source-history order; do not manually invent a timestamp or replace historic migration versions. Follow the team's canonical preflight/approval process.
2. Apply source migration only to a disposable local database initially and run negative transaction tests for foreign shop, VIEWER, revoked user, missing license, invalid storyboard, subscription expired and quota exhausted.
3. Stress two concurrent same-storyboard render requests and simulated lost HTTP ACK. Assert **one** render job, **one** outbox row, **one** reservation; then change approved storyboard and verify a new distinct logical job as expected. Compare idempotency with Python-created historical jobs and all public error codes.
4. Run Supabase security advisors, pg_catalog privilege/policy checks and isolate the exact real DEV project + migrations history. Deployment to the existing hosted DEV database is a separately audited source-versioned schema gate, NOT part of this documentation work.
5. Only then implement/register the final Node `POST /api/campaigns/{id}/renders` route using the verified **current user JWT** and reviewed RPC; no worker key or direct PostgreSQL table INSERT.
6. Verify actual hosted signed-in ROOT/EDITOR/VIEWER and foreign-shop browser E2E with campaign/day, licensed image, poster, real queued 30-second H264/AAC MP4, private signed download, retries, and exact cleanup. Keep current Python queue/timer/FFmpeg workers and the live frontend origin untouched until the full switch is proven.

## Current execution state

- Source-only Node adapter PRs [#338](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/338), [#341](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/341), [#345](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/345) delivered authenticated GET parity, private downloads, poster DB RPC writes, campaign planning and draft day CAS source. These Node writes are **unregistered/not deployed**.
- Real Free SWA synthetic Node preview #40295844516 tested 200/401/404/200 in ~0.65–1.88s. This is not a secure retailer endpoint or proof of repeated reliability over many days.
- **Azure issue #249 remains OPEN:** original Python Flex had 4/6 read-only post-TLS client timeouts on #40291064533, prior actual gateway 503s. No root cause confirmed, no new plan/always-ready spend, no support case filed at owner's direction, and no PROD/WineShopPOS changes.

## 2026-10-26 — Verified code and next integration gate
- Reviewed source-only SQL: `experiments/secure-node-http/sql/request_reel_render_job.proposal.sql`. Privileged implementation is hidden in `retail_private`; public `request_reel_render_job` is SECURITY INVOKER with only two UUID inputs, and anon/PUBLIC EXECUTE explicitly revoked. Python-compatible sorted compact ensure_ascii=True Unicode digest verified against existing Python-created job. License checks reject NULL explicitly (`IN (...) IS NOT TRUE`) to avoid a SQL three-valued logic bypass.
- Test `tests/security/poster_reel_intent_negative.sql` is auto-run by existing `poster*.sql` disposable CI and wrapped in BEGIN/ROLLBACK. [Run #40321452358](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40321452358) 4/4 PASS, including actual SQL function execution and exact job/reservation/outbox counters. No hosted migration. After coordinator security review, generate a versioned migration, stage to existing RetailGrowthAI DEV only, and re-verify grants/advisors; separately verify concurrent retry/quota exhaustion and authenticated end-to-end on isolated Free SWA staging. Keep #249 OPEN.
