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

No generated/published campaigns exist yet; the seven-day fixture remains mock data. Workstream A's tenant schema, Auth and RLS code is in open PR #5 and is not integrated to main.
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
- Frontend runs npm install until `frontend/package-lock.json` is reviewed; Python checks currently exercise only the shared fixture contract; FFmpeg smoke checks a 2-second synthetic MP4, not a completed campaign renderer.
- Four remote Part 1 workstream branches exist; coordinator synchronizes them to the final documented baseline before worker chats begin. No live model, tenant database, cloud resources, publishing, or production render was created by this CI update.

## Coordinator auth/security integration proposal — 2026-10-22
- Branch `chore/p1-foundation-auth-ci-integration` is based on open Workstream A PR #5 (do not merge out of order).
- AuthProvider now wraps the application shell; `/account` renders AccountWorkspace (sign-in, registration, shop creation, profile editing) instead of the bootstrap placeholder. The campaign overview is still clearly mock-only.
- A fourth Actions job runs Node browser Auth client tests and starts disposable local Supabase Postgres to apply all three A migrations and execute both negative RLS/storage SQL scripts; uses no cloud credentials and cannot modify hosted resources.
- Workstream A previously verified 10 RLS-enabled tables, 25 tenant policies, four private-storage policies, and zero Supabase security advisories on the dedicated DEV/pilot project. Live tests used rollback and created no persistent test data.
- Do not interpret code/CI success as real browser login over HTTPS; VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY must be set in a RetailGrowthAI-only deployment, followed by manual functional testing. No production database/project is available yet.

- Coordinator branch verification: [Actions run 39752723276](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39752723276) **passed all four jobs**, including live-on-disposable-DB SQL negative tests and browser-client Node tests. This is branch-only CI evidence; main and the production deployment are unchanged.
