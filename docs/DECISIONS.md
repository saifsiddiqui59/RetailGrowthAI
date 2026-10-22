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
