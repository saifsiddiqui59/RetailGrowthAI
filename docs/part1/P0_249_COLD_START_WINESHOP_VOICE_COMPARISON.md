# P0 #249 — Cold-start comparison with WineShopPOS and Voice Agent (2026-10-26)

**Status:** Evidence review only. No deployed remediation, Azure setting, new expense, customer-account action, or Microsoft Support ticket. Issue [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) stays OPEN.

## What is demonstrated in existing RetailGrowthAI DEV

- Existing `rg-retailgrowth-dev / rgai-dev-functions-d4e5ddbd` Central India Python 3.12 **Flex Consumption** app uses 2048 MiB and ARM `maximumInstanceCount=1` **per independently scaling on-demand group**; HTTP concurrency and configured HTTP always-ready count were not returned in the validated allowlist. `AlwaysReadyUnits=0` was an observed metric sample, not the complete configured property.
- All **21 indexed Functions** were found after the code-only deployment that deferred heavy FFmpeg/Pillow imports to queue/timer execution (PR #256; run #40098789883). The original HTTP gateway symptom persisted: anonymous GET returned actual **503 after 60.954 s** despite neighboring correctly authenticated-denial **401 around 0.95 s**. Earlier run #40097206285 observed **503 after 60.806 s**.
- Two separate owner-approved transport matrices #40175539961 and #40176054781 showed **6/8** and **5/8** anonymous requests completing DNS/TCP/TLS but **no first HTTP byte within 20 s** and **no Python `X-Request-ID`**. These 20 s aborts were **client-side 000 timeouts**, not proven Azure 503s. Known and nonexistent GET routes were affected; earlier matrices also captured poster-select POST. The issue cannot be attributed to one application route or GET-specific business logic.
- Independently, Azure Queue + outbox + FFmpeg successfully delivered real private signed 30 s H264/AAC MP4, 1080x1920 (#40136464084). Queue success does **not** establish HTTP-front-door health. Host `functionTimeout` is `00:20:00`, so a 60 s response is not the configured execution-duration limit. Python `function_app.py` still imports several API/storage/worker modules at indexing; eager imports could contribute to cold-start work, but this has **not** been connected to the failing requests.

## Concrete WineShopPOS comparison — read-only source inspection

- `saifsiddiqui59/WineShopPOS/docs/AI_PRODUCTION_BASELINE.md` records a **production** Central India Azure Function `wineshoppos-ai-1a61d5885c` on **legacy Consumption Y1**. Its `azure-functions/ai-owner-assistant/package.json` uses **Node.js / @azure/functions v4**, and `host.json` specifies a **1-minute function execution timeout**.
- Its separate V3 invoice Function also uses Node.js. The WineShopPOS prod baseline reports successful authenticated AI interactions, but **does not show comparable cold-start/first-byte benchmarks under RetailGrowthAI's actual load, runtime, region/subscription, deployment package or scale configuration**.
- **Do not infer** that simply migrating RetailGrowthAI Python Flex to legacy Y1 (also scales to zero) fixes #249. Reusable patterns are clean authenticated API boundaries, small independent functions, server-side Supabase scope and request tracing — not WineShopPOS deployment changes or shared secrets.

## Voice Agent comparison — provenance limitation

- Connected public `saifsiddiqui59/Voice-agent` repository currently contains only a README title, with no verifiable Azure Function, Container App, image, replica, or deployment configuration. Prior operational descriptions of the WebSocket Container App plus Azure Functions cannot establish its *current* cold-start/replica policy.
- Do **not** claim Voice Agent has a proven warm-start architecture, reuse unverified minimum replicas, or change/inspect its production resources to investigate RetailGrowthAI.

## Cold-start hypothesis vs other plausible failure points

Microsoft Azure Functions documents that **both Flex and legacy Consumption scale to zero**, and that Python language-worker startup has a separate **60-second nonconfigurable startup limit**. Flex HTTP has a dedicated per-function scale group; optional always-ready HTTP is billed even when idle. Matching ~60.9 s timings **support testing a startup/readiness path but cannot prove it**. A warm adjacent 401, combined with a stalled unknown route and missing app-level header, also leaves ingress frontend, allocation/recycling, worker gRPC, response routing and host-to-instance handoff in scope.

References:
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale
- https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan
- https://learn.microsoft.com/en-us/azure/azure-functions/event-driven-scaling

## Next action (no additional speculative probing or spend)

1. **External P0 dependency:** authorized subscription owner submits existing sanitized [support-case draft](DEV_FLEX_HTTP_SUPPORT_CASE_DRAFT.md) with exact UTC windows 2026-10-25 **08:10–08:20 UTC**. Request platform ingress -> HTTP-group scale decision -> host assigned/readiness -> Python worker startup/channel correlation, including whether failed calls were first after an idle scale-to-zero versus already warm. The current service log aggregates cannot independently establish a cause.
2. **Only if support evidence is inconclusive and operator approves a specific cap:** propose a *temporary, controlled* minimal Flex Python HTTP-only control app or short `http=1` always-ready comparison, with Central India rate/budget, rollback/deletion plan and no privileged real tenant traffic. Never perform it on this document's authority.
3. After a demonstrated backend correction, require repeated correct direct 401/404 preflights and the protected real signed-in ROOT-approved end-to-end campaign/poster/30 s Reel negative-tenant and cleanup gate. Do not replay uncertain POST/PATCH or bypass JWT/RLS to mask the problem.

**What was not done:** no Microsoft support case filed, live Azure telemetry queried in this comparison, paid scaling, plan migration, code redeploy, WineShopPOS or Voice Agent modification. All quantities above are from existing recorded approved DEV runs/source.
