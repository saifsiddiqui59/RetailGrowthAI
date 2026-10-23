# Part 2 — Next unfinished tasks

1. Verify all four 4/4 GitHub Actions jobs on PR #108/#110/#112/#114 exact heads; self-review and merge passing PRs **only** into `feat/part2-integration`. Verify 4/4 on combined integration head. Fix failures without disabling tests.
2. Rebase or merge current `main` into Part 2 integration after reviewing Part 1 API, migration and frontend changes. No force-push to main.
3. Design backend `/api/social/accounts`, `/api/social/oauth/start`, `/api/social/oauth/callback`, `/api/social/accounts/{id}/disconnect`, `/api/social/jobs`, approval and cancel endpoints. Verify live user+shop actor for EVERY action. OAuth state DB consume must be atomic; callback tokens encrypted before private persistence. Callback CSRF/session and provider account/role checks mandatory.
4. Build worker path: atomic due-claim/lease, server verified approval digest, approved media/rights and metadata, active account/scope, subscription publishing quota, no external side effects on absent entitlement. Queue messages UUID-only; deduplicated private outbound receipts. No blind retry on ambiguous external POST, including YouTube resumable session or Instagram container publication.
5. Implement *approved* platform-specific API transports and upload protocols; no live calls until scopes/app review and explicit owner approval. Meta professional IG, Page scopes/roles, LinkedIn developer program and YouTube consent/audit remain blockers.
6. Add tested post approval/revoke/schedule/unschedule and disconnect flows, approval freshness after draft edits, blackout for regulated/uncleared media, platform-specific FFprobe media checks (not generic 30-second assumption).
7. Add role/tenant/security/expiry/replay negative SQL tests to disposable DB CI, end-to-end mocked browser journey, and cross-platform reconciliation tests. Existing P1 historical SQL preflight must remain unchanged.
8. Determine Part 2 per-plan publish allowances with owner approval; reserve exactly once per logical approved job using authoritative subscription period; do not invent paid plans or reuse P1 campaign/render units.
9. After internal completion and green CI, open one `feat/part2-integration` -> `main` final PR for Coordinator. Do not merge it.

Separate approvals are mandatory before hosted DEV SQL, Azure deployment, provider OAuth installation or any real customer publish.

## Latest checked priority after internal P2 foundations (2026-10-23)

1. Finish/disclose current combined integration-head four-job CI after main refresh and #123, and fix any regressions on P2 only. Existing `main` might continue moving; refresh again before final PR. Do **not** overwrite Part 1's new Account/Subscription shell.
2. Implement **DB-atomic** OAuth state consume (and rejection of replay/mismatched actor), provider account connect/disconnect + encrypted credentials; backend authorization and refresh must never expose server secrets.
3. Review pending social SQL in disposable Supabase/Postgres, add negative RLS role/tenant tests, append a uniquely versioned reviewed migration after applied 11. Hosted Supabase application requires separate explicit owner approval. Historical P1 migration preflight is pinned; do not insert unapproved SQL into `supabase/migrations`.
4. Build durable publication schedule, job/attempt claim token RPC, server-authoritative subscription-quota reservation with no double debit, queue/timer and poisoned/reconciliation workers. Existing Part 1 queue names and usage enums remain untouched.
5. Implement network transports with current per-provider API requirements; never automatically retry ambiguous external create-post calls. Instagram container FINISHED, YouTube resumable binary completion, Facebook Page and LinkedIn granted author roles must be verified in mocks before live app approval.
6. End-to-end approval/edit/cancel and cross-tenant, expired account, revoked role, media-rights and quota exhaustion tests. Enable `VITE_PART2_SOCIAL_ENABLED` or `RETAIL_PART2_SOCIAL_ENABLED` only as part of independently approved hosted release.
7. When **all** internal functionality is implemented and 4/4 final integration CI green, open `feat/part2-integration` → fresh `main` final PR for coordinator. Do not merge it yourself.

## Next after security/schema correction
- Run **four actual Actions jobs** on the exact final `feat/part2-integration` commit after this doc update; don't infer integration green from the preceding PRs.
- Before final Part 2-to-main PR, inspect fresh Part 1 main and preserve latest frontend/subscription and any API changes. Current Part 2 main merge baseline was `302ee4ad`; newer coordinator commits may exist.
- Still no real OAuth code exchange/refresh/disconnect, no publication quota configuration, no durable social dispatcher SQL and Queue trigger, no posted social content or E2E. Implement and test those as separate owner-managed Part 2 branches without requiring coordinator merges.

## Latest next executable development after #131/#132/#133

