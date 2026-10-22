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
- PR #16 private upload/registration merged as `6c62e514`. [Feature-PR CI #39769374328](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769374328) passed frontend, Python, FFmpeg and disposable Supabase security checks. Post-merge [main run #39769717413](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769717413) is a separate required verification.
- These are **source-code milestones only**: hosted RetailGrowthAI DEV has not received the new migrations and there is no deployed Azure API or queues, so real authenticated upload/render/browser E2E is unverified. WineShopPOS remains untouched.
