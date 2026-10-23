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