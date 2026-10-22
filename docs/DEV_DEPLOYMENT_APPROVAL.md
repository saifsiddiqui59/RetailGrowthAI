# RetailGrowthAI — DEV deployment approval checklist

**Status: NOT APPROVED.** This is a decision record/template, not permission to deploy, provision, execute hosted smoke or apply hosted database migrations. Date: 2026-10-22. No WineShopPOS or production resources may be used.

## A. Identity, scope and budget (all required)
- [ ] Record requested action and change owner, designated approver, date/time, exact `main` SHA and successful four-job CI run.
- [ ] Record dedicated RetailGrowthAI Azure subscription, **DEV resource-group name and subscription-scoped resource IDs**, region **Central India**, and explicit evidence effective GitHub OIDC principal has only the intended minimum role at **that resource-group** scope. OIDC login alone does not prove IAM scope; do not use subscription-wide Contributor/Owner.
- [ ] Confirm existing RetailGrowthAI DEV/pilot Supabase project **jeearzffnjbvghwjjjrf** (Tokyo) is the only hosted DB target and that project selection, active migration history and environment isolation were reviewed; PROD is not created/authorized.
- [ ] Identify Azure runtime/Storage/queue names, resource tags, expiry and cleanup owner; confirm no collisions with other projects, especially WineShopPOS.
- [ ] Record current pricing assumptions, max DEV monthly spend, Azure Cost Management alerts, instance/concurrency/retention caps, Storage budget, and abort/cleanup threshold. Verify region/SKU/quotas before provisioning.
- [ ] Confirm secrets are environment-scoped, least privilege, server-only; neither PR CI nor browser receives service keys. Plan rotation/audit and encryption/private object configuration.

## B. Source/technical gates (all required)
- [x] Baseline source test gate: `main` `84c9b87`, [GitHub Actions #39805920327](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39805920327) completed 4/4. Recheck **new** SHA/CI after L/M/N/O integrate.
- [ ] Review all ten chronological `supabase/migrations/**` SQL scripts against hosted migration history; first three originally reported applied, **seven later scripts reported unapplied**. Verify this with read-only hosted evidence rather than assuming. Back up DEV DB/storage configuration; log migration fingerprints, ordered plan, expected locks/downtime, transaction behavior and roll-forward recovery. Negative tenant-RLS/storage and no privilege escalation checks must pass on a disposable fresh + upgraded DB and after authorized DEV application.
- [ ] Confirm durable transactional outbox, queue schema, claim attempt/lease fencing, poison processing, timer indexing, idempotency and replay behavior; 20m host / 25m lease / 780s FFmpeg subprocess configuration remains consistent. Establish runtime crash/saturation alarm thresholds.
- [ ] Audit complete FFmpeg and ffprobe build provenance, corresponding binary and codecs/font/music/stock licenses, notices and commercial terms; provide actual Linux x86_64 Flex-compatible executable hash and repeatable packaging.
- [ ] Benchmark real target-size **1080x1920 30-second** media on an approved representative resource profile: cold start, CPU, max RSS, ephemeral scratch, temp cleanup, worker wall clock, p95, output size, codec compatibility and estimated per-job cost; stay within quotas/timeouts and adjust only with new design review.
- [ ] Confirm independent user-rights checks/attribution and publishing compliance; declarations alone do not establish third-party commercial licenses.
- [ ] Review L/M/N/O PRs and required four CI jobs after **each** integration merge. Separate non-deploy source checks from runtime proof.

## C. Explicit independent authorizations

| Gate | Exact operation, scope and change window | Owner decision/date | Evidence/rollback |
| --- | --- | --- | --- |
| **1 — Hosted Supabase DEV migration** | Capture exact target ref, SHA, read-only history/diff, backup; enumerate ordered SQL commands and stopping points | **PENDING — not authorized** | Restore strategy, verification queries, rollback owner |
| **2 — Azure DEV provision + deploy** | List Bicep parameters, isolated Central India RG, approved resource delta/what-if, Functions/queues/Storage/app settings and GitHub workflow invocation | **PENDING — not authorized** | Cost cap, alerts, rollback to previous package, resource deletion |
| **3 — Hosted DEV E2E smoke** | List approved tenant test identities, isolated cleanup/tagging, JWT/tenant-denial/media rights checks, upload/generation/save/render/signed download, queue poison/replay and short-lived token expiry; log scrub | **PENDING — not authorized** | Test-data cleanup, evidence location, incident/stop owner |

A **separate explicit user go/no-go for EACH gate** must be recorded in this document before anyone runs the corresponding hosted command/workflow. Source-only branches, offline CI, GitHub OIDC authentication and this checklist grant no approval.

## D. Deployment acceptance after future approvals (none performed yet)
- [ ] Confirm application endpoints and timer/queue/poison functions index; test valid and revoked tenants, cross-shop RLS, JWT expiry, signed URL TTL and private-object access denial.
- [ ] Verify licensed/authorized media ingestion, deterministic seven-day planning, remote draft save, bounded 30-second MP4, secure signed download and idempotent crash/replay; record failures and real cost.
- [ ] Confirm monitoring/alerts, deployment audit, migration IDs, version SHA and rollback instructions.
- [ ] Record explicit DEV sign-off before broader release. Part 2 publishing, Part 3 Wan, PROD billing and any production migration remain out of scope.

## Change record
- 2026-10-22 — Coordinator 3 created approval template from merged I/J/K plus green main baseline. **No approvals granted and no hosted changes executed.**
