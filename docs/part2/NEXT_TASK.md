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

6. `main` now `d590a3cf` (diverged; 12 ahead/47 behind against P2 `b78cd4d0` as checked). Coordinator compatibility pass must preserve newer P1 onboarding approval SQL, platform admin/auth SPA fixes, main App.jsx and release workflows. No final PR until refreshed safety review.

7. #183/#184 RLS social audit metadata and dashboard warnings are **complete source milestones**, each 4/4 CI and internally merged. #180 browser mock first failed because the social workspace called a nonexistent Supabase JWT accessor. Corrected in workspace and callback, branch run #40022253485 passed 4/4 and merged `870b6334`. Verify exact integration CI and continue remaining source-only provider/reconciliation work. Then verify integration-head CI and update checkpoint. No production publish flags, hosted migrations or real provider posts.

## 2026-10-24 — After offline four-provider samples
1. Review the exact-head 4/4 PR and post-merge Part 2 integration CI for offline publisher gallery; mock browser and unit tests must not be skipped.
2. Keep existing Part 1 poster/video generation out of Part 2: next connect only **authorized, rights-cleared** campaign content to reviewed draft previews, not new media-generation features.
3. Finish real provider OAuth selection/permissions, Instagram Reels container and YouTube resumable media receipts, publish quota policy and retry/reconciliation; require distinct owner approvals before hosted SQL, deployment, OAuth app install or test social posts.
4. The gallery is *not* evidence of a real posted LinkedIn/Facebook message, Instagram Reel or YouTube Short. The Final Coordinator owns the last branch-to-main compatibility review.

- 2026-10-24 — Clothing preview next: Verify four CI jobs on PR and merged Part 2 branch. For an **actual** user-photo-driven RetailGrowthAI campaign, image must be uploaded by an authenticated shop user through existing private-media registration, then generated by the existing Part 1 Foundry and FFmpeg flows; do not publish the user photo into this public GitHub repository or claim that the static social gallery invokes Foundry. An app-hosted clothing preview link requires a separately approved branch integration + SWA deploy, not a made-up URL.

## After source-only media transport PR #218
1. Confirm exact four-job CI on #218; address any failure before merging to feat/part2-integration. Verify post-merge branch CI independently.
2. Wire Instagram/YouTube **only after** an approved server-owned media preflight record, tenant/private-media lookup, valid H.264/AAC FFprobe, time-bounded signed media, consent and approved provider grants. The outbound adapter remains opt-in and unregistered by default.
3. Persist encrypted provider upload session/remote container state in reviewed P2 SQL with lease CAS; reconcile ambiguous initiation, HTTP 308 partial transfer and Instagram publication, never blind retry remote writes.
4. Source-only provider adapters do not authorize live platform tests. Hosted migrations, Azure queue/worker deploy, provider credentials, account grants, quota values and any real post require separate explicit owner approvals.

- 2026-10-24 — Source safety #221: verify all four checks before P2 internal merge and post-merge branch CI. Next unblock server-authoritative licensed media approval and provider remote receipt reconciliation only with separately approved hosted migrations, OAuth grants, quota limits and cloud worker release.

## 2026-10-24 — Verified after #218/#221, actionable remainder
1. **Do not repeat completed safety work**: #218 and #221 merged into the dedicated integration branch with post-merge four-job CI; #220 closed unmerged, no action.
2. Finish reviewable, service-owned Instagram/YouTube media certification: only tenant-authorized existing Part1 MP4s with license provenance, expiry and H.264/AAC probe; staged-only SQL must bind media approval and provider session/receipt to shop/job and prevent replay or cross-tenant approval. Transport #218 remains default disabled; do not switch on unapproved live worker.
3. Complete approved Meta multi-Page account selection, OAuth scopes and revocation/expiry review; real Meta/Google/LinkedIn app permissions and server secrets require owner authorization.
4. Finish video receipt reconciliation and quota cancellation/refund policy and exercise cross-tenant, revoked grant, stale hash, poisoned/repeated queue and ambiguous remote create tests.
5. Final Coordinator must rebase/merge safely against newer P1 `main` preserving login, approvals, subscriptions, platform admin and P3 isolation. Distinct owner authorizations needed for hosted P2 migration, Azure trigger/worker deploy, subscription publishing caps, OAuth app grants and test platform posts. Do not claim preview gallery is live Part1 generation or real publishing.

