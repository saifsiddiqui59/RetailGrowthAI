# Issue #249 — WineShopPOS-style Node HTTP facade migration tasks (2026-10-29)

**Scope:** Reuse the existing RetailGrowthAI `experiments/secure-node-http/` Node 22 Free SWA managed-API *DEV candidate* and the current Supabase user JWT/RLS RPC/outbox, while keeping the original Python Functions Queue/Timer + FFmpeg rendering authoritative. No access to or modification of WineShopPOS or Voice Agent deployments. This is not a Python Flex 503 root-cause fix.

**Observed baseline:** original Python Flex Central India HTTP 9/20 genuine unmarked ~61s 503; same experiment Node synthetic 0/20 expected 401; neither is proof of authenticated production-like parity. See `P0_249_20261028_HTTP_INGRESS_ATTRIBUTION_VERDICT.md`.

| ID | Scope | Acceptance | State |
|---|---|---|---|
| N01 | Compare WineShopPOS/Voice HTTP design and existing Node candidate | Read-only current source review, do not assume Voice has a deployed runtime | DONE |
| N02 | Inventory Node route contract vs original Python | Seven GETs and six POST/PATCH candidate methods at fixed `/api` paths; ensure Python Queue/FFmpeg stays intact | SOURCE CHECKED; full signed parity NOT PROVED |
| N03 | Verify JWT + Supabase tenant isolation in candidate | Node JWKS ES256/RS256, user JWT/current RLS checks, OWNER/EDITOR/VIEWER/foreign/revoked and media rights negative gates | SOURCE TESTS EXIST; live roles gate PENDING |
| N04 | Build frontend Node transport adapter | Exact source-reviewed `p0249writes` preview origin, same-origin document, explicit build flag, custom independently verified JWT transport only, default Python unchanged | THIS BRANCH (SOURCE) |
| N05 | Test browser→Node request shape with mock dispatcher | Exact 13 public v1 methods; no auth cookie/service key; Node request `x-rgai-supabase-jwt` and unchanged JSON; no silent redirect | THIS BRANCH (OFFLINE TESTS) |
| N06 | Verify contract parity of all real read/write routes | Signed actual campaign create, DRAFT save, poster create/render/select, Reel submit/status and private downloads | EXISTING SOURCE PARTIAL; positive hosted E2E PENDING |
| N07 | Validate durable jobs, billing and mutation uncertainty | Existing user-RLS RPC quotas, same-transaction outbox, CAS/leases, at most one mutation; no replay after lost 503 | OFFLINE NEGATIVE TESTS; live behavior PENDING |
| N08 | Protected actual signed-in two-shop DEV canary | Normal ROOT approval within timed window; fresh two shops, real private PNG, 30s H264/AAC FFprobe, foreign/VIEWER deny, cleanup | BLOCKED BY OWNER ROOT INTERACTIVE AUTH + DISPATCH |
| N09 | Reliability/head-to-head HTTP comparison | 20+ measured first/warm/idle/concurrent routes for current Python and isolated Node; separate application vs gateway 503, p95/p99 | BLOCKED BY AUTHORIZED LIVE TEST + ORIGINAL AZURE DIAGNOSTICS |
| N10 | Reversible DEV API cutover | Reviewed deployment of full frontend onto same Node preview for same-origin JWT; verified exact deployment SHA, no customer cutover; rollback by deleting preview or restoring Python origin | PENDING COORDINATOR/OWNER APPROVAL |
| N11 | Coordinator PR merge and postmerge CI | 4/4 exact-head PR jobs, coordinator-owned merge only, independent 4/4 main jobs | PENDING |
| N12 | Issue #249 closure | Retire original unmarked 503 based on causal Azure evidence or explicitly approved reliable replacement; real tenant/media parity proven, no paid surprise | BLOCKED; issue OPEN |

## First implementation: fail-closed frontend transport

`frontend/src/features/campaigns/campaign-api.mjs` supports `transport:'node-preview'` only when both the configured API origin AND the actual browser document origin exactly match the pinned existing Free SWA `p0249writes` hostname. It sends the current Supabase JWT in `x-rgai-supabase-jwt` solely to that same origin, with no `Authorization`, credentials, cookies, redirects or service-role key. The Node gateway independently checks cryptographic signature and caller RLS; the header is not proof of authorization by itself.

`CampaignDashboard.jsx` only selects this mode when `VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'` at **build time**; otherwise it uses the unchanged Python `VITE_CAMPAIGN_API_BASE_URL`. Production .env stays unchanged; no toggle via URL/localStorage/query or redirect; build with a different host fails closed before requesting a token. The current `p0249writes` preview does not contain the full retailer SPA and **must not** be treated as a ready-to-use live website. Coordinator must first build and deploy the reviewed full SPA to that *same exact* isolated named preview before enabling the flag.

Existing safe GET-only bounded retries continue, but the Node preview deliberately disables the Python 503 direct-Supabase-render-read fallback so live gateway comparisons cannot be hidden. POST/PATCH are one-shot only; an uncertain ACK fails and must be reconciled by authenticated read before further action.

## Release / cost / security boundaries

