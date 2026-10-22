# RetailGrowthAI - Project State

## Goal
Build a low-cost, multi-tenant Agentic AI marketing SaaS.

Owners give natural-language marketing instructions.
The system generates multi-day marketing campaigns.

## Example campaigns
- Clothing brand: 7-day Navratri campaign with product images.
- AI engineer: daily Agentic AI educational posts.
- Restaurant: Diwali 20% offer campaign.
- Beer retailer: compliant informational content.

## Four-Part Roadmap

### Part 1 - AI Campaign Creation
- Shop onboarding and authentication
- Multi-tenant business profiles
- Natural-language campaign briefs
- Multi-day campaign planner
- LinkedIn written posts
- Instagram banners and captions
- Instagram Reels with multiple images
- Discounts, music, transitions and CTA
- 30-second stock footage videos using FFmpeg
- Preview, edit, save and download

### Part 2 - Platform Integration
- Instagram and Facebook
- LinkedIn and YouTube
- OAuth, scheduling and publishing
- Automated posting and approvals

### Part 3 - Premium Video
- Alibaba Wan integration
- Budget-aware premium AI video generation

### Part 4 - Final Testing
- End-to-end testing
- Security and tenant isolation
- Performance and cost controls
- Production readiness

## Technology
- React + Vite
- Supabase PostgreSQL, Auth and RLS
- Azure Functions
- Azure AI Foundry
- LangGraph
- Python managed with uv
- FFmpeg
- Azure Storage GPv2
- GitHub

## Current Status
GitHub access and initial uv scaffold verified. Architecture and parallel contracts documented on 2026-10-22. Coordinator bootstrap on 2026-10-22 added a runnable React/Vite shell, router and shared mock campaign fixture. GitHub Actions completed successfully on the bootstrap commit: npm installed 69 packages, 2 JavaScript tests passed, 1 Python test passed, and Vite v7.3.7 built 42 modules. Evidence: https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39739502984. No business service is implemented.

No generated or published campaigns exist yet; the seven-day UI fixture is mock data. Workstream A tenant schema, RLS and Auth are merged; AccountWorkspace is mounted and the CampaignDashboard is mounted but uses local request previews, not a live API.
A dedicated RetailGrowthAI **DEV/pilot** Supabase project exists (`jeearzffnjbvghwjjjrf`, Tokyo); a separate production project does not exist.
No new Azure application resources deployed yet.

## Next
See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by project-specific credentials/resources; do not connect WineShopPOS.

## Parallel Part 1 architecture baseline
- See docs/ARCHITECTURE.md for technical flow and infrastructure boundaries.
- See docs/INTERFACES_V1.md for campaign/day/render API contracts and fixtures.
- See docs/PARALLEL_WORK.md for four feature branches, disjoint file ownership and integration rules.
- Coordinator bootstrap: React/Vite router shell and seven-day v1 fixture on main, dependency-free JavaScript and Python contract checks, and GitHub Actions build workflow.
- Four Part 1 feature branches created from the verified coordinator baseline: feat/p1-foundation, feat/p1-campaign-ai, feat/p1-video, feat/p1-campaign-ui. See docs/PARALLEL_WORK.md; the workstreams have not implemented features yet.
- No cloud deployment or live model calls verified as part of this architecture milestone.

