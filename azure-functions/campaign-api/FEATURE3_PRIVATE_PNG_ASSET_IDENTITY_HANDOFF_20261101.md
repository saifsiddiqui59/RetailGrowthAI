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

## 2026-11-02 — F3-08/F3-13: fail-closed authenticated PNG gateway and current-rights outages

- Same **existing PR #863** and original tasks F3-08/F3-13; no duplicate PR or changes to other feature leads. Before this batch, PR #863 had no submitted independent review and was source-only. The concrete reader accepted typed malformed `Content-Type` or a broken HTTP header accessor, and injected JWT/RLS/current-rights adapters could throw backend diagnostics rather than returning a bounded private-output denial.
- `feature3_private_png_reader.py` now validates callable HTTP methods and header accessor, strict MIME/length/encoding types, and masks unexpected HTTP transport exceptions. It independently catches current tenant membership/job/asset lookup and rights-service outages **before and after** the actual private read, never treating an exception or truthy non-boolean callback as authorization. Existing exact current-asset identity, SHA, JWT, RLS, private GET, second rights check and no signed URL are preserved.
- `tests/api/test_feature3_private_png_reader.py` adds typed/throwing headers, missing HTTP methods, runtime transport outage, initial/post-read independent rights outage, and first/second JWT/RLS adapter failures. Tests require no raw internal diagnostics, no second rights check for failed byte reads, and **no private GET** when the first authorization fails.
- **Next gates:** targeted Python regression + exact **final-head** mandatory four-job PR CI, then independent private-media/security reviewer approval, fresh main compatibility, authorized merge and fresh postmerge main four-job CI. Prior green runs are stale after these commits. No self-approval; F3-08/F3-13 remain SOURCE-ONLY IN PROGRESS, 0/33 hosted complete. Hosted no-URL route #471/#325, approved current output rights, signed two-tenant DEV checks, genuine licensed media and Azure #249 remain outstanding. No GPU, paid provider, hosted SQL, PROD or WineShopPOS mutation.
