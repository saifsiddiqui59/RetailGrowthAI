# CI Automation — RetailGrowthAI Part 1

## What this provides
Workflow: `.github/workflows/frontend-bootstrap.yml` (retained path to preserve compatibility; displayed workflow name is **RetailGrowthAI Part 1 CI**).
GitHub automatically runs the four independent jobs below on pushes to `main`, `feat/**`, `chore/**`, and pull requests targeting `main`. It may also be started manually from the Actions tab after merging the workflow to the default branch.

| Job | Executed checks |
| --- | --- |
| Frontend build + contract tests | Node.js 22, `npm ci` when a reviewed lockfile exists (otherwise `npm install` warning), `npm test`, `npm run build` |
| Python / uv + campaign contract tests | `uv` 0.13.1, Python 3.13, `uv sync --project ai-agents`, run pytest against `tests/contracts` and optional `tests/ai`, `ai-agents/tests` |
| FFmpeg codecs + renderer tests | install FFmpeg, encode a **2-second synthetic portrait** H.264/AAC video, verify streams via ffprobe, and call `video-engine/ci.sh` when implemented |
| Supabase isolation + authentication client tests | Node 22 client unit tests, isolated Supabase CLI Postgres, apply all tenant migrations, execute RLS and private-storage negative SQL tests with assertion failures fatal |

The two-second synthetic MP4 is a toolchain smoke test. After PR #2, `video-engine/ci.sh` additionally renders and verifies a genuine **30-second synthetic multi-image** H.264/AAC Reel. This still is not evidence that externally licensed commercial Reels are production-ready. If renderer code is added without `video-engine/ci.sh`, the media job fails intentionally. Workstream C owns creating an executable `video-engine/ci.sh` that renders fixture inputs offline, validates duration/aspect/codecs/content and returns nonzero on failure. It should write permitted non-sensitive evidence into `ci-artifacts/` if an artifact is useful.

## Chat-based coding and debugging loop
1. Worker chat uses its assigned feature branch and file ownership from `docs/PARALLEL_WORK.md`.
2. ChatGPT commits/pushes changes via the connected GitHub app; CI starts automatically, no interactive Codespaces terminal needed.
3. ChatGPT reads workflow runs, job steps/logs through the GitHub app, fixes the code on that same branch and pushes again.
4. Repeat while actively interacting in chat until checks pass, or clearly report a blocker. Do not claim an uninspected CI run passed.
5. Open a PR to `main`; coordinator reviews, tests integration and decides whether to merge. Workers must not merge their own PRs.

Note: GitHub Actions only runs declared commands. It **does not automatically repair code**, test unimplemented UI behaviors, create live Supabase/Azure resources, provide interactive terminal access or continue ChatGPT thinking after the chat ends. Fixes require ChatGPT to inspect logs in an active session.

## Security, cost, and current gaps
- Workflow has read-only `contents: read` permissions. No production secrets, service keys, cloud deploys or `pull_request_target` privilege elevation.
- PR jobs can execute untrusted code, so never inject deployment credentials into them.
- The merged workflow includes a fourth independent local Supabase security job; all jobs have timeouts, and redundant runs are cancelled. GitHub-hosted runner minutes/storage depend on current repository plan.
- The existing frontend uses `npm install` until its reviewed `package-lock.json` is committed. Once committed, workflow uses deterministic `npm ci`.
- Workstream B committed `ai-agents/uv.lock`; the frontend still needs its package lock.
- Workstream A provides cross-tenant RLS/private-media tests, executed on dedicated DEV; the coordinator security job runs them against disposable local Supabase on each push. Python pytest now exercises B campaign/provider/service tests and coordinator B-to-C contract tests; the C renderer CI runs real 30s synthetic encoding.
- Read GitHub Actions job logs/artifacts before changing code. Do not assume a successful smoke check proves cloud auth/tenant isolation, FFmpeg quality, model correctness or production readiness.
- `ci-artifacts/` contains synthetic test output only; artifact retention is 3 days.

