# Feature3 authenticated generated PNG reader (source-only, 2026-10-29)

## Problem and scope

Existing `GET /api/shops/{shop_id}/feature3-gpu-jobs/{job_id}/download` returns a Supabase signed Storage URL valid up to **60 seconds**. Once issued, ordinary browser hide/logout or user role revocation cannot guarantee invalidation of the already-minted URL. This class does not change or disable the existing endpoint. It supplies a **backend-only byte reader** for a future reviewed streamed/no-cache download route with fresh per-request entitlement checks.

## Implementation

- New `azure-functions/campaign-api/feature3_private_png_reader.py`: `Feature3RevocablePNGReader`.
- Requires a **real JWT verifier**, existing user-JWT/RLS `TenantStore` and an **independent service-owned current_output_rights(shop,job,asset)** callback which must verify source/model/garment revocation and immutable private output eligibility. Never derive that callback's result from retailer POST, local demo manifest, fictional test token, UI state or a static `True`.
- Before bytes: fresh active shop membership; exact successful existing GPU job and output asset; exact immutable `{shop}/feature3/gpu/{job}/{sha256}.png`; current full rights. Uses the *user's* JWT and publishable key for `/storage/v1/object/authenticated/retailgrowth-media/{path}` **GET**, never service key, public or signed endpoints.
- Bounded HTTPS-only Supabase project origin, redirects blocked; response must be 200 with correct URL and optional PNG MIME, at most 25MiB; decode real Pillow PNG dimensions/single-frame/unsafe metadata and compare actual SHA256 to stored filename. No signed URL or object path in caller result.
- Re-reads current shop membership, job status/output identity, registered media path and independent rights **after download before returning**. If revoked midread, return denial instead of private bytes. This still is **not** an atomic SQL transaction/byte-stream revocation guarantee and does not erase bytes already delivered to an earlier consumer.
- `tests/api/test_feature3_private_png_reader.py`: CPU Pillow bytes, fake tenant/JWT, exact mocked urllib request; owner success and reauthorization twice, membership+source rights revoked during response, foreign/missing/failed media, altered SHA, invalid PNG, redirected HTTP, missing credentials/rights and no link leakage.
- API/backend `Pillow==13.0.0` dependency already exists. No new third-party provider, database schema or infra resource.

## Required coordinator / runtime integration

This is a **source-only internal primitive**. The existing signed URL route, Azure Functions binary `HttpResponse` path, frontend Blob lifecycle and real rights verifier are not wired here; adding the public versioned endpoint and changing product behavior belongs to coordinator/interface review, plus exact signed DEV multi-role Storage and browser acceptance. It also depends on Feature3 JWT GPU table path fix [PR #637](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/637); until merged, real `TenantStore` cannot query `feature3_gpu_jobs`.

Do **not** claim instant revocation of previously issued 60-second links. Complete live hosted checks including old-link token behavior, revoked user, foreign shop, revoked model/garment, stale output lease, mutated blob, private RLS, browser cache and potential bytes delivered before revocation. Real DEV currently has no GPU generated outputs; no hosted read was performed. This source cannot approve paid inference, images or publishing.

No GPU, paid provider, SQL migration, PROD, real tenant data or WineShopPOS work.
