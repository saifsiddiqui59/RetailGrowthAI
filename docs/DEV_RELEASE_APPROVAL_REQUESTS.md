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
| A SWA frontend-only | **PENDING** | R PR not yet verified | **NONE** | No live URL |
| B Supabase DEV SQL | **PENDING** | P PR not yet verified | **NONE** | Read-only history to be refreshed |
| C Azure backend | **PENDING** | Q PR not yet verified | **NONE** | Read-only OIDC authentication only |
| D Hosted E2E | **PENDING** | Offline harness previously merged as O | **NONE** | Mock-only validation |

**Approval language:** A future user message should explicitly identify *which one* of A/B/C/D, exact reviewed site/project/RG, cost cap and rollout scope. Approval for A never includes B/C/D. Do not interpret “prepare,” “PR merged,” “OIDC works,” or “show preview” as a hosted-change authorization.

## 2026-10-22 — Source-approved vs hosted-unapproved distinction
- P [PR #56](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/56), R [PR #59](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/59) and Q [PR #57](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/57) are merged; coordinator manual frontend-only workflow [#58](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/58) is also merged. Combined main [CI #39835674846 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39835674846) **passed 4/4**. Those are **source code** checks, not live runtime evidence.
- **A #51 PENDING**: approve separately one isolated Azure Static Web App DEV mock website, exact name/region/plan/cost, protected GitHub secret and manual deploy; only after actual HTTPS `/`, `/campaigns`, `/account` checks may a real URL be reported. **No URL exists yet.**
- **B #52 PENDING**: separate hosted RetailGrowthAI DEV Supabase SQL migration authorization for seven ordered versions with backup/restore validation. **C #53 PENDING**: separate Azure DEV Functions/Storage/queue/FFmpeg resource provisioning/deploy with IAM/cost/rollback. **D #54 PENDING**: separate real hosted DEV E2E testing with live test identities, media-rights evidence and cleanup.
- Permission for A never includes B/C/D; none of these grants WineShopPOS or PROD access.
