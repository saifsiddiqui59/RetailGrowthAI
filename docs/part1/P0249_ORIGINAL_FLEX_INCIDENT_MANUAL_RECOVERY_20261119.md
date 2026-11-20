# Issue #249 — manual-only original Flex gateway incident correlation

**Source prepared; no Azure/log query was dispatched in this PR.**

This recovery starts from current main and rescues the useful two files of
old conflicted [#887](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/887).
The unchanged source collector `ops/p0_249_recent_http_platform_readonly.py`
was verified to exist **byte-for-byte already on main** (Git blob
`6aefe12004852926cd16f32c500c03c14876a7e9`).

## Read-only fixed windows and approval
- The workflow is strictly `workflow_dispatch` only on `main` with
  `YES-P0249-FLEX-INCIDENT-READONLY`, protected `dev` environment,
  repository identity check and Azure OIDC scoped to the existing DEV
  subscription. No push, schedule, token logging or Azure app mutation.
- The existing collector fixes its **four historical known incident time
  windows** and three host/request/activity classifications. It requests
  bounded Azure Monitor summaries, redacts raw Kusto log text and emits
  sanitized categories only. It does NOT create new observations for the
  latest date, and old windows cannot establish the current Flex health.
- The job validates the exact static Kusto source query/window shape and
  collector compilation before any Azure login. All intended modifications
  require independent shared-workflow/security review. CI is offline only.
- Separate live hosted Y1 two-route negative-auth evidence
  [#42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296)
  does NOT resolve original FC1 markerless 503 nor signed multi-shop RLS.
  No Y1 route deployment, Auth, private media, SQL, GPU, paid provider,
  PROD or WineShopPOS change occurs here.

## Later acceptance (not performed here)
The original #249 closure still needs timestamped live original Flex host
diagnostics, measured p95/p99 signed POST/PATCH/private media paths,
cross-tenant denial and carefully approved rollback/cutover review.
A historical read-only incident query can narrow a host-side hypothesis;
it is **not** a fix or an automatic cloud diagnostic.

## 2026-11-20 protected actual diagnostic results (not a fix)
- The manually protected fixed-window collector was launched once by the owner-delegated one-shot GitHub bridge [#44761572109](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44761572109), after exact main Part1 CI [#44761572161](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44761572161) 4/4. The protected [original Flex diagnostic #44762122469](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44762122469) completed SUCCESS in DEV and only performed read-only Azure Monitor aggregated queries. All source filters and immutable incident windows preserved, no raw messages/request paths printed.
- Per Nov 5, 6, 7, 8 fixed window: host/start events **15, 30, 39, 24** respectively; only host_start and worker_start classes, **108 total**. AppRequests aggregates **12, 7, 13, 9** respectively; 401 counts **2, 2, 2, 4**, total **10**, and **0 reported_503** (not evidence client never received gateway 503). AzureActivity **NO_MATCHING_EVIDENCE** all four. No drain_mode, listener_stop or specialization timeout was returned by these filters. Aggregated timing alone does not demonstrate a causal platform failure.
- A cold/restarting worker or 503 occurring before the application handler is a candidate, not a confirmed root cause or issue closure. Obtain timestamp-correlated fresh current client-side 503 plus gateway/host lifecycle evidence, p95/p99 and signed multi-shop original endpoint/mutation tests before decisions. One-shot bridge is retired; permanent protected manual diagnostic remains source-only pending any new owner-controlled manual dispatch.
