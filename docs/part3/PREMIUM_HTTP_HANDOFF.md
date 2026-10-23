# Part 3: Additive, disabled premium HTTP boundary (source only)

Branch: `feat/p3-premium-http-gate` targeting `feat/part3-integration` (self-merged by Part3 Lead after all tests).

## New source contract
`azure-functions/campaign-api/premium_http.py` provides `PremiumHTTPBoundary` with a verified user JWT at every request:
- `POST /campaigns/{campaign_id}/premium-videos`: forwards a strictly canonical campaign ID and payload to the existing premium coordinator; does **not** publish any Azure queue payload or charge a provider.
- `GET /premium-video-jobs/{job_id}`: returns only coordinator-safe status without provider task IDs or signed output URLs.
- `GET /premium-video-jobs/{job_id}/download`: only after RLS-scoped job fetch, CURRENT shop membership, SUCCEEDED status, exact output asset ID/shop/bucket/MIME, immutable `{shop_id}/renders/{job_id}/{lease_uuid}.mp4` receipt and the existing user-JWT `TenantStore.sign_download` 60-second private Storage signer.

The entire boundary has `enabled=False` by default; even a verified user cannot access it without the separately approved backend gate. Requests are never enabled from request parameters or browser flags. Unauthorized/foreign/expired/stale/wrong-status requests return restricted error codes, with no raw provider/storage errors.

## Explicit limitations
This is NOT mounted into the live `function_app.py` or `HTTPAPI`; no Azure API route exists until Coordinator-approved additive wiring. `PremiumVideoCoordinator` currently depends on unimplemented real P3 database reservation/claim RPCs, and staged SQL has NOT been applied to DEV. Neither the existing Part1 HTTP contract nor the standard FFmpeg render/upload/download flow changes.

Before integration in Azure:
- Finish exact new premium SQL schema, existing-ledger credits, atomic idempotency and tenant denial SQL tests; apply hosted migration ONLY after explicit approval.
- Implement backend-only real premium repository and HTTP dependencies with bounded response/timeouts and RLS JWT validation.
- Register new Azure Function routes only under locked premium backend activation; wire UUID-only transactional outbox + premium queue/recovery/poller/import and signed private output.
- Verify real user auth, foreign tenant denial, positive owner entitlement and output delivery in DEV. Approve vendor spend separately.

Tests: `tests/api/test_premium_http.py` validates disabled-by-default auth, create/status routing, read-only private tenant access, signed download shape, wrong status, forged object path and foreign/mismatched media denials. Existing four GitHub CI jobs cover this source-only test; 2/2 dedicated Part3 tests also required.

No paid API calls, cloud deployment, schema modification, charges or cross-project files.
