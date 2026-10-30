# Issue #249 — Original Python Flex vs Free SWA Live Read-only HTTP Reliability (2026-10-28)

## Environment and provenance
- Original HTTP backend: Central India Azure Functions **Python Flex Consumption**, resource group `rg-retailgrowth-dev`, application `rgai-dev-functions-d4e5ddbd`; validated via existing GitHub Actions DEV OIDC, account subscription, environment tags, and exact app name.
- Comparison: existing **Free** Azure Static Web Apps managed Node 22 API named preview `https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net`. This is **not** the original Functions app or live customer frontend, and not the complete authenticated retailer E2E.
- Protected live [run #40672031548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672031548) at 2026-10-28 **10:26–10:35 UTC**: diagnostic **FAILED exit 4 by design** because four real HTTP 503s were captured. Exact [PR #494](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/494), [PR CI #40671571499](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40671571499) and independent [main CI #40672031366](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672031366) all **4/4 PASS**. The test used only fixed fake ID/unknown path anonymous GET, no user/JWT/media/AI or write.
- [GitHub issue comment #6466785357](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249#issuecomment-6466785357) contains the precise original live status/timing table.

## Actual per-request results (no fabricated p95/p99)

| Phase / synthetic route | Original Python Flex: HTTP / total / TTFB | Free SWA Node: HTTP / total |
|---|---:|---:|
| initial campaign | 401 / 4.862s / 4.861s (app marker) | 401 / 1.891s |
| initial unknown | **503 / 60.902s / 60.902s** (no marker) | 404 / 0.744s |
| repeat campaign | 401 / 0.989s / 0.989s (app marker) | 401 / 0.742s |
| repeat unknown | **503 / 60.889s / 60.889s** (no marker) | 404 / 0.742s |
| two concurrent campaign #1 | 401 / 0.924s / 0.924s (app marker) | 401 / 0.731s |
| two concurrent campaign #2 | **503 / 60.912s / 60.912s** (no marker) | 401 / 0.748s |
| post-300s-idle campaign | 401 / 4.907s / 4.907s (app marker) | 401 / 0.744s |
| post-300s-idle unknown | **503 / 60.903s / 60.903s** (no marker) | 404 / 0.730s |

- **8 fixed GETs per backend**, 75s max per request, two concurrent per host; all 16 returned a real HTTP code, **0 client timeouts** and **0 network errors**. Four actual original-host **HTTP 503** (all approximately 60.9s), Free SWA **0 HTTP 503**. Expected-response rate: Flex **4/8 (50%)**, SWA **8/8 (100%)**. On directly comparable campaign-auth GETs: Flex **4/5 401**, **1/5 503**; SWA **5/5 401**. Unknown-route 404 can originate at SWA routing, so **not identical application handler evidence**.
- Observed p50 across all completed HTTP codes, **including 503**: Flex **32.898s**, Node **0.743s**. p95 and p99 explicitly **unreported/insufficient sample count**. Treat these as a small bounded snapshot, not a SLA or proof of multi-day production reliability.
- In all four confirmed 503s, DNS/TCP/TLS were already completed; TLS time was **0.657–0.675s**; no Python `X-Request-ID` application marker was present and first byte arrived only with the 503 at ~60.9s. This narrows failure to after transport handshake but **does not prove** where the failure occurred (ingress dispatch, cold activation, host assignment, worker startup/gRPC, or another gateway dependency). Five-minute inactivity does not prove scale-to-zero; warm/concurrent failures refute a purely first-cold-request explanation.

## Telemetry, diagnosis, and safe follow-up
- Existing historic read-only [ARM/scale diagnostic #40170746627](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40170746627) found Python 3.12, 2048MB per instance, maximum on-demand instance count 1 and sampled AlwaysReadyUnits=0. Historic Log Analytics aggregate evidence [#40176054781](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40176054781) recorded worker start and request buckets without causal per-request matching. Earlier two distinct original-host **HTTP503** at **60.806s** [#40097206285](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40097206285) and **60.954s** [#40098789883](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40098789883); separate 2026-10-28 Feature2 signed [#40659456731](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40659456731) also saw ~60s 503.
- New run's optional read-only Azure metric-definition poststep encountered a **reporting parser defect**: Azure CLI returned **list** but inline Python assumed `{value:[...]}`, producing `AttributeError: 'list' object has no attribute 'get'`. This is not an Azure service/host failure, and **no new timestamp-correlated platform metric or App Insights proof was gathered in this run**. A safe source/test parser correction accepts both shapes; not retrospectively claimed executed as a fresh cloud diagnostic.
- **Confirmed problem:** intermittent original Python Flex HTTP ingress unreliability and ~60.9s 503. **Root cause:** UNKNOWN. No source/host setting fix is justified solely by this correlation. Existing poster/Reel JavaScript name-collision defect is independently fixed on Node and does not fix the Python Flex issue.
- **Next:** using existing DEV-only protected read-only access, inspect timestamp-correlated 2026-10-28 **10:26–10:35 UTC** and earlier **08:49–08:51**, **09:40–09:46** Functions host startup/worker gRPC, Azure ingress/scale/restarts, Application Insights and storage dependencies, with sanitized aggregated output only. Check whether 503s have matching host/request traces; unavailable telemetry must be labeled unavailable, not clean.
- If a specific cause is confirmed, propose the smallest safe source-only fix with regression, four CI jobs, PR/merge, and post-release live validation under existing authorization; **no speculative always-ready, paid new plan, instance scaling, DB privileges, PROD or WineShopPOS**.
- Before closing #249: repeat first/warm/idle and bounded-concurrent comparative probes over more cycles with adequate sample for p95/p99; complete explicit separately approved ROOT/OWNER/EDITOR/VIEWER and second-shop negative/positive signed-user routes; actual rights-owned private asset→poster PNG→durable banner select→queued **30s 1080x1920 H264/AAC** Python FFmpeg Reel→private signed-download and cleanup, including quota/outbox/idempotency. Keep Python workers and customer frontend unchanged until acceptance.

**Decision: #249 must remain OPEN.** No new Azure resource, Azure configuration, customer data mutation, paid AI/GPU call, subscription change or WineShopPOS/PROD modification occurred in this test.
