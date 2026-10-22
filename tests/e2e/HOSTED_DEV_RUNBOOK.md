# Workstream O — hosted DEV end-to-end qualification

Status: **source-ready only**. Workstream K mocked browser/API tests already run in CI. This is a separate opt-in, real-network qualification, not proof of deployment or permission to deploy.

## Hard gates — do not run without explicit approval

1. Coordinator confirms migrated **RetailGrowthAI DEV only** (Supabase project jeearzffnjbvghwjjjrf), DEV Azure API/queues/worker and HTTPS frontend are deployed and approved. Never use WineShopPOS or PROD endpoints.
2. Use two **DEV-only** accounts and active shops. User A is OWNER/EDITOR in shop A; user B is not a member of A. Both must use enabled password sign-in. IDs must be distinct.
3. Independent rights review authorizes a genuine PNG/JPEG/WebP image, maximum 25 MB, owned or licensed for commercial use. The harness uploads real bytes. User declaration alone does not provide independent clearance.
4. Coordinator reviews cost ceilings, claim lease, private storage retention and queue/poison controls. Hosted testing mutates DEV and incurs costs.
5. Operator explicitly opts in on an isolated workstation. **All GitHub Actions runners are forbidden** from hosted test execution. Never commit passwords, JWTs, service keys or real media.

## Required environment variables (not committed)

| Name | Purpose |
| --- | --- |
| RG_E2E_APPROVAL | exact I_APPROVE_RETAILGROWTHAI_DEV_E2E after explicit authorization |
| RG_E2E_TARGET | exact dev |
| RG_E2E_FRONTEND_URL | RetailGrowthAI DEV HTTPS deployed frontend origin |
| RG_E2E_API_URL | RetailGrowthAI DEV HTTPS deployed API origin |
| RG_E2E_SUPABASE_URL | exact https://jeearzffnjbvghwjjjrf.supabase.co |
| RG_E2E_ALLOWED_ORIGINS | comma-separated **exact three** origins above; operator-pinned |
| RG_E2E_SUPABASE_PUBLISHABLE_KEY | DEV browser publishable key, never service key |
| RG_E2E_USER_A_EMAIL, RG_E2E_USER_A_PASSWORD | Dedicated DEV owner/editor account |
| RG_E2E_USER_B_EMAIL, RG_E2E_USER_B_PASSWORD | Dedicated independent DEV account |
| RG_E2E_SHOP_A_ID, RG_E2E_SHOP_B_ID | Distinct active DEV shop UUIDs |
| RG_E2E_IMAGE_PATH | Local, rights-cleared real PNG/JPEG/WebP file |
| RG_E2E_IMAGE_EVIDENCE | Honest source/ownership/license attribution |
| RG_E2E_RIGHTS_ATTESTED | exact yes after rights clearance |
| RG_E2E_EXPIRED_JWT | Actual previously issued DEV JWT, expired >=60s, issuer and audience match DEV; NOT a forged offline token |
| RG_E2E_POLL_TIMEOUT_MS | Optional 60000–1800000, defaults to 1200000 |
| RG_E2E_RECOVERY_JOB_ID | Optional authorized shop A job created during separately approved DEV fault injection |

Preflight rejects CI, production/unrecognized Supabase project, unpinned/non-HTTPS origins (frontend/API hostname must both contain "dev", duplicate tenants/users, unlicensed/invalid file bytes and nonexpired JWTs. JWT payload validation does not establish signature authenticity, so a genuine expired JWT must be supplied by the operator.

The frontend must already be built with matching VITE_SUPABASE_URL, VITE_SUPABASE_PUBLISHABLE_KEY and VITE_CAMPAIGN_API_BASE_URL. Tests never deploy or apply migrations.

## Run manually only after deployment approval

Install Node dependencies and Chromium and ensure ffprobe is available in PATH. In Git Bash, from repository root:

    cd frontend
    npm install --no-audit --no-fund
    npm install --prefix e2e --no-audit --no-fund
    ./e2e/node_modules/.bin/playwright install chromium
    cd e2e
    npm run test:hosted-dev

Export environment variables from a secure local secret source without printing keys/passwords/JWTs. Never run this via GitHub Actions.

## Qualification coverage

- Browser real A sign-in; private image byte upload/registration and RLS media verification; seven-day campaign generation; saved PATCH draft and server re-read; genuine async 30s render, signed MP4 download; ffprobe H.264/AAC, 1080x1920, 29–31s.
- Separately authenticated B cannot GET/PATCH/render/download A's resources or enumerate private A media.
- Genuine expired JWT denied on all campaign/render methods.
- Duplicate render request must return the same job ID. Read-only polling tolerates transient 429/502/503/504, never automatically replays POST/PATCH.
- Optional recovery job watcher requires a **pre-faulted** DEV job and operator approval. Its success alone does **not** prove retry/poison handling: independently collect SQL attempt/outbox receipts, stale-token fencing, Azure queue/reconciler events and logs. Without deliberate injected fault and audit evidence, retry recovery is **UNVERIFIED**.
- No test cleanup/delete API assumed; inventoried outputs must be removed through an approved tenant-safe retention procedure, within DEV budgets.
- Traces, screenshots and videos disabled to avoid storing JWTs/private images.

## CI and coordinator handoff

The standard default frontend Playwright config matches *.spec.mjs **only** and runs existing mocked K cases plus new offline approval/validation/poll tests. Hosted file *.hosted.mjs is excluded, requires a separate config, and refuses any CI runner, even if approval credentials were accidentally injected. CI must run all four existing jobs green, but green offline checks are **not hosted evidence**.

Only frontend/e2e/** and tests/e2e/** changed. Coordinator 3 owns canonical docs, interfaces, CI workflow and merges; after merging, update PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG. No hosted Supabase migrations, Azure deployment or WineShopPOS changes are authorized by this PR.
