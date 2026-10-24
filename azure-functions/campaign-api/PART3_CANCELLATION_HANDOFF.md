# Part 3 — premium-video cancellation boundary (source only)

This workstream adds `PremiumCancelBoundary` and offline mocked race/authorization tests. It is intentionally **not registered** with Azure Functions and no SQL migration is applied. Every existing FFmpeg/campaign flow is unaffected; premium mode remains disabled by default and no Wan API request, customer charge, queue, or infrastructure deployment is performed.

## Safe cancellation contract

- **Only QUEUED before submission** may be canceled. Any `SUBMITTING`, `PENDING`, `RUNNING`, `IMPORTING`, `SUCCEEDED`, `FAILED`, `UNKNOWN`, or observed provider task/lease is **not** safely refundable without provider reconciliation.
- Authorize with the existing user JWT/RLS and active shop OWNER/EDITOR permission. Return 404 for foreign/removed-member jobs.
- Future `store.cancel_unsubmitted_atomic(job_id, shop_id, user_id)` must be ONE audited, service-only PostgreSQL transaction. Row-lock both the premium job and existing subscription ledger reservation; verify current membership/shop, `status='QUEUED'`, `provider_task_id IS NULL`, `attempt_token IS NULL`, and absence of a committed provider submission; transition to CANCELED and release **only that reservation** in the same transaction. The operation loses to the worker's `QUEUED -> SUBMITTING` CAS if submission has begun.
- Return a typed exact receipt confirming same job/shop, canceled status, ledger credit released and provider submission never started. Missing/mismatched receipt fails closed (503). None/race returns 409 for reconciliation; no credit or cancellation success is assumed.
- Repeated cancellation returns 200 only when a persisted cancellation receipt proves release. Otherwise 409. No provider cancellation or assumed refund is invoked.
- No new billing ledger, no client price/URL/provider-ID input, no PII/provider URLs in safe responses.
- Existing Part1 trial/premium allowances remain ZERO pending owner provider, region, terms and spending approvals.

## Activation dependencies

1. Reviewed NEW migration/RPC with adversarial PostgreSQL transaction tests for cancel-vs-submit races and idempotency; must integrate with source-only proposed premium schema and **existing** `shop_usage_reservations` without replaying previously applied migrations.
2. Add a narrow authenticated `POST /api/premium-video-jobs/{job_id}/cancel` route only after safe live transactional RPC, protected deployment and human approval. Shared API contracts/Part1 UI changes require Coordinator review.
3. Verify hosted DEV tenant denials, provider task unknown states, canceled reservation counters, and no double refunds. No production activation or paid generation without explicit owner authorization.

## Current test scope

`tests/api/test_premium_cancel.py` is discovered by the existing Python CI job; tests cover disabled path, member denials, unsubmitted vs uncertain statuses, foreign job, incomplete credits, losing CAS race and idempotent cancellation response. Mock behavior is **not evidence of a deployed atomic database RPC**.
