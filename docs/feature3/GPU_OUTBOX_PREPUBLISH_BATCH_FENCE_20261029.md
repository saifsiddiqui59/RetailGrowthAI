# Feature #3 pre-publication Azure Queue batch safety — 2026-10-29

## Scoped GPU-OFF source continuation (F3-05 / F3-13)
- The existing `Feature3GPUOutboxService` validates claimed rows, but the outbox publisher previously forwarded rows from its injected service without a second full-batch shape check. A duplicate or forged row could be sent before an unsafe sibling was discovered. The new publisher gate inspects the **entire claimed batch before the first queue send**.
- Requires exact `job_id,shop_id,dispatch_token,expires_in_seconds,gpu_started` keys; canonical UUIDv4 job/shop/token, exact integer 120-second lease, explicit `gpu_started=False`, unique jobs and dispatch tokens, list type and bounded 1–10 limit. Rejections perform **zero** send or confirm actions.
- Source-only tests cover invalid/foreign/uppercase identity, false or extra paid flags, malformed lease, repeated claims, oversize and invalid limits, plus two unique legitimate dummy sends and confirmation.
- Existing uncertain Queue or SQL ACK semantics remain *unchanged*: no automatic resend, replay, billing, inference, refund, or dequeue/delete. The SQL claim itself may have written a short lease before a batch is rejected; only operator reconciliation can decide what happened.

## Coordinator handoff
- Branch `feat/feature3-gpuoutbox-prepublish-batch-validation-20261029`; exact-head 4/4 PR CI and coordinator-reviewed merge + fresh postmerge 4/4 required. Keep 0/33 fully hosted DONE; F3-05 and F3-13 remain source-partial, with actual Azure delivery/unknown ACK, provider/rights grants and real signed DEV acceptance outstanding.
- Do not change the shared original 33-package tracker from this branch because PR #683 owns a concurrent edit. Coordinator should append this handoff on integration.
- Never start GPU, deploy, change hosted SQL, approve real sources, modify PROD or WineShopPOS.

## Existing contract compatibility
- The established GPU envelope validator continues to raise `GPUEnvelopeDenied` for malformed shop/job IDs; it is applied to every claimed row before any queue send. Malformed dispatch tokens/batches remain `StorageUnavailable`. This preserves existing queue sender tests and prevents a malformed source identity being treated as ambiguous transport-ACK.
