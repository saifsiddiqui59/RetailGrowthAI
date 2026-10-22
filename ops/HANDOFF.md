# Worker reliability handoff to coordinator — 2026-10-22

Branch: `feat/p1-worker-reliability` — **ops/** and **tests/reliability/** ONLY.

## Implemented (offline, no cloud provisioning)
- `ops/recovery.py`: deterministic bounded recovery/poison decisions for canonical UUID-only messages; respects DB attempt limit (3) and lease + 60s grace, plans terminal failure when exhausted; stable fingerprint for requeue dedup.
- `ops/orphan_cleanup.py`: inventory comparison for private tenant uploads ONLY, conservative 48-hour minimum age, metadata/ETag and DB-reference recheck; no renderer output removal. Applying deletion requires explicit approval, exclusive durable claim and conditional delete; no live adapter.
- `ops/monitor.py`: offline state counts, stale (>15-minute) and actionable-job alerts without tenant IDs or tokens.
- `ops/benchmark.py`: reproducible synthetic real-engine FFmpeg execution, 30s ffprobe stream/duration/resolution validation, wall-time distribution and optional *input-rate-only* compute budget model. Run `python -m ops.benchmark --profile worker --repeats 3`. CI-size smoke: `--profile ci`.
- `ops/runbook.py`: dry-run JSON stdin CLI for recovery, poison-delivery quarantine decisions and stale tenant upload candidate inventory. No live side effects.
- `ops/ci.sh`: standalone `pytest -q tests/reliability` runner for coordinator CI integration.
- `tests/reliability/`: negative/edge/unit tests using only standard library and pytest.

## Mandatory coordinator-owned backend changes BEFORE live retry or cleanup
1. `azure-functions/campaign-api/function_app.py`: add two queue poison triggers (`retail-campaign-planning-poison`, `retail-reel-render-poison`), decode UUID-only messages, record an auditable dead-letter event and acknowledge only after a durable decision. Also schedule a reconciler for lost original deliveries.
2. `admin_store.py` plus a reviewed `supabase/migrations/**` migration: atomic compare-and-swap status transition / retry-reservation fence keyed by fingerprint and attempt/lease, and idempotent enqueue outbox. Without a transactionally written claim or outbox a scan can enqueue a job many times or lose one after a crash. At 3 DB attempts mark stale PLANNING/QUEUED/RUNNING as FAILED, not indefinitely pending. Protect tenant boundaries and revoke public mutation rights.
3. `private_media.py` / SQL: implement safe orphan cleanup with an exclusive registration-blocking fence, current storage ETag, conditional delete, audit events and inventory pagination; only AFTER cloud approval and verified media rights/registration window. **Do not wire destructive deletion from the offline planner alone.**
4. `function_app.py` / hosting configuration: set Queue trigger poison/maxDequeueCount to a documented value, visibility timeout vs 4-minute DB lease and real observed render time; avoid parallel processing of an expired lease. Test queue storage outages, duplicate messages, failed status writes and Azure Functions host restart.
5. Coordinator-owned `.github/workflows/frontend-bootstrap.yml` Python step: include `tests/reliability` in the pytest paths so this suite is run on every branch and PR. Existing 4 jobs do NOT automatically discover this directory.
6. Coordinator alone updates `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` on integration; path ownership precludes worker edits.

## Safety and evidence boundaries
- No hosted Supabase migration, Azure queue, Functions app or real media touched.
- Recovery and poison are **plans, not live handlers**; actions `requeue` and `mark_failed` are not executed unless an atomic coordinator adapter is implemented and approved.
- Compute costs require user-supplied regional rates and *do not* include networking, storage, retries, AI or Azure platform charges. Synthetic CPU timings are not production latency guarantees.
- Real end-to-end queue/poison cleanup and 1080p DEV load benchmarks require deployment approval.
- Do not touch WineShopPOS.
