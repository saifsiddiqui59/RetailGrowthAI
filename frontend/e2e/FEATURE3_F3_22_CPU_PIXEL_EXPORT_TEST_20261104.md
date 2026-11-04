# F3-22/F3-13 — synthetic CPU poster pixel-export integration test (2026-11-04)

**Source-only, offline.** A real Chromium + mocked JWT/campaign route starts the
existing authenticated Campaign UI, opens Feature3 CPU Studio, generates a
1080x1920 vertical story draft, downloads day-bound JSON and PNG, and then
independently decodes the PNG in Chromium. The test verifies a valid PNG
signature/IHDR, bounded bytes, actual nonblank coloured pixels, no unapproved
90% promotional claim in the structured design, no uploads/remote GPU renders,
and no Storage signed opens.

This advances original F3-22 synthetic source-test coverage and F3-13 negative
tests; **it does not complete the original F3-22 hosted task**. All users/shops,
business details and captions are mocked; no customer rights, true signed DEV
JWT/RLS, remote PNG binary route, approved output, payment or production
deployment is claimed.

Run the existing `frontend/e2e/campaign-journey.spec.mjs` through GitHub Part1
frontend browser CI. Merge only after exact-head 4/4 and verify fresh main CI.
Document exact PR/CI in the project state once accepted. GPU and paid
providers remain OFF. No WineShopPOS or hosted DB/DEV/PROD changes.
