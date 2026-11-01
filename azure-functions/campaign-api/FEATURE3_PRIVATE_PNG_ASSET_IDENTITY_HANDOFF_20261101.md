# Feature3 F3-08/F3-13 — independent private generated-asset identity checks

## Original task and bug

F3-08 (authenticated no-URL binary delivery) and F3-13 (forged tenant/rights/unknown-state denials) currently have source-only components and remain unaccepted for hosted deployment. The backend `Feature3RevocablePNGReader` previously trusted `tenant_store.feature3_generated_asset` to have verified the identity and private bucket of its returned asset. The current concrete `TenantStore` does enforce those fields, but the `Feature3RevocablePNGReader` constructor accepts any object exposing that method. A future injected store adapter could return a forged foreign asset ID, shop ID, wrong bucket or an `UPLOAD` row while keeping a plausible `shop/feature3/gpu/job/hash.png` path.

The private byte-reader now **independently requires** the current row's exact `id`, `shop_id`, `storage_bucket=retailgrowth-media`, `source=GENERATED`, correct PNG SHA-addressed object path and MIME. The check happens on **both** the first RLS read and again after the private Storage read, before returning any bytes. The existing live rights callback remains mandatory on both reads. This is defense in depth, not a substitute for JWT/RLS or approval.

## Tests / external blockers

- `tests/api/test_feature3_private_png_reader.py`: initial and poststream wrong media ID, foreign shop, wrong Storage bucket, uploaded/model source, or missing fields; asserts pre-stream rejection makes no private GET and never calls the rights callback, while poststream mutations cannot return already-read private bytes.
- `tests/api/test_feature3_private_binary_reader_composition.py`: exercises the complete source-only HTTP adapter with an actual Pillow-created **test fixture**, injected JWT/RLS/Storage doubles and no signed/public URLs. Opaque 404 and no private PNG/hash headers for forged identity on first or second check.
- Required verification: exact-head Part 1 4/4 GitHub Actions CI, independent private-media/security review, merge to latest `main` only after review, fresh postmerge `main` 4/4. This marks only a SOURCE-TESTED subcomponent, **not F3-08/F3-13 product DONE**.
- **Still blocked:** mounted Azure HTTP route and genuine trusted rights callback (#325/#471), licensed original/genuine output, real separate JWT OWNER/EDITOR/VIEWER/foreign/revoked DEV tests, Azure issue #249 and authenticated persistence. Do not activate previously issued signed URLs or claim instant revocation.

GPU and paid inference OFF. No hosted DEV/PROD SQL, cloud queue, live customer asset, sample poster/video or WineShopPOS change.
