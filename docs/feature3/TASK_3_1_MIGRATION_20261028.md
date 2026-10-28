# Task 3.1 — Feature #3 safe migration chronology (2026-10-28)

Source migration previously named `20261026173000_feature3_model_catalog_drafts.sql`
was pending in DEV even though the later `20261026194000_feature2_ai_cost_ledger`
had already been applied. Existing migration preflight requires live history to
match the exact ordered repository prefix, so deployment was correctly blocked.

- Replace that *unapplied* source file with `20261028092346_feature3_model_catalog_drafts.sql`, keeping the same RLS, validated CAS design-save RPC and tenant/model foreign keys.
- Remove deprecated `auth.role()` check from the security-definer save RPC, keeping `auth.uid()`, active OWNER/EDITOR role and subscription locks mandatory.
- Adjust strict `dev-db-preflight` expected order and negative test.
- Do **not** overwrite/rewrite any already-applied Feature2 migration or bypass hosted migration-history checks.
- Hosted DEV application remains separate from source PR CI: verify exact live 22-version prefix; use only approved additive DDL and verify new tables/RLS/RPC, foreign/VIEWER denial and no public writes. Do not recreate test users/borrow inactive Feature2 shop.
- Source state is NOT proof of DEV deployment. No GPU/PROD/WineShopPOS.

Next workstreams: Task 3.2 signed merchant private upload; Task 3.3 model registration/review; Task 3.4 metered GPU attempt/outbox.

## 2026-10-28 Actual DEV application
- Authenticated current RetailGrowthAI DEV project: 22 exact ordered prior versions through 20261026194000, with Feature3 tables absent before apply.
- Applied reviewed Feature3 model catalog + CAS designs SQL through Supabase migration API. Its assigned **hosted version is 20261028092346**, name `feature3_model_catalog_drafts`; this follow-on source PR synchronizes the source filename and strict history preflight.
- Verified actual DEV: both `feature3_models` and `feature3_poster_designs` exist; both RLS enabled; `authenticated` SELECT-only on models, no direct catalog/design INSERT; only authenticated design RPC EXECUTE, anon denied. No tenant media/model records inserted or privileges bypassed.
- Still pending signed-in real owner/VIEWER/foreign API use, which is distinct from static SQL privilege checks. Feature3 feature flag remains OFF, no GPU/PROD/WineShopPOS. Independent CI must verify source reconciliation.
