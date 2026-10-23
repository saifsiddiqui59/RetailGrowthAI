# RetailGrowthAI email and onboarding approval (source preparation)

## What is live right now

- Supabase Auth email signup currently **auto-confirms**: the checked DEV owner account has \`email_confirmed_at\` set on creation and **no \`confirmation_sent_at\`**. No verification message was requested; merely adding an Auth email or a private root grant does not send an email.
- Existing signup currently creates an Auth user, **not** a separate platform approval request.
- The new source migration \`20261023210000_p1_onboarding_approval.sql\` adds a secure queue and root review RPCs. It is NOT applied merely by merging the PR. Its DB shop-creation gate is OFF by default for compatibility; enable only after UI and negative-security tests.
- The email design template is prepared here, not installed as a live Supabase Auth email template, and no outbound request to any SMTP provider is implemented.

## Wire email before using it

Supabase announced on **2026-06-03** that NEW free-tier projects cannot customize Auth templates while using its default email provider. To send branded login/confirmation/reset/invite emails, configure **RetailGrowthAI-owned** SMTP (not WineShopPOS Gmail credentials) in Supabase Dashboard → Authentication → SMTP. Verify sender/domain and DKIM/SPF; then configure Authentication → Email Templates → **Confirm signup** using \`confirmation.html\`. Set Auth → Sign In / Providers → Email → **Confirm email** on, and set URL Configuration Site URL to the actual RetailGrowthAI DEV website, with approved redirect URLs. Test with a controlled test mailbox and avoid logging tokens/links. These are hosted changes that require separate verification.

The approval queue is **not** an email itself. New accounts appear in the provider's in-app Platform Control queue. Sending separate "new account request" admin emails and "approved/rejected" customer emails requires a server-side SMTP worker/Send Email Hook with retries, suppression, idempotency and audit; never call a mail provider directly from the browser, never embed secrets in \`VITE_*\` settings.

## Rollout checklist

1. Review and test additive SQL, unit/browser tests and four CI jobs in PR; merge with four clean main jobs.
2. Apply new SQL once to dedicated RetailGrowthAI DEV, ensuring migration history matches.
3. Deploy UI to the **existing** DEV Static Web App.
4. Verify root-only pending account listing and approve/reject actions; non-root denied.
5. With a controlled test signup, confirm pending request appears. Only after this, switch \`retail_private.onboarding_gate.enforce_approval\` to \`true\` via trusted DB operator and retest: new signup cannot create a shop until approved; when approved it can create a shop and receive the existing 7-day trial. If gate is still OFF, UI must not describe approval as a blocker.
6. Configure SMTP/verification emails separately and test delivery with a controlled mailbox; avoid claims of emails being sent until confirmed.

Do not modify WineShopPOS, use its old SMTP app password, or grant root to any signup automatically.
