# Feature3 F3-13 — signed PNG render-time URL fence (source-only)

Owner: Feature3. Target: coordinator review against `main`.

## Scope
- Reject a forged, foreign-shop, foreign-job, public, non-PNG, wrong-scheme, non-Supabase, malformed-token or over-parameterized generated-image signed URL at the final React presentation boundary.
- Preserve existing upstream exact configured Storage-origin validation in `createFeature3Api.getGeneratedImageDownload`, 60-second server expiry, 55-second client lifetime and tenant/day/request epoch checks.
- This is a defense-in-depth guard for the already-issued URL flow. It **does not** authorize a download, revoke a previously copied signed URL, deploy an API, or assert production rights.
- Regression tests use invented identifiers and synthetic URLs only. No GPU, AI inference, private media, SQL, PROD, or WineShopPOS access.

## Evidence and coordinator task-status proposal
- Task: `F3-13` (cross-tenant, rights and ambiguous-ACK regressions), sub-scope: final signed-link URL rendering denial.
- Changed source: `frontend/src/features/creative/feature3-signed-link-scope.mjs`.
- Test: `tests/frontend/feature3-private-generated-download.test.mjs` (malicious URL matrix and legitimate fixture).
- Integration status: **IN PROGRESS / source proposal**, not DONE. Only coordinator may merge, update `coordination/task_progress.json`, or claim postmerge four-job CI.
- Remaining F3-13 acceptance: hosted signed JWT/RLS cross-tenant negatives and genuine provider/queue failure injection; dependencies: #471/#325 (coordinator mounted signed private route), #249 (Azure reliability lead, reliable signed DEV), F3-LICENSED-MEDIA (Feature3 rights owner, independently approved original), and current two nonprivileged DEV accounts not yet provisioned.
- If this branch is accepted, coordinator should record a reviewed source-only evidence event for `F3-13` with PR number, exact head SHA, CI runs, and merged-main SHA. Do not promote the full package to DONE without the remaining acceptance.