1. Wire authenticated OAuth start and callback routes to `OAuthLifecycle` with **reviewed official provider adapters**, exact app-owned redirects, configured app credentials only on server, short-lived atomic CSRF state and verified grant scopes; encrypt before persisting. Add disconnect, refresh and provider revocation with tenant/role tests. Current code is isolated orchestration and RPC layers, not a live route.
2. Review the two `supabase/part2/pending` migration sources for unique hosted version/order; atomic OAuth source passed disposable negative SQL only. **No hosted Supabase write** without fresh explicit approval.
3. Implement transactional published-content approval and server-authoritative publication quota with existing subscription periods and no Part 1 double debits; platform API limits may differ by account.
4. Implement social publishing due dispatch, Azure Queue/timer worker, attempt lease fencing, media preflight, reconciliation and poison receipts. Ship no provider writes until all guards and test fixtures are complete.
5. Extend test coverage to mocked Playwright OAuth/account connect/schedule/revoke/publish, SQL concurrent-claim negative tests, and platform media/license/retry/expiry cases; require final 4/4 integrated commit after main refresh. Final PR to `main` must **not** be opened while incomplete.

## After Part 1 platform-admin sync (#134)
- Treat `main` `33ee5769` as the latest **reconciled** P1 baseline; any later main commits require another reviewed merge before final Part 2 PR. Do not roll back `/platform-admin`, P1 12th migration or its 4/4 browser/SQL tests.
- Keep **platform super-admin** and **shop OWNER social-publishing consent** distinct. Neither token holder may silently impersonate or post for another shop.
- Build the not-yet-wired OAuth provider transports, refresh/disconnect API, social job quota/dispatch/lease and tested scheduling/approval frontend. Do not request Coordinator merge of these internal tasks.

## Follow-up after internally merged #138 (YouTube OAuth)

1. Wire the **authenticated** OAuth start/completion/disconnect API to the existing owner-bound `OAuthLifecycle`, service-only transactional repository and reviewed YouTube adapter through explicit **server-only** environment settings and exact redirect; prevent raw OAuth code/token logging and callback replay. Default disabled.
2. Add official Meta Facebook/Instagram and LinkedIn identity/code-exchange adapters and safe refresh/revocation; test account-role boundaries and denied permissions. Do not present a connected account from mocked transport alone.
3. Finish atomic social publish quota, scheduled claim/lease/receipt SQL, queue worker, approval/schedule/cancel UX, real provider transport/media pipeline and mocked E2E. Keep both Part2 staged SQL migrations pending until **separate hosted approval**.
4. Require exact integration SHA four-job GitHub Actions success after any new internal merge. Final Part2->main PR is **not ready**.

## Current executable priorities after #140–#145 parallel merges (2026-10-23)

