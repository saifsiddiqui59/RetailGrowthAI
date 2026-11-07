# RetailGrowthAI — DEV test logins & Playwright safe protocol

## Current account verification and limitations

Existing RetailGrowthAI Supabase project is `jeearzffnjbvghwjjjrf`. A **pre-existing** owner-provided approval email was confirmed present by a read-only auth-users query; no password was verified, changed or stored here. **Two new login accounts have not been created.** The connected Supabase management connector does not expose Auth Admin `createUser`, and direct SQL insertion into `auth.users` is unsafe and unsupported. Do not claim the new logins exist or that signed UI testing passed.

The planned nonprivileged DEV accounts are:
- `rgai-owner-test@retailgrowth.test` — a **test-only** identity, role not granted by Auth creation
- `rgai-editor-test@retailgrowth.test` — a separate **test-only** identity, role not granted by Auth creation

Use only the documented Auth Admin API (trusted server context), never raw `auth.users` SQL. The DEV-only script `scripts/dev/provision_test_users.py` is **dry-run by default**, hardcodes the DEV project ID and refuses PROD, needs an operator-held service-role key and **distinct 16+ character** passwords via secrets, and will never overwrite an existing account or log passwords.

## Operator provisioning (on a trusted DEV machine; NOT in GitHub Actions)

```bash
export SUPABASE_PROJECT_REF="jeearzffnjbvghwjjjrf"
export SUPABASE_URL="https://jeearzffnjbvghwjjjrf.supabase.co"
python scripts/dev/provision_test_users.py
# Review plan first. Then, through private local secret injection:
# SUPABASE_SERVICE_ROLE_KEY, RGAI_TEST_OWNER_PASSWORD, RGAI_TEST_EDITOR_PASSWORD
export RGAI_DEV_TEST_USERS_APPLY="YES"
python scripts/dev/provision_test_users.py --apply
```

Keep local credential files out of Git, CI artifacts, screenshots, PR comments and chat. Do not insert these test users into real shop memberships or grant OWNER/EDITOR by `user_metadata`; use existing approved, signed JWT/RLS onboarding and verify a real two-tenant isolation test separately. These `.test` addresses do not receive email, so do not use email verification or password-recovery delivery as a pass criterion. The Auth Admin script marks them confirmed for DEV regression sign-in only.

## Playwright guidance

- Use Playwright Chromium **only when UI/login checks are needed**; existing mocked E2E is valuable but NOT a real hosted signed login. For hosted login, use a separate browser context for each DEV synthetic test account, with credentials passed via local environment variables (`RGAI_TEST_OWNER_EMAIL`, `RGAI_TEST_OWNER_PASSWORD`, `RGAI_TEST_EDITOR_EMAIL`, `RGAI_TEST_EDITOR_PASSWORD`).
- Do not print or screenshot passwords, tokens, private URLs, cookies, headers or customer media; scrub artifacts and request logs.
- Approval identity is an **existing owner-controlled account**, not a test user. Only the real account owner may authorize approvals; no automatic owner-admin/content/payment approval, consent, JWT forgery or gate bypass. Never store the supplied approval password in the repository or Playwright tests.
- Test real sign-in, sign-out, unauthorized VIEWER paths, foreign tenant isolation and expired/revoked session handling with nonprivileged accounts. Follow existing signed tenant and rights checks. A failing login is FAILED or BLOCKED with a real error, not a mock PASS.
- No user-visible demo Reel, video, generated poster, or sample screenshots during the owner's 10-hour absence; do not generate such samples later without an explicit request. Automated fixture-only test screenshots are ephemeral and should not be shared.

## Budget protection

Use **zero paid AI/GPU calls by default**. No Wan, FLUX, A100, cloud model downloads, paid image/video model inference, provisioned compute, PROD or changes to WineShopPOS. GPT-4.1 Mini is the only allowable optional model for a narrowly scoped DEV test if **existing deployment + explicit metered budget guard** are verified; otherwise BLOCKED. Prefer ordinary Playwright, Python, CPU/FFmpeg and contract tests.
