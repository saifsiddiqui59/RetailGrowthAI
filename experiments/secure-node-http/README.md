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
