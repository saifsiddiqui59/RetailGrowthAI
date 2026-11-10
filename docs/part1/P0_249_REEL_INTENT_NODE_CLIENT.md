# Issue #249 — Low-cost Reel intent adapter checkpoint (source only)

Date: 2026-10-26. **This adapter is neither deployed nor registered as a public Node Azure Function. No Supabase migration is deployed.**

## What the owned branch adds

`experiments/secure-node-http/src/reel-intent.mjs` builds a strict, caller-token-bound source-only candidate for `POST /api/campaigns/{id}/renders`. It reuses the existing Supabase ES256/RS256 verifier, user JWT, active OWNER/EDITOR check, campaign/day association, 30-second storyboard validation, and licensed tenant-owned private media checks. It sends **only** `p_campaign_id` and `p_day_id` to the proposed `public.request_reel_render_job` RPC; it never accepts caller-provided shop IDs, service keys, object storage keys, pricing, or idempotency digests. The target RPC does not yet exist in the real DEV schema; until separately reviewed/applied, this route must remain UNREGISTERED and in any case fails closed.

The database remains the only authority to validate all rights again, compute a digest matching the **original Python** algorithm or safely reconcile old jobs, reserve a single subscription unit, insert the Reel job exactly once and let the **existing** BEFORE INSERT subscription trigger and AFTER INSERT durable outbox trigger execute in the same transaction. The Node app must never receive the Python AdminStore's service-role token or directly GRANT the `authenticated` role INSERT on `render_jobs`. Do not create a second ledger or manually enqueue an Azure Queue message.

## Cost and security gates

1. **Free** existing Static Web App managed Node HTTP preview, with original Python Queue/FFmpeg workers; no dedicated paid Node Function App, always-ready replicas, GPU, paid external trend service, or new SQL database.
2. **No blind mutation retries:** a lost SQL response returns HTTP 503. If the database actually committed a job, only the database's atomically deduplicating RPC can return it on an intentional later new client request. This branch adds no auto-retry.
3. Node maps real database SQLSTATE RG001 to HTTP 402 and RG002 to 429, and validates exact `job_id/status` response before reporting a job. A missing or unauthorized RPC returns a denied/503 response, not a fake success or a second job.
4. Offline negative tests cover JWT rejection, forbidden methods/fields, VIEWER/revoked/foreign members, invalid Reel, unlicensed/mis-scoped sources/music, missing RPC, malicious procedure response, quota errors, and no retry on a possibly committed SQL write.
5. **Coordinator-owned next migration:** follow `docs/part1/P0_249_RENDER_INTENT_RPC_SECURITY_PLAN.md`; use a generated new migration version and execute *only* against a disposable database first, with migration history, SQL privilege advisors, two-concurrent-client idempotency tests, real Python-created job digest reconciliation, and exact job/outbox/reservation count assertions. No production or existing DEV database mutation from this PR.
6. After real safe SQL migration acceptance, register the Node route *only* on an isolated DEV named preview and validate the managed SWA JWT transport (not native principal trust). Then test ROOT-approved signed-in shop, foreign shop, VIEWER and expired-JWT denials, real upload→poster→30-second Reel→signed download and cleanup before ever switching the real frontend API origin.

**Not complete:** source-only adapter + tests is a portion of the remaining #249 work. Live Python Flex pre-handler timeouts/503 still exist, and browser-customer API traffic must not be routed to this experimental Node adapter.
