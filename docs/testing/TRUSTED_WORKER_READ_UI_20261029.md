# Testing Chat — signed private worker-span evidence panel

## Source change (no hosted deployment)
The existing private backend worker ledger already lives in
`retail_private.feature_worker_spans` as release-candidate SQL. Its authorized
read entry point is `public.retail_feature_worker_spans(p_shop_id,p_job_id,p_limit)`,
NOT an exposed public worker table.

This UI extends the existing Testing Chat route without creating a parallel
worker-ledger schema or public table grants. It reads no more than five distinct
job IDs from browser-observed F2 campaign or F4 FFmpeg events, performs one
signed Supabase PostgREST `POST /rest/v1/rpc/retail_feature_worker_spans`
per job, with `p_limit=10`, then fail-closes on wrong `source`, shop, job,
feature, status, attempt or duration. It does not put service keys in the
browser. The RPC itself enforces fresh tenant OWNER/EDITOR role and active
membership, with no VIEWER, foreign or anonymous access.

The panel is opt-in per selected test, displays the service-authored records
separately and does not promote the original browser PASS to a backend PASS.
A referenced job ID is still based on a browser-authored receipt; that link
does NOT independently prove which Testing Chat run initiated the job.
Absent RPC/schema/rows show an explicit unavailable/not observed message,
never a fabricated worker failure.

## Verification
- Source Node tests assert signed JWT headers, exact private RPC rather than
  direct table, absent service-role key, bounded requests, no retry on
  transport errors, and foreign-shop/job/unsupported-feature rejection.
- Existing isolated Supabase CI covers protected `retail_private` ledger
  and its RLS/role-denial tests. Four exact-head CI jobs, postmerge main,
  reviewed canonical SQL release, actual Functions flag activation and
  signed hosted two-tenant E2E remain separate gates.
- This PR intentionally closes no Azure issue #249, does not deploy the
  new trace schema/worker ledger or frontend and does not trigger paid GPU,
  provider requests, social publishing, PROD or WineShopPOS writes.

## Integration context
Earlier candidate PR #626 was closed unmerged because it duplicated the
existing more restrictive private ledger with a second public-schema table.
Only the narrow UI consumer was retained and rewritten against the existing
RPC to keep one authoritative worker-span architecture.
