# Next Development Task

## Current phase — Part 1 integration, not production launch (2026-10-22)

Coordinator merged Workstream A PR #5, stacked coordinator PR #6, Workstream B PR #3, Workstream C PR #2 and Workstream D PR #4, in dependency order. PR #4 required explicit root App.jsx reconciliation preserving both AuthProvider/AccountWorkspace and CampaignDashboard. See docs/PROJECT_STATE.md and docs/WORK_LOG.md.

## Verified and committed work
- React/Vite routes: `/account` uses configurable RetailGrowthAI Auth and business onboarding; `/campaigns` is an interactive seven-day **mock** editor with local draft exports.
- Supabase migration-led tenant schema, private media, OWNER/EDITOR/VIEWER roles and negative cross-shop RLS/storage tests.
- Dependency-free Python validated campaign planner, bounded reviewer, mocked Foundry adapter and **non-deployed** CampaignService service boundary.
- Offline FFmpeg renderer (30-second, 1080x1920, H.264/AAC, multiple images/transitions/overlays), test media rights metadata and negative tests.
- Four CI jobs: frontend tests/build, Python fixture/planner/API tests plus offline B-to-C interface tests, 30-second synthetic video rendering, disposable Supabase tenant isolation.
- PR #4 reconciled branch passed all four jobs in [Actions #39755166150](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39755166150). Inspect the **latest main** CI run before marking final integration green.

