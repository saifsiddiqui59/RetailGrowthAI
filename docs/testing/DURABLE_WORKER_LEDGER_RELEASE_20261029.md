# Testing Chat: protected worker span ledger — source-only proposal

## Design and trust boundary
A second, separate PostgreSQL ledger `retail_private.feature_worker_spans`
is proposed for **trusted service-generated worker observations**, not retailer
feedback. `public.feature_test_events` is only a **browser observation /
subjective quality** store; user-written PASS in that table is not evidence
that backend FFmpeg/Foundry actually ran. Never merge the two trust levels.

`supabase/release-candidates/20261029120000_feature_worker_trace_spans.sql`
is source-only; it remains outside the exact canonical migration directory.
No hosted RetailGrowthAI DEV or production change is made by this PR.

## Authenticated boundaries
- Service-only `public.retail_feature_worker_append` RPC accepts a tightly
  bounded backend span, checks `auth.role()=service_role`, derives tenant
  shop from the **actual existing campaign/render job**, checks terminal
  status and attempted claim number, checks seven persisted draft days or
  real terminal private Reel output asset, and deduplicates each operation.
  It rejects an unauthorized F5/unknown feature, forged failure on a DRAFT,
  premature success before complete, mismatched attempt or arbitrary
  metadata. No arbitrary `shop_id` is supplied to this write API.
- Signed `public.retail_feature_worker_spans` read RPC requires active
  OWNER/EDITOR membership for the shop at **each read**, and uses exact
  shop and job filters with a 1–50 event bound. No direct browser table
  grants; VIEWER, anon and foreign shop reads are denied.
- Stored fields are bounded feature, operation, terminal status, attempt,
  elapsed duration, minimal metadata and time; never store prompt text,
  raw license evidence, JWT, object path, signed URL or provider secret.
  Source worker-spans are still **not persisted** unless a reviewed backend
  sink explicitly calls the service RPC after the schema is hosted.

## What remains
- This PR only supplies reviewed candidate schema + isolated disposable
  PostgreSQL negative tests; it does not install it, expose live API, create
  a background worker, change queue payloads or replace project history.
- Next source milestone: wire the optional worker callback to a service-only
  PostgREST client after the current claim/lease-fenced DB terminal step.
  Backend failure to ingest span should be independently observable, not
  concealed as a successful audit event; it must not double-render.
- Next reviewed DEV release: independently verify canonical 31-version
  history, separately version the SQL, do a migration/readiness/rollback
  review, apply only to RetailGrowthAI DEV; verify signed OWNER/EDITOR/VIEWER
  and cross-tenant reads with no fake authentication. User intent to test
  does not waive technical safety guards.
- Next UI milestone: consume actual server-verified span RPC from signed
  TEST owner/EDITOR, correlate by existing private campaign/render job UUID,
  and label a worker step `BACKEND_VERIFIED` only with this RPC evidence.
  Never mark a browser `PASS` as a server success.
- #249 Azure 503 remains a separate reliability gate; unavailable or
  unconfirmed HTTP POST/ACK still means UNKNOWN, not FAILED.

No GPU/API spend, social publishing, PROD or WineShopPOS changes.
