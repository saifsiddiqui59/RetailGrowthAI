# Issue #249 — Actual existing DEV Python Flex import-isolation canary FAILED (2026-10-28)

**Live verdict:** original Azure Functions HTTP is **NOT FIXED**. [Issue #249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) has been reopened; do not merge [source PR #568](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/568) as a verified 503 repair. The PR has been returned to **draft** for audit.

## Verified source and protected deployment

- Source [PR #568](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/568) exact candidate SHA `7b887b6a1f168b0197ed0acf670f22c3597be1e7`; four-job [source CI #40754062483](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40754062483) SUCCESS. Python Function App indexing was reduced to `json`, `os`, `azure.functions` and sanitized `request_diagnostics`. HTTP JWT/tenant/queue/store imports and worker-only planning, poison, rendering, notification and poster modules are deferred to the invoking HTTP request or queue/timer handler. The additional `python -S` indexing test passed. None of this is proof of Azure ingress/worker readiness.
- Coordinator [PR #572](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/572) squash-merged as `4cea038d3e1c8cba37b6f0bcde9c44581fb538d3` after four-job [PR CI #40754751290](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40754751290) SUCCESS. Independent [postmerge main #40755301309](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40755301309) 4/4 SUCCESS.
- Actual protected [DEV Azure canary #40755301253](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40755301253) **FAIL by designed exit 4**: original Central India tagged DEV RG/app/subscription OIDC audit passed; pinned FFmpeg candidate and baseline-source ZIPs verified; existing app code-only ZIP deployment succeeded; original read_campaign, plan_campaign, render_campaign_reel and recover_stale_jobs function indexing verified. No new app/storage/plan/settings/always-ready, GPU or PROD. After live HTTP failure the protected fallback **source-baseline** ZIP deployment step completed SUCCESS, printing `P0249_SOURCE_BASELINE_RESTORED=TRUE_EXACT_PRIOR_DEPLOY_BYTES_UNKNOWN`. That fallback is the previously four-job-green prechange main source `6e8077f4...`, **not a byte-for-byte restoration of the historically installed pre-canary package**; a new independent read-only source/trigger health audit is still prudent. Rollback success does not prove healthy HTTP.

## 40 genuine matched synthetic HTTP GET outcomes

Path: `GET /api/campaigns/11111111-1111-4111-8111-111111111111` without JWT; 20 per original Python Flex and existing Free SWA Node preview, at most two concurrent per host, 75s curl per request, 2 initial + 8 warm + 4 concurrent + 6 after 300s inactivity.

| Observed property | Original Python Flex after candidate deployment | Existing Free SWA Node |
|---|---:|---:|
| Completed HTTP requests | 20/20 | 20/20 |
| Expected 401 | **11 with Python X-Request-ID** | **20** |
| True HTTP503 | **9 WITHOUT Python X-Request-ID** | **0** |
| Curl/client timeout | 0 | 0 |
| All-completed HTTP p50 (including failures) | **4.617s** | **0.879s** |
| All-completed HTTP p95 (including failures) | **60.871s** | **1.841s** |
| Successful-handler-only p95 | **UNAVAILABLE (11 verified)** | 1.841s |
| p99 | **UNAVAILABLE (n=20)** | **UNAVAILABLE (n=20)** |

Phase-specific original Python 503s: **initial 1/2; warm 4/8; bounded concurrent 2/4; after idle 2/6**. Post-idle genuine 503 TTFB ~60.857–60.860s, TLS completed in ~0.63s; 401 application responses present among the same runs. This directly refutes the assumption that *only first cold starts* are affected. Original cause **UNKNOWN**: HTTPS gateway-to-host/instance routing, specialization and Python worker/gRPC readiness remain possible. A 60s language-worker-startup limit is only a hypothesis.

Comparative pre-change protected [#40691854364](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40691854364) had **exactly 9/20 original Python HTTP503** and **0/20 Node HTTP503** (Python p95 60.999s; Node p95 1.727s). The source-only lazy import candidate therefore made **no demonstrated reliability improvement** in this bounded repeat. Node's no-JWT success **is not** authorization, queue, commercial media or customer parity.

## Required next steps

1. **P0:** independently verify after-fallback original DEV app identity, HTTP and worker-trigger indexing; make a few READ-ONLY fixed-UUID GET observations, reporting 401/503 separately. Do not claim source rollback was byte-identical or fixed host.
2. **P0:** acquire causal original Azure platform ingress/instance assignment/worker gRPC evidence correlated to live canary 2026-10-28 roughly **19:35–19:50 UTC** using existing protected read-only diagnostic scope; previous sanitized AppRequests/workers minute-buckets and ARM detector row counts were not causal. Do not change max instances, always-ready, plan/cost, auto-retry writes or start a Microsoft support ticket against the prior owner request.
3. **P0 alternative:** continue the existing secure Free SWA Node *HTTP-only* facade, keeping Python Queue/FFmpeg workers, JWT cryptographic validation, current shop membership, quotas/outbox/CAS and private signed download. Before **any** customer origin change require real signed positive and negative two-shop OWNER/EDITOR/VIEWER/revoked 30-second H264/AAC MP4 end-to-end with cleanup. Existing [draft PR #423](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/423) is a separately ROOT-gated harness, NOT proof its workflow executed.
4. Leave #249 **OPEN**; PR #568 **DRAFT/unmerged**, pending an actual verified repair. No new paid infrastructure/GPU, hosted Supabase SQL/customer writes, PROD, WineShopPOS or user frontend API cutover in this experiment.
