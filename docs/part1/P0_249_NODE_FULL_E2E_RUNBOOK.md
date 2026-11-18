# P0 #249 — ROOT-approved full Node DEV acceptance

**Status: prepared, NOT executed.** The existing RetailGrowthAI Free SWA named preview is p0249writes; the customer application still uses its original Python endpoint.

## Controlled manual activation

Use the GitHub Actions workflow named **RetailGrowthAI owner-authorized DEV temporary test accounts + live tenant canary**. Manually select main and provide the protected approval code AUTHORIZED_RETAILGROWTHAI_DEV_ONLY. Choose either node-poster-reel or node-browser-reel. There is no automatic deployment, production switch, paid hosting or workflow trigger on PR merge.

The two unique disposable retailer users and shops are created by the existing canary and require explicit current SaaS ROOT onboarding approval for each newly registered shop. The test never changes the approval gate or impersonates ROOT. On failure, the original finally handler must clean exactly those shops, accounts, media and jobs. Never use WineShopPOS or real customer identities.

## Acceptance paths

- **node-poster-reel:** original first-party licensed synthetic PNG through authenticated REST upload, seven-day campaign, DRAFT save, real poster generation, private 1080x1350 PNG download and optimistic banner selection, then 30-second 1080x1920 H.264/AAC FFmpeg Reel with genuine signed private download and exact cleanup.
- **node-browser-reel:** real Playwright upload, seven-day campaign/DRAFT and 30-second H.264/AAC private Reel through Node; the existing browser-upload canary deliberately skips the separate poster flow. It must also clean up completely.

Source wrapper: tests/e2e/p0249_dev_node_full_canary_once.py. It reuses tests/e2e/retail_dev_canary_once.py; only the exact Node HTTP target changes to the pinned p0249writes hostname, and only original user-issued Supabase JWTs are forwarded using x-rgai-supabase-jwt. Other queries still use caller-token Supabase RLS. No service-role key is sent to browser or Node.

Before Auth creation, five anonymous Node routes must return real application 401 markers and Node health 200. Any Node mutation 502/503/504 or timeout must be reported as a **failed HTTP acceptance**, not silently bypassed with direct SQL fallback or blind POST replay. A completed MP4 requires signed private URL retrieval and ffprobe-confirmed 29–31s portrait H.264 plus AAC, not a mock artifact.

## Outstanding gates and verified prerequisites

Existing signed-in read #40354972715, applied caller-authorized Reel RPC and actual Free SWA write-route negative #40380525626 do not prove successful positive two-shop work. The separate real-JWT no-shop negative canary must also pass before full E2E. Owner/VIEWER/foreign and stale/revoked JWT denial, uncertainty reconciliation, real storage rights, quota/outbox idempotency, cloud MP4 and after-idle reliability must be evidenced in completed Actions logs.

Until those gates pass, keep issue #249 OPEN, leave production frontend on Python Flex, do not provision paid Free-SWA upgrades, GPU/always-ready, PROD or WineShopPOS resources.