## GitHub Actions expansion — PR #1 merged (2026-10-22)
- PR #1 (`chore/part1-ci`) squash-merged to `main` at commit `6e3627968beb8288afe857adea0238db4fcda862`.
- Three new independent CI jobs (frontend, Python/uv, FFmpeg) all passed **after merge** in [GitHub Actions run #39745758948](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39745758948).
- Frontend runs npm install until `frontend/package-lock.json` is reviewed; Python checks also run the campaign planner/service and coordinator B-to-C contract tests; video-engine/ci.sh runs a real 30-second synthetic MP4 render in addition to the 2-second smoke.
- Four remote Part 1 workstream branches exist; coordinator synchronizes them to the final documented baseline before worker chats begin. No live model, tenant database, cloud resources, publishing, or production render was created by this CI update.

## Coordinator auth/security integration proposal — 2026-10-22
- Branch `chore/p1-foundation-auth-ci-integration` is based on open Workstream A PR #5 (do not merge out of order).
- AuthProvider now wraps the application shell; `/account` renders AccountWorkspace (sign-in, registration, shop creation, profile editing) instead of the bootstrap placeholder. The campaign overview is still clearly mock-only.
- A fourth Actions job runs Node browser Auth client tests and starts disposable local Supabase Postgres to apply all three A migrations and execute both negative RLS/storage SQL scripts; uses no cloud credentials and cannot modify hosted resources.
- Workstream A previously verified 10 RLS-enabled tables, 25 tenant policies, four private-storage policies, and zero Supabase security advisories on the dedicated DEV/pilot project. Live tests used rollback and created no persistent test data.
- Do not interpret code/CI success as real browser login over HTTPS; VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY must be set in a RetailGrowthAI-only deployment, followed by manual functional testing. No production database/project is available yet.

- Coordinator branch verification: [Actions run 39752723276](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39752723276) **passed all four jobs**, including live-on-disposable-DB SQL negative tests and browser-client Node tests. This is branch-only CI evidence; main and the production deployment are unchanged.


## Integrated Part 1 checkpoint — 2026-10-22
- PR #5 (Supabase foundation) merged as `0ae77540f5808a3e16bba116ab024781ba55e8c0`; stacked PR #6 (Auth route + isolated security CI) retargeted, then merged as `8ab4250f5763164d914a0566395008f6aa960189`.
- PR #3 (mock planner/API boundary) merged as `b75438da96334020bdea08603c312bd1a398c451`; PR #2 (FFmpeg 30-second offline renderer) merged as `7ae0c50e12b226599255be49af6b5970674b3ced`.
- PR #4 (React campaign studio) required a root `App.jsx` conflict resolution with AuthProvider. The reconciled PR branch passed **four jobs** in [run #39755166150](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39755166150), then merged as `8d2e85e50d05d542d285784e566459ff2b5f691e`.
- Account route supports configurable RetailGrowthAI DEV Auth; campaign route supports a seven-day **mock** editor/export. Python generates/offline-reviews v1 data; the video CLI renders validated synthetic media. A coordinator integration test asserts planner output can be consumed by the renderer, including rejection of mismatched shops and unauthorized assets.
- Four GitHub Actions jobs: frontend tests/build; Python pytest + coordinator cross-component contract; FFmpeg smoke + real synthetic 30-second render/ffprobe; isolated Supabase Auth/RLS/storage negative tests. Read the final post-integration Actions run before claiming this last commit is green.
- Dedicated RetailGrowthAI DEV/pilot Supabase (Tokyo, ref `jeearzffnjbvghwjjjrf`) exists, but credentials are **not** committed/configured for hosted frontend. PROD remains absent. No WineShopPOS resources touched.
- **Not yet end-to-end:** no deployed authenticated campaign HTTP endpoint or durable queue, no live Foundry/AI credentials, no uploaded/authorized real user media manifest or signed MP4 delivery, no browser-to-API wired campaign generation/save/render, no platform OAuth/publishing or production QA.

## Secure API milestone (PR branch, 2026-10-22)
- Azure Functions v2 HTTP adapter authored: signed RS256/ES256 Supabase JWT checks with pinned project issuer/audience; RLS user-token PostgREST tenant reads and write-gated campaign creation.
- **POST remains fail-closed (503)** until a durable queue is added. GET can return tenant-filtered draft records when configured. Not deployed, not E2E-verified.

## Durable planning milestone (branch)
- Added pending-campaign media IDs, atomic claim/attempt/lease migration, Azure Storage Queue producer and queue-trigger planner with revoked-membership/media rechecks. This is code only; **neither migration nor Azure queue deployed**. Production Foundry remains unconfigured.

## Render API milestone (branch)
- Authenticated render job create/status and short-lived signed private download endpoints implemented in code. Tenant rights checks and request idempotency included. Actual renderer worker, object upload and cloud deployment remain unfinished.

## Render worker milestone (branch)
- Azure Queue trigger and service-only PostgREST claim handler code for private 30-second FFmpeg generation, tenant source/right checks and private output recording added. No cloud migration/service deployed or real user video verified.

## Live frontend API wiring (branch)
- React dashboard now supports an explicit authenticated API mode with shop selection from RLS-backed memberships and authorized media IDs, job polling, render status and private signed MP4 links. Absent API configuration it remains a clearly labeled mock editor. No cloud deployment, upload UI or remote edit persistence.

## 2026-10-22 — Coordinator backend authorization hotfix
- Queue error cleanup is an explicitly scoped backend status update; a missing backend key blocks POST before persistence. Opaque Supabase sb_secret_ keys use apikey only, legacy service JWTs additionally use Bearer. Private media 409 collisions fail closed. Offline tests added; no cloud deployed.


## Coordinator feature-integration checkpoint — 2026-10-22
- Merged PR #7 (secure Supabase JWT HTTP API), #8 (durable campaign queue and DB lease), #9 (render API and signed private downloads), #10 (FFmpeg queue worker and private upload), #11 (authenticated React live-mode wiring) and #12 (backend status cleanup, opaque-key/media safety). Each milestone passed the four-job CI before merge.
- Live-mode campaign request preview now uses selected RLS-authorized shop/media IDs, not fixture UUIDs; offline UI remains in demo mode without settings.
- All changes are GitHub source code and disposable CI tests only. **No Azure Functions deployment, Azure Queue creation, additional Supabase resources, DEV migration push, or browser E2E was performed.** An existing RetailGrowthAI DEV database is not equivalent to a deployed API.
- Use latest main GitHub Actions run as final CI authority; project is NOT production-ready.

## 2026-10-22 — Draft-save API milestone (feature branch; no deployment)
- Added authenticated PATCH /api/campaigns/{campaign_id}/days/{day_id} for remotely saving only editable day fields, after v1 campaign shape validation, active OWNER/EDITOR membership and shop asset checks.
- New migration removes direct authenticated campaign_days UPDATE grants and exposes an optimistic, membership-rechecking save RPC. Concurrent stale writes, non-DRAFT parent campaigns and active queued/running renders fail closed.
- Added Python API/transport denial tests and disposable Postgres RPC bypass/viewer/conflict checks in the fourth CI job.
- **Pending:** branch/PR and post-merge CI evidence, DEV migration approval/application, frontend Save button and real browser E2E. No Azure or Supabase hosted resource was modified.

## 2026-10-22 — Authenticated draft Save UI (stacked feature branch)
- CampaignDashboard now provides live-only **Save day** for topic, LinkedIn and Instagram edits via scoped PATCH API; returned tenant/day identity is checked and local baseline updates only after success.
- Late in-flight edits remain visibly unsaved. Render is blocked during save or whenever the local day differs from the server baseline. Demo fixture still has no remote Save button.
- This is front-end code only; the draft-save API/SQL migration PR must land first. No deployed UI, real assets or browser E2E verification.

## 2026-10-22 — Private tenant image uploads (feature branch, NOT deployed)
- Authenticated React uploads actual PNG/JPEG/WebP bytes (25 MB limit, signature check) into the existing private `retailgrowth-media` bucket under tenant-specific `shop_id/uploads/UUID.ext` paths without service keys. The uploader requires user-confirmed commercial rights and source attribution/evidence.
- New restricted `register_uploaded_image` Postgres RPC derives MIME and size from the uploaded storage object's metadata; checks current storage-object owner and active shop OWNER/EDITOR membership, supported type, license evidence and uniqueness. Browser INSERT into `media_assets` is revoked to prevent metadata-only fake assets.
- Browser displays rights as **user-declared**, never provider-verified. No automated legal provenance audit or user-generated commercial publishing approval; real media processing and final output E2E still require a hosted DEV environment and approvals.
- New isolated SQL security tests cover cross-shop/viewer/anonymous registrations, missing/mismatched objects, MIME spoofing, duplicate paths and forbidden INSERT. Browser Node tests cover token forwarding, binary upload and denial. No Supabase DEV changes, Azure deployment or WineShopPOS mutation.

## 2026-10-22 — Merged draft-save and media upload checkpoints
- PR #14 authenticated day edit API merged as `0317ea2e`; post-merge main [run #39767119764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39767119764) passed four jobs.
- PR #15 live draft Save UI merged as `aa2f1bc4`. Four PR checks passed; [post-merge run #39768177407](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39768177407) must be checked separately for its final outcome.
- PR #16 private upload/registration merged as `6c62e514`. [Feature-PR CI #39769374328](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769374328) passed frontend, Python, FFmpeg and disposable Supabase security checks. Post-merge [main run #39769717413](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769717413) **passed all four jobs**.
- These are **source-code milestones only**: hosted RetailGrowthAI DEV has not received the new migrations and there is no deployed Azure API or queues, so real authenticated upload/render/browser E2E is unverified. WineShopPOS remains untouched.

## 2026-10-22 — Coordinator E/F/G/H integration (source only)
- Reviewed and squash-merged E [PR #18](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/18) as `f915765d`: unapplied, canonical image-only Storage policy hardening and tenant/registration negative SQL tests. Hosted RetailGrowthAI DEV had only the three initial migrations as of E's read-only review; five subsequent migrations (durable planning, render claim, day-save, upload registration, media integrity) remain unapplied.
- Coordinator [PR #22](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/22) (`283d3584`) extended the existing four CI jobs to execute newly added Python reliability and API E2E tests, mocked Playwright Chromium browser tests and approval-gated Azure packaging checks when those files are present. Coordinator feature-branch run [#39774730459](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39774730459) passed four jobs.
- Reviewed and merged H [PR #19](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/19) as `0afd8e0a`: offline poison/retry decisions, safe orphan discovery/guarded deletion interface, monitors and synthetic FFmpeg cost benchmarking. This is NOT a connected Azure poison/replay/reconciliation or deletion service.
- Reviewed and merged G [PR #20](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/20) as `0fd247df`: Python service-boundary API journeys and real React browser tests with mocked external Supabase/API. It does NOT prove hosted login, JWT, file upload, licensed MP4 or live downloads.
- Reviewed and merged F [PR #21](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/21) as `bde4357b`: DEV-only Bicep and source/FFmpeg packaging, explicit approval-gated deployment scripts. **Do not deploy** until real rendering/lease consistency is solved: existing host and DB lease are 4 minutes while FFmpeg subprocess timeout is 780 seconds; host/runtime quotas and Bicep compatibility also require verification.
- Full post-integration GitHub Actions run: [#39775525458](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39775525458), verify its final conclusion rather than assuming green. Earlier intermediate main runs were superseded/cancelled by subsequent merges.
- No cloud resource created, no hosted Supabase migration applied, no production-ready Azure worker or browser-to-cloud journey verified, no WineShopPOS modification. Licensing is still user-declared rather than independently cleared.

## 2026-10-22 — GitHub Azure DEV OIDC authentication preparation
- Coordinator merged [PR #26](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/26) as `8bcaa4d9`: adds a *manual, main-only, read-only* `dev` Azure login verification workflow using `azure/login@v3`, plus `docs/AZURE_GITHUB_OIDC.md` with the repository's immutable OIDC subject and owner setup instructions.
- PR #26 [CI run #39777549911](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39777549911) passed all four tests before merge. Verify newest post-merge main CI separately; prior intermediate main runs may be cancelled by further merges.
- **Historical PR #26 handoff (superseded):** owner-managed OIDC setup was pending at merge time. The latest verification result appears in the newest checkpoint below; resource-group IAM scope is not independently confirmed.
- This feature does **not** deploy Functions/queues, authorize migrations, grant Contributor, configure runtime secrets or touch WineShopPOS.

## 2026-10-22 — Bounded worker timeout/lease safety fix (feature PR, source only)
- Coordinator merged Azure OIDC documentation PR #27 (`1b755328`); the manual Azure DEV login check was then unverified (its later rerun succeeded; see newest checkpoint).
- Candidate next milestone changes the Flex Functions host timeout from 4 to 20 minutes and appends a **pending** migration making both planning/render claims 25 minutes. FFmpeg remains strictly capped at 780 seconds (13 minutes); a source/package test rejects drift. This prevents a database lease expiring while the host may still be executing under its configured cap.
- **Not deployment-ready:** actual asset staging/upload and 1080p encoding must be benchmarked under the target plan, failed/stale attempts need a durable reconciler and poison handlers, and the claim token/attempt should fence all final writes. No Azure resource, DEV migration, or WineShopPOS change was made.

## 2026-10-22 — Verified coordinator worker-budget integration (supersedes feature-PR status)
- Merged [PR #28](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/28) as `4b6ecb779bedaa88ebe487b8f7da679399505b64`. PR [run #39781338310](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39781338310) and **post-merge main** [run #39781848452](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39781848452) each passed all four jobs. Source host 20m, new **unapplied** 25m claim-lease migration, FFmpeg 780s and offline package consistency tests are integrated.
- Manual read-only [Azure DEV OIDC run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) **failed** with `AADSTS70025`: the `retailgrowthai-github-dev` Entra app has no configured federated identity credentials. This is an Azure portal owner-action blocker, **not** an Azure deployment. No Supabase hosted migration or WineShopPOS change.
- Unfinished: durable outbox/poison/reconciler, attempt-fenced job completion, approved runtime benchmarks and live browser-to-cloud E2E. The source-only alignment does NOT authorize cloud deployment.

## Verified Azure OIDC authentication — 2026-10-22 (latest status)
- The **latest attempt** of [Azure DEV OIDC workflow run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) completed successfully, including protected environment identifier checks, federated Azure login, and read-only subscription verification. This **supersedes the earlier `AADSTS70025` failure** recorded in prior dated checkpoints.
- Only read-only authentication/subscription visibility is verified. Resource-group role permissions, deploy permissions, runtime secrets, queues/Functions, hosted DEV migrations and real browser E2E remain unverified or approval-gated. No cloud provisioning or WineShopPOS changes occurred in this docs milestone.

## 2026-10-22 — Coordinator continuation for parallel hardening I/J/K
- [PR #30](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/30) was reviewed and squash-merged as `7c6c506a2a86127845dfa6afedd0cad1a46bf057`; all four feature PR CI jobs passed [run #39789324313](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39789324313). The same read-only Azure OIDC workflow [#39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) succeeded on **attempt 3**, correcting the historical initial failure. Post-merge main CI [run #39790938647](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39790938647) independently **passed all four jobs** on `7c6c506a`.
- Workstream branches I/J/K exist, but their branch tips were still based on the earlier `3d4495c3` commit and **no corresponding open feature PRs** had been submitted at the initial coordinator check. Their integration is therefore NOT complete. See `docs/PARALLEL_WORK.md` for updated disjoint ownership and ordered merge plan.
- No Azure resource deployment, Supabase DEV migration application, live user/media E2E, or WineShopPOS modifications by this coordinator checkpoint.

## 2026-10-22 — I/J/K source integration completed (no hosted rollout)
- Coordinator reviewed and squash-merged **I** [PR #34](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/34) as `3d115e1dea38a56e1903568651dd87e9dd1777e4`. The latest [feature-PR run #39798607296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39798607296) concluded **success** (four required tests). The **NEW, UNAPPLIED** `20261022220000_p1_durable_recovery.sql` adds an atomic planning/render job outbox, private poison receipts, CAS claim tokens/attempts, lease-fenced completion, and stale job reconciliation; Azure timer and poison Functions and offline reliability regressions are source-only.
- Squash-merged **J** [PR #33](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/33) as `f6f9b76948ae6fd8f1a226ede8dc27d5b43c4fb2`. Branch [run #39792621639](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39792621639) passed four jobs, including corrected Bicep compilation. This adds DEV-only Python Flex settings, conservative on-demand instance/memory settings, and fail-closed static FFmpeg/ffprobe ZIP verification. It **does not** provide a licensed binary, cost measurement, cloud Function indexing, or deployment.
- Squash-merged **K** [PR #31](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/31) as `5de50cd4b4decb70b0df1bac9055e9d3b66ff2b6`. [PR run #39791472265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39791472265) passed all four jobs. Expanded **mock-only** Python HTTP and Playwright browser journeys for JWT failures, membership denial, private image upload/retry, campaign errors, unsaved draft recovery and private signed downloads. This is **not** a hosted browser-to-cloud or real licensed-media E2E pass.
- Final combined [post-K main run #39801130265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39801130265) independently **completed successfully with 4/4 jobs** (FFmpeg, Python, Supabase SQL/RLS and frontend/Playwright). Intermediate runs #39800688710 and #39801076940 may be superseded/cancelled by successive merges. All workstream branches are integrated; no I/J/K feature PR remains to merge.
- GitHub-to-Azure OIDC login was already **verified** by the latest successful attempt of #39780713421. Owner reports Azure **Contributor** role granted, but this coordinator has not independently verified its resource-group IAM scope; the verification workflow performed only read-only checks. **No Azure deploy/provisioning, hosted RetailGrowthAI Supabase migration, Azure runtime smoke test or WineShopPOS change** was performed.

## 2026-10-22 — Coordinator 3 launch baseline (L/M/N/O; no deployment)
- Verified latest `main` `84c9b87be8b0c2ec4ffca2377532f5825205b979` following merged documentation PR #35 and FFmpeg bootstrap CI fix PR #36. [Post-merge `main` Actions run #39805920327](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39805920327) independently completed **four of four jobs successfully** (frontend/Playwright, Python, FFmpeg, isolated Supabase); unlike superseded run #39803979666, this run is final. PR #37 (optional Chromium timeout) was closed **without merge** because main passed; do not count it as integrated work.
- Workstreams I #34 / J #33 / K #31 are already integrated and must not be reimplemented. New L/M/N/O sprint is underway on `feat/p1-dev-db-release-readiness`, `feat/p1-azure-release-readiness`, `feat/p1-render-performance`, and `feat/p1-hosted-e2e-readiness` (first three branches already have source changes; O is at baseline as of this inspection), with disjoint ownership in `docs/PARALLEL_WORK.md`. See `docs/DEV_DEPLOYMENT_APPROVAL.md` for explicit separate authorization gates.
- No new Azure DEV resources, hosted Supabase migration application, real licensed-media benchmark or hosted end-to-end journey is verified. Azure DEV OIDC authentication previously passed, while effective Contributor IAM **scope** is still not independently validated. Seven migrations after the original three DEV foundation migrations remain reported as unapplied; confirm actual hosted migration history before authorizing changes. WineShopPOS is out of scope.

## 2026-10-22 — Coordinator 3 L/M/N/O integration status (NOT YET MERGED)
- Coordinator source-only handoff [PR #38](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/38) merged as `2ca338aba54ee628a955313175df98e97fe8a795` after [4/4 feature CI #39809952845](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39809952845); contains `docs/DEV_DEPLOYMENT_APPROVAL.md`, canonical L/M/N/O ownership and expanded offline CI discovery.
- **Post-merge main was NOT green:** [run #39810509471](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810509471) had 3/4 success; media FFmpeg package install exceeded its bounded Ubuntu package-mirror timeout. It did not execute the renderer; do not claim full post-merge success.
- L [#43](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/43) DEV migration-order/RLS/outbox negative preflight passed [4/4 PR run #39809858590](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39809858590); M [#46](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/46) read-only Azure/IAM/runtime/cost/rollback safeguards had Python/frontend/security success and media install timeout on [PR run #39810592159](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810592159); N [#44](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/44) offline synthetic 1080x1920 media benchmarking passed [4/4 PR run #39810720819](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810720819); O [#45](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/45) opt-in hosted-DEV harness source submitted, but [PR run #39811545219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39811545219) failed without runner/job steps and is not approved or host-verified.
- Coordinator CI package-mirror correction [PR #47](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/47) is pending. Its [PR run #39812135974](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39812135974), including reruns, had all jobs fail before runners or steps started. Public GitHub Status declared Actions/PR degraded performance on 2026-10-22; cannot attribute pre-run failures to source code without logs. Source PRs **#43/#46/#44/#45 are NOT merged** at this checkpoint. Continue CI/PR review after GitHub runner service resumes; verify **4/4 on each updated PR and post-merge main** before proceeding to the next merge. No hosted Supabase migrations, Azure resource changes, licensed Azure render or real hosted E2E; no WineShopPOS modifications.

## 2026-10-22 — Coordinator 3 follow-up: GitHub Actions still blocks L/M/N/O integration
- Rechecked `main` at `2ca338aba54ee628a955313175df98e97fe8a795`: the post-merge run [#39810509471](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810509471) remains 3/4, because the FFmpeg package mirror install timed out. Official [GitHub Status](https://www.githubstatus.com/) listed Actions, PRs, Issues and Packages degraded on 2026-10-22.
- Coordinator reran [CI mirror fix #47 workflow #39812135974](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39812135974) through attempt **5**, and the updated [L PR #43 workflow #39815674157](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39815674157) through attempt **2**. Both latest attempts returned 4/4 GitHub job failure **without runner names, steps or usable job logs**; this is an Actions execution blocker, not executed regression evidence. Do not claim either change passes or attribute no-runner jobs to a failing test.
- L PR #43 source branch `bb240294b48a716d1e5b75c666e52cb837b3a26a` was updated to prevent duplicate SQL and Node test execution because coordinator CI #38 discovers each separately. N PR #44 passed 4/4 earlier on `3d0dd2b0`; M PR #46 push run #39810453954 passed 4/4 while its PR run failed FFmpeg bootstrap; O PR #45 retry run #39811545219 failed before executable steps. **All four workstream PRs remain open, unmerged**. Source-only continuity docs are pending as PR #49. No Azure/Supabase hosted write, hosted E2E, or WineShopPOS change.

## 2026-10-22 — L/M/N/O release-readiness integrated on public GitHub (LATEST; supersedes blocked checkpoints)
- Repository owner changed `saifsiddiqui59/RetailGrowthAI` visibility from private to **public** to make standard GitHub-hosted Actions available after the private GitHub Free 2,000-minute Actions allowance was exhausted. Source, commit history, PRs and Actions logs are now publicly readable. No secrets should be committed; review past history/logs and rotate any exposed credential. Changing visibility does **not** authorize Azure/hosted Supabase actions.
- GitHub Actions became executable after the change. Coordinator merged CI apt mirror repairs **#47** (FFmpeg, `e9d6c47ff0041c285c58b056dc08e644ea109912`, exact-head PR run [#39812135974 attempt 6](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39812135974) 4/4) and **#50** (Playwright Chromium, `fff2ea911c4a4edf04634b875c1323c111d802e1`, PR run [#39827416615](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39827416615) 4/4). Source tests were never disabled. [Post-#50 main #39827785931](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39827785931) passed 4/4.
- **L** [#43](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/43) merged `16ba6f47ef007d2ac39a6f5488bd13403ac78b2c`: ordered, offline DEV Supabase migration/security preflight, durable recovery negative SQL and rollback runbook. Exactly **four completed successful jobs** verified in PR [#39827712699](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39827712699); [post-L main #39828375693](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39828375693) passed 4/4.
- **M** [#46](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/46) merged `648dec1a01b6ba920733f1ba8d395840ad665511`: read-only Azure DEV IAM/runtime/cost/budget checks, explicitly guarded deployment and rollback preflight. [PR #39810592159 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810592159) and [post-M main #39828664342](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39828664342) passed 4/4.
- **N** [#44](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/44) merged `30efa0cba6bd279a3972176ba7174cf6e2796095`: locally measured synthetic 1080×1920 media render, resource/license/asset safeguards and estimated cost envelope, **not Azure measurements**. [PR #39810720819](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810720819) and [post-N main #39829076503](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39829076503) passed 4/4.
- **O** [#45](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/45) merged `ce5e56b8d6806f8ccc7bda5ca6aa3c0012ca61e8`: manual, approval-gated genuine DEV login/private image/campaign/day-save/render/signed-download and denial/recovery harness with offline mocked guardrail tests. [PR #39811545219 attempt 4](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39811545219) and **final combined [main #39829360425](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39829360425)** passed **4/4** (frontend Playwright, Python, FFmpeg, isolated Supabase).
- All four L/M/N/O **source PRs are merged**. Earlier “unmerged/CI blocked” sections are historical snapshots only. Coordinator docs PR #49 records this final verified checkpoint. No Azure provisioning/deployment, hosted Supabase migration, genuine hosted E2E, licensed-media publishing, or WineShopPOS changes were performed. See `docs/DEV_DEPLOYMENT_APPROVAL.md`: **three separate owner approvals remain pending**.

## 2026-10-22 — Coordinator 3 P/Q/R release-preparation handoff (NO hosted deployment)
- Independently verified `main` `fa64eb38b4e016c42852fea9cd30413ca9d4b666` after final L/M/N/O documentation and 4/4 successful [main CI #39830444332](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39830444332): frontend/Playwright, Python/uv/infrastructure, full synthetic FFmpeg, disposable Supabase security.
- Three parallel branches already exist at this verified base: **P** `feat/p1-dev-migration-execution`, **Q** `feat/p1-azure-deployment-execution`, and **R** `feat/p1-frontend-static-preview`. At coordinator kickoff their heads were still identical to `main` and **no P/Q/R PR was open**. Worker implementation, test outcomes, and merges must be verified later; do not claim they are complete.
- Prioritize integrating **R first** so owner can request a **frontend-only** Azure Static Web Apps DEV demonstration. It will display clearly labeled local mock campaign content on `/`, `/campaigns` and `/account` with SPA fallback, without needing Azure Functions or hosted Supabase. An actual public HTTPS URL **does not exist until owner-approved SWA creation and deployment succeeds**; no URL is invented.
- Four separate approval requests are [frontend-only SWA #51](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/51), [hosted DEV migrations #52](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/52), [Azure backend DEV #53](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/53), and [hosted real E2E #54](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/54); all **PENDING**. See `docs/DEV_RELEASE_APPROVAL_REQUESTS.md`. No hosted Azure/Supabase change or WineShopPOS modification has been authorized.
