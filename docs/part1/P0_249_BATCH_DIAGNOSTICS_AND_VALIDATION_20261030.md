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
