# RetailGrowthAI — Scheduled coding executor migration (2026-11-17)

## Problem verified

Coding automation runs finish in about 26–46 seconds (recent F2 27.749 s, F3 45.589 s, F4 25.817 s, F7 36.097 s; average 33.813 s). Last runs verified code/test commits: 0. The tasks can use GitHub connector file edits and external GitHub Actions, but they do not have a confirmed persistent executable repository checkout.

The four existing task IDs:
- F2: `Automation_da1315db6a28819188762e271906839a`
- F3: `6ae731649368819198cd8ceea7a15a60`
- F4: `6af396f7239481918480cfed86af4b2c`
- F7: `6af396facd5c8191a5add51a377f199c`

Their `environment_selection` is `inherited`, and `environments` currently returns `null` (details unavailable). THIS IS NOT proof that a cloud executor exists. The exposed Automations update tool supports title/prompt/schedule/enabled/timing, but does **not** expose attaching or provisioning an execution environment; changing text or schedule cadence cannot guarantee longer runtime.

## Actual fix (requires user-side environment selection)

1. In ChatGPT **Work > Cloud** (or Codex on web), set up/select a cloud coding environment with GitHub repo `saifsiddiqui59/RetailGrowthAI`. Make sure a clean repo checkout and Python/uv, Node/npm and FFmpeg tests work. Configure environment setup as needed; keep Azure paid resources and GPU disabled. Cloud tasks can continue independently of the user's device being awake.
2. Alternatively in the ChatGPT **desktop app**, configure a scheduled coding task for local repository `E:\\RetailGrowthAI` and choose an **isolated Git worktree** rather than editing the user's main checkout. The PC/app must remain on for local tasks.
3. **Move/replace** the four GitHub-connector-only coding tasks to tasks created in Work/Codex with the selected coding environment. Preserve original ownership, PR queue CAS lease discipline, task IDs in `coordination/feature_tasks.json`, exact-head four-job CI and manual-integration ownership. Do not allow concurrently executing old and new coding schedules on the same PR. Pause the old feature task only AFTER the new environment-backed task has proven a tested source commit on an owned PR.
4. In the environment-backed task, run the exact targeted local regression (uv/node/FFmpeg as applicable) first; then commit to the feature PR branch, trigger/recheck GitHub CI, and release lease. If no safe code gap exists, report `REVIEW_BLOCKED` rather than spending minutes artificially waiting.

## Acceptance protocol

- An environment-backed coding task must show a confirmed environment ID/worktree in its Scheduled task details, repo commit SHA, an actual executed test command + result and correct PR ownership.
- Verify **two consecutive runs**: actual started/end timestamps, source/test commits, GitHub-hosted CI by exact final head, and executed local tests. The goal is more useful real coding, not a fake minimum wall time. An active multi-step repair may take several minutes; a truly blocked no-op should finish quickly.
- The health monitor must report executor type `GITHUB_CONNECTOR_ONLY` vs `CLOUD_CODEX` vs `LOCAL_WORKTREE`, observed duration (not target duration), and verified commits/tests. If the environment cannot be configured, mark `EXECUTOR_NOT_PROVISIONED`, avoid inventing a duration guarantee, and continue using connector+GitHub Actions for small safe fixes.
- Keep feature/main integration reviews, tenant/RLS/auth, rights and licensed media gates; never touch WineShopPOS, production, or paid GPU without separate approval.

## References

OpenAI documentation: https://learn.chatgpt.com/docs/environments/cloud-environments and https://learn.chatgpt.com/docs/automations

## Current status

Prepared migration plan only. Environment selection requires user action in Work/Codex or desktop Scheduled UI; no cloud instance has been provisioned by this document. No feature code, Azure/PROD, or WineShopPOS changes.
