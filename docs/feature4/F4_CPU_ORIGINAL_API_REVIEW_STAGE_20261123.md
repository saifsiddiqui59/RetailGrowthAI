# Feature #2 → #4 — guarded original DEV API review-only activation

**Source candidate.** This document is not proof the original API flags were changed, nor is it a two-shop E2E receipt.

## Verified prerequisite
- PR #1118 merged and protected DEV trigger run [#45103369693](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/45103369693) passed: **exactly three** private F4 queue/timer functions indexed in the isolated 1×2GiB worker, service-only connection verified, customer CPU_RENDER remains OFF. Previously installed six F4 SQL candidates and two dedicated DEV queues are reused, not recreated.
- Source-only PR #1121 (GET-only recovery) and #1122 canonical handoff merged; new frontend rendering is still disabled.

## Review-only original API preflight and stage
`.github/workflows/retail-dev-feature4-api-review-once.yml` runs only from a reviewed merge to `main` in the existing protected `dev` environment. Before any setting change it:
1. Authenticates exact DEV Azure OIDC and reads exact original/worker resource identity, 1×2GiB Python 3.11 worker capacity and both private queues.
2. Verifies actual current worker index has **three** known private functions and worker flag ON / CPU_RENDER OFF. Verifies actual original hosted ZIP already indexes all **seven** Feature4 plan, review, render/status/download HTTP handlers. A source file on GitHub alone is not sufficient.
3. Requires identical DEV Supabase URL, protected service-role identity and private queue storage on original and worker, a backend publishable key, current protected SQL/RPC and an empty F4 render job list. No raw settings are printed; evidence files are transient with `umask 077`.
4. Only after every preflight passes, sets **original** `RETAIL_FEATURE4_PLAN_ISSUE_ENABLED=true`, `RETAIL_FEATURE4_PLAN_REVIEW_ENABLED=true`, `RETAIL_FEATURE4_CPU_WORKER_ENABLED=true`, `RETAIL_FEATURE4_CPU_RENDER_ENABLED=false`; validates actual readback and restores all four OFF on failure. No worker restart, queue replay, model/GPU call, or private media write.

**Deliberate limit:** This stage enables only guarded, non-rendering editorial API paths. Customer CPU render activation and frontend flags remain OFF. No genuine two-shop login, owned-media approval, job/quota, private H.264/AAC download or tenant-denial evidence is inferred.

## Further actions
After a genuinely successful protected original API stage, provision two **nonprivileged actual Supabase Auth Admin test users** with separate shops and approved synthetic owned media; never insert directly into `auth.users`, invent JWTs, or self-approve protected GitHub deployments. Recheck exact source/retailer approval, rights, lease, idempotency, quota and worker health; turn CPU_RENDER on **last** under separately guarded activation. Run the existing opt-in browser `frontend/e2e/feature4-cpu.hosted.mjs` with real signed test identities and FFprobe. Keep Issue #249/Y1, PROD, GPU and WineShopPOS unchanged.

## 2026-11-23 protected API-stage diagnosis follow-up
Protected main run [#45104337519](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/45104337519) passed actual DEV F4 service-only schema/zero-job checks and Azure OIDC, then **failed closed before setting original API flags** at the package/connection readiness stage. Existing generic denial hid the exact failing predicate, not a secret. Next source patch emits one fixed validator category token only; unknown/malformed data still logs no values. Re-run is allowed only under the same exact DEV checks, original flags OFF and protected environment. No customer activation, test account, video or two-shop E2E is claimed.
