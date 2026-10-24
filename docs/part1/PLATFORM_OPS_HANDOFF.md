# Part 1 Platform Operations — Persistent Super Admin monitoring

Source branch: `feat/p1-platform-operations-inbox`; schema `20261024190000_p1_platform_operations.sql`.

## Scope
- Root-only, per-admin persistent **read/unread** history and resolved-event history. Private `retail_private.platform_notifications` and `platform_notification_reads` tables, no browser table write, no app-metadata root bypass.
- Read-time transactional reconciliation of **real Supabase job statuses**: failed campaign, video and poster jobs; persisted poison receipts; delayed planning/video and poster outboxes; stale DB render/poster leases. Each alert has stable dedupe key, first seen, last seen and resolved status. Fail closed on query/migration problems.
- **Database-backed health only**: a successful verified RPC proves that the database responded at the recorded time. The SQL outbox is NOT the live Azure Storage Queue depth; Azure Functions, infrastructure uptime, real queue depth/scale alarms are marked `NOT_CONNECTED`. Full Azure Monitor connectivity remains a separately permissioned, future extension. No fictitious cloud checks, emails or auto-remediation.
- Full-provider, database-counted subscription statuses/search with bounded 25-row pages: upcoming seven days, expired, suspended, unknown and other active. The global summary is calculated from all shop subscriptions independently of pagination. Existing manual plan changes remain audited; no billing/renewal features added.
- UI uses the existing DB-verified `PlatformBoundary` and only allowlisted user-JWT RPCs. Persistent read receipts are personal to each verified root. Nonroot/anon users never access the records or issue changes.

## Tests and rollout gates
- New source-only SQL migration adds private tables/RLS, root-authenticated RPCs and transactional event sweep; no migrated DEV/PROD data or deployment claimed. It is later than existing poster migrations and separate from the email backlog.
- `tests/security/notification_platform_operations_negative.sql` exercises cross-shop denial, root revocation, per-root read receipt isolation, true DB job/queue signals and 55-shop global server pagination in disposable Postgres. Browser mock tests check UI read/unread, root navigation denial and global search.
- Before **any hosted DEV** migration: coordinator reviews final main/Part2/3 schema compatibility, remote migration prefix and role/security lints, rollback/backup evidence, owner-authorized operator scope. Apply via tracked Supabase CLI under one writer, then deploy approved existing DEV Free SWA (no new resources). Signed-in root/nonroot hosted E2E required. Never enable `RETAIL_NOTIFICATIONS_ENABLED` or configure SMTP.
- Current in-app snapshot must continue to show failure rather than fake zeros if the new RPC is not deployed. Rollback UI to prior read-only root page if hosted schema activation is deferred. No WineShopPOS/PROD or Part2/Part3 writes.
