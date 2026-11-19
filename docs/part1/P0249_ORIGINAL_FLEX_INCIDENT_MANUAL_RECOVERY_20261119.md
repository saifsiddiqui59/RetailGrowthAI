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
