# Part 1 private cloud 30-second Reel — manual DEV artifact gate

Owner-authorized **RetailGrowthAI DEV only**. This is an executable source handoff,
**not a successful hosted Reel acceptance report**.

## What is already verified
- Real private queue-based promotional **poster** PNG 1080×1350, saved and selected, cross-tenant denial and cleanup: successful protected [GitHub run #40094276454](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40094276454); artifact #12560732018.
- Actual offline source FFmpeg rendered a synthetic 30-second H.264/AAC Reel in [run #40081154973](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40081154973), artifact #12555496142. This is **not** cloud execution.
- The DEV Flex ingress can return HTTP 503 after ~60s before the application, including on GET. P0 [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) **OPEN**. Running a real account-creating canary while the no-JWT GET preflight fails is not acceptable.

## Manual protected acceptance (still requires intentional dispatch)
Existing `.github/workflows/retail-dev-test-accounts-canary-once.yml`,
`workflow_dispatch` on **main**, input `approval_code` exactly
`AUTHORIZED_RETAILGROWTHAI_DEV_ONLY`, mode `browser-upload`, and
existing protected **dev** Environment/ROOT operator approval. Ordinary pushes
or CI do NOT provision temporary accounts. This workflow uses first-party
synthetic garment media, not customer assets or scraped third-party footage.

Following a passing bounded anonymous GET 401+handler-header preflight, the
test creates exactly two nonce-scoped example.invalid retailers, requires real
ROOT approvals, uses actual browser file upload, creates the seven-day Foundry
draft, reviews its day, accepts an idempotent real FFmpeg render, polls for
`SUCCEEDED`, reads the private signed object, verifies via **ffprobe**:
- one H.264 video stream, 1080×1920 portrait,
- one AAC audio stream,
- media duration 29–31 seconds,
- bounded private MP4 bytes from the exact RetailGrowthAI Storage origin.

Only **after** codec/byte validation, optional fixed output
`output/video-acceptance/retailgrowthai-dev-cloud-reel.mp4` is written on the
ephemeral GitHub runner and uploaded as seven-day artifact
`retailgrowthai-dev-live-cloud-30s-reel` when present. No signed URLs, JWTs,
service credentials or user email/password are logged/artifacted.

The test's `finally` block must independently clean up exactly its own
synthetic objects, jobs, shops and users and print
`CANARY_TEMP_FIXTURES_CLEANUP= PASS`. A produced artifact without full cleanup
does **not** certify the canary passed. A failed/timeout/aborted run should be
reviewed for orphaned fixtures before any re-run. Do not disable tenant RLS,
enable email/publishing or bypass the ROOT approval.

## Explicit remaining proof
A passed code review/4-job CI is not a real cloud video. The owner must still
see GitHub Actions log markers:
`CANARY_REAL_BROWSER_FILE_UPLOAD=true`,
`CANARY_REAL_SEVEN_DAY_DRAFT=true`,
`CANARY_RENDER_SUCCEEDED=true`,
`CANARY_PRIVATE_30S_H264_AAC_MP4_VERIFIED=true`,
`CANARY_REAL_CLOUD_REEL_ARTIFACT_READY=true`, and
`CANARY_TEMP_FIXTURES_CLEANUP= PASS`, plus the actual MP4 artifact.

Part 2 social scheduling and Part 3 Wan generation, SMTP, PROD and WineShopPOS
are outside this test and must remain untouched.
