# Feature #5 / Part 3 — Live DEV ledger reconciliation proposal

**2026-10-26 read-only verification.** Status: **proposed for RetailGrowthAI coordinator, not applied**. Feature #5 branch: `feat/feature5-premium-ai-motion`; draft PR #323. Related unmerged Part 3 draft PR #125 and Feature #4 draft PR #322.

## Source of truth: actual DEV database (read-only query)

Project: dedicated RetailGrowthAI DEV Supabase `jeearzffnjbvghwjjjrf`, not WineShopPOS. Checked `information_schema.columns` and PostgreSQL `pg_constraint` via read-only SQL. **No writes occurred.**

| Existing object | Observed DEV status | Needed for optional Hunyuan |
|---|---|---|
| `public.shop_subscriptions` | Columns: `shop_id,plan_code,status,valid_from,valid_until,period_start,period_end,created_at`. No premium budget/seconds. | Add optional, default-zero premium allowance and hard per-period cost ceiling using existing subscription row |
| `public.shop_usage_reservations` | `shop_id,operation,job_id,period_start,reserved_at`; `operation` CHECK allows **only** `campaign` and `render`; no `units` column. | Add `premium_video` operation and monotonic reserved units within existing ledger, preserve old operations |
| `public.premium_video_jobs` | **Not present**. | Coordinator reviews Part 3's proposed table and evolves **that same table** for Wan and Hunyuan, not separate competing jobs |
| `public.job_outbox` | Existing kind check **only** `planning` or `render`; states `PENDING/CLAIMED/SENT`. | Add `premium_video` kind with same durable outbox and delivery/poison/lease rules, not best-effort direct Queue publish |
| `public.render_jobs` | Existing free FFmpeg rendering job and quota. | Compose after Feature5 clip human review; do not duplicate premium credit reservation when composing an existing premium motion asset |

The Part 3 **staged but unmerged** SQL `azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql` permits only Wan model IDs and `720P/1080P`. Its proposed `reserve_premium_video` trigger prices only those resolutions as `seconds × 0.10/0.15` USD. **It is incompatible with 5s, 480p Hunyuan and GPU wall-clock billing. Do not execute it verbatim then blindly insert Hunyuan jobs.**

## Coordinator-owned staged migration design (no migration files or SQL executed here)

1. Build on existing Part 3 provider-neutral `premium_video_jobs`; add provider/model profile for `hunyuanvideo-1.5-480p`, `480p`, 5s profile and optional `image` input. Existing Wan behavior and all old reservations remain valid. Add source `media_assets` shop+asset composite FK and campaign/day same-tenant join checks before spend.
2. Preserve one **existing** `shop_subscriptions` row lock and `shop_usage_reservations` table for *all* premium jobs. Add `units` and a premium operation to existing usage ledger; default premium seconds/budget to **zero** for all existing shops. Never auto-upgrade TRIAL plans or modify their subscriptions.
3. Price Hunyuan from **reviewed server-side tariff/workload profile**, with the operator's selected region, GPU+vCPU+RAM retail rate, max billable wall time and ancillary allowance; compute `reserved_usd` **inside an atomic service-role SQL path**, never accept client-submitted USD or blindly apply Wan's `per output video second` price. Feature5 `MotionSpendGuard` checks the same maximum and that the existing reservation covers it.
4. Durable `job_outbox.kind='premium_video'` triggered in the same transaction as reservation. Queue payload is canonical UUID only; worker atomically claims a bounded lease token; all state changes and storage receipts must fence `shop_id+job_id+attempt_token`. Handle ambiguous GPU/DB/storage outcomes as `UNKNOWN` without automatic charged replay or refunds.
5. After private `retailgrowth-media` upload and exact receipt verified, mark machine status `SUCCEEDED` but `quality_review_required=True`; disallow Feature4 and publishing until an independently stored authenticated reviewer grants `VisualReview` with exact immutable clip SHA256 and all commercial/licensing/garment checks. Commit output `media_assets` under correct shop RLS; never issue vendor or private source URLs to public API.
6. Let Feature4 consume an approved, privately staged `source_feature=feature5` video via proposed `creative_reel_v1` server manifest. Apply the normal separately requested final-composition render quota **only if the product contract requires it**, never a second *premium model inference* reservation.
7. Keep per-provider feature flags OFF until coordinator migration, RLS, signed-in E2E, per-shop caps, budget/region eligibility, source-license and GPU/legal acceptance pass. Have one vetted DEV release, original 20 migration history intact. Do not touch WineShopPOS or PROD.

## Minimum negative SQL/E2E tests (coordinator to execute)

- Anonymous, unapproved VIEWER and other shop cannot create/fetch source, reserve, claim, view output, or approve final clip.
- Unapproved campaign day, mismatched media tenant, invalid commercial rights, wrong plan, expired plan, zero cap, suspended plan and over-budget job all fail **before** queue/GPU.
- Simultaneous job inserts honor same shop subscription row lock; two duplicate idempotency requests produce **one** reserved job, not two charges.
- Insertion with spoofed `reserved_usd`, changed source prompt hash/seed, invalid 480p profile, unauthorised model or missing durable outbox fail.
- Replayed queue message, expired/mismatched lease token, private upload timeout, DB commit ambiguity and slow GPU overrun never trigger automatic second inference or false refund.
- A real authorized clip with wrong shop, media SHA, revoked review role, pending VisualReview or unreviewed AI disclosure cannot enter Feature4.
- Preserve all current `campaign`/`render` operations, render worker, Supabase isolation, existing DEV shop/user and 4 required CI jobs.

## Strictly deferred until integration is actually verified

A real GPU job, model weights checksums, actual tariff/billing reconciliation, image-to-video retailer consent for regional processing, approval of Tencent's territory/hosted commercial terms, human visual results and Feature4 real end-to-end composition **are not complete**. The branch has only offline CPU and contract-level tests. The coordinator alone owns `supabase/migrations/**`, `docs/INTERFACES_V1.md`, current main, PROD, and live rollout.
