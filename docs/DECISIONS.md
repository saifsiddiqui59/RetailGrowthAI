# Architecture Decisions

- Use Git Bash and VS Code.
- Use an independent GitHub repository.
- Reuse selected WineShopPOS patterns.
- Never share WineShopPOS production data or secrets.
- Supabase for Auth, PostgreSQL and RLS.
- Azure Functions for application APIs.
- Azure AI Foundry for AI generation.
- LangGraph only where agent orchestration adds value.
- uv for Python and npm for JavaScript.
- Stock footage plus FFmpeg before premium AI video.
- Postiz excluded.
- Razorpay excluded.
- Platform integrations deferred to Part 2.
- Wan integration deferred to Part 3.
- Maintain strong tenant isolation from the beginning.

## 2026-10-22 — Architecture for parallel Part 1
- Keep four product parts, but parallelize four independent Part 1 coding workstreams under coordinator-owned contracts.
- Use Python + uv for campaign API and agent package, and npm/React for the frontend; borrow WineShopPOS security and UI patterns but never copy credentials or POS-specific tools.
- Protect contracts in docs/INTERFACES_V1.md and branch ownership in docs/PARALLEL_WORK.md. No worker chat merges to main.
- Use async campaign planning and video rendering; return job IDs and poll, rather than block browser HTTP calls while FFmpeg runs.
- Render initial 30-second 1080x1920 H.264/AAC Reel locally with FFmpeg; choose Azure video worker hosting only after benchmarking.
- Store uploaded content as private media with tenant authorization, track usage and rights metadata, and treat regulatory content as review-gated.
- This is an architecture decision and documentation update only, not an implemented/deployed feature.

## 2026-10-22 — Minimal coordinator frontend bootstrap
- Keep the shared v1 mock campaign as a normalized GET /api/campaigns response under frontend/src/features/campaigns/fixtures/ with exactly seven distinct sequential days and contiguous 30-second storyboards; UUIDs are synthetic, not real media references.
- Coordinator owns the root React Router shell and Vite dependencies. Feature D owns the eventual campaign UI within its designated directory; Feature A owns the auth implementation.
- Pin direct frontend dependency versions. Because npm registry access is not available in the coordinator sandbox, use GitHub Actions for independent install, contract and build verification; generate and review the lockfile before adopting npm ci. Do not mistake static validation for a successful Vite build.

## 2026-10-22 — GitHub Actions as iterative development test runner
- Use one existing workflow path (.github/workflows/frontend-bootstrap.yml) with frontend, Python/uv and FFmpeg CI jobs; avoid duplicating frontend runners.
- Trigger on main/feature branch pushes and main-targeted PRs. Use read-only workflow token, no secrets on PRs and no cloud provisioning. Cancel superseded runs to limit billed minutes.
- Require each workstream to record actual CI run evidence before requesting coordinator merge. ChatGPT may inspect failures and push fixes during an active chat, but GitHub Actions does not autonomously write fixes.
- Real 30-second renderer validation is owned by Workstream C; synthetic two-second FFmpeg check only confirms codecs and tool installation. See docs/CI_AUTOMATION.md.

## 2026-10-22 — Approved Part 1 CI integration (PR #1)
- Merge the read-only, secret-free three-job CI workflow; post-merge run #39745758948 passed all three checks. Workstream chats must provide passing PR-run evidence; the coordinator validates integration on main.
- A two-second synthetic video test only confirms FFmpeg H.264/AAC toolchain; separate 30-second renderer, RLS denial, and AI behavior tests are mandatory in workstream PRs. A green scaffold check is not production readiness.
- After coordinator documentation updates, fast-forward the four unchanged feature branches to the same latest main commit before parallel work. Preserve branch ownership and contracts.

## 2026-10-22 — Coordinator Auth route and reusable security gate
- Keep Workstream A schema/Auth implementation in PR #5; coordinator owns root router and shared CI changes in a separate stacked branch rather than breaking parallel file ownership.
- Wrap root app with Workstream A AuthProvider, mount AccountWorkspace only under `/account`, and continue labeling campaign data as mock. Live Auth depends on RetailGrowthAI-only VITE publishable settings; never ship service-role or secret keys.
- Add an independent read-only GitHub Actions security job: Node client tests plus disposable Supabase Postgres and migrations followed by negative SQL tests. No hosted Supabase database or credential is used in CI; do not weaken tests for green status.
- Dedicated RetailGrowthAI Supabase project `jeearzffnjbvghwjjjrf` is DEV/pilot only; production requires a separate project. No changes to WineShopPOS or existing voice projects.


