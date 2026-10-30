# Feature3 DEV two-account signed QA gate — read-only check, 2026-10-30

A read-only aggregate query of the documented RetailGrowthAI **DEV** Supabase Auth project confirmed **0 of 1 proposed owner test identities** and **0 of 1 proposed editor test identities** exist in `auth.users`. No account was provisioned, no password or token was read, no shop membership or approval was granted, and no SQL write occurred. Consequently, real two-user/two-tenant signed Playwright and Feature3 hosted rights tests are **NOT VERIFIED**. Existing offline mocks are not evidence of hosted authentication.

**Blocker:** F3-21 / DEV-TEST-ACCOUNTS. **Owner:** DEV Auth Admin operator / coordinator. **Required output:** two distinct, nonprivileged, independently authenticated DEV test identities provisioned via the documented supported Auth Admin API, with isolated authorized shop memberships granted through signed onboarding (not direct auth SQL). **Acceptance:** independent real JWT sign-in, signed role and cross-tenant denial tests, expired/revoked token denial, no leaked credentials or private media. Do not use the existing owner approval account as a substitute or bypass review.

Read-only evidence only. No GPU, paid model, migrations, Azure, PROD or WineShopPOS changes.
