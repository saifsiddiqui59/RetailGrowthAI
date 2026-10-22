# Next Development Task

## Current phase
Part 1 — AI Campaign Creation. Architecture baseline recorded; implementation not started.

## Completed 2026-10-22
- Private GitHub repository and project continuity docs verified.
- Python uv project scaffold exists in ai-agents/.
- Confirmed safe WineShopPOS patterns for reuse; WineShopPOS unchanged.
- Created docs/ARCHITECTURE.md, docs/INTERFACES_V1.md and docs/PARALLEL_WORK.md.

## Next: Coordinator bootstrap (must precede parallel feature branches)
1. Read AGENTS.md and every canonical document, especially INTERFACES_V1.md and PARALLEL_WORK.md.
2. Verify current main and do not overwrite user/local work.
3. Initialize runnable React/Vite frontend with npm under frontend/; keep frontend assets separate from WineShopPOS.
4. Implement starter app router/layout and a fixture matching docs/INTERFACES_V1.md (no claims of live AI or published content).
5. Run npm install, npm run build, and basic contract verification; do not declare tests passed unless actually run.
6. Commit and push bootstrap to RetailGrowthAI main; update PROJECT_STATE, NEXT_TASK, WORK_LOG, and DECISIONS if needed.
7. Create separate branches for parallel chats only after the bootstrap commit:
   - feat/p1-foundation
   - feat/p1-campaign-ai
   - feat/p1-video
   - feat/p1-campaign-ui

## Parallel milestone acceptance
- A: auth/RLS tenant boundary tested.
- B: typed seven-day AI plan generates valid offline fixture shape and bounded review.
- C: independent FFmpeg renderer produces a 30-sec MP4 locally from legal test media.
- D: campaign brief/calendar/content preview UI runs with contract-compliant mocks.
- Integration completed through reviewed PRs; one campaign input yields seven daily LinkedIn drafts and seven Instagram Reel drafts/assets.

## Blockers / deployment gates
- A dedicated RetailGrowthAI Supabase project does not exist; no WineShopPOS project may be used.
- No model credentials/Foundry deployment or cloud video render infrastructure is configured yet.
- Live publishing, Wan, and production deployment remain out of Part 1.
