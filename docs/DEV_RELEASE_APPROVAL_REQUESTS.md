# RetailGrowthAI — Four independent DEV approval requests (2026-10-22)

**Overall status: NOT APPROVED.** This repository record and linked GitHub issues are requests for **future separate decisions** only. They do not authorize hosted actions. The four gates are intentionally independently approvable. Record separate owner, exact source SHA, date, target, budget, rollback and explicit go/no-go in the corresponding issue before acting. Never modify WineShopPOS or PROD.

## Request A — frontend-only Azure Static Web Apps public demo — [GitHub issue #51](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/51)
**Decision: PENDING. Priority: FIRST.**

**Exact proposed scope:** after R `feat/p1-frontend-static-preview` is reviewed, merged, and its exact main commit passes four CI jobs, create or configure **one** dedicated RetailGrowthAI **DEV** Azure Static Web App solely to serve existing static React/Vite demonstration in **mock mode**, then deploy and check an **actual** HTTPS URL.

Required controls:
- `app_location: frontend`, `output_location: dist`, production Vite build and SPA `navigationFallback.rewrite=/index.html`; verify direct navigation/refresh on `/`, `/campaigns`, `/account`.
- Confirm exact DEV Azure subscription/resource group/name/region/hosting plan, quota, cost ceiling, cleanup and protected workflow/environment permissions **before approval**. Never assume a free plan or a predictable hostname.
- Do **not** set production Azure Functions URLs, service-role keys, hosted Supabase migrations, backend queue triggers, model inference, custom domains or new database as part of this approval.
- Make the mock/demo nature obvious; URLs are unknown until the approved deployment and real HTTPS verification.
- Rollback: redeploy the reviewed last-good static commit/artifact or remove only the new isolated DEV site following the approved procedure.
- **Owner decision:** PENDING — no SWA create/deploy granted.

## Request B — hosted Supabase RetailGrowthAI DEV migrations — [GitHub issue #52](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/52)
**Decision: PENDING. Independent of A.** Verify release-time migration history read-only for **project `jeearzffnjbvghwjjjrf` (Tokyo)**, then back up and validate restore, approve seven exact pending ordered SQL files and an operator/window; apply only after separate explicit approval and check RLS, Storage, revocation, claim fences, outbox, poison and rollback guards. Reference `supabase/DEV_RELEASE_READINESS.md` and P source PR. No production or WineShopPOS.

## Request C — Azure DEV Functions/Queues/FFmpeg backend provisioning/deployment — [GitHub issue #53](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/53)
**Decision: PENDING. Independent of A and B; operationally dependent on approved schema.** Before action, verify scoped DEV Central India IAM/read-only, resource tags, deployment what-if, cost ceilings/alerts, secure app settings, queue/poison/timer indexing, verified licensed static FFmpeg, 20-minute host/25-minute DB lease/780-second subprocess caps, and recoverable ZIP/infra rollback. Reference Q PR and `infra/azure/RELEASE_READINESS.md`. No subscription-wide roles or WineShopPOS.

## Request D — genuine hosted RetailGrowthAI DEV E2E tests — [GitHub issue #54](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/54)
**Decision: PENDING. Independent of A/B/C and only technically possible after corresponding approved hosted services exist.** Scope tenant-specific DEV-only user credentials and test shops, licensed real test photo upload, seven-day plan, draft save, 30-second video/private signed MP4, JWT expiry, tenant denial, replay/poison fault injection, bounded paid execution, log masking, approved cleanup/retention. Run O's manual harness **only** after separate explicit owner authorization, with no PR secrets. Refer to `tests/e2e/HOSTED_DEV_RUNBOOK.md`.

## Evidence / decision ledger

| Gate | Owner decision | Latest source and 4/4 main CI | Hosted change | Actual verification |
| --- | --- | --- | --- | --- |
| A SWA frontend-only | **PENDING** | R #59 merged db8aeee6; main #39834922909 4/4 | **NONE** | No live URL |
| B Supabase DEV SQL | **PENDING** | P #56 merged a393787b; main #39834506027 4/4 | **NONE** | Read-only history to be refreshed |
| C Azure backend | **PENDING** | Q #57 merged 28cd7a6c; main #39835674846 attempt 2 4/4 | **NONE** | Read-only OIDC authentication only |
| D Hosted E2E | **PENDING** | Offline O harness merged; main #39835674846 attempt 2 4/4 | **NONE** | Mock-only validation |

**Approval language:** A future user message should explicitly identify *which one* of A/B/C/D, exact reviewed site/project/RG, cost cap and rollout scope. Approval for A never includes B/C/D. Do not interpret “prepare,” “PR merged,” “OIDC works,” or “show preview” as a hosted-change authorization.


## 2026-10-22 — verified source handoff (LATEST)
- All P/Q/R PRs and coordinator workflow are merged: P #56 / a393787b, R #59 / db8aeee6, Q #57 / 28cd7a6c. Latest main #39835674846 attempt 2 passed all four offline CI jobs. The first attempt only failed due to ghcr.io disposable database image rate limiting. R mock static website is prepared, but no live Azure Static Web App has been created and no HTTPS demo URL was verified.
- GitHub issues #51, #52, #53 and #54 remain **OPEN/PENDING** for separate go/no-go decisions. Gate A is first; source integration, issue creation and this document are NOT permission to deploy any website, migrate SQL, provision Functions or execute hosted E2E.

## 2026-10-22 — Owner umbrella go-ahead captured; all four execution checks remain BLOCKED
- User stated “lets do all i have approved all now” for A/B/C/D. This is an explicit instruction to pursue all stages, superseding old messages indicating no user consent. **No actual hosted operations are claimed as approved-to-execute unconditionally**, because each existing DEV release checklist still requires exact target/rollback/budget/secret proof that has not been established.
- **A**: mock SPA source CI green; no current Azure static site, verified resource, protected deployment token or public HTTPS URL. **B**: verified `jeearzffnjbvghwjjjrf` has 3 applied / 7 pending migrations, all public tables RLS on, no actual user/tenant/media data; backup/restore proof missing and generic connector cannot specify canonical version IDs. **C**: Azure subscription/RG IAM, cost budget, licensed FFmpeg binaries and B completion pending. **D**: deployed services/test identities/licensed media and cleanup prerequisites pending. Recorded per-issue comments at [#51](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/51), [#52](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/52), [#53](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/53), [#54](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/54).
