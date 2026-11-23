# Feature #2 → #4 CPU Worker — protected DEV release checklist

Scope: PR #1059; isolated CPU-only reel lane; **never WineShopPOS, GPU, PROD,
Issue #249 Y1, or the existing v1 render queue**. This document is an executable
review gate, NOT evidence that a cloud deployment occurred.

## Before any hosted mutation
1. Verify the exact **final** PR head, no merge conflicts, all four Part 1 CI
   jobs **SUCCESS**, the native F2→F4 30s MP4 workflow **SUCCESS**, and
   the separate worker ZIP build/manifest verification. Review modified
   paths against main and inspect the actual CI logs, not old head checks.
2. Obtain a genuine independent affected-feature/security review of the
   SECURITY DEFINER functions, RLS/browser grants, private storage, billing
   reservation, 25-minute claim fencing, stale-job retry, poison receipts,
   and source SHA. Account-owner GitHub approval is not required, but do not
   substitute the author's own review for the independent security gate.
3. On DEV only, use read-only SQL to confirm base objects exist:
   public.shops, public.media_assets, public.campaigns,
   public.shop_subscriptions, public.shop_usage_reservations, storage.objects,
   and retail_private.python_json_v1(jsonb). Confirm F4 tables are absent
   or match exactly the reviewed versions. No table truncation/drop.
4. Pin an original configured backend Azure Flex package and restore URI
   *before* touching public API flags. Ensure the distinct F4 worker app
   has its own correct deployment package and a rollback-to-disabled plan.
   Never deploy the professional renderer into the legacy 120-member ZIP.

## Additive SQL order (ONLY after review, checked deployment gate)
Apply to the exact RetailGrowthAI Supabase DEV project and record checksums:
1. supabase/candidates/feature4_reviewed_cpu_plans_20261121.sql
2. supabase/candidates/feature4_cpu_render_jobs_20261121.sql
3. supabase/candidates/feature4_cpu_worker_claim_20261122.sql
4. supabase/candidates/feature4_cpu_worker_outbox_20261122.sql
5. supabase/candidates/feature4_cpu_worker_finish_20261122.sql
6. supabase/candidates/feature4_cpu_worker_poison_20261122.sql

These files remain **source candidates**, not canonical migrations, until
independently reviewed release inventory and rollback are accepted. Each
candidate is verified only in disposable SQL CI now. Do not use a service-role
key in client JavaScript or publish unreviewed SQL functions to anon/JWT users.

