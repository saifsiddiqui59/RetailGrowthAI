# Feature #3 — generated output download must have independent human review

Date: 2026-10-28. GPU remains OFF. Existing `SUCCEEDED` GPU status is a
durable worker settlement, **not** proof of accurate garment fit, valid
model likeness rights, original-byte integrity or human approval.

## Source behavior

`Feature3V2API.gpu_download` is now fail-closed even for existing
registered, same-shop `SUCCEEDED` output PNGs. It will not call
`TenantStore.sign_download` unless a **server-injected**
`verify_reviewed_output` callback independently returns exact
`shop_id/job_id/media_asset_id/image_sha256`, positive versioned
`HUMAN_REVIEW_PASSED` state and current independently checked rights:
`human_confirmed`, `private_bytes_verified`,
`source_rights_current`, `commercial_use_cleared` and
`rights_revoked=false`. It also checks the exact immutable
`{shop}/feature3/gpu/{job}/{sha256}.png` owner-key shape.
Any missing or inconsistent proof returns HTTP 409
`OUTPUT_REVIEW_REQUIRED`, **without generating a signed URL**.

This interface reuses the current JWT/tenant membership and generated
media registration checks; it does not add a public output approval
endpoint, GPU invocation or user-supplied review. Source tests use
fake callback receipts; there is no real durable human-reviewed output
ledger or injected hosted production verifier yet.

## Next actual work

Create a secure per-output rights/human-review ledger and verifiable
private byte SHA check, then inject that verified service at the
authenticated backend. Keep related output metadata and generated asset
registration fenced to exact one-shot GPU job claim and measured
prepaid settlement. Ensure expired/revoked source/model rights block
downloads and short-lived URLs cannot be reused after revocation
(use very short TTL, no caching and explicit invalidation strategy).
Actual reviewed garment/photo accuracy requires a separately licensed
VTON provider and genuinely reviewed customer images; a synthetic
Pillow mock is not such a review.

Azure Functions original 503 #249, hosted DEV migrations and real
signed retailer approval are separate external release blockers.
GPU, paid CUDA and hosted DEV/PROD remain unchanged. Never modify
WineShopPOS.