## 2026-10-22 — Workstream integration and truthful runtime boundaries
- Integrate A PR #5 before stacked coordinator PR #6, then B PR #3, C PR #2, and D PR #4; reconcile the shared App.jsx router to retain both live-configurable AccountWorkspace and mock CampaignDashboard.
- The UI's natural-language campaign brief must remain preview-only until a real authenticated HTTP service and authorized tenant-specific media are wired. Never silently replace synthetic fixture IDs with trusted IDs or enable fake render/download controls.
- The Python CampaignService is a dependency-injected **non-deployed** API boundary, not a working Azure Function; the 30-second renderer is a tested offline CLI. A coordinator cross-component integration test validates v1 B planner -> C renderer manifest compatibility without pretending to run an online campaign.
- Four CI jobs run independently; a green CI run proves covered fixture, unit, synthetic render and disposable Supabase security checks, not browser E2E or production cloud auth. Never share WineShopPOS secrets/resources.

## 2026-10-22 — API security boundary
- Prefer project-pinned asymmetric Supabase JWKS verification, exact issuer/audience and RLS access via the end-user bearer token; reject missing secrets/unsigned or HS256 JWT without a verified migration plan.
- Keep API POST returning 503 until a persistent, acknowledged queue exists. Never present an in-memory queue or unqueued write as accepted.

- Pin FFmpeg CI runner to `ubuntu-24.04` after the rolling runner introduced FFmpeg 8 with unverified pixel-format behavior. Keep all smoke, codec, duration and content assertions enabled; verify compatibility before upgrading.

- Durable planning uses existing Supabase campaigns as atomic idempotent claim state plus Azure Storage Queue for persisted deliveries. Worker uses service role only server-side, never trusts message/asset rights and never self-provisions cloud resources.

- Signed MP4 URLs are minted only from tenant-authorized private storage via the end-user JWT (60-second expiry). Render job POST needs verified membership and licensed asset IDs; server-derived idempotency key prevents duplicate requests for identical day/reel.

- Keep renderer as bounded server-only Queue trigger consuming opaque job IDs; regenerate trusted manifest using tenant-authenticated DB rows and private media paths. Persist deterministic output key and never allow arbitrary browser-provided FFmpeg paths. Quota/lease sizing must be benchmarked before cloud deployment.

- Frontend must never send synthetic fixture asset IDs; authenticated live mode selects previously authorized per-shop media via RLS. API calls refresh the Supabase access token, reject redirects and gate signed downloads to the configured private storage origin. Unsaved edits remain local and cannot be rendered as saved server drafts.

- The campaign status column remains server-owned. Privileged cleanup is narrowly filtered by campaign, tenant, owner and status. Use opaque sb_secret_ keys only in apikey; reject unverified existing rendered objects rather than treating 409 as upload success.


## 2026-10-22 — Live UI request consistency
- The campaign request shown to a signed-in user must exactly match the authorized payload sent to the API. Only selected business/asset UUIDs from the RLS-backed UI may appear; never substitute sample fixture IDs in live requests. Missing or duplicate media blocks submission. Offline mock mode remains unchanged.

## 2026-10-22 — Draft edits through a restricted user-scoped RPC
- Require the HTTP boundary to validate complete v1 campaign output and authorized source asset IDs before accepting an edit. Only topic, LinkedIn and Instagram draft fields can change; identity/schedule/status are server-owned.
- Revoke direct authenticated UPDATE on public.campaign_days and use a PostgreSQL security-definer RPC with explicit auth.uid() and active OWNER/EDITOR membership checks, plus original-value comparison and blocked edits during queued/running renders. Do not grant service-role tokens to browsers.
- A UI preview is never evidence that a draft is saved; remote edits are enabled only after the authenticated PATCH returns committed data. DEV migration needs explicit approval, no hosted mutation in CI.

## 2026-10-22 — Bind user-uploaded media metadata to private Storage objects
- Browser may upload only PNG/JPEG/WebP bytes after declared commercial-use ownership/permission and evidence. Direct authenticated `media_assets` INSERT is revoked; a restricted server-side PostgreSQL RPC verifies the user-owned private Storage object, current shop edit membership, MIME/size/path and license fields before recording metadata.
- Upload UUID and shop ID determine the object path; neither browser-submitted paths nor browser-side license declarations alone grant access to another tenant or confirm independent copyright clearance. Storage object size/content-type remain untrusted until renderer decodes real bytes. Browser JWT/publishable key only; service keys never cross into the client.
- Registration/RLS checks are automated in disposable CI. Hosted migration and actual third-party asset provenance/approval remain unverified/approval-gated.

