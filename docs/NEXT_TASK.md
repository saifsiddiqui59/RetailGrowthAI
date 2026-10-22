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
