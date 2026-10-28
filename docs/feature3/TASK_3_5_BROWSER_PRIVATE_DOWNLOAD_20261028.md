# Feature3 Task3.5 — Signed private generated-image history + UI (2026-10-28)

Source-only, **no generated FLUX output yet**. This change reuses the existing
JWT/RLS `feature3_gpu_jobs` table and 60-second private PNG download endpoint.
It adds a bounded per-shop history read and explicit read-only browser buttons
that retrieve the existing signed URL on demand, only for `SUCCEEDED` jobs.

- `GET /api/shops/{shop_id}/feature3-gpu-jobs` checks current active membership,
  then reads status-only rows with the same user JWT and database RLS. Max 20
  records, no paid GPU submit or output path and no other-shop entries.
- The frontend matches the job, asset UUID, exact private shop/job/sha PNG key,
  configured HTTPS Supabase Storage origin, a single signed token parameter and
  precisely 60 seconds before offering a link. Untrusted response URLs are
  rejected. The URL remains short-lived; no public image path is stored.
- Controls require opt-in Feature3 v2 host and live signed-in API. This does NOT
  enable GPU generation, certify pixels, skip human image approval, or publish.
- Python actual-router tests and Node frontend/JSX tests are offline using fake
  JWT/verifiers and response fixtures. Not live tenant or Storage proof.

Still pending: actual GPU worker private byte writer, same-shop immutable media
receipt, SHA-256 verification, current rights/revocation after issuance, private
orphan cleanup, genuine signed DEV account/image, model approval and CUDA.
No paid resources, PROD or WineShopPOS modifications.