1. Finalize independently running **[#146](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/146)** staged SQL attempt fencing only after **4/4 actual Actions jobs** pass. This adds due-job discovery, claim CAS, pre-network `SENDING` barrier and receipt/reconciliation. It is pending-only SQL, not a live publishing worker.
2. Wire official platform adapters into the disabled-by-default OAuth backend *only after* verifying each provider's exact supported server-side OAuth flow/permissions. Currently the **YouTube** adapter alone is registered; Meta and LinkedIn adapters are reviewed source modules, not enabled live. Confirm LinkedIn app-specific PKCE access and scopes and Meta business configuration/permissions before enabling. Register production OAuth apps and configure secrets only with owner approval.
3. Build authenticated OWNER/EDITOR **draft -> reviewed hash approval -> scheduled publish -> revoke/cancel** API plus frontend with server-side current role and media rights checks. Never create a post from a browser-provided approval flag or callback.
4. Integrate real **DB-atomic quota reservation and attempt RPC** with encrypted credential loader, a dedicated Azure Storage Queue and timer/poison reconciliation. Keep worker disabled by default; queue payload UUID-only; manual reconciliation of ambiguous remote writes, no blind provider retries.
5. Implement actual platform publish transports and receipt/verification: Instagram FINISHED media container + media_publish, Facebook Page feed roles, LinkedIn organic text post, YouTube resumable binary completion and privacy/consent. Verify tenant-owned media, rights, model-generated disclosure, platform limits and expirations before any real send.
6. Run browser mocked E2E, replay/expiry/wrong actor tests, transaction concurrency and media/license/quota negative tests, then CI **4/4 on the exact final integration head** after refreshing fresh `main`. No Part2->main PR while end-to-end code is incomplete.
7. Seek **separate explicit approvals** for (a) hosted P2 database migration, (b) Azure backend/worker deployment, (c) installing OAuth apps with required reviews/secrets, (d) test/sandbox content publishing and (e) published plan quotas. None are implied by ordinary internal PR merges.

Completed, not repeat: PR #140 OAuth routes, #141 LinkedIn adapter, #143 gated UI, #144 quota source, #145 Meta account adapter (all 4/4 exact feature-head CI and merged to Part2 integration). Their implementation is not evidence of hosted functionality.


## Next executable cross-workstream priority after #150/#152
1. Review current `main` `a1bac624` Part1 login-first/admin UX against current P2 root `App.jsx`. Coordinator retains final Part2-to-main integration; do not overwrite P1.
2. Connect browser social draft/approve/cancel UX to flagged `/api/social/jobs/{create,approve,cancel}`; collect customer review intent and selected real campaign days/accounts, show quota/denial errors, support revoke/edit/reschedule invalidating stale hashes.
3. Add server-authoritative media license/probe review and grant to Instagram/YouTube approval; current P2 staged authoring SQL intentionally returns false for both video providers. Implement Meta and LinkedIn OAuth upstream transports/refresh/revocation with app approvals before registering their OAuth builder providers.
4. Complete a dedicated Azure queue adapter, due timer, poisoned attempt recovery, fixed provider outbound HTTP clients, token refresh/credential loading and provider receipts; preserve claim-before-send and RECONCILE on ambiguity.
5. Run real mocked browser and SQL concurrent CAS negative tests; require 4/4 combined P2 integration head, but hosted P2 migrations and actual platform content require separate explicit owner authorization. Keep final PR to main unopened until complete.


## After #155 and #156 — highest-priority unfinished work
1. Review [#158](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/158) exact four Actions jobs, fix within text-transport branch and self-merge to Part2 integration only if green. Do not silently enable live outbound posts.
2. Build service-only credential decrypt/refresh and context loader that verifies shop/account role, original approval hash, quota reservation, media rights, current scopes, platform limits and private claim token before publishing.
3. Wire dedicated social Azure Queue consumer, scheduled due scanner, poison and reconciliation workers only once `social_dispatch.process_publish` and staged RPC safety are fully covered; a possibly successful external create-post must never auto-repeat.
4. Complete Instagram Reel container processing and `media_publish` receipt and YouTube resumable binary upload completion/verification. Use approved rights/FFprobe/provenance records and no user-supplied public video URL. Include cross-tenant, expired rights, revoked grants and failed provider receipts.
5. Finish frontend editing, rescheduling/revoking stale approvals and Playwright/mock E2E. The initial reviewed form supports text-only Facebook/LinkedIn drafts; video authoring approval is intentionally denied until media certification exists.
6. Keep P2 migrations in `supabase/part2/pending`, all browser/backend publishing switches OFF and no live account/content action without specific approval. Reconcile newer `main` `1c59f981`; final Part2->main Coordinator PR remains blocked.


## 2026-10-23 — Verified follow-up: text posting source #158
PR [#158](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/158) completed **4/4** on [Actions #40007522818](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40007522818) and was internally squash-merged into feat/part2-integration as `80805066`. This supersedes any earlier note calling #158 pending. It implements source-only, opt-in Facebook Page text and LinkedIn member text request/receipt checks with uncertainty handled as RECONCILE. **Not yet activated:** real provider publishing, worker connection, hosted P2 migrations, approved OAuth apps, video uploads and independent publishing quotas. Next task is the secure credential loader and server-authoritative job-context worker with test-only provider calls.


## Immediately following verified #161/#162
1. Finish provider grant lifecycle: server-only refresh-on-expiry with provider-specific grants, Page/token revocation confirmation and account disconnect atomicity. Do not infer unknown expiry as permanent permission.
2. Wire guarded `social_due_queue.py` to Azure due timer and queue/poison receipt consumers, using the new `SocialPublishRpcRepository` and `social_dispatch.process_publish`; add explicit provider configuration, media review, private token lifecycle and reconciliation before any outbound network write. No hosted worker activation until all gates are approved.
3. Add actual Instagram container FINISHED / media_publish and YouTube resumable binary uploads with remote IDs and ambiguous-network reconciliation. Authoritative media tenant/provenance/license and H264/AAC/FFprobe checks are required. Current P2 SQL correctly denies video approval.
4. Validate entire publisher under offline tenant/role/expired grants, duplicate enqueue, stale hash, revocation, quota rollovers, failed SQL pre-send barrier and ambiguous provider receipts; run 4/4 CI on final exact integration commit.
5. Six P2 migrations `190000,190100,190200,190300,190400,190500` remain **staged only**, no hosted DEV writes; `social_publish_plan_limits` begins empty. Get distinct owner approvals for hosted SQL, OAuth apps, Azure worker release, test posting and publish plan allowances. Refresh latest P1 `main` (observed `19124243`) only via reviewed coordinator compatibility merge. Do not open incomplete final PR.


## 2026-10-23 — Latest actionable queue after #171/#172/#174
1. [PR #175](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/175) passed [four exact jobs #40019171343](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019171343) and internally merged `362ffd0b`. Post-merge Part2 [run #40019649987](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019649987) **4/4 passed.** It provides DRAFT-only edit/rescheduling, not cancellation/refund of outbound jobs.
2. Reconcile latest Part 1 main without overwriting platform admin, login/email or subscription changes; keep Part2 SQL staged-only. Refresh migration ordering including `20261023190900_p2_social_draft_revision.sql` if #175 merges.
3. Implement missing account selection, provider-verified scopes/revocation, safe Instagram/YouTube worker media/session persistence and receipt reconciliation, real-grant uncertainty handling, approved-job cancellation/refund/reschedule policy, security E2E and tested release configuration.
4. Verify four-job exact integration CI, update part2 handoff and only then offer a final Part2-to-main PR to Coordinator. Separate owner approvals required for hosted SQL, OAuth app reviews, Azure triggers, plan publishing limits and any real posts.

5. Inspect [PR #180](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/180) actual Playwright browser E2E CI, fix test/product regressions without skipping checks, merge only when four jobs green, then recheck exact integration CI. Source-only #178 JWT redirect fix is already 4/4 and merged; no hosted feature flags are enabled.
