# Feature #2 — 27 Oct 2026, exact DEV ledger migration release and recovery gate

Status: **READ-ONLY / DISPOSABLE TESTS, no hosted DDL**. User said “let's do it” to proceed with protected DEV schema and isolated test-identity setup following the previously stated migration-order, backup/recovery safeguards. This is not an instruction to bypass any failed gate or deploy an unrelated Feature #3 migration.

## Live, independently verified facts

- Connected only to existing healthy Supabase `RetailGrowthAI` DEV `jeearzffnjbvghwjjjrf` (Tokyo, PostgreSQL 17).
- Exactly **21 applied versions** through `20261026152102_p0_249_reel_render_intent`; Feature3 `20261026173000_feature3_model_catalog_drafts.sql` and Feature2 `20261026194000_feature2_ai_cost_ledger.sql` are not deployed.
- `shop_ai_budget_controls`, `shop_ai_spend_reservations`, and `feature3_models` are absent; one shop, one actual authenticated user, one active author and active trial subscription; no registered media or persisted content drafts.
- Supabase organization `alsak` currently reports **Free** plan. Per official [database backup documentation](https://supabase.com/docs/guides/platform/backups), daily automatic provider backups are for Pro/Team/Enterprise. Free requires a private operator-managed logical backup. No verified retrievable backup ID or independent restore proof is yet available.
- The source Feature2 ledger is additive only and creates two new RLS-on service-only cost tables, one index and two server-only budget RPCs. Its input `p_request_id` UUID blocks same-submission replay. No existing shop subscription is to be modified and no default budget is enabled.
- The previously existing one-person/one-shop trial must **not** be converted to a test STARTER subscription or spent against; TRIAL's one-call limit cannot cover both a prompt sample and a campaign. Separate controlled test fixture required if both calls are to be accepted.
- Existing South India GPT-4.1-mini Standard Azure S0 model and official public per-million token rates ($0.44 input/$1.76 output) verified in read-only OIDC run #40401262949. Owner approved **USD $0.20 maximum total** one isolated DEV acceptance exercise, NOT blanket usage.

## Reviewed exact-version promotion plan

Release only `supabase/migrations/20261026194000_feature2_ai_cost_ledger.sql` using a **version-preserving** operator-run method that preserves the original GitHub 14-digit timestamp `20261026194000` and original migration source hash. **Do not invoke** unfiltered `supabase db push` or `supabase migration up`, which would first apply unrelated Feature3. **Do not use** the Supabase MCP `apply_migration` action here: it generates a new version timestamp and would desynchronize the canonical source. Do not spoof an `applied` entry with `migration repair` alone. This action cannot run until a vetted selective migration mechanism and security review exist.

Read-only exact-version plan helper:
`node tests/security/feature2_scoped_dev_release_plan.mjs --remote-history PRIVATE_READONLY_21_VERSION_SNAPSHOT.json`
The private JSON must contain the exact project ref, `captured_at` observed time (no older than 30min), and ordered actual version/name pairs; it is never written to git or CI logs. Output computes reviewed SHA-256, confirms 21-version prefix and two source-only pending versions, chooses only Feature2 and always prints `authorized_to_apply=false`. The helper never calls Supabase.

## Recovery Gate — must be proven before hosted DDL

1. Export a **private full logical schema and data backup** for only `jeearzffnjbvghwjjjrf` from a trusted operator session with `pg_dump`/Supabase CLI `db dump` using securely provided DEV-only connection, without putting secrets on the command line, in logs, commits or public CI artifacts. Back up roles and auth dependencies as permitted; private Storage bytes and metadata must be separately considered (current registered-media count = 0, recheck immediately before release).
2. Secure the encrypted backup **outside the public repository**, with access controls, UTC timestamp, SHA-256 and retention/recovery owner. Check actual database connection and restore permissions; never assume the Supabase Free plan has automatic restore/PITR.
3. Rehearse integrity and **full restore into isolated disposable PostgreSQL**, verifying table counts, tenant relationships, RLS/grants and migration version ledger; record restored dump hash, operator and result. A `pg_restore --list` inspection alone is **not a restore rehearsal**.
4. CI additionally runs the Feature2-only reversible DDL smoke: within disposable local PostgreSQL, drop only the two new functions and tables **inside an always-ROLLBACK transaction**; verify old `shops`/`shop_subscriptions` survive and four new objects reappear after rollback. This is NOT a substitute for the private full-database backup. It is protected by exact loopback PGHOST/port and a session-only application-name marker.
5. Freeze SHA/approvals, choose a maintenance window, reconcile live auth/Storage/queues, and run an operator-reviewed exact-version dry-run. Stop on drift. Before any billable call, recheck the real actor/shop has active trial/subscription, OWNER/EDITOR, expiry and a single USD0.20 approved ledger row, USD0.05 maximum per request. Never reuse the existing actual tenant or auto-assign spending permissions.

## After separately proven recovery + scoped migration

- Hosted SELECT-only check of exact version history and expected four objects, service_role-only function grants, RLS enabled without browser access, no default spend approvals. Cross-tenant, VIEWER and browser RPC denial must be tested without affecting live customers.
- Create only specifically authorized disposable test shop/users via protected credentials, verified ACTIVE subscription and tenant isolation; do not create platform ROOT accounts casually. Record test fixture cleanup and *never* use a real customer identity as an AI test substitute.
- Enable Foundry real AI only via existing protected DEV release, secret server-only configuration, verified applicable billing, safe per-call cost bound and single-shop expiring budget. One prompt request and one seven-day text-only clothing campaign with authentic Azure token/cost receipts, human DRAFT/no publishing, no blind retries. Real current clothing trend and rights-cleared private media remain independent requirements for a **saved hosted** draft.
- Protect other feature branches, issue #249, PROD, WineShopPOS, and any external services from incidental changes.

**Actual live migration = NOT APPLIED.** **Actual Azure paid tokens = 0**. No backup/recovery proof yet. The owner may explicitly choose to waive full recovery separately, but this release plan does not presume a waiver.
