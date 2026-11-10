# Issue #249 — Real original Python Flex vs Free SWA 20+20 equal-route reliability, 2026-10-28

**Decision:** original Azure Functions HTTP acceptance **FAILED**; Issue [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) must remain OPEN. No fix deployed.

## Executed evidence
- [Real protected Azure DEV Actions run #40691854364](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40691854364): **FAIL exit 4 intentionally on original Flex unreliable responses**; prior offline security assertions and exact tagged Central India DEV Azure OIDC verification **PASS**. Source [PR #533](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/533) merged `f2dd858aeba2c062bfd76e21258441b3398ecedc`, all [four exact-head CI #40691369828](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40691369828) passed. Source postmerge main #40691854193 ran Python/Supabase/FFmpeg PASS but frontend CANCELLED by competing main changes, **not** 4/4 independent PASS.
- **40 real synthetic no-JWT requests:** same exact fixed campaign-auth GET `/api/campaigns/11111111-1111-4111-8111-111111111111` on existing original Python Functions host and named Free SWA Node preview; 20 per host, max two simultaneous per backend, 75-second deadline, 2 initial, 8 warm, 4 concurrent, 6 post 300-second inactivity. No unknown-route 404 comparison, privileged write, real tenant/JWT, data mutation, paid compute or other Azure configuration.

| Verified live metric | Original Python Flex | Existing Free SWA Node preview |
|---|---:|---:|
| Requests issued / completed HTTP | 20 / 20 | 20 / 20 |
| Expected HTTP401 | **11** (all application X-Request-ID marked) | **20** |
| Real HTTP503 | **9** (all without Python app marker) | **0** |
| Curl/client timeout | 0 | 0 |
| Expected-handler rate | **55%** | **100%** |
| p50 across all 20 completed HTTP responses, including errors | **5.160s** | **0.768s** |
| p95 across all 20 completed HTTP responses, including errors | **60.999s** | **1.727s** |
| p95 expected-handler responses only | **Unavailable: 11 < 20** | **1.727s** |
| p99 | **Unavailable: only 20 requests** | **Unavailable: only 20 requests** |

| Phase | Python HTTP503 | Node HTTP503 |
|---|---:|---:|
| Initial | 1 / 2 | 0 / 2 |
| Warm | 4 / 8 | 0 / 8 |
| Bounded concurrent | 2 / 4 | 0 / 4 |
| After 300s inactivity | 2 / 6 | 0 / 6 |

Confirmed original Flex 503 first response byte times were about **60.884–61.034 seconds**; TLS/DNS/TCP were established before gateway error responses. A Python `X-Request-ID` was absent on the nine 503s and present on all eleven handler HTTP401 responses. The original failure is **NOT exclusively first-idle cold request**: warm and concurrent calls fail too. Neither a five-minute idle nor 60.9s timing proves a specific scale-to-zero event or Azure language worker timeout.

**Scope limitations:** one 20-per-host bounded sample can calculate a descriptive p95 over completed responses but **cannot certify a 24-hour SLA, production percentiles, multi-shop authorization, or Node equivalence of original Python Queue, FFmpeg and secure assets**. App and platform diagnostic [reports](P0_249_20261028_ARM_DETECTOR_VERDICT.md) still lack per-request host/worker ingress causality. Root cause **UNKNOWN**, not proven gateway, host, Python worker startup or gRPC.

## Next action / ownership
1. Obtain causal Azure original host ingress/request routing and language worker startup/grpc trace for the **actual same-path failures around 2026-10-28 12:57–13:10 UTC**, using existing private DEV diagnostics. Check timestamp correlation with AppRequests/worker-start metrics but never export raw tokens, host instance IDs or tenant data. If unavailable, record platform telemetry blocker honestly; do not infer cause or change paid capacity.
2. Only implement minimal reversible fix after evidence; test exact request path, CI 4/4, protected DEV release, repeated same-path reliability. Avoid always-ready purchase, plan migration, POST retries, weakening auth/RLS, or customer origin change on conjecture.
3. Separately gated ROOT-approved real signed OWNER/EDITOR/VIEWER/revoked/two-shop positive-negative private image→poster PNG/selection→durable queued **30s H264/AAC** MP4→signed private GET and outbox/quota/recovery/cleanup. Existing offline E2E and synthetic FFmpeg tests do not establish this live acceptance.
4. Keep [Issue #249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) **OPEN**. [Issue evidence comment](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249#issuecomment-6469902496) captures the actual measurements.

**No new Azure resources, config, GPU/paid AI, tenant/customer writes, PROD or WineShopPOS modifications** in this run.
