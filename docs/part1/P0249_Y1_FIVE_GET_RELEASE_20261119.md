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
- Both release shapes are staged from the exact source allowlist and indexed in
  separate isolated Python interpreters using the real `azure.functions` module.
- Every entrypoint must return a handler-marked 401 when unauthenticated,
  except the explicit health endpoint (200). Original JWT/RLS/store modules
  must remain lazily unloaded while shadow flags and Supabase settings are off.
- This source CI check does **not** constitute independent review, real hosted
  JWT/tenant authorization, a five-route Azure deployment, or an approval to
  bypass the protected DEV environment.

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