- Do **not** modify `frontend/.env.production`, existing Free SWA production environment, `VITE_CAMPAIGN_API_BASE_URL`, Python HTTP endpoint, SUPABASE schema, Azure queue/worker, billed plans, WineShopPOS or Voice.
- The current Node DEV preview has synthetic/negative and some genuine signed-in tests, but **not** a complete ROOT-approved private campaign/poster/30s Reel happy path. Do not direct customer traffic or assume Node 0/20 synthetic 503 proves parity.
- Only the coordinator may alter `.github/workflows/**`, shared interfaces, integrate `main` or approve actual deployment. An owner/operator must explicitly authorize a protected DEV canary and perform real ROOT UI approval; never impersonate ROOT or embed credentials.
- Keep Issue #249 open and preserve `AZURE_INTERNAL_TRACE_REQUIRED` for original Python Flex ingress→scale→worker causal trace. A working replacement route does not explain the original 503.


## 2026-10-29 continued — independent code vs exact external dependency ledger

Source-only evidence: `tests/frontend/p0249-node-full-route-dispatch.test.mjs` drives **all 13** browser campaign/poster/Reel methods through the existing actual Node `createSecureHttpDispatcher` with synthetic JWT and mocked downstream handlers, checks original path/verb/JSON and no header/token cross-origin forwarding; checks 401/403/404/409/402/429 single-write denials. Test fixtures are **not** AI output, approved commercial media, hosted JWT or release acceptance. No need to wait for Features #2/#3/#4/#5 to provide genuine production artifacts to run source tests.

Playwright attempt: launched installed headless Chromium against the existing DEV Static Web App HTTPS login host; navigation failed **before** a page load with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. No credentials submitted, browser login, authenticated session, Azure deployment, ROOT decision or mutation. The isolated Node `p0249writes` preview is still a placeholder and does not itself provide the full retailer login SPA. Protected canary also requires a separate approved owner-dispatched workflow. Do not copy credentials into repo, CI variables, logs or fixtures.

| Dependency ID | Blocked task | Owning workstream | Required artifact / input | Acceptance / unblock proof |
|---|---|---|---|---|
| DEP-249-BROWSER-DEV | N08 actual Playwright login | Issue #249 DEV operator/environment | Network-reachable existing approved RetailGrowthAI **DEV** SPA and a real owner-authenticated browser; no reuse of WineShopPOS or PROD | Actual app login page loads, current user JWT verified, role/current shop established; safely record redacted evidence only |
| DEP-249-PREVIEW-SPA | N08/N10 Node browser flow | Issue #249 + shared coordinator | Reviewed full RetailGrowthAI SPA build mounted at **same** existing `p0249writes` hostname with opt-in transport flag and existing isolated Node handlers; coordinator-only deployment workflow | Signed session works same-origin; exact deployed SHA and rollback source recorded; customer Python origin unchanged |
| DEP-249-ROOT-APPROVAL | N08 two-shop positive canary | Feature #1 ROOT onboarding + Issue #249 operator | Explicitly approved protected manual DEV canary; two unique disposable retailer accounts; operator applies genuine ROOT approval before window closes | Both exact pending account IDs approved once by authenticated ROOT, actual signed user sessions, private two-shop negatives and finally cleanup PASS; PR #639 remains a separate pending source integration |
| DEP-249-POSTER-REAL | N06/N08 poster flow | Feature #3 Poster Studio | Existing legitimate test original owned/source-rights asset, applied current DEV poster RPC/migrations and working private PNG output from CPU renderer (no GPU required) | Real tenant upload, original rights and DRAFT lineage verified; 1080x1350 PNG signed private read, banner optimistic CAS and revoked/foreign negatives |
| DEP-249-REEL-REAL | N06/N07/N08 30-second Reel flow | Feature #4 Video Studio + Part 1 render worker | Existing rights-safe fixture inputs and Python Queue/FFmpeg worker path; authoritative user-token `request_reel_render_job` RPC/outbox/usage state in DEV | Actual atomic one-job+outbox+quota, stable idempotency/lease, 29–31-second portrait H.264/AAC private MP4 and negative cross-tenant signed URL; never label mocked media a real render |
| DEP-249-SECURITY-E2E | N03/N06/N07 | Issue #249 Node gateway + Supabase/Part 1 backend | Authenticated JWT/JWKS transport and DEV Supabase RLS/RPC rights and billing verification | OWNER/EDITOR positive; VIEWER, revoked, foreign and expired token negative; uncertain POST read-reconciliation and one-charge semantics verified on DEV |
| DEP-249-HTTP-TRACE | N09/N12 original 503 root cause | Azure Issue #249 DEV infra owner / Azure internal diagnostics | Request-correlated Azure ingress→HTTP-scale-group→host→Python worker trace for true 9/20 unmarked ~61-second 503 samples | Named causal component/condition and approved reversible repair; repeated HTTP warm/idle/concurrency samples plus p95/p99, no speculative AlwaysReady spend |
| DEP-249-RELEASE | N10/N11/N12 | Shared coordinator | Reviewed PR #668 + existing #639 separate ROOT helper PR, protected workflow/release plan and exact main CI | All four PR jobs success on exact head, coordinator-only merge, independent main 4/4, approved isolated DEV release/rollback and complete E2E before any customer cutover |

**Independent / not blocked:** N01/N02 source comparison, N04/N05 secure frontend adapter and tests, all-route mocked dispatch matrix, source-only negative roles/error/mutation cases, deterministic CI, migration-readiness documentation, and honest input/output trace fixtures. Do not wait on actual Creative Director (#2), Fashion media (#3), video composition (#4) or GPU Motion (#5) to complete these independent tasks; none of their mock fixtures establish hosted media acceptance.