## Troubleshooting
Open **GitHub → RetailGrowthAI → Actions → RetailGrowthAI Part 1 CI → failed run → failed job**. Read logs. The coordinator may request failing job logs through the GitHub connection.

If a workflow change is not yet merged, its manual `workflow_dispatch` trigger may not appear on the default branch; pushes/PRs to its feature branch will still run CI.

## Coordinator verification — 2026-10-22
- PR #1 squash-merged as `6e3627968beb8288afe857adea0238db4fcda862`.
- [Post-merge GitHub Actions run #39745758948](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39745758948) concluded **success** on `main` with all three jobs successful.
- This records the earlier three-job scaffold only. PRs #5/#6/#3/#2/#4 later added tenant isolation, Python behavior and a real 30-second synthetic MP4 render; see the updated coordinator checkpoint below.

## Proposed coordinator gate — Workstream A dependency
- Workstream A [PR #5](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/5) must land first. Coordinator integration branch `chore/p1-foundation-auth-ci-integration` then brings the fourth job and account route onto main after CI passes.
- The fourth job is intentionally isolated: `supabase init --yes`, `supabase db start`, Postgres client `psql -v ON_ERROR_STOP=1` runs `tests/security/rls_negative.sql` and `tests/security/storage_negative.sql`, then `supabase stop --no-backup`. It never links to a remote Supabase project or uses service keys.
- CI tests are not production/browser Auth end-to-end tests. Validate actual email sign-in, profile editing and session expiry separately with RetailGrowthAI DEV settings before release.

- Verified on coordinator integration branch: [run 39752723276](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39752723276) completed successfully; security step executed Supabase migrations and both negative SQL tests. All four jobs passed. This evidence is from the branch, not post-merge main.


## Integrated coordinator checkpoint — 2026-10-22
- PRs #5, #6, #3, #2, #4 integrated to main, preserving an authenticated `/account` route and a mock-only `/campaigns` editor.
- Four expected CI jobs: frontend Node/Vite build; Python uv pytest including `tests/integration/`; FFmpeg smoke **plus** `video-engine/ci.sh` 30-second synthetic render, ffprobe and media unit tests; local-only Supabase auth client and SQL isolation checks.
- Integrated offline test: `tests/integration/test_campaign_render_contract.py` checks B MockFoundryProvider v1 output against C asset-rights/tenant-safe `load_job` for seven days; does **not** exercise HTTP, real JWT, a hosted database, or signed media downloads.
- The reconciled PR #4 commit passed all four jobs in [run 39755166150](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39755166150). Verify the final coordinator commit on main separately.

## 2026-10-22 — Upload registration gate
- The Supabase security job also runs `tests/security/draft_save_negative.sql` and `tests/security/upload_registration_negative.sql` on an isolated disposable DB, including denied cross-shop / VIEWER / anonymous operations, stale edits and unsigned media metadata registration. The frontend security tests exercise signed-in private binary upload, byte-signature checks and restricted RPC behavior.
- PR #16 [run #39769374328](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769374328) passed all four jobs before merge. Post-merge main [#39769717413](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39769717413) independently passed all four checks.
- These checks do not validate real Supabase Storage HTTP upload or genuine third-party commercial license provenance without an approved DEV deployment.

## 2026-10-22 — Coordinator E/F/G/H test gates (PR #22)
- The same four jobs now cover `tests/reliability/` and `tests/e2e/` under Python pytest, real Playwright Chromium browser runs with mocked external Supabase/API when `frontend/e2e/package.json` exists, and offline packaging/unit/Bicep checks when `scripts/deploy/check.sh` exists.
- Browser E2E uses intercepted network responses and does not contact a real Supabase/Azure project or encode a licensed production MP4. Azure package checks never deploy; Bicep compile is conditional on local `az` CLI availability. DEV deployment requires explicit owner approval and unresolved timeout/lease/risk fixes.
- Existing FFmpeg synthetic tests, local-only Supabase migrations/negative RLS tests, and all authorization checks remain mandatory. Workstream PRs #18–#21 passed the original CI; only integrated main with #22 covers newly introduced H/G/F tests. See WORK_LOG for final main run evidence.
