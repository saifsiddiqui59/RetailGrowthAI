# RetailGrowthAI DEV Supabase — Approval-Gated Database Release Runbook

**Status: readiness source only; no hosted migration authorized or applied.** This guide targets only the RetailGrowthAI DEV Supabase project `jeearzffnjbvghwjjjrf` (Tokyo), not WineShopPOS or production. Worker and Azure rollout are separate approvals.

## Verified read-only history — 2026-10-22

Supabase's read-only migration listing reported exactly:

| Remote version | Migration | Status |
| --- | --- | --- |
| 20261022085124 | p1_foundation | applied |
| 20261022085132 | p1_private_media | applied |
| 20261022085503 | p1_security_hardening | applied |

The following **seven** local migrations are **not** present in the DEV migration history. Apply only in ascending version order **after explicit approval**:

1. `20261022100400_p1_durable_planning.sql` — planning claim/retry and lease RPC
2. `20261022101800_p1_render_claim.sql` — renderer claim/lease
3. `20261022162000_p1_draft_save.sql` — protected draft save RPC
4. `20261022173000_p1_private_upload_registration.sql` — owner-bound private Storage object registration
5. `20261022180000_p1_dev_media_integrity.sql` — canonical upload paths, deny overwrite/rename/registered-blob deletion
6. `20261022205000_p1_worker_execution_budget.sql` — 25-minute claim leases for 20-minute host budget
7. `20261022220000_p1_durable_recovery.sql` — transactional planning/render outbox, attempt fences, poison receipts, replay and recovery

**History is mutable in reality; this date-stamped observation is NOT a fresh release-time authorization.** Always fetch the live history again just before approval/deployment.

## Read-only preflight (safe to run now)

1. Confirm target repo, branch, DEV project ID and the current reviewed commit; never assume the currently logged-in Supabase project is DEV. Use a read-only Supabase migration history listing or the CLI's documented `supabase migration list` after inspecting `--help`; do not link or change a production/WineShopPOS project.
2. Prepare an **uncommitted** JSON file with the *fresh read-only DEV* migration history, not a guessed or copied historic value:

    ```json
    {
      "project_ref": "jeearzffnjbvghwjjjrf",
      "applied": [
        {"version":"20261022085124","name":"p1_foundation"},
        {"version":"20261022085132","name":"p1_private_media"},
        {"version":"20261022085503","name":"p1_security_hardening"}
      ]
    }
    ```

    This is an **example snapshot**, not an instruction to overwrite any existing history. As migrations are deployed, update it from the actual DEV history.
3. Run from repository root: `node tests/security/dev-db-preflight.mjs --remote-history /path/to/fresh-dev-history.json`. The command checks project ID, a complete applied prefix, strictly increasing unique timestamps, file presence and critical RLS/outbox/RPC syntax; it reports pending SQL files. It cannot connect to or mutate Supabase.
4. Run automated disposable-database checks through standard four-job GitHub Actions CI. Existing security CI executes both Node migration preflight tests and `tests/security/durable_recovery_negative.sql` through `rls_negative.sql`. SQL checks use a transaction that rolls back on a local Supabase instance. **This is not proof of hosted RLS behavior**.

**Hard STOP** on unknown remote migrations, version/name drift, missing migration, skipped version, non-prefix history, unauthorized project, new unexpected object GRANT, failing negative test, or insufficient recovery evidence. Do not use `migration repair` to conceal drift: it changes tracking state, not physical schema.

## Required owner/coordinator approval before any hosted change

- Written approval naming **this precise DEV project**, exact reviewed commit/PR and migration list; separate authorization required for Azure provisioning and migration execution.
- Capture recoverable pre-release backups for **both schema/data and Storage metadata/objects** as appropriate; verify restore path and recovery point on a separate test project. Snapshot the migration ledger and grant/policy definitions. Record backup identifiers privately, **not** in Git.
- Stop new HTTP/worker writes and queue consumers for the migration window. Pending jobs can be backfilled by the final migration; coordinate restart and reconciliation deliberately, and keep a record of preexisting in-flight claims.
- Approve maintenance window, on-call ownership, rollback/restore criteria and monitoring, then run the seven scripts in order using an authorized, scoped operator process. **Do not apply from this workstream's PR or GitHub PR CI.**

## Post-approval verification checklist (must be performed on hosted DEV)

- Requery migration ledger: all ten local versions exactly match the hosted prefix; no extra/unrecognized versions or partially recorded application.
- Check `public.job_outbox` and `public.job_poison_events` have RLS enabled and **no** `anon`/`authenticated` CRUD grants; verify all claim, ack, completion, failure, poison and reconcile RPCs have EXECUTE only for `service_role`.
- Verify outbox triggers for campaign and render records, no duplicate dispatch for job ID, poisoned fingerprint idempotency, lost-ACK retry, expiring outbox claim, stale attempt denial, and a permanently exhausted job transitioning to FAILED.
- Check the `retailgrowth-media` bucket remains private and tenant-rooted. Validate **with the hosted Storage API**, not direct `storage.objects` deletion, that other tenants and VIEWER/anon cannot upload/read/update, and a registered source cannot be renamed, overwritten or deleted by browsers. Validate authorized owner/editor creation and the registration RPC.
- Verify cross-tenant RLS on shops, membership, media, campaign days, render jobs, plus revoked membership; verify draft-save optimistic conflict denial and user cannot directly update protected status.
- Run Supabase security/performance advisors. Capture evidence for an approved throwaway DEV identity/test tenant without exposing credentials in CI. Do not claim live media processing or licensed delivery from SQL tests.
- Validate actual worker/queue lifecycle only following **separate Azure approval**; confirm 20-minute Functions host, 25-minute claim lease, 780-second FFmpeg limit and resource quotas in the target host, with alerts and real benchmark.

## Restore / rollback decision

These migrations add columns, tables, triggers, indexes, functions, grants and private Storage restrictions; **there is no guaranteed safe generic SQL DOWN**. Never blanket-drop the schema or simply delete migration history rows. If preflight fails, **do not start**. On any failed hosted migration, freeze writes, capture exact error, migration ledger and current schema, and have the operator decide either (a) a reviewed **forward-fix** migration with an isolated rehearsal, or (b) restore to a **verified earlier backup/PITR** in an isolated restored instance and cut over only with approval. Account for client writes, queue messages, object bytes and backups beyond Postgres. Migration ledger repair alone does not roll back DDL/data. Do not reconnect workers until state, replay invariants, RLS and object ownership are reverified.

## Residual blockers

The tests are SQL/disposable and source-only. Hosted auth/storage API, cost/sizing, Azure worker packaging and commercial image licensing still require verification. A 50 MB shared private media bucket does not itself implement per-tenant storage quotas or orphan cleanup. No Supabase-hosted migration, Azure deployment, new PROD project, or WineShopPOS change is part of Workstream L.
