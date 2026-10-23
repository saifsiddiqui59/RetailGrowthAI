# RetailGrowthAI — Final Part 2 / Part 3 Integration Gate

Status: COORDINATOR CONTRACT / SOURCE PREPARATION ONLY. Not a merged Part 2 or Part 3 release. Updated 2026-10-23.

## Verified baseline and branch custody

- Latest verified review baseline: `main` `7dc79700aba58608a34d3360b94658a6e5cbca38` (documentation closeout following Part 1 gateway source PR #107). PR #107's post-merge Actions run #39972501578 is 4/4 successful on `154d82169a559adffdf4bad0e9e7cb8e221bfeef`; CI for later documentation commit must be checked separately.
- Hosted RetailGrowthAI DEV Part 1 genuinely passed signed-in two-tenant 7-day Foundry generation, approved draft edits, FFmpeg 30s H.264 1080x1920 private signed MP4 delivery, quota reservation and complete synthetic cleanup in owner-approved canary #39958569041 attempt 2. Owner-only subscription status is live in existing DEV SWA. This is **not** PROD or paid-plan authorization.
- At this checkpoint `feat/part2-integration` and `feat/part3-integration` both point to `1ef7271004666c13a13cf627ed47460397799edc`, are behind `main`, and have no Part 2/3 integration changes ahead of `main`. Zero open PRs; no final integration PR received.
- Part 2 lead autonomously owns its tasks/internal PRs/CI/merges into `feat/part2-integration`; Part 3 lead does the same into `feat/part3-integration`. Coordinator must **not** merge, supervise or block their internal PRs. Part 1 DEV Deployment Operator 2 owns its independent operational changes.

## Unshared system ownership — no replacements or duplicates

| Boundary | Existing Part 1 authority | Part 2 obligation | Part 3 obligation |
| --- | --- | --- | --- |
| Identity & tenants | Supabase Auth JWT, `shops`, `shop_memberships`, RLS and OWNER/EDITOR/VIEWER | Reuse membership; server-side provider grants scoped to shop + actor, securely store revocable OAuth tokens | Reuse membership; never create separate auth/tenant/identity/keys |
| Campaign source | `campaigns`, `campaign_days` and reviewed remote PATCH | Reference authorized canonical day/version and explicit reviewed publish approvals | Reference canonical day/media IDs; premium job must not mutate drafts as implicit approval |
| Media | Existing private Supabase `retailgrowth-media` bucket and `media_assets` provenance/tenant rights; FFmpeg pipeline | Publish only signed/authorized private media references, no independent public media store | Register verified premium output with same tenant media record/storage rights; keep FFmpeg as default/fallback |
| Queue & retries | Azure Storage queues `retail-campaign-planning`, `retail-reel-render`; transactional `job_outbox`; claim token/lease/outbox/poison reconciliation | Own separately named publishing work/dispatch and provider-specific idempotent reconciliation; do not reuse planning/render queue or expand outbox enum without additive migration | Own separately named premium generation work; do not overwrite `render_jobs` worker or outbox semantics |
| Trial / billing | `shop_subscriptions`, `shop_usage_reservations`; server-enforced 7-day trial, 2 campaign / 2 FFmpeg render reservations | No separate subscription or charge; platform operations gated by existing entitlement and explicit authorization | Distinct server-authoritative premium cost reservation/ceiling and provider-specific usage; do not debit `render_jobs` twice for one logical request; paid providers OFF until separately approved |
| Backend / UI | One Azure Functions DEV app, signed JWT + RLS; one React/Vite app / Account / Campaigns routes | Add provider-specific routes and UI without replacing Part 1 paths | Add optional premium UI/API without replacing existing render preview/download |

## Contract compatibility / schema guard

1. `docs/INTERFACES_V1.md` remains the authoritative backward-compatible v1 campaign/day/render interface. Existing `POST /api/campaigns`, `GET /api/campaigns/{id}`, `PATCH /api/campaigns/{id}/days/{day_id}`, render and signed-download API response shapes must survive unchanged.
2. New Part 2 / 3 endpoints must use authenticated user JWT, resolve shop membership at every mutable action, check source rights, and avoid service-role/browser secret exposure. Both interfaces must fail closed on revoked membership, expired approval and tenant-ID mismatch.
3. Database changes must be **additive, unique versioned migration files** after the existing 11 migrations, including `20261023134701_p1_subscription_quota.sql`. Never modify applied files, reapply migrations, collide timestamps or drop Part 1 policies/triggers. If both parts need the same table/outbox enum, coordinator reconciles the final migration *after* each lead submits a final PR. Document migration order, downgrade/rollback and DEV-only application approval separately.
4. `job_outbox.kind` currently accepts only `planning|render`; `shop_usage_reservations.operation` accepts `campaign|render`; `render_jobs` INSERT triggers reserve a render unit. Publishing or Wan may **not** silently insert their values into these existing check constraints/objects; propose additive, isolated extension with security and concurrency tests. Premium→FFmpeg fallback must have one explicit, testable charge/quota outcome and no double billing.
5. Approval is per reviewed content version + target channel/account + scheduled time; a draft or rendering success does not imply posting permission. Store UTC scheduled instant with original IANA timezone and verify DST; no unapproved publish on queue replay. For provider uncertain responses, reconcile provider IDs/state before retrying. OAuth token revocation/disconnection disables future jobs.
6. Wan must be opt-in and provider-disabled by default. Confirm official provider terms, commercial rights, available model capabilities and current pricing before provider activation; server-enforce per-shop budget cap, maximum output duration/resolution, concurrency, retry ceiling and a no-charge FFmpeg fallback policy where appropriate. Never infer a live usable provider from mocks/fixtures.
7. Do not touch WineShopPOS or GenAI Galaxy. No Postiz, Razorpay, extra auth, unapproved billing provider, second media bucket, second frontend, parallel subscription ledger or paid provider credential in ordinary GitHub Actions.

## Final PR acceptance (coordinator only)

- **Eligibility:** lead confirms internal tasks/PRs merged to its part integration branch, posts final PR targeting latest `main`, and supplies source/test/handoff evidence. No speculative integration of scaffolding branches.
- **Review:** compare head to latest `main` and the other completed part, verify RLS and adverse tests (cross tenant, viewer/revocation, idempotency, token expiry, approvals, queue retries, budget exceed, provider timeout, media rights, no duplicate charge). Scan secrets, migrations, release workflows, runtime cost and backward-compatible API behavior. No weakening/disabling an existing test.
- **Part order:** normally Part 2 first (OAuth/social scheduling only) then reconcile/rebase Part 3 atop fresh `main` (optional premium media). Reverse only when demonstrated dependency requires it; retest both parts after integration. Do not rewrite either lead's owned work without explicit reconciliation.
- **CI:** before *each* merge require the four existing GitHub Actions jobs green on the exact final PR head: frontend/browser, Python/API/infra, FFmpeg/media, isolated Supabase migration/RLS. After *each* merge inspect a new complete four-job `main` run on the exact merged SHA. Green Part 1 CI alone is insufficient to prove new social/Wan behavior; add relevant Part 2/3 tests to existing jobs.
- **Hosted gates:** source merge ≠ hosted deployment. Reuse currently proven DEV resources only with separate owner permission for each new hosted migration, platform OAuth credentials, outbound publishing, Wan paid API, premium spend authorization or customer payment. Mark offline/mock and actual hosted outcomes separately. Production remains unapproved.
- **Evidence:** after each actual merge update `PROJECT_STATE`, `NEXT_TASK`, `DECISIONS`, `WORK_LOG`, `PARALLEL_WORK`, `ARCHITECTURE`, `INTERFACES_V1` with exact PR #, full head/merge SHA, CI job/run URLs, tested vs untested host capabilities, migrations/rollback and next work. Do not write imagined merges.

## Current outcome

Contract gate recorded; neither final Part 2 nor Part 3 PR exists or is merged as of this checkpoint. No hosted or paid execution performed by the coordinator. The two leads may continue autonomously in parallel.
