# Feature #2 — private Kokoro CPU budget and fenced job reservation (2026-10-29)

**Scope and status:** Implemented a fail-closed **source contract** in existing `ai-agents/src/ai_agents/feature2_local_voice_workflow.py::reserve_budgeted_local_voice_job`. This is not a deployed Supabase transaction or a real CPU model execution. It does not authorize paid Azure Speech, customer audio, private downloads or publishing.

## Server-side contract

The server provides authoritative callbacks: `authorize_current_editor(shop,campaign)`, `read_current_plan(shop,campaign)`, `read_authoritative_quota(shop,campaign)`, `reserve_atomic_once(shop,campaign,job_uuid,request_sha,budget_revision,cpu_ms,request)`. The browser must **never** implement these callbacks or choose a reserved CPU budget. The source validates original Creative Director plan, exact shop/campaign, voice/locale/speed, one UUID job key and current editor/plan **before and after** the reservation.

The trusted quota must identify the shop, campaign, provider `kokoro-onnx`, active budget period `YYYY-MM`, nonnegative used+reserved CPU milliseconds, maximum 86,400,000ms monthly allowance, bounded 2,000..180,000ms reservation per job, allowed 1..4 concurrent CPU job leases and a monotonically increasing budget revision. The entire claim is **local CPU only** with `paid_api_calls_allowed:false`. A precheck fails quickly on exhausted budget or active worker slots, but it **is not** a replacement for the database transaction.

The request digest SHA256 binds exact shop/campaign, reviewed plan/script hashes, local voice/locale/speed/provider, job UUID, budget revision, month and CPU reservation. The coordinator's `reserve_atomic_once` MUST atomically:

1. Lock the tenant/campaign authoritative quota row and check active signed OWNER/EDITOR membership, plan hash, month and subscription/worker entitlement in **the same transaction**.
2. Enforce a unique `(shop_id,campaign_id,job_key)` across real jobs, even when submitted with an alternate idempotency payload, while preventing CPU reservation replay. If a request is already reserved, return a bounded explicit **existing job status**; do not synthesize or spend again.
3. Enforce actual cumulative `used_cpu_ms + reserved_cpu_ms + requested_cpu_ms <= monthly_limit_ms` and active count < cap **under the row lock**, not merely this caller's precheck.
4. Increment a positive 64-bit lease fence, store `request_sha256`, `budget_revision`, `lease_expires_ms` (<=5 minutes), immutable source hashes, reserved CPU allocation and status `RESERVED`, with a transactionally committed receipt.
5. Consume that same fence under current source/rights checks when the worker **claims**, **renews**, **writes** and **settles** the job. Expired/revoked/mismatched fences cannot write private media or adjust usage. Settle once, including after failures, and release the reservation according to an agreed policy.
6. For any timeout/uncertain transport, **read the existing private job by key** before asking to reserve. Never auto-submit a different UUID, double-charge, auto-invoke Azure, or falsely claim a successful synthesis.

The source validator rejects foreign, unpublished, overbudget, replay-like or uncommitted receipts, wrong job key/digest/lease, lease duration outside 5 minutes, nonlocal provider, any paid provider call and any publish flag. It returns only a private source reservation reference; `real_model_inference_observed:false` and `reservation_is_not_worker_completion:true`. It does not return an audio URL, script, JWT, service token or billing endorsement.

## Tests and remaining coordinator steps

`ai-agents/tests/test_feature2_local_voice_workflow.py` covers normal source reservation plus invalid locale, foreign scope, missing/overused budget, concurrent count, wrong month, fabricated atomic commit, expired/overlong fence, changed request SHA, paid/provider escalation, revoked editor and stale plan.

To wire this into **actual** `synthesize_and_stage`, the coordinator must implement durable budget tables/transactions or reuse existing signed outbox/lease logic, and pass a trusted `reserve_job_once` adapter using the same fenced token. Backend storage must reject any unreserved or expired lease when saving the original WAV. The helper by itself **does not** make `synthesize_and_stage` budget-safe; don't claim that task #21 is complete on source tests alone. Resolve [Azure ZIP packager issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) before release.

No hosted migration, paid credits, GPU, new cloud resources, PROD or WineShopPOS change was made.
