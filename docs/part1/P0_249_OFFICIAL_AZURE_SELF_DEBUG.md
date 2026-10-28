# P0 #249 — Official Azure self-diagnosis, low-cost first (2026-10-26)

Status: SOURCE/TEST PREPARATION ONLY. No service fix, Azure deployment or price/capacity change is established by this work. No Microsoft Support case needed or requested.

## What official documentation rules in / rules out

1. Microsoft Learn **Troubleshoot Azure Functions app down or reporting errors**:
   https://learn.microsoft.com/en-us/troubleshoot/azure/azure-functions/availability/functions-troubleshoot-issues
   Recommends Azure Portal Function App > **Diagnose and solve problems** > **Function App Down or Reporting Errors (Preview)**. Inspect **host startup** (placeholder specialization, allocation), **deployment timeline**, configuration/Storage connectivity, host collisions, extension versions, memory/CPU, SNAT/TCP exhaustion. For network diagnostics search **Connectivity Troubleshooter**. The Kudu log tool excludes Flex Consumption; don't prescribe Kudu.
2. Microsoft Learn **Functions scaling**:
   https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale
   Host timeout vs 60-second **language worker startup limit** are DIFFERENT. The Python Flex app's host.json says 20 minutes, while two actual platform HTTP 503s arrived after ~60.8/~60.95 seconds without Python X-Request-ID. Similar seconds alone are not a diagnosis.
3. Microsoft Learn **Flex Consumption hosting**, **Event-driven scaling**:
   https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan
   https://learn.microsoft.com/en-us/azure/azure-functions/event-driven-scaling
   HTTP has its own scale group; **maximumInstanceCount=1** limits *on-demand* instances per group, not a global app instance count. Flex may scale HTTP to zero; the next request can cold start. But earlier runs had correct fast 401s between HTTP stalls, including a nonexistent route. Do not assume the stalled attempt was the first request after an idle period.
4. Microsoft Learn **Python deployment build options**:
   https://learn.microsoft.com/en-us/azure/azure-functions/python-build-options
   Large dependency/ZIP packages can increase cold-start and import/index time. Current RetailGrowthAI source builds **one ZIP** with Python HTTP code, queue/timer workers, poster/video engines and **both FFmpeg/ffprobe binaries**. Heavy imports were deferred in PR #256 but bytes remain in the deployed package. This is a strong **testable architecture difference** from WineShopPOS's separate small Node v4 HTTP Function; not proven to be the failing host issue.
5. Microsoft Learn **Flex management**:
   https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-how-to
   Portal **Settings > Scale and concurrency** shows HTTP concurrency/always-ready group. Inspect only; do **not** change without separate cost approval. Region pricing must be verified before any billable always-ready experiment.
6. Microsoft Learn **Compare Functions runtime versions**:
   https://learn.microsoft.com/en-us/azure/azure-functions/functions-versions
   Classic Linux Consumption is scheduled for retirement **2028-09-30** and also scales to zero. WineShopPOS uses **Node.js Functions v4 Consumption Y1**; blindly cloning its plan is not a future-proof repair.

## Self-service diagnostic plan, no new resource or spending

A. In the Azure Portal select exact existing **rg-retailgrowth-dev / rgai-dev-functions-d4e5ddbd**, Central India, and open **Diagnose and solve problems > Function App Down or Reporting Errors (Preview)**. Check **Startup issues**, **Recent deployments**, **Host errors**, **Scale**, **SNAT** and **Connections**, and run **Connectivity Troubleshooter** if exposed. Note only safe category/count/timestamps; never copy secrets or raw auth headers.

