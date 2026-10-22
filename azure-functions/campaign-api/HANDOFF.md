# Workstream I — durable recovery coordinator handoff (source-only)

Branch: feat/p1-durable-recovery. Do not merge this file's branch before four checks pass and migration/security review.

## Implemented
- Transactional INSERT triggers write planning/render outbox entries in the *same PostgreSQL transaction* as each accepted job.
- Backend HTTP mode returns 202 after commit, independent of transient Azure queue availability (existing mock/legacy unit mode intentionally retains synchronous semantics). Outbox timer claims with CAS leases and sends only UUIDs, confirming delivery with token CAS; lost confirmation causes safe at-least-once replay.
- Planning completion writes days and final DRAFT atomically; render completion writes generated metadata and SUCCEEDED atomically. Both require the current attempt and random DB-issued token plus an unexpired lease. Failure RPCs use the same fencing; expired worker cannot downgrade or overwrite successful attempts.
- Render output path includes claim token to prevent previous attempt object collisions.
- Azure poison queue handlers record deduplicated event fingerprints in a private DB table before ACK, never accepting queue-supplied tenancy or file paths. Timer reconciliation replays old unleased jobs and terminalizes exhausted attempts; queue-send retry exhaustion is bounded.
- Python reliability failure-injection tests and migrations are included; no storage DELETE and no user credentials/PII in messages.

## Explicit gates / unknowns
- New migration 20261022220000_p1_durable_recovery.sql is **UNAPPLIED**; it relies on all prior migrations including 25-minute budget.
- Only coordinator may update docs/PROJECT_STATE.md, docs/NEXT_TASK.md, docs/DECISIONS.md, docs/WORK_LOG.md and shared workflow / contracts. Record this handoff as source-only, then verify latest main CI after merging.
- Existing GitHub CI applies the new migration on a disposable Supabase DB; Python offline tests exercise queue/DB failure paths. Real live Azure poison/replay, Flex timer identity, hosted worker data, tenant revocation races, TTL retention and end-to-end paid resource performance are **UNVERIFIED**.
- Until authorized DEV migration plus cloud hosting and real 1080p licensed-content benchmarks, **do not deploy**. Azure GitHub OIDC was independently reverified read-only in coordinator PR #30; DEV resource-group IAM and any deployment authorization remain separately unverified.
- WineShopPOS has not been touched; no cloud resources created or changed.

## Coordinator decision request
Confirm host and queue SDK message encoding against Azure Functions queues extension in an approved isolated DEV smoke test; verify timer host storage, concurrency and cold-start behavior. Preserve the read-only CI credential model and audit poison retention/alert thresholds before any deployment.
