# Feature3 Task 3.4 — Prepaid SQL/optional GPU adapter bridge

The live DEV SQL migration `20261028101328_feature3_gpu_budget_jobs`
**reserves shop/actor/price within the same PostgreSQL transaction that creates
an outbox event**, whereas `OptionalGPUProvider.execute` calls its
`reserve_usage` callback *after* the service-only SQL job claim.
The provider's finalize callback also receives **wall time**, but the SQL
settles a verified USD value and requires a registered private output media ID.

`poster-engine/feature3_gpu_prepaid_bridge.py` now maps those two contracts
without creating a second reservation. The bridge:
- Requires SQL's one-shot exact-token, shop and attempt claim receipt.
- Authorizes current rights before and after inference; rejects denied media.
- Reads existing authoritative same-shop pre-reserved receipt with a bounded
  amount; it must NOT insert another usage ledger row or retry an unknown ACK.
- Captures the immutable same-tenant PNG media ID returned by the private
  writer; the existing provider validates SHA and UNREVIEWED receipt.
- Requires a **server-trusted measured USD cost** distinct from wall-time;
  cannot settle with a fabricated/unknown cloud quote.
- Passes claim token, actual bounded cost and private output ID to a
  service-only finish RPC. Any missing settlement acknowledgment blocks
  success; do not retry possibly charged jobs.

**This is a pure server-side callback adapter, not an Azure or Supabase
transport.** The worker/queue needs implementation of exact SQL RPC calls,
service-role security, expired-lease recovery, storage byte registration and
a trusted meter. Before those exist, the GPU provider stays OFF and no actual
customer inference is authorized. Synthetic Pillow tests are NOT CUDA.

The SQL currently makes only a single attempt and requires the private
outbox state SENT before claim. A job claimed then denied rights before
the adapter's reservation-phase handler is a fenced running lease requiring
a separate non-retrying stale-job reconciler. No auto-billing should infer
or write zero cost if the runtime may have been allocated.

No new GPU infrastructure, Azure resource, PROD or WineShopPOS changes.
