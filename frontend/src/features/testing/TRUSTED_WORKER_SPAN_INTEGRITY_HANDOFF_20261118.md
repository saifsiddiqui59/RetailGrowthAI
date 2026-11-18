# Signed worker span RPC response-integrity hardening (2026-11-18)

The current browser `createTraceStore.listWorkerSpans(shopId, jobIds)` trusts the signed server-side PostgREST RPC `public.retail_feature_worker_spans`, backed by the SOURCE-ONLY release candidate `supabase/release-candidates/20261029120000_feature_worker_trace_spans.sql`. It already uses the current retailer JWT, a publishable API key, an exact HTTPS tenant origin, bounded job inputs, and authenticated shop/job/source matching.

This scoped change closes an outstanding **defense-in-depth** gap: before exposing any fetched worker rows to TestingConsole or report downloads, require the exact ten SQL-returned fields; parseable timezone-aware receipt timestamps; valid unique UUID event IDs within/across job requests; F2/F4 operation/status combinations; bounded attempts and duration; and strict completion-vs-denial metadata aligned with the existing SQL worker-append contract (7-day dev_mock/foundry plan, or 1080×1920 H.264/AAC ~30s synthetic renderer).

- Updated the two existing fake-transport unit fixtures to include the SQL receipt timestamp, complete planner metadata and per-job unique event IDs without changing the production RPC function signature.
- Added `tests/frontend/feature-testing-worker-current-rpc-integrity.test.mjs` with positive current F2/F4 records and negative forged IDs, fields, timestamps, mismatched operation/status, unexpected metadata, duplicate row IDs, foreign job reuse and invalid media metrics.
- The reader now denies the entire result on any inconsistent row; **no partial result is returned** from a later failed job, no automatic retry and no browser promotion of source evidence into commercial publish rights.

**Boundary:** This is a browser-side check over fake-transport tests only, **not** proof that the backend truly wrote the worker receipts, that RLS/migrations are deployed, that hosted shop identities work, that any model rendered video, or that any source media is licensed. No changes to SQL, Cloud/DEV/PROD, service keys, billing, GPU, model inference, WineShopPOS or shared interface v1.

The change affects cross-feature F2/F4 worker trust display and therefore **requires independent affected feature/security reviewer** before merge under `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`; exact final PR-head 4/4 CI and fresh postmerge main 4/4 are mandatory. Until hosted proof, related original feature tasks remain IN PROGRESS.
