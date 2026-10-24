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


## 2026-10-23 — Auth recovery DEV frontend release: deployed, sender not configured
- Source PRs #169 (signup redirect) and #173 (password recovery, callback sanitization, branded recovery template) are merged. Only the existing Free DEV SWA was updated via scoped release PR #177 and successful GitHub Actions [#40020086287](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40020086287). Six public HTTPS routes responded; **real mailbox link delivery and logged-in recovery have not been verified**.
- A dedicated RetailGrowthAI SMTP identity and Supabase Dashboard changes remain required: Authentication → URL Configuration: Site URL `https://purple-dune-06b5da200.2.azurestaticapps.net/`; Redirect URLs include exact `https://purple-dune-06b5da200.2.azurestaticapps.net/account`. Set dedicated SMTP credentials and sender; paste source-reviewed confirmation/recovery templates in Auth → Email Templates and verify actual delivery with a fresh controlled mailbox and link. Current connected tools cannot update Auth URL Configuration/SMTP/template settings. Do not copy WineShopPOS Gmail production app password.
- Retailer approval in-app queue is still active with gate ON; new-applicant SaaS owner emails and approval/rejection emails are **not implemented or delivered**. Backend outbox+retry+dedup and verified SMTP are a separate pending feature.


## 2026-10-24 — Opt-in notification implementation integrated, LIVE delivery still OFF
- The backend transactional onboarding outbox source [#206](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/206) is merged into Part 1 integration, and branded `RetailGrowthAI` SMTP email body/sender [#212](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/212) is merged. Events: new retailer request → confirmed Platform Admin recipients; APPROVED and REJECTED → retailer. No rejection audit reason, password or token in the customer message.
- **Not live:** new migration `20261024160000_p1_notification_outbox.sql` not applied in Supabase DEV, separate RetailGrowthAI SMTP server not configured, worker opt-in remains disabled, no authentic approval/rejection email has been sent. The same authorized Gmail sender address as WineShopPOS may show a different From display name, with separate RetailGrowthAI credential/configuration and no changes to WineShopPOS.
- New source-only root alerts page `/platform-alerts` #209 and current-page subscription watch #210 help the owner act on verified server signals. These are *not* mailbox/history features and are not yet deployed on the Free DEV SWA. Existing branded Supabase Auth confirmation/reset templates also still require manual provider setup and verified inbox.


## 2026-10-24 — Source released to main, no hosted customer notification delivery
- #215 merged the opt-in private onboarding notification outbox #206 and branded RetailGrowthAI HTML/plain-text SMTP #212 into main; #216 successfully deployed *frontend only* to the existing Free DEV SWA. The owner may now reach the ROOT-protected in-app notifications snapshot route; email confirmations/approvals cannot be assumed sent from a deployed static page.
- **Live email still OFF**: notification outbox migration `20261024160000_p1_notification_outbox.sql` unapplied on DEV as verified with list_migrations, server SMTP not installed/verified, no new Azure Functions backend deployment or worker opt-in, Supabase-hosted confirmation/recovery templates and auth sender URLs still require authenticated Dashboard configuration.
- Next user-controlled action: separately create/authorize RetailGrowthAI SMTP for an existing owned mailbox address (same address as WineShopPOS allowed, separate credential) and set Supabase Dashboard `Authentication → URL Configuration` Site URL + `/account` redirect plus custom SMTP/template settings. Securely configure server-only keys through protected service settings; never paste app passwords into chat, repository, browser Vite env or logs. Test new verification and recovery emails, then tenant-gated retailer approvals and rejections in a controlled inbox.

## 2026-10-24 — CURRENT OWNER DECISION: email FUTURE WORK
- Outbound email is **DEFERRED** until owner explicitly reopens this item: new retailer signup notification, approval/rejection outcome mail, custom SMTP/provider credentials, Supabase-branded hosted verification/recovery templates, and real inbox smoke tests.
- Do **not** reuse, retrieve or reset WineShopPOS SMTP secrets. No Gmail password is needed for current work. Keep `RETAIL_NOTIFICATIONS_ENABLED=false` and do not treat an additive, separately approved poster-release migration as authorization to turn on email dispatch. Keep the notification sender disabled even if canonical schema order results in an inert email outbox table.
- Existing in-app Platform Control → Retailer signup approvals and `/platform-alerts` snapshot notices remain available and are **not** blocked by this decision. Public-facing hosted Auth URL misconfiguration can be fixed in a future independent non-SMTP security task if needed; do not represent emailed verification or recovery as production ready.
- Resume outbound email later only as a separately reviewed, owner-authorized deliverability workstream with project-specific sender configuration, safe migration and controlled inbox checks.
