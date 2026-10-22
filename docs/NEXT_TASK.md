# Next Development Task

## Current phase
Part 1 — AI Campaign Creation. Coordinator bootstrap verified in GitHub Actions and all four Part 1 feature branches established; parallel implementation may begin.

## Completed 2026-10-22
- Private GitHub repository and continuity docs verified; Python uv scaffold retained.
- Architecture, v1 interfaces and parallel ownership documented.
- Coordinator-owned React/Vite frontend initialized with an overview, mock campaign preview and account placeholder.
- Seven-day shared campaign fixture added at `frontend/src/features/campaigns/fixtures/sample-campaign.json`.
- JavaScript and Python offline contract checks added; GitHub Actions workflow defined to execute npm install, tests and build.
- No cloud resources, live AI, tenant database, video rendering, social platform integration or WineShopPOS edits.

## Next: Run four Part 1 workstreams (only from separate feature branches)
- A `feat/p1-foundation`: implement RetailGrowthAI-only Supabase schema/RLS, membership and auth shell; prove cross-shop denial. Do not use WineShopPOS resources.
- B `feat/p1-campaign-ai`: Python deterministic v1 schemas, seven-day planner and reviewer with mocked provider; authenticated campaign API boundary proposal.
- C `feat/p1-video`: offline FFmpeg 30-second portrait MP4 using authorized test media, with duration/codecs verified and license metadata.
- D `feat/p1-campaign-ui`: prompt, seven-day calendar, editor and mock render job UX within owned path; never label mock content as live.
- All read `AGENTS.md`, `docs/INTERFACES_V1.md` and `docs/PARALLEL_WORK.md`; create PRs to main without merging. Coordinator integrates with contract/security checks.

## Verification / coordination gates
- GitHub Actions `Frontend bootstrap checks` succeeded on bootstrap commit `5b7eb6f`: https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39739502984. Actual results: npm install (69 packages), JavaScript tests (2/2), Python unittest (1/1), Vite production build (42 modules; 2.17 seconds).
- The local sandbox cannot reach the npm registry; local npm install/build must not be claimed as executed successfully.
- The coordinator should generate and commit a reviewed `frontend/package-lock.json` with `npm install` from Git Bash, then change CI to `npm ci`.
- The initial mock contract has no live storage asset IDs; workstreams must not interpret fixture UUIDs as actual uploaded media.
- The four remote branches exist at the same coordinator-verified baseline. Workers must create their own local Git worktree and then open PRs. Review/merge in the documented order.

## Integration acceptance
- Cross-tenant reads/writes denied; each campaign response matches v1, with seven days and seven LinkedIn + Reel drafts.
- FFmpeg generates verified playable 30-sec H.264/AAC outputs from appropriately licensed test media.
- Complete auth -> prompt -> planning job -> draft review -> local render -> signed download, with bounded retries, idempotency and usage safety, before any deployment.

## Deployment blockers
- Dedicated RetailGrowthAI Supabase DEV/PROD projects absent.
- No model credentials/Foundry deployment or cloud video worker configured.
- Live publishing is Part 2, Wan is Part 3, and production testing is Part 4.

## CI upgrade integration gate (chore/part1-ci)
- Coordinator: review/merge the CI upgrade PR only after the **new** three-job workflow passes; existing bootstrap success is not evidence for the upgrade.
- Workstream C: add `video-engine/ci.sh` to perform real 30-second offline render, ffprobe validation and assertions; synthetic FFmpeg smoke is not a renderer test.
- Workstream B: add Python tests to `tests/ai` or `ai-agents/tests`; when AI dependencies are settled commit `ai-agents/uv.lock`.
- Coordinator: generate/review/commit `frontend/package-lock.json` in Git Bash; CI will then use `npm ci`.
- See docs/CI_AUTOMATION.md for tests, GitHub Actions logging/debugging and security limits.
