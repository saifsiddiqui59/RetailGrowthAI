# RetailGrowthAI — Parallel Chat / Git Branch Ownership (v1)

## Principle
There are FOUR PRODUCT PARTS delivered sequentially. For speed, PART 1 has FOUR PARALLEL WORKSTREAMS after one coordinator bootstrap. Do not run all four product parts in parallel because Part 2 relies on Part 1 content assets, Part 3 on renderer adapter, and Part 4 requires integration.

## Prerequisite coordinator chat
Read AGENTS.md, docs/PROJECT_STATE.md, docs/NEXT_TASK.md, docs/DECISIONS.md, docs/WORK_LOG.md, docs/ARCHITECTURE.md and docs/INTERFACES_V1.md.
Verify remote main, create a minimal runnable frontend/package.json + Vite/React shell and a shared JSON fixture. Commit and push to main; ensure `npm install && npm run build` passes. Only then create four feature branches from that baseline.

## Parallel workstreams — disjoint ownership
A. `feat/p1-foundation` — Supabase schema/RLS/tenant auth, shop profiles and auth shell. Owns `supabase/**`, `frontend/src/auth/**`, `frontend/src/lib/supabase.js`, `tests/security/**`. Changes to frontend root/package files require coordinator request.

B. `feat/p1-campaign-ai` — deterministic schemas, seven-day planner, LinkedIn copy, Instagram caption/storyboard and AI reviewer; Foundry provider adapter and Python API scaffold. Owns `ai-agents/**`, `azure-functions/campaign-api/**`, `tests/ai/**`.

C. `feat/p1-video` — standalone FFmpeg render engine for multi-image 30-second 1080x1920 MP4, music, safe title/discount/CTA overlays, optional banner. Must generate a test MP4 with fixture inputs, documenting input licenses/rights. Owns `video-engine/**`, `tests/media/**`. Do not edit global dependencies.

D. `feat/p1-campaign-ui` — responsive campaign prompt form, seven-day calendar, LinkedIn text editor, Reel storyboard preview, render status, downloads using v1 mock fixtures then API. Owns `frontend/src/features/campaigns/**`, `tests/frontend/**`. Coordinator owns root app router/nav integrations.

Coordinator/Integrator alone owns `docs/**`, `AGENTS.md`, `README.md`, `frontend/package.json`, `frontend/src/main.jsx`, `frontend/src/App.jsx`, `frontend/src/config/**`, shared contracts and release branches. Workstreams may propose, not silently modify, these files.

## Concurrency rules
- Each chat reads all canonical docs first. Create or use its OWN feature branch; never commit directly to main.
- One workstream cannot edit another's directories.
- Record unresolved interface assumptions in its own `<workstream>/HANDOFF.md` (within owned path).
- Use fixtures and local tests. Tests may be marked unverified when not executed; do not fabricate test evidence.
- Push to branch and open a pull request to main. Do NOT self-merge. Coordinator reviews, tests, resolves dependencies and merges in sequence.
- For local work, use one distinct Git worktree/directory per feature branch; NEVER have four chats alter the same E:/RetailGrowthAI worktree.
- Main is updated only by coordinator after tested integration. Worker chat should not call `scripts/checkpoint.sh` if it would stage unrelated work or push to main.
- Limit service credentials, tokens, pricing and production identifiers in logs or commits.
- Contract change: stop, propose to coordinator and wait for contract-version change before implementing incompatible assumptions.

## Integration order
1. Freeze architecture/contracts and bootstrap shell.
2. Workstreams A/B/C/D in parallel.
3. Integrate A's RLS/auth, then B structured campaign generation, then D UI to API and C renderer; can vary based on test readiness.
4. Verify end-to-end one prompt -> seven days -> seven LinkedIn drafts -> seven Instagram reels with asset tracking/download. Include denial tests, cost bound, job retry/idempotency.
5. Update PROJECT_STATE, NEXT_TASK, DECISIONS, WORK_LOG and release evidence.
