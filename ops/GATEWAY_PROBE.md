# DEV gateway first-request diagnostics (Part 1)

This is a manual, read-only DEV 502/503/504 sampler and not a fix or an automatic warmup.
It never supplies credentials, real tenant IDs, write requests or request bodies, and does not provision resources.

From the RetailGrowthAI repository with Python 3.13:

    python -m ops.gateway_probe --samples 3 --timeout-seconds 20 --pause-seconds 5

The target is pinned to the existing DEV Azure Function App. Two sentinel-ID GET
routes are probed 1–6 times each; timeout 1–30 seconds, pause 0–30 seconds.
Do not schedule repetitive keep-warm checks without a separate cost/security decision.

An HTTP 401 means the protected route reached its authentication boundary.
A 502/503/504, timeout, or absent X-Request-ID flag is an observation, NOT proof
of Azure cold start or of where the failure originated. The output is aggregate
JSON with no user data, exception strings, header values or response bodies.
An exit code of 3 means the protected routes never reached 401 or an unexpected
response occurred. Exit code 0 may still report degraded=true: inspect that flag.

Correlate the bounded manual sample timestamps with sanitized Application Insights
http.request counts/latency and Azure Functions platform/scale-out metrics.
Preserve Supabase JWT/RLS, idempotent write handling and trial quota controls;
measure costs before any min-replica or always-on workaround. Do not touch
WineShopPOS, GenAI Galaxy, Part 2 platform connectors or Part 3 Wan.
