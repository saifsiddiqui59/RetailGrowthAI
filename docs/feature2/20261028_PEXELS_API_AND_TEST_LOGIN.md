# Feature #2 — signed DEV shop and Pexels API check (2026-10-28)

## Verified real account, but not forged login

Read-only Supabase DEV SQL confirmed that the owner's designated existing DEV email exists, email verified, and has an **active OWNER** membership in `test-clothing-business`. This is **not** an authenticated user session or proof of access to the customer's email/password. Neither an account reset, fabricated session, nor role/permission change was performed.

The repository's existing protected `scripts/ops/feature2_free_signed_dev_canary.py` can produce a **genuine signed** zero-cost temporary credential for an existing `@example.invalid` canary account in the isolated shop `f2e20403-0000-4000-8000-000000000403`; it checks signed image upload and prompt and explicitly revokes the test membership after. Previous successful signed hosted smoke #40665965219 did *not* test Pexels stock or render a Reel. This canary requires the protected `dev` GitHub Actions environment; the Feature #2 worker must not commit secrets/alter coordinator workflows or reuse real customer's password.

## Pexels status

According to [Pexels official API policy](https://help.pexels.com/hc/en-us/articles/47677890260761-Is-the-Pexels-API-free-to-use), API use is free with defaults 200 requests/hr, 20,000 requests/mo. Official [key-issuance notice](https://www.pexels.com/api/) dated 2026-10-28: **issuance of new keys is paused**. Existing valid Pexels keys remain usable. No current `PEXELS_API_KEY` was confirmed available inside this developer's environment or the existing GitHub source; secrets in protected environments are intentionally not disclosed.

The official `pexels/pexels-javascript@1.2.1` test importer already exists for four named clothing photos/videos, but it requires an existing Pexels key. The new opt-in Python source module `ai_agents.feature2_pexels_live.discover_clothing_stock` implements **real official Pexels** metadata search at `/v1/search` and `/v1/videos/search` with server-only `PEXELS_API_KEY` and `RETAIL_FEATURE2_PEXELS_ENABLED=true`. Two bounded 8-result API calls fetch photo+vertical-HD video recommendations for allowed clothing search terms. The actual pinned MIT MoneyPrinterTurbo resolution picker selects the smallest adequate 1080x1920 video file. It rechecks the authoritative signed OWNER/EDITOR shop reader before/after fetch, validates source/CDN domains and response shape, fails closed on missing keys/network errors, and returns **discovery-only, not imported/licensed asset** metadata. HTTP integration must be reviewed and deployed by the backend coordinator; this module is not a hosted public route.

Pexels' license permits commercial marketing but does **not** imply that a stock person endorses the shop or that third-party clothing is an actual shop SKU. No original bytes SHA256/private storage, explicit human releases or rights-review acceptance have been created. The one live DEV media row remains a signed **PNG UPLOAD**, not stock video. An authenticated video import needs a reviewed and deployed STOCK/VIDEO storage+registration interface; current `register_uploaded_image` is image-only. Do not impersonate a signed user via DB administrative SQL.

## Required real hosted completion

1. Existing authorized OWNER signs in through the actual https://purple-dune-06b5da200.2.azurestaticapps.net/account page (or existing isolated canary runs from protected main Actions).
2. Supply an **existing** Pexels key server-side (do not commit it or send it in chat). New registration is paused.
3. Coordinator integrates reviewed STOCK photo/video registration/storage with original-byte SHA and separate rights review, then hosts Feature #2 discovery.
4. Fix Azure #249 503, perform real signed Reel FFmpeg output, prove private download, checksum and role isolation. An unchanged public page/CI passing mocks do not prove this.
5. Keep PROD, paid inference, GPU and WineShopPOS untouched.

## 2026-10-28 authentic OWNER browser smoke and Playwright handoff

Live authenticated browser agent **passed read-only**: saved RetailGrowthAI OWNER profile opened `/account`, `/campaigns` and `/trends` without redirects, confirmed active `test-clothing-business` OWNER access, selected shop available and prompt checkbox visible. Zero writes/uploads/render attempts. Hosted page still displays **mock/demo 7-day content, no licensed images, no live trend options, zero verified Reel jobs and legacy nonautomatic prompt copy**. Source PR auto-preview is **not deployed**. This is a real signed-in browser smoke, not an actual hosted Reel/stock acceptance.

Existing PR Playwright CI previously passed 93 mocked Chromium browser tests. It does NOT reuse user cookies from the browser agent and did NOT test a real authenticated uploaded stock video. Added `frontend/e2e/feature2-dev-owner-readonly-playwright.mjs` for **manual actual Playwright** headed Chromium login without transmitting any password through chat, storing authentication files, or modifying hosted data. The script checks real routes and expected authorized shop by UUID, plus hosted prompt-copy deployment status; it exits safely in GitHub Actions and is not part of the default mocked CI suite. Source `--plan`, `node --check`, and denial under CI have automated coverage. Real headed mode must run locally because the agent's signed browser profile is isolated from Playwright's browser context.

Example manual command from local `frontend/e2e` after `npm ci` and `npx playwright install chromium`:

```bash
RGAI_DEV_READONLY_APPROVAL=I_APPROVE_RETAILGROWTHAI_DEV_OWNER_READONLY \
RGAI_DEV_TEST_SHOP_ID=0753c503-ce7f-4544-b8fe-609444ebf068 \
node feature2-dev-owner-readonly-playwright.mjs --run
```

Sign in only in the DEV browser window; never paste credentials into chat. Test intentionally does not upload media, initiate paid AI or confirm a Reel. Complete stock/Reel E2E still requires approved provider key, registered rights and fixed Azure #249.
