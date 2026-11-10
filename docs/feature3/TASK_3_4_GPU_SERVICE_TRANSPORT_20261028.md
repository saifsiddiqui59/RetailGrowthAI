# Feature3 Task3.4 — Backend-only GPU SQL RPC transport (2026-10-28)

This is an additive **pre-GPU** implementation. It provides real server-side
PostgREST calls to the existing DEV-deployed
`feature3_reserve_gpu_job`, `feature3_claim_gpu_job` and
`feature3_finish_gpu_job` SQL RPCs through `AdminStore`'s vetted service-only
backend key transport. It reuses the existing `shop_ai_spend_reservations`
ledger and reads the current claim/lease and **existing** reservation; it does
not create a second wallet.

The `Feature3GPUServiceStore` method signatures are:

- `reserve(shop_id, actor_id, design_id, revision, design_sha256, request_id, upper_cost_usd)`
- `claim(job_id, claim_token)`
- `read_prepaid_reservation(shop_id, job_id, attempt, claim_token)`
- `finish(job_id, claim_token, actual_usd, output_asset_id=None)`

Inputs are bounded canonical UUIDs, the exact source SHA-256/revision and
six-decimal USD. The deployed SQL remains authoritative for actual active
OWNER/EDITOR, subscription, default-off budget, source rights and one-job cap.
No method accepts a browser asserted payment approval. The existing one-shot
SQL claim and lease token remain authoritative. A transport timeout or absent
settlement ACK is **not** automatically retried: the operator must independently
read the existing job/ledger before deciding any recovery action.

New `tests/api/test_feature3_gpu_service_transport.py` uses mocked PostgREST
(no secrets or cloud) to verify exact RPC payloads, service-only secret header,
wrong-shop/stale/expired claims, budget bounds and one request on an unknown ACK.
The original `PrepaidGPUJobCallbacks` adapter remains source-only. No queue,
worker, output bytes, hosted authenticated user or CUDA inference was activated.

## Remaining integration (do not mark Task3.4 complete)

1. Add a protected, migration-led, server-only transactional **outbox dispatch**
   RPC for `retail_private.feature3_gpu_outbox`. It currently cannot transition
   to `SENT` via the Data API and hence SQL claim deliberately fails closed.
   Establish no-repeat queue delivery even for an unknown Azure ACK.
2. Wire backend request authorization to a genuine JWT and approved GPU usage
   flow, and bind this class to the source prepaid worker callbacks only in a
   trusted private worker (not the public Functions HTTP process).
3. Add current rights rechecks, private source bytes/registered PNG writer and
   trusted Azure measured cost before any billed generation.
4. Add explicit orphan/expired-claim reconciliation and immutable output cleanup.
5. Test disposable SQL concurrency, hosted signed roles, versioned history,
   Azure Queue false ACK and independent main CI before enabling.
6. Obtain explicit **paid** GPU spend approval for any real CUDA test.

The hosted DEV schema has 24 migrations including
`20261028101328_feature3_gpu_budget_jobs`; the read-only count on October 28
was 0 GPU jobs, 0 GPU outbox rows, 0 GPU-enabled tenants, 0 registered Feature3
models and 0 versioned designs. No hosted DDL or data writes are made here.

No changes to WineShopPOS, PROD, Azure compute or GPU spending.
