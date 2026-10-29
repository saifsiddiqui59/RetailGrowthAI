# Feature3 operator evidence fail-closed exception boundary — 2026-10-30

## F3-06/F3-13 source-only hardening
- An external private Storage/SQL verification failure could previously propagate its raw exception from `Feature3GPUOperatorReconciliation.inspect` to a service/operator caller. Backend library errors can contain private object paths or even sensitive request details; no missing or uncertain evidence may become a successful financial/production settlement receipt.
- The inspector now converts independent private-image read exceptions and the post-evidence authoritative job/reservation re-read exceptions into two fixed `Feature3ReconciliationUnknown` messages, suppressing the original exception chain in the API-facing error. Verified receipts and the existing no-retry/no-refund/no-finalize flags are unchanged.
- Isolated Python negative tests prove no untrusted private path or simulated service credential is revealed and no `TERMINAL_SUCCESS_EVIDENCE_OBSERVED` receipt is returned when either backend fails. Tests do not inspect a real cloud object or provider invoice.
- **No Azure/GPU invocation, spend, SQL migration, hosted release, PROD, media approval or WineShopPOS modification.** Existing hosted 33-package acceptance count remains 0/33.

## Coordinator handoff
- Branch `feat/feature3-operator-private-evidence-exception-fence-20261030` must pass exact-head 4/4 CI and coordinator code review, then fresh main 4/4 after integration. Preserve PR #683's ongoing original 33-package tracker edit; reconcile this separate handoff only after integration.
- Independent private-output evidence RPC, genuine source rights, signed tenant roles, unknown billing-ACK operator decisions, #249 Azure 503, F3-LICENSED-MEDIA and F5-GPU-AUTHORIZATION remain external acceptance gates.
