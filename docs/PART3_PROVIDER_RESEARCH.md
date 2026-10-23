# RetailGrowthAI — Part 3 Provider and Cost Evaluation (2026-10-23)

**State: research and disabled source prototypes only. No approved account, paid video call, hosted migration, cloud worker or customer charge.** Preserve Part 1 FFmpeg as the default for all shops.

## Current official Alibaba provider matrix

Official sources:
- Wan 3.0 standard: https://www.alibabacloud.com/help/en/model-studio/wan3-0-video
- Wan 3.0 Prime: https://www.alibabacloud.com/help/en/model-studio/wan3-0-video-prime
- Wan 3.0 API/guide: https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide
- Wan 2.7 text API: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
- Wan 2.7 image API: https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
- Price table: https://www.alibabacloud.com/help/en/model-studio/model-pricing

| Model ID | Text/Image | Duration | Resolution | Singapore nominal price / output second |
| --- | --- | --- | --- | --- |
| wan3.0-video | both, plus other references | 2–30s | 480P/720P/1080P | $0.05 / $0.10 / $0.20 |
| wan3.0-video-prime | both, speed-oriented | 2–30s | 480P/720P/1080P | $0.068 / $0.14 / $0.28 |
| wan2.7-t2v-2026-06-12 | text | 2–15s | 720P/1080P | $0.10 / $0.15 |
| wan2.7-i2v-2026-04-25 | image-first-frame | 2–15s | 720P/1080P | $0.10 / $0.15 |

Prices above are Alibaba's published original list prices, **not a negotiated commitment**. The Wan 3.0 site advertises a dated discount ending 2026-09-24; do NOT use that expired promotion in pricing policy. Other deployment regions have different prices and must be verified independently with matched model, API key, workspace and endpoint. Availability must be checked in the actual target workspace before activation. WAN 3.0 now supports a single full 30-second output and is a candidate for the production adapter; narrow Wan 2.7 source implementation remains sandboxed for now.

### Illustrative clip cost excluding tax, FX fees and storage

Using October 23 USD/INR reference **~₹94.9 per USD** (https://wise.com/us/currency-converter/usd-to-inr-rate/history/23-10-2026):

| Output | Alibaba list cost | Indicative INR |
| --- | ---: | ---: |
| Wan3.0 standard 30s 720p | $3.00 | ~₹285 |
| Wan3.0 standard 30s 1080p | $6.00 | ~₹569 |
| Wan3.0 Prime 30s 720p | $4.20 | ~₹399 |
| Wan3.0 Prime 30s 1080p | $8.40 | ~₹797 |
| Wan2.7 15s 720p | $1.50 | ~₹142 |
| Wan2.7 15s 1080p | $2.25 | ~₹214 |

**Free promotional quota is never assumed**; its eligibility, region, model and expiry may change. Output billing and real invoicing should be reconciled via provider usage, not UI estimates. Reserve the worst-case cost before any request, retain reservations for UNKNOWN attempts, enforce daily/provider and per-shop ceilings, and reconcile actual usage after success/failure before credit release. Trial and existing plan premium allowance remains zero.

## Async tasks, safety and rights

- The official APIs require async submission and task-ID polling; output URLs and task IDs are time-limited (documented ~24h). Never repeat a provider POST after uncertain acceptance. Persist SUBMITTING before send; after response loss, UNKNOWN pending reconciliation rather than another paid POST.
- Video is generated outside the RetailGrowthAI Supabase/Azure storage boundary. Require explicit product/data-region review and commercial-rights and user-media consent before transferring customer images. Only server-issued short-lived tenant-private storage links may be inputs; do not accept arbitrary HTTP URLs. Verify file size/MIME/license/provenance and reject unsupported/regulated claims.
- Model Studio product terms: https://www.alibabacloud.com/help/en/legal/latest/alibaba-cloud-international-website-product-terms-of-service-v-3-8-0 — provider says it does not claim ownership of Output IPR, but customers remain responsible for input/output lawful use, data protection and necessary consents. This is **not** blanket copyright clearance or a guarantee of exclusivity. Review current agreement, relevant jurisdiction and commercial use before launch.
- Provider result URLs must not be shown to end users. Import bytes via a verified allowlisted origin, bound and validate content/FFprobe, register media_assets with tenant rights in existing private bucket, and expose only existing short-lived signed private download.
- FFmpeg still handles the baseline free/included path, sound/overlays and any approved fallback. **Never silently switch from failed Wan to another paid model** or automatically charge again; any provider substitution needs a new price/consent check.
- Alibaba Model Studio is official primary. Third-party API resellers (e.g. Runway, https://dev.runwayml.com/learn/wan-3-0-api) claim hosted Wan 3.0 access; independent account pricing, rights, data location, contractual status, and API compatibility are NOT verified and are not approved.

## Approval gates for future live use

1. Formal provider/model/version/region and commercial terms review; ensure purchased plan permits customer commercial outputs and external user media, including consent and data residency.
2. Verified server-only credentials stored in RetailGrowthAI-specific secret store, immutable per-model pricing/FX snapshots, nonzero owner-approved budget ceiling and alerts.
3. Reviewed additive Supabase migration + RLS/tenant denial/atomic reservation+refund tests; idempotent status transitions, safe cancel semantics and reconcilable UNKNOWN states.
4. Configured and approved *existing* Azure worker/queue/outbox or separately approved queue provisioning, bounded retries and concurrency, safe importer and private downloads.
5. 4/4 existing CI + additional P3 tests, security review, and a **separately owner-approved** single controlled paid DEV test; no automatic customer charges.
6. Part 3 final PR reviewed by Coordinator only; do not merge Part 3 directly to main.

## Implementation handoff snapshot

Integration branch: `feat/part3-integration`, internal #109 gated Wan2.7 adapter, #113 zero-default quota/job schema + worker scaffolding, #115 free-first standalone UI. These feature PRs target the integration branch. The current frontend chooser is deliberately **not mounted** in the shared Part 1 dashboard. Premium HTTP routes, queue/outbox wiring, DB RPCs, secure provider-output importer, hosted SQL application, cancellation and live video tests are **unfinished**. Source code is not proof of live Wan generation.

## LATEST Part 3 progress addendum — 2026-10-23
- The prior handoff snapshot is historical. Dedicated branches for provider (#109), zero-default job/credit scaffolding (#113), disabled chooser (#115), and private output importer (#122) all merged into **feat/part3-integration** after verified six-job mock CI. Importer is code only: no registered live queue worker. The chooser is now mounted disabled, with FFmpeg still default.
- The original proposed premium SQL was moved outside runnable migration history, pending Coordinator-approved new migration/ledger/security tests. Default quota remains zero. Vendor output CDN hostname compatibility requires checking the official `dashscope-a717.oss-accelerate.aliyuncs.com` example; follow-up PR #126 is under CI/review and should not be claimed merged until confirmed.
- No paid Wan API request, external media transfer, plan payment or production activation took place.
