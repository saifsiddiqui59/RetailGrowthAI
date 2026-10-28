# Issue #249 — Verified original Azure Flex host/worker correlation, 2026-10-28

## Scope
This is a **historical read-only Azure telemetry investigation**, not a fix or a successful HTTP acceptance. Original exact DEV Azure Function App: `rgai-dev-functions-d4e5ddbd` in tagged Central India `rg-retailgrowth-dev`. Existing protected OIDC Azure run [#40683849143](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40683849143) **SUCCESS as telemetry collection**. Guarded [PR #512](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/512) merged `7e43fda3d0a6e361dafff1275a69d3e07b3cd7e8` after exact 4/4 [CI #40683260617](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40683260617). Original 75-second live HTTP reliability run [#40672031548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672031548) previously **FAILED** because original Python Flex 4/8 real HTTP 503 at 60.889–60.912s; isolated Free SWA Node expected 8/8 responses. This telemetry workflow did **not** retest HTTP, provide any JWT, perform customer writes, or deploy code.

## Azure ARM and platform metrics
- Actual ARM `functionAppConfig` visible; runtime **Python 3.12**, memory **2048 MB**, `maximumInstanceCount=1`; `perInstanceConcurrency` and exact configured HTTP always-ready entries **unknown** (fields not returned).
- Between **10:25 and 10:34 UTC** sampled Azure `InstanceCount` averages **1.0 for nine minutes and 1.2 at 10:31**; `AlwaysReadyUnits=0.0` in all ten minute buckets. This does not prove HTTP scaled to zero or identify the instance receiving an individual request.
- `CpuPercentage` minute average **1.0–1.333%**; `AverageMemoryWorkingSet` **486,516,736–588,772,966 bytes** (approximately **464–562 MiB**). These platform aggregates do not prove no instantaneous high load or crash; no CPU/memory pressure was demonstrated at the sampled resolution.

## Azure scoped Log Analytics
Each query was limited to the original application by role/resource and fixed historical UTC window. No raw log messages, exception text, request URLs, user/shop IDs, tokens, secrets or operation IDs were printed.

| Window | Application request status buckets | Classified worker traces | Exceptions / other |
|---|---|---|---|
| **10:25:40–10:35:30 UTC** (4 live 503s) | status **0** at 10:26, 10:28, 10:30, 10:32, 10:34; **401** at 10:26, 10:27, 10:28, 10:34 | `worker_start` at **10:26, 10:28, 10:29, 10:30, 10:34** | AppExceptions, AppDependencies and AzureActivity: **empty_or_filtered** |
| **08:48:30–08:51:30 UTC** (Feature2 signed 503) | **200** at 08:48, 08:49; **0** at 08:50 | `worker_start` at 08:48, 08:51 | Exceptions / dependencies / activity: **empty_or_filtered** |
| **09:39:45–09:46:30 UTC** (prior client timeouts) | **0** at 09:40, 09:42, 09:44, 09:46; **200** at 09:39, 09:42; **401** at 09:46 | `worker_start` at 09:39, 09:41, 09:45, 09:46 | One **connection_aborted** category bucket at 09:44; dependencies/activity empty_or_filtered |

**Critical caveats**: These are **presence of minute-level rows, not event counts**. The safe output did not retain values for `events` or `p95_ms`; do not infer counts/rates, and do not claim the returned status `0` rows correspond one-for-one to HTTP 503 responses. The source can include non-HTTP timers and queue triggers. There were **no AppRequests status 503 rows** in the scoped returned output; that is consistent with missing app-level invocation evidence, but sampling and platform telemetry gaps mean it does not prove no handler invocation. The `worker_start` event classification uses text predicates inside KQL and is **not a confirmed worker restart/crash** or direct causation. Azure-specific gateway/instance correlation IDs were not accessible from these safe aggregates.

## Classification and decision
- **Confirmed:** original Azure Flex HTTP returns genuine 60.889–60.912s 503 with TLS established and no Python `X-Request-ID` (run #40672031548), interspersed with valid marked 401; different route classes affected including unknown GET. A separate free Node managed API had no 503 in its eight anonymous synthetic GETs.
- **Corroborated but noncausal:** worker-start trace buckets overlap failed HTTP windows, `AlwaysReadyUnits=0`, some app request status `0`, one earlier categorized connection-aborted event, no sustained high sampled CPU/memory.
- **Unconfirmed:** exact cause (Azure HTTP gateway dispatch/host specialization/worker startup/gRPC/scale/subprocess or other dependency); 60-second language-worker startup timeout is a plausible hypothesis only.
- **No fix deployed:** no speculative HTTP route patch, instance-count/capacity change, paid always-ready, legacy plan migration, support ticket, customer origin cutover, service-role sharing, PROD or WineShopPOS modification.

## Remaining closure gates
1. Establish **causal** original-host instance/language worker startup/exit and ingress evidence via existing Azure diagnostics/detectors (or explicitly record platform telemetry unavailable). Avoid replaying privileged writes or dumping raw logs.
2. Apply a **small proven** reversible source/config mitigation only if causality and safety are established, with regression, four CI jobs and protected post-deployment live verification. Do not buy always-ready or move to Consumption on conjecture.
3. Re-evaluate first/warm/idle and concurrent HTTP reliability with representative sample size and p95/p99 where valid; compare equivalent protected GET routes after auth gate and distinguish free SWA routing 404 vs application 401.
4. Retain separate **ROOT-approved** multi-shop OWNER/EDITOR/VIEWER/revoked-negative signed-in flow, rights-verified media→poster PNG and selection→Python queued 30s H264/AAC MP4→private signed download, quota/outbox/lost-ACK and cleanup. No incomplete Feature3/4/5 dependencies assumed.

**Status: Issue [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) remains OPEN.** Detailed live HTTP timings: [20261028_75S_HTTP_COMPARISON.md](P0_249_20261028_75S_HTTP_COMPARISON.md). Issue evidence comment [#6468402267](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249#issuecomment-6468402267).
