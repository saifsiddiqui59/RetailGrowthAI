# Part 3 — Internal development and activation gates (2026-10-23)

## Branch ownership and internal PRs
- Independent integration: `feat/part3-integration` → **final coordinator PR to main only after tests**.
- Provider / T2V / I2V / prompt: `feat/p3-wan-provider`, PR #109, owns `ai-agents/src/ai_agents/premium_video.py` and provider tests.
- Durable jobs + credit ledger: `feat/p3-premium-jobs`, PR #113, owns `azure-functions/campaign-api/premium_video_jobs.py`, NEW un-applied 20261023180000 SQL migration and tests.
- Premium UI: `feat/p3-premium-ui`, PR #115, owns new `frontend/src/features/premium-video/**` and mocked Node tests.
- Two-job isolated PR workflow and existing four-job repository CI must pass all internal PRs; do not merge failing code. Final integration adds files without touching Part 2 OAuth or Part 1 production deployment.

## Current implemented / staged boundaries
- **Default free FFmpeg**: existing `instagram_reel_30s` API and worker remain unchanged.
- Alibaba WAN 2.7 opt-in Python adapter: async submit/poll and bounded prompt, strict workspace endpoint and signed tenant-private source URL format, per-job maximum USD budget, default off. It does NOT send any vendor calls without explicit on/off flag, valid API key, workspace and nonzero cap.
- Source-only premium table includes job identity, tenant, provider task ID, safe statuses, encrypted/private separation and idempotency key; source migration extends **existing** `shop_subscriptions` and `shop_usage_reservations` by operation/premium seconds. Premium allowance defaults 0, so no trial/customer receives premium access. Row lock + shared ledger prevents concurrent over-reservation. These are not additional card/billing services.
- Authenticated job controller scaffold requires reviewed DRAFT and OWNER/EDITOR role, user JWT/RLS asset check + service-side media rights, deterministic request idempotency and safe job response. Mock worker records UNKNOWN on uncertain submission, never sends an unbounded duplicate POST.
- Frontend component defaults to FFmpeg; selectable Wan state requires all THREE server entitlement, enabled feature, and ready authenticated endpoint. Component currently intentionally not mounted in shared CampaignDashboard to preserve Part 1 behavior.

## Incomplete before provider activation
1. Review source schema and **authorize/apply the new migration separately** to DEV (never replay Part 1's 11 versions); require disposable negative SQL and real concurrency/tenant tests.
2. Wire a new **transactional premium outbox** and queue trigger into existing Azure Functions/Storage config; use UUID-only messages, CAS leases and poison/recovery behavior. Do not overload Part 1's free render queue.
3. Ensure credentials, workspace region, cost limits, customer consent and provider terms reviewed and approved; add a per-tenant monthly spend ceiling and provider call concurrency limit. Do not enable the feature just by deploying source.
4. Implement server-side encrypted provider task persistence/lease token fencing, bounded poller, cancel semantics (local cancellation does not imply refunded provider usage) and billing reconciliation on UNKNOWN.
5. Implement safe provider output importer with allowlisted redirect destinations, time/byte limits and MP4 ffprobe; upload to existing `retailgrowth-media` bucket under validated tenant-scoped private path with signed RetailGrowthAI-only download URL. Current poller intentionally **does not** pass through vendor result URL or mark completion until import.
6. Wire explicit authenticated premium API routes/status, user-reviewed brand claims and frontend selection; submit API must reject missing approved credit quote, expired JWT, foreign/VIEWER, unsupported images, unreviewed claims, expired subscription.
7. Run full offline pytest/Node/SQL/FFmpeg + hosted DEV canary with approved isolated test identity/provider spending; measure real $/clip and retry/failed spend; then decide production activation. **No billable tests without specific owner approval.**
8. No social publishing side effects (Part 2 owns OAuth/schedulers), no changes to WineShopPOS or GenAI Galaxy, no duplicate payment system.

## Current operational default
`RETAIL_PREMIUM_VIDEO_ENABLED=false`; `RETAIL_WAN_APPROVED_PER_JOB_USD=0`; no model key, paid-provider request, SaaS bill or new resource. Do not deploy the unreviewed Part 3 migration or mount and expose an enabled premium control.
