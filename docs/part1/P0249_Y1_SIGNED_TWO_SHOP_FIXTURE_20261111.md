# Issue #249 — signed two-shop original read-only GET fixture (source-only)

The existing isolated Y1 Python Linux Consumption host has verified two indexed GET routes and protected **12/12** missing-Bearer handler-denial responses, but original-auth positive membership and RLS have **not** been verified with live signed DEV users. Existing [PR #931](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/931) separately owns the after-idle **read-only hosted** canary. This task must not duplicate its Azure workflow.

## What the new local original-source test actually does

`tests/infra/test_p0249_y1_signed_two_shop_transport.py` generates a temporary in-memory 2048-bit RSA test signing key, signs two synthetic `authenticated` project-scoped access tokens, and invokes the **actual** Y1 shadow `handle_campaign_get`, **unmodified original** `SupabaseJWTVerifier`, `HTTPAPI`, and `TenantStore`. Only the external JWKS lookup and Supabase PostgREST HTTP transport are replaced with local, assertion-heavy fixture adapters; no tokens/keys are stored in the Git repository, no host setting is changed and no DB is contacted.

Controls: two authorized identities can fetch only their own synthetic shop campaign; foreign campaign data is hidden even if a malicious/stale PostgREST response returns a row; current membership revocation denies the next GET; invalid signature/issuer/audience/role/expiry/sub are denied before DB; disabled Y1 feature flag does not load JWT/store modules; malformed campaign IDs return sanitized responses; only GET and JWT-scoped `apikey` headers are used. Existing Y1 health/negative-auth hosted evidence remains separate.

## Gates not yet passed

A successful CI test is **not** a live Supabase JWKS request, real signed test account, RLS-backed PostgREST response, server-side appsetting deployment, or production API migration. Do **not** copy privileged Supabase service keys or enroll a real retailer account. Next stage: review/enable only the isolated DEV Y1 shadow with public project URL/publishable key, then run two safe nonprivileged DEV signed test identities and explicit positive + denial cross-shop checks, while preserving original Flex, no queue/timer triggers, no frontend cutover, no model/GPU/PROD/WineShopPOS.
