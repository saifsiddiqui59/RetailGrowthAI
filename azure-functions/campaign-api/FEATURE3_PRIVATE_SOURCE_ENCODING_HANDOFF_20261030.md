# Feature #3 private source transport encoding guard — 2026-10-30

Original task IDs: **F3-03** (trusted original-byte source verifier), **F3-13** (negative source/rights regressions). These remain **IN PROGRESS** for hosted acceptance; this is a distinct offline source-hardening batch, not a new completed hosted package.

Base main: `a75f9df62451dbc701633782a9baf1b16e32c8c8`. Existing open Feature3 branches/PRs were inspected before this change; no shared contract, existing PR, task registry or canonical coordinator file was edited.

The backend private Storage source verifier now fails closed on any `Content-Encoding` other than explicit `identity` or absence. Encoded/intermediary-transformed response bytes must not be mistaken for exact registered original bytes even if a transport adapter decodes them before the original SHA and independent rights check. Offline test doubles cover gzip, br, deflate, malformed/multi-value and identity controls; no actual retailer rights or hosted bytes are asserted.

**Verification:** GitHub Actions exact-head four-job CI is required; tests are not claimed passed until inspected. Coordinator only may merge and update `coordination/task_progress.json`. No source-only result is integrated DONE until reviewed merge and fresh main 4/4.

**Remaining blockers:** F3-LICENSED-MEDIA (Feature3/authorized customer: independently approved current original, likeness and commercial rights); #471/#325 (coordinator/Feature3: mounted signed no-URL output route, real tenant/rights denials); #249 (Azure reliability: live DEV gateway stability); approved one-shot provider/queue ACK and genuine signed DEV negative tests (Feature3/coordinator). Acceptance requires actual current licensed media, signed hosted rights checks and accepted main integration. No inference, GPU, paid provider, Azure queue mutation, SQL, PROD or WineShopPOS was used.
