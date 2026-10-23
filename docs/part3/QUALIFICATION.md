# Part 3 full integration source-qualification record — 2026-10-23

**Branch:** `feat/part3-integration`; **final draft PR:** #125 into main — Coordinator only. This qualification file is a source-only integration CI trigger and records exact PR evidence. No hosted deployment.

## Reviewed internal merges and CI evidence

| Internal PR | Scope | Exact check runs | Result |
|---|---|---|---|
| #109 | WAN 2.7 provider, async T2V/I2V, prompt/limits | Dedicated #39975248007 2/2; existing #39975248169 4/4 | PASS, merged to Part3 |
| #115 | FFmpeg-default premium chooser, no billing | Dedicated #39975257823 2/2; existing #39975257898 4/4 | PASS, merged to Part3 |
| #113 | premium job scaffold, zero-default shared-ledger SQL proposal | Dedicated #39975690745 2/2; existing #39975690715 4/4 | PASS after fixing isolated provider mock and unreviewed-migration conflict, merged to Part3 |
| #122 | no-redirect, bounded, verified private Wan MP4 output importer | Dedicated #39976479632 2/2; existing #39976479459 4/4 | PASS, merged to Part3 |
| #126 | vendor official output OSS hostname compatibility fix/regression | Dedicated #39977762809 2/2; existing #39977763357 4/4 | PASS, merged to Part3 |

The five PRs merge only into `feat/part3-integration`; the final PR #125 is open as **DRAFT**, not merged into `main`.

## Default-safe integrated behavior

- Current Part 1 `RenderStatus` and FFmpeg 30s Reel remain unchanged. The new PremiumVideoPanel is mounted AFTER standard render and its activation props default to **false**, so the premium mode is visible as an unavailable alternative but cannot launch paid requests.
- Wan 2.7 T2V/I2V adapter is gated by disabled-by-default server flag, trusted Singapore Alibaba Workspace origin, valid server key, and nonzero explicit per-job USD ceiling. Provider submit is async and only returns safe task ID/status.
- Source-only server premium coordinator checks tenant JWT/RLS campaign/day membership, image rights, disallowed inputs, and idempotency; worker marks uncertain task creation UNKNOWN instead of blindly re-posting a billable request.
- The source-only proposed SQL in `azure-functions/campaign-api/part3_sql/` extends the EXISTING `shop_subscriptions`/`shop_usage_reservations` rather than adding a second billing system. Premium allocation defaults to 0. The proposal is **not** in executable `supabase/migrations/` and has **NOT** been applied to hosted DEV.
- Provider output private importer allows documented `dashscope-a717.oss-accelerate.aliyuncs.com` URLs and reviewed matching host shapes, but rejects arbitrary URL/redirects/local IP and invalid MP4 bytes/codecs/duration. Uploads use existing tenant-private storage and require a lease-token-checked completion callback. No external provider URL is returned to browser.

## Incomplete / release-blocking tasks

1. Coordinator rebase/merge review against newer Part1 main commits, especially shared React campaign UI, workflows and canonical docs. No Part2-owned files touched.
2. **Promote/add new DB migration only under explicit approval:** review staged SQL, authoritative migration history, negative foreign tenant and race/rollback/credit test evidence, stable dollar exchange/cost pricing; no hosted schema changes today.
3. Wire private premium create/status/download HTTP API, transactional premium outbox/queue trigger/poison/recovery, service-role CAS claim/lease/finalization RPCs and registered worker, so tasks progress end-to-end using UUID-only messages. None are live yet.
4. Implement safe full provider result retrieval and pass **only** valid signed provider data from the internal poller into importer. Confirm expiry handling and no duplicate provider charge on UNKNOWN. Add cancellation/cost reconciliation and restricted production error codes.
5. Compose multiple provider clips into 30-second campaign using current FFmpeg with explicit free fallback, optional provider substitution only after fresh price/rights approval, and independently licensed music.
6. Owner to approve paid commercial API workspace, data-region/rights and image consent, per-tenant monetary ceilings and one strictly bounded paid DEV smoke before enabling customer premium.
7. Real browser Auth with cross-tenant denials, provider clip MP4/ffprobe and signed download under approved fresh test identities. No live Wan invoice/task/media exists, no paid subscription or checkout activation.

**DO NOT** mistake mocked CI or draft final PR for feature launch. Retain `RETAIL_PREMIUM_VIDEO_ENABLED=false` and no positive premium allowance until the tasks and separate approvals are complete. No WineShopPOS or GenAI Galaxy mutation.
