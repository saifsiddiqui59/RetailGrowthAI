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
