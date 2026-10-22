# CI Automation — RetailGrowthAI Part 1

## What this provides
Workflow: `.github/workflows/frontend-bootstrap.yml` (retained path to preserve compatibility; displayed workflow name is **RetailGrowthAI Part 1 CI**).
GitHub automatically runs the three independent jobs below on pushes to `main`, `feat/**`, `chore/**`, and pull requests targeting `main`. It may also be started manually from the Actions tab after merging the workflow to the default branch.

| Job | Executed checks |
| --- | --- |
| Frontend build + contract tests | Node.js 22, `npm ci` when a reviewed lockfile exists (otherwise `npm install` warning), `npm test`, `npm run build` |
| Python / uv + campaign contract tests | `uv` 0.13.1, Python 3.13, `uv sync --project ai-agents`, run pytest against `tests/contracts` and optional `tests/ai`, `ai-agents/tests` |
| FFmpeg codecs + renderer tests | install FFmpeg, encode a **2-second synthetic portrait** H.264/AAC video, verify streams via ffprobe, and call `video-engine/ci.sh` when implemented |
| Supabase isolation + authentication client tests | Node 22 client unit tests, isolated Supabase CLI Postgres, apply all tenant migrations, execute RLS and private-storage negative SQL tests with assertion failures fatal |

The synthetic MP4 is a **toolchain smoke test**, not evidence that real 30-second commercial Reels render. If renderer code is added without `video-engine/ci.sh`, the media job fails intentionally. Workstream C owns creating an executable `video-engine/ci.sh` that renders fixture inputs offline, validates duration/aspect/codecs/content and returns nonzero on failure. It should write permitted non-sensitive evidence into `ci-artifacts/` if an artifact is useful.

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
- The coordinator integration branch adds a fourth independent local Supabase security job; all jobs have timeouts, and redundant runs are cancelled. GitHub-hosted runner minutes/storage depend on current repository plan.
- The existing frontend uses `npm install` until its reviewed `package-lock.json` is committed. Once committed, workflow uses deterministic `npm ci`.
- For AI dependencies, commit `ai-agents/uv.lock` when established; until then `uv sync` can resolve current packages.
- Workstream A provides cross-tenant RLS/private-media tests, executed on dedicated DEV; the coordinator security job runs them against disposable local Supabase on each push. Python `pytest` and renderer coverage are still being extended by B/C.
- Read GitHub Actions job logs/artifacts before changing code. Do not assume a successful smoke check proves cloud auth/tenant isolation, FFmpeg quality, model correctness or production readiness.
- `ci-artifacts/` contains synthetic test output only; artifact retention is 3 days.

## Troubleshooting
Open **GitHub → RetailGrowthAI → Actions → RetailGrowthAI Part 1 CI → failed run → failed job**. Read logs. The coordinator may request failing job logs through the GitHub connection.

If a workflow change is not yet merged, its manual `workflow_dispatch` trigger may not appear on the default branch; pushes/PRs to its feature branch will still run CI.

## Coordinator verification — 2026-10-22
- PR #1 squash-merged as `6e3627968beb8288afe857adea0238db4fcda862`.
- [Post-merge GitHub Actions run #39745758948](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39745758948) concluded **success** on `main` with all three jobs successful.
- This validates the workflow scaffold only. Frontend lockfile, Python behavior tests, tenant isolation and real 30-second MP4 rendering remain for subsequent tasks.

## Proposed coordinator gate — Workstream A dependency
- Workstream A [PR #5](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/5) must land first. Coordinator integration branch `chore/p1-foundation-auth-ci-integration` then brings the fourth job and account route onto main after CI passes.
- The fourth job is intentionally isolated: `supabase init --yes`, `supabase db start`, Postgres client `psql -v ON_ERROR_STOP=1` runs `tests/security/rls_negative.sql` and `tests/security/storage_negative.sql`, then `supabase stop --no-backup`. It never links to a remote Supabase project or uses service keys.
- CI tests are not production/browser Auth end-to-end tests. Validate actual email sign-in, profile editing and session expiry separately with RetailGrowthAI DEV settings before release.

- Verified on coordinator integration branch: [run 39752723276](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39752723276) completed successfully; security step executed Supabase migrations and both negative SQL tests. All four jobs passed. This evidence is from the branch, not post-merge main.
