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