## Dedicated queue and host (after SQL)
1. Provision only the existing DEV storage account queues
   \`retail-feature4-cpu-render\` and \`retail-feature4-cpu-render-poison\`,
   both absent from the v1 queue namespace. Do not create GPU, model, or
   always-ready instances; use minimal CPU scale-to-zero hosting where supported.
2. Build \`scripts/deploy/package_feature4_cpu.py --build\` from Python 3.11,
   pinned Node22, pinned FFmpeg+ffprobe with libx264/AAC/drawtext, exact
   \`video-engine/hyperframes/package-lock.json\` dependencies, and the
   installed \`chrome-headless-shell\`. The result must carry
   \`function_app.py\`, \`cpu_backend.py\`, \`host.json\`, all required Python
   site packages, \`hyperframes/node_modules\`, executable bins and the
   \`package_manifest.json\`. It must be less than 1 GiB with no secrets.
3. Deploy the isolated worker to its **own tagged, identity-audited DEV app**.
   Keep \`RETAIL_FEATURE4_CPU_WORKER_ENABLED=false\` in the original API during initial deployment. In the original API
   this is a worker-readiness attestation; leave it false until the separate
   dedicated worker has verified queue and trigger indexing. The isolated
   worker app uses the same flag separately to index its private triggers.
   In the worker app, use only protected server-side \`RETAIL_SUPABASE_URL\`,
   \`RETAIL_SUPABASE_SERVICE_ROLE_KEY\`, \`RETAIL_STORAGE\` and
   \`AzureWebJobsStorage\`. Verify app environment and role scope before
   writing settings; never print secret values.
4. Enable isolated worker indexing only after native artifact and private
   queue exist, then verify these **three only** expected functions:
   \`feature4_cpu_render_message\`, \`feature4_cpu_poison_message\`,
   \`feature4_cpu_dispatch_timer\`. No public worker HTTP endpoint.
   Verify queue is draining/recoverable without accepting customer jobs.
5. Verify the original API hosted ZIP actually contains Feature4 plan issue,
   review, render and download routes, with its old URI rollback pinned. Only
   after protected JWT/RLS RPCs, dedicated worker and queue proof, media rights
   and quota safeguards may the ORIGINAL API set
   `RETAIL_FEATURE4_PLAN_ISSUE_ENABLED=true`,
   `RETAIL_FEATURE4_PLAN_REVIEW_ENABLED=true` and
   `RETAIL_FEATURE4_CPU_WORKER_ENABLED=true` (API readiness attestation,
   NOT in-app trigger indexing), then `RETAIL_FEATURE4_CPU_RENDER_ENABLED=true`
   LAST. Enable frontend controls only after authenticated API verification.
   Never create synthetic billable jobs without a separately authorized DEV
   fixture; genuine signed two-shop E2E remains mandatory.

## Release gates and rollback
- Service-role-only mutation RPCs, unique plan/job/credit/outbox, exact review
  SHA, owner/editor recheck, 25m fenced token, max three render attempts, max
  eight outbox sends, stale/lost-ACK recovery, poison receipts, no public output.
- A current retailer signature must be the **only** source of the editorial
  approval; worker/service_role cannot forge a customer click. Revoked source,
  foreign tenant, viewer and stale worker must fail closed.
- Before finalization, re-download private MP4 and compare actual SHA256;
  SQL finalizes only matching exact \`shop/renders/job/lease.mp4\` and current
  authority. No unreviewed soundtrack, paid model or GPU calls.
- On any index/rights/worker failure: disable
  \`RETAIL_FEATURE4_CPU_RENDER_ENABLED\` in the existing API first; then disable worker-readiness, plan issue/review
  flags and frontend F4 controls. Disable the isolated worker if necessary. Leave new
  outbox/job/credit rows intact for fenced recovery; do **not** delete private
  user assets or mutate v1 render queues. Restore the original Azure app
  package/URI if backend deployment was touched. Do not mark released.
- Only after two-shop genuine signed DEV owner/editor/foreign/revoked,
  short-lived private preview/download, 240s idle, quota and queue poison
  acceptance, and fresh postmerge main 4/4 may this flow be considered E2E
  ready. Issue #249 ingress remains a separate open dependency.

**Status as authored:** source package and disposable SQL are implemented;
actual DEV migration, queue provisioning, hosted worker, independent review
and signed two-shop E2E are NOT verified.

## 2026-11-23 — Source-only recovery from an uncertain CPU render POST

- The authenticated React review surface now offers **Check existing render (read only)**. It uses the Feature4-owned `findFeature4CpuRenderJob` helper with the exact shop, plan and review SHA plus only the current user's Supabase JWT, filtering the existing RLS-protected `feature4_cpu_render_jobs` table by exact shop+plan. It accepts **at most one** valid same-shop, same-approved-hash receipt.
- After this read, the frontend separately verifies job status through the signed Feature4 API and renews the current short-lived private MP4 link only for an actually completed job. The polling flow resolves that signed preview URL **before** committing terminal SUCCEEDED state, preventing effect cleanup from cancelling the preview refresh. No customer quote, media path, service key, quota reservation, POST replay or frontend self-approval is issued by recovery.
- A 503, foreign row, unexpected status, changed review hash or multiple rows fails closed; a lost submit acknowledgement is **never** interpreted as permission for an automatic second render. This adds browser continuity after reload/timeout, but it is NOT proof that private worker functions, API flags, signed test shops or hosted video acceptance are ready.
- Source tests: `tests/frontend/feature4-private-job-recovery.test.mjs`. Exact-head main CI and hosted protected acceptance remain separate; no Y1/#249, PROD, WineShopPOS, paid model or GPU change.
