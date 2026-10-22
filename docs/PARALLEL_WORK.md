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

## Active parallel workstreams I / J / K — 2026-10-22
The original A-D ownership above remains historical. For the current source-only Part 1 hardening sprint, branch heads were initially seeded from `3d4495c3`. All future PRs must target the latest `main`; worker branches should update from `main` before final CI if their code depends on later merges.

- **I — `feat/p1-durable-recovery`**: own `azure-functions/campaign-api/**`, related NEW `supabase/migrations/**`, and `tests/reliability/**` plus directly relevant backend tests. Transactional outbox, replay, poison handling, stale-job reconciliation and attempt/lease-fenced terminal writes. Do NOT apply hosted SQL or use live cloud queues.
- **J — `feat/p1-azure-dev-readiness`**: own `infra/azure/**`, `scripts/deploy/**` and infrastructure tests. Validate Python Flex app package, approved FFmpeg binary/notice compatibility, 20m host/25m lease assumptions, quotas and low-cost DEV-only guardrails. Do NOT provision or deploy Azure.
- **K — `feat/p1-integration-e2e-hardening`**: own `tests/e2e/**` and `frontend/e2e/**`. Expand mocked HTTP/browser coverage for authentication, revoked memberships, tenant isolation, authorized uploads, campaign/draft/render/downloads, expired JWT and failures. Hosted E2E remains approval-gated.

**Integration dependency:** review/merge I first (DB/worker semantics), then J (package/runtime verification against I), then K (tests reflecting integrated behavior); handle cross-workstream failures only with small coordinator PRs. Verify four required GitHub Actions checks on each feature PR and every post-merge `main`. Coordinator alone owns `docs/**`, shared interfaces and `.github/workflows/**`. Do not silently update API contracts. No WineShopPOS changes.

## I / J / K integration completion — 2026-10-22
- **I merged** [#34](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/34), backend outbox/poison/claim fencing, latest PR CI success; new SQL migration remains unapplied.
- **J merged** [#33](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/33), Azure Flex source preparation, package/cost checks, branch CI success; no Azure provisioning.
- **K merged** [#31](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/31), offline mock browser/API denial/recovery suite, PR CI success; no real hosted E2E.
- Coordinator integrated in I → J → K order. No remaining worker PR integration is implied. Final combined main CI [#39801130265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39801130265) passed 4/4. DEV deployment/migration authorization remains a separate gate, tracked in `NEXT_TASK.md`.

## Coordinator 3 parallel release-qualification workstreams L / M / N / O — 2026-10-22
These are **NEW and not yet implemented**. Start from the latest post-coordinator documentation `main`; do not use stale I/J/K branch heads. Existing I/J/K work has landed; do not redo those features. The L/M/N/O branches below were already created by the workers; adopt their actual names rather than seeding replacement branches. Each workstream must read AGENTS and canonical docs, make scoped commits, run all four CI jobs, submit PR to `main`, and leave merging to Coordinator 3. No hosted migration, cloud resource write, real hosted test or WineShopPOS modification without explicit owner approval.

| Workstream / branch | Exclusive files/intent | Out of scope |
| --- | --- | --- |
| **L** `feat/p1-dev-db-release-readiness` | `supabase/**`, `tests/security/**`; ordered seven-migration inventory, local disposable upgrade/denial rehearsal, backup/rollback/runbook inside `supabase/**` | No hosted migration; do not alter previously applied migration history or I's durable-recovery semantics |
| **M** `feat/p1-azure-release-readiness` | `infra/azure/**`, `scripts/deploy/**` and `tests/infra/**`; read-only RG IAM scope, gated what-if/cost/rollback validation, approval checks | No Azure writes, resources, workflow privilege elevation or shared `.github/**` edits |
| **N** `feat/p1-render-performance` | `video-engine/**`, `tests/media/**`, `ops/benchmarks/**`; FFmpeg/ffprobe/license inventory, offline 1080p synthetic performance + scratch/memory/runtime/cost evidence | No third-party asset clearance claim, no cloud render, no `ops/**` H rework |
| **O** `feat/p1-hosted-e2e-readiness` | `tests/e2e/**`, `frontend/e2e/**`; secure manually opted-in DEV journey/negative-isolation test harness with safe cleanup, offline validation only in ordinary CI | No hosted smoke execution or destructive test/tenant data, no K mocked-test duplication, no cloud credentials in PR CI |

**Shared coordinator files only:** `docs/**`, `AGENTS.md`, `.github/workflows/**`, `docs/INTERFACES_V1.md`, frontend root/router/config and shared API contract. Where a worker needs CI wiring or cross-stream changes, submit a handoff proposal; coordinator fixes in a small separate PR. Proposed integration order L → M → N → O, subject to demonstrated dependencies and complete 4/4 checks after **every** merge. The checklist `docs/DEV_DEPLOYMENT_APPROVAL.md` is the hard authorization source.
