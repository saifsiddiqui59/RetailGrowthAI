# RetailGrowthAI Node HTTP A/B control (WineShopPOS style)

**Source-only: not deployed and not a replacement customer API.** Uses the same Node.js Azure Functions v4 registration style as WineShopPOS, but no WineShopPOS resources, secrets, customers or source files are modified.

This deliberately tiny standalone Functions app provides GET /api/p0-health-lite (200) and a synthetic protected GET /api/campaigns/{id} (401 without JWT; fails closed even with supplied JWT). No Supabase service role, token verification, shop-level access, invoice API, writes, or real private data. It cannot safely substitute for RetailGrowthAI's existing backend.

Offline: run npm install --no-audit --no-fund, npm test, npm run check with Node.js 22. The experimental package should remain much smaller than the current Python/FFmpeg/Pillow release. These offline checks do not prove improved Azure startup.

**Only if the existing host cannot be remedied** and a separately priced and approved DEV-only experiment is authorized, provision a small Node Azure Functions Flex Consumption app with 0 always-ready to test the same synthetic 401/404 patterns. Do not place it on the user's production origin, deploy over the current Python application, or rely on Linux legacy Consumption (retiring September 2028). Before routing real traffic, implement and test *all* JWT/RLS/tenant membership, subscription/quota, durable transactional writes, idempotency/CAS, downloads and private media parity. Keep Python queue/video workers as they are.
