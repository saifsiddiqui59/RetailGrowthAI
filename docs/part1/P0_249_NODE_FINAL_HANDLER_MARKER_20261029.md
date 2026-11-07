# Issue #249 — Final-response Node handler marker evidence gate (2026-10-29)

## What source inspection found
The existing anonymous Flex-vs-Free-SWA HTTP probes counted any HTTP 401 from the Node candidate as a **verified** handler response. Unlike Python (which required `X-Request-ID`), Node did not require the existing `X-RGAI-Secure-Adapter: candidate-v1` marker. A synthetic 401 emitted by proxy, edge, wrong route, or fallback could therefore pass the 20/20 Node handler gate without reaching the secure dispatcher. **This is a test-evidence classification bug, not proof that the live Node candidate is broken.**

## Source-only correction
- `ops/p0_249_http_comparison_probe.py` parses only the final HTTP header block, avoiding mistaken acceptance of a proxy CONNECT/1xx marker. It records only booleans for the original Python request marker and the exact Node adapter marker, never token/header/body/request-ID contents.
- The existing two backends and two synthetic GET paths, 75-second deadline, idle delay, no mutation, capped concurrency and metrics are unchanged.
- `ops/p0_249_powered_equal_route_probe.py` verifies Node 401 only if the **exact final Node handler marker** exists. Old marker-less 401 data cannot retroactively satisfy this stricter gate. Unmarked 401 is explicitly `UNMARKED_401_NOT_PROVEN_HANDLER`.
- Offline regression tests use fake response headers: legitimate Python and Node markers, wrong node values, proxy preamble containing both markers, empty Python ID, missing header block, and 20 generic unmarked Node HTTP401 results.

## Acceptance and deferred dependencies
This fixes a classification false-positive in **source only**. Exact-head 4/4 CI and coordinator-only merge with fresh main CI required. No real HTTP probe, Azure setting change, external paid service, real user JWT, ROOT approval, hosted poster/30-second MP4 or customer cutover was made by this patch. To close N09/N12 still require independently authorized first/warm/idle/concurrent signed DEV runs (meaningful p95 and adequately sampled p99), two-shop OWNER/VIEWER/revoked/foreign rights and media/output acceptance, and original internal Azure ingress→HTTP-group→worker causal trace (`AZURE_INTERNAL_TRACE_REQUIRED`). Original #249 unmarked ~61-second Python Flex 503 remains **unresolved**.

## Coordinator record update proposal
After reviewing the isolated PR and observing the **exact** final CI run, coordinator append this finding to `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md`, and update shared task manager status for #249 (source correctness, NOT hosted issue DONE). Do not overwrite concurrent Feature3/coordination document additions.

## Additional 16-GET gate correction
The legacy comparison `run_series()` also considered any raw **401** from a *nonexistent campaign route* or generic **404** from the *campaign API route* acceptable, as long as it was not 503/UNEXPECTED. A broken Node route with generic 404, or a proxy-issued 401, could therefore make the legacy CLI exit 0. The new source requires each of the 16 fixed synthetic requests to match its exact **backend + phase + route** and outcome: campaign must yield **application-marked 401** (Python nonempty final `X-Request-ID`, Node exact final `candidate-v1`); nonexistent path must yield 404 and remains only routing-negative evidence, *not* handler attestation. No response body/credential is stored and no mutation retries exist.

The summary now keeps raw `success_rate_http_percent` for **HTTP transport observations only**, and separately emits `verified_campaign_handler_401`, `campaign_samples` and `verified_campaign_handler_rate_percent`. A 100% transport 401/404 rate with 0 marked campaign handlers is explicitly a **failure**, not a Node readiness win. New mocked sender tests cover all 16 GETs, 503, mismatched target, unmarked campaign, and zero false verified success. Source CI and real approved hosted acceptance remain separate.
