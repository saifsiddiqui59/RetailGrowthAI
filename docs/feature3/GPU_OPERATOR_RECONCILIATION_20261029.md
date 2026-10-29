# Feature3 operator-only uncertain GPU financial reconciliation — 2026-10-29

Source-only: `feature3_gpu_operator_reconciliation.py` inspects actual existing service-only `feature3_gpu_jobs` and `shop_ai_spend_reservations` via GET and requires independently verified private output-evidence callback for any claimed success. It does not start GPUs, send queue messages, release reservations, finalize charges, delete private objects, publish media or invent retry authorization.

Classifications:
- QUEUED/RUNNING + current RESERVED ledger -> PENDING_OR_UNCERTAIN_HOLD; a stale lease or lost Queue/Storage ACK **does not authorize a second execution or refund**.
- FAILED + exactly one attempted, SETTLED, no output -> TERMINAL_FAILURE_OBSERVED (read-only).
- SUCCEEDED + SETTLED + output asset + exact private evidence (same shop/job/asset, one attempt, immutable sha, UNREVIEWED) -> TERMINAL_SUCCESS_EVIDENCE_OBSERVED (read-only, NOT publication approval).
- Foreign shop, out-of-range money, ambiguous data, forged receipt, incorrect job/ledger, missing output proof -> exception and **no automatic change**.

The private output evidence reader must be trusted and backend-only, accessing `retail_private.feature3_gpu_output_evidence` through an approved service procedure. Neither a browser, log line, object filename nor customer JWT can assert it. This runbook does not implement that privileged RPC/deploy; the final operator console and an immutable provider billing meter remain incomplete. Before anyone processes an unknown billed outcome, inspect real DB logs, provider invoice and Storage bytes and obtain authorized reconciliation review. No paid inference, remote SQL write, Azure deployment, PROD or WineShopPOS modification.

Synthetic regression `tests/api/test_feature3_gpu_operator_reconciliation.py` covers queued/running, observed settled success/failure, foreign mismatch, forged evidence, missing private proof and paid quote over cap. Passing CI is not actual hosted reconciliation.

## 2026-10-29 — Current SQL double-snapshot and verified actual-byte reader composition
- `build_verified_feature3_operator_reconciliation` now connects the existing `Feature3VerifiedOutputEvidenceReader` (service-only output-evidence RPC, bounded private Storage GET, real Pillow PNG SHA/size/format, second evidence RPC) with the previously separate read-only `Feature3GPUOperatorReconciliation` service. This is a real backend composition with mocked HTTPS in regression testing; it cannot produce a success without the **unapplied** source-only output RPC being reviewed and deployed separately.
- Before reporting an observed success, the operator inspector re-reads both the exact job SQL fields and the exact spend-reservation fields **after** independently verifying private bytes. Any changed job attempt/status/output/claim/lease or measured charge/state fails closed as **uncertain**, never automatically settles, refunds or retries.
- The state inspector rejects a QUEUED row carrying a claim, an invalid RUNNING lease/token (including missing timezone), or a terminal SUCCEEDED/FAILED row retaining a claim/lease. Expired RUNNING lease is still a **HOLD**, not permission to retry.
- Tests use a genuine Pillow PNG and mock the HTTPS private Storage response, actual service RPC contract and PostgREST-backed source ports, plus inject concurrent SQL mutations midproof. No provider invoice exists: a successful operator report proves a consistent observed private-output receipt, **not** real spending, commercial title or publication approval. No DB/Storage/queue/financial state is written.
