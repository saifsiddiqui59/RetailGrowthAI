# Feature3 private generated PNG binary — full source composition tests (2026-10-29)

## Scope
Added `tests/api/test_feature3_private_binary_reader_composition.py` to test the **existing** `Feature3PrivateBinaryHTTP` adapter together with the real `Feature3RevocablePNGReader`, rather than testing only a fake abstract reader. Tests create actual PNG images with Pillow and mock the existing authenticated private Supabase Storage GET; the fake user token, RLS membership and source-licence callback are **fixtures**, not genuine customer approvals.

## Evidence tested
- A current signed-user/tenant-scoped `SUCCEEDED` job and generated `media_asset_id`, deterministic immutable private SHA-named PNG path, actual PNG decode and SHA256, strict binary integrity response headers and absence of public/signed URLs, no real provider inference or queue consumption.
- Independent pre-and-post-GET role and rights checks are invoked twice; membership revoked after the first check and output licence revoked after the private GET both result in an opaque 404 with **zero PNG bytes returned**. Wrong-shop paths, expired/failed job, rejected authorization and unsupported HTTP method never perform private Storage GET.
- Wrong announced HTTP Content-Length, unexpected gzip response, changed-but-valid PNG bytes, backend membership outage and authenticated reader uncertainty fail closed; they do not disclose a private object path or retry financial/queue operations.

## Honest release blockers
No actual authenticated Azure route is mounted for `/api/shops/{shop_id}/feature3-gpu-jobs/{job_id}/private-png`; the production output-rights authority is not deployed, and the read-only SQL model/evidence RPC proposals remain unapproved for hosted DEV. The synthetic signed token and fake rights callback in these tests are NOT legal provenance. A real signed retailer/user, live RLS, independent commercial image rights and registered private output are required before any hosted acceptance can be claimed. No hosted SQL migration, GPU spend, media publication, queue ACK, PROD or WineShopPOS change.
