# Feature3 private evidence runtime: implementation and release boundary

2026-10-28. Continue existing Feature3 (#532/#542/#544) without waiting for
Feature2/4/5. Existing pinned FLUX.2 Klein worker and start/stop controls
are retained. **GPU and paid inference remain disabled.**

## Implemented in source

- New `poster-engine/feature3_private_evidence_io.py` bridges the existing
  `prepare_verified_model_evidence` gate to **real Supabase REST URLs**
  using the current user's signed JWT for metadata and authenticated private
  Storage GET. Caller injects `SupabaseJWTVerifier` from the existing
  campaign API; this class requires a verified user UUID and checks an active
  OWNER/EDITOR membership via the same user JWT. No public Storage URLs,
  signed links, binary output or service-role download are returned.
- Checks current original `feature3_models`, registered `media_assets`,
  exact owner-first PNG object key and true binary SHA-256/dimensions through
  the merged model evidence gate. Files are bounded at 25 MiB; redirects,
  foreign object keys, replaced data, invalid license and unsafe originals
  fail closed. The image rights/likeness authority is **separately injected
  server-only** and cannot be constructed from a customer POST body.
- New additive source migration
  `20261028210000_feature3_private_evidence_commit.sql` creates exactly
  one new `public.feature3_commit_verified_evidence` RPC, **EXECUTE only
  for service_role**; it does not grant user/anon table privileges.
  The RPC locks the current PENDING_REVIEW model and media source, verifies
  original SHA, independent legal proof digest, shop/creator eligibility
  and current active OWNER/EDITOR verifier, ensures one immutable evidence
  insert and returns a precise receipt. No model approval or paid job occurs.
  No blind upsert or uncertain-write retry is attempted. Authenticated
  retailer model approval still uses the existing *separate* human reviewer
  RPC and durable audit from migration #542.
- Disposable local Postgres regression
  `tests/security/poster_feature3_evidence_commit_negative.sql` and
  synthetic mocked-HTTP/PNG test
  `tests/media/test_feature3_private_evidence_io.py` verify service-only
  grants, same-shop rights, altered SHA, failed license, replay, redirect
  and original-blob identity. Fixture marketing images and legal rights
  are intentionally fictional, **not real licensed model assets**.
- Migration inventory/preflight is updated to recognize exactly this
  migration while preserving historic DEV release `authorized_to_apply=false`
  and rejecting surprise migrations. All source tests run in GitHub Actions
  and disposable local Supabase only.

## Still NOT production/live

The actual hosted reviewer/evidence migration #542 is not deployed; neither
is this new writer. Tests inject a fake independently verifying rights
service; we have NOT reviewed source provider licenses, original models,
commercial likeness rights, or generated a realistic kurti. The real
`SupabaseJWTVerifier` must be instantiated for the exact active Supabase
issuer by a secure worker handler, and the independent license-verification
provider configured with its actual validated evidence source. Source
permissions and transaction checks are valuable but cannot prove the
legitimacy of external legal documents. No live Storage requests or hosted
SQL writes were issued.

Additional requirements before feature completion: actual signed retailer
import/review UI and its trusted private Storage lifecycle, continuous
revoked-rights fences through Feature2/4/5, generated private output/outbox
settlement and secure download, accurate VTON human fidelity checks, true
licensed media and hosted signed acceptance, and original Azure #249
reliability. GPU remains OFF until separately approved bounded run and
cost/cleanup review. No WineShopPOS or PROD touched.
