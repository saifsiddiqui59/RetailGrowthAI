# Feature3 Task 3.4 — Default-off, durable GPU ledger (source review 2026-10-28)

This work extends the **existing** RetailGrowthAI Supabase database, `shop_ai_budget_controls`, `shop_ai_spend_reservations` and existing `shop_subscriptions` lock. It does not create a second wallet, start a Container Apps GPU, or deploy any worker.

- `feature3_gpu_enabled=false`, `feature3_gpu_max_job_usd=0` for every existing or future shop. A human-signed, server-owned authorization must explicitly enable the tenant later.
- A service-role-only `feature3_reserve_gpu_job` locks the current subscription and budget rows, validates active OWNER/EDITOR, immutable DRAFT design revision/hash, per-job quote, global period spending and one outstanding job per shop. The reservation, job row and private outbox are one PostgreSQL transaction; an unknown ACK is **not** automatically retried.
- Only service role can issue one attempt-fenced `feature3_claim_gpu_job`; claim requires the private outbox to be SENT. There is **no automatic GPU retry** after timeout.
- `feature3_finish_gpu_job` requires the current claim/lease and exact private tenant-generated PNG registration plus a real Storage object. It commits actual capped USD spending and SUCCEEDED/FAILED atomically. It cannot forge cross-tenant media or replay a terminal claim.
- `public.feature3_gpu_jobs` and `retail_private.feature3_gpu_outbox` both have RLS, no browser writes, and no worker deployment. No client-supplied rate may override the operator-quoted maximum.
- Disposable SQL negative checks are in `tests/security/poster_feature3_gpu_budget_negative.sql`; runtime PHP/JS tests are not real Azure GPU billing evidence.
- Dependencies: Task3.1 model catalog source **actual** DEV version `20261028092346` merged #475. This Task3.4 SQL remains *unapplied to hosted DEV* pending exact-head 4/4 CI and reviewed protected release. Check source-only CI outcome before claiming readiness.

Remaining after this schema: authenticated backend bridge between source #458 callbacks and the service-only RPCs, outbox-to-Azure Queue relay, model approval, private bytes and current-rights rechecks, and one paid CUDA benchmark only after owner approval.

No WineShopPOS/PROD or GPU resource changes.

## Verified actual DEV deployment — 2026-10-28

The reviewed source migration in PR #479 merged as `92f9c7a3` after exact-head CI #40667005701 **4/4 PASS**. Fresh live RetailGrowthAI DEV history before migration: 23, through Feature3 catalog 20261028092346; no existing GPU jobs or outbox. Applied `feature3_gpu_budget_jobs` using connected Supabase, which returned **success** and assigned actual version **20261028101328** (24 versions). Verified live:
- `public.feature3_gpu_jobs` and `retail_private.feature3_gpu_outbox` exist; both RLS enabled.
- Existing/new GPU approval default `false`, **0 GPU-enabled tenants**.
- `anon` and `authenticated` cannot execute reserve/claim/finalize GPU service RPCs.
- GPU jobs=0, private outbox events=0, no GPU worker or Azure compute was started.
- Source version synchronized by follow-on migration reconciliation PR (CI/merge must be independently checked).

This is a **hosted schema result**, NOT real CUDA inference, end-to-end tenant claim or paid budget acceptance. Outstanding: actual authenticated backend adapter, runtime outbox/queue relay and negative concurrency/expiry tenant tests.
