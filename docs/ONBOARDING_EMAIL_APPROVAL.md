# RetailGrowthAI email and onboarding approval

## Current LIVE DEV release status — 2026-10-23
- **LIVE**: The protected Platform Control approval queue UI is now deployed at the existing single-login https://purple-dune-06b5da200.2.azurestaticapps.net/ (merge #160, Azure release [#40010214349](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40010214349) SUCCESS). Independent post-main CI [#40010214381](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40010214381) **4/4**.
- **LIVE**: Supabase migration `p1_onboarding_approval` applied exactly once in project `jeearzffnjbvghwjjjrf` at Supabase-assigned version **20261023191246**; local SQL filename updated to `20261023191246_p1_onboarding_approval.sql`. Auth insert trigger now queues future new user registrations. Existing owner retained APPROVED state. `retail_private.onboarding_gate.enforce_approval` is **true**; pending users cannot create shops. Root RPC access/nonroot denial/rolled-back gate restriction was checked in hosted DEV; disposable CI covers eventual approval→trial. At verification 0 pending approvals and 0 retailer shops. A real new-user hosted onboarding interaction is still unverified.
- **NOT LIVE**: Supabase Auth branded confirmation emails, approval notification emails and customer decision emails. Existing Auth signup auto-confirmed owner without sending any confirmation message. No RetailGrowthAI-owned external SMTP/verified sender domain configuration or mail-delivery proof is available through current connected tools. Never tell the owner an email was sent or manually flip Confirm Email until SMTP provider, sender/domain, site/redirect URLs and controlled inbox delivery are ready. The HTML template exists only in source.
- **Operational flow:** Customer uses same login → signup trigger creates PENDING record → user can sign in but cannot create a business → owner opens Platform Control → Retailer signup approvals → Review requests → approves/rejects with reason → approved user can create business and receive existing seven-day trial. Approval requests reach the in-app queue, **not automatically the SaaS owner's mailbox**. Once an email sender is connected, add a server-side outbox and notifications with retry/audit and approval-state idempotency.


---



## Historical preparation (before 2026-10-23 activation)

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


## 2026-10-23 — Confirmation email redirects to localhost: checked and addressed in source
- Owner deleted their earlier Auth account and registered again with the same confirmed mailbox. New `auth.users.id` was generated, and the old platform-root/onboarding grant disappeared through user deletion; the new verified replacement UUID was restored as the single active root through a guard-checked trusted DEV transaction, retaining approval enforcement for ordinary retailers.
- Confirmation email delivery WAS observed for that owner: `confirmation_sent_at` before `email_confirmed_at`, plus Auth sign-in timestamp. This does **not** establish working branded SMTP for arbitrary retail customer inboxes or a valid deployed redirect. The email link returned to localhost because signup did not pass a `redirect_to` and Supabase defaulted to its stale Auth Site URL.
- Frontend source now explicitly requests `redirect_to = window.location.origin + '/account'` for signup. **Operator must still set hosted Auth URL Configuration**: Site URL `https://purple-dune-06b5da200.2.azurestaticapps.net/`, Redirect URLs include `https://purple-dune-06b5da200.2.azurestaticapps.net/account` or the same-origin path wildcard. Provider configuration cannot be changed by the current connected tool. Previously delivered links cannot be changed in place; verify a NEW signup email without sharing its URL/tokens.
- WineShopPOS's Gmail SMTP account powers invoice receipt/oversize messages from its Azure worker, not general authentication. The same sender email address can be used in RetailGrowthAI if it is authorized and set up separately (new app-specific credential and sender display name); do not copy WineShopPOS secret/configuration into RetailGrowthAI. For reliable commercial volumes, configure a dedicated transactional SMTP and authenticated sending domain, and test delivery/bounces. Approval inbox is live in-app; external notifications are not live.

## 2026-10-23 — Recovery implementation boundary
- Source branch `fix/p1-auth-recovery-email` adds Forgot password and Reset password UI with Supabase REST `/recover` and authenticated `/user` password update. Recovery emails must route to existing `/account` and use `supabase/email-templates/recovery.html` (Supabase Dashboard → Authentication → Email Templates → Reset Password). A recovered session is verified server-side, its URL fragment removed, its app privileges not exposed, and it is signed out after changing the password. Do not claim hosted E2E until a real recovery inbox and token flow passes.
- Supabase Dashboard owner must set URL Configuration and a dedicated SMTP provider/sender; this project's connected database tools **cannot** edit Auth Site URL, redirect allowlist, custom SMTP or Auth email templates. Same **authorized sender email address** as WineShopPOS is possible; its production app password must not be reused. Approval notifications remain in-app until secure server-side SMTP outbox/worker exists with delivery retries and idempotency.
