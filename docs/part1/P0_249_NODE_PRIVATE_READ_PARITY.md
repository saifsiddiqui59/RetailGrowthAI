# Issue #249 — Secure Node HTTP private-read parity checkpoint

**Status: SOURCE ONLY; not deployed to any Azure Static Web Apps API.** The `p0249node` named Free SWA preview is still the separate tenantless synthetic 200/401/404 control. The live retailer frontend still uses the existing Python Flex API; Python Storage Queue, timer and FFmpeg render workers remain authoritative.

## Completed source-only GET parity

The isolated `experiments/secure-node-http` adapter (requiring a cryptographically verified Supabase user JWT and active shop membership checked under the same user's RLS token) now registers:

| Existing Part 1 v1 path | Security/parity expectation |
| --- | --- |
| `GET /api/campaigns/{id}` | RLS-active shop campaign with validated days |
| `GET /api/render-jobs/{id}` | RLS-active render status, no output path |
| `GET /api/render-jobs/{id}/download` | Only SUCCEEDED private MP4; user-RLS Storage 60-second signed URL |
| `GET /api/poster-drafts/{id}` | Existing Python v1 `poster_id/status/campaign/day/template/colors/assets` response fields |
| `GET /api/campaigns/{id}/days/{dayId}/posters` | Exact authorized campaign/day/shop lineage, newest first, at most 21 poster revisions, paired private job status |
| `GET /api/poster-jobs/{id}` | RLS-active poster render status and original poster ID |
| `GET /api/poster-jobs/{id}/download` | Only SUCCEEDED private PNG from exactly `<shop>/posters/<posterId>/` with 60-second user-RLS signature |

Privacy gates: **no service-role**, no trust in client-supplied shop ID, no real JWT values logged, no cross-tenant data, no raw private object path in public responses, no external redirect/signed link accepted, no write to campaign/job/usage/outbox through GET. The Storage sign operation is an ephemeral RLS-user-token POST to Supabase Storage after full shop+asset authorization; it is NOT a user-triggered campaign/queue mutation.

Tests include poster GET response shape, foreign/inactive membership, mis-scoped or duplicate jobs, campaign-day mismatch, wrong MIME, nonready jobs, cross-shop/traversal storage paths, invalid signer response/origin, GET-only and no-token denial. Existing asymmetric ES256/RS256 JWKS and Node crypto negative tests remain enabled. Pass/fail is determined by actual GitHub CI, **not** by the existence of tests.

## Still OPEN

1. The current Flex Python HTTP gateway's pre-handler stalls/503s (#249) are not resolved by source-only code. The hosted Free SWA `p0249node` synthetic control has proven 4 short GETs only, not signed-in JWT/RLS reliability.
2. **Writes:** Build and validate full customer v1 HTTP `POST /campaigns`, campaign-day `PATCH`, Reel `POST /renders`, poster draft creation/render/selection. Preserve the current Python schema's RLS, subscription/usage, existing transactional job-outbox triggers, idempotency, media rights, optimistic CAS and safe retries. Do not invent a new quota ledger or enqueue synchronously after lost acknowledgement.
3. **Transport:** The experimental Node handler expects `x-rgai-supabase-jwt` because managed SWA may rewrite Authorization; token is independently signature-verified. This header/CORS/browser integration is **not** accepted and is not live. Review origin, CORS, CSRF/exfiltration, session expiry and operation limits before using it with a real session.
4. Deploy the **secure** API only to a separately reviewed isolated DEV named preview, with noncustomer negative paths first; then a fully reviewed signed-in cross-shop/VIEWER, media, campaign, poster and MP4 E2E including cleanup. Only then change the production SPA `VITE_CAMPAIGN_API_BASE_URL`.
5. No Azure paid service, always-ready, new Function App, Production or WineShopPOS modification is required or authorized by this PR.

**Outcome cannot be called complete** until the post-PR and post-merge CI passes and hosted tenant-safe end-to-end is demonstrated. Keep issue #249 open.