## 2026-10-24 — Following AAC media review hardening (source-only)
1. Verify all four GitHub Actions jobs on `feat/p2-media-aac-review-guard`, review and self-merge only to `feat/part2-integration` if green; verify post-merge integration-head CI separately.
2. Implement a **trusted server-side** media evidence producer that streams the authorized existing Part 1 tenant asset, computes and binds its actual SHA-256, probes real H.264/**AAC** media using FFprobe, and attaches independently checked license/expiry evidence. Do not accept client-submitted FFprobe JSON or arbitrary hashes as a certification.
3. Add job-bound, lease-CAS Instagram container/YouTube resumable session and receipt persistence, complete reconciliation tests, permissions/account selection and plan-specific quotas. Keep staged P2 SQL, OAuth and all outbound publishing release gates OFF until separately authorized.

## Following trusted private MP4 preflight source PR (2026-10-24)
1. Check all four CI jobs for `feat/p2-trusted-mp4-preflight`, review/merge to the dedicated Part 2 integration branch only after green; verify integration CI separately.
2. Connect only a separately reviewed server-owned asset loader: verify signed-in shop membership, Storage object rights, authoritative source SHA (never a browser-supplied hash), registered media ID, FFprobe results, rights evidence, rights expiry and approved revision; persist source digest before granting any new video approval.
3. Close remaining fail-closed lease-CAS Meta/YouTube remote session/receipt reconciliation, provider grant/revocation, quota/refund policy and E2E. Hosted schema, OAuth grants, worker deploy and actual publishing remain separately owner-gated.

## 2026-10-24 — Verified source merges; do not redo #244/#245
- #244 AAC SQL review guard and #245 trusted private file hash/FFprobe primitive are internally merged to `feat/part2-integration` at `9bd5830`. Post-merge four-job Actions #40094490959 all passed.
- Highest-priority engineering blocker: integrate trusted Part1 tenant media fetch, independently stored source digest, actual FFprobe, license/rights and expiry verification, and immutable approved social job/media/revision context. The preflight helper is NOT an authority to publish.
- Next complete durable Meta/YouTube session and receipt reconciliation, provider account grant/revocation and published quota/refund policies, then offline adversarial E2E and coordinator compatibility with newer Part1 main. Hosted migration, OAuth app activation, Azure deployment and actual posts require separately explicit approvals; feature flags stay OFF.

## Unsent cancellation quota accounting (staged source change)
- Verify exact-head and post-merge four-job CI for `feat/p2-cancel-quota-safe-refund` before marking complete.
- Never refund `SENDING`/`PROCESSING`/`PUBLISHED`/`RECONCILE` or any active-claim job. The staged cancel RPC can release a reserved unit only once for an authorized never-sent cancellation within the same DB transaction.
- Remaining priorities: job/version-bound licensed video authority from actual Part1 private bytes, provider session/remote receipt reconciliation and app grant lifecycle, safe Azure trigger release after explicit operator gates, eventual Final Coordinator compatibility with newer main.

## 2026-10-24 — Video source review binding next gates
- Check four PR/post-merge CI jobs for `feat/p2-media-job-review-bindings` before marking merged. The video approve SQL hard-deny stays in place.
- Wire service-only candidate retrieval to existing private Part1 MP4 download and bounded real FFprobe: establish source digest from trusted service-owned bytes; require independent commercial rights evidence. Re-check bytes/object immutability at publish, because Part1 Storage UPDATE/DELETE permissions can alter an old reviewed object.
- Complete claim-fenced encrypted provider upload session/receipt and definite/ambiguous reconciliation, then review P2-to-main compatibility and separately approved OAuth/quotas/hosted deployment. Never treat a job review binding as final publisher authorization.

## Video upload state (staged source) next
1. Require all four exact-head and post-merge CI checks before accepting the new private session/receipt source work.
2. Wire existing Instagram/YouTube staged transport to fixed service-only job/claim RPCs and cryptographic session encryption; ensure the remote account/tenant/media digest, granted scopes and durable intent are verified BEFORE each outbound provider request. Any unknown response -> RECONCILE, no second create/upload.
3. Finish immutable provider-readable media copies for Meta, real signed URL expiry, rights preflight and job revision CAS. Do not activate video approval or scheduled Azure workers before hosted migrations, approved OAuth app credentials and publish quotas.

## Source-only certification pipeline remaining integration
1. Verify four-job CI, reviewed internal merge and post-merge branch CI for `feat/p2-reviewed-video-preflight`.
2. Provide a real service-side render-finalized SHA receipt and external rights-review ledger (no client-supplied digest or claims); resolve timestamp from tenant-authorized P2 DB source, then bind the existing private record CAS using backend service role.
3. Re-verify stored media bytes or immutable provider-safe copy immediately before Meta/YouTube upload; integrate claim-fenced encrypted video upload RPC/session state and transport under a separately approved release. No live video approval until this is tested, grant-scoped and gated.

## Part2 finalization after private evidence registry
1. Confirm exact four-job CI and review/merge of staged render integrity + rights ledger; verify post-merge Part2 branch.
2. Coordinate with Part1 output finalization to write a server-computed SHA immediately after successful render, before editable Storage content may change; obtain separately reviewed commercial license attestation for each video job and expiry. Browser-provided attestation/digest are forbidden; do not backfill by merely trusting user-editable metadata.
3. Last blocker for safe real video publishing: immutable provider-fetchable copy for Meta, rehash at final transfer, signed URL expiry, claim-fenced stage RPC→remote adapter with token scope, provider receipt reconciliation and mock-to-hosted security/E2E.
4. Final Coordinator handles Part2→current main compatibility; hosted migration, app permissions, plan publish caps and actual posts require verified operator configuration and explicit release.

## 2026-10-24 — Immutable outbound media export remains gated
- Verify exact-head and post-merge four-job CI for the service-only export bucket/publisher URL policy. An ordinary P1 tenant media signed URL must now be rejected by Instagram transport.
- Implement the reviewed copy-once producer from a hash-pinned P1 MP4 into isolated `retailgrowth-social-exports`, check stable bytes before+after storage handoff, strict rights/revision/account/claim CAS and URL TTL. The export uploader may not overwrite or let users edit provider-readable content.
- Register the consented video worker only after hosted P2 migrations, plan publishing caps, legitimate approved Meta/Google scopes and E2E provider-safe test accounts. Keep provider posting OFF until that release review.

## Signed export writer integration pending
- Confirm exact feature and integration branch four-job CI for the off-by-default media exporter. Backend `claim_authority.allow_export` must be implemented by a service-role RPC rechecking active approved video job, rights expiry, grant, quota, source SHA, scheduled/revision fence and outbound lease just before both copy and signing. A generic boolean request parameter or browser role is unacceptable.
- Activate only after explicit hosted P2 migrations + billing/quota caps + OAuth provider app consent, real media rights and Azure queue/poison tests, and Meta/YouTube receipt reconciliation. Browser never receives exporter credential, signed URL or provider token.

## Active video claim/export authorization remaining bridge
- Verify feature exact-head 4/4 CI, internal PR merge and post-merge branch CI. Claim-CAS backend authority is now available as a source-only component for the existing disabled export writer.
- Still must connect finalized P1 render SHA receipt production at trusted render completion, independently reviewed rights evidence, job/media/revision approval, optional provider-fetchable immutable export upload, and the provider-specific remote session state/receipt through a real tested Azure worker. The current live worker deliberately remains TEXT-ONLY; video approval hard-deny stays.
- Real provider OAuth app grants, licensed test accounts, plan caps, P2 hosted migrations and Azure release/real posts must be verified before enabling anything. Final Coordinator reconciles advancing Part1 main and opens final merged Part2 release.

## Corrected release architecture: one private P1 media bucket
- The pending-only P2 SQL 191400 now reserves an authenticated-client-inaccessible `<shop>/social-exports/` prefix inside original P1 `retailgrowth-media`; never provision a second bucket. Verify exact four-job CI and post-merge integration branch.
- Still required: real trusted Part1 final render SHA recording, separately checked commercial-rights evidence, service-only claim/rights validation, copy-once export under single bucket, final upload + remote reconciliation and hosted test. Real publishing remains OFF. Coordinator owns final integration into latest Part1 main.

## Provider-create duplicate safety
- Verify four-job exact-head and post-merge CI for `feat/p2-ambiguous-video-retry-guard`. Ensure the publisher treats any failed already-started media initiation as reconciliation, not FAILED or RETRYABLE unsent. Durable remote receipt verification/Instagram status and encrypted YouTube 308 recovery remain release requirements.

## Video upload DB bridge remaining release conditions
- Verify feature exact-head 4/4 CI, internally merge only to `feat/part2-integration`, and confirm independent post-merge branch CI. All Azure media publishing still deliberately unregistered; Part2 must not claim live Instagram/YouTube.
- Outstanding source integration: trusted Part1 render-finalized SHA writer and externally reviewed commercial-rights process, actual video approval CAS (currently hard-denied), immutable export bytes+signed URL anchored to claim, AAD-key availability/rotation policy, OAuth provider-granted apps, Meta/YouTube remote receipt reconciliation and quota/cancel E2E.
- Final Coordinator must reconcile latest Part1 main, preserve Part3 source and configure only separately authorized hosted DEV migration/worker release/plan publish quotas. No live posts without a confirmed test account and explicit release switch.

## Quality checkpoint — AES negative test stability
- Verify exact-head and independent post-merge four-job CI for `feat/p2-deterministic-aes-tamper-test`. This is a negative-test reliability fix only; it does not unblock live social publishing or provider app/rights/hosted gates.

## P2 reviewed video approval CAS — integration boundary
- Run exact-head 4-job CI, verify disposable Supabase positive/negative evidence and service-role-only access, merge `feat/p2-reviewed-video-approval-cas` internally only when green; confirm post-merge CI.
- Preserve legacy text-only HTTP `p2_approve_social_job` and outward worker gates until real Part1 finalized SHA receipt and independently validated commercial license documents/expiry exist. The new source-only service RPC is NOT to be exposed through a browser route until approved backend read/computed digest integration, provider account OAuth grants, publishing plan caps and whole-route E2E.
- Coordinator will reconcile later Part1 `main`, then separately approve hosted migration and release tests. No live social posts performed.

## Video approval service next integration gate
- Verify exact-head feature CI for the source-only, disabled backend approval adapter, internally merge only after 4/4 and inspect post-merge P2 CI. Do NOT register it as a public route without a separately approved release contract and real hosted license+render SHA and OAuth app/plan cap checks.
- Remaining P0: legitimate P1 finalized-render service receipt, real commercial music/stock-use clearance, immutable same-bucket export & final hash at transfer, SQL claim/receipt state reconciliation under real provider sandbox tests. Only Final Coordinator integrates Part2 with latest P1 `main`.

## Part1 render SHA callback dependency after source adapter
- Verify exact-head four-job CI, internal merge and post-merge branch checks for `feat/p2-render-finalized-receipt-writer`.
- Ask Part1/Final Coordinator to integrate this service-only adapter at original FFmpeg render completion while retaining trusted private output bytes, after persisting SUCCEEDED render/asset and before releasing the private scratch. Do not call this as backfill from tenant-editable Storage or expose its method on public HTTP. Verify P1 object bytes and SHA persist at finalization, and separately validate music/stock commercial rights. Only after those prerequisites can the P2 video approval review be used for licensed DEV tests.

## 2026-10-25 — Remaining Part2 release blockers after verified source PRs
- Verify post-merge #292 CI #40169220089 and docs PR; no open internal source PRs anticipated after checkpoint.
- Cross-part P0: Part1 renderer must wire trusted finalizer adapter and produce actual immutable original-output digest; independently licensed stock/music reviewer must populate rights evidence (including expiry and commercial permission). This cannot be faked by generated-asset metadata.
- P0 external: enable real provider OAuth test grants, owner-approved social publication plan limits and consented test accounts; only then coordinate hosted P2 SQL 190000–191700, Azure timer/queue/poison worker and conditional video API activation with explicit owner rollout review, negative E2E and durable remote receipt reconciliation.
- Coordinator alone handles main compatibility and final PR; do not modify WineShopPOS or disable existing social/Part1 safety guards.