## Next unfinished work — priority order
1. **Secure API adapters (highest priority):** deploy a RetailGrowthAI-only Azure Functions HTTP API implementing INTERFACES_V1 POST/GET endpoints with cryptographically verified Supabase Auth JWTs; server-side active shop membership checks; real per-tenant media authorization; RLS-aware durable persistence. B's `service.py` is not an HTTP server.
2. **Durable jobs and render integration:** build real queue/worker orchestration for planning and rendering; ensure idempotency, retry limits, state transitions, usage accounting, review/approval checks, asset rights verification and signed private output downloads. Never accept a browser-asserted license or local path as authorization.
3. **Frontend connected flows:** configure *only* `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in the RetailGrowthAI environment. With authenticated shop selection, wire CampaignDashboard brief submission, job polling, draft save/edit, authorized media uploads and verified download/render controls. Keep mock-mode honesty until live flows pass.
4. **Release-level verification:** browser signup/login/password expiry/session refresh, onboarding and profile updates, denial of cross-tenant API calls, full end-to-end prompt -> seven drafts -> authorized 30s output, negative paths, external media licensing/attribution, accessibility, performance and cost benchmark.
5. **Reproducibility/deployment:** commit reviewed `frontend/package-lock.json` using Git Bash (CI uses npm install until then), configure isolated RetailGrowthAI DEV/PROD cloud resources only under explicit deployment work, Azure AI Foundry adapter/credentials, and separate production Supabase project when launch is approved.

## Not in current scope
- No platform publishing/OAuth (Part 2), no Wan integration (Part 3), and no claim of production readiness (Part 4).
- Never use or modify WineShopPOS resources.
- Keep INTERFACES_V1.md stable; change only via coordinator-reviewed contract revision.

## Secure HTTP API milestone handoff
- Add durable queue + worker + retry/idempotent database operations before enabling POST. No accepted campaign may be silently dropped.
- Then expose renderer jobs and signed media downloads; wire React only with authenticated non-mock campaign data.
- Review and test HTTP boundary with real Azure Functions host locally; this milestone has tests but no cloud deployment.

## After durable planning code
- Review migration and apply to isolated RetailGrowthAI DEV only after explicit deployment authorization. Provision/configure an Azure Queue only after approval, then verify queue poison/retry and seeded load tests.
- Add tenant-safe render jobs, a verified media staging worker and signed downloads. Connect React to deployed endpoints only after auth/asset live E2E.

## Render API follow-up
- Implement real Azure Queue-triggered renderer with atomic job claims, securely staged licensed media and bounded uploads. Do not enable render UX until that worker and browser-to-API tests pass.

## Render worker follow-up
- Review/apply latest render claim migration to dedicated DEV only after deployment approval; configure existing Azure queue and worker secrets, test with licensed images/music and real Auth sign/download. Add bounded worker observability/cleanup.

## After frontend wiring
- Set VITE_CAMPAIGN_API_BASE_URL and RetailGrowthAI-only Supabase publishable settings on an approved deployment; verify browser E2E and CORS. Media upload UI, remote edit/save, production licensing and post approval remain separate work.

- Verify post-merge four-job CI and complete live Auth/queue/render/browser testing before deployment. Fix any orphaned queued jobs with monitored recovery; do not grant user UPDATE on campaigns.status.


## Next implementation blockers after PR #7–#13 (approval-gated)
1. Review and apply durable planning + rendering migrations to **RetailGrowthAI-only DEV** (never WineShopPOS); verify DB advisors and RPC permissions.
2. Provision/configure approved Azure Functions app and two Storage queues, using backend-only secrets and packaging `ai_agents` + `video-engine`. Test Azure Functions host locally and in isolated DEV before enabling frontend.
3. Set HTTPS API origin and Supabase publishable values for RetailGrowthAI; test real sign-in, per-tenant uploads/rights and CORS.
4. Add live save/edit draft API, uploads with licensing, verified final downloads, poison/recovery reconciliation, cost/lease limits and browser E2E.
5. Commit reviewed npm lockfile, implement production Foundry provider, create separate PROD only with approval. Publishing remains Part 2; Wan Part 3.

## Following the draft-save API milestone (code, not deployed)
1. Verify the new draft-save SQL/Python/CI changes on a feature PR and merge only after all four jobs pass; confirm post-merge main CI.
2. Wire a live-only **Save day** UI action using PATCH and its returned persisted day; preserve demo mode, unsaved-change protection and render gating.
3. Build a proper media registration/upload path with verified license provenance and private-object authorization, plus negative tenant tests; do not trust user-declared licensing alone.
4. After explicit approval, apply RetailGrowthAI-only pending migrations and deploy isolated DEV API/queues; verify Supabase Auth, JWT, uploads, worker retries, download and browser E2E. No PROD yet.

## After live Save day wiring
- Merge draft-save backend PR before stacked React Save UI PR; verify all 4 jobs on both and on main.
- Approve and apply RetailGrowthAI-only migrations to isolated DEV, then test an actual signed-in browser Save/PATCH/GET round trip and cross-tenant denial. Source-only CI cannot prove this.
- Next: private, licensed media upload/registration; app/queue deployment after approval; real media render/download, poison recovery and end-to-end QA.

## After private-media upload code
1. Merge the private image-upload migration/UI PR only after all four jobs pass, then verify post-merge main.
2. Obtain approval to apply all new RetailGrowthAI-only pending migrations to isolated DEV. The uploader stays nonoperational on cloud until the registration RPC is present.
3. Real signed-in browser upload -> media row -> campaign planning -> saved edit -> render -> download E2E with actual licensed media; verify file content, CORS, 25 MB bounds and cross-tenant denial. Human rights evidence review required before commercial publishing.
4. Add bounded abandoned-private-upload cleanup, media deletion/revocation safety, licensed audio/stock ingestion, worker recovery/poison monitoring and cost benchmarking. Deploy Functions/storage queues and Foundry only after explicit approval.

## Current next steps after merged PR #16 (supersedes earlier feature-branch handoffs)
1. Verify the final post-merge four-job Actions run on main; fix any failures using a small PR. Keep the tenant/security tests enabled.
2. **Approval required:** apply pending migrations (durable planning, render claim, draft save, private upload registration) to **existing RetailGrowthAI DEV only** after review and backup; do not create a new project or touch WineShopPOS.
3. **Approval required:** configure and deploy isolated RetailGrowthAI Azure Functions and two existing/approved queues, package worker dependencies and licensed FFmpeg assets; configure frontend HTTPS API origin and Supabase publishable key without revealing backend secrets.
4. Verify a real browser flow: authenticated login -> private upload -> registered media -> 7-day campaign -> saved day edit -> 30-second rendered MP4 -> signed download. Test cross-shop/VIEWER denials and broken uploads.
5. Before a production claim: independent third-party licensing review, orphan-storage cleanup, media revocation, retry/poison reconciliation, rendering budget and latency benchmark, accessibility and security review. No publishing/Wan/PROD deployment now.

## Current coordinator priorities after E/F/G/H merges (2026-10-22)
1. **Validate latest main with the expanded four-job CI** ([run #39775525458](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39775525458)); do not count a superseded/cancelled intermediate run as passing. Fix Playwright, Python reliability/API journey, isolated SQL or Azure packaging/Bicep test failures in small reviewable PRs without disabling checks.
2. **Hard pre-deployment blocker:** reconcile FFmpeg 780-second subprocess cap against the 4-minute Functions host timeout and database claim lease; benchmark 1080x1920 in the target resource profile, and choose appropriately bounded host/lease renewal or approved Container Apps Jobs. Review Flex Consumption Bicep and packaging, verify approved binary licenses and cost ceilings.
3. **Not implemented live:** coordinator-owned durable replay/outbox compare-and-swap and terminal-state recording, Azure planning/render poison handlers, lease reconciliation, bounded alerting, conditional ETag storage deletion with registration fencing, cleanup quota and audit. H contains only offline planning primitives.
4. **Explicit user approval required:** back up and sequentially apply five pending migrations to the **existing RetailGrowthAI DEV** project only, verify RLS/Storage API-level mutation denials; then authorize separate Azure DEV configuration/deployment when blockers resolved. Do not touch WineShopPOS/PROD.
5. **Real end-to-end release gate:** signed-in browser + actual private photo upload/registration -> seven-day campaign -> saved edit -> licensed 30s FFmpeg output -> secure download; test expired JWT, membership revocation and tenant leakage with hosted DEV. Perform independent commercial rights verification, production provider integration, cost and accessibility checks. Mock E2E passing is not real hosted E2E.

## Azure OIDC GitHub verification handoff (2026-10-22)
1. In RetailGrowthAI GitHub Settings create environment `dev`, restrict to `main`, and add `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` as **environment** secrets; see `docs/AZURE_GITHUB_OIDC.md` for details.
2. In the dedicated Entra app `retailgrowthai-github-dev` add the documented immutable-subject GitHub OIDC federated credential. Assign only **Reader** on an isolated RetailGrowthAI DEV resource group for authentication verification. Do not grant subscription-wide Contributor/Owner or connect WineShopPOS.
3. On approved `main`, manually run `Azure DEV OIDC connection check (read-only)` and capture its real result; the four standard CI jobs cannot prove Azure authentication. No deployment, migrations, cost-bearing resource creation or runtime configuration is authorized by this task.

## Next after worker execution-budget PR (2026-10-22)
1. Verify **four green PR checks**, merge only after review, and verify **post-merge main** separately. New `20261022205000_p1_worker_execution_budget.sql` is **NOT applied to DEV** without explicit owner authorization.
2. **Still blocking deployment:** design and test transactional outbox/replay, durable poison acknowledgements, stale-job terminalization, and attempt/lease fencing on planning/render completion/failure. Current CI tests are offline and do not prove Azure Queue crash recovery.
3. Benchmark actual licensed 1080x1920 render and tenant-private download/upload time within the 20-minute host budget on an approved Flex DEV target; verify Flex runtime/Bicep and FFmpeg binary packaging. The 780-second subprocess leaves 7 minutes for other worker phases; 25-minute lease exceeds host timeout by 5 minutes. Absent evidence, do **not** deploy.
4. Hosted Supabase migrations, Azure DEV infrastructure and live authenticated E2E remain separately **approval-gated**. Azure OIDC read-only workflow must pass independently; it is not deployment approval.

## Active next task after merged coordinator PR #28 (2026-10-22)
- **Verified:** merged source-only worker execution budget in [PR #28](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/28); [post-merge main run #39781848452](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39781848452) passed 4/4 jobs. Five earlier pending migrations plus new worker-budget migration remain **UNAPPLIED** to hosted RetailGrowthAI DEV.
- **Next development PR:** durable transactional outbox/requeue and poison-event handling with compare-and-swap claim-attempt fencing; ensure crashed/in-flight/stale/duplicate jobs cannot be ACKed, overwritten, replayed or left forever in nonterminal states. Test queue retry exhaustion and DB-write failures offline before any hosted integration.
- **Azure OIDC verified (read-only):** the latest attempt of [Azure DEV OIDC workflow run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) succeeded for federated login and subscription identity checks, superseding the initial `AADSTS70025` failure. Verify precise DEV resource-group IAM separately. No Contributor/deploy privileges, migration application or Azure deployment are implied.
- **Still approval-gated:** hosted Supabase migrations, Azure Functions/queues, 1080p performance/cost testing with licensed assets and real authenticated browser E2E. Do not modify WineShopPOS.

## Active Coordinator 1 I/J/K integration queue (2026-10-22)
1. **Done:** review and merge OIDC documentation PR #30 (`7c6c506a`) after all four branch CI checks passed. [Post-merge main run #39790938647](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39790938647) **passed all four jobs**.
2. **Await PR I:** review durable queue transactional outbox, replay, poison acknowledgements, stale-job terminalization, claim/attempt fencing, negative RLS and fault-injection. Fail if changes break tenant invariants or apply hosted SQL. Require 4/4 PR and main CI, then merge.
3. **Await PR J:** validate Azure DEV-only Flex/Bicep/FFmpeg source packaging, quota and cost safety against merged I and migration/lease constraints. No provisioning/deployment. Require 4/4 PR and main CI, then merge.
4. **Await PR K:** validate mocked API and Chromium browser suites cover authentication expiry/revocation, cross-tenant denial, upload, generate, save, render and download plus error recovery. Do not claim real hosted E2E. Require 4/4 PR and main CI, then merge.
5. Coordinator-owned integration fixes in small PRs only; update all four canonical handoff docs on completed integration, preserving exact run/merge evidence. Real Supabase migrations and Azure deployment are separately approval-gated; WineShopPOS is out of scope.

## After I/J/K merge — next release gates (2026-10-22)
- **Source integration done:** I #34 durable outbox/fenced recovery, J #33 Flex/FFmpeg deployment safeguards, K #31 offline E2E denial/retry coverage are now on `main` (SHAs in `PROJECT_STATE.md`). Combined [post-K main run #39801130265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39801130265) independently **passed all four jobs**. Confirm the final documentation PR and post-doc-merge CI separately.
- **Next technical gates:** (1) independently validate Azure **Contributor scope** specifically on RetailGrowthAI DEV resource group (owner reports grant; not independently enumerated), keep other subscriptions and WineShopPOS out; (2) with explicit owner approval only, apply every pending DEV SQL migration in order with rollback/backup, check migration + RLS under real hosted identities; (3) with separate deployment approval only, provision isolated Central India DEV Functions/queues/Storage and verify host indexing, timer/poison behavior and queue encoding; (4) inspect actual FFmpeg third-party licenses, codec/font behavior, memory/scratch and 1080p 30-second CPU/time and cost, with alerts and quotas; (5) test hosted JWT tenant isolation, real uploads, generation, save, render, signed MP4 download, expiry, poison replay and idempotent failure recovery end-to-end.
- **Release remains blocked** without these hosted checks and approvals. No social integrations (Part 2), Wan video (Part 3), billing/production launch, or production permissions until separately scoped. Never deploy or apply migrations implicitly; never alter WineShopPOS.

## Coordinator 3 — next parallel workstreams L/M/N/O (2026-10-22)
Baseline: `main` `84c9b87`, [latest completed 4/4 main CI #39805920327](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39805920327), zero workstream L/M/N/O PRs at assignment (the coordinator documentation PR #38 is separately open). I/J/K are complete and merged; do not duplicate.
1. **L — migration/RLS deployment rehearsal** (`feat/p1-dev-db-release-readiness`): inventory and order seven reported unapplied migration scripts, exercise disposable DB upgrade/negative RLS/idempotency/backup-and-rollback rehearsal, produce non-destructive hosted DEV runbook. No hosted `supabase db push`, SQL apply or secret exposure.
2. **M — Azure DEV least-privilege preflight** (`feat/p1-azure-release-readiness`): source-only read-only RG role-scope validation, deployment plan output, rollback/cost/budget verification and gate-fail tests, with NO Azure resource writes and NO unattended deployment.
3. **N — render licensing/performance qualification** (`feat/p1-render-performance`): audit FFmpeg/ffprobe and assets license evidence, deterministic offline 1080x1920 benchmark with measured CPU/memory/scratch/runtime, cost-envelope thresholds and encoded-media assertions. Synthetic/stock inputs must not be described as commercially cleared.
4. **O — gated hosted smoke harness** (`feat/p1-hosted-e2e-readiness`): independently opt-in/approval-gated real-DEV authenticated browser/API smoke harness, clean tenant fixture/teardown and negative isolation/expiry/recovery case definitions; normal CI must remain offline, existing K mocks should not be duplicated, and NO hosted smoke run may execute before approval.
5. **Coordinator 3 only:** maintain contracts/shared docs/`.github/workflows/**`, review L/M/N/O PRs, merge in L → M → N → O order unless actual dependency dictates otherwise; require four successful checks for each PR and post-merge `main`, updating all continuity docs with actual run numbers. Fix failures in separate coordinator-owned PRs; do not silence tests.
6. **Release boundary:** use `docs/DEV_DEPLOYMENT_APPROVAL.md`. Owner approval for hosted SQL, Azure provision/deploy and hosted browser smoke are **three independent explicit decisions**, none implied by prior OIDC login, GitHub permissions or these assignments.

## Coordinator 3 active blocker and exact continuation — 2026-10-22
- **Do not confuse completed branch implementation with integration:** open workstream PRs L #43, M #46, N #44, O #45; CI correction #47. Coordinator docs/CI PR #38 merged to main `2ca338ab`; post-merge `main` [#39810509471](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810509471) failed FFmpeg apt mirror timeout.
- **Immediate priority:** GitHub Actions service incident on 2026-10-22 also produced instant four-job failures without any started runner/steps on CI repair [#39812135974](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39812135974) and O [#39811545219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39811545219). Recheck public GitHub Status, runner provisioning and GitHub Actions quota/billing if problem persists; do not disable testing, weaken repository protections or misreport these as code test failures. Re-run/repair #47 and require 4/4 success before merge, then verify post-merge **main 4/4** independently.
- **Next merges only with verified evidence:** review/finalize L #43 (the coordinator workflow already discovers Node and SQL negative tests; avoid duplicate invocations), M #46 (scoped IAM and rollback checks), N #44 (media safety and measured offline cost evidence), O #45 (guard hosted test execution; offline suite only in CI). Merge sequentially and independently verify all four main checks after **each** merge; if CI runners fail, pause rather than skipping gates.
- After integrations, append actual PR numbers, merge SHAs and run URLs to PROJECT_STATE/WORK_LOG/DECISIONS and prepare a separate DEV rollout go/no-go. Approval gates 1 hosted Supabase migration, 2 Azure deployment/provisioning and 3 real hosted DEV E2E are **all pending**. No deployment, migration, hosted smoke or WineShopPOS modifications.

## Coordinator 3 updated recovery checkpoint (2026-10-22, following GitHub Actions retries)
1. **External blocker:** official GitHub Status still reported degraded Actions/PR service. Repeated PR #47 runnerless attempts through #39812135974 attempt 5 and L PR #43 runnerless attempts through #39815674157 attempt 2 ended as GitHub failures without job steps. Stop re-running in a tight loop; require actual runner assignment and executed steps when service recovers. These do not meet 4/4.
2. Verify #47's FFmpeg mirror+file apt fix with four executed successful jobs on its current exact head; merge it first and independently verify four **post-merge main** jobs. Repair any true test failure without skipping it.
3. Then verify and integrate L #43 current head `bb240294` (independent SQL/Node negative tests), M #46 current head `7a9c889f` (Azure read-only gates), N #44 current head `3d0dd2b0` (measured local 1080p synthetic renderer), O #45 current head `66b42961` (hosted smoke remains opt-in). Confirm four jobs executed and succeeded on the updated PR and after every merge. PR #49 is a dated blocked-state docs checkpoint; reconcile its text with actual merged SHAs before merging rather than publishing stale NOT MERGED statements.
4. Only after verified source integration: seek **three separate explicit owner approvals** for hosted DEV Supabase migrations, Azure DEV provision/deploy, and real hosted DEV E2E. No cloud work and no WineShopPOS access before consent.

## ACTIVE NEXT WORK — after all four L/M/N/O source merges (2026-10-22)
- **Source integration and CI issues resolved**: #47, #50, L #43, M #46, N #44 and O #45 are merged. The final combined `main` [run #39829360425](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39829360425) passed all four jobs on `ce5e56b8d6806f8ccc7bda5ca6aa3c0012ca61e8`. Older sections asking to retry/merge these PRs describe the historical blocked stage and are **not** current work.
- **Release gate 1 — DEV Supabase SQL**: owner must independently approve the exact pending seven migrations after verifying ordered history, transaction/backup/rollback compatibility, service role/RLS/storage isolation and L's negative preflight. **Do not execute hosted migrations yet.**
- **Release gate 2 — Azure DEV resources/deploy**: separately approve target Central India RG scoped Contributor IAM after M's **read-only** verification, cost ceiling and budget alerts, Flex/queue/poison/timer indexing, FFmpeg packaging/license/runtime measurements and verified rollback bundle. GitHub OIDC success and public CI do **not** authorize provisioning/deployment.
- **Release gate 3 — real hosted DEV E2E**: only after the above two approved deployments, obtain a **third explicit approval** for O's actual password logins, commercial-rights-attested private image upload, tenant-denial/expired JWT, remote draft save, 30-second MP4 signed download and operator-controlled retry/poison fault injection. Use only RetailGrowthAI DEV and audited cleanup; never use PROD or WineShopPOS.
- Cross-check the [DEV approval checklist](DEV_DEPLOYMENT_APPROVAL.md) and `supabase/DEV_RELEASE_READINESS.md`, `infra/azure/RELEASE_READINESS.md`, and `tests/e2e/HOSTED_DEV_RUNBOOK.md`. Keep all branch workflow secrets protected; the owner made the repository **public** for unlimited standard hosted-runner Actions and historical code/logs are exposed. Never commit credentials. Parts 2 (social OAuth/publishing), 3 (Wan) and production launch remain out of scope until separate milestones.

## Coordinator 3 — active P/Q/R parallel integration (2026-10-22; source only)
- **Prioritize R**: review `feat/p1-frontend-static-preview` PR as soon as submitted; verify `frontend`→`dist` static output, immutable `index.html` SPA fallback, offline navigation of `/`, `/campaigns`, `/account`, explicit demo/mock mode with no backend settings, and absence of secrets/privileged deployment tokens. Coordinator owns shared Actions edits. Require **4/4 PR CI**, merge R, independently require **4/4 post-merge main CI**. Owner may then separately approve frontend-only Azure Static Web Apps DEV site creation/deployment; no site/public URL is claimed before a real approved rollout.
- **P**: `feat/p1-dev-migration-execution` owns `supabase/**` and `tests/security/**`; review live history *read-only*, backup/restore rehearsal, exact seven unapplied ordered migrations, negative RLS/storage and rollback runbook. Do not execute hosted SQL. Require 4/4 PR + post-merge main.
- **Q**: `feat/p1-azure-deployment-execution` owns `infra/azure/**`, `scripts/deploy/**`, `tests/infra/**`; review least-privilege RG IAM (read-only), Flex/queue/poison/timer, FFmpeg licenses/binary/package, budgets, preflight/rollback. Do not provision or publish Azure. Require 4/4 PR + post-merge main.
- Merge plan **R → P → Q** where reviewed dependencies allow, with disjoint file ownership and no incompatible Interfaces v1 changes; fix cross-stream issues in separate coordinator PRs, not by bypassing tests. Every merge must have exact latest PR SHA, review of changed files, four green PR checks, independent four green main checks, and canonical doc updates.
- **Four explicit approval requests—all pending, mutually independent:** frontend-only SWA #51; hosted Supabase DEV migration #52; Azure backend/Storage/Functions DEV #53; real hosted E2E #54. Details and prerequisites in `docs/DEV_RELEASE_APPROVAL_REQUESTS.md` and `docs/DEV_DEPLOYMENT_APPROVAL.md`. Do not execute any action without a separate user go/no-go for that exact scope and cost ceiling; no PROD or WineShopPOS changes.

## ACTIVE NEXT TASK — P/Q/R source integration verified (2026-10-22)
- **SOURCE/CI COMPLETE**: #55 coordinator gates, #58 manual Static Web Apps workflow, P #56, R #59 and Q #57 are merged. Final main source commit **28cd7a6c528ba4df287d3ac125017f696bff7ab3**, [post-Q CI #39835674846 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39835674846) **four successful executed jobs**. P/R/Q integration instructions appearing above are historical checkpoints and not currently unfinished work. Latest main after this documentation merge must separately pass 4/4.
- **FIRST owner decision: Gate A / approval issue #51** — frontend-only Azure Static Web Apps preview. R's Vite mock routes /, /campaigns, /account, dist SPA fallback and protected manual SWA workflow are source-ready. Before asking for owner go/no-go, determine actual isolated DEV subscription/resource group/site/region/hosting plan, alert/cost cap, environment restrictions and rollback. The frontend-only demo may be deployed **only after** explicit Gate A approval. No URL exists or may be claimed before confirmed HTTPS deployment.
- **SECOND separate decision: Gate B / issue #52** — hosted DEV Supabase seven ordered migration scripts, only after fresh read-only project history, backup/restore rehearsal, operator/change window/rollback and explicit approval. Never run hosted migration from PR CI.
- **THIRD separate decision: Gate C / issue #53** — Azure DEV Functions/Flex/queues/FFmpeg backend, only after Q source release package, exact resource-group IAM scope, approved cost budget, physical queue/poison indexing plan, licenses/limits, rollback, prior approved database schema and explicit backend rollout approval.
- **FOURTH separate decision: Gate D / issue #54** — hosted DEV identity/tenant isolation/upload/plan/save/render/download/recovery test, only after deployment prerequisites and its own explicit owner approval, licensed real test assets and bounded test costs.
- See [DEV_RELEASE_APPROVAL_REQUESTS.md](DEV_RELEASE_APPROVAL_REQUESTS.md) and [DEV_DEPLOYMENT_APPROVAL.md](DEV_DEPLOYMENT_APPROVAL.md). Do not provision cloud, deploy SWA, apply hosted migrations, execute hosted E2E, expose secrets or modify WineShopPOS merely because source and CI are ready.
