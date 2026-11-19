# Issue #249 — isolated Y1 five GET release + rollback

**CODE PREPARED ONLY: not merged, dispatched, deployed, or signed-hosted-accepted.**
Original Flex `rgai-dev-functions-d4e5ddbd` is unchanged; issue #249 stays OPEN.

## Verified prior hosting
- Isolated Python3.12 Linux Consumption Y1 already hosts exactly 2 GET functions:
  health and an original-JWT campaign read shadow with the feature flag OFF.
- Protected real Azure #42964811296: 40/40 health/unknown GET statuses and
  12/12 handler-marked unauthenticated campaign 401 across 240 seconds idle.
  These are NOT signed two-shop RLS tests.
- Original Flex had 6/9 anomalous read/write probes on its recent comparison.

## Source release and rollback preparation
- Parent source #968 adds read-only render-job, poster-job and poster-draft
  GETs using the ORIGINAL JWT verifier and current per-request TenantStore.
- Source staging #995 passed exact-head 4/4 CI #44375583051.
- `build_five_get_release.py` stages an explicit allowlist for FIVE Python
  v1 GET functions or restores the original TWO GET shapes; no queue/timer,
  POST/PATCH, service-role credentials, paid provider or side-effect route.
- The new workflow is explicitly `workflow_dispatch` only, requires the
  exact reviewed main SHA and protected DEV environment, and refuses writes
  when current Y1 is not exactly 2 GETs or any public/shadow setting exists.
  It builds Linux Python3.12 pinned dependencies and preserves the two-route
  rollback ZIP as a short-lived workflow artifact before deploy.
- Deployment changes ONLY the existing isolated Y1 ZIP. Verification requires
  5 exact GET index names; two 20/20 health/unknown GET windows 240s apart;
  and 8 handler-marked missing-JWT 401 responses across four real API GET
  routes; original Flex FC1 must remain unchanged.
- On ordinary failure an EXIT trap attempts the two-route rollback, followed
  by a separate protected restore job that refuses unexpected routes/settings
  and requires 2 indexed GETs and real health checks. Full workflow cancellation,
  lost artifact/credentials, or unavailable approvals may still prevent
  automatic cleanup. The operator must check final state.
- The two-route rollback package is reconstructed from reviewed current main:
  it reproduces the prior **route shape**, not the exact unknown historical
  deployed ZIP bytes. Do not claim bit-identical rollback.

## CI-only fresh-process safety gate
- Both release shapes are staged from the exact source allowlist and exercised
  in separate Python interpreters. The uv/pytest CI path requires the pinned
  **real** `azure.functions` SDK; the existing stdlib-only deployment checks
  execute the same denial paths with a minimal SDK interface stand-in.
  The protected manual workflow additionally vendors/loads actual pinned
  Python3.12 Azure SDK dependencies before any Y1 cloud mutation.
- Every entrypoint must return a handler-marked 401 when unauthenticated,
  except the explicit health endpoint (200). Original JWT/RLS/store modules
  must remain lazily unloaded while shadow flags and Supabase settings are off.
- This source CI check does **not** constitute independent review, real hosted
  JWT/tenant authorization, a five-route Azure deployment, or an approval to
  bypass the protected DEV environment.

## Parent-safe release import audit (2026-11-19)
- Parent #995's staging module is kept **byte-for-byte unchanged**: it bounds
  each original source before reading, validates exact manifests/pins and copies
  only the immutable validated bytes. Its sparse multi-GB file rejection remains.
- This release's `build_five_get_release.py` then audits imports from those
  **exact staged bytes**, not mutable original checkout paths. A newly introduced
  unvendored, privileged worker, relative or unpinned Azure SDK import removes
  the staging directory and aborts **before** any ZIP, dependency install or
  Azure change. The rollback-two path also audits all five originals first.
- This separation keeps the parent staging security intact while allowing the
  Y1 release to apply stricter packaging-only import closure without modifying
  the shared parent stage script. Neither CI nor the source audit approves DEV
  deployment, tenant RLS or independent JWT/ops review.

## Pre-deploy inherited JWT/PostgREST redirect security gate (2026-11-19)
- The staged Y1 original `tenant_store.py` is imported from the original
  repository, not rewritten or forked. Until the independently reviewed
  original PostgREST redirect protection (proposed in [#1018](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1018))
  is actually integrated into `main`, the old default `urlopen` could
  follow a 30x response with a signed user JWT. **Do not deploy that ZIP.**
- The protected manual workflow now calls
  `verify_staged_y1_auth_transport.py` against both the exact five-route
  ZIP stage and the two-route rollback stage **before vendoring, Azure login
  or any configuration/code write**. The offline guard loads the staged
  source with a synthetic exception module, asserts its default transport
  contains a redirect-denying handler, rejects malformed/redirection-prone
  Supabase origins, then exercises HTTP 301/302/303/307/308 with an
  in-process synthetic HTTPS responder. It fails on any off-origin retry,
  response-handle leak, or unsafe default.
- The current source branch intentionally contains the **older** original
  PostgREST module: the protected manual dispatch therefore remains
  fail-closed until reviewed upstream #1018 (or an equivalent independently
  accepted fix) reaches the actually deployed main. CI validates both
  vulnerable-denied and safe-allowed synthetic fixtures; it does **not**
  claim the original source was already secured, signed-hosted-tested,
  merged or deployed.
- This gate tests only redirect transport behavior. Positive two-shop RLS,
  real signed/expired JWKS, all media permissions and rollback hosting still
  require separate independent acceptance.

## Read-only hosted Y1 health probe stays on exact host (2026-11-19)
- The original `ops/p0249_y1_canary_guard.py` health/unknown check was
  following HTTP 30x by default. A redirected request could be counted as
  an expected code and marker even when the response came from another host.
- The shared Y1 canary now uses an explicit deny-redirect opener, closes
  HTTPError response bodies and refuses any 301/302/303/307/308 as health
  or unknown-route acceptance. Five deterministic in-memory fake-HTTPS
  cases prove no second request is issued to the `Location` hostname.
  No Azure endpoint, customer JWT, live request, settings or deployment
  is exercised by these source tests.
- Both release soak windows and the independent two-route restore use the
  same pinned host canary, so neither may report 20/20 from a redirected
  server. This is test reliability, not signed-tenant authorization,
  five-GET hosting, or resolution of original Flex markerless 503.

## Remaining before Y1 replacement
1. Independent shared JWT/RLS/render/poster/Azure ops review of #968, #995,
   and this workflow; exact-head 4/4, main merge in parent-child order.
2. Actual approved protected DEV operator dispatch; no automatic push/merge
   activation, no Azure settings writes during this code preparation.
3. Separately reviewed signed JWT-only trial #939 and genuine two-shop
   active-membership, revoked/foreign tenant real hosted GET tests. Never
   seed campaign/shop tables casually: triggers can create outbox jobs and
   trial/quota reservations.
4. Original POST/PATCH, private media, worker ownership, cost/latency and
   signed two-shop E2E must pass before any frontend cutover or #249 closure.

No cloud/Auth/SQL writes, GPU or paid model, PROD or WineShopPOS operations
are performed by this source change.
