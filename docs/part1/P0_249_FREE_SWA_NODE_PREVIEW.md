# P0 #249: existing Free SWA isolated Node.js managed-API comparison

**Deployment status:** This plan is separate from the legacy Python Flex Functions app. A successful source/CI test is not an actual hosted API fix. Record any actual GitHub Actions run and status before updating the status.

## Verified decision

- The existing RetailGrowthAI Free Azure Static Web App is `retailgrowthai-dev-preview`, verified DEV RG `rg-retailgrowth-dev` and hostname `purple-dune-06b5da200.2.azurestaticapps.net`.
- Microsoft's official Azure Static Web Apps **Free** offering includes managed Azure Functions APIs and up to **three staging environments**. Named preview environments are selected by `deployment_environment` and have their **own preview URL**. The runtime supports `node:22`, HTTP only, and a maximum **45-second HTTP request**. Sources: [plans](https://learn.microsoft.com/en-us/azure/static-web-apps/plans), [named environments](https://learn.microsoft.com/en-us/azure/static-web-apps/named-environments), [configuration](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration), [API limitations](https://learn.microsoft.com/en-us/azure/static-web-apps/apis).
- Therefore an **isolated Node.js v4 HTTP gateway** (like WineShopPOS's Node Functions pattern) can be tested on the **existing Free SWA named preview** without touching the Python FFmpeg/queue workers, buying an always-ready replica, or provisioning a separate Function App.

## Scope of this initial safe test

`experiments/wineshop-node-http-control/` is deliberately **not a customer backend**. It exposes only `GET /api/p0-health-lite` (200), a *fake-id protected campaign GET* (401 without JWT, 503 for an unverified Bearer to fail closed) and `GET /api/p0-249-missing` (404). Responses include a synthetic `X-P0-Control: node-v4` marker, which confirms that Azure routed the request to the actual Node handler. A random unknown path without a registered handler may return a platform 404 without this marker.

It has no real user, JWT validation, Supabase RLS calls, service_role credentials, Stripe/payment keys, Queue permissions, publishing or other writes. The preview static HTML is a simple noindex test notice; neither the retailer SPA nor an actual customer session is included.

## Deployment safety

1. Only the **reviewed branch** and full **4/4 GitHub PR CI** (Python, Node security, media, Supabase RLS) can be merged.
2. A workflow on main `.github/workflows/p0-dev-free-swa-node-preview-once.yml` is a **single audit-gated release**. It requires the exact approved release commit message (no manual bypass), protected DEV GitHub OIDC, exact matching tagged RG, existing **Free** SKU and known hostname, preview capacity (no more than three), and no access to WineShopPOS.
3. The upload uses `deployment_environment: p0249node`, `app_location: experiments/wineshop-node-http-control/site`, `api_location: experiments/wineshop-node-http-control`, and `skip_app_build: true`. **Never** set `deployment_environment` to production or omit it.
4. The upload only publishes the small static placeholder and Node HTTP control to **p0249node**. A backend deployment to the production SPA or the existing Python Functions app is prohibited.
5. Post-deploy probes must verify the **actual Azure-returned** HTTPS hostname is the exact p0249node named-preview hostname, then require 200 / 401 / 404 / 200 + `X-P0-Control` marker within 15 seconds. The owner gets an actual run ID and measured results. No tokens, response bodies, signed links, customer IDs, or settings values may be logged.
6. To roll back, remove the **p0249node staging environment** only after inspecting its current ownership, through the Static Web App **Environments** view or a separately reviewed exact-scope cleanup. Existing production Free SWA and Python workers remain unaltered.
7. Free tier means **no extra standalone Functions plan purchase for this test**. Still subject to Free managed-API and staging quotas; do not claim unbounded usage or a commercial SLA.

## Decision from actual tests

- If Node managed API synthetic routes reliably return normal results while Python Flex had 4/6 post-TLS no-byte client timeouts, this validates a plausible alternative **HTTP execution surface**, **not the exact Azure root cause**. Run repeated non-customer route checks and verify instance/storage/queue readiness independently.
- If the Node managed API also intermittently stalls, investigate shared Azure ingress/platform or test network before rewriting any Python endpoints.
- If the preview succeeds, engineer a **separate tenant-safe gateway** which cryptographically validates Supabase JWT, verifies shop membership/RLS, honors private asset rights and subscription caps, persists durable planning/render outbox writes with idempotency/CAS, and implements fully backward-compatible Part 1 campaign/poster/video API. Do not send real user traffic to the synthetic control.
- A full signed-in ROOT-approved, negative cross-tenant, create→poster→video→download browser acceptance is required before changing `VITE_CAMPAIGN_API_BASE_URL`. Continue using existing Python queue + FFmpeg workers; don't move expensive rendering into the 45-second managed API.

**Issue #249 remains P0 OPEN** until a real secure, reliable HTTP interface and E2E are demonstrated.

## 2026-10-26 — Hosted synthetic Free Node managed API: verified acceptance

- Existing RetailGrowthAI DEV **Free** SWA named `p0249node` successfully deployed managed **Node.js 22** (source on main at `3a7aab81`); Azure run [#40295844516](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40295844516) returned **SUCCESS**, protected source/DEV identity/FREE plan checks passed, and the live `X-P0-Control: node-v4` application marker was present on every observed response.
- Actual no-JWT synthetic API measurements, in tested order: `GET /api/p0-health-lite` **200 / 0.838360 seconds**; fake `GET /api/campaigns/{UUID}` **401 / 0.704971 seconds**; deliberate `GET /api/p0-249-missing` **404 / 1.880591 seconds**; repeat health **200 / 0.655087 seconds**. The synthetic handler discards managed SWA/proxy Authorization values; it intentionally never accesses user data, cryptographically verifies a JWT, or performs a write.
- This is **one** hosted comparison, not a cold-start reliability benchmark or a secure retailer API. The original Python Flex public HTTP host still experienced 4/6 12-second post-TLS no-first-byte client timeouts in [#40291064533](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40291064533) and earlier independent true HTTP gateway 503s after ~61s. Node managed API has no full Auth/RLS/outbox/media parity or real signed-in browser acceptance, so #249 remains OPEN.
- Prior diagnostic [#40295092212](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40295092212) had health 200/0.712s and fake campaign **application-authored 503/0.687s**, both with Node marker; the **synthetic** Authorization handling issue was corrected without touching WineShopPOS or customer API.
- **Next engineering gate:** separate, isolated secure Node HTTP facade that validates existing Supabase ES256/RS256 JWT and issuer/audience/expiry, performs exact user+shop RLS membership and rights checks, preserves quota and transactional outbox/CAS writes and short-lived private media, and maintains unchanged current Python Queue+FFmpeg worker. Only after full backward-compatible route, negative cross-tenant, write idempotency and real signed-in E2E may the production SPA `VITE_CAMPAIGN_API_BASE_URL` be changed. No paid always-ready or new plan necessary for the initial proof.
