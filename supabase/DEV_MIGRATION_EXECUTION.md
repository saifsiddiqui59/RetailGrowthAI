# Workstream P — Final approval-gated RetailGrowthAI DEV migration execution plan

**State: SOURCE/READ-ONLY PLAN ONLY. Gate 1 is NOT approved. No hosted SQL has been applied as part of P.** Supersedes no Workstream L controls: use [DEV_RELEASE_READINESS.md](DEV_RELEASE_READINESS.md) and the coordinator-owned `docs/DEV_DEPLOYMENT_APPROVAL.md` together.

## Immutable scope and current read-only snapshot (2026-10-22)
- **Only target:** existing Supabase **RetailGrowthAI DEV** project `jeearzffnjbvghwjjjrf`, Tokyo (`ap-northeast-1`), PostgreSQL 17. Never connect WineShopPOS, a different Supabase project or PROD.
- At P preflight, Supabase `list_migrations` returned exactly three applied versions: `20261022085124` (`p1_foundation`), `20261022085132` (`p1_private_media`), `20261022085503` (`p1_security_hardening`). Seven local files are absent from hosted migration history.
- P's **SELECT-only** hosted metadata inspection found: 0 public base tables lacking RLS, 1 non-public `retailgrowth-media` bucket and 0 deployed `public.job_outbox` tables. These are snapshot observations, not deployment approval.
- No backup or PITR restore **has been verified** by this workstream. Do not interpret an available dashboard backup setting as verified recoverability.
- Branch `feat/p1-dev-migration-execution`; record reviewed Git commit, file hashes, CI run, owner approval and actual live history afresh **at Gate 1**, not from this document.

## Stage 0 — safe read-only preparation, no Gate 1 required
1. Pin the exact target project ref, environment, Git SHA, operator and proposed UTC maintenance window. Take a **fresh** `list_migrations` read from the explicitly selected DEV project and copy those exact version/name pairs into a local, **uncommitted** JSON file; set `captured_at` to the actual UTC observation time, never a prefilled example time.
2. Run `node tests/security/dev-db-preflight.mjs --remote-history <local-json>` (L baseline) and `node tests/security/dev-migration-plan.mjs --remote-history <local-json>` (P plan). The P tool rejects history older than 30 minutes, non-prefix/drift, unexpected files, missing transaction wrappers and any deviation from the currently reviewed 3-applied/7-pending state. Output includes ordered SHA-256 hashes and prints **authorized_to_apply=false**. The capture timestamp is operator-entered; a valid timestamp is not a remote authenticity guarantee.
3. Compare SHA-256 for each SQL file against a reviewed artifact from that **same commit**, and independently check the diff from reviewed commit to execution commit. Freeze changes. Verify `supabase db push --help`, `supabase migration list --help` on the operator's actual CLI version. `supabase db push --dry-run` can show pending changes once a verified dedicated DEV link is configured; it MUST NOT be confused with an application, backup, or approval. Linking must be explicit and checked to avoid another project.
4. Run `supabase/DEV_MIGRATION_READONLY.sql` **only** against that DEV project using a read-only SQL client/role. Snapshot (privately) the migration ledger, public-table RLS state, policies, grants, bucket configuration and RPC security-definer settings. Record any unexpected grants, object drift, schema mismatch or existing data/job counts; stop if any. L's disposable tests must pass without cloud credentials.

**Gate 1 cannot be approved until backups/restores and risks below are evidenced.** Do not start migrations from PR CI or an automated unattended trigger.

## Stage 1 — backup, maintenance and approval (hard STOP until complete)
- [ ] Written **user Gate 1** approval explicitly names `jeearzffnjbvghwjjjrf`, the 7 exact versions below, reviewed Git SHA/hash manifest, operator, maintenance window and recovery owner. Coordinator must record decision in `docs/DEV_DEPLOYMENT_APPROVAL.md`; Workstream P has no authority to edit coordinator docs.
- [ ] Encrypted access-controlled **prechange schema/roles/data backup** captured, with backup ID, UTC creation time, retention, integrity/hash, and safely stored secret/restore credentials **outside Git/Actions logs**. Check provider-managed backup/PITR entitlement and retention rather than assuming point-in-time recovery exists.
- [ ] Preserve **private Storage bytes and object metadata**, bucket policy/config, auth-related recovery dependencies and existing queue/job state; a Postgres dump alone does **not** restore Storage object bytes. Record restore/rehydration method.
- [ ] Rehearse the **entire restore** on a separately authorized, isolated disposable environment; prove schema, required rows, policies, Auth/Storage relationships and file-byte counts/availability, and capture elapsed recovery time/RPO/RTO. Do **not** restore into the active DEV project.
- [ ] Confirm downtime/writes-freeze, paused worker and API ingestion (if any), queues/poison backlog, no active migrations, monitoring, operator privileges, expected locks and enough disk headroom. Migration 7 adds triggers and **backfills** unfinished campaign/render rows into the outbox: inspect counts; avoid an unexpected dispatch surge.
- [ ] Verify all 4 ordinary CI jobs and L's full disposable SQL/negative/RLS tests have passed against the reviewed head; review `supabase db push --dry-run` output for **exactly these seven**. Any extra migration or different target = STOP.
- [ ] Confirm allowed rollback mode (restore verified snapshot vs reviewed forward fix), criteria, data-loss window and who authorizes cutover; require explicit coordinator go/no-go immediately before action.

