# Worker span sink — safe activation checklist (2026-10-29)

The already merged worker span pilot (#620) generates only optional, 
backend-authored receipts after actual lease-fenced DB outcomes. The staged
private ledger (#622) independently checks real terminal campaigns/renders.
This source addition provides a service-only PostgREST sink and a separate
`RETAIL_FEATURE_WORKER_SPANS_ENABLED` switch, **OFF by default**.

## Source behavior
- `WorkerSpanStore` allows only planner/FFmpeg operations with matching
  status, actual UUIDs, bounded duration/attempt and operation-specific
  metadata. It supplies no caller `shop_id` to the SQL RPC; the PostgreSQL
  service-only procedure derives tenant and verifies the terminal job.
- The backend reply must positively assert persisted=true and match
  shop/job/attempt/feature/operation/status. A missing RPC, rejected SQL,
  wrong tenant or service outage raises; `emit_worker_span` treats an
  unavailable injected sink as telemetry failure, never successful durable
  audit or a reason to retry the business operation.
- The queue worker passes a `span_sink` ONLY when the exact
  `RETAIL_FEATURE_WORKER_SPANS_ENABLED=true` is set. No string or
  truthiness fallback. By default, existing queue behavior is unchanged.
- No new external HTTP endpoint, queue payload, JWT, media download, AI
  call, Azure SKU or dependency on a browser trace run.
- The current store has no production-side monitoring of lost optional
  span writes. A future release must create an independent sink-failure
  counter/inbox before relying on completeness metrics.

## Release gates before enabling
1. Have exact 31+ reviewed RetailGrowthAI DEV canonical migrations plus
   an independently approved, transactionally tested worker-ledger
   migration; do not apply source release candidates blindly.
2. Validate only service-role execution of
   `retail_feature_worker_append`; verify owner/editor read-only,
   VIEWER/foreign/revoked/anon denial, F2 seven saved days and F4 private
   output rights. Deploy correct API host and SQL before flipping the flag.
3. Verify actual queue worker connection, no blind retry when POST ACK is
   unknown, low-volume trace writes, quota/cost, no sensitive details.
4. Only then enable for RetailGrowthAI DEV and test actual authenticated
   two-shop journeys; do not route customers or touch production.
5. Browser QA receipts are still untrusted; the Testing Chat UI must query
   the independent signed worker-span RPC and display its provenance
   separately, rather than re-labeling browser PASS as backend success.

Azure issue #249 remains OPEN; no source change here resolves gateway
HTTP503, modifies WineShopPOS or spends on Feature5 premium AI motion.