## 2026-10-22 — E/F/G/H integration and release gates
- Merge isolated workstreams E (private media integrity), H (reliability planning), G (offline browser/API journeys), F (approval-gated Azure scaffolding), and coordinator CI integration #22 in conflict-free dependency order. Record merge SHAs in PROJECT_STATE/WORK_LOG. Their functionality is source-only until approved runtime setup.
- Keep **four** existing GitHub Actions jobs, but require reliability and offline API E2E Python tests, mocked Playwright Chromium browser tests, and Azure packaging checks whenever their paths exist. Do not claim a green run that skipped new tests or an unfinished/superseded run.
- Restrict user uploads to their canonical shop/upload UUID image path; browser cannot overwrite, rename, or delete registered assets. Registration-safe deletion is reserved for a separately audited service workflow and requires explicit approval and persistent fencing.
- Keep recovery and orphan cleanup in offline **dry-run** mode. Poison ACK, replay and actual Storage DELETE require durable compare-and-swap idempotence, audit, ETag and recheck; do not connect stubs directly to queues.
- Flex Consumption Bicep/deployment scripts are **preparation only**. Real deployment is blocked until database lease/Function timeout vs 780s FFmpeg cap is reconciled, cloud runtime and licensed binary packaging are verified, and the owner authorizes isolated DEV. Retain all user-to-tenant checks and never commit backend secrets.

## 2026-10-22 — Least-privilege GitHub-to-Azure DEV authentication baseline
- Use GitHub Actions OIDC (not a stored client secret/publishing profile) for `retailgrowthai-github-dev`; trust only the **immutable GitHub owner/repo numeric-ID** subject scoped to environment `dev`, as documented in `docs/AZURE_GITHUB_OIDC.md`.
- The verification workflow is `workflow_dispatch` on main only, has `id-token: write` solely for its verification job, performs a read-only Azure subscription identity check, and uses protected environment secrets for three Azure identifiers. Existing PR CI never receives cloud credentials.
- Assign initially only Reader on a RetailGrowthAI-specific DEV resource group. Azure provisioning/deployment and migration approval are separate actions; never inherit WineShopPOS permissions or secrets.

## 2026-10-22 — Bounded Flex execution and conservative DB claim lease
- Source configuration uses Azure **Flex Consumption** with a 20-minute `functionTimeout` for asynchronous work and a 25-minute claim lease for **both** planning and rendering; keep FFmpeg subprocess bounded at 780 seconds. This provides seven minutes for asset I/O/validation outside encoding and a five-minute lease safety margin above the host's configured timeout. Package tests reject changes that violate the exact current bounds; revise together after performance data.
- Use a **new unapplied migration** rather than modifying earlier migration history. Hosted changes require owner permission and sequential migration/backup. A host timeout is not a guarantee against cold starts, platform termination or failed status writes; no poison/replay correctness is claimed. Fail closed on cloud deployment pending durable fencing, recovery and benchmarks.

## 2026-10-22 — Verification does not lift deployment gates
- The 20m Functions / 25m database claim lease / 780s FFmpeg **source alignment** merged as PR #28 and passed four Python, frontend, FFmpeg and isolated SQL CI jobs on main (run #39781848452). Treat this as **static/offline compatibility evidence only**. Live crash recovery, poison handling, idempotent completion, replay and actual Flex media performance still block approval.
- Azure DEV OIDC login uses the exact environment-restricted federated credential. The initial attempt of [Azure DEV OIDC workflow run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) failed with `AADSTS70025`, but the **latest rerun passed** federated Azure login and read-only subscription checks. This establishes authentication only; IAM write scopes and permission to deploy/migrate are separate approval gates.

## 2026-10-22 — I/J/K dependency and authorization boundaries
- Workstream I owns persisted transactional retry/poison/attempt-fence semantics; merge before J's package/config consistency checks and K's API/browser mocked integration. Separate file ownership prevents workers from changing coordinator `docs/**` and CI workflows; semantic conflicts are reviewed in integration PRs.
- The successful third attempt of read-only Azure OIDC workflow #39780713421 verifies Azure login/subscription visibility only, not Contributor/IAM scope. Its initial `AADSTS70025` failure is historical. No explicit owner approval exists here to deploy or run hosted migrations; static CI success cannot substitute for it.

