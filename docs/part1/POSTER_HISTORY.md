# Part 1 — saved poster history and reopening (source only)

The existing Creative Studio could save/generate a private poster but lost its
`poster_id` and `job_id` after navigation or browser refresh. This feature
adds a bounded, authenticated **read-only** history for each saved campaign day.

## Contract
- `GET /api/campaigns/{campaign_id}/days/{day_id}/posters`
- The Azure handler verifies a Supabase bearer JWT, loads an RLS-visible
  campaign, checks that the requested day belongs to that campaign and that
  the user still has active shop membership.
- TenantStore queries only `poster_drafts` and `poster_jobs` with the same
  authenticated JWT and exact shop/campaign/day filters. At most **21** draft
  records and job states are returned; unexpected cross-tenant records fail
  closed. No media object paths, service credentials or signed URLs are in
  this response.
- Cloud download still mints a fresh 60-second signed URL through the
  existing `GET /poster-jobs/{id}/download` route; no persisted signed links.
- Creative Studio explicitly offers **Find saved posters** and **Reopen saved
  design**, restoring brand, palette, template, approved offer and registered
  image ID; finished job status restores private download/selection controls.
  Changing design options invalidates the selected poster rather than
  silently overwriting approved output. Browser-local PNG export remains
  separate from cloud output.
- No new migration, billing, queues, publishing, Wan features, or hosted
  rollout are required by this **source-only** change.

## Verification / remaining gates
- Auth/tenant/day negative API tests in
  `tests/api/test_poster_history.py`.
- JWT/origin/UUID client tests in
  `tests/frontend/poster-history.test.mjs`.
- Full four-job PR CI and post-integration checks are required before final
  coordinator handoff.
- Real DEV E2E (sign in, save, browser refresh, reopen, view signed private
  PNG, attempt wrong-shop access) requires separately approved Azure worker,
  queue, migration and front-end release. Do not claim it passed on source CI.
