# RetailGrowthAI — On-demand extended CPU acceptance (2026-11-18)

## Why

ChatGPT coding automations have an observed **33.8-second average last-run duration**. Their automation settings do not expose a minimum session duration, and no executable checkout environment is provisioned. **This workflow does not lengthen ChatGPT's reasoning session or run an AI coder.** Instead it lets the existing short scheduler hand off real, longer CPU work to GitHub Actions.

## Implementation

- New workflow: `.github/workflows/retailgrowthai-f4-extended-cpu.yml`, from a standalone reviewable PR. A single branch-only push smoke is allowed for initial verification; after integration, normal operation is **manual `workflow_dispatch` only**. No cron and no repeated billable runs.
- Target: existing F4 parent `feat/feature4-professional-video-studio` and its existing synthetic `video-engine/demo_feature4_diwali.py` plus HyperFrames `render.mjs`. No new renderer/model. Record the **actual checked-out SHA**, with optional exact-40-character expected SHA rejection.
- Run a **real 60-second, 1080×1920, 24fps H.264/AAC** CPU-only synthetic encode and verify via existing `render_adapter.verify_mp4`. Lock guard checks pinned dependencies before `npm ci`. Store SHA-256, source SHA, workflow SHA and run ID in JSON. Upload only small proof JSON; discard the private synthetic MP4.
- Budget: Ubuntu 24.04, read-only repository token, no secrets, no GPU or paid model, overall job `timeout-minutes: 25`, render step `timeout-minutes: 18`, render command maximum 900s, dependency install/browser download bounded. GitHub-hosted runner minutes may have usage cost depending on the repository/plan. A job can finish earlier or fail; **25 minutes is the cap, not a guaranteed runtime**.
- Source-only: proving codecs and timing does not establish visual quality, licensing, signed-in DEV, customer media, Azure worker, payment, or security acceptance. F4-01/F4-02/F4-03 remain IN PROGRESS and PR #322 remains draft until independent review, true 60s receipt coverage, and hosted acceptance.

## Verification and activation

1. Verify YAML and review the exact workflow diff; obtain independent affected-lead review (shared `.github/workflows/**` change).
2. Verify the one-off branch smoke run actually appears; log job start/end, source head, `receipt.json` hash and overall status. If branch push did not trigger it, **do not claim it ran**.
3. After approval and integration to main, GitHub Actions → `RetailGrowthAI F4 extended CPU acceptance` → **Run workflow** → optionally supply the exact current F4 source SHA. This starts the long CPU test; it is not invoked by the existing ChatGPT automation tool.
4. Keep existing Part 1 CI four required jobs and PR #967's proposed 15→25-minute FFmpeg budget intact. Do not quietly merge #967 or this workflow; never bypass review or repo checks.
5. Reconcile results into `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, and append to `docs/WORK_LOG.md` at approved integration. Do not mark source/render accepted without passing run evidence.

## Rollback

Remove the dedicated workflow after independent review, or disable its manual use. It does not modify any existing CI jobs, Actions permissions, cloud infrastructure or WineShopPOS.
