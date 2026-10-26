# RetailGrowthAI secure Node HTTP READ adapter (source-only, NOT DEPLOYED)

A lightweight WineShopPOS-style Node v4 HTTP facade candidate for replacing the unreliable Python **HTTP ingress only**, while the original RetailGrowthAI Python Queue/FFmpeg/video/poster worker remains unchanged.

**Gate:** No customer use, static-web-apps API wiring, sensitive keys, DB migrations, production route changes or deployment has been authorized by this source. The previous `experiments/wineshop-node-http-control` remains an entirely synthetic tenantless 200/401/404 control. Do NOT overwrite or route users to it.

## Security properties
- Trust **only** the current RetailGrowthAI Supabase project's asymmetric JWKS at pinned `https://<project>/auth/v1/.well-known/jwks.json`; verify ES256/RS256 signature, kid, exp, iat, issuer, audience, authenticated role and UUID sub. No HS256, `none`, custom key urls, SWA `x-ms-client-principal` trust, or unsigned fallback. An SWA proxy may handle Authorization specially; production JWT transport requires a separate reviewed secure channel and real E2E validation.
- Send only the verified user JWT plus public publishable key to Supabase PostgREST; existing shop membership/RLS must deny other tenants and inactive memberships. Never expose service role or private media path. No logging auth token.
- **Read-only** API candidate for `GET /api/campaigns/{uuid}` and `GET /api/render-jobs/{uuid}`; no POST/PATCH, quota reservations, outbox acceptance, poster, signed media or customers yet. No authenticated writes or deployment.
- All incoming identifiers canonical UUID, strict response shape and tenant cross-shop checks, bounded upstream timeout; fail closed. Outage 503 is not conflated with authenticated 401.

### Next
Complete all Part 1 APIs, rights/usage/outbox/CAS, private media signed downloads, transport and negative tenancy tests, then the **separate** guarded DEV SWA staging deployment and ROOT-authorized real end-to-end canary before touching `VITE_CAMPAIGN_API_BASE_URL`.

Run offline Node builtin tests under `tests/security/p0_secure_node_read_gateway.test.mjs` from standard CI. No new npm dependency is required by the test code.

## Additional source-only poster write RPC capability (NOT REGISTERED)

`src/poster-writes.mjs` now contains a separate **unregistered** adapter for `POST /api/campaigns/{id}/posters`, `POST /api/poster-drafts/{id}/renders` and `POST /api/poster-drafts/{id}/select`. The real Node Azure Functions `index.mjs` registers **only seven GET routes**; **do not advertise the POST routes as deployed or usable in production**.

For poster draft creation, it verifies cryptographically authenticated user, actual campaign + DRAFT day, OWNER/EDITOR membership, uploaded image ownership/lineage and strict text/color/template inputs, then delegates to the **existing user-JWT `create_poster_draft` RPC** which rechecks rights, licence, subscription and active membership in PostgreSQL. For render request it validates poster+OWNER/EDITOR and calls the **existing `request_poster_job` RPC**, which atomically reserves usage and writes job/outbox. For reviewed banner selection it uses the **existing `select_poster_banner` optimistic-CAS RPC** with a complete expected Instagram document. A lost RPC acknowledgment is terminal 503, never an automatic POST replay.

The adapter uses **no service-role key**, no Azure Queue SDK, no additional SQL migration, and no new quota ledger. Its Node negative unit tests cover foreign/inactive/VIEWER, invalid payloads, untrusted assets, stale CAS, quota/expiry SQLSTATE, DB/network ambiguity and forbidden POST routes. Still missing complete campaign creation, draft PATCH and 30-second Reel render submission; no secure write endpoint has been deployed and live Supabase data is untouched.

## 2026-10-26 — Source-only campaign planning and draft-edit mutation parity (NOT DEPLOYED)

`src/v1-contract.mjs` validates the existing Part 1 campaign brief and full campaign/day v1 contract: max seven days, valid ISO date/IANA timezone, language, authorized media asset references, consecutive dates and unique subjects, DRAFT-only review status, LinkedIn/Instagram fields and an exact 30-second continuous 9:16 storyboard. `src/campaign-day-writes.mjs` provides a separately injectable but **unregistered** gateway for `POST /api/campaigns` and `PATCH /api/campaigns/{id}/days/{dayId}`.

- Campaign creation requires externally verified user JWT, fresh active OWNER/EDITOR membership and private shop-owned assets, then inserts one PLANNING campaign via the **existing user-token RLS PostgREST table**, where the existing database INSERT trigger stores the durable planning outbox in the same transaction. It uses no Queue SDK, server-role, direct outbox INSERT or duplicated quota reservations.
- Draft PATCH rereads the current authorized campaign/day, checks the *complete* replacement campaign v1 document, source/media rights and OWNER/EDITOR, then calls the **existing `save_campaign_day` SQL CAS RPC** with the prior values. Only a true CAS acknowledgement yields 200, followed by a fresh authorized read of the saved day; false yields conflict 409. Unknown/ambiguous DB responses fail closed and are never automatically repeated.
- No API route was registered in Node `index.mjs`; the existing Free SWA preview, live Python Functions, QUEUE/FFmpeg, DEV Supabase schema, production frontend and WineShopPOS are unchanged. **Do not enable writes or change the retailer API origin** based on source-only unit tests.

**Still open for #249:** `POST /api/campaigns/{id}/renders` requires the original licensed media check, stable idempotency digest, quota + atomic outbox and safe concurrent job creation. The existing Python path currently uses worker-only admin queries; do **not** copy a worker service key into the Free SWA Node API. Complete a reviewed user-RLS SQL RPC/interface instead. Real Supabase JWT transport, CORS/browser isolation, cross-tenant and customer upload→campaign→poster→30s MP4 E2E acceptance are unverified.

## 2026-10-26 — Safe source-only Reel request (missing SQL RPC)

`src/reel-intent.mjs` implements an **unregistered and undeployed** candidate `POST /api/campaigns/{id}/renders` that verifies current-user Supabase JWT (by injected verified security boundary), shop writer role and media license, validates the 30-second source Reel, and issues only `p_campaign_id,p_day_id` to a future narrow `request_reel_render_job` PostgREST procedure. The required user-JWT SQL RPC is *currently absent* from DEV; Node neither receives service_role credentials nor writes directly to the `render_jobs` table or queue. SQL concurrency/idempotency, current Python digest compatibility and subscription/outbox rights remain coordinator-owned gating work. Errors fail closed; 503 responses after an uncertain Postgres reply are never automatically replayed. The operational/cost/security gate is [docs/part1/P0_249_REEL_INTENT_NODE_CLIENT.md](../../docs/part1/P0_249_REEL_INTENT_NODE_CLIENT.md). Existing Free SWA preview has only a **fake** tenantless handler; do not confuse it with this source adapter.
