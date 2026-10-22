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
