# RetailGrowthAI DEV — Browser Upload Canary Handoff (2026-10-24)

## Purpose and scope
The owner requested a **real Playwright-hosted DEV test**, not a phone upload, TinyFish native file-picker click or a fake preview. Existing `frontend/e2e/campaign-journey.spec.mjs` already proves `setInputFiles` under offline request interception; existing `hosted-journey.hosted.mjs` covers a manually configured host, but `hosted-support.mjs` deliberately *forbids GitHub Actions*. Preserve both boundaries.

This isolated change adds `frontend/e2e/dev-canary-upload.mjs`, invoked by the already-approved temporary DEV canary in `tests/e2e/retail_dev_canary_once.py` **only if** `RGAI_DEV_PLAYWRIGHT_UPLOAD=1`. It:
- Uses the real existing Azure Static Web Apps DEV login, the disposable `rgai-canary-*@example.invalid` test OWNER/shop and the existing private image-upload UI.
- Generates an **original three-shirt-color PNG** inside the test runner with Python standard library (no external license, Calvin Klein photo, public media URL or user image).
- Passes the PNG bytes to Playwright's `setInputFiles`; uses only the test retailer's login, not a service-role credential in Chromium.
- Registers one shop-scoped private media asset, then continues the existing backend Foundry→seven-day campaign→30-second Reel/FFmpeg workflow where deployed and authorized. The separate Part 1 poster runtime is skipped in this browser-upload mode and remains unchanged in the default canary.
- Returns only a temporary UUID and private object **path** for the pre-existing exact cleanup logic, including partial uploads; no JWT, password, media bytes, signed URLs, or user data are printed.
- Does **not** connect social OAuth, publish a post, touch WineShopPOS, provision resources, or change hosted SQL.

## Protected manual DEV workflow, never automatic
The replacement PR changes the canary workflow to `workflow_dispatch` **only**, with an explicit `approval_code` and `mode` gate. GitHub push, ordinary PR CI, and merges must never create test accounts or alter the hosted environment. Launch manually only through the existing protected `dev` GitHub Environment, after the owner authorizes the exact run.

A safe single-purpose DEV operator job should:
1. Use only the existing `dev` GitHub Environment and its RetailGrowthAI project-scoped `RETAIL_SUPABASE_SERVICE_ROLE_KEY` secret. Do not put that key into a browser process.
2. Require owner approval for this run, `RGAI_DEV_CANARY_APPROVAL=AUTHORIZED_RETAILGROWTHAI_DEV_ONLY`, and set `RGAI_DEV_PLAYWRIGHT_UPLOAD=1` ONLY for the one-time job.
3. Install Node 22, `npm --prefix frontend/e2e install --no-audit --no-fund`, and `frontend/e2e/node_modules/.bin/playwright install --with-deps chromium` before running the existing Python canary.
4. Have a ROOT operator approve only the two temporary `rgai-canary-<nonce>-{a,b}@example.invalid` onboarding requests as the existing canary requires; **never** disable onboarding or silently grant shop access.
5. Allow time for backend Foundry and FFmpeg worker; Part 1 poster is intentionally outside this browser-upload acceptance path. The default canary still independently covers poster when deployed.
6. Never expose the privileged service secret in logs, browser environment, artifacts, traces, network HAR, or webpage.
7. Require `CANARY_REAL_BROWSER_FILE_UPLOAD=true`, `CANARY_REAL_SEVEN_DAY_DRAFT=true`, `CANARY_PRIVATE_30S_H264_MP4_VERIFIED=true`, and `CANARY_TEMP_FIXTURES_CLEANUP=PASS` before reporting full hosted success.
8. Keep `main` merge, workflow launch, Azure changes and any hosted DB migration under the Final Coordinator/DEV Operator.

## Execution state
Source-only until manual owner-approved execution of the protected workflow prepares Playwright. **No cloud Playwright canary execution or hosted image upload is claimed by this branch.** The ordinary four CI jobs are offline and cannot substitute for hosted evidence. Record exact run IDs and cleanup status after an actual approved run.
