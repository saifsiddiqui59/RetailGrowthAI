# Issue #249 — Original Flex platform detector investigation, 28 October 2026

## Current verdict
**Issue #249 is OPEN and the HTTP 503 reliability defect is UNFIXED.** The original Python Flex endpoint returned **4/8 actual HTTP503 at 60.889–60.912 seconds**, after TLS handshake, with no Python `X-Request-ID`, in the last actual bounded HTTP comparison [#40672031548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672031548). The separate Free SWA Node managed preview returned 8/8 expected synthetic responses, not production-parity proof.

The signed Feature2 request also saw ~60s 503 [#40659456731](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40659456731); previous read-only original-host Azure AppRequests/AppTraces/metrics [#40683849143](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40683849143) recorded worker_start minute buckets, no app 503 request bucket, sampled AlwaysReadyUnits=0 and one existing capped host instance, **without causal per-request correlation**. See [original probe](P0_249_20261028_75S_HTTP_COMPARISON.md) and [timestamp telemetry](P0_249_20261028_AZURE_HOST_TELEMETRY.md).

## New performed Azure REST detector work

Original tagged Central India `rg-retailgrowth-dev` Function App `rgai-dev-functions-d4e5ddbd`, approved existing DEV OIDC; REST `GET` requests only, with strict resource ID scope; sensitive raw detector tables/messages, resource IDs, JWTs and customer data not printed. The code requested the **10:25:40–10:35:30Z** historical window; the restricted response does NOT establish that Azure honored the period. API-version 2024-11-01.

| Merged PR | Exact PR CI | Protected actual Azure run | Observation |
|---|---|---|---|
| [#519](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/519) `f0b86c2c` | [4/4 PASS #40686157345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686157345) | [#40686643501 SUCCESS](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686643501) | Root `sites/{app}/detectors` list available, 80 capped entries including six relevant diagnostics; `diagnostics/{category}/detectors` unavailable for all three categories |
| [#524](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/524) `7aeb9f54` | [4/4 PASS #40687067710](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40687067710) | [#40687621617 SUCCESS](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40687621617) | Exact six fixed `sites/{app}/detectors/{detectorName}` GETs returned data, but sanitizer reported Unknown status |
| [#528](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/528) `93be497d` | [4/4 PASS #40688075645](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40688075645) | [#40688639732 SUCCESS](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40688639732) | Corrected Microsoft ARM `properties.status.statusId` parsing; redacted row counts and known severity only; no actionable status returned |

Actual final redacted response:

| Verified available detector | Dataset rows by section | Severity |
|---|---:|---|
| `ColdStartFailuresWorkflowNode` | [1] | Unknown |
| `functioncoldstart` | [2] | Unknown |
| `functionappdownanderrors` | [0,0,1,1,1,0] | Unknown |
| `ErrorsInApacheErrorLogForWorker` | [] | Unknown |
| `FNAppOpenTelemetryErrors` | [1] | Unknown |
| `AvailabilityAndPerformanceFunctionApp` | [1,3] | Unknown |

**Do not interpret a data row as a failed cold start, 503, worker crash, or error count.** None of these safe responses exposed a known `Critical`, `Warning`, `Info`, `Success`, or `None` `statusId`. They lack request-to-host identifiers and an independently verified effective window, and their free-form cells were intentionally withheld. Azure category endpoints were unavailable, not evidence of a healthy service.

**Workflow integration:** Each source PR passed its four jobs before merge; postmerge main runs of #519 [#40686643716](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686643716) and #524 [#40687621313](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40687621313) were cancelled when newer main pushed. Do not call them four-job postmerge PASS. Latest #528 main CI [#40688639731](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40688639731) must be checked separately.

## Root-cause classification and safe closure gates
Azure's own Functions scale documentation specifies an independent, non-configurable **60-second language-worker startup limit**; the user's ~61s HTTP 503s are **consistent with** that class of failure, **not proof** that this app hit it. Previous minute-bucket worker_start records are not per-request attribution. An exact original ingress/host/worker trace, Azure Diagnose and Solve Problems detailed private forensic analysis or other currently inaccessible platform evidence is required to **confirm a root cause**. The owner requested **no Microsoft support ticket**, and no ticket was opened.

No source code/service configuration change will be represented as a successful repair without causal evidence. Do not buy always-ready capacity, tune memory/instance count, migrate to Consumption, weaken tenant guards, auto-retry uncertain POST/PATCH, switch customer frontend to Node, or alter PROD/WineShopPOS. The separate Node Free SWA may be investigated in an approved production-parity plan, but is not yet a replacement for original Python Queue/FFmpeg workers.

**Outstanding:** (1) obtain causal ingress/host/worker attribution in existing Azure diagnostics, or record it as a platform visibility blocker; (2) if proven, implement smallest reversible fix with regression and four-job CI, protected deployment/rollback and repeated first/warm/idle/concurrent live HTTP with valid p95/p99 sample; (3) separately gate ROOT-approved signed OWNER/EDITOR/VIEWER and cross-tenant/revoked positive/negative private image→poster PNG→queued real 30s H264/AAC MP4→private signed download, quota/outbox/idempotency and cleanup. **Keep Issue [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) OPEN.** Detailed issue [comment #6469098069](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249#issuecomment-6469098069).

No new Azure resources, app configuration, paid AI/GPU, tenant/user mutations, customer cutover, PROD or WineShopPOS changes were performed by these three diagnostic deployments.
