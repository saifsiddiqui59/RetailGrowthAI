# Issue #249 — batched independent source work and staged acceptance (2026-10-30)

Status: source work for coordinator review; **original Azure Functions Flex 503 is NOT resolved**.

## Independent changes in this single PR

1. Historical read-only Azure Kusto postmortem: retain all 80 **aggregated** rows allowed by the inspector's own `take 80` queries. The old generic helper silently truncated these results at 30, including possible later worker/instance signals. Limit to 80, redact all values except fixed classes, timestamp buckets, bounded counters and hashed instance IDs. No raw log content or token output; keep the original 30-row generic helper untouched.
2. Older 6-GET synthetic smoke: require 401 *only* on the actual campaign route with a nonempty **final response** `X-Request-ID`; require 404 *only* on the intentionally unknown route. Proxy CONNECT/interim headers and wrong-route 404s cannot falsely pass. Six fixed no-auth GETs; no new remote probes or writes.
3. Offline deterministic negative tests: Azure list/value/table 31st–80th rows, bad shapes, no raw log text; mocked curl headers and wrong status/route; no credentials, no external network or media.

## Parallel and integration policy

Issue #249 lead may complete read-only telemetry analysis and six-GET probe fixes independently of Features #2/#3/#4/#5/#7. Read the existing `coordination/shared_feature_references.json` for fixture inputs only; it never supplies production JWT, ROOT permission or signed media acceptance. The independent Node JWT/canary source work remains in PRs #679/#692; coordinator handles those merges and conflicts. For speed, group unrelated owned source changes into one reviewed PR commit and run targeted checks before **one final 4-job exact-head CI** rather than restarting full CI after every individual task. Do not postpone all checks until after risky production actions; after merge a fresh main 4/4 remains required.

Real acceptance sequencing, with explicit operator approval: (a) resolve actual Azure gateway/platform request correlation and original 503; (b) ROOT-authenticated two temporary signed tenants and negative RLS/roles; (c) genuine private PNG and 30-second H.264/AAC MP4 readback/rights/cleanup. Neither source-only fixture nor a green CI closes #249. Keep GPU/paid calls OFF, no PROD/WineShopPOS modifications or unsigned JWT shortcuts.

## Tracking for coordinator

Both sub-tasks are **SOURCE PROPOSED** pending this PR's exact-head tests, review, merge and postmerge CI. The Azure ingress→HTTP scale-group→worker causal trace is **BLOCKED** on platform-side evidence `AZURE_INTERNAL_TRACE_REQUIRED`; the ROOT-gated signed live canary remains **BLOCKED** on human review/dependent merged PRs. Do not mark a source proposal as integrated DONE.

## Follow-up batched fix: temporal incident evidence and public telemetry safety

- The prior startup-versus-auth401 indicator joined **all** 401 responses on a host-instance over the entire incident window; a 401 *before* worker startup or many minutes afterward falsely implied nearby readiness. Restrict aggregate evidence to the same instance and at most 120 seconds **after** each worker start using Kusto datetime comparisons, and deduplicate per instance/start timestamp before counting. This is still *not* ingress→worker per-request causal proof and never establishes a fixed original 503.
- Historical telemetry redaction now allows only numeric finite nonnegative bounded metrics, bounded nonnegative integer event counts, exact UTC timestamp shapes on the fixed investigation date, trusted status categories and boolean dependency success. Never print a malicious timestamp suffix or NaN/Infinity as if valid JSON. Preserve all fixed DEV scopes and no-cloud-write boundaries.
- Offline negative checks cover the temporal join guard, timestamp smuggling, nonfinite numbers, true/false dependency receipt and metric whitelists. Scope remains source-only awaiting exact-head four-job CI, coordinator review/merge and fresh main four-job CI.

## 2026-10-31 — Azure whole-minute fractional timestamp continuation

- Existing historical platform sanitizer used a strict minute bucket string that accepted `2026-10-28T19:40:00Z` but **dropped** equivalent Azure/Kusto serialized whole-minute `2026-10-28T19:40:00.0000000Z` (also `+00:00`), potentially reporting actual bounded aggregated evidence as `EMPTY_OR_FILTERED`. This is an **offline evidence completeness bug**, not the original Functions gateway 503 root cause.
- Extend only the existing fixed-day, minute-aligned `BUCKET` allowlist to accept one through seven **zero** fractional seconds; still refuse nonzero fractions, excess precision, non-UTC, wrong day and arbitrary trailing private data. Do not change historical Kusto scopes, host settings, credentials, cloud cost or customer requests.
- Add `test_azure_minute_bucket_zero_fraction_is_retained_without_private_suffixes` for positive/negative actual sanitizer output; existing 80-row and caller safety checks remain.
- **Status: SOURCE PROPOSED**, not integrated DONE. Verify targeted Python test, full exact-head four-job PR CI, independent review and fresh main four-job CI; Azure ingress→scale-group→worker request causation `AZURE_INTERNAL_TRACE_REQUIRED`, protected two-shop signed PNG/MP4 canary and measured hosted p95/p99 remain BLOCKED.

## 2026-10-31 — Malformed optional Azure cells must not suppress safe evidence

- **Source bug:** `safe_rows` previously checked `category in CATEGORIES` without requiring a string. An Azure result containing an unhashable `category` list/dict raised `TypeError`; `collect()` then labeled the whole fixed-window query `UNAVAILABLE` and suppressed otherwise well-formed aggregate counts, timestamp buckets and later rows. Similarly, a lone Unicode surrogate in an optional worker `instance` would raise `UnicodeEncodeError` when hashing, dropping the query.
- **Bounded fix:** Accept only allowlisted **string** categories; reject malformed optional worker identity before publishing any digest. Do not print original category, raw host ID, messages, request identifiers, credentials or dynamic fields. Preserve independent valid aggregate counts/buckets and continue sanitizing later rows. The query scope, 80-row bound, fixed UTC windows, host/worker speculation guard, and read-only Azure calls are unchanged.
- **Regression:** `test_malformed_telemetry_cells_retain_valid_aggregate_evidence` exercises list/dict categories, malformed Unicode instance, intact valid counts/known class, stable hashed legitimate identity and privacy denial.
- **Status:** SOURCE PROPOSED until final exact-head four-job CI, independent review, safe merge and fresh main 4/4. Original ~61-second unmarked Azure gateway HTTP 503, platform request-to-worker causality, and approved signed 2-shop PNG/MP4 + latency acceptance remain BLOCKED. No DEV/PROD deployment, hosted database, GPU/provider, paid call, ROOT approval or WineShopPOS modification.
