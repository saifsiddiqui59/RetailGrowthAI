# RetailGrowthAI DEV — Azure Functions Flex HTTP intermittent 503 support case draft (2026-10-25)

**Status:** Draft for the account owner/authorized Azure support channel. **Not filed. No support case number.**
**Scope:** Existing tagged RetailGrowthAI-only DEV `rg-retailgrowth-dev / rgai-dev-functions-d4e5ddbd`, Central India, Python 3.12 Functions v4, Flex Consumption 2048 MiB, maximum **one on-demand instance PER independently scaling function group**. HTTP always-ready and concurrency configuration are unknown. No WineShopPOS or PROD access.

## Issue for Microsoft Azure Functions engineering
HTTP requests intermittently complete TLS handshake and then receive no HTTP first byte. Some requests later returned a real gateway-origin **HTTP 503 at 60.806s / 60.954s** without Python `X-Request-ID`. Repeated shorter client aborts at 18–20 seconds were **client timeout / curl 000**, not proven HTTP 503. Both known GET routes and nonexistent GET routes were affected; nearby requests to the same Function App returned correct 401/404.

## Reproduction references, UTC
- 2026-10-25 08:10:39–08:12:20 UTC: [protected diagnostic #40175539961](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40175539961), **6 of 8** anonymous fake-ID GETs aborted at 20.002–20.003 seconds before first byte; TLS complete in 0.70–0.75 seconds.
- 2026-10-25 08:18:46, 08:19:06, 08:19:26, 08:19:46, 08:20:07 UTC: [protected #40176054781](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40176054781), **5 of 8** no-first-byte 20.002–20.003-second client aborts; TLS completed in 0.567–0.619 seconds.
- Real service 503s originally observed around 60.8 and 60.95 seconds in [#40097206285](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40097206285) and [#40098789883](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40098789883).
- 2026-10-25 10:38 UTC: [Resource/Service Health #40185571820](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40185571820) protected exact DEV OIDC read-only; `Microsoft.ResourceHealth/events` for the resource and subscription each returned **0 events and no next page**; `availabilityStatuses/current` was **unavailable**, NOT confirmed healthy. The public Azure status page reported no broad active events. Azure can still have resource-specific unreported faults.

## Environment evidence and limits
- Azure resource configuration from [#40170746627](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40170746627) verified Python 3.12 / 2048MiB / maximumInstanceCount=1; sampled AlwaysReadyUnits=0, *not* a verified configured always-ready HTTP value.
- Earlier Azure Application Insights aggregate worker-start-labeled trace buckets and ResultCode=0 rows **cannot be correlated to a specific failed HTTP request**. Do not claim restarts/crashes based on bucket labels.
- Separate queue-trigger Azure FFmpeg successfully rendered a **private signed 30-second H264/AAC 1080×1920 Reel**, cleanup PASS, [#40136464084](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40136464084). That shows a queue execution path works; it does not prove HTTP ingress.
- Existing HTTP source uses 20-minute functionTimeout (not a configured 60-second execution timeout). Heavy media engine imports were deferred in a deployed ZIP, yet intermittent ingress failures persisted.
- No secret, token, account identifier, shop ID, media URL, raw Azure log or credentials are attached. Protected GitHub Actions logs have a user-authorized access boundary.

## Requested support investigation
Please use platform-only telemetry for the exact UTC timestamp windows to correlate Function App HTTP front end, reverse proxy, instance assignment and demand scaling, trigger group specialization, Functions host readiness, Python 3.12 language-worker initialization and gRPC connection, worker process exits/restarts, and 60-second host/worker startup timeout. Determine whether this is app ZIP/indexing startup time, per-instance HTTP concurrency/one-instance throttling, cold-start assignment, backend response-loss, or platform incident. Why can an unknown route hang without returning 404 and why do adjacent authorized routes respond 401 quickly? Please advise supported read-only diagnostics and root-cause/remediation *before* any paid always-ready or plan migration.

## Cost/risk-controlled experiments — proposals only, NOT executed
1. An isolated **minimal Python v4 HTTP Flex control app in Central India** with same 2048 MiB scale mode; requires reviewed provisioning/deletion plan, metering, resource limits, verification of policy/permissions and a cost ceiling. This is not a test of the existing app if no separate control is created.
2. If engineering evidence specifically implicates cold start, consider a brief **one HTTP always-ready instance** trial under written cost cap and immediate rollback. Pricing includes idle baseline plus execution and log cost: illustrative *non-region/contract-specific* published list meter of **$0.000004 per GB-second** gives a 2 GB idle baseline around **$0.0288/hour**, around **$0.69/day**, or **$20.74/30 days**, before additional execution/meters. Verify exact Central India subscription quote first: https://learn.microsoft.com/azure/azure-functions/pricing .
3. Classic Linux Consumption is not a preferred migration: Linux Consumption retirement is **2028-09-30**, it scales to zero and could retain cold starts; Python 3.12 is the last Linux Consumption Python version: https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale .

**Approval boundaries:** no new paid Function App, no always-ready, plan/configuration resize, deployment, PROD/WineShopPOS changes, JWT/RLS downgrades, replay of uncertain POST/PATCH, or real retailer fixture creation until specific budget/plan and safer E2E preflight. A successful read-only diagnostic does NOT close P0 #249.
