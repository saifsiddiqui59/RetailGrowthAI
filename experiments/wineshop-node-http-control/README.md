# RetailGrowthAI Node HTTP A/B control (WineShopPOS style)

**Source-only: not deployed and not a replacement customer API.** Uses the same Node.js Azure Functions v4 registration style as WineShopPOS, but no WineShopPOS resources, secrets, customers or source files are modified.

This deliberately tiny standalone Functions app provides GET /api/p0-health-lite (200) and a synthetic protected GET /api/campaigns/{id} (401 without JWT; fails closed even with supplied JWT). No Supabase service role, token verification, shop-level access, invoice API, writes, or real private data. It cannot safely substitute for RetailGrowthAI's existing backend.

Offline: run npm install --no-audit --no-fund, npm test, npm run check with Node.js 22. The experimental package should remain much smaller than the current Python/FFmpeg/Pillow release. These offline checks do not prove improved Azure startup.

**Only if the existing host cannot be remedied** and a separately priced and approved DEV-only experiment is authorized, provision a small Node Azure Functions Flex Consumption app with 0 always-ready to test the same synthetic 401/404 patterns. Do not place it on the user's production origin, deploy over the current Python application, or rely on Linux legacy Consumption (retiring September 2028). Before routing real traffic, implement and test *all* JWT/RLS/tenant membership, subscription/quota, durable transactional writes, idempotency/CAS, downloads and private media parity. Keep Python queue/video workers as they are.

## 2026-10-26 — First hosted synthetic route finding and fail-closed correction
- Azure Free SWA managed Node API **deployed** (run #40294163365) to named preview `p0249node.eastasia.2.azurestaticapps.net`; this is not a customer backend.
- First read-only acceptance [#40295092212](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40295092212): Node `GET /api/p0-health-lite` HTTP **200 in 0.712s** with `X-P0-Control`; synthetic campaign read HTTP **503 in 0.687s** with the **same marker**. This is a Node-handler response, **not** an Azure pre-handler gateway 503. The previous synthetic implementation intentionally returned 503 when it saw an authorization value beginning with Bearer; the source of that value is not yet proven.
- Changed the **synthetic control only** so **all fake campaign reads return 401**, with or without incoming headers. The control no longer consumes an Authorization header. Real JWT/RLS, membership and write APIs remain unimplemented and no real customer data flows through Node. The adjusted named preview requires independent hosted retest; do not report full acceptance before its actual evidence.