## Stage 2 — exact SQL sequence, only AFTER Gate 1
Do **not** execute this section during P. For a vetted CLI/version, the canonical migration-ledger-preserving path is `supabase db push --linked` against an operator-verified `jeearzffnjbvghwjjjrf` link. **CAUTION:** Supabase CLI `db push` applies **all** pending migrations in one operation; it is **not** a per-step pause or automatic rollback mechanism. If the rollout requires a checkpoint between each file, STOP and have the coordinator approve a version-preserving per-migration execution method first; do not use ad hoc SQL editor queries or MCP `apply_migration` without validating history/version behavior. Never use `migration repair` to hide drift.

| Order | Exact approved migration | Release effect / operator watch |
| --- | --- | --- |
| 1 | `20261022100400_p1_durable_planning.sql` | New campaign claim/lease fields and service-only RPC |
| 2 | `20261022101800_p1_render_claim.sql` | Render claim/lease, service-only RPC |
| 3 | `20261022162000_p1_draft_save.sql` | Browser UPDATE revoke, versioned authorized save RPC |
| 4 | `20261022173000_p1_private_upload_registration.sql` | Authenticated upload registration, private-object owner and rights metadata checks |
| 5 | `20261022180000_p1_dev_media_integrity.sql` | Canonical image paths; deny browser overwrite/registered-object deletion; leave generated-video service semantics intact |
| 6 | `20261022205000_p1_worker_execution_budget.sql` | 25-minute planner/render DB leases (20-minute host, 780-second FFmpeg cap) |
| 7 | `20261022220000_p1_durable_recovery.sql` | Transactional job outbox/poison tables, attempt fencing, replay RPCs, new-job triggers **and unfinished-job backfill** |

Each file contains explicit `BEGIN`/`COMMIT`, but **the seven-file deployment is not globally atomic**. If any file or ledger update fails, **STOP**: disable writes/dispatch, preserve backup and error evidence, reread physical schema **and** migration history, and do not blindly rerun. Record the migration result and run release checks before re-enabling traffic.

## Stage 3 — post-approval hosted validation and no-go criteria
1. Reread migration history and physical schema: **all 10 ordered versions**, no drift, `job_outbox` and `job_poison_events` RLS on. Capture schema/policy/grant diffs and required service-only execute privileges (including `reconcile_stale_jobs`, `record_poison_event`, claim/ack/complete/fail functions). Confirm registration and draft-save execute only for intended authenticated roles, not anonymous/public.
2. Run Supabase Security and Performance advisors. **Do not** run fixture SQL that edits users or Storage data on hosted DEV without a separate, explicitly scoped test-data authorization and guaranteed cleanup. L's SQL scripts mutate a disposable DB and rollback; offline evidence cannot establish real hosted Auth or Storage API behavior.
3. With specifically approved throwaway DEV identities and hosted-test permission, check authorized OWNER/EDITOR flows; deny VIEWER, revoked member, anon, cross-tenant, stale claim/fenced ACK, duplicate poison and registered upload overwrite/deletion. Use **Storage API** for object-byte operations (never raw Storage metadata DELETE). Check 25-minute lease, outbox enqueue/backfill count and dispatch idempotency before enabling any consumer.
4. Monitor errors, lock/blocking time, failed jobs, outbox lag/poison queue, consumption and Storage; reconcile incomplete states before enabling new writes. A migrated DB alone does not prove Azure Functions deployment or real licensed E2E; these remain Gate 2 and Gate 3 separately.

**No-go:** unexpected history or wrong project; missing/unrestorable backup; failed disposable CI; changed SQL fingerprints; RLS/grant regression; storage-policy failure; incomplete ledger; duplicate dispatch; unbounded backfill/locks; unresolved error or missing explicit Gate 1 approval.

## Recovery / rollback safeguards
- **Before starting:** STOP, no changes and no rollback needed if any gate fails.
- **During/after partial migration:** Stop workers/new writes. Retain exact error, successful migration versions, physical schema snapshot and job/outbox/storage state. Migration-ledger edits alone do not undo DDL. Use a reviewed forward-fix only after isolated rehearsal and renewed authorization; otherwise recover to a **verified earlier database plus Storage objects** in an **isolated restored instance**, validate tenant/RLS/rights/queues, then authorize deliberate cutover.
- Do not drop tables or disable RLS to make tests green. Capture post-snapshot writes and queue events separately: data arriving after the backup may be lost on restore unless explicitly reconciled; this is a decision for the owner.
- Restart consumers only after proof of exactly-once **database transition fencing** and at-least-once delivery recovery. Preserve fail-closed behavior and record incident/postmortem.

## P handoff to Coordinator 3
Review this plan and `tests/security/dev-migration-plan*.mjs`; accept this PR only after verified four-job CI and do not mistake merge for Gate 1. Coordinator alone updates `PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md`, `WORK_LOG.md`, and `DEV_DEPLOYMENT_APPROVAL.md`. No Azure deployment, hosted migration, hosted test identities, WineShopPOS or PROD changes in P.
