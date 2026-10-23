# RetailGrowthAI subscriptions — Part 1 design and implementation boundary

Read-only inspiration: WineShopPOS v4 subscription demos, server-gated RequireAuth, shop selector, and app-only renewal messaging. Never copy its users, subscriptions, prices, credentials or Supabase project.

## RetailGrowthAI-specific plans (proposal; **not charged**)

| Plan | Trial and quotas | Enforcement readiness |
| --- | --- | --- |
| TRIAL | 7 days, 2 campaign plans, 2 renders | Proposed; not active |
| STARTER | 15 plans and 10 renders per billing month | Proposed; not active |
| GROWTH | 60 plans and 45 renders per billing month | Proposed; not active |
| BUSINESS | Configurable contract limits | Proposed; not active |

No Razorpay, checkout, publishing, self-service payment, or pricing claim is implemented. Plan prices must be calculated from measured token/video costs and explicitly agreed before being displayed as purchasable.

## Security-first implementation roadmap

- Persist server-owned entitlements keyed to shop_id, status, valid_from/to, metered periods and controlled plan identifiers in a reviewed **RetailGrowthAI-only** Supabase migration.
- RLS user access: OWNER reads current shop entitlement; user_metadata never authorizes a plan; anonymous sees no tenant plan data. Admin controls remain service-side.
- Atomic reserve/consume with idempotency on campaign job ID and render job ID. Enforce quotas server side before creating durable outbox records, never just in React.
- Plan expiry blocks new AI/render spending; account read-only, draft export and security-recovery flows remain accessible.
- Test trial expiry, revoked membership, unauthorized plan escalation, cross-shop records and concurrent quota races; add renewal notices without new messaging vendors.

## Already implemented / verified in this iteration

- Supabase verified sessions and backend RLS membership remain authoritative. Improved React AuthProvider rejects stale verification responses after logout or a later sign-in, inspired by WineShopPOS sequence guards.
- Privacy-safe Python operational events include randomized correlation, per-process pseudonymous tenant/job labels, mode, outcome, latency and Foundry token totals. No prompts, JWT, service keys or direct shop IDs.
- Event logger is source instrumentation only until actual Azure Application Insights ingestion is demonstrated.

**Do not present subscription enforcement as currently active.**

## DEV enforcement (2026-10-23)
- 7-day shop trial and fixed candidate per-period spend caps are now **enforced for new RetailGrowthAI DEV shops** by reviewed DB trigger; not a paid subscription system. Source [#102](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/102), live migration `20261023134701_p1_subscription_quota.sql`, with server-only plan/meter changes and OWNER RLS read access.
- TRIAL: 2 campaigns, 2 rendered MP4s; STARTER: 15/10; GROWTH: 60/45; BUSINESS: 200/150 candidate units. Only TRIAL is auto-granted; paid-tier identifiers cannot be self-selected and no plans can be purchased yet. Plan periods are server-owned and no renewal scheduler is implemented.
- Database trigger atomically reserves units **before new campaign/render INSERT**, locks the shop entitlement row to fence concurrent requests, uses unique job IDs, and rolls back on rejection. Browser owner can read plan and expiry but cannot alter allowance. HTTP returns sanitized 402 (`SUBSCRIPTION_REQUIRED`) or 429 (`QUOTA_EXCEEDED`).
- [DEV backend release #39965140549](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39965140549) succeeded; owner-only Account UI [#104](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/104) merged and site deployment is [#39965683074](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39965683074). Deployment #39965683074 is SUCCESS, existing Free SWA HTTPS route checks passed; owner-only plan status display live.
- **Do not advertise paid billing, prices, renewals or upgrade buttons.** Commercial plan activation requires reviewed operator procedure or future billing integration with separate approval. Never copy WineShopPOS accounts, payment config or entitlement rows.

## 2026-10-23 — Hosted trial quotas verified
- [DEV canary attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39958569041) SUCCESS: two test shops received seven-day trials and reserved one campaign plus one render quota. Real Foundry plan, tenant denial, saved draft, FFmpeg signed private 30-second H264 MP4 and cleanup all passed. Post-run zero temporary test users, shops and reservations. Pricing, checkout and renewal features remain future work.
