# Azure Issue #249 — Azure Portal diagnostic visibility check (2026-10-28)

**Status:** READ-ONLY PRELIMINARY DIAGNOSTIC ONLY; **NOT** a validated 503 root cause or a fixed deployment. Issue #249 remains **OPEN**. Rejected import-isolation PR #568 is **CLOSED UNMERGED** (it retained a GitHub draft flag; it is not an open draft PR).

## Context and original authoritative failure

The previous protected original Azure DEV lazy-import candidate [#40755301253](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40755301253) yielded **9/20 real unmarked ~61s HTTP503** vs the independent Free SWA Node facade **0/20**, then restored a reviewed baseline *source ZIP*, not byte-for-byte prior deployment. Separate protected AppInsights [#40768869977](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40768869977) recorded **11 marked application 401, 14 missing/zero status AppRequests and zero application-marked 503** in the incident window; **3/25 worker starts** could be linked to an HTTP401-serving instance, but 22 are unclassified because other Flex Queue/Timer trigger groups scale separately. None of these counts tie an individual failed client request to a gateway/HTTP-group host.

## New Azure Portal read-only navigation

- Source: [visible browser session — Azure Portal read-only run](https://agent.tinyfish.ai/runs/b4216d61-275b-4324-85d1-6e83ea3adfa2).
- Target: existing **rg-retailgrowth-dev / rgai-dev-functions-d4e5ddbd**, Central India; visited **Diagnose and solve problems** and **Function App Down or Reporting Errors**. No app configuration, deployment, paid instances, resource groups, credentials, traffic routing, customer state or data were changed.
- The portal summary presented **three observation/solution topics**: an **\"Functions runtime is unreachable\"** warning; **\"HTTP errors on HTTP Triggered Function\"** guidance discussing HTTP **502 and 429**; and an **extension-version range** advisory. It showed **Function App Offline History** and **Deployment Settings** as passed among seven successful checks.
- **Critical qualification:** The portal run did **NOT** successfully apply the original exact **2026-10-28 19:35–19:51 UTC** canary and **19:59–20:02 UTC** rollback windows. It inspected the portal's **default Last 24 Hours**, and the 502/429 text may be generic diagnostic guidance rather than observed event counts. The runtime warning may not concern the specific failing requests. It is **incorrect to infer** an HTTP429/502/worker/reachability causal explanation for the actual 9 client-side 503 responses from this display.
- No request-level **gateway 503 -> HTTP scale-group instance -> host specialization / Python gRPC worker** correlation was visible in this initial portal diagnostic. The Python Function diagnostic topic was not examined. This does not prove absence of the issue; the exact-time portal view remains unexamined.

## Next P0: evidence required, no speculative code changes

1. Reopen the existing DEV Function App's **Diagnose and solve problems > Function App Down or Reporting Errors (Preview)**. Apply **Custom UTC 2026-10-28 19:35–19:51** and independently **19:59–20:02** (not Last 24 Hours). Check runtime reachability, Function Execution and Errors, Python Function and instance/specialization/worker views; report only sanitized categories/counts and whether original HTTP 503 requests can be linked to a specific ingress/HTTP scale-group instance/worker event.
2. If the portal cannot reveal a request-to-host binding, keep the explicit blocker **AZURE_INTERNAL_TRACE_REQUIRED**. A generic 502/429 advisory, normal host init, absent AppInsights 503, or empty ARM detector is **not** proof of a cause. No support ticket per current owner instruction.
3. After **causal** evidence, propose a minimally-scoped, reversible, cost-neutral DEV fix. Require **four CI jobs**, original Azure protected real HTTP 20+ first/warm/idle/concurrent retest (failure-free target and measured p95; p99 requires adequate sample size), plus separately authorized real signed two-shop tenant/media acceptance. Do not equate Node preview results or offline CI with a fixed original Functions backend.

**Invariants:** original JWT/RLS, no POST/PATCH replay, existing Python Queue/FFmpeg and app boundaries unchanged; no paid Azure/SKU/AlwaysReady/concurrency change, no PROD or WineShopPOS change, no customer cutover. No Azure deployment or 503 repair claimed by this document.

Official Microsoft references: [Troubleshoot Functions app down or reporting errors](https://learn.microsoft.com/en-us/troubleshoot/azure/azure-functions/availability/functions-troubleshoot-issues), [Flex diagnostics and host telemetry](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-how-to), [Microsoft.Web detector REST](https://learn.microsoft.com/en-us/rest/api/appservice/diagnostics/list-site-detector-responses?view=rest-appservice-2024-11-01).

## Source-only follow-up on extension advisory

Checked the exact current-main **source** file [azure-functions/campaign-api/host.json](../../azure-functions/campaign-api/host.json): the extensionBundle version is **[4.0.0, 5.0.0)**, the **official Microsoft-supported 4.x version range** (not a hard pin to one package version). Microsoft recommends this same range in [Extension Bundles guidance](https://learn.microsoft.com/en-us/azure/azure-functions/extension-bundles). Therefore the generic portal *Avoid Pinning* advisory alone is **not a reason to change source host.json**. **The installed version in the original Azure deployed package was not independently verified** by this read-only source check. No bundle change/deployment was made.
