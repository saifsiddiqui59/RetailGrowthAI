# RetailGrowthAI — Tasks 1, 2 and 5: poster DEV release gate (2026-10-24)

**Status:** Part 1 source is on `main` (#215) and frontend deployed to the existing Free SWA (#216). **Cloud poster saving/rendering/download is not yet live.** This runbook is scoped to RetailGrowthAI DEV; it does not authorize PROD/WineShopPOS changes.

## Verified baseline

- Supabase project: `jeearzffnjbvghwjjjrf` (RetailGrowthAI only). Migration history contains **13** canonical baseline versions through `20261023191246`. Read-only remote inspection on 2026-10-24 found **no** poster tables, poster RPCs or new migration versions.
- Existing Azure DEV resource group: `rg-retailgrowth-dev` (Central India); existing Function App: `rgai-dev-functions-d4e5ddbd`; existing Storage account: `rgaid4e5ddbdf0d21d96`; existing Free SWA: `retailgrowthai-dev-preview` / `https://purple-dune-06b5da200.2.azurestaticapps.net/`.
- The newly merged `function_app.py` includes poster draft/list/renders/download/select routes, a 2-minute outbox dispatcher and dedicated `retail-poster-render` queue trigger. Flags `RETAIL_ENABLE_POSTER_DRAFTS` and `RETAIL_ENABLE_POSTER_RENDERING` are **default OFF**.
- Important pre-release correction: packaging previously omitted `poster-engine/render.py`, which `poster_worker.py` imports at Function indexing. Fix PR #219 requires the actual module in the Functions ZIP and tests reject archives without it.

## Mandatory order, with independent operator gates

1. **Review PR #219; four green CI jobs; coordinator merges it into `main`.** Validate `python3 scripts/deploy/package.py --check`, `python3 -m unittest scripts/deploy/test_package.py` and the full ZIP `--verify-zip` against the exact `main` source. Do not redeploy the broken pre-#219 ZIP.
2. **DEV-only migration approval and recovery evidence** before any remote DDL: confirm a securely held *tested* backup/restore plan, no parallel schema operator active, 13-version baseline intact, expected RLS grants, explicit approved rollout window. Never copy production secrets or export tenant data to a public artifact.
3. Use the official Supabase CLI migration workflow with **exact tracked file versions** and one migration operator: `20261024113000_p1_poster_drafts.sql`, `20261024150000_p1_poster_jobs.sql`, `20261024160000_p1_notification_outbox.sql`, `20261024170000_p1_poster_banner_selection.sql`. The notification migration is additive but **SMTP stays OFF**; preserving canonical ordering avoids orphaned migration-history timestamps. Confirm local disposable Supabase security CI passes and remote preflight confirms exactly these four outstanding files. Avoid arbitrary MCP-generated timestamp migrations and do not run untracked remote SQL.
4. Re-read `supabase_migrations.schema_migrations`, RLS policies, RPC role grants and [security advisors](https://supabase.com/docs/guides/database/database-linter). Never enable a worker on an unverified schema; never expose service-role credentials in browser code.
5. **Existing Azure DEV only:** verify exact tagged resource group, Function App and Storage account with Azure OIDC. Create only the isolated `retail-poster-render` queue in that existing Storage account, with cost/poison count monitoring. No second Function App or Storage account. Keep `RETAIL_NOTIFICATIONS_ENABLED=false`.
6. Package with the fixed `scripts/deploy/package.py`, pinned FFmpeg runtime and Pillow requirements, and deploy to the **existing** Flex Function App. Confirm indexed routes/triggers including `create_poster_draft`, `list_saved_posters`, `render_campaign_poster`, `dispatch_pending_posters`, plus all original campaign/reel jobs; unauthorized POST still returns 401. Enable both poster flags only after steps 1–6 pass and queue/worker storage connectivity is verified; never enable the poster flag without queue readiness.
7. Live authenticated shop E2E: upload an owned/licensed retailer source photo (with rights evidence), create campaign, cloud-save poster, request queue render, poll for completed PNG, refresh/reopen from history, mint private short-lived download, explicitly select banner into DRAFT campaign day. Test 403/404 cross-shop, revoked membership, VIEWER write denial, expired trial, stale worker lease, poison queue, retry and iOS/Android usability. **A public SPA 200 and mocked CI are not substitutes.**
8. **Rollback/stop:** set `RETAIL_ENABLE_POSTER_RENDERING=false` and `RETAIL_ENABLE_POSTER_DRAFTS=false`, disable the dedicated poster queue trigger to prevent dequeue churn, inspect the outbox, restore the earlier Functions ZIP only if imports/indexing fail. Preserve DB rows and migrations; never blindly DROP migrated user data.

## Evidence retained

- Source integration: PR #215; frontend DEV deploy: #216 / Actions #40074804323 (success).
- Packaging repair proposal: PR #219. Do not call it a hosted deployment.
- Current hosted DB verification: 2026-10-24 read-only Supabase project/migration listing and poster object existence query (no poster objects).
- **Outstanding:** operator backup/restore attestation, tracked migrations, queue creation, backend deploy, feature-flag activation, signed-in acceptance evidence. This document does not itself perform those writes.


## 2026-10-24 — Poster schema access correction actually applied
- Owner approved DEV DB correction. Live post-#235, the optional canonical poster outbox privilege migration `20261024180000` was applied directly as an atomic guarded, source-backed SQL + migration history record, not by the failed #236 release workflow. Supabase remote history now contains **18** versions and browser private access remains revoked.
- Supabase edge evidence: `claim_poster_outbox` HTTP **403** at 11:00 UTC, then HTTP **200** at 11:02 UTC after the grant. Direct `SET LOCAL ROLE service_role` RPC returned empty JSON array (no pending poster jobs). Azure worker can now claim outbox jobs; actual image-generation outcome not proven.
- Owner sign-in and ROOT approval still required for protected manual-only canary; tests can only claim full E2E success when an approved live poster completes, the private signed PNG verifies and an edited campaign day references its banner asset. Do not auto-trigger the account-creation canary from a doc/code push.
