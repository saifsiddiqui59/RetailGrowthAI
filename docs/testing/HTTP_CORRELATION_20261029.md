# Testing Chat — HTTP correlation handoff (2026-10-29)

## Why
The existing Azure Functions HTTP adapter already emits a randomized server
`X-Request-ID` via `request_diagnostics.py` and writes a sanitized
`http.request` log entry without retailer IDs or secrets. Previous Testing
Chat receipts had browser timings and resource IDs but no reliable correlation
key for that existing server diagnostic.

## Additive implementation
- `frontend/src/lib/feature-http-receipt.mjs` allowlists source, method,
  a UUID-redacted route, HTTP status, bounded browser duration and attempt
  number. It accepts `X-Request-ID` only as exactly 32 hex characters,
  otherwise `null`. It never records Authorization, cookies, response
  body, signed private URLs, user email, shop UUID or unredacted path.
- `createCampaignApi` and `createTrendApi` gain optional `onResponse`;
  existing callers are unchanged. A throwing telemetry callback cannot change
  a real request outcome. Every received GET retry has an individual receipt.
  An ambiguous POST is **never retried** to get a correlation marker.
- Testing Chat collects these events only while an authenticated test is
  actively executing and appends at most eight new sanitized HTTP observations
  to the next private feature event, retaining the existing tenant JWT and
  append-only storage boundary. The callback is informational and not an
  authorizing token.
- Node regressions exercise marker acceptance/rejection, URL/UUID/bearer
  redaction, optional callback failure, Feature2 and campaign route scoping,
  and the two GET retries without replaying a mutation.

## Interpretation
- **Marker present:** browser received a syntactically valid correlation ID,
  claimed in the HTTP response header. The existing server code creates this
  value on an executed dispatch path; it may support investigation by joining
  to legitimate Azure logs with independent server evidence.
- **Marker missing:** client did not observe the header. This alone cannot
  prove a gateway/pre-handler 503: a proxy could strip headers, CORS could hide
  the header, a transport could fail, or the HTTP response could originate
  elsewhere. Do NOT assert #249 root cause from this datum.
- The browser is not a trusted service and can falsify receipts. Future
  authoritative worker spans require service-role writes to a separate
  protected table and audited tenant/lease/output checks.
- The upstream server must include `Access-Control-Expose-Headers:
  X-Request-ID` when the client origin is cross-origin; otherwise frontend
  JavaScript may see a `null` marker even when a server header exists.
  Do not silently change the live HTTP CORS or Azure config in this source PR.

## Deployment boundary
Source only; no hosted Azure/Supabase writes. Feature3/5/7 remain NOT_RUN in
this first orchestrated test path. DEV `feature_test_runs` and
`feature_test_events` are not installed, so no real hosted receipt is claimed.
Current unresolved Azure issue #249 and protected real two-tenant acceptance
are separate gates. No GPU/provider spend, PROD or WineShopPOS change.
