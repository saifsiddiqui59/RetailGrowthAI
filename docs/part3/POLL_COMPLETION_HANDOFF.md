# Part 3: Internal Wan poll -> private clip completion (source only)

Implementation workstream: `feat/p3-private-poll-completion`, targeting `feat/part3-integration`.

## Scope and external evidence
- Alibaba Model Studio WAN 2.7 official async task query: GET workspace `/api/v1/tasks/{task_id}`, task statuses PENDING/RUNNING/SUCCEEDED/FAILED/CANCELED/UNKNOWN, `output.video_url` on success, 24-hour task/media expiry.
- Official vendor guides: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference and https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference.
- The existing public `AlibabaWanProvider.poll()` **still returns only safe status**. The new `poll_private()` is strictly server/internal and includes the expiring URL ONLY on SUCCEEDED.
- `PremiumPollCompletion.run_once(job_id)` accepts only a canonical UUID, checks a backend-claimed IMPORTING lease, verified premium reservation and tenant identity, reads the vendor output once, validates signed OSS hostname/expiry, downloads without redirects, validates MP4/H.264/duration, uploads privately and calls fenced store finalization.
- Any ambiguous provider task (UNKNOWN/CANCELED/FAILED) is **RECONCILE**, not an automatic refund or another billable POST. Expired URLs, forged tenant leases and missing reservation cannot import. Nothing returns signed vendor URLs in the public result.
- `premium_private_import.validate_vendor_video_url` now requires exactly one future `Expires` epoch with >=30 seconds remaining, rejecting expired or duplicate values before network access.
- The backend and provider both remain **disabled by default**. This module has no registered Azure Function, deployed code path, Supabase migration, actual provider task or media.

## Required runtime/service-role contracts BEFORE wiring
- `store.claim_import(job_id)`: one atomic privileged DB claim for this canonical job UUID; return `None` for unclaimed/foreign/expired job; otherwise DB-authored `{id, shop_id, attempt_token, provider_task_id, status: IMPORTING, reservation_confirmed: true, seconds}`. Verify the premium reservation in the existing Part 1 usage ledger, a current lease and original tenant. Never let HTTP or Azure Queue payload supply these fields.
- `store.finalize(job_id, shop_id, attempt_token, private_path)`: CAS checks the **same** live claim and tenant, creates/links one tenant-private `media_assets` record in existing `retailgrowth-media`, records billing outcome from actual vendor usage and marks SUCCEEDED atomically. The fake test implementation only proves the expected interface.
- `media.upload`: must implement tenant-scoped existing private bucket storage, no overwrite, bounded file, and a well-defined stale-lease/orphan cleanup strategy. Post-upload DB failure may leave an object: reconcile rather than blindly repeat.
- Add a durable Azure poll timer/UUID queue, enforced per-shop spend and provider concurrency, poison and failure reconciliation, secure signed RetailGrowthAI downloads, and operator audit. Do not put provider URL, prompt, token or key into queue, logs or frontend.
- For a real provider task `poll_private` performs one outbound **nonbillable** status GET, but it is nevertheless gated by an owner-approved API key and enabled flag. Do not activate or run billable tasks without explicit approval.

## Offline tests
- `ai-agents/tests/test_premium_video.py`: worker-private vs safe public response and disabled gate.
- `tests/reliability/test_premium_poll_completion.py`: safe import, lease/tenant/usage denials, provider status reconciliation, expired/forged/duplicate signed URL denials, failed DB CAS, no secret leakage.
- `tests/reliability/test_premium_private_import.py`: bounded download, codec/bytes validation and private finalization.
- Both existing four-job CI and dedicated Part 3 CI are required for a merge. Green mock tests do not authorize a live release.

## Follow-up/ownership
The still-unfinished Part 3 work is schema/RPC review, durable outbox, registered Azure polling/import worker, live API/frontend authentication/credit UI, premium multi-clip 30-second FFmpeg composition, cost/rights review and separately approved hosted DEV smoke. Coordinator only reviews/merges the final `feat/part3-integration` -> `main` PR.