## 2026-10-22 — I/J/K integrated as approval-gated source
- Accept durable **transactional job outbox** as the internal queue dispatch source of truth: PostgreSQL INSERT triggers atomically create dispatch rows alongside authenticated jobs; service-role-only leases and CAS confirmation allow safe at-least-once Azure Queue delivery. Processing uses current job attempt and random claim token to fence final SQL effects; poisoned queue payloads are fingerprinted/deduplicated before ACK; timer reconciliation replays safely under bounded retries. These features are **source-only until new SQL migration is deliberately applied**.
- Preserve the 20-minute Functions host / 25-minute DB lease / 780-second FFmpeg configuration and DEV-only on-demand Flex memory/scale ceilings. Packaged FFmpeg/ffprobe must be approved/licensed static Linux x86_64 ELF with notices, safe executable bits/ZIP paths/size, and a fresh binary-runtime benchmark. Offline Bicep/package validation and OIDC authentication do not grant provisioning permission or prove Azure host compatibility.
- Keep mocked E2E independent from hosted infrastructure: mock JWT, fake image bytes, intercepted Supabase/API and synthetic MP4 validate UI boundary behaviors, not live auth, RLS, real videos or regulatory licensing. No v1 public HTTP contract changes. Contributor RBAC was reported by the owner, while GitHub OIDC verification itself was read-only; verify effective IAM scope before any owner-approved deployment.

## 2026-10-22 — Coordinator 3 parallel qualification split and DEV approval gate
- Freeze public Interfaces v1 and existing outbox/lease/fencing semantics during L/M/N/O. L owns migration/RLS rehearsal; M owns Azure preflight/IAM/cost scripts; N owns video media binary/license and measured performance (`ops/benchmarks/**`); O owns separately gated hosted-smoke harness within existing `tests/e2e/**` and `frontend/e2e/**` directories, without duplicating K mocks. No workstream may replace I/J/K functionality or edit the coordinator's `docs/**`, `.github/workflows/**`, shared API contracts or root app wiring.
- Keep each workstream isolated on a dedicated branch; workers submit PRs and do not merge. Coordinator integrates only after evidence-backed 4/4 PR checks and post-merge main checks; no fake cloud-pass labels. A green isolated GitHub CI is not hosted migration/Function/real FFmpeg validation.
- Split authorization into **(a) hosted Supabase DEV migration**, **(b) Azure DEV provisioning/deployment**, and **(c) live DEV smoke/data mutation**. Each needs a separately recorded owner go/no-go decision after the checklist, target identity, cost cap, exact commands, backup and rollback have been reviewed. Prior successful read-only GitHub OIDC login and reported Contributor assignment are NOT approvals. Never modify WineShopPOS.

## 2026-10-22 — CI outage handling and integration gate preservation
- A worker PR's claimed code completion is not equivalent to a verified, merged release. CI must execute all **four** required jobs rather than count job records with no runner/steps as a pass. After coordinator PR #38 the FFmpeg apt-mirror setup timed out on main; a bounded package mirror repair is proposed in #47, subject to its own complete CI.
- During the public GitHub Actions degradation on 2026-10-22, new PR attempts ended before runner assignment and without executable steps. Treat these as infrastructure verification blockers, not as passing code tests; preserve build/FFmpeg/browser/SQL validation and independent post-merge checks. Never bypass required checks to expedite L/M/N/O.
- Keep L/M/N/O changes strictly source-only and preserve three separately approval-gated hosted actions: Supabase DEV migrations, Azure DEV provision/deploy, and real hosted DEV E2E. CI and OIDC sign-in alone confer no rollout authorization.

## 2026-10-22 — Runnerless failure handling during final L/M/N/O integration
- A GitHub Actions job that is marked `failure` without assigned runner, executable steps or job logs cannot establish whether the application tests passed or failed. Likewise, earlier green checks on a prior SHA do not verify a revised PR. Retain the requirement for executed **four-of-four** PR and post-merge main jobs despite an upstream GitHub incident; do not weaken protection, fabricate results or bypass checks.
- The coordinator fixed L duplicate security-test invocation in PR #43 by removing imports already covered by the four-job coordinator CI discovery; no negative tests were disabled. Ubuntu mirror+file source repair in PR #47 is still an **unverified candidate** because latest Actions attempt 5 failed without executing steps.
- DEV approval remains segmented into independent hosted database migration, Azure deployment and genuine DEV E2E gates. All three are pending, unrelated to source CI authorization; WineShopPOS is excluded.
