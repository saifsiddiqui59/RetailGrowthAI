# CI Automation — RetailGrowthAI Part 1

## What this provides
Workflow: `.github/workflows/frontend-bootstrap.yml` (retained path to preserve compatibility; displayed workflow name is **RetailGrowthAI Part 1 CI**).
GitHub automatically runs the three independent jobs below on pushes to `main`, `feat/**`, `chore/**`, and pull requests targeting `main`. It may also be started manually from the Actions tab after merging the workflow to the default branch.

| Job | Executed checks |
| --- | --- |
| Frontend build + contract tests | Node.js 22, `npm ci` when a reviewed lockfile exists (otherwise `npm install` warning), `npm test`, `npm run build` |
| Python / uv + campaign contract tests | `uv` 0.13.1, Python 3.13, `uv sync --project ai-agents`, run pytest against `tests/contracts` and optional `tests/ai`, `ai-agents/tests` |
| FFmpeg codecs + renderer tests | install FFmpeg, encode a **2-second synthetic portrait** H.264/AAC video, verify streams via ffprobe, and call `video-engine/ci.sh` when implemented |

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
- There are three separate jobs, with timeouts and cancellation for older runs. GitHub-hosted runner minutes/storage depend on current repository plan.
- The existing frontend uses `npm install` until its reviewed `package-lock.json` is committed. Once committed, workflow uses deterministic `npm ci`.
- For AI dependencies, commit `ai-agents/uv.lock` when established; until then `uv sync` can resolve current packages.
- Python `pytest` and renderer harness remain initially thin; add negative cross-tenant and true renderer tests as Part 1 progresses.
- Read GitHub Actions job logs/artifacts before changing code. Do not assume a successful smoke check proves cloud auth/tenant isolation, FFmpeg quality, model correctness or production readiness.
- `ci-artifacts/` contains synthetic test output only; artifact retention is 3 days.

## Troubleshooting
Open **GitHub → RetailGrowthAI → Actions → RetailGrowthAI Part 1 CI → failed run → failed job**. Read logs. The coordinator may request failing job logs through the GitHub connection.

If a workflow change is not yet merged, its manual `workflow_dispatch` trigger may not appear on the default branch; pushes/PRs to its feature branch will still run CI.

## Coordinator verification — 2026-10-22
- PR #1 squash-merged as `6e3627968beb8288afe857adea0238db4fcda862`.
- [Post-merge GitHub Actions run #39745758948](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39745758948) concluded **success** on `main` with all three jobs successful.
- This validates the workflow scaffold only. Frontend lockfile, Python behavior tests, tenant isolation and real 30-second MP4 rendering remain for subsequent tasks.
