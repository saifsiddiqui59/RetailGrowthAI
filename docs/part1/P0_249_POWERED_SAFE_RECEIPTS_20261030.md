# P0 Issue #249 — 20-per-backend anonymous probe safe receipts (2026-10-30)

**Scope:** Existing Python Azure Flex DEV versus existing Free SWA DEV candidate; one 20-per-backend fixed synthetic campaign GET run. This is a SOURCE-ONLY diagnostic hardening handoff, not original Azure gateway 503 remediation or production authorization.

## Fixed evidence risk

Previously the 20-sample script printed the complete `sender()` observation. Any future sender adding an authorization token, private download URL, raw response body, cookie or request ID would leak that field into Actions logs. Malformed numerical observations (NaN/Infinity/negative/excessive elapsed times or strings) could also pollute p95 and falsely certify a handler. All evidence now passes through `public_receipt()`, whose output is limited to fixed backend/route/phase, exact UTC timestamp, whitelisted HTTP status and category, bounded numeric CURL exit/timing, boolean final-response marker presence and controlled sequence. Unknown keys are silently discarded, not echoed. Malformed required fields become `INVALID_OBSERVATION` with nonzero exit and no marker; acceptance and percentiles fail closed. Bounded curl timeouts remain distinguished from HTTP 503.

## Deterministic offline proof

`tests/infra/test_p0_249_powered_equal_route_probe.py` covers 40 output receipts with malicious injected fields, missing/invalid timestamp and HTTP status, non-boolean marker, wrong category, nonfinite/tampered elapsed times, and valid curl timeout classification. The original exact 20-per-backend schedule and max 2 concurrent GETs per backend, five-minute unproven idle, and no retry/write rule remain intact. No customer/shop JWT, media or user-approved login is used.

## Integration and real-host acceptance

Maintainer PR #692 head `054e98772688b0f42bee46035cad947b884f0274` has exact-head source CI [#41058133740](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41058133740) **4/4 SUCCESS** (Python 971 tests and 469 subtests). This file's addition needs the new final exact-head CI and independent **postmerge main 4/4**; only the coordinator may merge and mark integrated DONE. The actual original ~61-second unmarked Azure Functions Flex 503, Azure gateway→instance correlation, and signed ROOT-approved two-tenant private PNG + 30s MP4 acceptance remain OPEN/BLOCKED. No Azure config/release, PROD, GPU, paid inference or WineShopPOS changes.
