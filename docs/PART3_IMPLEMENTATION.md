# Part 3 — implementation map and integration gates

**Integration:** `feat/part3-integration` → final single coordinator-reviewed PR to `main`.
**Current status:** source under active implementation, not enabled/deployed, no billable test run.

## Branch/workstream ownership

| Workstream | Branch | Scope | Completion boundary |
| --- | --- | --- | --- |
| P3-A: provider + t2v/i2v + prompt | `feat/p3-wan-provider` (#109) | `ai-agents/src/ai_agents/premium_video.py`, provider tests, provider handoff | Async Wan2.7 adapter and mock gates only; actual Wan3.0 upgrade/approval separate |
| P3-B: entitlement, ledger, state, retries | `feat/p3-premium-jobs` (#113) | additive `supabase/migrations/20261023180000_p3_premium_video_reservations.sql`, independent service modules, Python tests | zero-allowance server-owned atomic reservations and UNKNOWN-safe prototype; no applied SQL or worker |
| P3-C: frontend selection | `feat/p3-premium-ui` (#115) | `frontend/src/features/premium-video/**`, isolated JS tests | FFmpeg default, premium disabled; not mounted in shared CampaignDashboard |
| P3-D: durable dispatch and Azure worker | **Not yet branched** | proposed new `azure-functions/campaign-api/premium_dispatch/**`, tests | exact queued UUID, transactional outbox, durable DB claim, timer/poll/poison, no existing queue trigger collision |
| P3-E: private ingestion + substitution | **Not yet branched** | proposed `azure-functions/campaign-api/premium_media/**`, media tests | validate provider destination/CDN/size/codec, private per-shop object+output media registration, existing private signed URL; explicit free FFmpeg fallback |
| P3-F: cancellation/refunds/security/performance | **Not yet branched** | independent security negative tests, performance and reconciliation runbook | no double charge, safe cancel before request, uncertain provider charges marked UNKNOWN, admin reconciliation, concurrency and load guardrails |

Do not claim a branch or PR exists unless verified. Independent branches must be based on the current Part 3 integration tip when actually started, with disjoint path ownership.

## Integration API proposal — stage, do not change shared v1 silently

- Future authenticated `POST /api/campaigns/{campaign_id}/premium-videos` accepts `{day_id, mode, resolution, duration_seconds, input_asset_id}`, no arbitrary path/URL/model ID; server derives selected provider, reviewed prompt, consent and price. Return `202 {job_id,status}` only if quota AND durable enqueue/outbox exist.
- Future authenticated `GET /api/premium-video-jobs/{job_id}` returns sanitized `{job_id,status,output_asset_id,error_code}`, tenant-filtered. Download should use the existing short-lived signed private mechanism, not provider CDN links.
- Existing `POST /api/campaigns/{id}/renders` and `GET /api/render-jobs/{id}` retain exactly their Part 1 meanings. Keep FFmpeg default; no implicit premium provider billable fallback.
- Route/contract additions and CampaignDashboard placement are staged for joint review with Part 2 coordinator; never edit overlapping Part 2 shared paths independently.

## Security and spending invariants

1. Existing RLS membership/asset provenance must be checked on request and again before provider transfer. Cloud service role cannot rely on only shop ID from the browser.
2. Existing subscription ledger `shop_usage_reservations` is the only quota source. Each premium job must have one idempotent atomic reservation of seconds and maximum USD (rounded up at vendor price); zero allowances by default. No self-service upgrades, card charges, Razorpay, or second billing system.
3. DB transaction writes a durable outbox event alongside accepting a job. Azure queued messages contain UUID only. Token-fenced job claims and owner-only or service-only status mutation prevent cross-tenant state writes.
4. Set SUBMITTING durably before contacting a paid provider. Network uncertainty is UNKNOWN: never automatically repeat POST or refund as though no provider charge occurred. Poll existing task IDs; time-limited URLs must be privately imported before expiry.
5. Cancel QUEUED locally only after atomic cancellation and release proof. Once SUBMITTING/PENDING or uncertain, cancellation/credit refund requires verified provider cancellation/billing semantics.
6. No uncontrolled SSRF or arbitrary HTTPS import; allowlist provider-origin download host, limit bytes/video streams/frame dimension, validate output via ffprobe, store in existing `retailgrowth-media` bucket.
7. No tokens, commercial inputs, signed URLs, model prompt with PII, or credentials in CI logs. Explicit image transfer/commercial license/AI disclosure consent before use.
8. Strict global/preset/user cost ceiling, alerts and approval flag; no provider key in `VITE_*`.

## Pre-merge verification

- Verify all existing **four** standard CI jobs on each PR and after integration. Dedicated P3 Python/security unit and mocked video tests must run and be inspectable, not inferred from source presence.
- Apply and negative-test the *new migration only* in disposable Postgres. Hosted DEV migration prohibited until explicit reviewed scope/approval. No Part 1 migration replay.
- Exercise mock provider creation and polling, timeouts/duplicates, failed storage upload, tenant denial, cancellation boundary, FFmpeg free fallback, UI disabled state and no double reservation.
- Run any truly billable and externally transferring smoke only after the separate owner/provider/license/region/cost consent gates. All existing Part 1 production and other repositories remain unchanged.

## Snapshot and blockers

Verified internal PRs: #109 / #113 / #115, each targeting `feat/part3-integration`. Their source currently includes offline tests, but this document **does not assert the CI runs completed**. The Phase 3 integration is **not complete**: outbox/RPCs, provider output ingestion, Wan3.0 adapter, compiled frontend placement, actual deployment, billing approval, hosted negative tests and live generation remain open. Do not merge any PR or the final branch solely on this documentation.
