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

## 2026-10-22 — Workstreams I/J/K merged; offline evidence only
- I [PR #34](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/34) [CI #39798607296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39798607296) completed successfully; Supabase disposable CI applies its NEW outbox/fencing migration and existing Python tests include reliability failure injection.
- J [PR #33](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/33) [branch CI #39792621639](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39792621639) passed all four jobs including Python deployment package/Bicep tests. Earlier duplicate Bicep decorator failure was fixed; no checks disabled.
- K [PR #31](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/31) [CI #39791472265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39791472265) passed all four jobs including mocked Playwright Chromium and HTTP API tests.
- The final [post-K main combined CI #39801130265](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39801130265) independently completed **4/4 PASS**: Python, Supabase isolation, FFmpeg renderer and frontend/Playwright. GitHub Actions and package tests never deploy Azure or apply hosted Supabase migrations. Actual JWT signatures, commercial media and cloud-hosted poison/replay remain unverified.

- On docs-only PR #35, the first final CI attempt #39801881035 verified the Python, frontend and isolated Supabase jobs, while FFmpeg availability remained in-progress on the runner for an unusually long period. Trigger a fresh complete run rather than counting the partially completed attempt as green; preserve the existing FFmpeg smoke, full 30s renderer, codec and artifact assertions. Await definitive all-four completion before merging.

## Coordinator 3 baseline (2026-10-22)
- [Post-PR #36 **main** run #39805920327](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39805920327) verified **four successful jobs** at `84c9b87`: frontend including mocked Playwright, Python incl. offline API/reliability E2E and Azure packaging, FFmpeg full synthetic video, disposable Supabase migration/RLS. The previous docs-merge run #39803979666 was cancelled/superseded. Optional Chromium timeout PR #37 was closed **unmerged**; no change needed on a green main.
- New L/M/N/O qualification work should add offline assertions through existing four jobs where owned harness files are discovered. Anything touching `.github/workflows/**` belongs only to Coordinator 3. Hosted smoke must be manual, explicitly approved, safely scoped to RetailGrowthAI DEV and never receive secrets on ordinary PR CI. No GitHub workflow can imply Azure deploy or hosted SQL permission.

- Coordinator 3 strengthened the same four non-deploy jobs for the active L/M/N/O branches: Security Node executes all `tests/security/*.test.mjs` (including ordered DEV DB migration preflight), isolated Postgres executes durable-recovery SQL denial regressions, and Python discovers `tests/infra/` in addition to existing `tests/e2e/`. The FFmpeg job already runs `tests/media` via `video-engine/ci.sh`. All are offline, with no cloud secrets or hosted DB operations; review L/M/N/O PR checks after integration.

## 2026-10-22 — GitHub public visibility and recovered all-four integration CI (LATEST)
- Owner switched RetailGrowthAI to public after exhausting GitHub Free private-repository Actions minutes (2,000/2,000). Standard public runners can execute free; source/history and Actions logs are visible to everyone, so no secrets or licensed assets may be committed/logged.
- Coordinator #47 directed GitHub Ubuntu runner `mirror+file:/etc/apt/apt-mirrors.txt` at the official archive for FFmpeg when installation is needed. Coordinator #50 applied identical ephemeral-runner mirror handling to Playwright's `install --with-deps chromium` after main #39826247419 showed an actual 420-second archive timeout. All original CI steps, offline browser tests, full synthetic 30-second video, disposable Supabase negative tests and Azure package preflights remain mandatory.
- Exact PR checks: #47 [#39812135974 attempt 6](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39812135974) 4/4; #50 [#39827416615](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39827416615) 4/4; L #43 [#39827712699](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39827712699) 4/4 successful jobs; M #46 [#39810592159 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810592159) 4/4; N #44 [#39810720819](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39810720819) 4/4; O #45 [#39811545219 attempt 4](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39811545219) 4/4.
- Corresponding post-integration `main` CI all passed **4/4**: #39827785931 after #50, #39828375693 after L, #39828664342 after M, #39829076503 after N and [#39829360425 after O](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39829360425). This is **offline source validation** only, not Azure deployment, hosted migration or real licensed-media E2E.
