# Current trusted backend worker RPC negative tests (2026-11-18)

Original historical [#627](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/627) head `6ef9788a26661c07a3feb851dfe1cb0209b310da` provided tests targeting the old `readTrustedWorkerSpans` interface. Current main `trace-store.mjs` instead exposes `listWorkerSpans(shopId, jobIds)`, with current signed-user token, publishable Supabase key, read-only POST RPC over exact HTTPS origin, 1–5 distinct IDs and server-bound response source/tenant/job/feature/status/attempt/duration. Do not restore deprecated UI or old method.

Added deterministic test-only `tests/frontend/feature-testing-worker-current-rpc-isolation.test.mjs` using fake transport, asserting signed headers and no service key, bounded per-job reads, missing/denied RPC denial, foreign tenant/job, malformed source/status/attempt/elapsed, duplicate job-input denial and no-JWT fail-closed. No hosted Supabase, actual backend worker spans or real tenant test identity is exercised.

Complete original #627 changed-file GitHub patch is preserved in `frontend/src/features/testing/source-archives/PR_627_ORIGINAL_WORKER_LEDGER_DIFF_20261118.md`, but archival is not live behavior acceptance. Current main still needs independent authorized backend RLS/store/read E2E and reviewer verification before any trusted worker/output or original feature task is marked DONE. Strict event-id uniqueness, operation/metadata semantics, and one-to-one correspondence with private spans require separate affected security review; this test-only patch does **not** claim those invariants or modify current auth logic.

No GPU/paid providers, production/DEV SQL writes, Azure, real jobs, licensed images, or WineShopPOS modifications.
