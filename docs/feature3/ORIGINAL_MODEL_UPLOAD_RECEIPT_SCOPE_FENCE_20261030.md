# Feature #3 — original model Storage receipt scope fence

**Tracked packages:** F3-11 (private model original upload), F3-13 (tenant/rights negative regression). Source-only, GPU OFF.

The browser must not issue a second non-idempotent model-registration POST after an untrusted private Storage response. `verifyPrivateModelOriginalUploadReceipt` now requires the exact current shop UUID, model UUID, immutable SHA256-based private object path, bounded byte length and explicitly unverified/unregistered flags. The signed workflow invokes this check before registration, and exposes only the digest to the API. Offline Node tests reject foreign shops, stale model/path, altered hashes, oversized/missing bytes, forged rights/approval and extra authority fields.

This does **not** prove the actual private bytes, legal likeness/commercial rights, Supabase DEV authentication, independent human approval or hosted persistence. It cannot enable GPU inference, queue dispatch or production output. The existing two DEV shop-owner accounts still require verified provisioning and signed hosted tests.

Review gate: exact-head 4/4 CI, coordinator PR review/merge, then fresh main 4/4. F3-11/F3-13 remain **source partial**, not integrated/hosted DONE, until all original acceptance criteria are met. No PROD, hosted SQL writes, GPU or WineShopPOS.