B. Use the reviewed \`ops/p0_249_cold_warm_http_probe.py\` through \`.github/workflows/p1-dev-p0-249-cold-warm-once.yml\` once after protected CI/merge. It validates subscription, tagged RG and app via OIDC, makes **six unauthenticated GET requests** to a fake UUID and nonexistent route, with two immediate pairs and a single 300-second inactivity interval. It prints only status, seconds, TLS/first-byte phases, and presence of application marker. No user account, POST, token, resource or settings writes; one-shot and bounded. Note: 300 s of quiet FROM THIS RUNNER does not prove Azure had no other traffic or scaled to zero. The diagnostic does not assert root cause.

C. Interpret without misleading labels:
   - **401 or 404 with app marker, sub-10s**: normal app response.
   - **curl 000 after TLS and no first byte**: client-aborted no-response, not proven upstream 503.
   - **actual 503 after ~61s and no Python marker**: upstream/host startup/assignment remains plausible.
   - If the FIRST probe after the inactivity interval alone fails but immediate repeats quickly succeed on repeated comparisons, cold-start is strengthened, **not proven** without host scale event correlation.
   - If warm immediate repeats or unknown routes also intermittently fail, investigate HTTP platform/host allocation, worker readiness, concurrency and package hydration, not solely cold starts.
   - Queue-trigger MP4 success is unrelated to the HTTP trigger scale-group reliability.
   - If all 6 GET requests pass, that is **not sufficient** to resolve prior intermittent behavior or real authenticated create/POST reliability.

D. **Next low-cost mitigation choices only after evidence:** trim/split HTTP package from media/queue workers, or review on-demand group ceiling (currently 1), with strictly reversible change and accepted cost/tenant impact; do not use frequent artificial warm pings or automatically replay POST/PATCH.

## WineShopPOS-style architecture fallback (already source-staged, NOT deployed)

\`experiments/wineshop-node-http-control/\` is a tiny **Node.js Azure Functions v4** standalone app: 200 anonymous \`/api/p0-health-lite\`, 401 anonymous fake campaign read, 404 unknown URL. An invalid supplied Bearer fails closed; it NEVER returns real campaign data. It uses no DB keys, queue access, registered users, or video engines. Existing full Python/RLS/queue/render code is unchanged.

If controlled diagnostics still cannot isolate/fix existing HTTP:
1. Review a NEW DEV-only minimal **Node Flex zero-always-ready** A/B app under a concrete cost cap and tear-down plan. Compare cold/warm unknown+protected synthetic HTTP under the same region. This mirrors WineShopPOS's lightweight Node Functions pattern, **not** its older Linux plan or production resources.
2. If A/B results show a reproducible advantage, move the HTTP facade only in stages while preserving original Supabase JWT cryptographic validation, tenant/shop RLS/membership, quota/subscription, exactly-once outbox/CAS and signed media access. Existing Python Azure Queue/FFmpeg workers remain.
3. Do NOT switch SWA API origin or perform real customer writes on the control app. Full protected signed-in acceptance (including cross-tenant denials and 30s MP4) is mandatory before replacing an API.

**Current stage:** scripts/negative tests/source are prepared; the protected Azure run and hosted A/B have NOT been executed. Issue #249 remains open.

## 2026-10-26 actual protected post-idle probe result — NOT fixed
- PR #324 merged `78789399` after 4/4 PR CI; post-main four CI [#40291064552](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40291064552) passed 4/4.
- Real one-shot existing DEV OIDC [#40291064533](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40291064533) **failed HTTP acceptance intentionally**: 4/6 requests were **curl 000 12s client timeouts**, all post-TLS (0.70–0.75s handshake) with **zero first byte and no app X-Request-ID**. First campaign GET returned 401 with app marker in 4.795s; immediate repeated campaign GET timed out 12.003s. After **300s inactivity from this runner**, campaign GET again 401 with marker in 4.740s while unknown GET timed out 12.002s. Unknown-route GETs timed out all three times. No tests include JWT/tenant data, writes, changes to Azure resources or billing.
- **Interpretation:** first-request-after-idle cold start *alone* is inconsistent with the immediate repeated failures and successful post-inactivity campaign request; it remains possible that platform HTTP instances restart/reassign at other times. A distinct real Azure 503 at ~61s occurred in previous tests, but this new test establishes only 000 timeouts. Do not buy always-ready or migrate based solely on timing.
- **New lower-spend option verified in current official docs:** Azure Static Web Apps **Free includes managed Azure Functions APIs**, including `apiRuntime: node:22` under the `platform` config. Managed API runs HTTP triggers **only**, has **45-second response cap**, and cannot use managed identities or queue triggers. Our current request model is durable async with Queue worker, so a **small Node HTTP facade in existing Free SWA + unchanged Python queue/video workers** is possible in principle. The full JWT/RLS, tenant, subscription/quotas, write-CAS and signed-media contract needs implementation and review before any frontend API-origin switchover; a source-only control is not sufficient. Official: https://learn.microsoft.com/en-us/azure/static-web-apps/faq ; https://learn.microsoft.com/en-us/azure/static-web-apps/apis-overview ; https://learn.microsoft.com/en-us/azure/static-web-apps/configuration .
- **Preferred next experiment:** if the owner wants the fallback, use an **isolated DEV preview environment** in the **existing** Free SWA (without replacing live site `api_location: ''`), deploy the synthetic Node 401/404 health control, verify live real response and isolate routing/runtime differences. Requires reviewed workflow, exact Free-host identity, no real tenant/JWT/DB access, bounded test quota and rollback. Do not claim this has been deployed. P0 remains OPEN.
