# Part 1 performance and role regression handoff

Status: source-tested on the Part 1 completion workstream, not deployed. No live
probe, Azure configuration change, hosted database write or paid call was made.

## Diagnostics implementation

`azure-functions/campaign-api/request_diagnostics.py` provides
`RequestDiagnostics(method, path)` and `complete(status_code, payload)`.
Create one instance on HTTP entry and use `complete` when constructing every
response, including malformed JSON and missing configuration. It returns
`Cache-Control: no-store`, `X-Content-Type-Options: nosniff` and a newly generated
server `X-Request-ID`. It logs one structured `http.request` event per instance.

Events contain only a fixed route name, allowlisted method/error code, HTTP
status, duration, outcome and retry advice. Raw paths, URLs, tenant/campaign IDs,
inbound correlation headers, prompts, user identities, exception text, response
bodies and signed media links are excluded. Unknown routes/errors become fixed
`unknown`/`OTHER` labels. Duration is bounded and duplicate completion calls do
not create duplicate telemetry. Existing JWT, RLS and claim checks are unchanged.

For GET/HEAD 502/503/504, the adapter receives `Retry-After: 2` and telemetry
labels the response `bounded_read`. POST/PATCH/PUT/DELETE receive no retry hint;
their advice is `reconcile_first`. This module performs no network retries.
Campaign creation does not have a global client idempotency key: an uncertain
POST response must not be replayed automatically. A renderer's own authoritative
idempotency/lease handling remains intact.

## Integration for the Part 1 lead

1. Import the helper into `function_app.py` and replace the current ad hoc trace,
   timing and `emit('http.request', ...)` with one helper per request. Keep the
   existing JWT-verifying `HTTPAPI.handle` call unchanged.
2. Convert invalid JSON's early `HttpResponse` into the common response path so
   it receives the same headers and telemetry. Existing configuration failures
   remain safe, explicit 503 responses.
3. Merge the helper and tests through `feat/part1-completion`. No public API body
   or schema changes are required. Parent-owned integration tests should use a
   real offline `azure.functions.HttpRequest` with mocked build dependencies.

Source inspection also found that `build_api()` constructs a fresh JWT verifier
and `PyJWKClient` on each request, discarding the configured in-memory 300-second
JWKS cache. The lead may retain the verifier by exact configured HTTPS origin
within a process, bounded to a few entries. Each token must still execute full
signature, issuer, audience, role and expiry verification; membership must never
be cached. This is a measured-source optimization candidate, not a diagnosis of
the actual hosted gateway 503s.

## Verification completed

Local command (using the lead's disposable virtual environment):

```bash
PYTHONPATH=ai-agents/src /path/to/venv/bin/python -m pytest \
  tests/api tests/reliability -q
```

Result: **114 tests passed, 6 subtests passed**. Seven new diagnostics tests and
five new role-journey tests exercise the actual `HTTPAPI`, `RenderAPI` and
`TenantStore` classes with an emulated HTTP transport. Coverage includes OWNER /
EDITOR writes, VIEWER read-only access, normal signed private reads, root not
implying shop membership, foreign tenant denials, membership revocation after a
successful read, a second membership check before job creation, and duplicate
render requests retaining one logical job. They do not prove hosted RLS: the
existing disposable SQL security job remains mandatory.

The parent integration owns four-job CI, frontend/mobile Playwright, actual
poster performance/image tests and disposable Supabase checks. CI status and
merge evidence must be read from GitHub before marking those passed.

## Remaining operational evidence

The existing `ops/gateway_probe.py` already provides a bounded GET-only manual
sampler. Do not add recurring keep-warm calls, min replicas or resource changes
without an approved budget. With separately authorized samples, correlate
observed gateway responses, server-generated `X-Request-ID`, Functions execution
logs and Application Insights dependency/platform timing. A missing header or
first-request delay alone does not establish cold start or gateway origin.

Creative Studio final QA must additionally verify poster worker p50/p95 timing,
bounded input/output bytes, tenant-negative asset/branding reads, stale draft
and day snapshot rejection, render lease/retry races, honest loading/failure
states, mobile download behavior and current campaign regression tests.
